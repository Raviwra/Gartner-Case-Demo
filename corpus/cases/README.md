# Additional borrower cases [SYNTHETIC]

Two more fictional borrower files for the Meridian credit memo prototype. Each follows the Larkspur documents in structure, IDs, section numbering and table row labels, so the same memo template, policy excerpt and rulebook apply unchanged. Larkspur Precision Components remains in corpus/ as the original case. All figures are $ in thousands unless noted, and every figure is reconciled by build/check_case_ledgers.py (results in each folder's LEDGER_CHECK.md).

## northwind_annual_review

Northwind Foodservice Distribution, LLC is a broadline foodservice distributor in Des Moines, Iowa, and a Meridian customer since 2016. The file is an annual review of its $14.0M facility ($4.0M term loan and a $10.0M revolver governed by a monthly borrowing base), with no change requested. FY2025 revenue was 104,600 and EBITDA 4,100 (3.9% margin); leverage rose from 2.55x to 3.20x and DSCR fell from 1.45x to 1.27x over FY2023 to FY2025, against covenants of 3.75x and 1.20x. The Q3 2025 DSCR test was 1.22x, and the Q2 2025 compliance certificate arrived 25 days late under waiver W-25-0388. Planted flaws: FY2025 revolver availability is "Not provided*" (so liquidity is "n/a*" and the minimum availability covenant cannot be tested), and FY2025 EBITDA of 4,100 conflicts with management's "about $4.5 million". The tool should surface the covenant results, the waiver, the two flaws, the Medium flag on §7.3 (Schedule 1.1 missing) and the Low flag on §7.6, and should note that Customer A at 23% is below the 25% concentration threshold. Whether the D4 origination tests apply to an annual review is left to the underwriter. See NOTES.md and LEDGER.md.

## harborline_new_money_exception

Harborline Dental Partners, Inc. is a dental support organization in Grand Rapids, Michigan, and a Meridian deposit customer since 2021. It requests new money: a $22.0M senior secured facility ($17.0M term loan, $5.0M revolver) to refinance its current lender and acquire two practices. Pro forma (FY2025 basis) EBITDA is 5,900, total funded debt 21,830, total leverage 3.70x and DSCR 1.27x. Planted flaws: the Practice 2 seller note amount is "Not provided*" and is excluded from pro forma debt, though the draft agreement counts it in Total Funded Debt; and pro forma EBITDA of 5,900 conflicts with management's "about $6.3 million". The tool should surface, without judging: a policy exception under D4 §4.2.1 (3.70x above 3.50x) requiring Chief Credit Officer approval; no DSCR exception under §4.2.2 (1.27x at or above 1.25x); senior review and Senior Loan Committee approval under §4.2.3 on all three grounds; and the §4.2.4 concentration requirement, since Payer A is 38% of FY2025 revenue (noting that the policy says "customer"). D2 carries a leverage step-down, a Medium flag on §7.3 (Schedule 1.1 missing) and a Low flag on the §7.6 key-person clause. See NOTES.md and LEDGER.md.

## Shared reference documents

- **D3**, corpus/D3_prior_credit_memo_template.md: the memo template (Part A) and the Larkspur exemplar (Part B).
- **D4**, corpus/D4_credit_policy_excerpt.md: credit policy §4.2.
- **D6**, corpus/D6_sr26-2_summary.md: a plain-language summary of SR 26-2 (model risk management guidance, April 17, 2026), written for the exercise and to be checked against the letter.

## How the app is expected to use them

The borrower file swaps per case: D1, D2 and D5 come from the case folder (or from corpus/ for Larkspur), while D3, D4 and D6 stay fixed across cases. LEDGER.md, NOTES.md and LEDGER_CHECK.md are design and reconciliation notes and are not loaded as sources. The app's case picker (app/store.py) loads each case's borrower file from its folder; see app/MEMO_NOTES.md, "Borrower cases and document groups".

FICTIONAL - prepared for case exercise.
