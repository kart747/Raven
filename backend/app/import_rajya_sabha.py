"""
Sitting members of the Rajya Sabha, from sansad.in's member list (the same data the site's member pages use).

Only public-office facts are kept: name (English and Hindi, as on the record), party, state, term and whether
they are a minister. Addresses, phone numbers and e-mail in the source are deliberately not stored.

    python -m app.cli ingest-rajya-sabha
"""
import datetime
import re
import time

import requests

from .database import SessionLocal, ensure_schema
from .parties import party_id_for
from .states import canonical_state
from . import models

API = "https://sansad.in/api_rs/member/sitting-members"
PAGE_URL = "https://sansad.in/rs/members"
USER_AGENT = "Raven/1.2 (+https://github.com/kart747/Raven; open-data research; respects robots.txt)"

# sansad.in party codes that differ from Raven's party ids (None: no party to link)
PARTY_CODES = {
    "JD(U)": "JDU", "J&KNC": "JKNC", "UPP(L)": "UPPL", "SS": "SHS", "SS-UBT": "SS(UBT)", "NCP-SCP": "NCP(SP)",
    "KC(M)": "KC", "NOM.": None, "IND.": None,
}
_TITLES_EN = r"(?:shri|smt\.?|sh\.?|dr\.?|ms\.?|mrs\.?|kumari|sushri|prof\.?|capt\.?|col\.?|lt\.?|gen\.?|adv\.?|\(retd\.?\))"
_TITLES_HI = ("श्रीमती", "श्री", "सुश्री", "कुमारी", "डा.", "डॉ.", "डॉ", "डा", "प्रो.", "प्रो")


def display_name(record_name: str) -> str:
    """'Sitharaman, Smt. Nirmala' -> 'Nirmala Sitharaman'; 'Abdul Wahab, Shri ' -> 'Abdul Wahab'."""
    last, _, rest = (record_name or "").partition(",")
    return " ".join(re.sub(rf"(?i)(?<![a-z]){_TITLES_EN}(?![a-z])", " ", f"{rest} {last}").split())


def display_name_hi(record_name: str | None) -> str | None:
    if not record_name or not record_name.strip():
        return None
    last, _, rest = record_name.partition(",")
    words = [w for w in rest.split() if w not in _TITLES_HI]
    return " ".join(words + last.split()) or None


def _iso(date: str | None) -> str | None:
    try:
        return datetime.datetime.strptime((date or "").strip(), "%d/%m/%Y").date().isoformat()
    except ValueError:
        return None


def parse(records: list[dict], party_ids: set[str]) -> list[dict]:
    rows = []
    for r in records:
        if (r.get("status") or "").strip() != "Sitting":
            continue
        code = (r.get("partyCode") or "").strip()
        if code in PARTY_CODES:
            pid = PARTY_CODES[code]
        else:
            pid = code if code in party_ids else party_id_for(r.get("party") or "")
        state = (r.get("state") or "").strip()
        rows.append({
            "id": int(r["mpsno"]),
            "name": display_name(r["name"]),
            "name_on_record": " ".join((r["name"] or "").split()),
            "name_hi": display_name_hi(r.get("hname")),
            "party_name": (r.get("party") or "").strip() or None,
            "party_id": pid if pid in party_ids else None,
            "state": "Nominated" if code == "NOM." or state.lower().startswith("nominated") else canonical_state(state),
            "term_start": _iso(r.get("notificationDate")),
            "term_end": _iso(r.get("expirationDate")),
            "terms_served": r.get("termCount"),
            "is_minister": bool(r.get("currentMinister")),
        })
    return rows


def run_import() -> dict:
    ensure_schema()
    records, page = [], 1
    while True:
        r = requests.get(API, params={"page": page, "size": 500}, headers={"User-Agent": USER_AGENT}, timeout=60)
        r.raise_for_status()
        payload = r.json()
        records += payload["records"]
        if page >= payload["_metadata"]["totalPages"]:
            break
        page += 1
        time.sleep(2)

    db = SessionLocal()
    try:
        party_ids = {p for (p,) in db.query(models.Party.id)}
        rows = parse(records, party_ids)
        db.query(models.RajyaSabhaMember).delete()
        db.add_all(models.RajyaSabhaMember(source_url=PAGE_URL, **row) for row in rows)
        db.commit()
        return {"records": len(records), "sitting": len(rows),
                "without_party": sum(1 for x in rows if not x["party_id"]),
                "ministers": sum(1 for x in rows if x["is_minister"])}
    finally:
        db.close()
