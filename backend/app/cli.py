"""
Data management commands. Run from backend/:

    python -m app.cli seed                 # party reference list
    python -m app.cli ingest-bonds         # electoral bonds (bond-number matched)
    python -m app.cli ingest-fcra          # NGO foreign contribution returns
    python -m app.cli ingest-fcra-status FILE --status Cancelled --source-url URL   # official MHA list
    python -m app.cli ingest-candidates    # Lok Sabha 2024 candidate affidavits (MyNeta)
    python -m app.cli ingest-assemblies    # sitting MLAs: winners of each state's latest assembly election (MyNeta)
    python -m app.cli ingest-legislative   # Lok Sabha MP activity + private member bills
    python -m app.cli ingest-events        # sourced events about purchasers (data/entity_events.csv)
    python -m app.cli brief                # regenerate the AI brief
    python -m app.cli ingest-all           # all of the above, in order
"""
import argparse
import json

from dotenv import load_dotenv

load_dotenv()

from .database import SessionLocal  # noqa: E402


def seed():
    from .seed import seed_db
    seed_db()


def ingest_bonds():
    from .import_electoral_bonds import run_import
    print(json.dumps(run_import(), indent=2))


def ingest_fcra():
    from .import_fcra_bulk import import_bulk
    import_bulk()


def ingest_candidates():
    from .import_myneta import run_import
    print(json.dumps(run_import(), indent=2))


def ingest_assemblies():
    from .import_myneta import run_assembly_import
    print(json.dumps(run_assembly_import(), indent=2))


def ingest_events():
    from .import_events import run_import
    print(json.dumps(run_import(), indent=2))


def ingest_legislative():
    from .legislative_ingest import ingest_legislative_data
    db = SessionLocal()
    try:
        print(json.dumps(ingest_legislative_data(db, refresh=True), indent=2))
    finally:
        db.close()


def brief():
    from .brief_worker import generate_and_save_weekly_brief
    generate_and_save_weekly_brief()


def ingest_fcra_status(args):
    from .import_fcra_status import run_import
    print(json.dumps(run_import(args.file, args.status, args.source_url), indent=2))


COMMANDS = {
    "seed": seed,
    "ingest-bonds": ingest_bonds,
    "ingest-fcra": ingest_fcra,
    "ingest-candidates": ingest_candidates,
    "ingest-assemblies": ingest_assemblies,
    "ingest-legislative": ingest_legislative,
    "ingest-events": ingest_events,
    "brief": brief,
}


def main():
    parser = argparse.ArgumentParser(description="Raven data management")
    parser.add_argument("command", choices=[*COMMANDS, "ingest-fcra-status", "ingest-all"])
    parser.add_argument("file", nargs="?", help="ingest-fcra-status: MHA list as CSV or XLSX")
    parser.add_argument("--status", help="ingest-fcra-status: Active | Suspended | Cancelled")
    parser.add_argument("--source-url", help="ingest-fcra-status: page the list was downloaded from")
    args = parser.parse_args()
    if args.command == "ingest-fcra-status":
        if not (args.file and args.status and args.source_url):
            parser.error("ingest-fcra-status needs FILE --status STATUS --source-url URL")
        ingest_fcra_status(args)
    elif args.command == "ingest-all":
        for name in ("seed", "ingest-bonds", "ingest-fcra", "ingest-candidates", "ingest-assemblies", "ingest-legislative", "ingest-events", "brief"):
            print(f"\n=== {name} ===")
            COMMANDS[name]()
    else:
        COMMANDS[args.command]()


if __name__ == "__main__":
    main()
