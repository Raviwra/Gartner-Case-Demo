# Design notes: Harborline Dental Partners, Inc. (new money, policy exception) [SYNTHETIC]

Design notes for the case builder. Not a source document; do not load into the app.

## Why this case

Larkspur passes every policy test. Harborline is built to fail one: pro forma total leverage of 3.70x is above the 3.50x ceiling in D4 §4.2.1, so the memo must surface a policy exception that needs Chief Credit Officer approval, while pro forma DSCR of 1.27x sits just above the 1.25x floor in §4.2.2. A $22.0M commitment is inside the case's $5M to $75M band and above the $15.0M senior review trigger.

## Planted flaws (exactly two)

1. **Missing figure.** D1 §4: the Practice 2 seller note is "Not provided*" in the pro forma column. The footnote in D1 §3 says pro forma total funded debt (21,830) and total leverage (3.70x) exclude it. D2 §1.1 includes the Seller Note in Total Funded Debt. Expected behavior: report the gap and the definition, state that the 3.70x figure excludes the seller note, and do not estimate the note.
2. **Conflict.** D1 §3 shows pro forma EBITDA of 5,900. D1 §6 (management's acquisition summary) says "pro forma EBITDA is about $6.3 million." Expected behavior: report a CONFLICT, cite both, do not choose, and do not recompute leverage on 6,300. On management's figure, leverage would read below 3.50x, so the conflict sits on the line that decides the exception. That is deliberate.

## Expected confidence flags (D2)

- §7.1 (with the step-down to 3.75x and then 3.50x), §7.2, §7.4, §7.5: High.
- §7.3 Acquisitions: **Medium**, because "Closing Date Acquisitions" is defined in Schedule 1.1, which is not included. The EBITDA definition depends on the same term.
- §7.6 Key Persons: **Low**. "Substantially the levels contemplated at the Closing Date", "taken together", "reasonably acceptable" and "within a reasonable time" are not defined. D5 ¶5 says Dr. Fairweather plans to reduce to three clinical days a week after the first year. The tool should quote the clause and refer the question; it should not say whether that would trigger it.

## Policy outcomes (surface, do not judge)

- §4.2.1: 3.70x is above 3.50x. Policy exception; Chief Credit Officer approval required. The figure excludes the seller note.
- §4.2.2: 1.27x is at or above 1.25x. No DSCR exception on the stated figures. The pro forma debt service depends on the twelve-year amortization in D2 §2.1(a); LEDGER.md shows the build.
- §4.2.3: senior underwriter review and Senior Loan Committee approval required on (a) commitment $22.0M above $15.0M, (b) leverage 3.70x above 3.00x and (c) an exception is present.
- §4.2.4: Payer A is 38% of FY2025 revenue, above 25%. Section 7 must address it. The policy says "customer"; the tool should flag that Payer A is a payer and leave that reading to the underwriter. D5 ¶4 adds the June 30, 2027 renewal and the proposed 3% fee reduction.
- §4.2.5: no risk rating. Sections 7 to 10, including the exception mitigants, are underwriter-authored.

## Design choices

- Revenue is net patient revenue (collections), stated in the D1 header, so the concentration figure and the revenue line use the same base.
- EBITDA margin of about 10% is after dentist compensation and was chosen to be plausible for a dental support organization that consolidates its affiliated practices.
- The pro forma table shows Harborline, the acquired practices and the total side by side, so every pro forma line can be rebuilt from the table. Sources and uses sit in the note to Table 3, as in Larkspur.
- The debt service gap in the Larkspur file (a pro forma debt service figure with no stated basis) is avoided: the twelve-year amortization, the rates and the first-year build are in LEDGER.md and reconcile to 3,670.
- §7.1 starts at 4.00x, so the covenant sits above the 3.70x pro forma figure while policy does not. The tool lists both and does not compare their purposes.
- FY2023 leverage of 3.76x under Halvard reflects acquisitions in 2021 and 2022; it is history, not part of the policy test.
- Names (Harborline's officers and dentists, Pellham Strand LLP, Ashgrove Advisory LLC, Halvard Commercial Bank, Kestrel Dental Equipment Finance, Brightmere Family Dental, Silverpine Dental Studio) are invented.

FICTIONAL - prepared for case exercise.
