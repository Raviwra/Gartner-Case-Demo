"""The model engine: one place that talks to Claude.

This prototype calls Claude Code non-interactively (`claude -p`) on the user's subscription login,
with every tool disabled, exactly as the eval harness does. Production would replace this file with a
call through the bank's LLM gateway (Azure OpenAI). Nothing else in the app needs to change.
"""
import glob
import json
import os
import re
import shutil
import subprocess
import tempfile
import time


def find_claude(explicit=None):
    """Locate the Claude Code executable: explicit path, CLAUDE_BIN, PATH, then the desktop app bundle."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("CLAUDE_BIN"):
        candidates.append(os.environ["CLAUDE_BIN"])
    for name in ("claude", "claude.exe", "claude.cmd"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    for base in (os.environ.get("APPDATA"), os.environ.get("LOCALAPPDATA")):
        if not base:
            continue
        patterns = [
            os.path.join(base, "Claude", "claude-code", "*", "*", "claude.exe"),
            os.path.join(base, "Packages", "Claude_*", "LocalCache", "Roaming", "Claude", "claude-code", "*", "*", "claude.exe"),
        ]
        for pat in patterns:
            candidates.extend(reversed(sorted(glob.glob(pat))))
    for c in candidates:
        if c and os.path.exists(c):
            return c
    return None


def _env():
    env = dict(os.environ)
    env.pop("CLAUDECODE", None)  # nested-session guard; this is a separate non-interactive run
    return env


def _run(args, timeout=60):
    exe = find_claude()
    if not exe:
        raise RuntimeError("claude executable not found")
    proc = subprocess.run([exe] + args, capture_output=True, text=True, encoding="utf-8", errors="replace",
                          env=_env(), timeout=timeout, cwd=tempfile.gettempdir())
    return proc.stdout.strip(), proc.stderr.strip(), proc.returncode


def health(model_setting="default", last_model=None, cleanup_model=None):
    exe = find_claude()
    if not exe:
        return {"engine": "claude-cli", "version": "", "logged_in": False, "model": "",
                "message": "Claude Code executable not found. Install Claude Code or set CLAUDE_BIN."}
    try:
        version, _, _ = _run(["--version"])
    except Exception as e:  # noqa: BLE001
        version = f"unknown ({e})"
    logged_in = False
    message = ""
    try:
        out, err, _ = _run(["auth", "status"])
        status = json.loads(out) if out.startswith("{") else {}
        logged_in = bool(status.get("loggedIn"))
        if not logged_in:
            message = "Not logged in. Run: claude auth login"
    except Exception as e:  # noqa: BLE001
        message = f"Could not read sign-in status: {e}"
    draft = model_setting if model_setting and model_setting != "default" else (last_model or "default (Claude Code)")
    model = model_label(draft, cleanup_model)
    return {"engine": "claude-cli", "version": version.replace(" (Claude Code)", ""), "logged_in": logged_in,
            "model": model, "draft_model": draft, "cleanup_model": cleanup_model or "", "message": message, "path": exe}


DRAFT_MODEL = "claude-sonnet-5-5"
CLEANUP_MODEL = "claude-haiku-5-5"

CLEANUP_PROMPT = """You are a copy editor for a bank's credit memo drafting assistant. You receive one draft response. Return the same response edited only for concision and clarity.

Rules:
- Keep every number, percentage, ratio, date and dollar amount exactly as written.
- Keep every bracket citation such as [D1, Table 1: Revenue, FY2025] exactly as written. Do not add, remove, merge or reorder citations.
- Keep every heading, every table with all its rows and columns, every bullet under "Underwriter to complete", the "Sources used" list, the words CONFLICT and "Not in provided documents", the opening disclaimer sentence, and the closing line "Section 9 Risk Rating and Rationale: underwriter only, required." exactly as they are.
- Keep scripted sentences word for word, in particular "Risk rating and recommendation are set by the underwriter [D4, §4.2.5]. I can list the cited facts relevant to that judgment." and any sentence of the form "Section [n] is underwriter-authored".
- Shorten wordy sentences. Remove repetition, filler, and any closing offer or question.
- Do not add any fact, adjective, opinion, rating or recommendation.
- Keep Markdown formatting. Do not use em dashes.
- Output only the edited response, with no preamble."""

_NUMBER_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d{4,}|\d+(?=\s?%)")
_CITE_RE = re.compile(r"\[\s*D\d+\s*,[^\[\]\n]*\]")
_FIXED_PHRASES = ("CONFLICT", "Not in provided documents",
                  "Section 9 Risk Rating and Rationale: underwriter only, required",
                  "Risk rating and recommendation are set by the underwriter",
                  "is underwriter-authored", "Drafting aid only.")


# Rating or recommendation wording: "rating ... 6", "7 out of 10", "recommend approval". Used by both guards.
_RATING_RE = re.compile(r"(?i)\b(rating|rated|rate)\b[^\n\d]{0,25}(?<!Section )(?<!Sections )\b([1-9]|10)\b(?!\s*(?:-|to)\s*\d)"
                        r"|\b([1-9]|10)\s*(?:out )?of\s*10\b|\brecommend (approval|decline|approving|declining)")


def model_label(draft_model, cleanup_model):
    if cleanup_model:
        return f"{draft_model} (draft) + {cleanup_model} (cleanup)"
    return draft_model


def check_cleanup(draft, cleaned):
    """Return None if the cleaned text preserved everything that must not change, else the reason."""
    if not cleaned or not cleaned.strip():
        return "empty result"
    if len(cleaned) < 0.4 * len(draft):
        return "result is less than 40 percent of the draft length"
    new_numbers = sorted(set(_NUMBER_RE.findall(cleaned)) - set(_NUMBER_RE.findall(draft)))
    if new_numbers:
        return f"introduced numbers {new_numbers}"
    missing_cites = sorted(set(_CITE_RE.findall(draft)) - set(_CITE_RE.findall(cleaned)))
    if missing_cites:
        return f"dropped citations {missing_cites[:3]}"
    for phrase in _FIXED_PHRASES:
        if phrase in draft and phrase not in cleaned:
            return f"dropped the phrase {phrase!r}"
    if draft.count("|") and cleaned.count("|") < 0.8 * draft.count("|"):
        return "table content was reduced"
    if _RATING_RE.search(cleaned) and not _RATING_RE.search(draft):
        return "introduced rating or recommendation wording"
    return None


def cleanup(draft, model=CLEANUP_MODEL, timeout=180):
    """Run the concision pass. Returns (text, status). On any failure the draft is returned unchanged."""
    exe = find_claude()
    if not exe or not draft.strip():
        return draft, "skipped"
    cmd = [exe, "-p", "--system-prompt", CLEANUP_PROMPT, "--tools", "", "--strict-mcp-config",
           "--output-format", "json", "--no-session-persistence", "--model", model]
    workdir = tempfile.mkdtemp(prefix="meridian-cleanup-")
    try:
        proc = subprocess.run(cmd, input=draft, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=_env(), cwd=workdir, timeout=timeout)
    except Exception as e:  # noqa: BLE001
        shutil.rmtree(workdir, ignore_errors=True)
        return draft, f"rejected: {e}"
    shutil.rmtree(workdir, ignore_errors=True)
    try:
        envelope = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        return draft, "rejected: unreadable engine output"
    if envelope.get("is_error") or not isinstance(envelope.get("result"), str):
        return draft, f"rejected: {envelope.get('result') or 'engine error'}"
    cleaned = envelope["result"].strip() + "\n"
    # The opening disclaimer is a fixed line the rulebook requires; put it back if the editor dropped it.
    first = draft.strip().splitlines()[0].strip() if draft.strip() else ""
    if first.startswith("Drafting aid only."):
        # Remove every copy the editor left (bolded, moved or duplicated), then put one exact copy first.
        kept = [ln for ln in cleaned.splitlines() if "Drafting aid only." not in ln.replace("*", "")]
        cleaned = first + "\n\n" + "\n".join(kept).lstrip("\n")
    reason = check_cleanup(draft, cleaned)
    if reason:
        snippet = " ".join(cleaned.split())[:160]
        return draft, f"rejected: {reason}; cleanup output began: {snippet!r}"
    return cleaned, "applied"


def stream(system_prompt, message, model=None, timeout=600):
    """Yield ("delta", text) chunks, then ("done", info). Raises RuntimeError on engine failure."""
    exe = find_claude()
    if not exe:
        raise RuntimeError("claude executable not found")
    cmd = [exe, "-p", "--system-prompt", system_prompt, "--tools", "", "--strict-mcp-config",
           "--output-format", "stream-json", "--include-partial-messages", "--verbose",
           "--no-session-persistence"]
    if model and model != "default":
        cmd += ["--model", model]
    workdir = tempfile.mkdtemp(prefix="meridian-app-")
    started = time.time()
    deltas = []
    final_text = None
    model_used = None
    is_error = False
    error_text = ""
    proc = None
    try:
        proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                text=True, encoding="utf-8", errors="replace", env=_env(), cwd=workdir)
        proc.stdin.write(message)
        proc.stdin.close()
        for line in proc.stdout:
            line = line.strip()
            if not line.startswith("{"):
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            t = obj.get("type")
            if t == "stream_event":
                ev = obj.get("event") or {}
                if ev.get("type") == "content_block_delta":
                    d = ev.get("delta") or {}
                    if d.get("type") == "text_delta" and d.get("text"):
                        deltas.append(d["text"])
                        yield ("delta", d["text"])
            elif t == "assistant" and not deltas:
                msg = obj.get("message") or {}
                parts = [c.get("text", "") for c in (msg.get("content") or []) if c.get("type") == "text"]
                if parts:
                    text = "".join(parts)
                    final_text = (final_text or "") + text
                    yield ("delta", text)
            elif t == "result":
                is_error = bool(obj.get("is_error"))
                usage = obj.get("modelUsage") or {}
                if isinstance(usage, dict) and usage:
                    # Claude Code may also bill a small helper model; report the one that wrote the answer.
                    def _out(v):
                        return (v or {}).get("outputTokens", 0) if isinstance(v, dict) else 0
                    if model and model in usage:
                        model_used = model
                    else:
                        model_used = max(usage.keys(), key=lambda k: _out(usage[k]))
                if isinstance(obj.get("result"), str):
                    if is_error:
                        error_text = obj["result"]
                    elif final_text is None and not deltas:
                        final_text = obj["result"]
                        yield ("delta", final_text)
        proc.wait(timeout=timeout)
        stderr = proc.stderr.read().strip()
        if proc.returncode not in (0, None) and not deltas and not final_text:
            raise RuntimeError(error_text or stderr or f"claude exited with code {proc.returncode}")
        if is_error:
            raise RuntimeError(error_text or stderr or "claude reported an error")
    finally:
        # If the caller stops consuming (browser closed mid-draft), do not leave the model process running.
        try:
            if proc is not None and proc.poll() is None:
                proc.kill()
        except Exception:  # noqa: BLE001
            pass
        shutil.rmtree(workdir, ignore_errors=True)
    text = "".join(deltas) if deltas else (final_text or "")
    yield ("done", {"text": text, "model": model_used or (model or "unknown"),
                    "duration_ms": int((time.time() - started) * 1000)})


# ---------------------------------------------------------------- checklist consolidation (Layer 2, suggestions only)
# One call to the draft model with the grouped "Underwriter to complete" items. The answer is JSON. It is accepted
# only if check_consolidation() passes; otherwise the page keeps showing the grouped list. Nothing is applied to
# the memo text: the result is stored beside the memo as suggestions for the underwriter.

CONSOLIDATE_PROMPT = """You help an underwriter at a bank tidy the "Underwriter to complete" checklist of a draft commercial credit memo. You receive the checklist as a numbered list that code has already sorted into groups. Each item shows the memo sections it came from, and keeps its bracket citations such as [D2, §1.1].

Return one JSON object with exactly these keys:
{
  "documents_to_request": [{"item": "", "would_be_in": "", "request_line": ""}],
  "conflicts": [{"item": "", "how_to_resolve": ""}],
  "policy_items": [{"item": "", "judgment_needed": ""}],
  "sections_to_write": [{"section": "", "what_it_needs": ""}],
  "suggested_edits": [{"section": "", "suggestion": ""}],
  "dropped": [{"item": 0, "reason": ""}]
}

What each key holds:
- documents_to_request: one entry per missing document or record. "item" names what is missing. "would_be_in" names the document or file that would normally hold it, as the input says. "request_line" is one plain, polite sentence the relationship manager could send to the borrower to ask for it. If the input says the record is kept inside the bank (for example the loan file or Credit Administration), write the request line to that bank team instead.
- conflicts: each conflict between sources, and how the underwriter could resolve it, for example which document to check. Do not choose between the values.
- policy_items: each item that needs the underwriter's policy judgment, and what that judgment is. You may name the policy test and the cited figures. Do not say whether any test is met or failed.
- sections_to_write: the underwriter-authored parts named in the items (3.5, 7, 8 and 10) and what each needs, from the items. Leave Section 9 out entirely: only the underwriter writes it.
- suggested_edits: wording or structure suggestions for the machine-drafted Sections 1 to 6 only, such as listing a repeated item once or making a request clearer. No new facts.
- dropped: the number of every input item you merged into another entry or removed as a duplicate or filler, with a two-word reason such as "duplicate item", "merged item", "filler reminder" or "pointer only". Filler means a reminder that a judgment belongs to the underwriter with no task in it.

Rules:
- Merge items that ask for the same thing into one entry. Every input item should end up either in an entry or in "dropped".
- Citations: copy each bracket citation whole, character for character, from the input. Never join two brackets into one, never split a bracket, never shorten or reorder what is inside one, and never put a plain-text reference such as D2 §2.2(a) into brackets. If an entry draws on several brackets, write each one separately, exactly as in the input. Add no citation that is not in the input. You may leave a citation out.
- Add no figures. Use only numbers that appear in the input, written the same way.
- Never state, suggest, imply or infer a risk rating, a score, an approval, a decline or a recommendation. Do not use the words rating, rated or score.
- Keep each text value under 25 words.
- These are suggestions only. The underwriter decides. Do not write as if anything has been decided or applied.
- Plain language. No em dashes.
- Output the JSON object only: no code fences, no text before or after it."""

CONSOLIDATE_GROUPS = ("documents_to_request", "conflicts", "policy_items", "sections_to_write", "suggested_edits")
CONSOLIDATE_FIELDS = {
    "documents_to_request": ("item", "would_be_in", "request_line"),
    "conflicts": ("item", "how_to_resolve"),
    "policy_items": ("item", "judgment_needed"),
    "sections_to_write": ("section", "what_it_needs"),
    "suggested_edits": ("section", "suggestion"),
}


def consolidate_input(grouped):
    """The user message for the consolidation call, and the numbered items it lists.
    `grouped` is store.group_checklist(memo)."""
    items, lines = [], [f"UNDERWRITER TO COMPLETE CHECKLIST: {grouped['original_count']} items in the memo, "
                        f"{grouped['count']} after grouping by code.", ""]
    for g in grouped["groups"]:
        if not g["items"]:
            continue
        lines.append(f"Group: {g['title']}")
        for it in g["items"]:
            n = len(items) + 1
            secs = it["sections"]
            label = ("Section " if len(secs) == 1 else "Sections ") + ", ".join(secs)
            also = it.get("also_cites") or []
            text = it["text"] + (" Also cited in the repeats: " + " ".join(also) if also else "")
            lines.append(f"{n}. ({label}) {text}")
            items.append({"n": n, "group": g["key"], "sections": secs, "text": text})
        lines.append("")
    lines.append("Return the JSON object described in your instructions.")
    return items, "\n".join(lines) + "\n"


def _strip_fences(text):
    t = str(text or "").strip()
    m = re.match(r"^```[a-zA-Z]*\s*\n(.*?)\n?```\s*$", t, re.S)
    if m:
        t = m.group(1).strip()
    if not t.startswith("{"):
        a, b = t.find("{"), t.rfind("}")
        if a >= 0 and b > a:
            t = t[a:b + 1]
    return t


def _no_dashes(s):
    return str(s).replace("\u2014", " - ").replace("\u2013", "-")


def parse_consolidation(text, item_count):
    """Parse and tidy the model's JSON. Returns (data, error)."""
    try:
        raw = json.loads(_strip_fences(text))
    except (json.JSONDecodeError, TypeError) as e:
        return None, f"the answer was not valid JSON ({e.msg if hasattr(e, 'msg') else e})"
    if not isinstance(raw, dict):
        return None, "the answer was not a JSON object"
    data = {}
    for key in CONSOLIDATE_GROUPS:
        rows = raw.get(key) or []
        if not isinstance(rows, list):
            return None, f"{key} is not a list"
        clean = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            entry = {f: _no_dashes(row.get(f) if row.get(f) is not None else "").strip() for f in CONSOLIDATE_FIELDS[key]}
            if any(entry.values()):
                clean.append(entry)
        data[key] = clean
    dropped = []
    for row in raw.get("dropped") or []:
        n, reason = (row.get("item"), row.get("reason", "")) if isinstance(row, dict) else (row, "")
        try:
            n = int(n)
        except (TypeError, ValueError):
            continue
        if 1 <= n <= item_count and n not in [d["item"] for d in dropped]:
            dropped.append({"item": n, "reason": _no_dashes(reason).strip()})
    data["dropped"] = dropped
    return data, None


def consolidation_text(data):
    """Every text value of a parsed result, joined: what the guard checks."""
    parts = []
    for key in CONSOLIDATE_GROUPS:
        for row in data.get(key) or []:
            parts.extend(str(v) for v in row.values())
    parts.extend(str(d.get("reason", "")) for d in data.get("dropped") or [])
    return "\n".join(parts)


def _ws(s):
    return re.sub(r"\s+", " ", s).strip()


def _repair_citation(cite, source):
    """Map a bracket citation that is not in the input back to what the input has, or return None.
    "[D1, §2; D2, §1.1]" becomes "[D1, §2] [D2, §1.1]" and "[D1, §5, §6]" becomes "[D1, §5] [D1, §6]" when those
    brackets are in the input; "[D5, ¶5]" becomes the plain text "D5 ¶5" when the input only mentions it in text."""
    src = _ws(source)
    parts = [p.strip() for p in cite.strip()[1:-1].split(";") if p.strip()]
    bracketed, plain = [], []
    for part in parts:
        m = re.match(r"^(D\d+)\s*,\s*(.+)$", part)
        if not m:
            return None
        doc, rest = m.group(1), _ws(m.group(2))
        whole = f"[{doc}, {rest}]"
        refs = [r.strip() for r in rest.split(",") if r.strip()]
        if whole in src:
            bracketed.append(whole)
        elif len(refs) > 1 and all(f"[{doc}, {r}]" in src for r in refs):
            bracketed.extend(f"[{doc}, {r}]" for r in refs)
        else:
            bracketed = None
            break
    if bracketed:
        return " ".join(bracketed)
    for part in parts:
        m = re.match(r"^(D\d+)\s*,\s*(.+)$", part)
        text = f"{m.group(1)} {_ws(m.group(2))}"
        if text not in src:
            return None
        plain.append(text)
    return " and ".join(plain)


def repair_citations(source, data):
    """Before the guard: rewrite bracket citations the model joined, split or invented from a plain-text
    reference, but only into brackets or plain text that appear in the input as written. Anything else is left
    for check_consolidation to reject. Returns the list of {from, to} changes."""
    changes = []
    src = _ws(source)

    def fix(text):
        def one(m):
            c = m.group(0)
            if _ws(c) in src:
                return c
            to = _repair_citation(c, source)
            if to is None:
                return c
            changes.append({"from": c, "to": to})
            return to
        return _CITE_RE.sub(one, text)

    for key in CONSOLIDATE_GROUPS:
        for row in data.get(key) or []:
            for f in list(row):
                row[f] = fix(row[f])
    return changes


def check_consolidation(source, data):
    """Return None if the suggestions may be shown, else the reason. Modelled on check_cleanup:
    citations must come from the input, no new figures, no rating or recommendation wording, something to show."""
    if not data or not any(data.get(k) for k in CONSOLIDATE_GROUPS):
        return "every group was empty"
    out = consolidation_text(data)
    src = _ws(source)
    added = sorted({c for c in _CITE_RE.findall(out) if _ws(c) not in src})
    if added:
        return f"citations not in the checklist {added[:3]}"
    new_numbers = sorted(set(_NUMBER_RE.findall(out)) - set(_NUMBER_RE.findall(source)))
    if new_numbers:
        return f"introduced numbers {new_numbers[:5]}"
    m = _RATING_RE.search(out)
    if m:
        return f"rating or recommendation wording ({m.group(0)!r})"
    return None


def consolidate(message, item_count, model=DRAFT_MODEL, timeout=300):
    """One non-streaming call to the draft model. Returns a dict:
    {status: "accepted" | "rejected" | "failed", reason, data, raw, model, duration_ms}."""
    started = time.time()
    out = {"status": "failed", "reason": "", "data": None, "raw": "", "model": model or "default", "duration_ms": 0,
           "citation_repairs": []}
    exe = find_claude()
    if not exe:
        out["reason"] = "claude executable not found"
        return out
    cmd = [exe, "-p", "--system-prompt", CONSOLIDATE_PROMPT, "--tools", "", "--strict-mcp-config",
           "--output-format", "json", "--no-session-persistence"]
    if model and model != "default":
        cmd += ["--model", model]
    workdir = tempfile.mkdtemp(prefix="meridian-consolidate-")
    try:
        proc = subprocess.run(cmd, input=message, capture_output=True, text=True, encoding="utf-8", errors="replace",
                              env=_env(), cwd=workdir, timeout=timeout)
    except Exception as e:  # noqa: BLE001
        out["reason"] = f"engine error: {e}"
        out["duration_ms"] = int((time.time() - started) * 1000)
        return out
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    out["duration_ms"] = int((time.time() - started) * 1000)
    try:
        envelope = json.loads(proc.stdout.strip())
    except json.JSONDecodeError:
        out["reason"] = "unreadable engine output" + (f": {proc.stderr.strip()[:200]}" if proc.stderr.strip() else "")
        return out
    usage = envelope.get("modelUsage") or {}
    if isinstance(usage, dict) and usage:
        if model in usage:
            out["model"] = model
        else:
            out["model"] = max(usage.keys(), key=lambda k: (usage[k] or {}).get("outputTokens", 0)
                               if isinstance(usage[k], dict) else 0)
    if envelope.get("is_error") or not isinstance(envelope.get("result"), str):
        out["reason"] = f"engine error: {envelope.get('result') or 'no result'}"
        return out
    out["raw"] = envelope["result"]
    data, error = parse_consolidation(out["raw"], item_count)
    if error:
        out["status"], out["reason"] = "rejected", error
        return out
    out["citation_repairs"] = repair_citations(message, data)
    reason = check_consolidation(message, data)
    if reason:
        out["status"], out["reason"], out["data"] = "rejected", reason, data
        return out
    out["status"], out["data"] = "accepted", data
    return out
