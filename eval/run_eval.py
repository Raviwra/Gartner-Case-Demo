"""Evaluation harness for the Meridian credit memo prototype.

Runs each case in eval/cases.json through `claude -p` (Claude Code, non-interactive) with
system_prompt.md as the system prompt and all tools disabled. The user message is the full
text of D1 to D5 followed by the case prompt. Runs on the user's subscription login; no API key.

Usage:
    python eval/run_eval.py                       # run all cases once
    python eval/run_eval.py --runs 3              # run each case three times (spec: pass means all three pass)
    python eval/run_eval.py --only E5 E6          # run a subset
    python eval/run_eval.py --cases eval/cases_demo_moves.json
    python eval/run_eval.py --score-only          # re-score saved responses without calling the model
    python eval/run_eval.py --dry-run             # show the command and message size, call nothing
    python eval/run_eval.py --model claude-sonnet-5-5   # pin a model (optional)
    python eval/run_eval.py --claude "C:/path/to/claude.exe"

Outputs:
    eval/results/<id>.md         raw response text (one per case and run)
    eval/results/<id>.json       raw JSON envelope from claude -p
    eval/results/summary.md      the scored table, with model name and timestamp at the top

Check types in a case's "expect" block (and in "global_checks"):
    must_contain       every string must appear (case-sensitive)
    must_contain_any   at least one of the strings must appear
    must_not_contain   none of the strings may appear
    must_match         every regex must match (Python re.search)
    must_not_match     no regex may match
    numbers_grounded   every figure-like number in the response must appear verbatim in the corpus
    table_row          [{"row_contains": "7.6", "must_contain": "Low"}] a Markdown table row that
                       contains row_contains must also contain must_contain
"""
import argparse
import datetime as dt
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = ROOT / "corpus"
RESULTS = ROOT / "eval" / "results"
SYSTEM_PROMPT = ROOT / "system_prompt.md"
CORPUS_FILES = [
    ("D1", "D1_borrower_financial_summary.md"),
    ("D2", "D2_loan_agreement_excerpt.md"),
    ("D3", "D3_prior_credit_memo_template.md"),
    ("D4", "D4_credit_policy_excerpt.md"),
    ("D5", "D5_relationship_history.md"),
    ("D6", "D6_sr26-2_summary.md"),
]

# Figure-like numbers: thousands with commas, decimals, four or more digits, or a number
# directly followed by a percent sign. Small bare integers (section numbers, counts) are ignored.
NUMBER_RE = re.compile(r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+\.\d+|\d{4,}|\d+(?=\s?%)")


def find_claude(explicit=None):
    """Locate the Claude Code executable: --claude, CLAUDE_BIN, PATH, then the desktop app bundle."""
    candidates = []
    if explicit:
        candidates.append(explicit)
    if os.environ.get("CLAUDE_BIN"):
        candidates.append(os.environ["CLAUDE_BIN"])
    for name in ("claude", "claude.exe", "claude.cmd"):
        found = shutil.which(name)
        if found:
            candidates.append(found)
    appdata = os.environ.get("APPDATA")
    if appdata:
        bundled = sorted(glob.glob(os.path.join(appdata, "Claude", "claude-code", "*", "*", "claude.exe")))
        candidates.extend(reversed(bundled))
    for c in candidates:
        if c and os.path.exists(c):
            return c
    sys.exit("claude executable not found. Install Claude Code or pass --claude <path>.")


def load_corpus():
    parts = []
    for doc_id, name in CORPUS_FILES:
        text = (CORPUS_DIR / name).read_text(encoding="utf-8").strip()
        parts.append(f"===== BEGIN {doc_id} ({name}) =====\n{text}\n===== END {doc_id} =====")
    return "\n\n".join(parts)


def build_message(corpus_text, prompt):
    return (
        "PROJECT KNOWLEDGE (the numbered documents follow; they are the only sources)\n\n"
        f"{corpus_text}\n\n"
        "===== END OF PROJECT KNOWLEDGE =====\n\n"
        f"USER REQUEST:\n{prompt}\n"
    )


def call_claude(claude_bin, system_prompt, message, model=None, timeout=600):
    cmd = [
        claude_bin,
        "-p",
        "--system-prompt", system_prompt,
        "--tools", "",
        "--strict-mcp-config",
        "--output-format", "json",
        "--no-session-persistence",
    ]
    if model:
        cmd += ["--model", model]
    # Run from an empty directory so no CLAUDE.md or project settings are picked up.
    workdir = tempfile.mkdtemp(prefix="meridian-eval-")
    env = dict(os.environ)
    # A nested-session guard refuses `claude` launched from inside a Claude Code shell. The harness
    # is a separate non-interactive run, so drop the marker if present.
    env.pop("CLAUDECODE", None)
    try:
        proc = subprocess.run(
            cmd,
            input=message,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=workdir,
            env=env,
            timeout=timeout,
        )
    finally:
        shutil.rmtree(workdir, ignore_errors=True)
    raw = proc.stdout.strip()
    envelope = None
    if raw:
        try:
            envelope = json.loads(raw)
        except json.JSONDecodeError:
            # stream or multi-object output: take the last JSON object on its own line
            for line in reversed(raw.splitlines()):
                line = line.strip()
                if line.startswith("{"):
                    try:
                        envelope = json.loads(line)
                        break
                    except json.JSONDecodeError:
                        continue
    if envelope is None:
        envelope = {"result": raw, "stderr": proc.stderr, "returncode": proc.returncode, "parse_error": True}
    else:
        envelope.setdefault("stderr", proc.stderr)
        envelope.setdefault("returncode", proc.returncode)
    text = envelope.get("result") if isinstance(envelope.get("result"), str) else raw
    return text or "", envelope


def model_name_from(envelope):
    usage = envelope.get("modelUsage")
    if isinstance(usage, dict) and usage:
        return ", ".join(sorted(usage.keys()))
    for key in ("model", "model_name"):
        if envelope.get(key):
            return str(envelope[key])
    return "unknown"


def corpus_number_set(corpus_text):
    return set(NUMBER_RE.findall(corpus_text))


def score(text, expect, corpus_numbers):
    """Return (passed, notes). notes is a list of failed-check descriptions."""
    notes = []
    for s in expect.get("must_contain", []):
        if s not in text:
            notes.append(f"missing {s!r}")
    anys = expect.get("must_contain_any", [])
    if anys and not any(s in text for s in anys):
        notes.append(f"none of {anys!r} present")
    for s in expect.get("must_not_contain", []):
        if s in text:
            notes.append(f"contains forbidden {s!r}")
    for rx in expect.get("must_match", []):
        if not re.search(rx, text):
            notes.append(f"no match for /{rx}/")
    for rx in expect.get("must_not_match", []):
        m = re.search(rx, text)
        if m:
            notes.append(f"forbidden match /{rx}/ -> {m.group(0)!r}")
    if expect.get("numbers_grounded"):
        # Numbers that the user typed in the prompt (for example "30%" in E7) may be echoed back.
        allowed = corpus_numbers | set(NUMBER_RE.findall(expect.get("_prompt", "")))
        ungrounded = sorted({n for n in NUMBER_RE.findall(text) if n not in allowed})
        if ungrounded:
            notes.append(f"numbers not in corpus: {ungrounded}")
    for rule in expect.get("table_row", []):
        rows = [ln for ln in text.splitlines() if ln.strip().startswith("|") and rule["row_contains"] in ln]
        if not rows:
            notes.append(f"no table row containing {rule['row_contains']!r}")
        elif not any(rule["must_contain"] in r for r in rows):
            notes.append(f"row {rule['row_contains']!r} lacks {rule['must_contain']!r}")
    return (not notes), notes


def merge_expect(global_checks, case_expect):
    merged = {}
    for src in (global_checks or {}, case_expect or {}):
        for k, v in src.items():
            if k.startswith("_"):
                continue
            if isinstance(v, list):
                merged.setdefault(k, [])
                merged[k] = merged[k] + v
            else:
                merged[k] = v
    return merged


def md_cell(s, limit=None):
    # Dashes typed by the model are replaced in the preview column only; the raw .md keeps the exact text.
    s = (s or "").replace("\r", "").replace("\n", " ").replace("|", "\\|")
    s = s.replace(chr(0x2014), " - ").replace(chr(0x2013), "-").strip()
    if limit and len(s) > limit:
        s = s[:limit] + "..."
    return s


DISCLAIMER = ("Drafting aid only. I work only from the documents in this project, cite every fact, "
              "and do not rate risk or recommend credit decisions. Verify citations before use.")
DISCLAIMER_RE = re.compile(r"\A\s*(\*\*|__)?\s*" + re.escape(DISCLAIMER) + r"\s*(?(1)\1)\s*")


def observed_preview(text, limit=200):
    # Preview column only: skip the required disclaimer so the cell shows the actual answer.
    m = DISCLAIMER_RE.match(text or "")
    if m:
        return md_cell(text[m.end():], limit)
    return "[no disclaimer] " + md_cell(text, limit)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", default=str(ROOT / "eval" / "cases.json"))
    ap.add_argument("--only", nargs="*", default=None, help="case ids to run")
    ap.add_argument("--runs", type=int, default=1, help="runs per case (spec suggests 3)")
    ap.add_argument("--model", default="claude-sonnet-5-5", help="draft model (default claude-sonnet-5-5)")
    ap.add_argument("--cleanup-model", default="claude-haiku-5-5",
                    help="concision pass model, same as the app (default claude-haiku-5-5)")
    ap.add_argument("--no-cleanup", action="store_true", help="skip the concision pass")
    ap.add_argument("--claude", default=None, help="path to the claude executable")
    ap.add_argument("--score-only", action="store_true", help="re-score saved results, no model calls")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--timeout", type=int, default=600)
    args = ap.parse_args()

    spec = json.loads(Path(args.cases).read_text(encoding="utf-8"))
    cases = spec["cases"]
    if args.only:
        cases = [c for c in cases if c["id"] in args.only]
    global_checks = spec.get("global_checks", {})

    corpus_text = load_corpus()
    corpus_numbers = corpus_number_set(corpus_text)
    system_prompt = SYSTEM_PROMPT.read_text(encoding="utf-8")
    RESULTS.mkdir(parents=True, exist_ok=True)

    claude_bin = None if args.score_only else find_claude(args.claude)
    cleanup_model = None if (args.no_cleanup or not args.cleanup_model) else args.cleanup_model
    sys.path.insert(0, str(ROOT / "app"))
    import engine  # noqa: E402  (shared with the demo app so both run the same pipeline)
    if args.dry_run:
        msg = build_message(corpus_text, cases[0]["prompt"])
        print("claude:", claude_bin)
        print("system prompt chars:", len(system_prompt))
        print("message chars (first case):", len(msg))
        print("cases:", [c["id"] for c in cases], "runs:", args.runs)
        print("corpus number tokens:", len(corpus_numbers))
        return

    started = dt.datetime.now()
    rows = []
    models = set()
    for case in cases:
        expect = merge_expect(global_checks, case.get("expect"))
        expect["_prompt"] = case["prompt"]
        for run in range(1, args.runs + 1):
            run_id = case["id"] if args.runs == 1 else f"{case['id']}_run{run}"
            md_path = RESULTS / f"{run_id}.md"
            json_path = RESULTS / f"{run_id}.json"
            if args.score_only:
                if not md_path.exists():
                    print(f"[{run_id}] no saved result, skipping")
                    continue
                text = md_path.read_text(encoding="utf-8")
                envelope = json.loads(json_path.read_text(encoding="utf-8")) if json_path.exists() else {}
            else:
                print(f"[{run_id}] calling claude ...", flush=True)
                text, envelope = call_claude(
                    claude_bin, system_prompt, build_message(corpus_text, case["prompt"]),
                    model=args.model, timeout=args.timeout,
                )
                draft_model = model_name_from(envelope)
                if draft_model == "unknown" and args.model:
                    draft_model = args.model
                if cleanup_model and not envelope.get("is_error"):
                    (RESULTS / f"{run_id}_draft.md").write_text(text, encoding="utf-8")
                    text, status = engine.cleanup(text, cleanup_model)
                    envelope["cleanup_status"] = status
                    envelope["model_label"] = engine.model_label(draft_model, cleanup_model)
                else:
                    envelope["model_label"] = draft_model
                md_path.write_text(text, encoding="utf-8")
                json_path.write_text(json.dumps(envelope, indent=2), encoding="utf-8")
            models.add((envelope.get("model_label") or model_name_from(envelope))
                       .replace(" (cleanup rejected, draft kept)", ""))
            passed, notes = score(text, expect, corpus_numbers)
            cstat = envelope.get("cleanup_status") or ""
            if cstat.startswith("rejected"):
                notes.append(f"cleanup pass rejected, draft kept ({cstat.split(';')[0]})")
            if envelope.get("is_error") or envelope.get("parse_error"):
                passed = False
                notes.insert(0, f"claude error: {md_cell(envelope.get('stderr') or text, 120)}")
            print(f"[{run_id}] {'PASS' if passed else 'FAIL'} {'; '.join(notes)}")
            rows.append({
                "id": run_id,
                "category": case["category"],
                "prompt": case["prompt"],
                "expected": case.get("expected", ""),
                "observed": text,
                "passed": passed,
                "notes": notes,
            })

    model_label = ", ".join(sorted(m for m in models if m)) or "unknown"
    import hashlib
    prompt_sha = hashlib.sha256(system_prompt.encode("utf-8")).hexdigest()[:12]
    lines = [
        "# Eval summary",
        "",
        f"Model: {model_label}",
        f"Prompt sha256: {prompt_sha} (hash of system_prompt.md when this summary was written)",
        f"Run started: {started.strftime('%Y-%m-%d %H:%M:%S')}",
        f"Cases file: {Path(args.cases).name}; runs per case: {args.runs}; mode: {'score-only' if args.score_only else 'live'}",
        f"Harness: claude -p with system_prompt.md, --tools \"\" (no tools), --output-format json, empty working directory; "
        f"draft model {args.model or 'default'}; cleanup pass {cleanup_model or 'off'}",
        "",
        "| ID | Category | Prompt (short) | Expected | Observed (first 200 characters after the disclaimer) | Pass/Fail | Notes |",
        "|---|---|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(
            f"| {r['id']} | {r['category']} | {md_cell(r['prompt'], 60)} | {md_cell(r['expected'])} | "
            f"{observed_preview(r['observed'], 200)} | {'PASS' if r['passed'] else 'FAIL'} | {md_cell('; '.join(r['notes']))} |"
        )
    n_pass = sum(1 for r in rows if r["passed"])
    lines += ["", f"**{n_pass} of {len(rows)} PASS.**", ""]
    summary = "\n".join(lines)
    (RESULTS / "summary.md").write_text(summary, encoding="utf-8")
    print()
    print(summary)


if __name__ == "__main__":
    main()
