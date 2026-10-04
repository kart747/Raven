"""
Lok Sabha members, 15th to 18th Lok Sabha (2009 onwards), and linking a sitting MP to earlier terms.

Source: Vonter/india-representatives-activity (ODbL-1.0), compiled from sansad.in.

Linking is conservative: an earlier-term record belongs to a sitting MP only when it is the same seat in
the same state AND the names share a significant word ("L. S. Tejasvi Surya" ~ "Tejasvi Surya").
A different person who held the same seat is never linked; MPs who changed seat are not linked either.
"""
import csv
import datetime
import difflib
import io
import re

import requests

from .database import SessionLocal, ensure_schema
from .seats import alias, seat_key
from .states import canonical_state
from . import models

SOURCE = "https://raw.githubusercontent.com/Vonter/india-representatives-activity/main/csv/Lok%20Sabha/{n}th.csv"
TERMS = (15, 16, 17, 18)
_TITLES = {"dr", "shri", "smt", "kumari", "adv", "advocate", "prof", "sh", "km", "col", "retd", "capt", "mr", "mrs", "ms"}


def name_tokens(name: str) -> set[str]:
    """Significant words of a name: no titles, no initials."""
    words = re.findall(r"[a-z]+", (name or "").lower())
    return {w for w in words if len(w) > 2 and w not in _TITLES}


def initials(name: str) -> set[str]:
    """First letters of every word, including single-letter initials ("K.C. Patel" -> {k, c, p})."""
    return {w[0] for w in re.findall(r"[a-z]+", (name or "").lower()) if w not in _TITLES}


def _word_match(w: str, words: set[str]) -> bool:
    # tolerate transliteration variants ("Lakhamashi" / "Lakhamshi")
    return w in words or any(difflib.SequenceMatcher(None, w, x).ratio() >= 0.8 for x in words)


def same_person(a: str, b: str) -> bool:
    """Every significant word of the shorter name appears (allowing spelling variants) in the longer one."""
    ta, tb = name_tokens(a), name_tokens(b)
    if not ta or not tb:
        return False
    (shorter, short_name), (longer, long_name) = sorted([(ta, a), (tb, b)], key=lambda x: len(x[0]))
    # "K.C. Patel" and "Dhaval Laxmanbhai Patel" share a surname but not initials: different people
    ia, ib = initials(short_name), initials(long_name)
    if not (ia <= ib or ib <= ia):
        return False
    if len(shorter) == 1:
        # One significant word ("S.P.Y. Reddy" -> "reddy") is too little for fuzzy matching
        return next(iter(shorter)) in longer
    return bool(shorter & longer) and all(_word_match(w, longer) for w in shorter)


def _num(v, cast=float):
    v = (v or "").strip().rstrip("%")
    try:
        return cast(float(v))
    except ValueError:
        return None


def _state(raw: str, term: int) -> str:
    return canonical_state(raw)


def run_import() -> dict:
    ensure_schema()
    db = SessionLocal()
    try:
        db.query(models.MemberTerm).delete(synchronize_session=False)
        now = datetime.datetime.utcnow()
        counts = {}
        for n in TERMS:
            text = requests.get(SOURCE.format(n=n), timeout=120).content.decode("utf-8-sig", errors="replace")
            rows = []
            for r in csv.DictReader(io.StringIO(text), delimiter=";"):
                name = (r.get("Name") or "").strip()
                if not name:
                    continue
                rows.append({
                    "lok_sabha": n, "name": name,
                    "constituency": (r.get("Constituency") or "").strip(),
                    "state": _state(r.get("State"), n),
                    "party": (r.get("Party") or "").strip() or None,
                    "attendance_pct": _num(r.get("Attendance")),
                    "debates": _num(r.get("Debates"), int),
                    "questions": _num(r.get("Questions"), int),
                    "private_member_bills": _num(r.get("Private Member Bills"), int),
                    "term_start": (r.get("Start of Term") or "").strip() or None,
                    "term_end": (r.get("End of Term") or "").strip() or None,
                    "membership": (r.get("Nature of membership") or "").strip() or None,
                    "source_url": SOURCE.format(n=n), "created_at": now,
                })
            db.bulk_insert_mappings(models.MemberTerm, rows)
            counts[f"{n}th Lok Sabha"] = len(rows)
        db.commit()
        return {"members_by_term": counts}
    finally:
        db.close()


# Telangana's seats belonged to Andhra Pradesh before June 2014 (15th Lok Sabha)
_STATE_BEFORE = {("Telangana", 15): "Andhra Pradesh"}


def career(db, mp: "models.MPActivity") -> list:
    """Earlier-term records of a sitting MP: same seat and state, compatible name."""
    keys = {seat_key(mp.constituency), seat_key(alias(mp.state_represented, mp.constituency))} - {""}
    out = []
    for term in sorted(TERMS, reverse=True):
        state = _STATE_BEFORE.get((mp.state_represented, term), mp.state_represented)
        matches = [t for t in db.query(models.MemberTerm).filter(models.MemberTerm.lok_sabha == term, models.MemberTerm.state == state)
                   if seat_key(t.constituency) in keys and same_person(t.name, mp.mp_name)]
        if matches:
            # A seat can have two members in one term (by-election); keep the closest name only
            out.append(max(matches, key=lambda t: difflib.SequenceMatcher(
                None, " ".join(sorted(name_tokens(t.name))), " ".join(sorted(name_tokens(mp.mp_name)))).ratio()))
    return out
