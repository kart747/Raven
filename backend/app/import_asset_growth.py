"""
Declared-asset changes for members who stood again: MPs elected in 2019 who contested 2024, and for each
state's latest assembly election, MLAs from the previous assembly who contested again.

Source: MyNeta (ADR) "Asset comparison for re-contest winners". Each row links the candidate's two
affidavits (id1 / id2), which are stored so the comparison can be checked.
Figures are self-declared; MyNeta's remarks (e.g. party changes) are kept as published.

    python -m app.cli ingest-asset-growth
"""
import datetime
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .database import SessionLocal, ensure_schema
from .import_myneta import fetch, latest_assemblies
from .states import canonical_state
from . import models

COMPARISON = "https://myneta.info/{slug}/index.php?action=recontestAssetsComparison"


def parse_amount(text: str) -> float | None:
    """'4,35,49,09,793 435 Crore+' -> 4354909793.0 (the first, exact figure)."""
    m = re.match(r"\s*([\d,]+)", text or "")
    return float(m.group(1).replace(",", "")) if m else None


def parse_page(html: str, base_url: str = COMPARISON.format(slug="LokSabha2024")) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    table = next((t for t in soup.find_all("table") if "Asset Increase" in t.get_text()), None)
    if table is None:
        return []
    out = []
    for tr in table.find_all("tr")[1:]:
        cells = [c.get_text(" ", strip=True) for c in tr.find_all("td")]
        link = tr.find("a", href=re.compile("affidavitComparison"))
        if len(cells) < 6 or not link:
            continue
        qs = parse_qs(urlparse(link["href"]).query)
        now, before = parse_amount(cells[2]), parse_amount(cells[3])
        if now is None or before is None:
            continue
        m = re.match(r"(.+?)\s*\(([^()]*(?:\([^()]*\))?[^()]*)\)\s*$", cells[1])
        name, party = (m.group(1), m.group(2)) if m else (cells[1], None)
        out.append({
            "myneta_id": int(qs["id1"][0]),
            "previous_myneta_id": int(qs["id2"][0]) if qs.get("id2") else None,
            "name": name.strip(), "party": party,
            "assets": now, "previous_assets": before,
            "remarks": cells[6] if len(cells) > 6 and cells[6] else None,
            "source_url": urljoin(base_url, link["href"]),
            "previous_slug": qs.get("myneta_folder2", [None])[0],
        })
    return out


def election_label(slug: str | None, state: str | None = None) -> str | None:
    """'LokSabha2019' -> 'Lok Sabha 2019'; 'karnataka2018' -> 'Karnataka 2018' (state given) ."""
    m = re.match(r"([A-Za-z_]+?)(\d{4})$", slug or "")
    if not m:
        return None
    if m.group(1).lower() in ("loksabha", "ls"):
        return f"Lok Sabha {m.group(2)}"
    return f"{state or m.group(1).title()} {m.group(2)}"


def _store(election: str, rows: list[dict], state: str | None) -> None:
    db = SessionLocal()
    try:
        db.query(models.AssetComparison).filter(models.AssetComparison.election == election).delete(synchronize_session=False)
        now = datetime.datetime.utcnow()
        db.bulk_insert_mappings(models.AssetComparison, [{
            **{k: v for k, v in r.items() if k != "previous_slug"},
            "election": election,
            "previous_election": election_label(r.get("previous_slug"), state) or "previous election",
            "created_at": now,
        } for r in rows])
        db.commit()
    finally:
        db.close()


def run_import(assemblies: bool = True) -> dict:
    ensure_schema()
    targets = [("LokSabha2024", "Lok Sabha 2024", None)]
    if assemblies:
        for state_label, slug in sorted(latest_assemblies().items()):
            state = canonical_state(state_label)
            year = re.search(r"(\d{4})", slug).group(1)
            targets.append((slug, f"{state} {year}", state))
    report = {}
    for slug, election, state in targets:
        url = COMPARISON.format(slug=slug)
        rows = parse_page(fetch(url), base_url=url)
        if rows:
            _store(election, rows, state)
        report[election] = {"comparisons": len(rows), "assets_increased": sum(r["assets"] > r["previous_assets"] for r in rows)}
    return {"elections": len(report), "comparisons": sum(r["comparisons"] for r in report.values()), "by_election": report}
