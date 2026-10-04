"""
Builds frontend/public/india-pc.geojson: Lok Sabha constituency boundaries with each seat's name
set to the exact constituency name used in Raven's candidate data, so the map can join on it.

Boundaries: DataMeet india_pc_2019_simplified (CC0), 2008 delimitation, which was used for the
2024 election everywhere except Jammu & Kashmir (redrawn 2022) and Assam (redrawn 2023);
seats there are drawn with pre-delimitation outlines and flagged with `redrawn`.

    python -m app.cli build-seat-map
"""
import difflib
import json
import os
import requests

from .database import SessionLocal
from . import models
from .states import canonical_state
from .seats import REDRAWN, SEAT_BY_NUMBER, alias, seat_key

SOURCE = "https://raw.githubusercontent.com/datameet/maps/master/parliamentary-constituencies/india_pc_2019_simplified.geojson"
OUT = os.path.join(os.path.dirname(__file__), "..", "..", "frontend", "public", "india-pc.geojson")


def _state_for(props: dict) -> str:
    # The 2019 file files Ladakh under Jammu & Kashmir; Ladakh is its own UT since 2019
    if seat_key(props.get("pc_name")) == "ladakh":
        return "Ladakh"
    return canonical_state(props.get("st_name"))


def match_seat(name: str, state_seats: list[str]) -> str | None:
    """Exact normalised match, else one clear close match within the state."""
    key = seat_key(name)
    by_key = {seat_key(s): s for s in state_seats}
    if key in by_key:
        return by_key[key]
    close = difflib.get_close_matches(key, list(by_key), n=2, cutoff=0.75)
    if not close:
        return None
    if len(close) == 2:
        r1 = difflib.SequenceMatcher(None, key, close[0]).ratio()
        r2 = difflib.SequenceMatcher(None, key, close[1]).ratio()
        if r1 - r2 <= 0.1:
            return None
    return by_key[close[0]]


def run_build() -> dict:
    data = requests.get(SOURCE, timeout=120).json()
    db = SessionLocal()
    try:
        seats: dict[str, set[str]] = {}
        for state, seat in db.query(models.Candidate.state, models.Candidate.constituency)\
                .filter(models.Candidate.election == "Lok Sabha 2024").distinct():
            seats.setdefault(state, set()).add(seat)
    finally:
        db.close()

    unmatched, used = [], set()
    for f in data["features"]:
        p = f["properties"]
        state = _state_for(p)
        seat = SEAT_BY_NUMBER.get((state, p.get("pc_no"))) or alias(state, p.get("pc_name")) \
            or match_seat(p.get("pc_name"), sorted(seats.get(state, [])))
        if seat is None or (state, seat) in used:
            unmatched.append(f"{p.get('pc_name')} ({state})")
            seat = None
        else:
            used.add((state, seat))
        f["properties"] = {
            "state": state,
            "seat": seat,                       # exact Raven constituency name, or null if unmatched
            "name": (p.get("pc_name") or "").title(),
            "name_hi": p.get("pc_name_hi"),
            "category": p.get("pc_category"),
            "wikidata": p.get("wikidata_qid"),
            "redrawn": REDRAWN.get(state),       # boundaries predate this delimitation
        }
    data["metadata"] = {
        "source": "DataMeet india_pc_2019_simplified (CC0); 2008 delimitation. J&K (2022) and Assam (2023) were redrawn later.",
        "url": "https://github.com/datameet/maps/tree/master/parliamentary-constituencies",
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, separators=(",", ":"))
    return {"seats": len(data["features"]), "matched": len(data["features"]) - len(unmatched), "unmatched": unmatched}
