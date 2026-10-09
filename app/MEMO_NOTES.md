# Memo view: notes

The Workspace has a two-way toggle, **Chat** (the original view, unchanged) and **Memo**. Memo shows the whole credit memo in the D3 Part A (Template v1) structure as an editable document with comments, and exports it to Word. The choice is remembered in localStorage (`meridian.wsMode`), as are the open memo (`meridian.memoId`) and the Review panel collapse state (`meridian.reviewCollapsed`). Every localStorage call is inside try/catch.

Restart the server after pulling these changes. A server that was already running keeps the old code and has no memo endpoints.

## Who writes what

| Section | Author | What the app allows |
|---|---|---|
| 1 Transaction Summary | M | Draft, Redraft, Edit |
| 2 Borrower Overview and Relationship History | M | Draft, Redraft, Edit |
| 3 Financial Analysis | M (hybrid) | One machine block. The assistant drafts 3.1 to 3.4 and leaves 3.5 Underwriter Commentary for the underwriter (Edit) |
| 4 Covenant Summary and Compliance | M | Draft, Redraft, Edit |
| 5 Collateral and Guaranty | M | Draft, Redraft, Edit |
| 6 Policy Compliance and Exceptions | M | Draft, Redraft, Edit |
| 7 Key Risks and Mitigants | U | Edit only |
| 8 Underwriter Analysis and Recommendation | U | Edit only |
| 9 Risk Rating and Rationale | locked | Edit only, by the person. No tool writes here |
| 10 Conditions and Approvals | U | Edit only |

Section 9 is protected three ways: the page renders no Draft control for U or locked sections; the draft endpoint returns 400 ("Section 9 is underwriter-only and cannot be drafted by a tool."); and `store.save_section_draft` raises if asked to store a machine draft in anything but an M section. The only write path into Section 9 is `PUT .../sections/9`, which the page calls when the person presses Save in the Section 9 editor.

The draft prompt for a machine section is fixed: `Draft Section N, <Title>, for <case name>.` (for the original memos, `... for Larkspur Precision Components.`; see "Borrower cases" below). It is sent with the memo's case corpus and no chat history, through the same pipeline as chat messages (Sonnet draft, Haiku cleanup with the same guard).

## Data model

One JSON file per memo: `app/data/memos/<memo_id>.json` (ids look like `m_` plus 10 hex characters).

```
id, name, created_at, updated_at,
header: {borrower, request_type, total_commitment, underwriter, senior_reviewer, date},
sections: [ {id "1".."10", title, author "M" | "U" | "locked", status "empty" | "drafted" | "edited",
             text (Markdown), drafted_text, drafted_at, edited_at, model, duration_ms, run_id,
             comments: [{id, author, text, at, resolved}]} ]
```

New memos prefill borrower, request type and total commitment from the memo's case (Larkspur: "Larkspur Precision Components, Inc.", "New-money increase to $18.0M senior secured facility", "$18.0 million"); the other header fields start empty. Memos also carry `case_id` (see "Borrower cases" below).

`drafted_text` is the last machine draft, kept so a save can tell "edited" from "drafted": a saved text equal to the draft is "drafted", a different non-blank text is "edited", a blank text is "empty".

When a draft is stored in a section, three things are removed from the model's response because the memo already supplies them: the chat disclaimer line ("Drafting aid only..."), the leading "## Section N: Title" heading, and the closing line "Section 9 Risk Rating and Rationale: underwriter only, required." (Section 9 has its own card). The full, unmodified response is in the run log.

Each draft is recorded as a normal run in `app/data/runs/` with `chat_id` "memo:<memo_id>" and `chat_name` "Memo: <memo name> / Section N", so it shows in the Run log tab with the other runs. `record_run` was not changed; the server passes it a small dict with `id` and `name`.

## Endpoints

All JSON. Errors are `{"error": msg}` with 400 or 404.

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | /api/memos | | list: id, name, created_at, updated_at, filled, sections |
| POST | /api/memos | {name?} | the new memo |
| GET | /api/memos/{id} | | memo |
| PATCH | /api/memos/{id} | {name?, header?} | memo (unknown header keys are ignored) |
| DELETE | /api/memos/{id} | | {ok: true} |
| PUT | /api/memos/{id}/sections/{sid} | {text} | section |
| POST | /api/memos/{id}/sections/{sid}/draft | | text/event-stream: start, delta, status, done, error (same as chat). `done` carries `section`. 400 for U and locked sections |
| POST | /api/memos/{id}/sections/{sid}/comments | {text, author?} | comment (author defaults to "Underwriter") |
| PATCH | /api/memos/{id}/sections/{sid}/comments/{cid} | {resolved?, text?} | comment |
| DELETE | /api/memos/{id}/sections/{sid}/comments/{cid} | | {ok: true} |
| GET | /api/memos/{id}/export.docx | | Word file, `Content-Disposition: attachment; filename="<memo name>.docx"` |
| POST | /api/memos/{id}/checklist/consolidate | | JSON, not streamed (about 40 to 50 s): `{status: "accepted", checklist_consolidated}`, or `{status: "rejected" or "failed", reason, run_id, duration_ms}`. 400 if the memo has no checklist items |
| DELETE | /api/memos/{id}/checklist/consolidate | | {ok: true}. Removes the stored suggestion |

The server now reads `PORT` from the environment (default 8765), so a second copy can run for testing: `PORT=8766 python app/server.py`.

## Word export (app/memo_docx.py)

python-docx 1.2.0 is installed, so `Document.add_comment` is available and **comments are real Word comments**, anchored to the "Section N: Title" heading of their section, with the stored author and initials. Resolved comments are prefixed "[Resolved]" (python-docx cannot set Word's resolved flag). With an older python-docx the export falls back to a final "Review comments" section.

Order of the document:
1. Title "Meridian Trust Bank, Commercial Credit Memo (Template v1)", the memo name, and the header-field table. Empty header fields read "Underwriter to complete" in yellow.
2. "Underwriter to complete (consolidated)": if the memo has a stored suggestion (`checklist_consolidated`), the page shows it under a gray label "AI suggestions, not applied. The underwriter decides.", one heading per group, request lines in small gray italics, and a "Dropped as duplicate or filler: N items" list. Otherwise it shows the grouped checklist (see "Underwriter to complete: grouping and AI suggestions" below), each item prefixed with the sections it came from. Page break.
3. Sections 1 to 10, each under Heading 1 "Section N: Title".
   - Machine section with text: a small gray label "Machine-assembled, cited" (light blue "Machine-assembled, cited. Edited by the underwriter." if edited), the Markdown converted to Word (headings, paragraphs, bullets, numbered lists, pipe tables as real Table Grid tables, **bold**; citations stay as plain bracket text), then an italic line with the model and draft time.
   - Machine section with no text: yellow "Not yet drafted: <title>...".
   - Section 3 without a 3.5 heading in its text: a "3.5 Underwriter Commentary" heading and a yellow placeholder.
   - Underwriter section with no text: yellow "Underwriter to complete: <title>."
   - Section 9 with no text: yellow "Underwriter only. Required. Not drafted or pre-populated by any tool."
   - Any underwriter or Section 9 text the person typed: a light-blue shaded "Underwriter-authored" label, then the text.
4. Footer on every page: "FICTIONAL - prepared for case exercise. All documents, people and figures are invented."

The export code writes no rating, score or recommendation. Section 9 in the export contains only what the person typed, or the placeholder.

## Front end (index.html)

- Toggle "Chat | Memo" in a slim bar at the top of the Workspace. Chat view is unchanged.
- Memo bar: memo name (rename inline), saved-memo selector, New memo, Delete (with confirm). If no memo exists, one is created on first open.
- Toolbar: "Draft all machine sections" (Sections 1 to 6 one after another, progress line "Drafting Section 4 (4 of 6 machine sections)", "Stop after this section" stops between sections; asks before replacing existing text), "Export to Word".
- Header fields: six inputs, saved on blur (change).
- Section cards: number and title; author badge ("Machine-assembled, cited", "Underwriter", "Underwriter only. Required."); status chip (Empty, Drafted, Edited); Draft or Redraft for M sections (streams into the card, then shows model, duration and time); Edit for every section (textarea with Save and Cancel; Ctrl+Enter saves). Redrafting an edited section asks first. Text renders with `richHTML`, so citation chips open the Sources reader and CONFLICT / "Not in provided documents" highlights apply.
- Judgment areas (Sections 7, 8, 9, 10): Sunstone left bar and light Sunstone tint, with the badge word always visible. No icons.
- Comments strip on every card: count, list (author, time, text, Resolve or Reopen, delete with confirm), add box with a Comment button (Enter adds).
- Review pane in Memo mode: the "Underwriter to complete" tab shows the checklist grouped by code, the AI suggestions when there are any, a "Show original list" toggle, and "Underwriter sections still blank". Run log and Eval tabs are unchanged. See the last section.
- Review panel collapse: a quiet "Collapse" ghost button (chevron plus word, Gartner Blue text, accessible name "Collapse Review panel") in the Review header. Collapsed, the Review region becomes a 44 px rail with an "Expand" button and a vertical "Review" label, and the Workspace takes the width. The tabs, `#reviewBody` and every other Review element stay in the DOM, only hidden. Clicking the Eval pill expands the panel.

## What was tested (port 8766, own server)

- `python -m py_compile` on server.py, store.py and memo_docx.py; inline script extracted and checked with `node --check`; all pre-existing element ids present exactly once; no em or en dashes in the touched files.
- Created a memo ("Test memo 8766", id m_c4a4d2b734): header prefilled as specified; 10 sections with the right authors.
- Draft refusals: Section 9 returned 400 with "Section 9 is underwriter-only and cannot be drafted by a tool."; Section 7 returned 400; an unknown section returned 404.
- Live drafts, two only: Section 1 (34.9 s, 238 deltas, cleanup applied) and Section 5 (45.3 s, 366 deltas, cleanup applied). Both stored with status "drafted", both visible in the Run log as "Memo: Test memo 8766 / Section N".
- Saved an edit to Section 7 (status "edited"); added a comment to Section 1; added, resolved and deleted comments on Section 5; an empty comment returned 400.
- Export: headings in template order, the consolidated page, yellow placeholders for undrafted M sections, 3.5, Sections 8 and 10 and Section 9, the "Underwriter-authored" label on Section 7, the footer text, two real Word comments, Section 9 blank apart from its placeholder, no rating, score or recommendation wording.
- Page in the Browser pane at 127.0.0.1:8766: Memo view renders, Section 9 card has no Draft button and opens an empty editor, Review collapse to the 44 px rail and back, Chat view still renders; no console errors.

## Not tested

- Sections 2, 3, 4 and 6 were not drafted live (to limit model calls), and "Draft all machine sections" was not run end to end; its Stop path was checked by reading the code only.
- The streamed card rendering and the Draft, Save and Comment buttons were not clicked in the browser; the same operations were exercised through the API.
- The .docx was read back with python-docx, not opened in Microsoft Word.
- Two people editing the same memo at once: last save wins per section; there is no merge.

The test memo "Test memo 8766" has since been deleted; its two runs remain in the Run log (`app/data/runs/`).


## Underwriter to complete: grouping and AI suggestions (added 2026-10-08)

The memo checklist (every bullet under "Underwriter to complete" in the drafted machine sections) had 45 items for "Larkspur new-money memo". It now has two layers. The chat checklist (`listUnder`, `todoHTML`) is unchanged.

### Layer 1: grouped by code, always shown, no model call

`store.group_checklist(memo)` (Python, used by the Word export and the AI call) and `groupChecklist(memo)` (the same rules in index.html, used by the page) must stay in step. A Node check on the Larkspur memo gave identical output from both.

- Each item goes to the first group whose rule matches, in this order: **Documents to request** (contains "Not in provided documents"; the phrase is removed and the rest kept, so the item says what is missing and where it would normally be), **Conflicts to resolve** ("CONFLICT"), **Sections to write** (names Section 3.5, 7, 8, 9 or 10, or says "underwriter-authored" or "Underwriter Commentary"), **Policy items for judgment** (cites D4, or says policy, exception, senior review, Senior Loan Committee or concentration), **Other checks**. Sections to write is checked before policy so that "concentration must be addressed in Section 7" lands with the section it asks for. The page shows the groups in the order Documents, Conflicts, Policy, Sections, Other.
- A bullet that is only a bold label ending in a colon (for example "**Definition differences for review:**") is a sub-heading, not a task, and is dropped.
- A pointer item ("All gaps listed under "Collateral valuation, lien position and guarantor support" above") is replaced by one Documents item that lists the first sentence of each "Not in provided documents" paragraph under that heading in the same section (appraisal, collateral coverage, lien search, guarantor financial statements, 2023 agreement terms, Expansion Project definition), with their citations.
- Repeats are merged: the first one is kept and shows every section that had it ("Sections 1, 3, 6"). Two items are repeats when their key is the same (lowercase, citations and punctuation removed, first 60 characters), or when they are in the same group, cite at least one common source, and also share two figures or a quoted phrase of two or more words, or cite the same set of two or more sources. Citations a repeat had that the kept item lacks are shown after it as "Also cited in the repeats: [...]", so no evidence is lost.
- Larkspur result: 45 items, 38 after grouping (2 sub-headings removed, 5 repeats merged). Documents to request 12, Conflicts to resolve 1 (Sections 1, 3, 6), Policy items for judgment 8, Sections to write 3, Other checks 14.
- The tab shows "45 items, 38 after grouping.", a count per group, the citation chips, tick boxes (not saved, as before) and a "Show original list" toggle back to the flat 45. The memo toolbar link reads "Underwriter to complete: 38 items (45 before grouping) ›".

### Layer 2: "Suggest consolidation", one guarded model call, suggestions only

- Buttons: "Suggest consolidation" in the memo toolbar (`#mConsolidate`, it also opens the Review tab) and at the top of the grouped checklist. A spinner line counts the seconds. Disabled while a section is drafting.
- `POST /api/memos/{id}/checklist/consolidate` numbers the grouped items (`engine.consolidate_input`), each with its sections and citations, and sends them once to the draft model in Settings ("model", claude-sonnet-5-5) with the system prompt `engine.CONSOLIDATE_PROMPT`, using the same `claude -p --tools "" --strict-mcp-config --output-format json --no-session-persistence --model <model>` call and environment as the cleanup pass. The model must return JSON with `documents_to_request` ({item, would_be_in, request_line}), `conflicts` ({item, how_to_resolve}), `policy_items` ({item, judgment_needed}), `sections_to_write` ({section, what_it_needs}; Section 9 is left out), `suggested_edits` ({section, suggestion}; Sections 1 to 6 only, no new facts) and `dropped` ({item, reason}).
- Parse: code fences are stripped, the JSON object is read, malformed rows are skipped, `dropped` numbers outside the list are ignored, and any em or en dash is replaced with a hyphen.
- Citation repair (before the guard, `engine.repair_citations`): a bracket the model joined ("[D1, §2; D2, §1.1]") or combined ("[D1, §5, §6]") is split back into brackets that exist in the input as written; a bracket the model made from a plain-text reference ("[D5, ¶5]" where the input only says "D5 ¶5") goes back to that plain text. Nothing else is changed, and anything that cannot be mapped this way is left for the guard to reject. The changes are stored in `citation_repairs`.
- Guard (`engine.check_consolidation`, modelled on `check_cleanup`); all must pass: every bracket citation in the output appears in the input exactly; no figure-like number (`_NUMBER_RE`) that is not in the input; no match for the rating regex (`_RATING_RE`, the same pattern `check_cleanup` uses, now a module constant); at least one group not empty. If it fails, the response is `{"status": "rejected", "reason": ...}`, nothing is stored, and the page shows "Suggestion rejected: <reason>. Showing the grouped list." An engine error gives `"failed"` and "Suggestion failed: ...".
- An accepted result is stored on the memo as `checklist_consolidated`: `{at, model, duration_ms, run_id, source_item_count, original_item_count, source_items, citation_repairs, documents_to_request, conflicts, policy_items, sections_to_write, suggested_edits, dropped}` (each dropped entry also carries the item text and sections). Every call, accepted or not, is a run in the Run log named "Memo: <name> / Checklist consolidation", with the numbered list as the prompt and the raw model answer as the response; a rejected call is marked Failed with "Guard rejected: <reason>".
- The page shows the suggestions above the grouped list, in a box labelled "AI suggestions, not applied. The underwriter decides.", with the model, time and duration, the same groups, request lines in smaller gray italics, "Suggested edits to the drafted sections" as a separate group, and a "Dropped as duplicate or filler: N items" expander. The grouped list stays underneath under "Grouped by code, no AI". If the checklist has changed since the suggestion (a section was redrafted or edited), a note says so. Nothing is written into the memo sections.
- **Re-run:** press "Suggest consolidation again" (one model call; the new result replaces the stored one only if it passes the guard). **Clear:** "Clear suggestion" in the box (asks first), or `DELETE /api/memos/{id}/checklist/consolidate`. The Word export then goes back to the grouped list.

### What was tested (port 8766, own server, 2026-10-08)

- `py_compile` on store.py, server.py, engine.py and memo_docx.py; inline script checked with `node --check`; all 77 pre-existing id attributes still present exactly once (new: `mConsolidate`, `clElapsed`); no em or en dashes in the touched files.
- Offline guard cases: an invented citation, a new figure (1.41), "rating of 5" and "recommend approval" were rejected; empty groups and non-JSON were rejected; code fences were accepted.
- Endpoint errors: 400 for a memo with no items, 404 for an unknown memo (POST and DELETE). No model call.
- Live calls on "Larkspur new-money memo": two, both rejected by the guard, nothing stored. Call 1 (47.2 s) joined and combined citations and bracketed "D2 §2.2(a)". The citation rule in the prompt was then tightened; call 2 (41.0 s) bracketed "D5 ¶5". The citation repair step was added after call 2 and tested offline on both recorded answers: both would then pass the guard with no other change. No third call was made, so the repaired path had not run live at that point and no suggestion was stored.
- Page: grouped view, counts, a tick, "Show original list" and back, a citation chip in the checklist opens the slide-over, the chat checklist still shows 21 items for "Move 3 run". The AI suggestion box was checked by loading the recorded answer of call 2 into the page in the browser only (not stored). No console errors.
- Export read back with python-docx: the grouped page from the server; the AI page built in memory from the recorded answer. Yellow placeholders, the Section 9 placeholder and the footer are unchanged.


## Borrower cases and document groups (added 2026-10-08)

The app now holds three synthetic borrower cases. The Documents panel has a "Borrower case" picker and two groups: **Borrower file** ("Intake documents. Change with each case.": D1, D2, D5 and any uploads, with Upload and "Reset to case corpus" under it) and **Meridian reference** ("Template, policy and regulation. Fixed.": D3, D4, D6). Every row has a "Synthetic" chip. Reference rows have no remove button.

| Case id | Name | Type | Borrower file from | Memo header prefill |
|---|---|---|---|---|
| larkspur | Larkspur Precision Components | New money | `corpus/` (D1, D2, D5) | "New-money increase to $18.0M senior secured facility", "$18.0 million" |
| northwind | Northwind Foodservice Distribution | Annual review | `corpus/cases/northwind_annual_review/` | "Annual review of $14.0M facility", "$14.0 million" |
| harborline | Harborline Dental Partners | New money, policy exception | `corpus/cases/harborline_new_money_exception/` | "New money, $22.0M senior secured facility", "$22.0 million" |

Reference set, shared by every case: D3 `corpus/D3_prior_credit_memo_template.md`, D4 `corpus/D4_credit_policy_excerpt.md`, D6 `corpus/D6_sr26-2_summary.md`.

**Storage.** `app/data/settings.json` key `active_case` (default larkspur). `app/data/documents/<case_id>/` holds that case's borrower file (`index.json` plus `D#.md`); `app/data/documents/_reference/` holds D3, D4 and D6. Uploads go into the active case and take the next ID not used by that case or the reference set (D7 first). On startup `store.init()` copies the old single-folder layout (`app/data/documents/index.json`, D1 to D5) into `documents/larkspur/` once, keeping the Larkspur borrower file as it stood. The old files are left in place so a server still running the previous code keeps working; nothing reads them now, and they can be deleted once every server has been restarted.

**What the model sees.** `store.corpus_text(case_id)` returns the reference set plus that case's borrower file, ordered by ID (D1, D2, D3, D4, D5, D6, then uploads), with the same BEGIN and END markers, so citations keep their form. A chat message uses the chat's case and a memo draft uses the memo's case (normally the active case, since only its items are listed). For Larkspur this is D1 to D5 as before plus D6, identical to what the eval harness now sends. "Reset to case corpus" resets only the active case's borrower file (removes its uploads) and reloads the reference set.

**Chats and memos.** Both carry `case_id`, set from the active case at creation; records made before this change have none and count as larkspur. The chat and memo pickers list only the active case's items, and "New chat" and "New memo" create under it. New memo names default to "<short name> credit memo" (Larkspur keeps "Larkspur credit memo"). Run records gain `case_id`, and their `documents` list is that case's set.

**Endpoints (new or changed).**

| Method | Path | Body | Returns |
|---|---|---|---|
| GET | /api/cases | | [{id, name, type, borrower, active, chats, memos}] (chats and memos are counts) |
| PUT | /api/cases/active | {case_id} | the case list. 400 for an unknown case |
| GET | /api/documents | | each record also has `group` ("borrower" or "reference") and `case_id` (null for reference) |
| DELETE | /api/documents/{id} | | 400 for D3, D4 or D6: the reference set is fixed |
| GET | /api/chats?case=<id> | | optional filter; records include `case_id`. 400 for an unknown case |
| POST | /api/chats | {name?, case_id?} | case defaults to the active case |
| GET | /api/memos?case=<id> | | optional filter; records include `case_id` |
| POST | /api/memos | {name?, case_id?} | case defaults to the active case; header prefilled from the case |

GET of a document by id, upload and reset keep their shapes. The checklist, consolidation, export and streaming paths are unchanged apart from the case being passed through; the Word export adds a small "Borrower case: <name> (<type>). Synthetic case file." line under the memo name.

**Page.** The picker (`#caseSel`, with `#caseType` showing the type and borrower) switches with `PUT /api/cases/active`, then reloads documents, chats and memos and shows a toast. It is disabled while a chat or memo draft or a consolidation is running. The top bar shows "Case: <short name>" (`#topCase`, full name and type in its tooltip) before the chat or memo name; it is hidden at 1,100 px or less, like the chat name. The Workspace empty state names the active case. Preset text is shown and filled with the active case's name in place of "Larkspur" (the saved presets are unchanged). The Workflow stage 1 note now mentions the three cases. New ids: `caseSel`, `caseType`, `topCase`, `grpBorrower`, `grpRef`; all 79 earlier ids are still present exactly once.

**Rulebook.** `system_prompt.md` named "D1-D5" in three places; they now say "the numbered documents in this project" (saved through Settings with a note, version 20261008-125216). See `eval/results/prompt_change_log.md`, Change 2. The eval must be re-run.

### What was tested (port 8766, own server, 2026-10-08)

- `py_compile` on store.py, server.py, memo_docx.py and eval/run_eval.py; inline script checked with `node --check`; id inventory before and after; no em or en dashes in the touched files.
- Migration: `documents/larkspur/` D1, D2 and D5 match the old files; `_reference/` holds D3, D4, D6.
- API: unknown case 400; switch to northwind; documents D1, D2, D5 (Northwind, borrower) plus D3, D4, D6 (reference); D4 delete refused; an upload became D7 in Northwind; reset removed it; upload and delete again.
- Live calls, two: Northwind chat, Move 1 (50.3 s), cites revenue 104,600 and EBITDA 4,100, marks the EBITDA CONFLICT (4,100 against "about $4.5 million") and reports FY2025 revolver availability and liquidity as "Not in provided documents". Harborline memo, Section 6 (50.4 s), prompt "Draft Section 6, Policy Compliance and Exceptions, for Harborline Dental Partners.", header prefilled from the case; it shows 3.70x against the 3.50x ceiling with the Chief Credit Officer approval rule and leaves the exception determination to the underwriter. Export read back with python-docx.
- Back on larkspur: "Move 1 run", "Move 3 run" and "Larkspur new-money memo" list; `corpus_text()` equals the Larkspur D1 to D5 plus D6 and equals the harness `load_corpus()`.
- Page at 1,280 x 720 in the Browser pane: picker, both groups, chips, switch to Northwind and back with the toast, a Northwind citation chip opened the Northwind D1 row in the slide-over, chat and memo pickers filtered; no console errors.

### Not tested

- Upload and remove were exercised through the API, not clicked in the page. The streaming Send and Draft buttons were not pressed in the page (the two live calls went through the API).
- At 1,280 px the top bar is tight while the eval pill reads "(prompt changed since)": the chat or memo name is squeezed to almost nothing. It returns once the eval is re-run and the pill is shorter.
- The test chat "Northwind Move 1 test" and the memo "Harborline credit memo" are left in `app/data/` under their cases. Delete them from the Workspace if they are not wanted.
