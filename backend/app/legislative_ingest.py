import csv
import io
import re
from typing import Dict, Iterable, List, Tuple

import requests
from sqlalchemy.orm import Session

from . import models
from .states import canonical_state


MP_ACTIVITY_CSV_URL = "https://raw.githubusercontent.com/Vonter/india-representatives-activity/main/csv/Lok%20Sabha/18th.csv"
BILLS_CSV_URL = "https://raw.githubusercontent.com/Vonter/india-representatives-activity/main/activity/Private%20Member%20Bills/Lok%20Sabha/18th.csv"


def _clean(value):
    if value is None:
        return ""
    return str(value).strip()


def _normalize_key(value: str) -> str:
    return re.sub(r"\s+", " ", _clean(value)).lower()


def _fetch_csv_rows(url: str) -> List[Dict[str, str]]:
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    text = response.text.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(text), delimiter=";")
    return [row for row in reader if any(_clean(cell) for cell in row.values())]


def _parse_float(value: str):
    value = _clean(value)
    if not value:
        return None
    try:
        return float(value.replace("%", ""))
    except ValueError:
        return None


def _parse_int(value: str) -> int:
    value = _clean(value)
    if not value:
        return 0
    try:
        return int(float(value))
    except ValueError:
        return 0


def _normalize_status(raw_status: str, passage_field: str) -> str:
    status_text = f"{_clean(raw_status)} {_clean(passage_field)}".lower()
    if "pass" in status_text and "pending" not in status_text:
        return "Passed"
    if "introduced" in status_text:
        return "Introduced"
    return "Pending"


def _extract_state_lookup(rows: Iterable[Dict[str, str]]) -> Dict[str, str]:
    lookup = {}
    for row in rows:
        name = _normalize_key(row.get("Name") or row.get("name"))
        state = _clean(row.get("State") or row.get("state"))
        if name and state:
            lookup[name] = canonical_state(state)
    return lookup


def ingest_legislative_data(db: Session, refresh: bool = False) -> Dict[str, int]:
    if refresh:
        db.query(models.MPActivity).delete(synchronize_session=False)
        db.query(models.LegislativeBill).delete(synchronize_session=False)
        db.commit()

    mp_rows = _fetch_csv_rows(MP_ACTIVITY_CSV_URL)
    bill_rows = _fetch_csv_rows(BILLS_CSV_URL)

    state_lookup = _extract_state_lookup(mp_rows)
    if not state_lookup:
        existing_legislators = db.query(models.Legislator).all()
        state_lookup = { _normalize_key(item.name): item.state for item in existing_legislators }

    existing_mps = {
        (_normalize_key(row.mp_name), _clean(row.constituency), _clean(row.state_represented))
        for row in db.query(models.MPActivity.mp_name, models.MPActivity.constituency, models.MPActivity.state_represented).all()
    }
    existing_bills = {
        (_normalize_key(row.bill_title), _normalize_key(row.introduced_by), _clean(row.official_url))
        for row in db.query(models.LegislativeBill.bill_title, models.LegislativeBill.introduced_by, models.LegislativeBill.official_url).all()
    }

    mp_added = 0
    for row in mp_rows:
        mp_name = _clean(row.get("Name") or row.get("name"))
        constituency = _clean(row.get("Constituency") or row.get("constituency"))
        state_represented = canonical_state(_clean(row.get("State") or row.get("state")) or None)
        if state_represented == "Unknown":
            state_represented = state_lookup.get(_normalize_key(mp_name), "Unknown")

        key = (_normalize_key(mp_name), constituency, state_represented)
        if not mp_name or not constituency or not state_represented or key in existing_mps:
            continue

        mp = models.MPActivity(
            mp_name=mp_name,
            constituency=constituency,
            party_name=_clean(row.get("Party") or row.get("party")) or "Independent",
            state_represented=state_represented,
            attendance_pct=_parse_float(row.get("Attendance")),
            debates_count=_parse_int(row.get("Debates")),
            questions_count=_parse_int(row.get("Questions")),
            bills_introduced=_parse_int(row.get("Private Member Bills") or row.get("Private Member Bill")),
            official_url=MP_ACTIVITY_CSV_URL,
        )
        db.add(mp)
        existing_mps.add(key)
        mp_added += 1

    bill_added = 0
    for row in bill_rows:
        bill_title = _clean(row.get("Bill title") or row.get("bill_title"))
        introduced_by = _clean(row.get("Representative") or row.get("representative"))
        official_url = _clean(row.get("link") or row.get("url"))
        current_status = _normalize_status(row.get("Current Status"), row.get("Date - Passage / Withdrawal / Lapsing"))
        introduced_on = _clean(row.get("Date of introduction") or row.get("date_of_introduction"))
        state_represented = state_lookup.get(_normalize_key(introduced_by), "Unknown")

        key = (_normalize_key(bill_title), _normalize_key(introduced_by), official_url)
        if not bill_title or not introduced_by or not official_url or key in existing_bills:
            continue

        bill = models.LegislativeBill(
            bill_title=bill_title,
            ministry="Private Member Business",
            current_status=current_status,
            state_represented=state_represented,
            introduced_by=introduced_by,
            introduced_on=introduced_on,
            official_url=official_url,
        )
        db.add(bill)
        existing_bills.add(key)
        bill_added += 1

    db.commit()
    return {
        "mp_activity_added": mp_added,
        "legislative_bills_added": bill_added,
    }
