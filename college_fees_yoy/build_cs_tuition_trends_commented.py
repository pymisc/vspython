#!/usr/bin/env python3
"""Compare published four-year undergraduate tuition for 20 U.S. universities.

Beginner's guide
----------------
1. Download official NCES/IPEDS annual tuition files (2000 through 2024).
2. Select rows belonging to our 20 universities using unique UNITID identifiers.
3. Read annual tuition for in-state and out-of-state students.
4. Add four successive academic years for each hypothetical entering class.
5. Write two CSV files and produce a graph (PNG).

Install: python -m pip install matplotlib
Run:     python build_cs_tuition_trends_commented.py

Change GRAPH_RESIDENCY below to "out_of_state" to compare nonresident rates.
Change INCLUDE_REQUIRED_FEES to False for tuition-only results, matching the
original script's numeric calculation. With True, the chart includes required
fees as well as tuition (when both IPEDS fields are reported).

Cautions:
- Public in-state prices require state residency eligibility. International
  students normally pay nonresident rates but may have additional charges.
- Private universities generally do not have different residency prices.
- Figures are institution-wide undergraduate sticker prices, not specifically
  Computer Science program tuition or actual prices after scholarships.
- No inflation adjustment, living costs, or student-specific fees are included.
- Entry year 2021 is the latest *complete* four-year cohort in 2000–2024 files.
- Missing annual data yields no four-year total; we never invent a value.
- Historical field definitions should be checked against the matching year's
  official IPEDS data dictionary before treating totals as audited results.

Official source: https://nces.ed.gov/ipeds/datacenter/DataFiles.aspx
"""

import csv                 # Read and write comma-separated (.csv) files
import io                  # Treat downloaded bytes/text as file-like objects
from pathlib import Path  # Cross-platform filesystem paths (Windows/Linux)
import urllib.error        # HTTP / network exceptions
import urllib.request      # Download files using Python's standard library
import zipfile             # Read ZIP archives without extracting to disk

# A dictionary maps each display name to (IPEDS institution ID, school type).
# A tuple is an ordered, immutable group of values.
# UNITID is more reliable than searching by school name.
SCHOOLS = {
    "MIT": (166683, "private"),
    "Stanford": (243744, "private"),
    "Carnegie Mellon": (211440, "private"),
    "Princeton": (186131, "private"),
    "Cornell": (190415, "private"),
    "Caltech": (110404, "private"),
    "Harvard": (166027, "private"),
    "Columbia": (190150, "private"),
    "Penn": (215062, "private"),
    "Johns Hopkins": (162928, "private"),
    "UC Berkeley": (110635, "public"),
    "Georgia Tech": (139755, "public"),
    "UIUC": (145637, "public"),
    "UT Austin": (228778, "public"),
    "U Washington": (236948, "public"),
    "UC San Diego": (110680, "public"),
    "U Michigan": (170976, "public"),
    "UCLA": (110662, "public"),
    "Purdue": (243780, "public"),
    "UW Madison": (240444, "public"),
}

FIRST_YEAR = 2000
LAST_YEAR = 2024
DEGREE_YEARS = 4
YEARS = range(FIRST_YEAR, LAST_YEAR + 1)  # Stop of range() is exclusive
ENTRY_YEARS = range(FIRST_YEAR, LAST_YEAR - DEGREE_YEARS + 2)

# Edit these two settings, then rerun the script to change the calculation.
GRAPH_RESIDENCY = "in_state"          # Choose "in_state" or "out_of_state"
INCLUDE_REQUIRED_FEES = True          # False reproduces tuition-only calculation

# Output into the folder containing this program, independent of where you run it.
OUTPUT_DIR = Path(__file__).resolve().parent
DATA_URL = "https://nces.ed.gov/ipeds/datacenter/data/IC{year}_AY.zip"

# IPEDS stores tuition and required fees in separate numeric columns.
# The older script read TUITION2/TUITION3 but not FEE2/FEE3.
FIELD_NAMES = {
    "in_state": ("TUITION2", "FEE2"),
    "out_of_state": ("TUITION3", "FEE3"),
}

# Use a set for fast membership checking when reading thousands of IPEDS rows.
SELECTED_UNITIDS = {school_id for school_id, _kind in SCHOOLS.values()}


def read_number(row, column):
    """Convert one CSV field to a nonnegative number, or return None.

    Example: '12,345' -> 12345.0; '-1' or empty -> None.
    IPEDS uses negative sentinel values for unavailable/not applicable fields.
    """
    raw = (row.get(column) or "").strip().replace(",", "")
    try:
        value = float(raw)
    except ValueError:
        return None
    return value if value >= 0 else None


def annual_price(row, residency):
    """Return tuition (+ mandatory fees if requested) for one institution/year.

    A missing component results in None, not an assumed zero.
    """
    tuition_field, fee_field = FIELD_NAMES[residency]
    tuition = read_number(row, tuition_field)
    if tuition is None:
        return None
    if not INCLUDE_REQUIRED_FEES:
        return tuition
    fee = read_number(row, fee_field)
    return tuition + fee if fee is not None else None


def fetch_year(year):
    """Download one IPEDS ZIP and return {UNITID: {residency: annual_price}}.

    Each CSV row is a dictionary, with column headers as keys.
    The outer dictionary lets us look up a university directly by UNITID.
    """
    url = DATA_URL.format(year=year)
    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})

    # 'with' automatically closes the network response and ZIP file.
    with urllib.request.urlopen(request, timeout=60) as response:
        zip_bytes = response.read()

    # BytesIO wraps downloaded bytes so ZipFile can read them in memory.
    with zipfile.ZipFile(io.BytesIO(zip_bytes)) as archive:
        csv_name = next(
            name for name in archive.namelist()
            if name.lower().endswith(".csv") and "dict" not in name.lower()
        )
        csv_text = archive.read(csv_name).decode("utf-8-sig", errors="replace")

    selected = {}
    for raw_row in csv.DictReader(io.StringIO(csv_text)):
        # Column names occasionally differ in letter case. Normalize to UPPER.
        row = {key.upper(): value for key, value in raw_row.items() if key}
        try:
            unitid = int(row.get("UNITID", ""))
        except ValueError:
            continue  # Bad identifier: skip this row and move to the next

        if unitid not in SELECTED_UNITIDS:
            continue  # We only care about the 20 institutions in SCHOOLS

        selected[unitid] = {
            residency: annual_price(row, residency)
            for residency in FIELD_NAMES
        }
    return selected


def cohort_total(panel, name, entry_year, residency):
    """Add four consecutive annual prices for one entering class.

    panel[(name, year)] is either a residency->price dictionary or missing.
    For entry year 2000, the years used are 2000, 2001, 2002, and 2003.
    Return (total or None, number_of_available_years).
    """
    amounts = []
    for year in range(entry_year, entry_year + DEGREE_YEARS):
        prices = panel.get((name, year), {})
        amounts.append(prices.get(residency))

    available = sum(value is not None for value in amounts)
    if available != DEGREE_YEARS:
        return None, available
    return sum(amounts), available


def write_annual_csv(panel):
    """Write the underlying annual tuition numbers for independent checking."""
    destination = OUTPUT_DIR / "cs_tuition_annual_2000_2024.csv"
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "university", "IPEDS_collection_year", "residency",
            "annual_price_USD", "includes_required_fees", "source_URL"
        ])
        for name in SCHOOLS:
            for year in YEARS:
                for residency in FIELD_NAMES:
                    value = panel.get((name, year), {}).get(residency)
                    writer.writerow([
                        name, year, residency, "" if value is None else int(value),
                        INCLUDE_REQUIRED_FEES, DATA_URL.format(year=year)
                    ])
    print(f"Saved: {destination}")


def write_cohort_csv(panel):
    """Write four-year totals for both residency categories, not just the graph."""
    destination = OUTPUT_DIR / "cs_four_year_cost_by_entry_year.csv"
    with destination.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow([
            "university", "entry_year", "residency", "four_year_price_USD",
            "years_covered", "includes_required_fees"
        ])
        for name in SCHOOLS:
            for entry_year in ENTRY_YEARS:
                for residency in FIELD_NAMES:
                    total, available = cohort_total(panel, name, entry_year, residency)
                    writer.writerow([
                        name, entry_year, residency,
                        "" if total is None else int(total),
                        available, INCLUDE_REQUIRED_FEES
                    ])
    print(f"Saved: {destination}")


def create_graph(panel):
    """Make a line graph: one line per school, one point per entry year."""
    import matplotlib.pyplot as plt  # Only non-standard dependency

    fig, ax = plt.subplots(figsize=(14, 9))
    for name, (_unitid, kind) in SCHOOLS.items():
        x_years = []
        y_thousands = []
        for entry_year in ENTRY_YEARS:
            total, available = cohort_total(panel, name, entry_year, GRAPH_RESIDENCY)
            if total is not None:
                x_years.append(entry_year)
                y_thousands.append(total / 1000)  # $150,000 -> 150 on Y-axis

        if x_years:
            ax.plot(
                x_years, y_thousands, label=name,
                linewidth=1.7, alpha=0.88,
                linestyle="--" if kind == "public" else "-"
            )
        else:
            print(f"WARNING: no complete four-year cohort found for {name}")

    price_label = "Tuition and required fees" if INCLUDE_REQUIRED_FEES else "Tuition only"
    ax.set(
        title=f"Four-year published undergraduate {price_label.lower()} — {GRAPH_RESIDENCY}",
        xlabel="Fall entry year",
        ylabel=f"{price_label} over four years (USD thousands)",
    )
    ax.grid(alpha=0.2)
    ax.legend(ncol=4, fontsize=8, loc="upper left")
    fig.text(
        0.01, 0.01,
        "Source: NCES/IPEDS IC_AY files (2000–2024). Nominal USD; "
        f"{GRAPH_RESIDENCY}; fees included: {INCLUDE_REQUIRED_FEES}. "
        "Excludes living costs and financial aid. Missing data omitted.",
        fontsize=8,
    )
    fig.tight_layout(rect=[0, 0.03, 1, 1])
    destination = OUTPUT_DIR / "top20_cs_four_year_tuition_trends.png"
    fig.savefig(destination, dpi=220)
    plt.close(fig)  # Avoid leaving a Matplotlib figure open in memory
    print(f"Saved: {destination}")


def main():
    """Coordinate download -> cleaning -> CSV exports -> visualization."""
    if GRAPH_RESIDENCY not in FIELD_NAMES:
        raise ValueError("GRAPH_RESIDENCY must be 'in_state' or 'out_of_state'")

    # A dictionary with tuple keys: (university name, academic year).
    panel = {}
    for year in YEARS:
        try:
            rows = fetch_year(year)
            print(f"{year}: found {len(rows)} of {len(SCHOOLS)} selected institutions")
            for name, (unitid, _kind) in SCHOOLS.items():
                if unitid in rows:
                    panel[(name, year)] = rows[unitid]
        except (urllib.error.URLError, zipfile.BadZipFile, StopIteration, TimeoutError) as error:
            # Continue with other years; missing data will be visible in CSVs.
            print(f"WARNING: {year} unavailable: {error}")

    if not panel:
        raise RuntimeError("No IPEDS data downloaded. Check connection and source URLs.")

    write_annual_csv(panel)
    write_cohort_csv(panel)
    create_graph(panel)


# This special check runs main() only when invoked as a script.
# Importing this module from a test file won't start downloading anything.
if __name__ == "__main__":
    main()
