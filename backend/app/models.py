import datetime
from sqlalchemy import Boolean, Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import relationship
from .database import Base

class Party(Base):
    __tablename__ = "parties"

    id = Column(String, primary_key=True, index=True) # e.g., "BJP", "INC"
    name = Column(String, nullable=False)
    symbol_url = Column(String, nullable=True)

    donations = relationship("Donation", back_populates="party")
    candidates = relationship("Candidate", back_populates="party")

class Donor(Base):
    __tablename__ = "donors"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, unique=True, index=True)
    industry = Column(String, default="Unknown")

    donations = relationship("Donation", back_populates="donor")

class Donation(Base):
    __tablename__ = "donations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    party_id = Column(String, ForeignKey("parties.id"), nullable=False, index=True)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False) # In INR
    date = Column(String, nullable=True) # YYYY-MM-DD
    year = Column(Integer, nullable=False, index=True) # Fiscal year, e.g., 2024
    funding_type = Column(String, nullable=False, index=True) # "Electoral Bond", "Direct Contribution", etc.
    source_name = Column(String, nullable=False) # e.g., "ECI / ADR"
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    party = relationship("Party", back_populates="donations")
    donor = relationship("Donor", back_populates="donations")

class Candidate(Base):
    __tablename__ = "candidates"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    party_id = Column(String, ForeignKey("parties.id"), nullable=False)
    state = Column(String, nullable=False, index=True)
    constituency = Column(String, nullable=False)
    year = Column(Integer, nullable=False, index=True) # e.g. 2024
    election = Column(String, nullable=True, index=True)  # e.g. "Lok Sabha 2024", "Karnataka 2023"
    house = Column(String, nullable=True, index=True)  # "Lok Sabha" | "Vidhan Sabha"
    is_winner = Column(Boolean, nullable=True)  # None = not known
    assets = Column(Float, nullable=False) # In INR
    liabilities = Column(Float, nullable=False) # In INR
    criminal_cases = Column(Integer, nullable=False, default=0)
    education = Column(String, nullable=False)
    source_name = Column(String, nullable=False) # e.g., "MyNeta / ADR"
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    party = relationship("Party", back_populates="candidates")


class NGO(Base):
    __tablename__ = "ngos"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    fcra_registration_number = Column(String, unique=True, index=True, nullable=False)
    state = Column(String, nullable=False, index=True)
    sector = Column(String, nullable=False, index=True) # e.g. "Media", "Policy & Advocacy", "Social Relief"
    registration_status = Column(String, nullable=False, index=True) # "Active", "Suspended", "Cancelled"
    data_as_of = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    donations = relationship("NGODonation", back_populates="ngo")


class NGODonation(Base):
    __tablename__ = "ngo_donations"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    ngo_id = Column(Integer, ForeignKey("ngos.id"), nullable=False, index=True)
    amount = Column(Float, nullable=False) # In INR
    year = Column(Integer, nullable=False, index=True)
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    ngo = relationship("NGO", back_populates="donations")


class Legislator(Base):
    __tablename__ = "legislators"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String, nullable=False, index=True)
    party_id = Column(String, ForeignKey("parties.id"), nullable=False)
    state = Column(String, nullable=False, index=True)
    constituency = Column(String, nullable=False)
    attendance_pct = Column(Float, nullable=False) # e.g., 85.0
    debates_count = Column(Integer, nullable=False, default=0)
    questions_count = Column(Integer, nullable=False, default=0)
    bills_introduced = Column(Integer, nullable=False, default=0) # Private Member Bills
    session_year = Column(Integer, nullable=False, index=True) # e.g. 2024
    source_name = Column(String, nullable=False)
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    party = relationship("Party")


class MPActivity(Base):
    __tablename__ = "mp_activity"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    mp_name = Column(String, nullable=False, index=True)
    constituency = Column(String, nullable=False)
    party_name = Column(String, nullable=False, index=True)
    state_represented = Column(String, nullable=False, index=True)
    attendance_pct = Column(Float, nullable=True)
    debates_count = Column(Integer, nullable=True, default=0)
    questions_count = Column(Integer, nullable=True, default=0)
    bills_introduced = Column(Integer, nullable=True, default=0)
    official_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("mp_name", "constituency", "state_represented", name="uq_mp_activity_member"),
        Index("ix_mp_activity_state_name", "state_represented", "mp_name"),
    )


class LegislativeBill(Base):
    __tablename__ = "legislative_bills"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bill_title = Column(String, nullable=False, index=True)
    ministry = Column(String, nullable=False, index=True)
    current_status = Column(String, nullable=False, index=True)
    state_represented = Column(String, nullable=False, index=True)
    introduced_by = Column(String, nullable=False, index=True)
    introduced_on = Column(String, nullable=True)
    official_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        UniqueConstraint("bill_title", "introduced_by", "official_url", name="uq_legislative_bill_record"),
        Index("ix_legislative_bills_state_status", "state_represented", "current_status"),
    )


class WeeklyBrief(Base):
    __tablename__ = "weekly_briefs"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    brief_text = Column(String, nullable=False)
    source_citation = Column(String, nullable=True)  # Plain text or JSON structure
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ElectoralBond(Base):
    """
    Denormalized raw archive of individual Electoral Bond transactions.
    Tracks the five required fields: donor_name, party_name, amount,
    date, and bank_branch.  Sourced from the apoorv74/electoral-bonds-sbi
    dataset (CSV only — no AGPL R scripts used).
    """
    __tablename__ = "electoral_bonds"

    id            = Column(Integer, primary_key=True, index=True, autoincrement=True)
    donor_name    = Column(String, nullable=False, index=True)   # purchaserName (upper-cased)
    party_name    = Column(String, nullable=False, index=True)   # politicalParty (canonical)
    amount        = Column(Float,  nullable=False)               # denomination in INR
    date          = Column(String, nullable=True)                # ISO YYYY-MM-DD (encashment date)
    bank_branch   = Column(String, nullable=True, default="SBI") # branch not in source → defaults to SBI
    fiscal_year   = Column(Integer, nullable=False, index=True)  # April-March fiscal year
    source_name   = Column(String, nullable=False)
    source_url    = Column(String, nullable=False)
    created_at    = Column(DateTime, default=datetime.datetime.utcnow)

    __table_args__ = (
        Index("ix_eb_party_year", "party_name", "fiscal_year"),
    )



class DonorAlias(Base):
    """Every raw purchaser spelling that was merged into a Donor (see app/entities.py)."""
    __tablename__ = "donor_aliases"

    id = Column(Integer, primary_key=True, autoincrement=True)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=False, index=True)
    raw_name = Column(String, nullable=False, unique=True)
    bond_count = Column(Integer, nullable=False, default=0)


class EntityEvent(Base):
    """Sourced, dated events about a bond purchaser (raids, contract awards, ...) for timeline cross-referencing."""
    __tablename__ = "entity_events"

    id = Column(Integer, primary_key=True, autoincrement=True)
    donor_id = Column(Integer, ForeignKey("donors.id"), nullable=True, index=True)
    entity_name = Column(String, nullable=False, index=True)  # as given in the source CSV
    event_date = Column(String, nullable=False)  # YYYY-MM-DD
    event_type = Column(String, nullable=False, index=True)  # e.g. "raid", "contract", "regulatory"
    description = Column(String, nullable=False)
    source_name = Column(String, nullable=True)
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class ParliamentQuestion(Base):
    """A question asked in the Lok Sabha (one row per asking member)."""
    __tablename__ = "parliament_questions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    lok_sabha = Column(Integer, nullable=False, index=True)  # 15, 16, 17, 18
    date = Column(String, nullable=False, index=True)  # YYYY-MM-DD
    title = Column(String, nullable=False)
    question_type = Column(String, nullable=True)  # Starred | Unstarred
    ministry = Column(String, nullable=True, index=True)
    representative = Column(String, nullable=False, index=True)
    official_url = Column(String, nullable=False)  # answer PDF on sansad.in
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)


class QuestionMention(Base):
    """A question whose title names a bond purchaser (exact phrase match, see app/import_questions.py)."""
    __tablename__ = "question_mentions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    question_id = Column(Integer, ForeignKey("parliament_questions.id"), nullable=False, index=True)
    donor_name = Column(String, nullable=False, index=True)  # canonical purchaser name
    matched_text = Column(String, nullable=False)


class AssetComparison(Base):
    """Declared assets of a candidate in two elections (MyNeta's re-contest comparison)."""
    __tablename__ = "asset_comparisons"

    id = Column(Integer, primary_key=True, autoincrement=True)
    election = Column(String, nullable=False, index=True)          # e.g. "Lok Sabha 2024"
    previous_election = Column(String, nullable=False)              # e.g. "Lok Sabha 2019"
    myneta_id = Column(Integer, nullable=False, index=True)         # candidate id in the later election
    previous_myneta_id = Column(Integer, nullable=True)
    name = Column(String, nullable=False)
    party = Column(String, nullable=True)
    assets = Column(Float, nullable=False)
    previous_assets = Column(Float, nullable=False)
    remarks = Column(String, nullable=True)
    source_url = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
