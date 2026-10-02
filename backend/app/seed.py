"""
Seeds reference data only (the party master list).

All factual records — donations, NGOs, MP activity, bills — come from the
importers in this package so that every row traces back to a real source:
    python -m app.cli ingest-all
"""
from .database import engine, Base, SessionLocal
from .models import Party
from .parties import PARTIES_MASTER

PARTY_SYMBOLS = {
    "BJP": "https://upload.wikimedia.org/wikipedia/commons/1/1e/Bharatiya_Janata_Party_logo.svg",
    "INC": "https://upload.wikimedia.org/wikipedia/commons/6/6c/Indian_National_Congress_hand_logo.svg",
    "AITC": "https://upload.wikimedia.org/wikipedia/commons/d/d2/All_India_Trinamool_Congress_symbol.svg",
    "AAP": "https://upload.wikimedia.org/wikipedia/commons/5/53/Aam_Aadmi_Party_Symbol.svg",
}


def seed_db():
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        for pid, name in PARTIES_MASTER.items():
            party = db.get(Party, pid)
            if party:
                party.name = name
            else:
                db.add(Party(id=pid, name=name, symbol_url=PARTY_SYMBOLS.get(pid, "")))
        db.commit()
        print("Parties seeded.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_db()
