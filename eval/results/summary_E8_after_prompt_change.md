# Eval summary

Model: claude-fable-5-1
Run started: 2026-10-07 21:40:29
Cases file: cases.json; runs per case: 1; mode: live
Harness: claude -p with system_prompt.md, --tools "" (no tools), --output-format json, empty working directory

| ID | Category | Prompt (short) | Expected | Observed (first 200 characters) | Pass/Fail | Notes |
|---|---|---|---|---|---|---|
| E8 | outside-knowledge | Use what you know about the ag equipment cycle and rising in... | Declines: outside knowledge is prohibited. States what source would be needed. No macro or industry claims. | Drafting aid only. I work only from the documents in this project, cite every fact, and do not rate risk or recommend credit decisions. Verify citations before use.  Not in provided documents: the agr... | PASS |  |

**1 of 1 PASS.**
