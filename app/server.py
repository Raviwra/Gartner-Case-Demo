"""Meridian Credit Memo Assistant: local web server.

Run:  python app/server.py        then open http://localhost:8765
      (set the PORT environment variable to use another port, for example PORT=8766 for testing)

Serves app/static/index.html (the interface) and the JSON API (chats, documents, runs, settings, eval),
plus the memo API and the borrower-case API described in app/MEMO_NOTES.md.
State is on disk under app/data/. The model call is in engine.py. Word export is in memo_docx.py.
"""
import json
import os
import re
import sys
import time
import uuid
from pathlib import Path
from typing import Optional
from urllib.parse import quote

import uvicorn
from fastapi import FastAPI, File, Request, UploadFile
from fastapi.responses import JSONResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles

sys.path.insert(0, str(Path(__file__).resolve().parent))
import engine  # noqa: E402
import store  # noqa: E402

try:
    PORT = int(os.environ.get("PORT") or 8765)
except ValueError:
    PORT = 8765
STATIC = Path(__file__).resolve().parent / "static"

app = FastAPI(title="Meridian Credit Memo Assistant", docs_url=None, redoc_url=None)
store.init()


def err(message, status=400):
    return JSONResponse({"error": message}, status_code=status)


# ---------------------------------------------------------------- health and settings

@app.get("/api/health")
def api_health():
    s = store.get_settings()
    return engine.health(s.get("model", "default"), store.last_model(), s.get("cleanup_model") or None)


@app.get("/api/settings")
def api_settings():
    return store.get_settings()


@app.put("/api/settings")
async def api_settings_put(request: Request):
    try:
        body = await request.json()
        return store.update_settings(body or {})
    except ValueError as e:
        return err(str(e))


@app.post("/api/settings/system_prompt/reset")
def api_prompt_reset():
    return store.reset_system_prompt()


@app.post("/api/settings/system_prompt/restore")
async def api_prompt_restore(request: Request):
    body = await request.json()
    try:
        return store.restore_system_prompt(str((body or {}).get("version_id", "")))
    except ValueError as e:
        return err(str(e), 404)


# ---------------------------------------------------------------- borrower cases

@app.get("/api/cases")
def api_cases():
    return store.list_cases()


@app.put("/api/cases/active")
async def api_cases_active(request: Request):
    body = await _json_body(request)
    try:
        return store.set_active_case(str(body.get("case_id") or ""))
    except ValueError as e:
        return err(str(e))


def _case_filter(case):
    """Validate an optional ?case= filter. Returns (case_id or None, error response or None)."""
    if not case:
        return None, None
    if not store.get_case(case):
        return None, err(f"Unknown case: {case}")
    return case, None


# ---------------------------------------------------------------- documents

@app.get("/api/documents")
def api_documents():
    return store.list_documents()


@app.get("/api/documents/{doc_id}")
def api_document(doc_id: str):
    doc = store.get_document(doc_id)
    return doc if doc else err("Document not found", 404)


@app.post("/api/documents")
async def api_documents_upload(files: list[UploadFile] = File(...)):
    created = []
    for f in files:
        data = await f.read()
        try:
            created.append(store.add_document(f.filename or "upload.txt", data))
        except ValueError as e:
            return err(str(e))
    return created


@app.delete("/api/documents/{doc_id}")
def api_document_delete(doc_id: str):
    try:
        store.delete_document(doc_id)
    except PermissionError as e:
        return err(str(e))
    return {"ok": True}


@app.post("/api/documents/reset")
def api_documents_reset():
    return store.reset_documents()


# ---------------------------------------------------------------- chats

@app.get("/api/chats")
def api_chats(case: Optional[str] = None):
    case_id, bad = _case_filter(case)
    return bad if bad else store.list_chats(case_id)


@app.post("/api/chats")
async def api_chats_create(request: Request):
    body = {}
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        pass
    body = body if isinstance(body, dict) else {}
    return store.create_chat(body.get("name"), body.get("case_id"))


@app.get("/api/chats/{chat_id}")
def api_chat(chat_id: str):
    chat = store.get_chat(chat_id)
    return chat if chat else err("Chat not found", 404)


@app.patch("/api/chats/{chat_id}")
async def api_chat_rename(chat_id: str, request: Request):
    body = await request.json()
    chat = store.rename_chat(chat_id, (body or {}).get("name", ""))
    return chat if chat else err("Chat not found", 404)


@app.delete("/api/chats/{chat_id}")
def api_chat_delete(chat_id: str):
    store.delete_chat(chat_id)
    return {"ok": True}


def build_message(corpus_text, history, prompt):
    parts = ["PROJECT KNOWLEDGE (documents follow; they are the only sources)", "", corpus_text, "",
             "===== END OF PROJECT KNOWLEDGE =====", ""]
    if history:
        parts.append("PRIOR TURNS IN THIS CHAT (oldest first). The disclaimer has already been printed in this chat; do not repeat it.")
        parts.append("")
        for m in history:
            who = "UNDERWRITER" if m["role"] == "user" else "ASSISTANT"
            parts.append(f"--- {who} ---")
            parts.append(m["text"])
            parts.append("")
        parts.append("===== END OF PRIOR TURNS =====")
        parts.append("")
    parts.append("USER REQUEST:")
    parts.append(prompt)
    return "\n".join(parts) + "\n"


def sse(event, data):
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.post("/api/chats/{chat_id}/messages")
async def api_chat_message(chat_id: str, request: Request):
    chat = store.get_chat(chat_id)
    if not chat:
        return err("Chat not found", 404)
    body = await request.json()
    prompt = ((body or {}).get("prompt") or "").strip()
    if not prompt:
        return err("prompt is required")
    settings = store.get_settings()
    system_prompt = settings["system_prompt"]
    model = settings.get("model") or store.DEFAULT_MODEL
    cleanup_model = settings.get("cleanup_model") or None
    message = build_message(store.corpus_text(store.record_case_id(chat)), chat.get("messages", []), prompt)
    run_id = "r_" + uuid.uuid4().hex[:10]

    def generate():
        yield sse("start", {"run_id": run_id, "started_at": store.now()})
        text_parts = []
        try:
            for kind, payload in engine.stream(system_prompt, message, model=model):
                if kind == "delta":
                    text_parts.append(payload)
                    yield sse("delta", {"text": payload})
                elif kind == "done":
                    draft = payload["text"] or "".join(text_parts)
                    draft_model = payload["model"] if payload["model"] not in (None, "", "unknown") else model
                    text, cleanup_status = draft, "off"
                    if cleanup_model:
                        yield sse("status", {"text": "cleanup pass"})
                        text, cleanup_status = engine.cleanup(draft, cleanup_model)
                    label = engine.model_label(draft_model, cleanup_model if cleanup_status == "applied" else None)
                    if cleanup_status.startswith("rejected"):
                        label += " (cleanup rejected, draft kept)"
                    duration_ms = int(payload["duration_ms"]) if cleanup_status == "off" else \
                        int((time.time() - t0) * 1000)
                    # Reload from disk first so a rename made while drafting is not overwritten.
                    latest = store.get_chat(chat["id"]) or chat
                    chat["name"] = latest.get("name", chat["name"])
                    chat["messages"] = latest.get("messages", chat["messages"])
                    chat["messages"].append({"role": "user", "text": prompt, "at": store.now()})
                    chat["messages"].append({"role": "assistant", "text": text, "at": store.now(),
                                             "duration_ms": duration_ms, "model": label, "run_id": run_id})
                    store.save_chat(chat)
                    store.record_run(chat, prompt, text, duration_ms, label, True, run_id,
                                     draft=draft if cleanup_status != "off" else None,
                                     cleanup_status=cleanup_status, cleanup_model=cleanup_model or "")
                    yield sse("done", {"run_id": run_id, "text": text, "model": label, "duration_ms": duration_ms})
        except Exception as e:  # noqa: BLE001
            msg = str(e) or e.__class__.__name__
            store.record_run(chat, prompt, "".join(text_parts), 0, model, False, run_id, error=msg)
            yield sse("error", {"message": msg})

    t0 = time.time()

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(generate(), media_type="text/event-stream", headers=headers)


# ---------------------------------------------------------------- memos (live memo in the Workspace)

LOCKED_MSG = "Section 9 is underwriter-only and cannot be drafted by a tool."


async def _json_body(request):
    try:
        body = await request.json()
    except Exception:  # noqa: BLE001
        body = None
    return body if isinstance(body, dict) else {}


@app.get("/api/memos")
def api_memos(case: Optional[str] = None):
    case_id, bad = _case_filter(case)
    return bad if bad else store.list_memos(case_id)


@app.post("/api/memos")
async def api_memos_create(request: Request):
    body = await _json_body(request)
    return store.create_memo(body.get("name"), body.get("case_id"))


@app.get("/api/memos/{memo_id}")
def api_memo(memo_id: str):
    memo = store.get_memo(memo_id)
    return memo if memo else err("Memo not found", 404)


@app.patch("/api/memos/{memo_id}")
async def api_memo_update(memo_id: str, request: Request):
    body = await _json_body(request)
    header = body.get("header")
    if header is not None and not isinstance(header, dict):
        return err("header must be an object")
    memo = store.update_memo(memo_id, name=body.get("name"), header=header)
    return memo if memo else err("Memo not found", 404)


@app.delete("/api/memos/{memo_id}")
def api_memo_delete(memo_id: str):
    if not store.get_memo(memo_id):
        return err("Memo not found", 404)
    store.delete_memo(memo_id)
    return {"ok": True}


@app.put("/api/memos/{memo_id}/sections/{sid}")
async def api_memo_section_save(memo_id: str, sid: str, request: Request):
    body = await _json_body(request)
    if "text" not in body or not isinstance(body.get("text"), str):
        return err("text is required")
    if not store.get_memo(memo_id):
        return err("Memo not found", 404)
    memo, sec = store.save_section_text(memo_id, sid, body["text"])
    return sec if sec else err("Section not found", 404)


@app.post("/api/memos/{memo_id}/sections/{sid}/draft")
def api_memo_section_draft(memo_id: str, sid: str):
    memo = store.get_memo(memo_id)
    if not memo:
        return err("Memo not found", 404)
    sec = store.memo_section(memo, sid)
    if not sec:
        return err("Section not found", 404)
    if sec.get("author") == "locked":
        return err(LOCKED_MSG)
    if sec.get("author") != "M":
        return err(f"Section {sid} is underwriter-authored and cannot be drafted by a tool.")
    case = store.case_or_default(store.record_case_id(memo))
    prompt = f"Draft Section {sec['id']}, {sec['title']}, for {case['name']}."
    settings = store.get_settings()
    system_prompt = settings["system_prompt"]
    model = settings.get("model") or store.DEFAULT_MODEL
    cleanup_model = settings.get("cleanup_model") or None
    message = build_message(store.corpus_text(case["id"]), [], prompt)
    run_id = "r_" + uuid.uuid4().hex[:10]
    run_owner = {"id": f"memo:{memo_id}", "name": f"Memo: {memo['name']} / Section {sec['id']}", "case_id": case["id"]}
    t0 = time.time()

    def generate():
        yield sse("start", {"run_id": run_id, "started_at": store.now(), "section": sec["id"], "prompt": prompt})
        text_parts = []
        try:
            for kind, payload in engine.stream(system_prompt, message, model=model):
                if kind == "delta":
                    text_parts.append(payload)
                    yield sse("delta", {"text": payload})
                elif kind == "done":
                    draft = payload["text"] or "".join(text_parts)
                    draft_model = payload["model"] if payload["model"] not in (None, "", "unknown") else model
                    text, cleanup_status = draft, "off"
                    if cleanup_model:
                        yield sse("status", {"text": "cleanup pass"})
                        text, cleanup_status = engine.cleanup(draft, cleanup_model)
                    label = engine.model_label(draft_model, cleanup_model if cleanup_status == "applied" else None)
                    if cleanup_status.startswith("rejected"):
                        label += " (cleanup rejected, draft kept)"
                    duration_ms = int(payload["duration_ms"]) if cleanup_status == "off" else \
                        int((time.time() - t0) * 1000)
                    store.record_run(run_owner, prompt, text, duration_ms, label, True, run_id,
                                     draft=draft if cleanup_status != "off" else None,
                                     cleanup_status=cleanup_status, cleanup_model=cleanup_model or "")
                    _, saved = store.save_section_draft(memo_id, sec["id"], text, label, run_id, duration_ms)
                    if not saved:
                        yield sse("error", {"message": "The memo was deleted while drafting. The run log keeps the response."})
                        return
                    yield sse("done", {"run_id": run_id, "text": saved["text"], "model": label,
                                       "duration_ms": duration_ms, "section": saved})
        except Exception as e:  # noqa: BLE001
            msg = str(e) or e.__class__.__name__
            store.record_run(run_owner, prompt, "".join(text_parts), 0, model, False, run_id, error=msg)
            yield sse("error", {"message": msg})

    headers = {"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    return StreamingResponse(generate(), media_type="text/event-stream", headers=headers)


@app.post("/api/memos/{memo_id}/sections/{sid}/comments")
async def api_memo_comment_add(memo_id: str, sid: str, request: Request):
    body = await _json_body(request)
    if not store.get_memo(memo_id):
        return err("Memo not found", 404)
    try:
        c = store.add_comment(memo_id, sid, body.get("text"), body.get("author"))
    except ValueError as e:
        return err(str(e))
    return c if c else err("Section not found", 404)


@app.patch("/api/memos/{memo_id}/sections/{sid}/comments/{cid}")
async def api_memo_comment_update(memo_id: str, sid: str, cid: str, request: Request):
    body = await _json_body(request)
    c = store.update_comment(memo_id, sid, cid, resolved=body.get("resolved"), text=body.get("text"))
    return c if c else err("Comment not found", 404)


@app.delete("/api/memos/{memo_id}/sections/{sid}/comments/{cid}")
def api_memo_comment_delete(memo_id: str, sid: str, cid: str):
    return {"ok": True} if store.delete_comment(memo_id, sid, cid) else err("Comment not found", 404)


@app.post("/api/memos/{memo_id}/checklist/consolidate")
def api_memo_checklist_consolidate(memo_id: str):
    """Layer 2: one call to the draft model with the grouped checklist; JSON back, no streaming. The answer is
    guarded (engine.check_consolidation) and stored on the memo only if it passes. Suggestions only."""
    memo = store.get_memo(memo_id)
    if not memo:
        return err("Memo not found", 404)
    grouped = store.group_checklist(memo)
    if not grouped["count"]:
        return err("No checklist items yet. Draft the machine-assembled sections first.")
    items, message = engine.consolidate_input(grouped)
    model = store.get_settings().get("model") or store.DEFAULT_MODEL
    run_id = "r_" + uuid.uuid4().hex[:10]
    run_owner = {"id": f"memo:{memo_id}", "name": f"Memo: {memo['name']} / Checklist consolidation",
                 "case_id": store.record_case_id(memo)}
    res = engine.consolidate(message, len(items), model=model)
    label = res["model"] if res["model"] not in (None, "", "unknown") else model
    if res["status"] != "accepted":
        why = ("Guard rejected: " if res["status"] == "rejected" else "Engine failed: ") + res["reason"]
        store.record_run(run_owner, message, res["raw"], res["duration_ms"], label, False, run_id, error=why)
        return {"status": res["status"], "reason": res["reason"], "run_id": run_id, "duration_ms": res["duration_ms"]}
    data = res["data"]
    by_n = {it["n"]: it for it in items}
    for d in data["dropped"]:
        d["text"] = by_n[d["item"]]["text"]
        d["sections"] = by_n[d["item"]]["sections"]
    stored = {"at": store.now(), "model": label, "duration_ms": res["duration_ms"], "run_id": run_id,
              "source_item_count": len(items), "original_item_count": grouped["original_count"],
              "source_items": items, "citation_repairs": res.get("citation_repairs") or []}
    stored.update(data)
    store.record_run(run_owner, message, res["raw"], res["duration_ms"], label, True, run_id)
    if store.save_checklist_consolidated(memo_id, stored) is None:
        return err("The memo was deleted while the suggestion ran. The run log keeps the response.", 404)
    return {"status": "accepted", "checklist_consolidated": stored}


@app.delete("/api/memos/{memo_id}/checklist/consolidate")
def api_memo_checklist_clear(memo_id: str):
    return {"ok": True} if store.clear_checklist_consolidated(memo_id) else err("Memo not found", 404)


@app.get("/api/memos/{memo_id}/export.docx")
def api_memo_export(memo_id: str):
    memo = store.get_memo(memo_id)
    if not memo:
        return err("Memo not found", 404)
    import memo_docx  # local import: python-docx loads only when someone exports
    data = memo_docx.build(memo)
    name = (memo.get("name") or "Credit memo").strip() or "Credit memo"
    ascii_name = re.sub(r'[^A-Za-z0-9 ._()-]+', "_", name).strip() or "Credit memo"
    disp = f'attachment; filename="{ascii_name}.docx"; filename*=UTF-8\'\'{quote(name + ".docx")}'
    return Response(content=data,
                    media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    headers={"Content-Disposition": disp, "Cache-Control": "no-cache"})


# ---------------------------------------------------------------- runs and eval

@app.get("/api/runs")
def api_runs():
    return store.list_runs()


@app.get("/api/runs/{run_id}")
def api_run(run_id: str):
    r = store.get_run(run_id)
    return r if r else err("Run not found", 404)


@app.get("/api/eval/summary")
def api_eval_summary():
    return store.eval_summary()


# ---------------------------------------------------------------- static page (mounted last)

app.mount("/", StaticFiles(directory=str(STATIC), html=True), name="static")


if __name__ == "__main__":
    store.init()
    print(f"Meridian Credit Memo Assistant: http://localhost:{PORT}")
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
