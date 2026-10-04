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
    assert canonical_state("DELHI (NCT)") == "Delhi"
    assert canonical_state("Chattisgarh") == "Chhattisgarh"
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
        "FUTURE GAMING AND HOTEL SERVICES PR": 1180,
        "FUTURE GAMING AND HOTEL SERVICES PRIVATE LIMITED": 93, "FUTURE GAMING AND HOTEL SERVICES PVT LTD": 64,
    }))
    # Cut off mid-"PRIVATE": still the same company
    assert m["FUTURE GAMING AND HOTEL SERVICES PR"] == m["FUTURE GAMING AND HOTEL SERVICES PVT LTD"] \
        == "FUTURE GAMING AND HOTEL SERVICES PRIVATE LIMITED"
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


def test_myneta_constituency_page_marks_winner_and_defers_image_figures():
    from app.import_myneta import parse_constituency_page, election_url
    html = """<html><head><title>List of Candidates in WEST DELHI : DELHI (NCT) Lok Sabha 2024</title></head><body><table>
      <tr><th>SNo</th><th>Candidate</th><th>Party</th><th>Criminal Cases</th><th>Education</th><th>Age</th>
          <th>Total Assets</th><th>Liabilities</th></tr>
      <tr><td>3</td><td><a href=candidate.php?candidate_id=7624>Winning Person</a><b>&nbsp<font> Winner </font></td>
          <td>BJP</td><td><span><b> 1 </b></span></td><td>10th Pass</td><td>53</td>
          <td><img src=x.png></td><td><img src=y.png></td></tr>
      <tr><td>1</td><td><a href=candidate.php?candidate_id=8727>Other Person</a><b></td>
          <td>IND</td><td>0</td><td>12th Pass</td><td>63</td>
          <td>Rs&nbsp;54,42,410<br><span> ~ 54&nbsp;Lacs+</span></td><td>Rs&nbsp;17,00,000</td></tr>
    </table></body></html>"""
    constituency, region, rows = parse_constituency_page(html, election_url("LokSabha2024"), "LokSabha2024")
    assert (constituency, region) == ("West Delhi", "DELHI (NCT)")
    multi_word = html.replace("WEST DELHI : DELHI (NCT) Lok Sabha 2024", "LUCKNOW : UTTAR PRADESH Lok Sabha 2024")
    assert parse_constituency_page(multi_word, election_url("LokSabha2024"), "LokSabha2024")[:2] == ("Lucknow", "UTTAR PRADESH")
    winner, other = rows
    assert winner["is_winner"] and winner["criminal_cases"] == 1 and winner["assets"] is None
    assert not other["is_winner"] and other["assets"] == 5442410 and other["liabilities"] == 1700000
    assert winner["source_url"] == "https://myneta.info/LokSabha2024/candidate.php?candidate_id=7624"


def test_myneta_prefers_the_elections_own_candidate_link():
    from app.import_myneta import parse_summary_page, election_url
    html = """<table>
      <tr><th>Sno</th><th>Candidate</th><th>Constituency</th><th>Party</th><th>Criminal Case</th>
          <th>Education</th><th>Total Assets</th><th>Liabilities</th></tr>
      <tr><td>1</td><td><a href=/candidate.php?candidate_id=7087><a href=/Karnataka2023/candidate.php?candidate_id=7087>M.Y.Patil</a></a></td>
          <td>AFZALPUR</td><td>INC</td><td>0</td><td>Graduate</td><td>Rs 4,69,32,109 ~ 4 Crore+</td><td>Rs 0 ~</td></tr>
    </table>"""
    [row] = parse_summary_page(html, base_url=election_url("Karnataka2023"), slug="Karnataka2023")
    assert row["source_url"] == "https://myneta.info/Karnataka2023/candidate.php?candidate_id=7087"
    assert row["name"] == "M.Y.Patil" and row["constituency"] == "Afzalpur" and row["assets"] == 46932109


def test_question_mentions_are_conservative():
    from app.import_questions import distinctive_name, find_mentions
    assert distinctive_name("VEDANTA LIMITED") is None  # single word core: too ambiguous
    assert distinctive_name("MEGHA ENGINEERING AND INFRASTRUCTURES LIMITED") == "MEGHA ENGINEERING AND INFRASTRUCTURES"
    assert distinctive_name("FUTURE GAMING AND HOTEL SERVICES PR") is None  # no legal form, could be truncated
    assert distinctive_name("LAKSHMI NIWAS MITTAL") is None  # individuals are never matched
    assert distinctive_name("INDIA POWER LIMITED") is None  # generic words only
    assert distinctive_name("INFRASTRUCTURE LOGISTICS PVT LTD") is None  # an ordinary phrase in titles
    assert distinctive_name("MARUTI SUZUKI INDIA LTD") == "MARUTI SUZUKI"
    titles = {1: "Contracts awarded to Megha Engineering and Infrastructures",
              2: "Megha rainfall in Engineering colleges"}
    assert find_mentions(titles, ["MEGHA ENGINEERING AND INFRASTRUCTURES LIMITED"]) == [
        (1, "MEGHA ENGINEERING AND INFRASTRUCTURES LIMITED", "MEGHA ENGINEERING AND INFRASTRUCTURES")]


def test_api_endpoints_respond_on_an_empty_database(tmp_path):
    """Smoke test: on a brand-new database every list/stats endpoint returns 200, not a 500."""
    import os
    import subprocess
    import sys
    script = """
from fastapi.testclient import TestClient
from app.main import app
paths = ["/api/v1/parties", "/api/v1/parties/scoreboard", "/api/v1/donations", "/api/v1/donations/stats", "/api/v1/candidates",
         "/api/v1/candidates/state-summary", "/api/v1/candidates/elections", "/api/v1/ngos",
         "/api/v1/ngos/stats", "/api/v1/ngos/state-totals", "/api/v1/mp-activity/stats", "/api/v1/questions",
         "/api/v1/questions/stats", "/api/v1/questions/ministries", "/api/v1/bonds/flows", "/api/v1/seats/lok-sabha-2024", "/api/v1/asset-growth",
         "/api/v1/search?q=ab", "/api/v1/insights", "/api/v1/data-quality", "/api/v1/brief/latest", "/api/v1/sources"]
with TestClient(app) as client:
    bad = [(p, client.get(p).status_code) for p in paths]
    bad = [b for b in bad if b[1] != 200]
    assert not bad, bad
print("ok")
"""
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'empty.db'}", "GROQ_API_KEY": ""}
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run([sys.executable, "-c", script], cwd=backend, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-2000:]


def test_rate_limit_returns_429_when_enabled(tmp_path):
    import os
    import subprocess
    import sys
    script = """
from fastapi.testclient import TestClient
from app.main import app
with TestClient(app) as client:
    codes = [client.get("/api/v1/parties").status_code for _ in range(4)]
    assert codes == [200, 200, 200, 429], codes
    assert client.get("/").status_code == 200  # non-API paths are not limited
print("ok")
"""
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'rl.db'}", "RATE_LIMIT_PER_MINUTE": "3", "GROQ_API_KEY": ""}
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run([sys.executable, "-c", script], cwd=backend, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-2000:]


def test_lok_sabha_by_elections_are_separate_elections():
    from app.import_myneta import split_region
    assert split_region("UTTAR PRADESH") == ("Uttar Pradesh", "Lok Sabha 2024", 2024)
    assert split_region("Bye Election On 13-11-2024 : Kerala") == ("Kerala", "Lok Sabha by-election 2024-11-13", 2024)


def test_cross_dataset_endpoints_on_fixture_data(tmp_path):
    """Profiles, key facts, flows and map summaries return the right values on a small fixture database."""
    import os
    import subprocess
    import sys
    script = r"""
import datetime
from fastapi.testclient import TestClient
from app.database import SessionLocal, ensure_schema
from app import models as m

ensure_schema()
db = SessionLocal()
now = datetime.datetime.utcnow()
db.add_all([
    m.Party(id="AAA", name="Alpha Party"), m.Party(id="Alpha Party", name="Alpha Party"),  # same name, two IDs
    m.Party(id="BBB", name="Beta Party"),
    m.Donor(id=1, name="ACME INDUSTRIES LIMITED", industry="Unknown"),
    m.Donor(id=2, name="UNKNOWN DONOR", industry="Unknown"),
])
for i, (donor, party, amt) in enumerate([(1, "AAA", 3e7), (1, "BBB", 1e7), (2, "AAA", 1e7)]):
    db.add(m.Donation(donor_id=donor, party_id=party, amount=amt, date="2022-04-0%d" % (i + 1), year=2022,
                      funding_type="Electoral Bond", source_name="t", source_url="t"))
base = dict(assets=5e7, liabilities=0, education="Graduate", source_name="t", source_url="t", year=2024, house="Lok Sabha")
db.add_all([
    m.Candidate(name="Asha Rao", party_id="AAA", state="Kerala", constituency="Kurnool", election="Lok Sabha 2024",
                is_winner=True, criminal_cases=2, **base),
    m.Candidate(name="Ravi Rao", party_id="BBB", state="Kerala", constituency="Kurnool", election="Lok Sabha 2024",
                is_winner=False, criminal_cases=0, **base),
    m.Candidate(name="New Member", party_id="AAA", state="Kerala", constituency="Kurnool",
                election="Lok Sabha by-election 2024-11-13", is_winner=True, criminal_cases=0, **base),
])
db.add(m.MPActivity(mp_name="New Member", constituency="Kurnoolu", party_name="Alpha Party",
                    state_represented="Kerala", attendance_pct=90.0, debates_count=1, questions_count=2,
                    bills_introduced=0, official_url="t"))
db.add(m.ParliamentQuestion(lok_sabha=18, date="2024-12-01", title="Acme Industries contracts", question_type="Unstarred",
                            ministry="Mines", representative="New Member", official_url="t", source_url="t"))
db.commit()
mp_id = db.query(m.MPActivity.id).scalar()

with TestClient(app_module.app) as c:
    mp = c.get(f"/api/v1/mps/{mp_id}/profile").json()
    assert mp["party_id"] == "AAA", mp["party_id"]                       # duplicate party name resolved
    assert mp["affidavit"]["name_on_affidavit"] == "New Member", mp      # by-election winner, fuzzy seat name
    assert mp["questions_total"] == 1

    party = c.get("/api/v1/parties/AAA/profile").json()
    assert party["bonds"]["total"] == 4e7 and party["bonds"]["undisclosed_purchaser_amount"] == 1e7
    assert party["lok_sabha_2024"]["winners"] == 1                       # by-election not counted as 2024 win

    facts = {f["id"]: f["text"] for f in c.get("/api/v1/insights").json()}
    assert "80%" in facts["top_party"], facts["top_party"]               # 4 of 5 crore
    assert "100% of Lok Sabha MPs" in facts["mp_cases"], facts["mp_cases"]

    flows = c.get("/api/v1/bonds/flows").json()
    assert {l["party_name"] for l in flows["links"]} == {"Alpha Party", "Beta Party"}
    assert all(n["name"] != "UNKNOWN DONOR" for n in flows["nodes"])

    summary = c.get("/api/v1/candidates/state-summary").json()
    assert summary["Kerala"]["candidate_count"] == 2                     # general election only

    asha = db.query(m.Candidate.id).filter(m.Candidate.name == "Asha Rao").scalar()
    prof = c.get(f"/api/v1/candidates/{asha}/profile").json()
    assert prof["party"] == "Alpha Party" and prof["is_winner"]
    assert [x["name"] for x in prof["seat_field"]] == ["Asha Rao", "Ravi Rao"]   # same election only, winner first
    assert c.get("/api/v1/candidates/999999/profile").status_code == 404
print("ok")
"""
    script = script.replace("from fastapi.testclient import TestClient", "from fastapi.testclient import TestClient\nimport app.main as app_module")
    env = {**os.environ, "DATABASE_URL": f"sqlite:///{tmp_path / 'fixture.db'}", "GROQ_API_KEY": ""}
    backend = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    result = subprocess.run([sys.executable, "-c", script], cwd=backend, env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr[-3000:]


def test_release_diff_reports_changed_new_and_removed_tables():
    from app.export_release import diff_manifests
    previous = {"files": [{"table": "donations", "rows": 10, "sha256": "a"},
                          {"table": "ngos", "rows": 5, "sha256": "b"},
                          {"table": "old", "rows": 1, "sha256": "c"}]}
    current = [{"table": "donations", "rows": 12, "sha256": "z"},
               {"table": "ngos", "rows": 5, "sha256": "b"},
               {"table": "parliament_questions", "rows": 7, "sha256": "q"}]
    changes = {c["table"]: c for c in diff_manifests(previous, current)}
    assert changes["donations"]["row_change"] == 2
    assert "ngos" not in changes                       # unchanged
    assert changes["parliament_questions"]["status"] == "new"
    assert changes["old"]["status"] == "removed"


def test_asset_comparison_parsing():
    from app.import_asset_growth import parse_amount, parse_page
    assert parse_amount("4,35,49,09,793 435\xa0Crore+") == 4354909793
    html = """<table><tr><th>Sno</th><th>Name (Party)</th><th>Total Assets in Lok Sabha 2024</th>
      <th>Total Assets in Lok Sabha 2019</th><th>Asset Increase</th><th>% Increase in Asset</th><th>Remarks</th></tr>
      <tr><td>1</td><td><a href="index.php?action=affidavitComparison&myneta_folder2=LokSabha2019&id1=5225&id2=4846">
      Dr Gaddam Ranjith Reddy (INC)</a></td><td>4,35,49,09,793 435 Crore+</td><td>1,63,46,95,131 163 Crore+</td>
      <td>2,72,02,14,662</td><td>166%</td><td>Party in last election was TRS</td></tr></table>"""
    [r] = parse_page(html)
    assert (r["myneta_id"], r["previous_myneta_id"], r["party"]) == (5225, 4846, "INC")
    assert r["name"] == "Dr Gaddam Ranjith Reddy" and r["previous_assets"] == 1634695131
    assert r["remarks"] == "Party in last election was TRS"
    from app.import_asset_growth import election_label
    assert election_label("LokSabha2019") == "Lok Sabha 2019"
    assert election_label("karnataka2018", "Karnataka") == "Karnataka 2018"


def test_member_term_name_matching_is_conservative():
    from app.import_member_terms import same_person
    assert same_person("L. S. Tejasvi Surya", "Tejasvi Surya")
    assert same_person("Dr. Shashi Tharoor", "Shashi Tharoor")
    assert same_person("Chavda Vinod Lakhamashi", "Chavda Vinod Lakhamshi")   # spelling variant
    assert not same_person("S.P.Y. Reddy", "Byreddy Shabari")   # father and daughter, same seat
    assert same_person("C. R. Patil", "Chandrakant Raghunath Patil")
    assert not same_person("K.C. Patel", "Dhaval Laxmanbhai Patel")   # predecessor, same seat
    assert not same_person("P.L. Punia", "Tanuj Punia")               # father and son
    assert not same_person("M. Selvaraj", "Selvaraj V")
    assert same_person("Andimuthu Raja", "Raja A") and same_person("P. Balram", "Balram Naik Porika")
    assert not same_person("Ananth Kumar", "Tejasvi Surya")
    # the shorter name's words must all appear in the longer one (seat and state must also match when linking)
    assert same_person("Vijay Kumar", "Vijay Kumar Hansdak")
    assert not same_person("Rahul Kumar", "Pankaj Kumar")      # a shared surname alone is not enough
    assert not same_person("A. K.", "A. K.")                  # initials only: nothing significant to compare
