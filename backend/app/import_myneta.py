"""
Lok Sabha 2024 candidate affidavits from MyNeta (Association for Democratic Reforms).

Two page types are combined, joined on MyNeta's candidate_id:
  - "candidates analysed" summary pages: name, constituency, party, cases, education, assets, liabilities
  - per-state candidate lists: which state each candidate_id contested in

Pages are cached under backend/data_cache/myneta/ so re-runs don't hit the site again,
and live requests are rate limited. robots.txt only disallows print views.

Run from backend/:  python -m app.cli ingest-candidates
"""
import datetime
import hashlib
import os
import re
import time
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from .database import SessionLocal, ensure_schema
from . import models
from .states import canonical_state

BASE_URL = "https://myneta.info/LokSabha2024/"
SUMMARY_URL = BASE_URL + "index.php?action=summary&subAction=candidates_analyzed&sort=candidate&page={page}"
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data_cache", "myneta")
REQUEST_DELAY = float(os.environ.get("MYNETA_DELAY_SECONDS", "1.5"))
USER_AGENT = "Raven/1.1 (open-data research; respects robots.txt)"
SOURCE_NAME = "MyNeta / ADR (Lok Sabha 2024 affidavits)"
ELECTION_YEAR = 2024

# MyNeta party labels -> internal party IDs (others are stored under their MyNeta label)
PARTY_ALIASES = {
    "BJP": "BJP", "INC": "INC", "AITC": "AITC", "SP": "SP", "DMK": "DMK", "TDP": "TDP",
    "YSRCP": "YSRCP", "BJD": "BJD", "BRS": "BRS", "AAP": "AAP", "BSP": "BSP", "RJD": "RJD",
    "JD(U)": "JDU", "JD(S)": "JDS", "JMM": "JMM", "SAD": "SAD", "AIADMK": "AIADMK",
    "SKM": "SKM", "AIMIM": "AIMIM", "RSP": "RSP", "JKNC": "JKNC", "JNP": "JSP",
}

_session = requests.Session()
_session.headers["User-Agent"] = USER_AGENT
_last_request = 0.0


def fetch(url: str) -> str:
    global _last_request
    os.makedirs(CACHE_DIR, exist_ok=True)
    path = os.path.join(CACHE_DIR, hashlib.sha1(url.encode()).hexdigest() + ".html")
    if os.path.exists(path):
        with open(path, encoding="utf-8") as f:
            return f.read()
    wait = REQUEST_DELAY - (time.monotonic() - _last_request)
    if wait > 0:
        time.sleep(wait)
    for attempt in range(3):
        try:
            resp = _session.get(url, timeout=60)
            resp.raise_for_status()
            break
        except requests.RequestException:
            if attempt == 2:
                raise
            time.sleep(5 * (attempt + 1))
    _last_request = time.monotonic()
    with open(path, "w", encoding="utf-8") as f:
        f.write(resp.text)
    return resp.text


def parse_rupees(text: str) -> float:
    """'Rs 2,74,39,170 ~ 2 Crore+' -> 27439170.0 ; 'Nil' -> 0.0"""
    head = text.split("~")[0]
    digits = re.sub(r"[^\d]", "", head)
    return float(digits) if digits else 0.0


def _candidate_id(href: str) -> int | None:
    qs = parse_qs(urlparse(href).query)
    value = qs.get("candidate_id", [None])[0]
    return int(value) if value and value.isdigit() else None


def _candidate_table(html: str):
    soup = BeautifulSoup(html, "html.parser")
    for table in soup.find_all("table"):
        header = [c.get_text(" ", strip=True) for c in table.find("tr").find_all(["th", "td"])] if table.find("tr") else []
        if any(h.startswith("Candidate") for h in header) and any("Assets" in h for h in header):
            return soup, header, table.find_all("tr")[1:]
    return soup, [], []


def _pick_link(row, slug: str | None):
    """MyNeta rows sometimes nest a broken '/candidate.php' link before the real one; prefer the election's own."""
    links = row.find_all("a", href=re.compile("candidate_id="))
    if not links:
        return None
    if slug:
        for a in links:
            if f"/{slug.lower()}/" in a["href"].lower():
                return a
    for a in links:
        if not a["href"].startswith("/candidate.php"):
            return a
    return links[0]


def parse_summary_page(html: str, base_url: str = BASE_URL, slug: str | None = None) -> list[dict]:
    _, header, rows = _candidate_table(html)
    col = {h.rstrip("∇").strip(): i for i, h in enumerate(header)}
    out = []
    for row in rows:
        cells = row.find_all("td")
        link = _pick_link(row, slug)
        if len(cells) < len(header) or not link:
            continue
        cid = _candidate_id(link["href"])
        if cid is None:
            continue
        text = lambda name: cells[col[name]].get_text(" ", strip=True)  # noqa: E731
        try:
            cases = int(re.sub(r"[^\d]", "", text("Criminal Case")) or 0)
        except KeyError:
            cases = 0
        out.append({
            "candidate_id": cid,
            "name": text("Candidate") or link.get_text(" ", strip=True),
            "constituency": text("Constituency").rstrip("∇ ").title(),
            "party": text("Party"),
            "criminal_cases": cases,
            "education": text("Education"),
            "assets": parse_rupees(text("Total Assets")),
            "liabilities": parse_rupees(text("Liabilities")),
            "source_url": urljoin(base_url, link["href"]),
        })
    return out


def election_url(slug: str) -> str:
    return f"https://myneta.info/{slug}/"


SORTS = ["candidate", "constituency", "party", "criminal", "edu", "asset", "liabi"]


def published_totals(slug: str) -> dict[str, int]:
    """'Total candidates/winners analyzed' as published on the election's home page."""
    text = BeautifulSoup(fetch(election_url(slug)), "html.parser").get_text(" ", strip=True)
    found = re.findall(r"Total (candidates|winners) analyzed by NEW\D{0,80}?(\d[\d,]*)", text)
    return {kind: int(n.replace(",", "")) for kind, n in found}


def summary_rows(slug: str, sub_action: str, expected: int | None = None, max_pages: int = 1000) -> dict[int, dict]:
    """
    Rows of a MyNeta summary listing (e.g. winner_analyzed).

    MyNeta's pagination is unstable: each sort order silently skips some rows across page boundaries.
    Taking the union over several sort orders recovers them; we stop once the published total is reached.
    """
    base = election_url(slug)
    rows: dict[int, dict] = {}
    for sort in SORTS:
        seen_this_sort: set[int] = set()
        for page in range(1, max_pages + 1):
            url = f"{base}index.php?action=summary&subAction={sub_action}&sort={sort}&page={page}"
            found = parse_summary_page(fetch(url), base_url=base, slug=slug)
            new = [r for r in found if r["candidate_id"] not in seen_this_sort]
            if not new:  # empty page, or MyNeta repeating the last page
                break
            for r in new:
                seen_this_sort.add(r["candidate_id"])
                rows.setdefault(r["candidate_id"], r)
        if expected is not None and len(rows) >= expected:
            break
    return rows


def constituency_ids(slug: str) -> list[int]:
    return sorted({int(n) for n in re.findall(r"show_candidates&constituency_id=(\d+)", fetch(election_url(slug)))})


def parse_constituency_page(html: str, base_url: str, slug: str) -> tuple[str, str, list[dict]]:
    """(constituency, region, candidates). Region is the state on Lok Sabha pages, the district on assembly pages."""
    soup, header, rows = _candidate_table(html)
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    m = re.match(r"List of Candidates in (.+?) : (.+?) (?:Lok Sabha \d{4}|[A-Za-z ]+ \d{4})$", title)
    constituency, region = (m.group(1).title(), m.group(2)) if m else ("", "")
    col = {h: i for i, h in enumerate(header)}
    out = []
    for row in rows:
        cells = row.find_all("td")
        link = _pick_link(row, slug)
        if not link or len(cells) < len(header) or (cid := _candidate_id(link["href"])) is None:
            continue
        text = lambda name: cells[col[name]].get_text(" ", strip=True)  # noqa: E731
        assets_cell, liab_cell = cells[col["Total Assets"]], cells[col["Liabilities"]]
        out.append({
            "candidate_id": cid,
            "name": link.get_text(" ", strip=True),
            "constituency": constituency,
            "party": text("Party"),
            "criminal_cases": int(re.sub(r"\D", "", text("Criminal Cases")) or 0),
            "education": text("Education"),
            # MyNeta renders winners' figures as images here; those are filled from text sources instead
            "assets": None if assets_cell.find("img") else parse_rupees(assets_cell.get_text(" ", strip=True)),
            "liabilities": None if liab_cell.find("img") else parse_rupees(liab_cell.get_text(" ", strip=True)),
            "is_winner": "Winner" in cells[col["Candidate"]].get_text(" ", strip=True),
            "source_url": urljoin(base_url, link["href"]),
        })
    return constituency, region, out


def candidate_page_figures(slug: str, candidate_id: int) -> tuple[float, float] | None:
    """Assets and liabilities as text from the candidate's own MyNeta page."""
    text = BeautifulSoup(fetch(f"{election_url(slug)}candidate.php?candidate_id={candidate_id}"), "html.parser")\
        .get_text(" ", strip=True)
    assets = re.search(r"Assets:\s*(Rs\s*[\d,]+|Nil)", text)
    liabilities = re.search(r"Liabilities:\s*(Rs\s*[\d,]+|Nil)", text)
    if not (assets and liabilities):
        return None
    return parse_rupees(assets.group(1)), parse_rupees(liabilities.group(1))


def _fill_figures(slug: str, rows: list[dict], text_rows: dict[int, dict]) -> int:
    """Fill missing assets/liabilities from summary listings, then candidate pages. Returns rows still missing."""
    missing = 0
    for r in rows:
        if r["assets"] is not None and r["liabilities"] is not None:
            continue
        src = text_rows.get(r["candidate_id"])
        figures = (src["assets"], src["liabilities"]) if src else candidate_page_figures(slug, r["candidate_id"])
        if figures:
            r["assets"], r["liabilities"] = figures
        else:
            r["assets"], r["liabilities"] = r["assets"] or 0.0, r["liabilities"] or 0.0
            missing += 1
    return missing


def _party_id(label: str, db, party_ids: set) -> str:
    label = label or "IND"
    pid = PARTY_ALIASES.get(label, label[:60])
    if pid not in party_ids:
        db.add(models.Party(id=pid, name=label, symbol_url=""))
        party_ids.add(pid)
    return pid


def _replace_election(election: str, house: str, year: int, rows: list[dict], legacy_year: int | None = None) -> None:
    """Swap one election's rows in a single transaction."""
    db = SessionLocal()
    try:
        party_ids = {p.id for p in db.query(models.Party.id)}
        stale = models.Candidate.election == election
        if legacy_year is not None:  # rows imported before the election column existed
            stale = stale | ((models.Candidate.election.is_(None)) & (models.Candidate.year == legacy_year))
        db.query(models.Candidate).filter(stale).delete(synchronize_session=False)
        now = datetime.datetime.utcnow()
        mappings = [{
            "name": r["name"],
            "party_id": _party_id(r["party"], db, party_ids),
            "state": r["state"],
            "constituency": r["constituency"],
            "year": year,
            "election": election,
            "house": house,
            "is_winner": r["is_winner"],
            "assets": r["assets"],
            "liabilities": r["liabilities"],
            "criminal_cases": r["criminal_cases"],
            "education": r["education"],
            "source_name": f"MyNeta / ADR ({election} affidavits)",
            "source_url": r["source_url"],
            "created_at": now,
        } for r in rows]
        db.flush()
        db.bulk_insert_mappings(models.Candidate, mappings)
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def run_import() -> dict:
    """Every Lok Sabha 2024 candidate, read constituency by constituency (complete, unlike the paged lists)."""
    ensure_schema()
    slug = "LokSabha2024"
    base = election_url(slug)
    rows: dict[int, dict] = {}
    for cid in constituency_ids(slug):
        constituency, region, candidates = parse_constituency_page(
            fetch(f"{base}index.php?action=show_candidates&constituency_id={cid}"), base, slug)
        for c in candidates:
            rows[c["candidate_id"]] = {**c, "state": canonical_state(region)}

    totals = published_totals(slug)
    winners_text = summary_rows(slug, "winner_analyzed", expected=totals.get("winners"))
    rows_list = list(rows.values())
    unresolved = _fill_figures(slug, rows_list, winners_text)
    _replace_election("Lok Sabha 2024", "Lok Sabha", ELECTION_YEAR, rows_list, legacy_year=ELECTION_YEAR)
    return {
        "candidates_imported": len(rows_list),
        "published_total": totals.get("candidates"),
        "winners": sum(r["is_winner"] for r in rows_list),
        "published_winners": totals.get("winners"),
        "without_state": sum(r["state"] == "Unknown" for r in rows_list),
        "figures_unavailable": unresolved,
        "with_criminal_cases": sum(r["criminal_cases"] > 0 for r in rows_list),
    }


def latest_assemblies() -> dict[str, str]:
    """State name -> MyNeta slug of its most recent assembly election that has published winners."""
    home = BeautifulSoup(fetch("https://myneta.info/"), "html.parser")
    out = {}
    for a in home.find_all("a", href=True):
        if "state_assembly.php?state=" not in a["href"]:
            continue
        state = a.get_text(" ", strip=True)
        page = fetch(a["href"].replace("http://", "https://"))
        slugs = {(int(year), slug) for slug, year in re.findall(r"href=[\"']?/?([A-Za-z_]+?(\d{4}))/", page)}
        for _, slug in sorted(slugs, reverse=True):
            if published_totals(slug).get("winners"):
                out[state] = slug
                break
    return out


def run_assembly_import(only_states: list[str] | None = None) -> dict:
    """Sitting MLAs: winners of each state's latest assembly election, checked against MyNeta's published count."""
    ensure_schema()
    report = {}
    for state_label, slug in sorted(latest_assemblies().items()):
        state = canonical_state(state_label)
        if only_states and state not in only_states:
            continue
        year = int(re.search(r"(\d{4})", slug).group(1))
        election = f"{state} {year}"
        expected = published_totals(slug).get("winners")
        winners = summary_rows(slug, "winner_analyzed", expected=expected)
        if expected and len(winners) < expected:
            # Last resort: walk the constituency pages for winners the listings never showed
            base = election_url(slug)
            for cid in constituency_ids(slug):
                _, _, candidates = parse_constituency_page(
                    fetch(f"{base}index.php?action=show_candidates&constituency_id={cid}"), base, slug)
                for c in candidates:
                    if c["is_winner"] and c["candidate_id"] not in winners:
                        _fill_figures(slug, [c], {})
                        winners[c["candidate_id"]] = c
                if len(winners) >= expected:
                    break
        rows = [{**w, "state": state, "is_winner": True} for w in winners.values()]
        if rows:
            _replace_election(election, "Vidhan Sabha", year, rows)
        report[election] = {"imported": len(rows), "published": expected}
    return {
        "assemblies": len(report),
        "mlas_imported": sum(r["imported"] for r in report.values()),
        "mlas_published": sum(r["published"] or 0 for r in report.values()),
        "short": {e: r for e, r in report.items() if r["published"] and r["imported"] < r["published"]},
        "by_election": report,
    }


if __name__ == "__main__":
    import json
    print(json.dumps(run_import(), indent=2))
