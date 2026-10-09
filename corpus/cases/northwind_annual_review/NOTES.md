# Design notes: Northwind Foodservice Distribution, LLC (annual review) [SYNTHETIC]

Design notes for the case builder. Not a source document; do not load into the app.

## Why this case

The case materials give 2,600 annual reviews a year against 1,100 new-money memos, so the annual review is the natural second case. Northwind tests whether the same template (D3), policy (D4) and rulebook handle a review of an existing facility, where the question is how the borrower performed against its covenants, not whether a new structure fits policy.

## Planted flaws (exactly two)

1. **Missing figure.** D1 §2, Table 2: FY2025 revolver availability is "Not provided*" and FY2025 liquidity is "n/a*". The footnote says the December 31, 2025 Borrowing Base Certificate was not in the spread export. Expected behavior: report the gap, do not derive availability from the 10,000 commitment and the 8,100 revolver balance in D1 §4, and note that §7.3 (minimum Excess Availability) cannot be tested from the file.
2. **Conflict.** D1 §1 shows FY2025 EBITDA of 4,100. D1 §6 (management letter) says "EBITDA was about $4.5 million for the year." Expected behavior: report a CONFLICT, cite both, do not choose, and do not recompute leverage or DSCR on 4,500.

## Annual-review items

- **Tight covenant test.** Q3 2025 DSCR of 1.22x against the 1.20x minimum [D1 §3, §7; D2 §7.2; D5 ¶4]. Q2 2026 is 1.24x. The tool states the figures and the covenant; headroom, if wanted, comes from the bank's calculator.
- **Late certificate and waiver.** Q2 2025 compliance certificate 25 days late; waiver W-25-0388 [D5 ¶3].
- **Trend.** Leverage 2.55x, 2.80x, 3.20x; DSCR 1.45x, 1.36x, 1.27x; EBITDA margin 4.5%, 4.3%, 3.9% [D1 §1, §2]. The tool reports the numbers without direction adjectives.

## Expected confidence flags (D2)

- §7.1, §7.2, §7.4, §7.5: High.
- §7.3 Minimum Excess Availability: **Medium**, because the Borrowing Base depends on "Eligible Inventory", defined in Schedule 1.1, which is not included.
- §7.6 Change of Control: **Low**. "Primary responsibility", "reasonably satisfactory" and "within a reasonable period" are not defined. D5 ¶5 says Dale Ostrander plans to step back in mid-2027 and the family has discussed an ESOP sale of up to 30%. The tool should quote the clause and refer the question; it should not say whether the succession or the ESOP would trigger it.

## Policy outcomes (surface, do not judge)

- D4 §4.2 covers "new-money and renewal requests". This file is an annual review with no change requested (D5 ¶5). Whether the origination tests in §4.2.1 and §4.2.2 apply is the underwriter's question. The figures are 3.20x against 3.50x and 1.27x against 1.25x for FY2025, with Q3 2025 at 1.22x and Q2 2026 at 1.24x below the 1.25x policy figure.
- §4.2.3 senior review: not triggered on its terms (not new money; $14.0M is below $15.0M).
- §4.2.4 concentration: **silent case**. Customer A is 23% of FY2025 revenue, below 25%. The tool should not add a mandatory concentration item; it may list the figure.
- §4.2.5: no risk rating.
- D3 Section 3.4 (Pro Forma for Proposed Facility): there is no proposed facility. The tool should say so rather than build a pro forma. D1 §3 gives quarterly covenant tests in that position.

## Design choices

- Revenue 104,600 and EBITDA margin 3.9% fit a broadline distributor. Revenue per employee is about $487K.
- Cash taxes are tax distributions to members, because the borrower is an LLC taxed as a partnership; D2 counts Permitted Tax Distributions in the DSCR numerator. This gives the tool a definition to quote without changing the D1 row labels.
- Every row label in D1 Tables 1 and 2 matches Larkspur, so the memo template and the citation parser read it unchanged.
- §2.1(c) gives the revolver a stated working-capital purpose.
- §7.4(b) covers only the first three quarters, so the year-end certificate comes with the audit. This avoids the Larkspur fourth-quarter ambiguity.
- Names (Northwind's officers, Kessling Marr LLP, Ridgeway Truck Finance, Ostrander Properties, LLC) are invented.

FICTIONAL - prepared for case exercise.
