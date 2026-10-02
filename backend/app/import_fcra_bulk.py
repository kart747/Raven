import os
import sys
import csv
from datetime import datetime

# Adjust Python path to import app models and database settings
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Base, engine
from app import models
from app.states import canonical_state
from sqlalchemy import func, desc

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
CSV_PATH = os.environ.get("FCRA_CSV_PATH", os.path.join(PROJECT_ROOT, "fcra_repo", "database.csv"))

# Optional verified registration statuses, e.g. from MHA's published cancellation lists.
# Columns: fcra_registration_number,status,source_url   (status: Active|Suspended|Cancelled)
STATUS_OVERRIDES_PATH = os.environ.get(
    "FCRA_STATUS_CSV", os.path.join(PROJECT_ROOT, "data", "fcra_status_overrides.csv")
)
VALID_STATUSES = {"Active", "Suspended", "Cancelled"}

SECTOR_KEYWORDS = [
    ("Faith-based", ["CHURCH", "DIOCESE", "MISSION", "PARISH", "TEMPLE", "MANDIR", "MASJID", "MOSQUE",
                     "MADRASA", "GURUDWARA", "MATH ", "ASHRAM", "WAQF", "BAPTIST", "CATHOLIC", "SISTERS OF"]),
    ("Education", ["SCHOOL", "COLLEGE", "EDUCATION", "ACADEMY", "LITERACY", "STUDENT", "TEACHER", "UNIVERSITY"]),
    ("Healthcare & Research", ["HEALTH", "MEDICAL", "HOSPITAL", "CLINIC", "CANCER", "DISEASE", "PHARMACY", "WELLNESS"]),
    ("Policy & Advocacy", ["RESEARCH", "POLICY", "ADVOCACY", "STUDIES", "FORUM", "DEMOCRACY"]),
    ("Environmental Advocacy", ["FOREST", "ENVIRONMENT", "WILDLIFE", "NATURE", "CLIMATE", "POLLUTION", "CONSERVATION"]),
    ("Media & Policy", ["MEDIA", "NEWS", "JOURNAL", "PRESS", "BROADCAST", "PUBLICATIONS", "COMMUNICATION"]),
    ("Human Rights Advocacy", ["HUMAN RIGHTS", "JUSTICE", "LIBERTY", "EQUALITY"]),
]


def determine_sector(name):
    """Best-effort sector inferred from the NGO's name only (the FCRA returns carry no sector)."""
    name_upper = f" {name.upper()} "
    for sector, words in SECTOR_KEYWORDS:
        if any(w in name_upper for w in words):
            return sector
    return "Social Relief / Other"


def load_status_overrides():
    """Registration status is not in the FCRA returns data; only verified statuses are applied."""
    if not os.path.exists(STATUS_OVERRIDES_PATH):
        return {}
    overrides = {}
    with open(STATUS_OVERRIDES_PATH, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            status = (row.get("status") or "").strip().title()
            reg = (row.get("fcra_registration_number") or "").strip()
            if reg and status in VALID_STATUSES:
                overrides[reg] = status
    return overrides


def parse_year(year_str):
    """'2020-2021' -> 2020 (fiscal year start, same convention as electoral bonds)."""
    if not year_str or not isinstance(year_str, str):
        return None
    parts = year_str.split('-')
    if len(parts) == 2:
        try:
            return int(parts[0])
        except ValueError:
            pass
    try:
        return int(parts[0])
    except ValueError:
        return None

def import_bulk():
    if not os.path.exists(CSV_PATH):
        print(f"Error: CSV file not found at {CSV_PATH}")
        sys.exit(1)

    print("Initializing Database Connection...")
    # Make sure tables exist
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        print("Clearing existing NGO seed data...")
        db.query(models.NGODonation).delete()
        db.query(models.NGO).delete()
        db.commit()
        print("Existing tables cleared successfully.")

        status_overrides = load_status_overrides()
        print(f"Loaded {len(status_overrides)} verified registration statuses.")
        print(f"Reading historical dataset from {CSV_PATH}...")
        ngo_records = {}
        donations_to_import = []

        with open(CSV_PATH, 'r', encoding='utf-8') as f:
            # We use quoting=csv.QUOTE_NONE to treat quotes as part of the text fields 
            # and prevent issues with mismatched quote chars.
            reader = csv.reader(f, delimiter='|', quoting=csv.QUOTE_NONE)
            header = next(reader)
            
            # Count variables for progress reporting
            row_count = 0
            for row in reader:
                if not row or len(row) < 10:
                    continue
                
                row_count += 1
                if row_count % 20000 == 0:
                    print(f"Processed {row_count} rows...")

                # Extract fields
                raw_name = row[1].strip().strip('"').strip('“').strip('”')
                year_str = row[3].strip()
                raw_state = row[4].strip()
                reg_num = row[6].strip()
                
                # Validation: Skip invalid registration numbers
                if not reg_num or reg_num == "-1" or len(reg_num) < 5:
                    continue

                try:
                    inr_amount = float(row[8])
                except ValueError:
                    inr_amount = 0.0

                # Determine mapped attributes
                state = canonical_state(raw_state)
                sector = determine_sector(raw_name)
                status = status_overrides.get(reg_num, "Unknown")
                year = parse_year(year_str)
                if year is None:
                    continue

                # Keep track of unique NGOs. If we encounter multiple, update to the most recent info
                if reg_num not in ngo_records:
                    ngo_records[reg_num] = {
                        "name": raw_name,
                        "fcra_registration_number": reg_num,
                        "state": state,
                        "sector": sector,
                        "registration_status": status,
                        "data_as_of": "FCRA annual returns FY2016-17 to FY2020-21",
                        "created_at": datetime.utcnow()
                    }
                else:
                    # Update to keep the most complete/latest name if needed
                    if len(raw_name) > len(ngo_records[reg_num]["name"]):
                        ngo_records[reg_num]["name"] = raw_name

                # Add contribution record
                donations_to_import.append({
                    "fcra_reg": reg_num,
                    "amount": inr_amount,
                    "year": year,
                    "source_name": "FCRA annual returns (via fcra_repo scrape)",
                    "source_url": "https://fcraonline.nic.in",
                    "created_at": datetime.utcnow()
                })

        print(f"Parsed {row_count} rows from CSV.")
        print(f"Identified {len(ngo_records)} unique NGOs. Inserting into database...")

        # Bulk insert NGOs
        ngo_list = list(ngo_records.values())
        db.bulk_insert_mappings(models.NGO, ngo_list)
        db.commit()
        print("NGOs inserted successfully.")

        # Re-fetch NGOs to map registration number to their new auto-incremented database ID
        print("Mapping database IDs for donations...")
        ngo_db_map = {
            ngo.fcra_registration_number: ngo.id
            for ngo in db.query(models.NGO.id, models.NGO.fcra_registration_number).all()
        }

        # Build donation list with resolved foreign keys
        final_donations = []
        skipped_donations = 0
        for d in donations_to_import:
            ngo_id = ngo_db_map.get(d["fcra_reg"])
            if ngo_id is None:
                skipped_donations += 1
                continue
            
            final_donations.append({
                "ngo_id": ngo_id,
                "amount": d["amount"],
                "year": d["year"],
                "source_name": d["source_name"],
                "source_url": d["source_url"],
                "created_at": d["created_at"]
            })

        print(f"Inserting {len(final_donations)} donation records (Skipped: {skipped_donations})...")
        
        # Bulk insert NGO donations in chunks to prevent memory/transaction bloat
        chunk_size = 10000
        for i in range(0, len(final_donations), chunk_size):
            chunk = final_donations[i:i + chunk_size]
            db.bulk_insert_mappings(models.NGODonation, chunk)
            db.commit()

        print("Donation records inserted successfully!")

        # Count Validation and Distributions Reporting
        total_ngos = db.query(models.NGO).count()
        total_donations = db.query(models.NGODonation).count()

        print("\n" + "="*50)
        print("IMPORT VALIDATION SUMMARY")
        print("="*50)
        print(f"Total NGOs Imported:      {total_ngos}")
        print(f"Total Donations Imported: {total_donations}")
        print("-"*50)
        
        # State distribution
        print("State-Specific NGO Distribution:")
        state_distribution = db.query(
            models.NGO.state,
            func.count(models.NGO.id)
        ).group_by(models.NGO.state).order_by(desc(func.count(models.NGO.id))).all()

        for state, count in state_distribution[:15]: # Show top 15 states
            print(f"  - {state:<25}: {count}")
        if len(state_distribution) > 15:
            print(f"  - ... and {len(state_distribution) - 15} more states")
        print("="*50)

    except Exception as e:
        db.rollback()
        print(f"An error occurred during import: {e}")
        raise e
    finally:
        db.close()

if __name__ == "__main__":
    import_bulk()
