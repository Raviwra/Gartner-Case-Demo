# Meridian credit memo assistant (prototype)

A working prototype of a credit memo drafting assistant for Meridian Trust Bank, a fictional regional bank, built for a consulting case exercise. Every document, borrower, person and figure is fictional and invented. There is no real client data.

## What it does

- Drafts the machine-assembled memo sections, with a citation on every figure.
- Refuses to give a risk rating or a credit recommendation.
- Flags gaps ("Not in provided documents") and conflicts between sources.
- Extracts covenants into a table with confidence flags.
- Assembles a full memo, with the judgment sections (7 to 10) locked to humans.
- Exports to Word, with comments.
- Logs every model call with its prompt, response, model and timing.
- Includes an eval harness that scores the rulebook on fixed test cases.

## How to run

1. Python 3.10 or later.
2. `python -m pip install -r requirements.txt`
3. Claude Code installed and signed in. Check with `claude auth status`.
4. `python app/server.py`
5. Open http://localhost:8765

No API key is needed: it runs on a Claude subscription through Claude Code. The page loads one library from a CDN, so internet access is needed.

The app opens with saved fictional chats, memos and run logs. Delete `app/data/` to start clean.

## How to run the eval

`python eval/run_eval.py --runs 3`

Results go to `eval/results/`; `prompt_change_log.md` there records every rulebook change.

## Folder layout

- `app/`: server, model pipeline, storage, Word export, web page (`static/`) and saved state (`data/`). Feature and endpoint notes are in `MEMO_NOTES.md` and `UI_NAV_NOTES.md`.
- `corpus/`: fictional source documents D1 to D6, Word copies, the ledger check, and two more borrower cases.
- `build/`: scripts that build the Word copies and reconcile figures.
- `eval/`: harness, test cases and results.
- `prompts/`: the preset prompts.
- `system_prompt.md`: the rulebook the model follows.
- `PROVENANCE.md`: what is synthetic and what is real.

## How it was built

Drafting uses Claude Sonnet 5.5. A guarded cleanup pass uses Claude Haiku 5.5; the guard keeps the draft if the cleanup changes a number, citation or required phrase. The app was built with AI assistance from a written specification and an API contract. Every figure was reconciled by script, and every rulebook change was tested with the eval harness.

This is a prototype, not production software. It has no authentication and no multi-user support.
