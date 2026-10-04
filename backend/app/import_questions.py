"""
Lok Sabha questions, 15th-18th Lok Sabha (2009 onwards).

Source: Vonter/india-representatives-activity (ODbL-1.0), compiled from sansad.in.
Each row links to the official answer PDF on sansad.in.

Also links questions to electoral bond purchasers when a question's *title* contains a
purchaser's distinctive name as an exact phrase. This is a text match, not a claim of any
relationship, and the UI says so.
"""
import csv
import datetime
import io
import re

import requests

from .database import SessionLocal, ensure_schema
from . import models

SOURCE = "https://raw.githubusercontent.com/Vonter/india-representatives-activity/main/activity/Questions/Lok%20Sabha/{n}th.csv"
LOK_SABHAS = (15, 16, 17, 18)
BATCH = 10_000

# Legal-form words stripped to get a company's distinctive name ("VEDANTA LIMITED" -> "VEDANTA")
_LEGAL = r"(PRIVATE|PVT|LIMITED|LTD|LLP|L L P|COMPANY|CO|CORPORATION|CORP|INC|\(INDIA\)|INDIA)"
_LEGAL_SUFFIX = re.compile(rf"(\s+{_LEGAL}\.?)+$")
_HAS_LEGAL_FORM = re.compile(r"\b(PRIVATE|PVT|LIMITED|LTD|LLP|COMPANY|CORPORATION)\b")
# Too generic to identify a company on their own
_GENERIC = {"INDIA", "INDUSTRIES", "ENTERPRISES", "INFRASTRUCTURE", "POWER", "ENERGY", "STEEL",
            "TRADING", "INVESTMENTS", "HOLDINGS", "SERVICES", "PROJECTS", "DEVELOPERS"}


def distinctive_name(donor_name: str) -> str | None:
    """
    The part of a company name that can identify it inside a question title, or None.
    Only companies (names with a legal form) are matched; individuals are never matched.
    """
    name = " ".join(donor_name.upper().replace("&", " AND ").split())
    if not _HAS_LEGAL_FORM.search(name):
        return None
    core = _LEGAL_SUFFIX.sub("", name).strip(" .,")
    words = core.split()
    if len(words) < 2 or len(core) < 8 or all(w in _GENERIC for w in words):
        return None
    return core


def find_mentions(titles: dict[int, str], donor_names: list[str]) -> list[tuple[int, str, str]]:
    """(question_id, donor_name, matched_text) for titles containing a donor's distinctive name."""
    cores = {}
    for name in donor_names:
        core = distinctive_name(name)
        if core:
            cores.setdefault(core, name)
    if not cores:
        return []
    pattern = re.compile(r"\b(" + "|".join(re.escape(c) for c in sorted(cores, key=len, reverse=True)) + r")\b")
    out = []
    for qid, title in titles.items():
        normalized = " ".join(title.upper().replace("&", " AND ").split())
        for m in pattern.finditer(normalized):
            out.append((qid, cores[m.group(1)], m.group(1)))
    return out


def _rows(n: int):
    resp = requests.get(SOURCE.format(n=n), timeout=120)
    resp.raise_for_status()
    reader = csv.DictReader(io.StringIO(resp.content.decode("utf-8-sig")), delimiter=";")
    for row in reader:
        title = (row.get("Title") or "").strip()
        date = (row.get("Date") or "").strip()
        link = (row.get("link") or "").strip()
        who = (row.get("Representative") or "").strip()
        if not (title and date and link and who):
            continue
        yield {
            "lok_sabha": n,
            "date": date,
            "title": title,
            "question_type": (row.get("Type") or "").strip() or None,
            "ministry": (row.get("Ministry or Category") or "").strip() or None,
            "representative": who,
            "official_url": link,
            "source_url": SOURCE.format(n=n),
        }


def link_mentions(db) -> int:
    """Rebuild question <-> bond purchaser mentions."""
    db.query(models.QuestionMention).delete(synchronize_session=False)
    donors = [n for (n,) in db.query(models.Donor.name)]
    titles = dict(db.query(models.ParliamentQuestion.id, models.ParliamentQuestion.title))
    mentions = find_mentions(titles, donors)
    db.bulk_insert_mappings(models.QuestionMention, [
        {"question_id": q, "donor_name": d, "matched_text": t} for q, d, t in mentions
    ])
    db.commit()
    return len(mentions)


def run_import() -> dict:
    ensure_schema()
    db = SessionLocal()
    try:
        db.query(models.QuestionMention).delete(synchronize_session=False)
        db.query(models.ParliamentQuestion).delete(synchronize_session=False)
        now = datetime.datetime.utcnow()
        counts = {}
        for n in LOK_SABHAS:
            batch, total = [], 0
            for row in _rows(n):
                batch.append({**row, "created_at": now})
                if len(batch) >= BATCH:
                    db.bulk_insert_mappings(models.ParliamentQuestion, batch)
                    total += len(batch)
                    batch = []
            db.bulk_insert_mappings(models.ParliamentQuestion, batch)
            counts[f"{n}th Lok Sabha"] = total + len(batch)
        db.commit()
        mentions = link_mentions(db)
        return {"questions": counts, "total": sum(counts.values()), "purchaser_mentions": mentions}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
