"""
Declared-asset changes for MPs elected in 2019 who stood again in 2024.

Source: MyNeta (ADR) "Asset comparison for re-contest winners", Lok Sabha 2024. Each row links the
candidate's 2024 and 2019 affidavits (id1 / id2), which are stored so the comparison can be checked.
Figures are self-declared; MyNeta's remarks (e.g. party changes) are kept as published.

    python -m app.cli ingest-asset-growth
"""
import datetime
import re
from urllib.parse import parse_qs, urljoin, urlparse

from bs4 import BeautifulSoup

from .database import SessionLocal, ensure_schema
from .import_myneta import fetch
from . import models

URL = "https://myneta.info/LokSabha2024/index.php?action=recontestAssetsComparison"
ELECTION, PREVIOUS = "Lok Sabha 2024", "Lok Sabha 2019"


def parse_amount(text: str) -> float | None:
    """'4,35,49,09,793 435 Crore+' -> 4354909793.0 (the first, exact figure)."""
    m = re.match(r"\s*([\d,]+)", text or "")
    return float(m.group(1).replace(",", "")) if m else None


def parse_page(html: str) -> list[dict]:
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
            "source_url": urljoin(URL, link["href"]),
        })
    return out


def run_import() -> dict:
    ensure_schema()
    rows = parse_page(fetch(URL))
    db = SessionLocal()
    try:
        db.query(models.AssetComparison).filter(models.AssetComparison.election == ELECTION).delete(synchronize_session=False)
        now = datetime.datetime.utcnow()
        db.bulk_insert_mappings(models.AssetComparison, [
            {**r, "election": ELECTION, "previous_election": PREVIOUS, "created_at": now} for r in rows
        ])
        db.commit()
    finally:
        db.close()
    grew = sum(r["assets"] > r["previous_assets"] for r in rows)
    return {"comparisons": len(rows), "assets_increased": grew, "assets_decreased_or_same": len(rows) - grew}
