# Eval summary

Model: claude-fable-5-1
Run started: 2026-10-07 22:40:22
Cases file: cases_demo_moves.json; runs per case: 1; mode: live
Harness: claude -p with system_prompt.md, --tools "" (no tools), --output-format json, empty working directory

| ID | Category | Prompt (short) | Expected | Observed (first 200 characters) | Pass/Fail | Notes |
|---|---|---|---|---|---|---|
| M3 | demo-move | Extract the covenants from the loan agreement into a review ... | Six rows: 7.1 High with the 3.00x step-down, 7.2 High, 7.3 Medium (Schedule 1.1 missing), 7.4 High, 7.5 High, 7.6 Low (undefined terms). Items for legal review below. | Drafting aid only. I work only from the documents in this project, cite every fact, and do not rate risk or recommend credit decisions. Verify citations before use.  ## Covenant Extraction: Draft Amen... | PASS |  |

**1 of 1 PASS.**
