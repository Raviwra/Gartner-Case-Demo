"""Reconcile every figure in the two added borrower cases against their Markdown documents.

Usage:
    python build/check_case_ledgers.py

Modelled on build/check_ledger.py and reuses its Markdown parser. For each case under
corpus/cases/ it runs three kinds of check and writes corpus/cases/<case>/LEDGER_CHECK.md:

1. Presence checks: (item, figure, doc, location, row, column) entries, as in
   check_ledger.py. Table entries must match the cell exactly (a trailing * is part
   of the cell). Section entries look for the figure inside the named section.
   Paragraph entries look inside the D5 paragraph that starts with the marker.
2. Arithmetic checks: every ratio, growth rate, margin, total, pro forma line and debt
   service build is recomputed from the tables (and from LEDGER.md for the builds)
   and compared with the figure as stated.
3. Labeling checks: "SYNTHETIC" in every title line and the footer on every document.

It also checks the shared D6 summary title and footer, and scans every file this
work added for em dashes and en dashes. Markdown only; no docx.
"""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from check_ledger import parse_markdown, find_block  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
CASES_DIR = ROOT / "corpus" / "cases"
D6_FILE = ROOT / "corpus" / "D6_sr26-2_summary.md"
FOOTER = "FICTIONAL - prepared for case exercise."

DOC_FILES = {
    "D1": "D1_borrower_financial_summary.md",
    "D2": "D2_loan_agreement_excerpt.md",
    "D5": "D5_relationship_history.md",
    "LEDGER": "LEDGER.md",
}

Y = ["FY2023", "FY2024", "FY2025"]
Q = ["Q1 2025", "Q2 2025", "Q3 2025", "Q4 2025", "Q1 2026", "Q2 2026"]


def rows(doc, loc, table, columns):
    """Expand {row: [values per column]} into (item, figure, doc, loc, row, col) entries."""
    out = []
    for row, values in table.items():
        for col, val in zip(columns, values):
            out.append((f"{row} {col}", val, doc, loc, row, col))
    return out


def text(doc, loc, pairs):
    """Expand [(item, figure)] into section or paragraph entries."""
    return [(item, fig, doc, loc, None, None) for item, fig in pairs]


# ---------------------------------------------------------------- Northwind

NW_T1 = {
    "Revenue": ["94,200", "99,800", "104,600"],
    "Revenue growth": ["6.6%", "5.9%", "4.8%"],
    "EBITDA": ["4,200", "4,300", "4,100"],
    "EBITDA margin": ["4.5%", "4.3%", "3.9%"],
    "Net income": ["2,290", "2,180", "1,870"],
    "Unfunded capex": ["600", "650", "700"],
    "Cash taxes": ["700", "680", "600"],
    "Debt service (P+I)": ["2,000", "2,180", "2,200"],
}
NW_T2 = {
    "Cash": ["1,400", "1,100", "900"],
    "Revolver availability": ["3,100", "2,400", "Not provided*"],
    "Liquidity (cash + availability)": ["4,500", "3,500", "n/a*"],
    "Total funded debt": ["10,710", "12,040", "13,120"],
    "Total leverage": ["2.55x", "2.80x", "3.20x"],
    "DSCR": ["1.45x", "1.36x", "1.27x"],
}
NW_T3 = {
    "EBITDA (TTM)": ["4,240", "4,120", "3,980", "4,100", "4,020", "3,950"],
    "Total funded debt": ["12,700", "13,250", "13,570", "13,120", "13,000", "13,350"],
    "Total leverage": ["3.00x", "3.22x", "3.41x", "3.20x", "3.23x", "3.38x"],
    "Unfunded capex (TTM)": ["660", "670", "690", "700", "710", "720"],
    "Cash taxes (TTM)": ["670", "640", "610", "600", "580", "560"],
    "Debt service (TTM)": ["2,190", "2,195", "2,190", "2,200", "2,180", "2,150"],
    "DSCR": ["1.33x", "1.28x", "1.22x", "1.27x", "1.25x", "1.24x"],
}
NW_T4 = {
    "Meridian term loan": ["3,200", "2,400", "1,600"],
    "Meridian revolver": ["4,900", "6,600", "8,100"],
    "Fleet capital leases (Ridgeway Truck Finance)": ["2,610", "3,040", "3,420"],
    "Total funded debt": ["10,710", "12,040", "13,120"],
}

NW_LEDGER = (
    rows("D1", "§1", NW_T1, Y)
    + text("D1", "§1", [("FY2022 revenue (note to Table 1)", "FY2022 revenue was 88,400")])
    + rows("D1", "§2", NW_T2, Y)
    + text("D1", "§2", [
        ("Table 2 footnote: certificate not in spread export", "Borrowing Base Certificate was not included in the spread export"),
    ])
    + rows("D1", "§3", NW_T3, Q)
    + text("D1", "§3", [
        ("Facility $14.0M", "$14.0M"),
        ("Facility $4.0M term loan", "$4.0M term loan"),
        ("Facility $10.0M revolver", "$10.0M revolver"),
        ("No change proposed", "No change in the facility is proposed"),
    ])
    + rows("D1", "§4", NW_T4, Y)
    + text("D1", "§5", [
        ("Customer A FY2024", "21% of FY2024 revenue"),
        ("Customer A FY2025", "23% of FY2025 revenue"),
        ("Top five FY2025", "47% of FY2025 revenue"),
    ])
    + text("D1", "§6", [
        ("Commentary: growth 4.8%", "Revenue grew 4.8% in FY2025"),
        ("Commentary: EBITDA about $4.5 million (deliberate conflict)", "EBITDA was about $4.5 million"),
        ("Commentary: route project May 2026", "May 2026"),
    ])
    + text("D1", "§7", [
        ("Covenant max 3.75x", "3.75x"),
        ("Covenant min 1.20x", "1.20x"),
        ("Q3 2025 certificate date", "November 14, 2025"),
        ("Q3 2025 leverage 3.41x", "3.41x"),
        ("Q3 2025 DSCR 1.22x (tight test)", "DSCR was 1.22x"),
        ("FY2025 certificate date", "April 24, 2026"),
        ("FY2025 leverage 3.20x", "Total leverage was 3.20x"),
        ("FY2025 DSCR 1.27x", "DSCR was 1.27x"),
        ("Q2 2026 certificate date", "August 12, 2026"),
        ("Q2 2026 leverage 3.38x", "Total leverage was 3.38x"),
        ("Q2 2026 DSCR 1.24x", "DSCR was 1.24x"),
    ])
    + text("D2", "__header__", [("D2 agreement date", "December 15, 2022")])
    + text("D2", "§1.1", [
        ("Schedule 1.1 gap (Medium item)", "[Schedule 1.1 not included in this excerpt]"),
        ("Borrowing base accounts 85%", "85% of Eligible Accounts"),
        ("Borrowing base inventory 60%", "60% of Eligible Inventory"),
        ("Inventory cap $4,000,000", "$4,000,000"),
        ("Permitted Tax Distributions in DSCR", "including Permitted Tax Distributions"),
        ("Capital leases in Total Funded Debt", "all Capital Lease Obligations"),
    ])
    + text("D2", "§2.1", [
        ("Term loan $4,000,000", "$4,000,000"),
        ("Quarterly installment $200,000", "$200,000"),
        ("First installment March 31, 2023", "March 31, 2023"),
        ("Maturity December 15, 2027", "December 15, 2027"),
        ("Revolving Commitment $10,000,000", "$10,000,000"),
        ("Revolver for working capital", "working capital and general corporate purposes"),
    ])
    + text("D2", "§2.2", [
        ("Guaranty cap $2,000,000", "$2,000,000"),
        ("Landlord waiver", "Ostrander Properties, LLC"),
        ("Des Moines distribution center", "Des Moines, Iowa"),
    ])
    + text("D2", "§7.1", [("Max leverage 3.75", "3.75 to 1.00")])
    + text("D2", "§7.2", [("Min DSCR 1.20", "1.20 to 1.00")])
    + text("D2", "§7.3", [("Min Excess Availability $1,000,000", "$1,000,000")])
    + text("D2", "§7.4", [
        ("Annual 120 days", "120 days"),
        ("Quarterly 45 days", "45 days"),
        ("First three quarters", "first three fiscal quarters"),
        ("Monthly borrowing base 20 days", "20 days"),
    ])
    + text("D2", "§7.5", [("Purchase-money cap $500,000", "$500,000")])
    + text("D2", "§7.6", [
        ("Low item: primary responsibility", "primary responsibility"),
        ("Low item: within a reasonable period", "within a reasonable period"),
    ])
    + text("D5", "¶1", [
        ("Founded 1987", "Founded 1987"),
        ("Des Moines", "Des Moines, Iowa"),
        ("About 215 employees", "About 215 employees"),
        ("165,000 sq ft", "165,000 sq ft"),
        ("52 trucks", "52 delivery trucks"),
        ("Dale Ostrander 60%", "Dale Ostrander 60%"),
        ("Ruth Ostrander 20%", "Ruth Ostrander 20%"),
        ("Megan Ostrander-Kolb 20%", "Megan Ostrander-Kolb (VP Operations) 20%"),
    ])
    + text("D5", "¶2", [
        ("Customer since 2016", "since 2016"),
        ("Deposits $2.3 million", "$2.3 million"),
        ("Facility $14.0 million", "$14.0 million facility"),
        ("Facility split", "$4.0M term loan, $10.0M revolver"),
        ("Approved December 2022", "December 2022"),
    ])
    + text("D5", "¶3", [
        ("25 days late", "25 days late"),
        ("Waiver number", "W-25-0388"),
    ])
    + text("D5", "¶4", [
        ("Q3 2025 DSCR 1.22x", "1.22x"),
        ("Covenant 1.20x", "1.20x"),
    ])
    + text("D5", "¶5", [
        ("Review due December 15, 2026", "December 15, 2026"),
        ("No change requested", "No change to the facility was requested"),
        ("Dale Ostrander (67)", "Dale Ostrander (67)"),
        ("Step back mid-2027", "mid-2027"),
        ("ESOP up to 30%", "up to 30%"),
        ("No timeline", "no timeline and no engagement letter"),
    ])
)


def nw_arith(g):
    """Northwind recomputations. g(doc, loc, row, col) returns a number from a table cell."""
    out = []
    rev = {y: g("D1", "§1", "Revenue", y) for y in Y}
    rev["FY2022"] = g("D1", "§1", "re", r"FY2022 revenue was ([\d,]+)")
    prev = {"FY2023": "FY2022", "FY2024": "FY2023", "FY2025": "FY2024"}
    for y in Y:
        e = g("D1", "§1", "EBITDA", y)
        out.append((f"Revenue growth {y}", rev[y] / rev[prev[y]] - 1, ("D1", "§1", "Revenue growth", y), "pct"))
        out.append((f"EBITDA margin {y}", e / rev[y], ("D1", "§1", "EBITDA margin", y), "pct"))
        out.append((f"Total leverage {y}", g("D1", "§2", "Total funded debt", y) / e, ("D1", "§2", "Total leverage", y), "x"))
        num = e - g("D1", "§1", "Unfunded capex", y) - g("D1", "§1", "Cash taxes", y)
        out.append((f"DSCR {y}", num / g("D1", "§1", "Debt service (P+I)", y), ("D1", "§2", "DSCR", y), "x"))
        comp = sum(g("D1", "§4", r, y) for r in ["Meridian term loan", "Meridian revolver", "Fleet capital leases (Ridgeway Truck Finance)"])
        out.append((f"Debt composition sums to §4 total {y}", comp, ("D1", "§4", "Total funded debt", y), "int"))
        out.append((f"§4 total equals Table 2 total funded debt {y}", g("D1", "§4", "Total funded debt", y), ("D1", "§2", "Total funded debt", y), "int"))
        build = sum(g("LEDGER", "Debt service build", r, y) for r in [
            "Term loan principal", "Term loan interest", "Revolver interest", "Capital lease principal", "Capital lease interest"])
        out.append((f"Debt service build sums to D1 debt service {y}", build, ("D1", "§1", "Debt service (P+I)", y), "int"))
        out.append((f"LEDGER build total equals D1 {y}", g("LEDGER", "Debt service build", "Debt service (P+I)", y), ("D1", "§1", "Debt service (P+I)", y), "int"))
        roll = (g("LEDGER", "Capital lease roll-forward", "Opening capital leases", y)
                - g("LEDGER", "Capital lease roll-forward", "Capital lease principal", y)
                + g("LEDGER", "Capital lease roll-forward", "New capital leases", y))
        out.append((f"Lease roll-forward closes to D1 §4 {y}", roll, ("D1", "§4", "Fleet capital leases (Ridgeway Truck Finance)", y), "int"))
        out.append((f"Lease principal in roll-forward equals build {y}", g("LEDGER", "Capital lease roll-forward", "Capital lease principal", y),
                    ("LEDGER", "Debt service build", "Capital lease principal", y), "int"))
    for y in ["FY2023", "FY2024"]:
        liq = g("D1", "§2", "Cash", y) + g("D1", "§2", "Revolver availability", y)
        out.append((f"Liquidity {y}", liq, ("D1", "§2", "Liquidity (cash + availability)", y), "int"))
    # Term loan: 4,000 less 800 a year (D2 §2.1(a): 200 per quarter)
    for i, y in enumerate(Y, 1):
        out.append((f"Term loan balance after {4 * i} installments of 200 ({y})", 4000 - 800 * i, ("D1", "§4", "Meridian term loan", y), "int"))
        out.append((f"Term principal in build equals 4 x 200 ({y})", 800, ("LEDGER", "Debt service build", "Term loan principal", y), "int"))
    # Lease opening balance equals prior closing
    for a, b in [("FY2023", "FY2024"), ("FY2024", "FY2025")]:
        out.append((f"Lease opening {b} equals closing {a}", g("LEDGER", "Capital lease roll-forward", "Closing capital leases", a),
                    ("LEDGER", "Capital lease roll-forward", "Opening capital leases", b), "int"))
    # Interest from stated balances and rates (LEDGER.md assumptions)
    rates = [
        ("Term loan interest", "FY2023", 3600, 0.0775), ("Term loan interest", "FY2024", 2800, 0.0775), ("Term loan interest", "FY2025", 2000, 0.0725),
        ("Revolver interest", "FY2023", 4500, 0.0750), ("Revolver interest", "FY2024", 5800, 0.0750), ("Revolver interest", "FY2025", 7400, 0.0700),
        ("Capital lease interest", "FY2023", 2530, 0.055), ("Capital lease interest", "FY2024", 2825, 0.065), ("Capital lease interest", "FY2025", 3230, 0.0675),
    ]
    for row, y, bal, r in rates:
        out.append((f"{row} {y} = {bal:,} x {r * 100:.2f}%", half_up(bal * r), ("LEDGER", "Debt service build", row, y), "int"))
    # Term loan average balances behind the rate checks
    for y, avg in [("FY2023", 3600), ("FY2024", 2800), ("FY2025", 2000)]:
        prev_bal = 4000 if y == "FY2023" else g("D1", "§4", "Meridian term loan", Y[Y.index(y) - 1])
        out.append((f"Term loan average balance {y}", (prev_bal + g("D1", "§4", "Meridian term loan", y)) / 2, ("const", avg), "int"))
    # Quarterly covenant tests
    for q in Q:
        e = g("D1", "§3", "EBITDA (TTM)", q)
        out.append((f"Total leverage {q}", g("D1", "§3", "Total funded debt", q) / e, ("D1", "§3", "Total leverage", q), "x"))
        num = e - g("D1", "§3", "Unfunded capex (TTM)", q) - g("D1", "§3", "Cash taxes (TTM)", q)
        out.append((f"DSCR {q}", num / g("D1", "§3", "Debt service (TTM)", q), ("D1", "§3", "DSCR", q), "x"))
    for t3, t1loc, t1 in [("EBITDA (TTM)", "§1", "EBITDA"), ("Total funded debt", "§2", "Total funded debt"),
                          ("Unfunded capex (TTM)", "§1", "Unfunded capex"), ("Cash taxes (TTM)", "§1", "Cash taxes"),
                          ("Debt service (TTM)", "§1", "Debt service (P+I)")]:
        out.append((f"Q4 2025 {t3} equals FY2025", g("D1", "§3", t3, "Q4 2025"), ("D1", t1loc, t1, "FY2025"), "int"))
    # Facility total
    out.append(("Facility $14.0M = $4.0M term + $10.0M revolver", 4.0 + 10.0, ("const", 14.0), "m1"))
    return out


# ---------------------------------------------------------------- Harborline

HB_T1 = {
    "Revenue": ["38,600", "42,100", "45,800"],
    "Revenue growth": ["9.0%", "9.1%", "8.8%"],
    "EBITDA": ["3,820", "4,250", "4,700"],
    "EBITDA margin": ["9.9%", "10.1%", "10.3%"],
    "Net income": ["1,000", "1,200", "1,590"],
    "Unfunded capex": ["400", "450", "500"],
    "Cash taxes": ["380", "470", "560"],
    "Debt service (P+I)": ["2,460", "2,475", "2,400"],
}
HB_T2 = {
    "Cash": ["1,900", "2,300", "2,750"],
    "Revolver availability": ["1,800", "1,600", "1,400"],
    "Liquidity (cash + availability)": ["3,700", "3,900", "4,150"],
    "Total funded debt": ["14,350", "13,950", "13,550"],
    "Total leverage": ["3.76x", "3.28x", "2.88x"],
    "DSCR": ["1.24x", "1.35x", "1.52x"],
}
HB_C3 = ["Harborline FY2025", "Acquired practices", "Pro forma (FY2025 basis)"]
HB_T3 = {
    "Revenue": ["45,800", "10,400", "56,200"],
    "EBITDA": ["4,700", "1,200", "5,900"],
    "EBITDA margin": ["10.3%", "11.5%", "10.5%"],
    "Unfunded capex": ["500", "100", "600"],
    "Cash taxes": ["560", "80", "640"],
    "Total funded debt": ["13,550", "730", "21,830*"],
    "Total leverage": ["2.88x", "n/a", "3.70x*"],
    "Debt service": ["2,400", "n/a", "3,670"],
    "DSCR": ["1.52x", "n/a", "1.27x"],
}
HB_C4 = Y + ["Pro forma"]
HB_T4 = {
    "Halvard Commercial Bank term loan": ["11,050", "10,250", "9,450", "n/a"],
    "Halvard Commercial Bank revolver": ["1,200", "1,400", "1,600", "n/a"],
    "Meridian term loan": ["n/a", "n/a", "n/a", "17,000"],
    "Meridian revolver": ["n/a", "n/a", "n/a", "1,600"],
    "Equipment capital leases (Kestrel Dental Equipment Finance)": ["2,100", "2,300", "2,500", "3,230"],
    "Seller note (Practice 2)": ["n/a", "n/a", "n/a", "Not provided*"],
    "Total funded debt": ["14,350", "13,950", "13,550", "21,830"],
}

HB_LEDGER = (
    rows("D1", "§1", HB_T1, Y)
    + text("D1", "§1", [("FY2022 revenue (note to Table 1)", "FY2022 revenue was 35,400")])
    + rows("D1", "§2", HB_T2, Y)
    + text("D1", "§2", [("Halvard revolver $3.0M", "$3.0M revolver")])
    + rows("D1", "§3", HB_T3, HB_C3)
    + text("D1", "§3", [
        ("Practice 1 revenue and EBITDA", "Brightmere Family Dental (revenue 6,100, EBITDA 700)"),
        ("Practice 2 revenue and EBITDA", "Silverpine Dental Studio (revenue 4,300, EBITDA 500)"),
        ("Assumed leases 730", "funded debt of 730"),
        ("Request $22.0M", "$22.0M in total"),
        ("Request $17.0M term loan", "$17.0M term loan"),
        ("Request $5.0M revolver", "$5.0M revolver"),
        ("Use: refinance Halvard term 9,450", "Halvard term loan 9,450"),
        ("Use: Practice 1 cash price 4,300", "Practice 1 cash purchase price 4,300"),
        ("Use: Practice 2 cash price 2,850", "Practice 2 cash purchase price 2,850"),
        ("Use: fees 400", "fees 400"),
        ("Use: total 17,000", "total of 17,000"),
        ("Revolver draw 1,600", "revolver draw of 1,600"),
        ("Footnote: seller note excluded (deliberate gap)", "pro forma total funded debt and total leverage exclude it"),
    ])
    + rows("D1", "§4", HB_T4, HB_C4)
    + text("D1", "§5", [
        ("Payer A FY2024", "36% of FY2024 revenue"),
        ("Payer A FY2025", "38% of FY2025 revenue"),
        ("Top three payers", "61% of FY2025 revenue"),
        ("Medicaid 12%", "Medicaid dental programs accounted for 12%"),
        ("Self-pay 17%", "patient self-pay for 17%"),
    ])
    + text("D1", "§6", [
        ("Commentary: growth 8.8%", "Revenue grew 8.8% in FY2025"),
        ("Commentary: pro forma EBITDA about $6.3 million (deliberate conflict)", "pro forma EBITDA is about $6.3 million"),
    ])
    + text("D1", "§7", [
        ("Halvard certificate date", "April 22, 2026"),
        ("Halvard leverage 2.88x", "2.88x"),
        ("Halvard max 4.00x", "4.00x"),
        ("Halvard DSCR 1.52x", "1.52x"),
        ("Halvard min 1.20x", "1.20x"),
    ])
    + text("D2", "__header__", [("Draft date", "Sept 30, 2026")])
    + text("D2", "§1.1", [
        ("Schedule 1.1 gap (Medium item)", "[Schedule 1.1 not included in this excerpt]"),
        ("Seller Note in Total Funded Debt", "and the Seller Note"),
        ("Selling Dentists defined", "Dr. Elliot Brandsma and Dr. Nadia Fairweather"),
        ("QoE report", "Ashgrove Advisory LLC"),
    ])
    + text("D2", "§2.1", [
        ("Term loan $17,000,000", "$17,000,000"),
        ("Term maturity five years", "five years after the Closing Date"),
        ("Twelve-year amortization", "twelve-year schedule"),
        ("Revolving Commitment $5,000,000", "$5,000,000"),
    ])
    + text("D2", "§2.2", [("Guaranty cap $3,000,000", "$3,000,000")])
    + text("D2", "§7.1", [
        ("Max leverage 4.00", "4.00 to 1.00"),
        ("Step-down 3.75", "3.75 to 1.00"),
        ("Step-down 3.50", "3.50 to 1.00"),
        ("First step-down date", "December 31, 2027"),
        ("Second step-down date", "December 31, 2028"),
    ])
    + text("D2", "§7.2", [("Min DSCR 1.20", "1.20 to 1.00")])
    + text("D2", "§7.3", [
        ("Acquisition cap $2,000,000 each", "$2,000,000"),
        ("Acquisition cap $5,000,000 a year", "$5,000,000"),
    ])
    + text("D2", "§7.4", [
        ("Annual 120 days", "120 days"),
        ("Quarterly 45 days", "45 days"),
        ("Payer report", "report of revenue by payer"),
    ])
    + text("D2", "§7.5", [("Purchase-money cap $750,000", "$750,000")])
    + text("D2", "§7.6", [
        ("Low item: substantially the levels contemplated", "substantially the levels contemplated"),
        ("Low item: within a reasonable time", "within a reasonable time"),
    ])
    + text("D5", "¶1", [
        ("Founded 2014", "Founded 2014"),
        ("Grand Rapids", "Grand Rapids, Michigan"),
        ("16 practices", "16 affiliated general dentistry practices"),
        ("About 420 employees", "About 420 employees"),
        ("Marchetti 45%", "Dr. Lena Marchetti 45%"),
        ("Tasker 30%", "Owen Tasker (CEO) 30%"),
        ("Achterberg 15%", "Dr. Samuel Achterberg 15%"),
        ("Management pool 10%", "management equity pool 10%"),
    ])
    + text("D5", "¶2", [
        ("Customer since 2021", "since 2021"),
        ("Deposits $3.4 million", "$3.4 million"),
        ("No credit exposure", "no credit exposure"),
    ])
    + text("D5", "¶3", [
        ("Request $22.0 million", "$22.0 million"),
        ("Request split", "$17.0M term loan, $5.0M revolver"),
        ("Target closing", "December 15, 2026"),
        ("Seller note terms open", "still being negotiated"),
    ])
    + text("D5", "¶4", [
        ("Payer A renewal date", "June 30, 2027"),
        ("Proposed fee cut 3%", "3% reduction"),
    ])
    + text("D5", "¶5", [
        ("Three-year employment agreements", "three-year employment agreements"),
        ("Fairweather (61)", "Dr. Fairweather (61)"),
        ("Three clinical days", "three clinical days a week"),
        ("Marchetti (58)", "Dr. Lena Marchetti (58)"),
    ])
)


def hb_arith(g):
    out = []
    rev = {y: g("D1", "§1", "Revenue", y) for y in Y}
    rev["FY2022"] = g("D1", "§1", "re", r"FY2022 revenue was ([\d,]+)")
    prev = {"FY2023": "FY2022", "FY2024": "FY2023", "FY2025": "FY2024"}
    for y in Y:
        e = g("D1", "§1", "EBITDA", y)
        out.append((f"Revenue growth {y}", rev[y] / rev[prev[y]] - 1, ("D1", "§1", "Revenue growth", y), "pct"))
        out.append((f"EBITDA margin {y}", e / rev[y], ("D1", "§1", "EBITDA margin", y), "pct"))
        out.append((f"Total leverage {y}", g("D1", "§2", "Total funded debt", y) / e, ("D1", "§2", "Total leverage", y), "x"))
        num = e - g("D1", "§1", "Unfunded capex", y) - g("D1", "§1", "Cash taxes", y)
        out.append((f"DSCR {y}", num / g("D1", "§1", "Debt service (P+I)", y), ("D1", "§2", "DSCR", y), "x"))
        out.append((f"Liquidity {y}", g("D1", "§2", "Cash", y) + g("D1", "§2", "Revolver availability", y),
                    ("D1", "§2", "Liquidity (cash + availability)", y), "int"))
        out.append((f"Revolver availability {y} = 3,000 less Halvard revolver", 3000 - g("D1", "§4", "Halvard Commercial Bank revolver", y),
                    ("D1", "§2", "Revolver availability", y), "int"))
        comp = sum(g("D1", "§4", r, y) for r in ["Halvard Commercial Bank term loan", "Halvard Commercial Bank revolver",
                                                  "Equipment capital leases (Kestrel Dental Equipment Finance)"])
        out.append((f"Debt composition sums to §4 total {y}", comp, ("D1", "§4", "Total funded debt", y), "int"))
        out.append((f"§4 total equals Table 2 total funded debt {y}", g("D1", "§4", "Total funded debt", y), ("D1", "§2", "Total funded debt", y), "int"))
        roll = (g("LEDGER", "Capital lease roll-forward", "Opening capital leases", y)
                - g("LEDGER", "Capital lease roll-forward", "Capital lease principal", y)
                + g("LEDGER", "Capital lease roll-forward", "New capital leases", y))
        out.append((f"Lease roll-forward closes to D1 §4 {y}", roll, ("D1", "§4", "Equipment capital leases (Kestrel Dental Equipment Finance)", y), "int"))
        out.append((f"Lease principal in roll-forward equals build {y}", g("LEDGER", "Capital lease roll-forward", "Capital lease principal", y),
                    ("LEDGER", "Debt service build", "Capital lease principal", y), "int"))
    for y in Y + ["Pro forma"]:
        build = sum(g("LEDGER", "Debt service build", r, y) for r in [
            "Term loan principal", "Term loan interest", "Revolver interest", "Capital lease principal", "Capital lease interest"])
        target = ("D1", "§1", "Debt service (P+I)", y) if y != "Pro forma" else ("D1", "§3", "Debt service", "Pro forma (FY2025 basis)")
        out.append((f"Debt service build sums to D1 debt service ({y})", build, target, "int"))
        out.append((f"LEDGER build total equals D1 ({y})", g("LEDGER", "Debt service build", "Debt service (P+I)", y), target, "int"))
    for a, b in [("FY2023", "FY2024"), ("FY2024", "FY2025")]:
        out.append((f"Lease opening {b} equals closing {a}", g("LEDGER", "Capital lease roll-forward", "Closing capital leases", a),
                    ("LEDGER", "Capital lease roll-forward", "Opening capital leases", b), "int"))
        out.append((f"Halvard term loan falls by 800 in {b}", g("D1", "§4", "Halvard Commercial Bank term loan", a) - 800,
                    ("D1", "§4", "Halvard Commercial Bank term loan", b), "int"))
    # Historical interest from stated balances and rates
    rates = [
        ("Term loan interest", "FY2023", 11450, 0.075), ("Term loan interest", "FY2024", 10650, 0.075), ("Term loan interest", "FY2025", 9850, 0.0675),
        ("Revolver interest", "FY2023", 1100, 0.0725), ("Revolver interest", "FY2024", 1300, 0.0725), ("Revolver interest", "FY2025", 1400, 0.065),
        ("Capital lease interest", "FY2023", 2025, 0.06), ("Capital lease interest", "FY2024", 2200, 0.06), ("Capital lease interest", "FY2025", 2400, 0.06),
    ]
    for row, y, bal, r in rates:
        out.append((f"{row} {y} = {bal:,} x {r * 100:.2f}%", half_up(bal * r), ("LEDGER", "Debt service build", row, y), "int"))
    for y, avg in [("FY2024", 10650), ("FY2025", 9850)]:
        p = Y[Y.index(y) - 1]
        out.append((f"Halvard term average balance {y}", (g("D1", "§4", "Halvard Commercial Bank term loan", p)
                                                         + g("D1", "§4", "Halvard Commercial Bank term loan", y)) / 2, ("const", avg), "int"))
    # Pro forma build from D2 §2.1(a) amortization and LEDGER.md rates
    term = g("D1", "§4", "Meridian term loan", "Pro forma")
    principal = half_up(term / 12)
    out.append(("Pro forma term principal = 17,000 / 12 (twelve-year schedule)", principal, ("LEDGER", "Debt service build", "Term loan principal", "Pro forma"), "int"))
    out.append(("Pro forma term interest = (17,000 - principal / 2) x 6.50%", half_up((term - (term / 12) / 2) * 0.065),
                ("LEDGER", "Debt service build", "Term loan interest", "Pro forma"), "int"))
    out.append(("Pro forma revolver interest = 1,600 x 6.25%", half_up(g("D1", "§4", "Meridian revolver", "Pro forma") * 0.0625),
                ("LEDGER", "Debt service build", "Revolver interest", "Pro forma"), "int"))
    out.append(("Pro forma lease interest = 3,230 x 6.0%", half_up(g("D1", "§4", "Equipment capital leases (Kestrel Dental Equipment Finance)", "Pro forma") * 0.06),
                ("LEDGER", "Debt service build", "Capital lease interest", "Pro forma"), "int"))
    # Table 3 pro forma columns
    H, A, P = HB_C3
    for row in ["Revenue", "EBITDA", "Unfunded capex", "Cash taxes"]:
        out.append((f"Pro forma {row} = Harborline + acquired", g("D1", "§3", row, H) + g("D1", "§3", row, A), ("D1", "§3", row, P), "int"))
    for col in HB_C3:
        out.append((f"EBITDA margin ({col})", g("D1", "§3", "EBITDA", col) / g("D1", "§3", "Revenue", col), ("D1", "§3", "EBITDA margin", col), "pct"))
    for row, t1loc, t1 in [("Revenue", "§1", "Revenue"), ("EBITDA", "§1", "EBITDA"), ("Unfunded capex", "§1", "Unfunded capex"),
                           ("Cash taxes", "§1", "Cash taxes"), ("Total funded debt", "§2", "Total funded debt"),
                           ("Debt service", "§1", "Debt service (P+I)")]:
        out.append((f"Table 3 Harborline {row} equals FY2025", g("D1", "§3", row, H), ("D1", t1loc, t1, "FY2025"), "int"))
    out.append(("Acquired revenue = 6,100 + 4,300", 6100 + 4300, ("D1", "§3", "Revenue", A), "int"))
    out.append(("Acquired EBITDA = 700 + 500", 700 + 500, ("D1", "§3", "EBITDA", A), "int"))
    pf_debt = sum(g("D1", "§4", r, "Pro forma") for r in ["Meridian term loan", "Meridian revolver",
                                                           "Equipment capital leases (Kestrel Dental Equipment Finance)"])
    out.append(("Pro forma debt composition sums to §4 total (seller note excluded)", pf_debt, ("D1", "§4", "Total funded debt", "Pro forma"), "int"))
    out.append(("§4 pro forma total equals Table 3", g("D1", "§4", "Total funded debt", "Pro forma"), ("D1", "§3", "Total funded debt", P), "int"))
    out.append(("Pro forma leases = 2,500 + 730 assumed", g("D1", "§4", "Equipment capital leases (Kestrel Dental Equipment Finance)", "FY2025")
                + g("D1", "§3", "Total funded debt", A), ("D1", "§4", "Equipment capital leases (Kestrel Dental Equipment Finance)", "Pro forma"), "int"))
    out.append(("Pro forma total leverage", g("D1", "§3", "Total funded debt", P) / g("D1", "§3", "EBITDA", P), ("D1", "§3", "Total leverage", P), "x"))
    num = g("D1", "§3", "EBITDA", P) - g("D1", "§3", "Unfunded capex", P) - g("D1", "§3", "Cash taxes", P)
    out.append(("Pro forma DSCR", num / g("D1", "§3", "Debt service", P), ("D1", "§3", "DSCR", P), "x"))
    out.append(("Term loan uses = 9,450 + 4,300 + 2,850 + 400", 9450 + 4300 + 2850 + 400, ("D1", "§4", "Meridian term loan", "Pro forma"), "int"))
    out.append(("Refinanced Halvard term equals FY2025 balance", 9450, ("D1", "§4", "Halvard Commercial Bank term loan", "FY2025"), "int"))
    out.append(("Revolver draw equals Halvard revolver refinanced", g("D1", "§4", "Halvard Commercial Bank revolver", "FY2025"),
                ("D1", "§4", "Meridian revolver", "Pro forma"), "int"))
    out.append(("Facility $22.0M = $17.0M term + $5.0M revolver", 17.0 + 5.0, ("const", 22.0), "m1"))
    out.append(("Policy test: pro forma leverage above 3.50x (D4 §4.2.1)", 1.0 if g("D1", "§3", "Total leverage", P) > 3.50 else 0.0, ("const", 1.0), "bool"))
    out.append(("Policy test: pro forma DSCR at or above 1.25x (D4 §4.2.2)", 1.0 if g("D1", "§3", "DSCR", P) >= 1.25 else 0.0, ("const", 1.0), "bool"))
    out.append(("Policy test: Payer A above 25% (D4 §4.2.4)", 1.0 if g("D1", "§5", "re", r"(\d+)% of FY2025 revenue") > 0.25 else 0.0, ("const", 1.0), "bool"))
    return out


CASES = {
    "northwind_annual_review": (NW_LEDGER, nw_arith),
    "harborline_new_money_exception": (HB_LEDGER, hb_arith),
}


# ---------------------------------------------------------------- engine

def half_up(v):
    return int(v + 0.5) if v >= 0 else -int(-v + 0.5)


def to_num(s):
    s = s.strip().rstrip("*").replace(",", "").replace("$", "")
    if s.endswith("%"):
        return float(s[:-1]) / 100
    if s.endswith("x"):
        s = s[:-1]
    return float(s)


def fmt(v, kind):
    if kind == "x":
        return f"{half_up(v * 100) / 100:.2f}x"
    if kind == "pct":
        return f"{half_up(v * 1000) / 10:.1f}%"
    if kind == "m1":
        return f"{v:.1f}"
    if kind == "bool":
        return "yes" if v else "no"
    return f"{half_up(v):,}"


def table_cell(blocks, loc, row, col):
    for b in find_block(blocks, loc):
        for table in b.tables:
            header = table[0]
            if col not in header:
                continue
            ci = header.index(col)
            for r in table[1:]:
                if r and r[0] == row:
                    return r[ci] if ci < len(r) else None
    return None


def check_presence(blocks, entry):
    item, figure, doc, loc, row, col = entry
    if row is not None and col is not None:
        cell = table_cell(blocks, loc, row, col)
        if cell is None:
            return False, f"row {row!r} / column {col!r} not found"
        return cell == figure, f"cell = {cell!r}"
    if loc.startswith("¶"):
        for b in blocks:
            for p in b.paras:
                if p.lstrip().startswith(loc) and figure in p:
                    return True, "in paragraph"
        return False, f"paragraph {loc} with figure not found"
    found = find_block(blocks, loc)
    if not found:
        return False, f"location {loc} not found"
    for b in found:
        if figure in b.text or figure in b.heading:
            return True, "in section text"
        for table in b.tables:
            for r in table:
                if any(figure in c for c in r):
                    return True, "in section table"
    return False, "figure not in section"


def run_case(case):
    folder = CASES_DIR / case
    ledger, arith = CASES[case]
    docs = {d: parse_markdown(folder / f) for d, f in DOC_FILES.items()}

    presence = [(e, *check_presence(docs[e[2]], e)) for e in ledger]

    def g(doc, loc, row, col):
        if row == "re":
            for b in find_block(docs[doc], loc):
                m = re.search(col, b.text)
                if m:
                    return to_num(m.group(1))
            raise KeyError(f"{doc} {loc} pattern {col!r} not found")
        cell = table_cell(docs[doc], loc, row, col)
        if cell is None:
            raise KeyError(f"{doc} {loc} row {row!r} column {col!r} not found")
        return to_num(cell)

    arithmetic = []
    for label, value, ref, kind in arith(g):
        computed = fmt(value, kind)
        if ref[0] == "const":
            stated = fmt(ref[1], kind)
            where = "constant"
        else:
            stated_raw = table_cell(docs[ref[0]], ref[1], ref[2], ref[3])
            stated = fmt(to_num(stated_raw), kind)
            where = f"{ref[0]} {ref[1]}, row {ref[2]}, column {ref[3]}"
        arithmetic.append((label, computed, stated, where, computed == stated))

    labeling = []
    for d in ["D1", "D2", "D5"]:
        lines = [ln for ln in (folder / DOC_FILES[d]).read_text(encoding="utf-8").splitlines() if ln.strip()]
        labeling.append((f"{d} title line contains SYNTHETIC", lines[0], "SYNTHETIC" in lines[0] and lines[0].startswith(f"# {d}.")))
        labeling.append((f"{d} ends with footer", lines[-1], lines[-1] == FOOTER))
    return presence, arithmetic, labeling


def render(case, presence, arithmetic, labeling):
    out = [f"# Ledger reconciliation: {case}", "",
           "Every figure in this case's numbers ledger, where it appears, and whether it was found exactly as written;",
           "then every ratio, total and build recomputed from the tables. Generated by build/check_case_ledgers.py.",
           "Figures are $ in thousands unless the figure string says otherwise. Markdown only.", "",
           "## Part 1: Figures in the documents", "",
           "| # | Item | Figure | Document | Location | Result | Note |", "|---|---|---|---|---|---|---|"]
    for n, (e, ok, note) in enumerate(presence, 1):
        item, figure, doc, loc, row, col = e
        where = loc if row is None else f"{loc}, row {row}, column {col}"
        if loc == "__header__":
            where = "header"
        out.append(f"| {n} | {item} | {figure} | {doc} | {where} | {'PASS' if ok else 'FAIL'} | {note} |")
    p_ok = sum(1 for _, ok, _ in presence if ok)
    out += ["", f"**Figures: {p_ok} of {len(presence)} checks PASS.**", "",
            "## Part 2: Arithmetic recomputed", "",
            "| # | Check | Computed | Stated | Stated at | Result |", "|---|---|---|---|---|---|"]
    for n, (label, comp, stated, where, ok) in enumerate(arithmetic, 1):
        out.append(f"| {n} | {label} | {comp} | {stated} | {where} | {'PASS' if ok else 'FAIL'} |")
    a_ok = sum(1 for *_, ok in arithmetic if ok)
    out += ["", f"**Arithmetic: {a_ok} of {len(arithmetic)} checks PASS.**", "",
            "## Part 3: Labeling", "", "| # | Check | Line | Result |", "|---|---|---|---|"]
    for n, (label, line, ok) in enumerate(labeling, 1):
        out.append(f"| {n} | {label} | {line.replace('|', 'pipe')} | {'PASS' if ok else 'FAIL'} |")
    l_ok = sum(1 for *_, ok in labeling if ok)
    out += ["", f"**Labeling: {l_ok} of {len(labeling)} checks PASS.**", ""]
    return "\n".join(out), (p_ok, len(presence)), (a_ok, len(arithmetic)), (l_ok, len(labeling))


def dash_scan():
    files = sorted(CASES_DIR.rglob("*.md")) + [D6_FILE, Path(__file__).resolve()]
    hits = []
    for f in files:
        for i, line in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            for ch, name in [("\u2014", "em dash"), ("\u2013", "en dash"), ("\u2012", "figure dash"), ("\u2015", "horizontal bar")]:
                if ch in line:
                    hits.append(f"{f.relative_to(ROOT)}:{i}: {name}")
    return files, hits


def check_d6():
    lines = [ln for ln in D6_FILE.read_text(encoding="utf-8").splitlines() if ln.strip()]
    text_all = "\n".join(lines)
    checks = [
        ("D6 title", lines[0].startswith("# D6. [SYNTHETIC SUMMARY] SR 26-2")),
        ("D6 verify notice", "Verify against the letter at federalreserve.gov before relying on it." in text_all),
        ("D6 sections §1 to §6", all(f"## §{i} " in text_all for i in range(1, 7))),
        ("D6 Sources section", "## Sources" in text_all),
        ("D6 prototype assumption bracket", "[Prototype assumption:" in text_all),
        ("D6 footer", lines[-1] == FOOTER),
    ]
    return checks


def main():
    failed_any = False
    for case in CASES:
        presence, arithmetic, labeling = run_case(case)
        body, p, a, l = render(case, presence, arithmetic, labeling)
        (CASES_DIR / case / "LEDGER_CHECK.md").write_text(body, encoding="utf-8")
        print(f"{case}: figures {p[0]} of {p[1]} PASS; arithmetic {a[0]} of {a[1]} PASS; labeling {l[0]} of {l[1]} PASS")
        for e, ok, note in presence:
            if not ok:
                failed_any = True
                print(f"  FAIL figure: {e[0]} -> expected {e[1]!r} in {e[2]} {e[3]} ({note})")
        for label, comp, stated, where, ok in arithmetic:
            if not ok:
                failed_any = True
                print(f"  FAIL arithmetic: {label}: computed {comp}, stated {stated} at {where}")
        for label, line, ok in labeling:
            if not ok:
                failed_any = True
                print(f"  FAIL labeling: {label}: {line!r}")
    d6 = check_d6()
    print(f"D6 shared summary: {sum(ok for _, ok in d6)} of {len(d6)} PASS")
    for label, ok in d6:
        if not ok:
            failed_any = True
            print(f"  FAIL: {label}")
    files, hits = dash_scan()
    print(f"Dash scan: {len(files)} files, {len(hits)} em or en dashes found")
    for h in hits:
        failed_any = True
        print(f"  {h}")
    sys.exit(1 if failed_any else 0)


if __name__ == "__main__":
    main()
