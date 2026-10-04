"""
Open data release: every table as gzipped CSV plus a manifest (row counts, SHA-256, sources, licence notes).

    python -m app.cli export-release            # -> ../data/releases/raven-YYYY-MM-DD/

Publish with e.g. `gh release create data-YYYY-MM-DD data/releases/raven-YYYY-MM-DD/*`.
"""
import csv
import datetime
import gzip
import hashlib
import json
import os

from sqlalchemy import inspect

from .database import engine, ensure_schema
from .database import Base
from . import models  # noqa: F401  (register tables)

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))

# Tables published, with the upstream source and its terms
PUBLISHED = {
    "parties": "Raven reference list",
    "donors": "SBI electoral bond disclosure to ECI (21 Mar 2024), purchaser names merged by app/entities.py",
    "donor_aliases": "Raw SBI purchaser spellings and the merged name each maps to",
    "donations": "SBI electoral bond disclosure to ECI (21 Mar 2024), matched on bond number",
    "electoral_bonds": "SBI electoral bond disclosure to ECI (21 Mar 2024)",
    "candidates": "MyNeta / ADR affidavit summaries (Lok Sabha 2024 and latest assembly elections)",
    "ngos": "MHA FCRA annual returns via mkonchady/fcra (MIT); sector inferred from name",
    "ngo_donations": "MHA FCRA annual returns via mkonchady/fcra (MIT)",
    "mp_activity": "Vonter/india-representatives-activity (ODbL-1.0), from sansad.in",
    "legislative_bills": "Vonter/india-representatives-activity (ODbL-1.0), from sansad.in",
    "parliament_questions": "Vonter/india-representatives-activity (ODbL-1.0), from sansad.in",
    "question_mentions": "Raven exact-name matches of purchasers in question titles",
    "entity_events": "Curated, source-cited events (data/entity_events.csv)",
}


def _sha256(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def diff_manifests(previous: dict, current_files: list[dict]) -> list[dict]:
    """Per-table row changes versus a previous release manifest."""
    before = {f["table"]: f for f in previous.get("files", [])}
    changes = []
    for f in current_files:
        old = before.get(f["table"])
        if old is None:
            changes.append({"table": f["table"], "status": "new", "rows": f["rows"]})
        elif old["sha256"] != f["sha256"]:
            changes.append({"table": f["table"], "status": "changed", "rows_before": old["rows"],
                            "rows": f["rows"], "row_change": f["rows"] - old["rows"]})
    for table in sorted(set(before) - {f["table"] for f in current_files}):
        changes.append({"table": table, "status": "removed", "rows_before": before[table]["rows"]})
    return changes


def run_export(out_dir: str | None = None, previous_manifest: str | None = None) -> dict:
    ensure_schema()
    today = datetime.date.today().isoformat()
    out_dir = out_dir or os.path.join(PROJECT_ROOT, "data", "releases", f"raven-{today}")
    os.makedirs(out_dir, exist_ok=True)
    existing = set(inspect(engine).get_table_names())

    files = []
    with engine.connect() as conn:
        for name, source in PUBLISHED.items():
            if name not in existing:
                continue
            table = Base.metadata.tables[name]
            path = os.path.join(out_dir, f"{name}.csv.gz")
            rows = 0
            with gzip.open(path, "wt", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)
                writer.writerow([c.name for c in table.columns])
                for row in conn.execute(table.select().order_by(*table.primary_key.columns)).yield_per(5000):
                    writer.writerow(row)
                    rows += 1
            files.append({"file": os.path.basename(path), "table": name, "rows": rows,
                          "sha256": _sha256(path), "source": source})

    manifest = {
        "name": f"Raven open data release {today}",
        "created": datetime.datetime.utcnow().isoformat() + "Z",
        "code_licence": "AGPL-3.0",
        "data_terms": "Each table keeps the terms of its upstream source (see 'source'). ODbL-1.0 tables "
                      "require attribution and share-alike for derived databases.",
        "caveats": [
            "Candidate figures are self-declared; 'criminal_cases' are pending cases declared, not convictions.",
            "NGO registration_status 'Unknown' means not verified, not active.",
            "question_mentions are exact name matches in titles, not evidence of any relationship.",
        ],
        "files": files,
    }
    if previous_manifest and os.path.isfile(previous_manifest):
        with open(previous_manifest, encoding="utf-8") as f:
            previous = json.load(f)
        manifest["previous_release"] = previous.get("name")
        manifest["changes_since_previous"] = diff_manifests(previous, files)
    with open(os.path.join(out_dir, "manifest.json"), "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    return {"out_dir": out_dir, "tables": len(files), "rows": sum(f["rows"] for f in files),
            "changed_tables": len(manifest.get("changes_since_previous", []))}
