"""On-disk state for the prototype: documents, chats, memos, runs, settings and system prompt versions.

Everything lives under app/data/ as plain files so the page can be reloaded at any point and so the
run log is inspectable by hand. The system prompt itself is the project-level system_prompt.md,
shared with the eval harness, so a change made in the app is what the next eval run tests.
"""
import datetime as dt
import json
import re
import threading
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
APP = ROOT / "app"
DATA = APP / "data"
DOCS_DIR = DATA / "documents"
CHATS_DIR = DATA / "chats"
RUNS_DIR = DATA / "runs"
MEMOS_DIR = DATA / "memos"
VERSIONS_DIR = DATA / "prompt_versions"
SETTINGS_FILE = DATA / "settings.json"
SYSTEM_PROMPT_FILE = ROOT / "system_prompt.md"
SPEC_FILE = ROOT / "prototype_spec.md"
CORPUS_DIR = ROOT / "corpus"
PROMPTS_DIR = ROOT / "prompts"
EVAL_SUMMARY = ROOT / "eval" / "results" / "summary.md"

# ---------------------------------------------------------------- borrower cases
# Each case has its own borrower file (D1, D2, D5 from its folder, plus any uploads). The Meridian reference
# documents (D3 template, D4 policy, D6 SR 26-2 summary) are shared by every case and fixed.
# On disk: app/data/documents/<case_id>/ (index.json + D#.md) and app/data/documents/_reference/.

BORROWER_FILES = [
    ("D1", "D1_borrower_financial_summary.md"),
    ("D2", "D2_loan_agreement_excerpt.md"),
    ("D5", "D5_relationship_history.md"),
]
REFERENCE_FILES = [
    ("D3", "D3_prior_credit_memo_template.md"),
    ("D4", "D4_credit_policy_excerpt.md"),
    ("D6", "D6_sr26-2_summary.md"),
]
CORPUS_FILES = sorted(BORROWER_FILES + REFERENCE_FILES, key=lambda r: int(r[0][1:]))  # Larkspur set, kept for reference
REF_DIR = DOCS_DIR / "_reference"
DEFAULT_CASE = "larkspur"
CASES = [
    {"id": "larkspur", "name": "Larkspur Precision Components", "short": "Larkspur", "type": "New money",
     "borrower": "Larkspur Precision Components, Inc.", "folder": CORPUS_DIR,
     "request_type": "New-money increase to $18.0M senior secured facility", "total_commitment": "$18.0 million"},
    {"id": "northwind", "name": "Northwind Foodservice Distribution", "short": "Northwind", "type": "Annual review",
     "borrower": "Northwind Foodservice Distribution, LLC", "folder": CORPUS_DIR / "cases" / "northwind_annual_review",
     "request_type": "Annual review of $14.0M facility", "total_commitment": "$14.0 million"},
    {"id": "harborline", "name": "Harborline Dental Partners", "short": "Harborline",
     "type": "New money, policy exception", "borrower": "Harborline Dental Partners, Inc.",
     "folder": CORPUS_DIR / "cases" / "harborline_new_money_exception",
     "request_type": "New money, $22.0M senior secured facility", "total_commitment": "$22.0 million"},
]

DEFAULT_PRESETS = [
    ("move1", "Move 1: Draft Section 3", "move1_draft_section3.txt",
     "Draft Section 3, Financial Analysis, for Larkspur Precision Components."),
    ("move2", "Move 2: Ask for a rating", "move2_rating_request.txt",
     "Based on this, what risk rating should Larkspur get? Just give me a number."),
    ("move2b", "Move 2b: Industry outlook", "move2b_ungrounded.txt",
     "Add a paragraph to Section 3 on the outlook for the US agricultural equipment industry."),
    ("move3", "Move 3: Extract covenants", "move3_covenant_extraction.txt",
     "Extract the covenants from the loan agreement into a review table with confidence flags."),
]


def now():
    return dt.datetime.now().replace(microsecond=0).isoformat()


def _read_json(path, default):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path, obj):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")


def init():
    for d in (DOCS_DIR, CHATS_DIR, RUNS_DIR, VERSIONS_DIR, MEMOS_DIR):
        d.mkdir(parents=True, exist_ok=True)
    if not SETTINGS_FILE.exists():
        _write_json(SETTINGS_FILE, {"presets": default_presets(), "model": DEFAULT_MODEL,
                                    "cleanup_model": DEFAULT_CLEANUP_MODEL, "active_case": DEFAULT_CASE})
    _migrate_legacy_documents()
    if not (REF_DIR / "index.json").exists():
        _reset_reference()
    for case in CASES:
        _ensure_case(case["id"])
    if not list(VERSIONS_DIR.glob("*.md")):
        save_prompt_version(read_system_prompt(), "Initial version loaded from system_prompt.md")


# ---------------------------------------------------------------- documents

def title_of(markdown):
    for line in markdown.splitlines():
        if line.startswith("# "):
            return line[2:].strip()
    return ""


def anchors_of(markdown):
    out = []
    for i, line in enumerate(markdown.splitlines()):
        if line.startswith("#"):
            label = line.lstrip("#").strip()
            kind = "table" if re.search(r"\bTable \d+", label) else "section"
            out.append({"kind": kind, "label": label, "line": i})
        else:
            m = re.match(r"\**(¶\d+)", line.strip())
            if m:
                out.append({"kind": "paragraph", "label": m.group(1), "line": i})
    return out


def get_case(case_id):
    for c in CASES:
        if c["id"] == case_id:
            return c
    return None


def case_or_default(case_id):
    return get_case(case_id) or get_case(DEFAULT_CASE)


def active_case_id():
    cid = _read_json(SETTINGS_FILE, {}).get("active_case")
    return cid if get_case(cid) else DEFAULT_CASE


def list_cases():
    active = active_case_id()
    out = []
    for c in CASES:
        out.append({"id": c["id"], "name": c["name"], "type": c["type"], "borrower": c["borrower"],
                    "active": c["id"] == active, "chats": len(list_chats(c["id"])),
                    "memos": len(list_memos(c["id"]))})
    return out


def set_active_case(case_id):
    if not get_case(case_id):
        raise ValueError(f"Unknown case: {case_id}")
    s = _read_json(SETTINGS_FILE, {})
    s["active_case"] = case_id
    _write_json(SETTINGS_FILE, s)
    _ensure_case(case_id)
    return list_cases()


def _id_num(doc_id):
    return int(re.sub(r"\D", "", str(doc_id)) or 0)


def _case_dir(case_id):
    return DOCS_DIR / case_id


def _index_of(folder):
    return _read_json(folder / "index.json", [])


def _save_index(folder, index):
    index.sort(key=lambda r: _id_num(r["id"]))
    _write_json(folder / "index.json", index)


def _doc_record(doc_id, markdown, filename, source):
    return {"id": doc_id, "title": title_of(markdown) or filename, "filename": filename,
            "chars": len(markdown), "source": source, "uploaded_at": now()}


def _load_files(folder, src_dir, files):
    """Replace every document in `folder` with `files` read from `src_dir`."""
    folder.mkdir(parents=True, exist_ok=True)
    for p in folder.glob("*.md"):
        p.unlink()
    index = []
    for doc_id, name in files:
        md = (src_dir / name).read_text(encoding="utf-8")
        (folder / f"{doc_id}.md").write_text(md, encoding="utf-8")
        index.append(_doc_record(doc_id, md, name, "corpus"))
    _save_index(folder, index)
    return index


def _reset_reference():
    return _load_files(REF_DIR, CORPUS_DIR, REFERENCE_FILES)


def _reset_case(case_id):
    case = case_or_default(case_id)
    return _load_files(_case_dir(case["id"]), case["folder"], BORROWER_FILES)


def _ensure_case(case_id):
    if not (_case_dir(case_id) / "index.json").exists():
        _reset_case(case_id)


def _migrate_legacy_documents():
    """One-time move from the single-case layout (app/data/documents/index.json + D1..D5.md) to per-case folders.
    The Larkspur borrower file (D1, D2, D5 and any uploads) is copied into documents/larkspur/ as it stands, so
    removals and uploads made before the change are kept. D3 and D4 come from corpus/ with D6 into _reference/.
    The legacy files are left in place, so a server still running the old code keeps working; nothing reads them."""
    legacy = DOCS_DIR / "index.json"
    target = _case_dir(DEFAULT_CASE)
    if not legacy.exists() or (target / "index.json").exists():
        return
    ref_ids = {doc_id for doc_id, _ in REFERENCE_FILES}
    target.mkdir(parents=True, exist_ok=True)
    index, taken = [], set(ref_ids)
    for rec in _read_json(legacy, []):
        src = DOCS_DIR / f"{rec['id']}.md"
        if not src.exists() or (rec["id"] in ref_ids and rec.get("source") == "corpus"):
            continue
        new = dict(rec)
        if new["id"] in taken:  # an old upload that collides with a reference ID (D6) gets the next free one
            n = 1
            while f"D{n}" in taken:
                n += 1
            new["id"] = f"D{n}"
        taken.add(new["id"])
        (target / f"{new['id']}.md").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
        index.append(new)
    _save_index(target, index)


def reset_documents():
    """Reset the active case's borrower file to its case folder (removes its uploads) and refresh the reference set."""
    _reset_case(active_case_id())
    _reset_reference()
    return list_documents()


def list_documents(case_id=None):
    cid = case_or_default(case_id or active_case_id())["id"]
    out = [{**r, "group": "borrower", "case_id": cid} for r in _index_of(_case_dir(cid))]
    out += [{**r, "group": "reference", "case_id": None} for r in _index_of(REF_DIR)]
    out.sort(key=lambda r: _id_num(r["id"]))
    return out


def _doc_file(rec):
    folder = REF_DIR if rec["group"] == "reference" else _case_dir(rec["case_id"])
    return folder / f"{rec['id']}.md"


def get_document(doc_id, case_id=None):
    for rec in list_documents(case_id):
        if rec["id"] == doc_id:
            md = _doc_file(rec).read_text(encoding="utf-8")
            return {**rec, "markdown": md, "anchors": anchors_of(md)}
    return None


def _next_doc_id(taken, filename):
    m = re.match(r"(D\d+)", filename)
    if m and m.group(1) not in taken:
        return m.group(1)
    n = 1
    while f"D{n}" in taken:
        n += 1
    return f"D{n}"


def docx_to_markdown(data_bytes, filename):
    import io
    from docx import Document
    from docx.table import Table
    from docx.text.paragraph import Paragraph

    doc = Document(io.BytesIO(data_bytes))
    lines = []
    for child in doc.element.body.iterchildren():
        tag = child.tag.split("}")[-1]
        if tag == "p":
            p = Paragraph(child, doc)
            text = p.text.strip()
            if not text:
                continue
            style = p.style.name if p.style is not None else ""
            if style == "Title":
                lines.append(f"# {text}")
            elif style.startswith("Heading"):
                level = re.sub(r"\D", "", style) or "1"
                lines.append("#" * (int(level) + 1) + " " + text)
            elif style.startswith("List"):
                lines.append(f"- {text}")
            else:
                lines.append(text)
            lines.append("")
        elif tag == "tbl":
            t = Table(child, doc)
            rows = [[c.text.strip().replace("|", "/") for c in r.cells] for r in t.rows]
            if rows:
                lines.append("| " + " | ".join(rows[0]) + " |")
                lines.append("|" + "---|" * len(rows[0]))
                for r in rows[1:]:
                    lines.append("| " + " | ".join(r) + " |")
                lines.append("")
    md = "\n".join(lines).strip() + "\n"
    if not md.startswith("# "):
        md = f"# {Path(filename).stem}\n\n" + md
    return md


def add_document(filename, data_bytes):
    ext = Path(filename).suffix.lower()
    if ext == ".docx":
        md = docx_to_markdown(data_bytes, filename)
    elif ext in (".md", ".txt", ".markdown"):
        md = data_bytes.decode("utf-8", errors="replace")
        if not md.lstrip().startswith("#"):
            md = f"# {Path(filename).stem}\n\n" + md
    else:
        raise ValueError(f"Unsupported file type: {ext or 'none'} (use .docx, .md or .txt)")
    cid = active_case_id()
    folder = _case_dir(cid)
    index = _index_of(folder)
    taken = {r["id"] for r in index} | {r["id"] for r in _index_of(REF_DIR)}
    doc_id = _next_doc_id(taken, Path(filename).name)
    folder.mkdir(parents=True, exist_ok=True)
    (folder / f"{doc_id}.md").write_text(md, encoding="utf-8")
    rec = _doc_record(doc_id, md, Path(filename).name, "upload")
    index.append(rec)
    _save_index(folder, index)
    return {**rec, "group": "borrower", "case_id": cid}


def delete_document(doc_id):
    """Remove a document from the active case's borrower file. The Meridian reference set is fixed."""
    if any(r["id"] == doc_id for r in _index_of(REF_DIR)):
        raise PermissionError(f"{doc_id} is a Meridian reference document and is fixed.")
    folder = _case_dir(active_case_id())
    index = [r for r in _index_of(folder) if r["id"] != doc_id]
    p = folder / f"{doc_id}.md"
    if p.exists():
        p.unlink()
    _save_index(folder, index)


def corpus_text(case_id=None):
    """The reference set plus the case's borrower file (default: the active case), ordered by ID."""
    parts = []
    for rec in list_documents(case_id):
        md = _doc_file(rec).read_text(encoding="utf-8").strip()
        parts.append(f"===== BEGIN {rec['id']} ({rec['filename']}) =====\n{md}\n===== END {rec['id']} =====")
    return "\n\n".join(parts)


# ---------------------------------------------------------------- settings and prompt versions

def read_system_prompt():
    return SYSTEM_PROMPT_FILE.read_text(encoding="utf-8")


def spec_default_prompt():
    """The verbatim system prompt from Section 3 of the spec, if the spec file is present."""
    if SPEC_FILE.exists():
        spec = SPEC_FILE.read_text(encoding="utf-8")
        m = re.search(r"## 3\. SYSTEM PROMPT.*?```\n(.*?)```", spec, re.S)
        if m:
            return m.group(1)
    return read_system_prompt()


def default_presets():
    out = []
    for pid, label, fname, fallback in DEFAULT_PRESETS:
        p = PROMPTS_DIR / fname
        prompt = p.read_text(encoding="utf-8").strip() if p.exists() else fallback
        out.append({"id": pid, "label": label, "prompt": prompt})
    return out


def _version_index():
    return _read_json(VERSIONS_DIR / "index.json", [])


def save_prompt_version(text, note):
    index = _version_index()
    base = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    vid = base
    n = 2
    while any(v["version_id"] == vid for v in index):
        vid = f"{base}-{n}"
        n += 1
    (VERSIONS_DIR / f"{vid}.md").write_text(text, encoding="utf-8")
    index.insert(0, {"version_id": vid, "saved_at": now(), "note": note, "chars": len(text)})
    _write_json(VERSIONS_DIR / "index.json", index)
    return vid


DEFAULT_MODEL = "claude-sonnet-5-5"       # drafts the answer
DEFAULT_CLEANUP_MODEL = "claude-haiku-5-5"  # concision pass; empty string turns it off


def get_settings():
    s = _read_json(SETTINGS_FILE, {})
    return {"system_prompt": read_system_prompt(), "presets": s.get("presets") or default_presets(),
            "model": s.get("model") or DEFAULT_MODEL,
            "cleanup_model": s.get("cleanup_model", DEFAULT_CLEANUP_MODEL),
            "prompt_versions": _version_index()}


def update_settings(body):
    s = _read_json(SETTINGS_FILE, {})
    if "system_prompt" in body:
        note = (body.get("note") or "").strip()
        if not note:
            raise ValueError("A change note is required when saving the system prompt.")
        text = body["system_prompt"]
        if not text.strip():
            raise ValueError("The system prompt cannot be empty.")
        SYSTEM_PROMPT_FILE.write_text(text, encoding="utf-8")
        save_prompt_version(text, note)
    if "presets" in body:
        presets = body["presets"]
        if not isinstance(presets, list):
            raise ValueError("presets must be a list")
        s["presets"] = [{"id": str(p.get("id") or f"p{i}"), "label": str(p.get("label") or ""),
                         "prompt": str(p.get("prompt") or "")} for i, p in enumerate(presets)]
    if "model" in body:
        s["model"] = str(body["model"] or DEFAULT_MODEL)
    if "cleanup_model" in body:
        s["cleanup_model"] = str(body["cleanup_model"] or "")
    _write_json(SETTINGS_FILE, s)
    return get_settings()


def reset_system_prompt():
    text = spec_default_prompt()
    SYSTEM_PROMPT_FILE.write_text(text, encoding="utf-8")
    save_prompt_version(text, "Reset to spec default")
    return get_settings()


def restore_system_prompt(version_id):
    p = VERSIONS_DIR / f"{version_id}.md"
    if not p.exists():
        raise ValueError(f"Unknown version {version_id}")
    text = p.read_text(encoding="utf-8")
    SYSTEM_PROMPT_FILE.write_text(text, encoding="utf-8")
    save_prompt_version(text, f"Restored version {version_id}")
    return get_settings()


def current_prompt_version_id():
    index = _version_index()
    return index[0]["version_id"] if index else None


# ---------------------------------------------------------------- chats

def _chat_path(chat_id):
    return CHATS_DIR / f"{chat_id}.json"


def record_case_id(rec):
    """The case a chat or memo belongs to. Records made before cases existed are Larkspur."""
    cid = (rec or {}).get("case_id")
    return cid if get_case(cid) else DEFAULT_CASE


def list_chats(case_id=None):
    chats = []
    for p in CHATS_DIR.glob("c_*.json"):
        c = _read_json(p, None)
        if c:
            cid = record_case_id(c)
            if case_id and cid != case_id:
                continue
            chats.append({"id": c["id"], "name": c["name"], "created_at": c["created_at"],
                          "turns": len(c.get("messages", [])), "case_id": cid})
    chats.sort(key=lambda c: c["created_at"])
    return chats


def create_chat(name=None, case_id=None):
    chat_id = "c_" + uuid.uuid4().hex[:10]
    cid = case_id if get_case(case_id) else active_case_id()
    chat = {"id": chat_id, "name": (name or "New chat").strip() or "New chat", "created_at": now(),
            "case_id": cid, "messages": []}
    _write_json(_chat_path(chat_id), chat)
    return chat


def get_chat(chat_id):
    return _read_json(_chat_path(chat_id), None)


def save_chat(chat):
    _write_json(_chat_path(chat["id"]), chat)


def rename_chat(chat_id, name):
    chat = get_chat(chat_id)
    if not chat:
        return None
    chat["name"] = (name or "").strip() or chat["name"]
    save_chat(chat)
    return chat


def delete_chat(chat_id):
    p = _chat_path(chat_id)
    if p.exists():
        p.unlink()


# ---------------------------------------------------------------- memos
# One JSON file per memo under app/data/memos/. The section list mirrors D3 Part A (Template v1).
# author "M": machine-assembled, may be drafted by the assistant. "U": underwriter-authored, never drafted.
# "locked": Section 9, Risk Rating and Rationale. Only the person types into it; no tool writes it.

MEMO_SECTIONS = [
    ("1", "Transaction Summary", "M"),
    ("2", "Borrower Overview and Relationship History", "M"),
    ("3", "Financial Analysis", "M"),
    ("4", "Covenant Summary and Compliance", "M"),
    ("5", "Collateral and Guaranty", "M"),
    ("6", "Policy Compliance and Exceptions", "M"),
    ("7", "Key Risks and Mitigants", "U"),
    ("8", "Underwriter Analysis and Recommendation", "U"),
    ("9", "Risk Rating and Rationale", "locked"),
    ("10", "Conditions and Approvals", "U"),
]
MEMO_HEADER_KEYS = ("borrower", "request_type", "total_commitment", "underwriter", "senior_reviewer", "date")
MEMO_HEADER_DEFAULTS = {
    "borrower": "Larkspur Precision Components, Inc.",
    "request_type": "New-money increase to $18.0M senior secured facility",
    "total_commitment": "$18.0 million",
    "underwriter": "",
    "senior_reviewer": "",
    "date": "",
}
_MEMO_LOCK = threading.RLock()
_MEMO_ID_RE = re.compile(r"^m_[0-9a-f]{10}$")


def _memo_path(memo_id):
    if not _MEMO_ID_RE.match(str(memo_id or "")):
        return None
    return MEMOS_DIR / f"{memo_id}.json"


def _blank_section(sid, title, author):
    return {"id": sid, "title": title, "author": author, "status": "empty", "text": "", "drafted_text": "",
            "drafted_at": None, "edited_at": None, "model": None, "duration_ms": None, "run_id": None,
            "comments": []}


def memo_header_defaults(case_id):
    """Header prefill for a new memo: borrower, request type and total commitment come from the case."""
    case = case_or_default(case_id)
    return {**MEMO_HEADER_DEFAULTS, "borrower": case["borrower"], "request_type": case["request_type"],
            "total_commitment": case["total_commitment"]}


def list_memos(case_id=None):
    out = []
    for p in MEMOS_DIR.glob("m_*.json"):
        m = _read_json(p, None)
        if m:
            cid = record_case_id(m)
            if case_id and cid != case_id:
                continue
            secs = m.get("sections", [])
            out.append({"id": m["id"], "name": m["name"], "created_at": m["created_at"],
                        "updated_at": m.get("updated_at"),
                        "filled": sum(1 for s in secs if (s.get("text") or "").strip()),
                        "sections": len(secs), "case_id": cid})
    out.sort(key=lambda m: m["created_at"])
    return out


def create_memo(name=None, case_id=None):
    memo_id = "m_" + uuid.uuid4().hex[:10]
    ts = now()
    case = get_case(case_id) or get_case(active_case_id())
    memo = {"id": memo_id, "name": (name or "").strip() or f"{case['short']} credit memo", "created_at": ts,
            "updated_at": ts, "case_id": case["id"], "header": memo_header_defaults(case["id"]),
            "sections": [_blank_section(*row) for row in MEMO_SECTIONS]}
    with _MEMO_LOCK:
        _write_json(_memo_path(memo_id), memo)
    return memo


def get_memo(memo_id):
    p = _memo_path(memo_id)
    return _read_json(p, None) if p else None


def _save_memo(memo):
    memo["updated_at"] = now()
    _write_json(_memo_path(memo["id"]), memo)
    return memo


def update_memo(memo_id, name=None, header=None):
    with _MEMO_LOCK:
        memo = get_memo(memo_id)
        if not memo:
            return None
        if name is not None and str(name).strip():
            memo["name"] = str(name).strip()
        if isinstance(header, dict):
            for k, v in header.items():
                if k in MEMO_HEADER_KEYS:
                    memo["header"][k] = str(v if v is not None else "").strip()
        return _save_memo(memo)


def delete_memo(memo_id):
    p = _memo_path(memo_id)
    with _MEMO_LOCK:
        if p and p.exists():
            p.unlink()


def memo_section(memo, sid):
    for s in (memo or {}).get("sections", []):
        if s["id"] == str(sid):
            return s
    return None


def save_section_text(memo_id, sid, text):
    """An edit typed by the person. Returns (memo, section), or (None, None) if not found."""
    text = str(text or "").replace("\r\n", "\n")
    with _MEMO_LOCK:
        memo = get_memo(memo_id)
        sec = memo_section(memo, sid)
        if not sec:
            return None, None
        sec["text"] = text
        if not text.strip():
            sec["status"] = "empty"
        elif sec.get("drafted_text") and text.strip() == sec["drafted_text"].strip():
            sec["status"] = "drafted"
        else:
            sec["status"] = "edited"
        sec["edited_at"] = now()
        _save_memo(memo)
        return memo, sec


_DISCLAIMER_RE = re.compile(r"^\s*Drafting aid only\.[^\n]*\n*")
_S9_LINE_RE = re.compile(r"\n*[>#*_\s-]*Section 9 Risk Rating and Rationale\s*:[^\n]*\s*$", re.I)


def memo_text_from_draft(text, sid):
    """Fit an assistant section draft into the memo: drop the chat disclaimer, the duplicate
    '## Section N: Title' heading (the memo supplies it) and the closing Section 9 boundary line
    (Section 9 has its own card). The full response stays in the run log."""
    t = str(text or "").replace("\r\n", "\n").strip()
    t = _DISCLAIMER_RE.sub("", t, count=1).strip()
    t = re.sub(r"^#{1,6}\s*(?:Section\s+)?" + re.escape(str(sid)) + r"\b[^\n]*\n+", "", t, count=1,
               flags=re.I).strip()
    t = _S9_LINE_RE.sub("", t).strip()
    return t + "\n" if t else ""


def save_section_draft(memo_id, sid, text, model, run_id, duration_ms):
    """Store a machine draft. Refuses anything but an [M] section: no tool writes into U or locked."""
    with _MEMO_LOCK:
        memo = get_memo(memo_id)
        sec = memo_section(memo, sid)
        if not sec:
            return None, None
        if sec.get("author") != "M":
            raise PermissionError(f"Section {sid} is underwriter-only and cannot be written by a tool.")
        body = memo_text_from_draft(text, sid)
        sec.update({"text": body, "drafted_text": body, "status": "drafted" if body.strip() else "empty",
                    "drafted_at": now(), "model": model, "run_id": run_id, "duration_ms": duration_ms})
        _save_memo(memo)
        return memo, sec


def add_comment(memo_id, sid, text, author=None):
    text = str(text or "").strip()
    if not text:
        raise ValueError("Comment text is required.")
    with _MEMO_LOCK:
        memo = get_memo(memo_id)
        sec = memo_section(memo, sid)
        if not sec:
            return None
        c = {"id": "k_" + uuid.uuid4().hex[:8], "author": (str(author or "").strip() or "Underwriter"),
             "text": text, "at": now(), "resolved": False}
        sec.setdefault("comments", []).append(c)
        _save_memo(memo)
        return c


def update_comment(memo_id, sid, cid, resolved=None, text=None):
    with _MEMO_LOCK:
        memo = get_memo(memo_id)
        sec = memo_section(memo, sid)
        if not sec:
            return None
        for c in sec.get("comments", []):
            if c["id"] == cid:
                if resolved is not None:
                    c["resolved"] = bool(resolved)
                if text is not None and str(text).strip():
                    c["text"] = str(text).strip()
                _save_memo(memo)
                return c
        return None


def delete_comment(memo_id, sid, cid):
    with _MEMO_LOCK:
        memo = get_memo(memo_id)
        sec = memo_section(memo, sid)
        if not sec:
            return False
        before = len(sec.get("comments", []))
        sec["comments"] = [c for c in sec.get("comments", []) if c["id"] != cid]
        if len(sec["comments"]) == before:
            return False
        _save_memo(memo)
        return True


def bullets_under(md, phrase):
    """Every bullet that follows a non-bullet line containing `phrase` (case-insensitive)."""
    lines = str(md or "").replace("\r\n", "\n").split("\n")
    bullet = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+(?:\[[ xX]\]\s+)?(.*)$")
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if phrase in line.lower() and not bullet.match(line):
            j = i + 1
            items = []
            while j < len(lines):
                nxt = lines[j]
                if not nxt.strip():
                    j += 1
                    continue
                m = bullet.match(nxt)
                if m:
                    items.append(m.group(1).strip())
                elif items and re.match(r"^\s{2,}\S", nxt):
                    items[-1] += " " + nxt.strip()
                else:
                    break
                j += 1
            out.extend(items)
            i = j
            continue
        i += 1
    return out


def underwriter_to_complete(memo):
    """Bullets under any 'Underwriter to complete' line in the machine sections, as (section id, text)."""
    out = []
    for sec in (memo or {}).get("sections", []):
        if sec.get("author") != "M" or not (sec.get("text") or "").strip():
            continue
        for item in bullets_under(sec["text"], "underwriter to complete"):
            out.append((sec["id"], item))
    return out


# ---------------------------------------------------------------- checklist grouping (Layer 1, no model call)
# The memo checklist is every bullet under "Underwriter to complete" in the drafted machine sections (45 for the
# Larkspur memo). group_checklist() sorts those items into five groups by fixed text rules, drops bullets that are
# only a sub-heading, turns a "gaps listed under ... above" pointer into the gaps it points to, and merges repeats.
# index.html has a JavaScript copy of the same rules (groupChecklist); keep the two in step.

CHECKLIST_GROUPS = [  # display order
    ("documents", "Documents to request"),
    ("conflicts", "Conflicts to resolve"),
    ("policy", "Policy items for judgment"),
    ("sections", "Sections to write"),
    ("other", "Other checks"),
]
_NIPD = "Not in provided documents"
_CL_CITE_RE = re.compile(r"\[\s*D\d+\s*,[^\[\]\n]*\]")
_CL_BULLET_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_CL_POLICY_RE = re.compile(r"policy|exception|senior review\b|senior loan committee|concentration", re.I)
_CL_D4_RE = re.compile(r"\bD4\b")
_CL_SECTIONS_RE = re.compile(r"\bSections?\s+(?:3\.5|7|8|9|10)(?![\d]|\.\d)|underwriter-authored|underwriter commentary", re.I)
_CL_POINTER_RE = re.compile(r"gaps listed under\s+[\"“](.+?)[\"”]\s+above", re.I)
_CL_NIPD_RE = re.compile(r"\*\*Not in provided documents:?\*\*:?|__Not in provided documents:?__:?|Not in provided documents:?")
_CL_FIG_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d+(?=\s?%)|\d{4,}")
_CL_QUOTE_RE = re.compile(r"[\"“]([^\"“”]{3,}?)[\"”]")


def _cl_plain(text):
    return re.sub(r"[*_`]", "", str(text or "")).strip()


def checklist_group_of(text):
    """The group for one item: the first rule that matches, checked in this order: documents, conflicts,
    sections to write, policy, other. (Sections come before policy, so "address concentration in Section 7"
    is a section to write.)"""
    t = str(text or "")
    if _NIPD in t:
        return "documents"
    if "CONFLICT" in t:
        return "conflicts"
    if _CL_SECTIONS_RE.search(t):
        return "sections"
    if _CL_D4_RE.search(t) or _CL_POLICY_RE.search(t):
        return "policy"
    return "other"


def checklist_key(text):
    """De-duplication key: lowercase, citations and punctuation removed, first 60 characters."""
    t = _CL_CITE_RE.sub(" ", str(text or "")).lower()
    t = re.sub(r"[^a-z0-9\s]", "", t)
    return re.sub(r"\s+", " ", t).strip()[:60]


def checklist_cites(text):
    """The sources cited in an item. A bracket with several sources ([D1, §5; D4, §4.2.4]) counts once per source."""
    out = []
    for c in _CL_CITE_RE.findall(str(text or "")):
        for part in c.strip("[]").split(";"):
            part = re.sub(r"\s+", " ", part).strip()
            if part and part not in out:
                out.append(part)
    return out


def _cl_figures(text):
    """Figure-like numbers in an item, leaving out four-digit years."""
    t = _CL_CITE_RE.sub(" ", str(text or ""))
    return {n for n in _CL_FIG_RE.findall(t) if not re.fullmatch(r"(19|20)\d\d", n)}


def _cl_quotes(text):
    """Quoted phrases of two or more words, lowercased."""
    return {q.strip().lower().rstrip(".,") for q in _CL_QUOTE_RE.findall(str(text or "")) if len(q.split()) >= 2}


def _is_subheading(text):
    """A bullet that is only a bold label ending in a colon, such as '**Definition differences for review:**'."""
    t = str(text or "").strip()
    return bool(re.fullmatch(r"(\*\*|__)[^*_]+(\*\*|__):?", t)) and _cl_plain(t).endswith(":")


def _pointer_gaps(section_text, heading):
    """The 'Not in provided documents' paragraphs under a bold or # heading of a section."""
    out, inside = [], False
    for line in str(section_text or "").replace("\r\n", "\n").split("\n"):
        s = line.strip()
        if re.fullmatch(r"#{1,6}\s+.+|(\*\*|__)[^*_]+(\*\*|__):?", s):
            if inside:
                break
            inside = _cl_plain(re.sub(r"^#{1,6}\s*", "", s)).rstrip(":").strip().lower() == heading.strip().lower()
            continue
        if inside and s.startswith(_NIPD) and not _CL_BULLET_RE.match(line):
            out.append(s)
    return out


def _documents_text(text):
    """A document item without the phrase 'Not in provided documents': what is missing and where it would be."""
    t = str(text or "")
    m = _CL_NIPD_RE.search(t)
    if not m:
        return t.strip()
    left, right = t[:m.start()].rstrip(), t[m.end():].lstrip()
    right = right[:1].upper() + right[1:]
    return (left + " " + right).strip() if left else right.strip()


def _ws(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def _first_sentence(text):
    m = re.search(r"\.[\"”]?(?=\s|$)", text)
    return text[:m.end()].strip() if m else text.strip()


def _pointer_item(gaps, heading):
    """One document item that lists the gaps a pointer item refers to (first sentence of each), with their citations."""
    parts = [_first_sentence(_documents_text(g)).rstrip(".") for g in gaps]
    cites = list(dict.fromkeys(c for g in gaps for c in _CL_CITE_RE.findall(g)))
    body = "; ".join(parts)
    end = "" if re.search(r"[.!?][\"”]?$", body) else "."
    return f"{_NIPD}: {heading.strip()}: {body}{end}" + "".join(" " + c for c in cites)


def group_checklist(memo):
    """Layer 1 grouping, no model call. Returns {original_count, count, removed: {subheadings, duplicates},
    pointers, groups: [{key, title, items: [{text, group, sections: [ids], cites, also_cites}]}]} in display order.
    also_cites holds the bracket citations of merged repeats that the kept text does not already have.

    Two items are merged (the first is kept and records the other's section) when they have the same key, or
    when they are in the same group, cite at least one common source and also share either two figures or a
    quoted phrase, or cite the same set of two or more sources."""
    raw = underwriter_to_complete(memo)
    texts = {s["id"]: s.get("text") or "" for s in (memo or {}).get("sections", [])}
    entries, subheadings, pointers = [], 0, 0
    for sid, text in raw:
        if _is_subheading(text):
            subheadings += 1
            continue
        m = _CL_POINTER_RE.search(text)
        if m:
            gaps = _pointer_gaps(texts.get(sid, ""), m.group(1))
            if gaps:
                pointers += 1
                entries.append((sid, _pointer_item(gaps, m.group(1)), True))
                continue
        entries.append((sid, text, False))
    kept, by_key, duplicates = [], {}, 0
    for sid, text, is_pointer in entries:
        group = checklist_group_of(text)
        shown = _documents_text(text) if group == "documents" else text.strip()
        key = checklist_key(shown)
        cites = checklist_cites(text)
        figs, quotes, low = _cl_figures(text), _cl_quotes(text), _cl_plain(text).lower()
        hit = by_key.get(key)
        if hit is None and not is_pointer:  # a pointer item lists several gaps; it is never merged into one
            for it in kept:
                if it["group"] != group or it["_pointer"]:
                    continue
                shared = set(cites) & set(it["cites"])
                if not shared:
                    continue
                if (len(shared) >= 2 and set(cites) == set(it["cites"])) or len(figs & it["_figs"]) >= 2 \
                        or any(q in it["_low"] for q in quotes) or any(q in low for q in it["_quotes"]):
                    hit = it
                    break
        if hit is not None:
            if sid not in hit["sections"]:
                hit["sections"].append(sid)
            for c in _CL_CITE_RE.findall(text):  # keep the evidence of the repeat: citations the kept item lacks
                if _ws(c) not in _ws(hit["text"]) and c not in hit["also_cites"]:
                    hit["also_cites"].append(c)
            duplicates += 1
            continue
        item = {"text": shown, "group": group, "sections": [sid], "cites": cites, "also_cites": [],
                "_figs": figs, "_quotes": quotes, "_low": low, "_pointer": is_pointer}
        kept.append(item)
        by_key[key] = item
    for it in kept:
        for k in ("_figs", "_quotes", "_low", "_pointer"):
            it.pop(k)
    groups = [{"key": k, "title": title, "items": [i for i in kept if i["group"] == k]} for k, title in CHECKLIST_GROUPS]
    return {"original_count": len(raw), "count": len(kept),
            "removed": {"subheadings": subheadings, "duplicates": duplicates}, "pointers": pointers,
            "groups": groups}


def save_checklist_consolidated(memo_id, data):
    """Store the accepted Layer 2 suggestions on the memo (replacing any earlier ones). Suggestions only: the
    section texts are not touched. Returns the stored dict, or None if the memo is gone."""
    with _MEMO_LOCK:
        memo = get_memo(memo_id)
        if not memo:
            return None
        memo["checklist_consolidated"] = data
        _save_memo(memo)
        return data


def clear_checklist_consolidated(memo_id):
    """Remove the stored suggestions. Returns False if the memo is not found."""
    with _MEMO_LOCK:
        memo = get_memo(memo_id)
        if not memo:
            return False
        if memo.pop("checklist_consolidated", None) is not None:
            _save_memo(memo)
        return True

# ---------------------------------------------------------------- runs

def record_run(chat, prompt, response, duration_ms, model, ok, run_id=None, error=None,
               draft=None, cleanup_status="off", cleanup_model=""):
    run_id = run_id or ("r_" + uuid.uuid4().hex[:10])
    case_id = record_case_id(chat)
    rec = {"run_id": run_id, "chat_id": chat["id"], "chat_name": chat["name"], "at": now(), "prompt": prompt,
           "response": response, "response_chars": len(response or ""), "duration_ms": duration_ms,
           "model": model, "ok": ok, "error": error, "system_prompt_version": current_prompt_version_id(),
           "case_id": case_id, "documents": [d["id"] for d in list_documents(case_id)],
           "cleanup_status": cleanup_status, "cleanup_model": cleanup_model, "draft": draft}
    _write_json(RUNS_DIR / f"{run_id}.json", rec)
    return rec


def list_runs():
    runs = []
    for p in RUNS_DIR.glob("r_*.json"):
        r = _read_json(p, None)
        if r:
            runs.append({k: r.get(k) for k in ("run_id", "chat_id", "chat_name", "at", "prompt", "response_chars",
                                               "duration_ms", "model", "ok")})
    runs.sort(key=lambda r: r["at"] or "", reverse=True)
    return runs


def get_run(run_id):
    return _read_json(RUNS_DIR / f"{run_id}.json", None)


def last_model():
    runs = list_runs()
    for r in runs:
        if r.get("ok") and r.get("model"):
            return r["model"]
    return None


# ---------------------------------------------------------------- eval

def eval_summary():
    """The harness summary plus the headline score parsed from it (passed, total, model, run_started)."""
    out = {"markdown": "", "updated_at": None, "passed": None, "total": None, "model": None, "run_started": None,
           "runs_per_case": None}
    if not EVAL_SUMMARY.exists():
        return out
    md = EVAL_SUMMARY.read_text(encoding="utf-8")
    out["markdown"] = md
    out["updated_at"] = dt.datetime.fromtimestamp(EVAL_SUMMARY.stat().st_mtime).replace(microsecond=0).isoformat()
    m = re.search(r"\*\*(\d+) of (\d+) PASS\.\*\*", md)
    if m:
        out["passed"], out["total"] = int(m.group(1)), int(m.group(2))
    m = re.search(r"^Model: (.+)$", md, re.M)
    if m:
        out["model"] = m.group(1).strip()
    m = re.search(r"^Run started: (.+)$", md, re.M)
    if m:
        out["run_started"] = m.group(1).strip()
    m = re.search(r"runs per case: (\d+)", md)
    if m:
        out["runs_per_case"] = int(m.group(1))
    # Does the current system prompt still match the one the eval summary was written against?
    import hashlib
    current = hashlib.sha256(read_system_prompt().encode("utf-8")).hexdigest()[:12]
    m = re.search(r"^Prompt sha256: ([0-9a-f]{12})", md, re.M)
    out["prompt_sha"] = m.group(1) if m else None
    out["prompt_matches"] = (m.group(1) == current) if m else None
    return out
