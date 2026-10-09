# UI navigation notes: left rail, one panel at a time (static/index.html)

Restructure of the interface on 2026-10-08. Only `static/index.html` changed. Every API call in the page is unchanged; server.py, store.py and engine.py were not touched. Light theme only. No new libraries: marked from cdnjs is still the only external script. No web fonts. No em or en dashes. No rating, score, gauge or recommendation element.

**If the page looks out of date, reload with Ctrl+F5.** During testing the browser served the old cached page on a normal reload. A hard refresh fixes it.

## The new layout

```
+------+------------------------------------------------------------------+
| rail | top bar: product name | Chat: <name> | engine pill | eval pill   |
|  M   +------------------------------------------------------------------+
| Docs |                                                                  |
| Work |   one panel, full width, content in a centered column            |
| Revw |                                                                  |
| Flow |                                                                  |
|      |                                                                  |
| Gear |                                                                  |
+------+------------------------------------------------------------------+
| FICTIONAL - prepared for case exercise. ... (always visible)            |
+-------------------------------------------------------------------------+
```

- **Left rail** (72 px, Gartner Blue): an "M" product mark, then four buttons with an icon and a short label: Documents, Workspace, Review, Workflow. Settings (the gear, still `#gearBtn`) sits at the bottom of the rail. The selected item has a lighter fill and a small Opal bar on its left edge. The items are `<button>`s with `aria-pressed`; Up and Down arrow keys move between them.
- **Top bar** (56 px, white): the product name, the current chat or memo name ("Chat: Move 1 run" or "Memo: ..."), the engine pill and the eval pill. Both pills work as before: the engine pill opens Settings at Engine, and the eval pill opens Review on the Eval tab.
- **One panel at a time, full width.** Hidden panels use the `hidden` attribute and stay in the DOM, so every element id still exists exactly once. The selected panel is saved in localStorage as `meridian.panel` (inside the existing try/catch helper). The default is Workspace. A reload restores the panel. When you leave a panel and come back, its scroll positions (transcript, memo, Review, sources list, reader, workflow) are restored.
- **Content column.** Each panel centers its content in a column and keeps even gutters on wide screens: Workspace 1,160 px, Documents 1,280 px, Review 1,100 px, Workflow 1,180 px. At 1,100 px wide or less the gutters shrink to 16 px.

## Rail and panel mapping

| Rail item | Panel element | What it holds |
|---|---|---|
| Documents | `section#docsPanel` (new wrapper) | The Sources list (`#srcList`) on the left (upload, Reset to case corpus, remove) and the reader (`#srcReader`) on the right. If no document is open, a short placeholder tells you to select one. The open document's row is tinted. |
| Workspace | `section#wsRegion` (unchanged id and children) | The Chat or Memo toggle, the chat header, transcript and composer, or the memo view. "Export to Word" and "Draft all machine sections" stay in the memo toolbar. |
| Review | `section#reviewRegion` | The three existing tabs: Underwriter to complete, Run log, Eval. |
| Workflow | `section#flowPanel` (new) | The illustrative end-to-end process (see below). |
| Settings | `#gearBtn` at the bottom of the rail | Opens the existing Settings drawer. |

The old Review collapse control is gone. `#reviewCollapse` and `#reviewExpand` remain as buttons inside a hidden `div` so the old handlers stay harmless. The collapse CSS was removed, and the page no longer reads `meridian.reviewCollapsed`.

### Flow between panels

- **Draft to checklist:** under the response the checklist comes from, the Workspace shows a quiet link, "Underwriter to complete: 6 items ›" in "Move 1 run" or "Items for legal and underwriter review: 21 items ›" in "Move 3 run". It opens Review on the "Underwriter to complete" tab. In Memo view the same link sits at the right of the memo toolbar ("Underwriter to complete: 45 items ›"). If there are no items, it reads "Open Review ›".
- **Eval pill:** opens Review on the Eval tab from any panel. The Eval table is now full width, so PASS and FAIL are visible without Expand.
- **Citation chip:** opens the source in a slide-over and keeps you in the Workspace (next section).

## The source slide-over

- Click any citation chip in the Workspace (chat or memo), in the Review checklist, or in a Run log response. A panel slides in from the right, 42 percent of the window wide (480 px at least), over a light scrim. It shows the cited document with the usual highlight and scroll: the row, section or paragraph is highlighted, and the status line reads "Showing [D1, Table 1: Net income, FY2025]".
- It is the existing reader. `openSlide()` moves the `#srcReader` element into the slide-over (`#slideBody`) and calls the existing `openDoc(id, ref)`, so `renderReader`, `locate` and the highlight logic run unchanged. `closeSlide()` moves `#srcReader` back into the Documents panel.
- To close it, press Escape, click the scrim or press ×. Focus returns to the chip you clicked, and the transcript stays where it was. The D1 to D5 switcher in the slide-over head opens another document in place. "Open in Documents" closes the slide-over and opens the Documents panel on the same document and highlight.
- If you are already on the Documents panel, a citation opens in place, as before. The "‹ All sources" back button (`#backDocs`) is still rendered but hidden by CSS, because the list is always visible in the Documents panel.

## Workflow mock-up

It is marked with a dashed badge, "Illustrative. Not built in this prototype.", next to the panel title. It makes no model calls and no backend calls.

- An intro line and three legend chips: **Automated** (gray), **AI-assisted (human review)** (white with a Cobalt marker), **Human only** (pale blue with an Opal marker and edge).
- A horizontal stepper with six stages. Each stage shows its number, name and a short state: Submission (Simulated), Assembly (In prototype), Underwriter (In prototype), Senior review (Partly built), Sign-off (Not built), Record (Partly built). Click a stage, or use Left, Right, Home and End. The chosen stage is saved as `meridian.flowStage`.
- A detail card for the selected stage. It shows a one-line summary, then **Who**, **Where** (system chips: nCino, CreditLens, SharePoint, This assistant, Word) and **In this prototype:**. Below those are three columns: Automated, AI-assisted (human review) and Human only. "Previous stage" and "Next stage" buttons sit at the bottom.
- Content follows the brief. Stage 1: RM submits in nCino; spread, draft agreement, relationship notes and prior memos are gathered. Stage 2: the assistant drafts with citations and flags gaps and conflicts; it drafts a document request to the RM, sent after the underwriter approves it. Stage 3: the underwriter writes 3.5, 7, 8, 9 and 10 and works the checklist. Stage 4: senior review against an enforced structure. Stage 5: sign-off; the AI-assisted column reads "None. The assistant takes no part in sign-off." Stage 6: export, memo library, run log and prompt version as the audit trail. No rating value, score or recommendation appears.

**To edit the text,** open index.html and search for `const FLOW=[`. Each stage is one object: `name`, `state` (the line under the step), `who`, `where` (array of system chips), `sum` (summary), `auto`, `ai`, `human` (arrays of bullets), `aiNone` (optional text when `ai` is empty), and `proto` (the "In this prototype:" text). Keep plain text: the page escapes it, and Markdown is not rendered. Do not use em or en dashes.

## Further additions

1. **Memo section jump bar** (`#mJump`, under the memo toolbar). It has ten number pills, 1 to 10. Clicking one scrolls that section card to the top of the memo. Long jumps are instant and short ones smooth, so Section 9 is one click away. Each pill shows the status by shape: filled circle for Drafted, diamond for Edited, ring for Empty. A key sits on the right, and each pill's tooltip and accessible name give the section title and status. Judgment sections (7, 8, 10) have pale blue pills, and Section 9 is solid navy. The pill for the section in view gets a Cobalt outline as you scroll.
2. **Section 9 is distinct, and judgment color is no longer the CONFLICT color.** Sunstone now means CONFLICT only. Judgment cards (3.5 lives inside Section 3; Sections 7, 8 and 10) have an Opal left bar and a pale blue tint, with the "Underwriter" chip in Crystal and Opal. Section 9 gets the navy boundary treatment of the chat banner: navy border, 8 px navy left bar, a solid navy "Underwriter only. Required." chip and a second chip, "Locked to tools". The "Machine-assembled, cited" chip is now neutral white, so machine, human and locked read as three steps. In the Workflow legend, "Human only" uses the same Opal judgment color, so "a human writes or decides this" looks the same on both screens.
3. **Chat checklist parser.** `listUnder` now skips bold sub-heading lines (for example "**Ambiguous legal terms...**") instead of stopping at them. The checklist gathers bulleted and numbered items under both "Underwriter to complete" and "Items for legal and underwriter review". It comes from the latest assistant response that has such a list, so a short answer after it (the rating refusal, the industry-outlook refusal) no longer empties it. The note then reads "From the latest response with a checklist in ...". Results: "Move 3 run" shows 21 items, and "Move 1 run" shows the 6 items from the Section 3 draft. The memo checklist (`bulletsUnder`, `memoTodoHTML`) is unchanged and still shows 45 items for the Larkspur memo.
4. **Wide tables in the Workspace.** With the 1,160 px Workspace column, the 8-column covenant table in "Move 3 run" fits at 1,280 px wide. The table frame measured 1,093 px against a 1,093 px table, and the Confidence column is visible without scrolling. The "Expand table" control now shows only when a table does not fit its frame (`syncTables()` sets a `fits` class after each render, on panel change and on window resize). At 1,024 px wide the button is back.

## CSS changes

- Tokens: `--r` from 2 px to 4 px, and new `--r-lg` (8 px, for cards), `--rail` (72 px) and `--col` (column width). Each `.region` computes its own gutter `--gut`. Spacing stays on the 8 px scale, body text 16 px, system font stack.
- Body is a grid with areas `rail top / rail main / foot foot`. The top bar is white with a hairline, and the pills are rounded outline chips on white. The rail is new.
- Fewer boxes: the mode bar lost its gray band and rule. The Chat or Memo toggle is a soft segmented control (navy for the selected view). The reader head is white. Empty boxes have no border. Cards (assistant turns, memo sections, header, stage card) use 8 px corners and a 1 px hairline with no shadows. Shadows remain only on overlays (drawer, modal, slide-over).
- One accent: Cobalt stays the only solid color for primary actions (Send, Save, Draft). Secondary buttons now have a light gray border with navy text.
- Chips share one shape (fully rounded): `.tag`, `.count`, `.who`, `.st`, legend chips, system chips, the mock badge and the jump pills. Document ID badges and section numbers stay square because they are identifiers.
- Section 9 and judgment colors as described above. The CONFLICT highlight, "Not in provided documents" outline, citation chips and the "Boundary: underwriter only" banner are unchanged.
- One bug fixed: in a highlighted table row, the cited cell (for example 3,900) was white text on Moonstone, because the row rule out-ranked the cell rule. It is now white on Cobalt as intended (`tr.hl-row td.hl-cell`).
- Removed: the Review collapse styles, `.icon-btn` styling for the gear (the gear is a rail button now), and the old three-column grid.

## JavaScript touched, and why

All API calls, the streaming code, the memo actions and the settings code are unchanged.

- New: `setPanel` (rail), `openSlide` and `closeSlide` (slide-over), `syncTables` (Expand only when needed), `renderJump`, `jumpTo` and `markJump` (memo jump bar), `renderMemoTodo` (memo link), `checklistOf`, `checklistSource` and `todoLinkHTML` (chat checklist and link), `FLOW`, `renderFlow` and `setStage` (Workflow).
- `renderSources`: the list is always visible (it used to hide while a document was open), and the open document's row gets an `on` class.
- `renderTranscript`: adds the checklist link under the source response and calls `syncTables`.
- `listUnder` and `todoHTML`: the parser fix above.
- `renderReview`, `renderMemo`, `renderMemoTools` and `renderCard`: call the new helpers (sync tables, jump bar, memo link).
- `secHTML`: Section 9 gets a `locked` class, a `who-l` chip and the "Locked to tools" chip.
- Click handler: a citation chip opens the slide-over unless you are on Documents. New handlers for rail items, the checklist link, stepper stages, jump pills and slide-over close or "Open in Documents".
- Keydown: Escape closes the slide-over (after modal and drawer). Arrow keys work on the rail and the stepper.
- Startup: the eval pill handler opens Review instead of expanding the collapsed column, and the page no longer restores the collapse state. A memo scroll listener drives the jump-bar highlight, and a resize listener re-checks tables. `setPanel` restores the saved panel, and `renderFlow` draws the stepper.
- Citation chip tooltip: "Open D1 source" (was "Open D1 in Sources").

## What was verified

- `node --check` on the extracted inline script: passes.
- Id inventory taken before the change (66 ids). After the change every one still appears exactly once in the file. Ten new ids were added (docsPanel, docsBody, mTodo, mJump, flowPanel, flowSteps, flowCard, flowTab0 to 5 generated, slideLayer, slideDocs, slideBody). No duplicates.
- No U+2014 or U+2013 in the file. The only external script is marked 12.0.2 from cdnjs, and there are no font links. The list of `api(...)` and `fetch(...)` calls is identical to the original.
- In the browser, on my own server on port 8766 (stopped afterwards, port 8765 untouched), at 1,280 x 720 and 1,024 x 700. Nothing that calls the model was pressed (no Send, Draft or Draft all).
  - Each rail item showed its panel. A reload restored the last panel (Review, then Documents).
  - Chat and Memo toggle.
  - In "Move 1 run", the "D1, Table 1: Net income, FY2025" chip in the CONFLICT line opened the slide-over. The Net income row was highlighted with 3,900 in white on Cobalt. Escape closed it, focus went back to the chip and the transcript scroll was unchanged.
  - "Open in Documents" showed D1 with the highlight in the Documents panel. Chips in the Review checklist and in Memo view also open the slide-over.
  - Workflow: clicking stages, arrow keys, and Previous and Next.
  - The eval pill opened Review on Eval from the Workflow panel. The gear opened Settings.
  - All three Review tabs. The checklist link went from the memo to Review.
  - The Section 9 jump pill scrolled to Section 9 and marked it current.
  - Covenant table fit and Expand hidden at 1,280; Expand shown at 1,024.
  - Scroll position kept across panel switches.
  - No console errors.

## Not verified

- Not checked at 125 and 150 percent browser zoom on a real screen share. 1,280 x 720 CSS pixels stands in for a 1080p screen at 150 percent.
- Screen reader behavior of the rail, slide-over and stepper was checked by reading the markup, not with a screen reader. The slide-over does not trap focus (neither did the existing drawer).
- The streaming path (live Send or Draft) was not run. The checklist link and table check are applied after a response finishes, through the same `renderTranscript` and `renderCard` calls.
- Upload and remove in the Documents panel were not exercised (no state changes to the corpus).
