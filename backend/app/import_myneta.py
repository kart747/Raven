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
STATE_URL = BASE_URL + "index.php?action=show_constituencies&state_id={state_id}"
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


def parse_summary_page(html: str) -> list[dict]:
    _, header, rows = _candidate_table(html)
    col = {h.rstrip("∇").strip(): i for i, h in enumerate(header)}
    out = []
    for row in rows:
        cells = row.find_all("td")
        link = row.find("a", href=re.compile("candidate_id="))
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
            "name": link.get_text(" ", strip=True),
            "constituency": text("Constituency").title(),
            "party": text("Party"),
            "criminal_cases": cases,
            "education": text("Education"),
            "assets": parse_rupees(text("Total Assets")),
            "liabilities": parse_rupees(text("Liabilities")),
            "source_url": urljoin(BASE_URL, link["href"]),
        })
    return out


def parse_state_page(html: str) -> tuple[str | None, set[int]]:
    soup, _, rows = _candidate_table(html)
    title = soup.title.get_text(strip=True) if soup.title else ""
    state = title.split(":", 1)[1].strip() if ":" in title else None
    ids = set()
    for row in rows:
        link = row.find("a", href=re.compile("candidate_id="))
        if link and (cid := _candidate_id(link["href"])) is not None:
            ids.add(cid)
    return state, ids


def state_ids() -> list[int]:
    soup = BeautifulSoup(fetch(BASE_URL), "html.parser")
    found = set()
    for a in soup.find_all("a", href=True):
        m = re.search(r"action=show_constituencies&state_id=(\d+)$", a["href"])
        if m:
            found.add(int(m.group(1)))
    return sorted(found)


def run_import(max_pages: int = 1000) -> dict:
    ensure_schema()

    state_by_candidate: dict[int, str] = {}
    for sid in state_ids():
        state, ids = parse_state_page(fetch(STATE_URL.format(state_id=sid)))
        if state:
            for cid in ids:
                state_by_candidate[cid] = canonical_state(state)

    candidates: dict[int, dict] = {}
    for page in range(1, max_pages + 1):
        rows = parse_summary_page(fetch(SUMMARY_URL.format(page=page)))
        if not rows:
            break
        for r in rows:
            candidates[r["candidate_id"]] = r

    db = SessionLocal()
    try:
        party_ids = {p.id for p in db.query(models.Party.id)}
        db.query(models.Candidate).filter(models.Candidate.year == ELECTION_YEAR).delete(synchronize_session=False)

        now = datetime.datetime.utcnow()
        rows, missing_state = [], 0
        for cid, c in candidates.items():
            state = state_by_candidate.get(cid)
            if not state:
                missing_state += 1
                state = "Unknown"
            label = c["party"] or "IND"
            pid = PARTY_ALIASES.get(label, label[:60])
            if pid not in party_ids:
                db.add(models.Party(id=pid, name=label, symbol_url=""))
                party_ids.add(pid)
            rows.append({
                "name": c["name"],
                "party_id": pid,
                "state": state,
                "constituency": c["constituency"],
                "year": ELECTION_YEAR,
                "assets": c["assets"],
                "liabilities": c["liabilities"],
                "criminal_cases": c["criminal_cases"],
                "education": c["education"],
                "source_name": SOURCE_NAME,
                "source_url": c["source_url"],
                "created_at": now,
            })
        db.flush()
        db.bulk_insert_mappings(models.Candidate, rows)
        db.commit()
        return {
            "candidates_imported": len(rows),
            "without_state": missing_state,
            "states": len(set(state_by_candidate.values())),
            "with_criminal_cases": sum(1 for r in rows if r["criminal_cases"] > 0),
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import json
    print(json.dumps(run_import(), indent=2))
