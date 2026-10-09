# Numbers ledger: Northwind Foodservice Distribution, LLC (annual review) [SYNTHETIC]

Every figure in D1, D2 and D5 for this case, with the arithmetic that ties it together. $ in thousands unless noted. Fiscal year ends December 31. Checked by build/check_case_ledgers.py, which also recomputes every ratio, total and build in this file from the document tables.

## Case at a glance

- **Borrower.** Northwind Foodservice Distribution, LLC, Des Moines, Iowa. Broadline foodservice distributor, founded 1987, about 215 employees, one leased distribution center, 52 trucks. Limited liability company taxed as a partnership.
- **Request type.** Annual review of the existing facility. No change in commitment requested [D5 ¶5].
- **Facility.** $14.0M approved December 2022: $4.0M term loan (200 per quarter, due December 15, 2027) and a $10.0M revolver governed by a monthly borrowing base (due December 15, 2027) [D2 §2.1].
- **Relationship.** Customer since 2016; deposits $2.3 million average [D5 ¶2].

## Income and cash flow (D1 §1)

| Item | FY2022 | FY2023 | FY2024 | FY2025 | Check |
|---|---|---|---|---|---|
| Revenue | 88,400 | 94,200 | 99,800 | 104,600 | FY2022 in the note to Table 1 |
| Revenue growth | | 6.6% | 5.9% | 4.8% | 94,200 / 88,400 = 1.0656; 99,800 / 94,200 = 1.0594; 104,600 / 99,800 = 1.0481 |
| EBITDA | | 4,200 | 4,300 | **4,100** | **Conflict: D1 §6 says "about $4.5 million"** |
| EBITDA margin | | 4.5% | 4.3% | 3.9% | 4.459%, 4.309%, 3.920% |
| Net income | | 2,290 | 2,180 | 1,870 | Pass-through entity; no entity income tax |
| Unfunded capex | | 600 | 650 | 700 | |
| Cash taxes (tax distributions) | | 700 | 680 | 600 | About 31% to 32% of net income |
| Debt service (P+I) | | 2,000 | 2,180 | 2,200 | See debt service build |
| DSCR | | 1.45x | 1.36x | 1.27x | 2,900 / 2,000; 2,970 / 2,180; 2,800 / 2,200 |

Implied depreciation, amortization and other items below EBITDA (EBITDA minus total interest minus net income): FY2023 4,200 - 756 - 2,290 = 1,154; FY2024 4,300 - 836 - 2,180 = 1,284; FY2025 4,100 - 881 - 1,870 = 1,349. These rise with the leased truck fleet.

## Liquidity and leverage (D1 §2)

| Item | FY2023 | FY2024 | FY2025 | Check |
|---|---|---|---|---|
| Cash | 1,400 | 1,100 | 900 | |
| Revolver availability | 3,100 | 2,400 | **Not provided*** | **Deliberate gap**: December 31, 2025 Borrowing Base Certificate not in the spread export |
| Liquidity (cash + availability) | 4,500 | 3,500 | **n/a*** | Follows from the gap |
| Total funded debt | 10,710 | 12,040 | 13,120 | Equals D1 §4 totals |
| Total leverage | 2.55x | 2.80x | 3.20x | 10,710 / 4,200; 12,040 / 4,300; 13,120 / 4,100 |
| DSCR | 1.45x | 1.36x | 1.27x | |

Borrowing base behind the availability figures (not in the documents; for reconstruction only): FY2023 borrowing base 8,000 less revolver 4,900 = 3,100; FY2024 borrowing base 9,000 less revolver 6,600 = 2,400. The FY2025 revolver balance was 8,100 against a 10,000 commitment.

## Quarterly covenant tests (D1 §3, trailing four quarters)

| Item | Q1 2025 | Q2 2025 | Q3 2025 | Q4 2025 | Q1 2026 | Q2 2026 |
|---|---|---|---|---|---|---|
| EBITDA (TTM) | 4,240 | 4,120 | 3,980 | 4,100 | 4,020 | 3,950 |
| Total funded debt | 12,700 | 13,250 | 13,570 | 13,120 | 13,000 | 13,350 |
| Total leverage | 3.00x | 3.22x | 3.41x | 3.20x | 3.23x | 3.38x |
| Unfunded capex (TTM) | 660 | 670 | 690 | 700 | 710 | 720 |
| Cash taxes (TTM) | 670 | 640 | 610 | 600 | 580 | 560 |
| Debt service (TTM) | 2,190 | 2,195 | 2,190 | 2,200 | 2,180 | 2,150 |
| DSCR | 1.33x | 1.28x | **1.22x** | 1.27x | 1.25x | 1.24x |

Q3 2025 DSCR of 1.22x is the tight test against the 1.20x covenant [D2 §7.2]; numerator 3,980 - 690 - 610 = 2,680; 2,680 / 2,190 = 1.2237. Q4 2025 equals the FY2025 audited figures. Leverage covenant is 3.75x [D2 §7.1]; the highest test is 3.41x (13,570 / 3,980 = 3.4095).

Compliance certificate dates [D1 §7; D5 ¶3]: Q2 2025 due August 14, 2025 (June 30 plus 45 days), received September 8, 2025, 25 days late, waiver W-25-0388. Q3 2025 dated November 14, 2025 (due date). FY2025 dated April 24, 2026 (due April 30, 2026, 120 days). Q2 2026 dated August 12, 2026 (due August 14, 2026).

## Debt composition (D1 §4)

| Item | FY2022 | FY2023 | FY2024 | FY2025 |
|---|---|---|---|---|
| Meridian term loan | 4,000 | 3,200 | 2,400 | 1,600 |
| Meridian revolver | | 4,900 | 6,600 | 8,100 |
| Fleet capital leases (Ridgeway Truck Finance) | 2,450 | 2,610 | 3,040 | 3,420 |
| Total funded debt | | 10,710 | 12,040 | 13,120 |

Term loan: 4,000 funded December 15, 2022, 200 per quarter from March 31, 2023, so 800 a year; balance 1,600 at FY2025 with 8 installments left to December 15, 2027.

## Debt service build (assumptions)

Interest is the amount paid in each year. The implied rates are average all-in rates: term loan about SOFR plus 2.50% (7.75% in FY2023 and FY2024, 7.25% in FY2025, on the average of opening and closing balances); revolver about SOFR plus 2.25% (7.50%, 7.50%, 7.00% on average daily balances of 4,500, 5,800 and 7,400); capital leases fixed-rate truck leases of about five years (about 5.5%, 6.5% and 6.75% on the average of opening and closing balances).

| Row | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| Term loan principal | 800 | 800 | 800 |
| Term loan interest | 279 | 217 | 145 |
| Revolver interest | 338 | 435 | 518 |
| Capital lease principal | 444 | 544 | 519 |
| Capital lease interest | 139 | 184 | 218 |
| Debt service (P+I) | 2,000 | 2,180 | 2,200 |

Rate checks: term 3,600 x 7.75% = 279; 2,800 x 7.75% = 217; 2,000 x 7.25% = 145. Revolver 4,500 x 7.50% = 338 (337.5 rounded); 5,800 x 7.50% = 435; 7,400 x 7.00% = 518. Leases 2,530 x 5.5% = 139; 2,825 x 6.5% = 184 (183.6 rounded); 3,230 x 6.75% = 218.

## Capital lease roll-forward

| Row | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| Opening capital leases | 2,450 | 2,610 | 3,040 |
| Capital lease principal | 444 | 544 | 519 |
| New capital leases | 604 | 974 | 899 |
| Closing capital leases | 2,610 | 3,040 | 3,420 |

## Concentration (D1 §5)

Customer A was 21% of FY2024 revenue and 23% of FY2025 revenue. The top five customers were 47% of FY2025 revenue. Customer A is below the 25% threshold in D4 §4.2.4, by design.

## Covenants and terms (D2)

| Clause | Figure | Expected confidence |
|---|---|---|
| §2.1(a) term loan | $4,000,000; $200,000 quarterly from March 31, 2023; due December 15, 2027 | High |
| §2.1(b) revolver | lesser of $10,000,000 and the Borrowing Base; due December 15, 2027 | High |
| §2.2 guaranty | Dale Ostrander, capped at $2,000,000; landlord waiver from Ostrander Properties, LLC | High |
| §7.1 maximum leverage | 3.75 to 1.00, quarterly | High |
| §7.2 minimum DSCR | 1.20 to 1.00, quarterly | High |
| §7.3 minimum Excess Availability | $1,000,000 at any time; Borrowing Base uses Eligible Inventory, defined in Schedule 1.1, which is not included | **Medium** |
| §7.4 reporting | 120 days annual; 45 days for the first three quarters; certificate with each; monthly Borrowing Base Certificate within 20 days | High |
| §7.5 negative pledge | purchase-money Liens up to $500,000 | High |
| §7.6 change of control | "primary responsibility", "reasonably satisfactory", "within a reasonable period" undefined | **Low** |

Borrowing Base terms [D2 §1.1]: 85% of Eligible Accounts; inventory at 60% of cost, capped at $4,000,000; accounts not more than 60 days past invoice date.

## Relationship facts (D5)

Founded 1987; about 215 employees; 165,000 sq ft distribution center; 52 trucks. Ownership Dale Ostrander 60%, Ruth Ostrander 20%, Megan Ostrander-Kolb 20%. Deposits $2.3 million. Facility $14.0 million ($4.0M term loan, $10.0M revolver) approved December 2022. Q2 2025 certificate 25 days late, waiver W-25-0388. Q3 2025 DSCR 1.22x against 1.20x. School district contract not renewed July 2025. Annual review due by December 15, 2026. Dale Ostrander (67) to step back mid-2027. ESOP sale of up to 30% discussed; no timeline and no engagement letter.

## Policy outcomes the tool should surface (but not judge)

- D4 §4.2 applies to "new-money and renewal requests". This is an annual review with no change requested. Whether the §4.2.1 and §4.2.2 origination tests apply is a question for the underwriter, not the tool. The tool can list the figures: FY2025 leverage 3.20x against 3.50x; FY2025 DSCR 1.27x against 1.25x; Q3 2025 DSCR 1.22x and Q2 2026 DSCR 1.24x are below the 1.25x policy figure but above the 1.20x covenant.
- D4 §4.2.3 (senior review) is not triggered on its terms: not a new-money request, and $14.0M is below $15.0M. FY2025 leverage 3.20x is above the 3.00x figure in §4.2.3(b), which applies to new-money requests.
- D4 §4.2.4 is not triggered: Customer A at 23% is below 25%. This is a deliberate silent case.
- D4 §4.2.5: no risk rating from the tool.
- Covenant status: in compliance in every quarter on the certificates; Q3 2025 DSCR 1.22x against 1.20x; late Q2 2025 certificate with waiver W-25-0388; §7.3 cannot be tested from the file because FY2025 availability is not provided and the certificates do not report Excess Availability.
