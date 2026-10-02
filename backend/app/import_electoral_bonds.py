"""
Electoral Bond importer.

Uses the 21 March 2024 SBI disclosure (cvrajeesh_repo/data), which includes the
unique bond number (Prefix + Bond Number) on both the purchase and redemption
sides. Joining on that key gives an exact purchaser -> party attribution.

Bonds encashed whose purchase record is not in the disclosure (purchases before
12 Apr 2019) are attributed to "UNKNOWN DONOR" rather than guessed.

Run standalone from backend/:  python -m app.import_electoral_bonds
"""

import csv
import datetime
from collections import Counter
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import func

from app.database import SessionLocal, Base, engine
from app import models
from app.entities import resolve
from app.parties import PARTIES_MASTER, party_id_for

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.environ.get("EB_DATA_DIR", os.path.join(PROJECT_ROOT, "cvrajeesh_repo", "data"))
PURCHASE_CSV = os.path.join(DATA_DIR, "20240321-EB-purchase-data-full.csv")
REDEMPTION_CSV = os.path.join(DATA_DIR, "20240321-EB-redemption-data-full.csv")
# Optional sourced industry labels. Columns: donor_name,industry,source_url
# donor_name may be any spelling; it is matched through the same entity resolution.
INDUSTRY_CSV = os.environ.get("DONOR_INDUSTRY_CSV", os.path.join(PROJECT_ROOT, "data", "donor_industry.csv"))

SOURCE_NAME = "SBI disclosure to ECI (21 Mar 2024, bond-number matched)"
SOURCE_URL = "https://www.eci.gov.in/disclosure-of-electoral-bonds"
UNKNOWN_DONOR = "UNKNOWN DONOR"
BATCH_SIZE = 5_000


def parse_disclosure_date(date_str: str) -> tuple[str | None, int | None]:
    """'12/Apr/2019' -> ('2019-04-12', 2019). Fiscal year runs April-March."""
    try:
        dt = datetime.datetime.strptime(date_str.strip(), "%d/%b/%Y")
    except ValueError:
        return None, None
    fiscal_year = dt.year if dt.month >= 4 else dt.year - 1
    return dt.strftime("%Y-%m-%d"), fiscal_year


def parse_amount(value: str) -> float:
    return float(value.replace(",", "").strip())


def load_purchases(path: str) -> dict[tuple[str, str], str]:
    """(prefix, bond_number) -> purchaser name."""
    purchases = {}
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 9:
                continue
            purchases[(row[6].strip(), row[7].strip())] = row[5].strip().upper()
    return purchases


def load_redemptions(path: str) -> list[dict]:
    """Unique encashed bonds, de-duplicated on bond number (the source repeats some rows)."""
    seen = set()
    redemptions = []
    with open(path, newline="", encoding="utf-8") as f:
        reader = csv.reader(f)
        next(reader)
        for row in reader:
            if len(row) < 8:
                continue
            key = (row[4].strip(), row[5].strip())
            if key in seen:
                continue
            seen.add(key)
            redemptions.append({
                "date": row[1].strip(),
                "party": row[2].strip(),
                "bond_key": key,
                "amount": row[6],
                "pay_branch_code": row[7].strip(),
            })
    return redemptions


def load_industries(mapping: dict[str, str]) -> dict[str, str]:
    """Canonical donor name -> industry, from the optional sourced CSV."""
    if not os.path.isfile(INDUSTRY_CSV):
        return {}
    from app.entities import entity_key
    by_key = {entity_key(raw): canon for raw, canon in mapping.items()}
    industries = {}
    with open(INDUSTRY_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            name, industry = (row.get("donor_name") or "").strip(), (row.get("industry") or "").strip()
            canon = by_key.get(entity_key(name)) if name else None
            if canon and industry and (row.get("source_url") or "").strip():
                industries[canon] = industry
    return industries


def run_import() -> dict:
    for path in (PURCHASE_CSV, REDEMPTION_CSV):
        if not os.path.isfile(path):
            raise FileNotFoundError(
                f"{path} not found. Clone cvrajeesh_repo into the project root or set EB_DATA_DIR."
            )

    Base.metadata.create_all(bind=engine)
    purchases = load_purchases(PURCHASE_CSV)
    redemptions = load_redemptions(REDEMPTION_CSV)

    raw_counts = Counter(purchases.values())
    canonical = resolve(raw_counts)
    industries = load_industries(canonical)

    db = SessionLocal()
    try:
        for pid, pname in PARTIES_MASTER.items():
            if not db.get(models.Party, pid):
                db.add(models.Party(id=pid, name=pname))
        db.commit()

        db.query(models.Donation).filter(
            models.Donation.funding_type == "Electoral Bond"
        ).delete(synchronize_session=False)
        db.query(models.ElectoralBond).delete(synchronize_session=False)
        db.query(models.DonorAlias).delete(synchronize_session=False)
        db.query(models.EntityEvent).update({models.EntityEvent.donor_id: None}, synchronize_session=False)
        # Donors are rebuilt from the resolved names; drop ones no longer referenced
        db.query(models.Donor).filter(
            ~models.Donor.id.in_(db.query(models.Donation.donor_id))
        ).delete(synchronize_session=False)

        donor_ids = {name: did for did, name in db.query(models.Donor.id, models.Donor.name)}

        def donor_id_for(name: str) -> int:
            if name not in donor_ids:
                donor = models.Donor(name=name, industry="Unknown")
                db.add(donor)
                db.flush()
                donor_ids[name] = donor.id
            return donor_ids[name]

        for raw, canon in canonical.items():
            db.add(models.DonorAlias(donor_id=donor_id_for(canon), raw_name=raw, bond_count=raw_counts[raw]))
        for donor in db.query(models.Donor):
            donor.industry = industries.get(donor.name, "Unknown")

        now = datetime.datetime.utcnow()
        donations, bonds = [], []
        matched = unmatched = 0
        unmapped_parties: set[str] = set()
        bad_rows = 0

        for r in redemptions:
            party_id = party_id_for(r["party"])
            if not party_id:
                unmapped_parties.add(r["party"])
                continue
            iso_date, fiscal_year = parse_disclosure_date(r["date"])
            try:
                amount = parse_amount(r["amount"])
            except ValueError:
                amount = None
            if fiscal_year is None or amount is None:
                bad_rows += 1
                continue

            purchaser = purchases.get(r["bond_key"])
            if purchaser:
                purchaser = canonical[purchaser]
                matched += 1
            else:
                unmatched += 1
                purchaser = UNKNOWN_DONOR

            donations.append({
                "party_id": party_id,
                "donor_id": donor_id_for(purchaser),
                "amount": amount,
                "date": iso_date,
                "year": fiscal_year,
                "funding_type": "Electoral Bond",
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
                "created_at": now,
            })
            bonds.append({
                "donor_name": purchaser,
                "party_name": PARTIES_MASTER[party_id],
                "amount": amount,
                "date": iso_date,
                "bank_branch": f"SBI pay branch {r['pay_branch_code']}" if r["pay_branch_code"] else "SBI",
                "fiscal_year": fiscal_year,
                "source_name": SOURCE_NAME,
                "source_url": SOURCE_URL,
                "created_at": now,
            })

        for i in range(0, len(donations), BATCH_SIZE):
            db.bulk_insert_mappings(models.Donation, donations[i:i + BATCH_SIZE])
            db.bulk_insert_mappings(models.ElectoralBond, bonds[i:i + BATCH_SIZE])
        db.commit()

        total_amount = func.sum(models.Donation.amount)
        top_parties = [
            {"party_name": name, "total_crore": round(total / 1e7, 2)}
            for name, total in db.query(models.Party.name, total_amount)
            .join(models.Donation, models.Donation.party_id == models.Party.id)
            .filter(models.Donation.funding_type == "Electoral Bond")
            .group_by(models.Party.name)
            .order_by(total_amount.desc())
            .limit(5)
        ]

        # Donor IDs were rebuilt, so re-link any sourced events
        from app.import_events import run_import as import_events
        events = import_events()

        return {
            "events_relinked": events.get("events_imported", 0),
            "unique_bonds_encashed": len(redemptions),
            "inserted": len(donations),
            "matched_to_purchaser": matched,
            "unmatched_unknown_donor": unmatched,
            "match_rate_pct": round(100 * matched / max(len(donations), 1), 1),
            "purchaser_spellings": len(raw_counts),
            "purchaser_entities": len(set(canonical.values())),
            "donors_with_sourced_industry": len(industries),
            "skipped_bad_rows": bad_rows,
            "unmapped_parties": sorted(unmapped_parties),
            "total_crore": round(sum(d["amount"] for d in donations) / 1e7, 2),
            "top_parties": top_parties,
        }
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    import json
    print(json.dumps(run_import(), indent=2))
