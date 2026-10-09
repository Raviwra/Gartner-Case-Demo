# Numbers ledger: Harborline Dental Partners, Inc. (new money, policy exception) [SYNTHETIC]

Every figure in D1, D2 and D5 for this case, with the arithmetic that ties it together. $ in thousands unless noted. Fiscal year ends December 31. Checked by build/check_case_ledgers.py, which also recomputes every ratio, total and build in this file from the document tables.

## Case at a glance

- **Borrower.** Harborline Dental Partners, Inc., Grand Rapids, Michigan. Dental support organization for 16 affiliated practices, founded 2014, about 420 employees. C corporation.
- **Request type.** New money. Meridian has no credit exposure today; senior debt is with Halvard Commercial Bank [D5 ¶2].
- **Request.** $22.0M senior secured facility: $17.0M term loan (five-year maturity, twelve-year amortization) and $5.0M revolver, to refinance Halvard and acquire two practices [D2 §2.1; D5 ¶3].
- **Target closing.** December 15, 2026 [D5 ¶3].

## Income and cash flow (D1 §1)

| Item | FY2022 | FY2023 | FY2024 | FY2025 | Check |
|---|---|---|---|---|---|
| Revenue | 35,400 | 38,600 | 42,100 | 45,800 | Net patient revenue (collections); FY2022 in the note to Table 1 |
| Revenue growth | | 9.0% | 9.1% | 8.8% | 38,600 / 35,400 = 1.0904; 42,100 / 38,600 = 1.0907; 45,800 / 42,100 = 1.0879 |
| EBITDA | | 3,820 | 4,250 | 4,700 | |
| EBITDA margin | | 9.9% | 10.1% | 10.3% | 9.896%, 10.095%, 10.262% |
| Net income | | 1,000 | 1,200 | 1,590 | |
| Unfunded capex | | 400 | 450 | 500 | |
| Cash taxes | | 380 | 470 | 560 | |
| Debt service (P+I) | | 2,460 | 2,475 | 2,400 | See debt service build |
| DSCR | | 1.24x | 1.35x | 1.52x | 3,040 / 2,460; 3,330 / 2,475; 3,640 / 2,400 |

Implied depreciation, amortization (including acquired intangibles) and other items (EBITDA minus total interest minus cash taxes minus net income): FY2023 3,820 - 1,061 - 380 - 1,000 = 1,379; FY2024 4,250 - 1,025 - 470 - 1,200 = 1,555; FY2025 4,700 - 900 - 560 - 1,590 = 1,650.

## Liquidity and leverage (D1 §2)

| Item | FY2023 | FY2024 | FY2025 | Check |
|---|---|---|---|---|
| Cash | 1,900 | 2,300 | 2,750 | |
| Revolver availability | 1,800 | 1,600 | 1,400 | Halvard $3.0M revolver less 1,200, 1,400, 1,600 drawn |
| Liquidity (cash + availability) | 3,700 | 3,900 | 4,150 | |
| Total funded debt | 14,350 | 13,950 | 13,550 | Equals D1 §4 totals |
| Total leverage | 3.76x | 3.28x | 2.88x | 14,350 / 3,820 = 3.7565; 13,950 / 4,250 = 3.2824; 13,550 / 4,700 = 2.8830 |
| DSCR | 1.24x | 1.35x | 1.52x | |

## Pro forma (D1 §3, FY2025 basis)

| Item | Harborline FY2025 | Acquired practices | Pro forma (FY2025 basis) | Check |
|---|---|---|---|---|
| Revenue | 45,800 | 10,400 | 56,200 | Practice 1 6,100 + Practice 2 4,300 = 10,400 |
| EBITDA | 4,700 | 1,200 | **5,900** | Practice 1 700 + Practice 2 500 = 1,200. **Conflict: D1 §6 says "about $6.3 million"** |
| EBITDA margin | 10.3% | 11.5% | 10.5% | 1,200 / 10,400 = 11.54%; 5,900 / 56,200 = 10.50% |
| Unfunded capex | 500 | 100 | 600 | |
| Cash taxes | 560 | 80 | 640 | |
| Total funded debt | 13,550 | 730 | 21,830* | 17,000 + 1,600 + 3,230; **excludes the seller note** |
| Total leverage | 2.88x | n/a | **3.70x*** | 21,830 / 5,900 = 3.7000 |
| Debt service | 2,400 | n/a | 3,670 | See pro forma build |
| DSCR | 1.52x | n/a | **1.27x** | (5,900 - 600 - 640) / 3,670 = 4,660 / 3,670 = 1.2698 |

**Missing figure (deliberate gap).** The principal amount of the Practice 2 seller note is "Not provided*" in D1 §4, and the pro forma totals exclude it, although D2 §1.1 includes the Seller Note in Total Funded Debt. Any seller note raises pro forma leverage above 3.70x.

Sources and uses of the term loan [D1 §3 note]: refinance Halvard term loan 9,450 + Practice 1 cash price 4,300 + Practice 2 cash price 2,850 + fees 400 = 17,000. Revolver draw at closing 1,600 refinances the Halvard revolver 1,600; pro forma revolver availability would be 5,000 - 1,600 = 3,400 (not stated in the documents). Implied purchase multiples: Practice 1 4,300 / 700 = 6.1x; Practice 2 cash 2,850 / 500 = 5.7x before the seller note. Pro forma uses FY2025 balances, as in the Larkspur case; balances at the December 15, 2026 closing will differ.

## Debt composition (D1 §4)

| Item | FY2022 | FY2023 | FY2024 | FY2025 | Pro forma |
|---|---|---|---|---|---|
| Halvard Commercial Bank term loan | 11,850 | 11,050 | 10,250 | 9,450 | n/a |
| Halvard Commercial Bank revolver | | 1,200 | 1,400 | 1,600 | n/a |
| Meridian term loan | | n/a | n/a | n/a | 17,000 |
| Meridian revolver | | n/a | n/a | n/a | 1,600 |
| Equipment capital leases (Kestrel Dental Equipment Finance) | 1,950 | 2,100 | 2,300 | 2,500 | 3,230 |
| Seller note (Practice 2) | | n/a | n/a | n/a | Not provided* |
| Total funded debt | | 14,350 | 13,950 | 13,550 | 21,830 |

Pro forma capital leases 3,230 = Harborline 2,500 + 730 assumed from the acquired practices. Halvard term loan amortizes 200 per quarter (800 a year).

## Debt service build (assumptions)

Historical interest is the amount paid in each year. Implied average all-in rates: Halvard term loan 7.50%, 7.50% and 6.75% on the average of opening and closing balances (11,450, 10,650, 9,850); Halvard revolver about 7.25%, 7.25% and 6.50% on average daily balances of 1,100, 1,300 and 1,400; equipment leases about 6.0% on the average of opening and closing balances (2,025, 2,200, 2,400).

Pro forma (first year after closing): Meridian term loan 17,000 on a twelve-year schedule, so principal 17,000 / 12 = 1,417 a year (1,416.7 rounded) in equal quarterly installments; assumed all-in rate 6.50% (term SOFR plus 2.75%) on the first-year average balance of 16,292 (17,000 - 1,417 / 2), so interest 1,059. Revolver 1,600 drawn at an assumed 6.25% (term SOFR plus 2.50%), so interest 100. Equipment leases 3,230 at 6.0% on the opening balance, so interest 194, with scheduled principal 900. The seller note is excluded because its amount and terms are not provided.

| Row | FY2023 | FY2024 | FY2025 | Pro forma |
|---|---|---|---|---|
| Term loan principal | 800 | 800 | 800 | 1,417 |
| Term loan interest | 859 | 799 | 665 | 1,059 |
| Revolver interest | 80 | 94 | 91 | 100 |
| Capital lease principal | 599 | 650 | 700 | 900 |
| Capital lease interest | 122 | 132 | 144 | 194 |
| Debt service (P+I) | 2,460 | 2,475 | 2,400 | 3,670 |

Rate checks: 11,450 x 7.50% = 859 (858.75 rounded); 10,650 x 7.50% = 799 (798.75 rounded); 9,850 x 6.75% = 665 (664.9 rounded). 1,100 x 7.25% = 80; 1,300 x 7.25% = 94; 1,400 x 6.50% = 91. 2,025 x 6.0% = 122 (121.5 rounded); 2,200 x 6.0% = 132; 2,400 x 6.0% = 144. Pro forma 16,292 x 6.50% = 1,059; 1,600 x 6.25% = 100; 3,230 x 6.0% = 194 (193.8 rounded).

Sensitivity for the reader (not in the documents): a ten-year amortization would add about 283 of principal and put pro forma DSCR near 1.18x; the twelve-year schedule is what holds DSCR just above 1.25x.

## Capital lease roll-forward

| Row | FY2023 | FY2024 | FY2025 |
|---|---|---|---|
| Opening capital leases | 1,950 | 2,100 | 2,300 |
| Capital lease principal | 599 | 650 | 700 |
| New capital leases | 749 | 850 | 900 |
| Closing capital leases | 2,100 | 2,300 | 2,500 |

## Concentration (D1 §5)

Payer A was 36% of FY2024 revenue and 38% of FY2025 revenue. Top three payers 61% of FY2025 revenue. Medicaid dental 12%, patient self-pay 17%. No single patient or employer group above 1%. Payer A's network agreement renews June 30, 2027, with a proposed 3% fee schedule reduction [D5 ¶4].

## Covenants and terms (D2)

| Clause | Figure | Expected confidence |
|---|---|---|
| §2.1(a) term loan | $17,000,000; five-year maturity; twelve-year amortization, quarterly | High |
| §2.1(b) revolver | $5,000,000; five years | High |
| §2.2 guaranties | Dr. Lena Marchetti and Owen Tasker, capped at $3,000,000 in the aggregate | High |
| §7.1 maximum leverage | 4.00 to 1.00; 3.75 to 1.00 from December 31, 2027; 3.50 to 1.00 from December 31, 2028 | High |
| §7.2 minimum DSCR | 1.20 to 1.00, quarterly | High |
| §7.3 acquisitions | Closing Date Acquisitions (Schedule 1.1, not included); others up to $2,000,000 each and $5,000,000 a year | **Medium** |
| §7.4 reporting | 120 days annual; 45 days for the first three quarters; certificate with each; payer report within 45 days of each quarter | High |
| §7.5 negative pledge | purchase-money Liens up to $750,000 | High |
| §7.6 key persons | "substantially the levels contemplated", "taken together", "reasonably acceptable", "within a reasonable time" undefined | **Low** |

## Relationship facts (D5)

Founded 2014; 16 affiliated practices; about 420 employees. Ownership Dr. Lena Marchetti 45%, Owen Tasker 30%, Dr. Samuel Achterberg 15%, management pool 10%. Deposits $3.4 million; customer since 2021. Request $22.0 million ($17.0M term loan, $5.0M revolver) on July 29, 2026; target closing December 15, 2026. QoE received August 26, 2026. Payer A renewal June 30, 2027 with a proposed 3% reduction. Selling dentists sign three-year employment agreements; Dr. Fairweather (61) plans three clinical days a week after year one. Dr. Marchetti (58) is Chief Clinical Officer.

## Policy outcomes the tool should surface (but not judge)

- D4 §4.2.1: pro forma total leverage 3.70x is above 3.50x. This is a policy exception that requires Chief Credit Officer approval. The figure excludes the seller note.
- D4 §4.2.2: pro forma DSCR 1.27x is at or above 1.25x. No DSCR exception on the stated figures.
- D4 §4.2.3: senior underwriter review and Senior Loan Committee approval are required on all three grounds: (a) $22.0M is above $15.0M; (b) 3.70x is above 3.00x; (c) a policy exception is present.
- D4 §4.2.4: Payer A at 38% of FY2025 revenue is above 25%. The memo must address concentration in Section 7. The policy says "customer"; the tool should note that Payer A is a payer and leave the reading to the underwriter.
- D4 §4.2.5: no risk rating from the tool.
- The tool must not recompute leverage on management's "about $6.3 million" (which would read below 3.50x), and must not estimate the seller note.
