import csv

from app.import_electoral_bonds import load_purchases, load_redemptions, parse_amount, parse_disclosure_date
from app.import_fcra_bulk import determine_sector, parse_year
from app.parties import party_id_for


def test_fiscal_year_runs_april_to_march():
    assert parse_disclosure_date("12/Apr/2019") == ("2019-04-12", 2019)
    assert parse_disclosure_date("15/Mar/2020") == ("2020-03-15", 2019)
    assert parse_disclosure_date("garbage") == (None, None)


def test_indian_grouped_amounts():
    assert parse_amount("1,00,00,000") == 10_000_000
    assert parse_amount(" 10,00,000 ") == 1_000_000


def test_party_lookup_ignores_spacing_and_case():
    assert party_id_for("YSR  CONGRESS PARTY  (YUVAJANA SRAMIKA RYTHU CONGRESS PARTY)") == "YSRCP"
    assert party_id_for("bharatiya janata party") == "BJP"
    assert party_id_for("NOT A PARTY") is None


def test_redemptions_join_purchases_on_bond_number(tmp_path):
    purchases = tmp_path / "p.csv"
    with open(purchases, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Sr", "URN", "Journal", "Purchase", "Expiry", "Name", "Prefix", "Number", "Denom", "Branch", "Teller", "Status"])
        w.writerow([1, "u", "12/Apr/2019", "12/Apr/2019", "26/Apr/2019", "acme ltd", "TL", "11448", "10,00,000", "1", "1", "Paid"])

    redemptions = tmp_path / "r.csv"
    with open(redemptions, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["Sr", "Date", "Party", "Acct", "Prefix", "Number", "Denom", "Branch", "Teller"])
        w.writerow([1, "20/Apr/2019", "BIJU JANATA DAL", "x", "TL", "11448", "10,00,000", "00800", "1"])
        w.writerow([2, "20/Apr/2019", "BIJU JANATA DAL", "x", "TL", "11448", "10,00,000", "00800", "1"])  # duplicate
        w.writerow([3, "20/Apr/2019", "BIJU JANATA DAL", "x", "OC", "1", "1,00,000", "00800", "1"])

    bought = load_purchases(str(purchases))
    encashed = load_redemptions(str(redemptions))

    assert len(encashed) == 2
    assert bought.get(encashed[0]["bond_key"]) == "ACME LTD"
    assert bought.get(encashed[1]["bond_key"]) is None  # unmatched -> UNKNOWN DONOR, never guessed


def test_fcra_year_is_fiscal_start_year():
    assert parse_year("2020-2021") == 2020
    assert parse_year("") is None


def test_sector_is_name_based_and_neutral():
    assert determine_sector("ST. MARY'S CHURCH TRUST") == "Faith-based"
    assert determine_sector("SHRI RAM MANDIR SAMITI") == "Faith-based"
    assert determine_sector("RURAL HEALTH SOCIETY") == "Healthcare & Research"
    assert determine_sector("AADHAR") == "Social Relief / Other"


def test_state_names_are_canonical():
    from app.states import canonical_state
    assert canonical_state("Jammu & Kashmir") == "Jammu and Kashmir"
    assert canonical_state("Jammu And Kashmir") == "Jammu and Kashmir"
    assert canonical_state("ORISSA") == "Odisha"
    assert canonical_state("Andaman & Nicobar") == "Andaman and Nicobar Islands"
    assert canonical_state("Pondicherry") == "Puducherry"
    assert canonical_state(None) == "Unknown"


def test_entity_resolution_merges_spellings_not_distinct_entities():
    from collections import Counter
    from app.entities import resolve
    m = resolve(Counter({
        "VEDANTA LIMITED": 380, "VEDANTA LTD": 42,
        "MEGHA ENGINEERING AND INFRASTRUCTURES LI MITED": 803,
        "MEGHA ENGINEERING & INFRASTRUCTURES LIMITED": 72,
        "B G SHIRKE CONSTRUCTION TECHNOLOGY PVT L TD": 113, "BG SHIRKE CONSTRUCTION TECHNOLOGY PVT LTD": 6,
        "WARORA CHANDRAPUR BALLARPUR TOLLRO": 3, "WARORA CHANDRAPUR BALLARPUR TOLLROA": 5,
        "KISHAN M AGARWAL": 1, "KISHAN M AGARWAL HUF": 1,
    }))
    assert m["VEDANTA LTD"] == m["VEDANTA LIMITED"] == "VEDANTA LIMITED"
    assert m["MEGHA ENGINEERING & INFRASTRUCTURES LIMITED"] == "MEGHA ENGINEERING AND INFRASTRUCTURES LIMITED"
    assert m["BG SHIRKE CONSTRUCTION TECHNOLOGY PVT LTD"] == m["B G SHIRKE CONSTRUCTION TECHNOLOGY PVT L TD"]
    assert m["WARORA CHANDRAPUR BALLARPUR TOLLRO"] == "WARORA CHANDRAPUR BALLARPUR TOLLROA"  # truncated in source
    assert m["KISHAN M AGARWAL"] != m["KISHAN M AGARWAL HUF"]  # an HUF is a separate legal entity


def test_myneta_rupee_parsing():
    from app.import_myneta import parse_rupees
    assert parse_rupees("Rs\xa02,74,39,170 ~ 2\xa0Crore+") == 27439170
    assert parse_rupees("Nil") == 0


def test_fcra_status_list_column_detection():
    from app.import_fcra_status import extract_registration_numbers
    rows = [
        ["List of associations whose registration is cancelled"],
        ["S.No", "Name of Association", "FCRA Registration No.", "State"],
        ["1", "Some Trust", "231650112", "Delhi"],
        ["2", "Other Society", " 075900983 ", "Tamil Nadu"],
        ["", "", "", ""],
    ]
    assert extract_registration_numbers(rows) == ["231650112", "075900983"]
