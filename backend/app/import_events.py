"""
Loads sourced events about bond purchasers from data/entity_events.csv.

Columns: entity_name,event_date,event_type,description,source_name,source_url
  - event_date: YYYY-MM-DD
  - event_type: free text, e.g. raid | contract | regulatory | other
  - source_url is required; rows without one are rejected.

entity_name may be any spelling of the purchaser; it is matched to a donor through
the same entity resolution used for the bond data (app/entities.py).
"""
import csv
import datetime
import os

from .database import SessionLocal, ensure_schema
from .entities import entity_key
from . import models

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
EVENTS_CSV = os.environ.get("ENTITY_EVENTS_CSV", os.path.join(PROJECT_ROOT, "data", "entity_events.csv"))
REQUIRED = ("entity_name", "event_date", "event_type", "description", "source_url")


def run_import(path: str = EVENTS_CSV) -> dict:
    if not os.path.isfile(path):
        return {"events_imported": 0, "note": f"{path} not found"}
    ensure_schema()
    db = SessionLocal()
    try:
        donor_by_key = {}
        for alias in db.query(models.DonorAlias):
            donor_by_key[entity_key(alias.raw_name)] = alias.donor_id
        for donor in db.query(models.Donor):
            donor_by_key.setdefault(entity_key(donor.name), donor.id)

        db.query(models.EntityEvent).delete(synchronize_session=False)
        imported, rejected, unmatched = 0, [], 0
        with open(path, newline="", encoding="utf-8") as f:
            for line_no, row in enumerate(csv.DictReader(f), start=2):
                row = {k: (v or "").strip() for k, v in row.items() if k}
                missing = [c for c in REQUIRED if not row.get(c)]
                try:
                    datetime.date.fromisoformat(row.get("event_date", ""))
                except ValueError:
                    missing.append("event_date (YYYY-MM-DD)")
                if missing:
                    rejected.append({"line": line_no, "missing_or_invalid": missing})
                    continue
                donor_id = donor_by_key.get(entity_key(row["entity_name"]))
                unmatched += donor_id is None
                db.add(models.EntityEvent(
                    donor_id=donor_id,
                    entity_name=row["entity_name"],
                    event_date=row["event_date"],
                    event_type=row["event_type"].lower(),
                    description=row["description"],
                    source_name=row.get("source_name") or None,
                    source_url=row["source_url"],
                ))
                imported += 1
        db.commit()
        return {"events_imported": imported, "not_matched_to_a_donor": unmatched, "rejected": rejected}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
