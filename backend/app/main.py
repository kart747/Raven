import csv
import json
import logging
import os
import secrets
import threading
from contextlib import asynccontextmanager
from io import StringIO
from typing import Iterable, List, Optional, Sequence, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import Depends, FastAPI, Header, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from sqlalchemy import case, desc, func, or_
from sqlalchemy.orm import Session

from . import crud, models, schemas
from .brief_worker import generate_and_save_weekly_brief
from .database import ensure_schema, get_db, SessionLocal
from .pib_ingest import PIB_FEEDS, get_cached_pib_releases
from .seed import seed_db

logger = logging.getLogger("raven")

MAX_PAGE = 1000
MAX_EXPORT_ROWS = 100_000
ALLOWED_ORIGINS = [
    o.strip()
    for o in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173").split(",")
    if o.strip()
]

ensure_schema()
scheduler = BackgroundScheduler()


def _warn_if_empty():
    db = SessionLocal()
    try:
        empty = [
            name for name, model in (
                ("electoral bonds", models.ElectoralBond),
                ("NGOs", models.NGO),
                ("MP activity", models.MPActivity),
            )
            if db.query(model).count() == 0
        ]
        if empty:
            logger.warning("No data loaded for: %s. Run `python -m app.cli ingest-all`.", ", ".join(empty))
        has_brief = db.query(models.WeeklyBrief).count() > 0
    finally:
        db.close()
    return has_brief


def _refresh_legislative():
    """Weekly re-pull of Lok Sabha activity (the source CSVs update after each session)."""
    from .legislative_ingest import ingest_legislative_data
    db = SessionLocal()
    try:
        logger.info("Legislative refresh: %s", ingest_legislative_data(db, refresh=True))
    except Exception:
        logger.exception("Legislative refresh failed")
    finally:
        db.close()


@asynccontextmanager
async def lifespan(app: FastAPI):
    seed_db()
    if not _warn_if_empty():
        # Generate in the background so a slow or missing LLM never blocks startup
        threading.Thread(target=generate_and_save_weekly_brief, daemon=True).start()
    scheduler.add_job(generate_and_save_weekly_brief, "interval", days=7, id="weekly_brief_job")
    if os.getenv("ENABLE_SCHEDULED_INGEST") == "1":
        scheduler.add_job(_refresh_legislative, "interval", days=7, id="legislative_refresh_job")
    scheduler.start()
    yield
    scheduler.shutdown()


app = FastAPI(
    title="Raven API",
    description="Factual OSINT tracker for Indian political and foreign influence data",
    version="1.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)


def require_admin(x_admin_key: Optional[str] = Header(None)):
    expected = os.getenv("ADMIN_API_KEY")
    if not expected:
        raise HTTPException(status_code=403, detail="Admin endpoints are disabled (ADMIN_API_KEY not set)")
    if not x_admin_key or not secrets.compare_digest(x_admin_key, expected):
        raise HTTPException(status_code=401, detail="Invalid admin key")


def csv_response(rows: Iterable[dict], columns: Sequence[Tuple[str, str]], filename: str) -> StreamingResponse:
    """Stream rows as CSV. `columns` is a list of (header, dict key)."""
    def generate():
        buf = StringIO()
        writer = csv.writer(buf)
        writer.writerow([header for header, _ in columns])
        yield buf.getvalue()
        for row in rows:
            buf.seek(0)
            buf.truncate(0)
            writer.writerow(["" if row.get(key) is None else row.get(key) for _, key in columns])
            yield buf.getvalue()

    return StreamingResponse(
        generate(),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


def paged(results, total, limit, offset):
    return {"data": results, "total": total, "limit": limit, "offset": offset}


@app.get("/")
def read_root():
    return {"message": "Welcome to Raven API. Go to /docs for API documentation."}


# --- Parties ---
@app.get("/api/v1/parties", response_model=List[schemas.PartyStatsResponse])
def read_parties(db: Session = Depends(get_db)):
    """Retrieve list of political parties along with total funding and donation counts."""
    return crud.get_parties(db)


# --- Donors ---
@app.get("/api/v1/donors", response_model=List[schemas.DonorResponse])
def read_donors(
    search: Optional[str] = Query(None, description="Search donor names"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """List and search corporate/individual donors."""
    return crud.get_donors(db, search=search, limit=limit, offset=offset)


# --- Donations ---
DONATION_CSV_COLUMNS = [
    ("Donation ID", "id"), ("Party ID", "party_id"), ("Party Name", "party_name"),
    ("Donor Name", "donor_name"), ("Donor Sector/Industry", "donor_industry"),
    ("Amount (INR)", "amount"), ("Date", "date"), ("Fiscal Year", "year"),
    ("Funding Type", "funding_type"), ("Source Name", "source_name"), ("Source URL", "source_url"),
]


@app.get("/api/v1/donations")
def read_donations(
    party_id: Optional[str] = Query(None, description="Filter by party ID"),
    donor_id: Optional[int] = Query(None, description="Filter by donor ID"),
    year: Optional[int] = Query(None, description="Filter by fiscal year (April-March, start year)"),
    funding_type: Optional[str] = Query(None, description="Filter by funding type"),
    search: Optional[str] = Query(None, description="Search donors or parties"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    export_csv: bool = Query(False, description="Export as CSV"),
    db: Session = Depends(get_db)
):
    """Retrieve donations with filtering, searching, and CSV export."""
    filters = dict(party_id=party_id, donor_id=donor_id, year=year, funding_type=funding_type, search=search)
    if export_csv:
        results, _ = crud.get_donations(db, **filters, limit=MAX_EXPORT_ROWS, offset=0)
        return csv_response(results, DONATION_CSV_COLUMNS, "raven_donations.csv")
    results, total = crud.get_donations(db, **filters, limit=limit, offset=offset)
    return paged(results, total, limit, offset)


@app.get("/api/v1/donations/stats", response_model=schemas.DashboardStats)
def read_donations_stats(
    year: Optional[int] = Query(None, description="Filter stats by fiscal year"),
    db: Session = Depends(get_db)
):
    """Aggregate statistics for dashboard charts."""
    return crud.get_dashboard_stats(db, year=year)


# --- Candidates ---
CANDIDATE_CSV_COLUMNS = [
    ("Candidate ID", "id"), ("Candidate Name", "name"), ("Party ID", "party_id"),
    ("Party Name", "party_name"), ("State", "state"), ("Constituency", "constituency"),
    ("Election", "election"), ("House", "house"), ("Won", "is_winner"), ("Total Assets (INR)", "assets"), ("Liabilities (INR)", "liabilities"),
    ("Criminal Cases Declared", "criminal_cases"), ("Education", "education"),
    ("Source Name", "source_name"), ("Source URL", "source_url"),
]


@app.get("/api/v1/candidates")
def read_candidates(
    state: Optional[str] = Query(None, description="Filter by candidate state"),
    party_id: Optional[str] = Query(None, description="Filter by party ID"),
    search: Optional[str] = Query(None, description="Search candidate name or constituency"),
    sort_by: Optional[str] = Query(None, description="Sort candidates by 'assets' or 'criminal_cases'"),
    house: Optional[str] = Query(None, description="'Lok Sabha' or 'Vidhan Sabha'"),
    election: Optional[str] = Query(None, description="e.g. 'Lok Sabha 2024', 'Karnataka 2023'"),
    winners_only: bool = Query(False, description="Only election winners (sitting MPs/MLAs)"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    export_csv: bool = Query(False, description="Export as CSV"),
    db: Session = Depends(get_db)
):
    """Candidate affidavit dossiers with filtering, sorting, and CSV export."""
    filters = dict(state=state, party_id=party_id, search=search, sort_by=sort_by,
                   house=house, election=election, winners_only=winners_only)
    if export_csv:
        results, _ = crud.get_candidates(db, **filters, limit=MAX_EXPORT_ROWS, offset=0)
        return csv_response(results, CANDIDATE_CSV_COLUMNS, "raven_candidates.csv")
    results, total = crud.get_candidates(db, **filters, limit=limit, offset=offset)
    return paged(results, total, limit, offset)


@app.get("/api/v1/candidates/elections")
def read_candidate_elections(db: Session = Depends(get_db)):
    """Elections with imported affidavits, newest first."""
    rows = db.query(
        models.Candidate.election, models.Candidate.house, models.Candidate.state, models.Candidate.year,
        func.count(models.Candidate.id),
    ).filter(models.Candidate.election.isnot(None))\
     .group_by(models.Candidate.election, models.Candidate.house, models.Candidate.state, models.Candidate.year).all()
    elections = {}
    for election, house, state, year, count in rows:
        e = elections.setdefault(election, {"election": election, "house": house, "year": year, "count": 0,
                                            "state": state if house == "Vidhan Sabha" else None})
        e["count"] += count
    return sorted(elections.values(), key=lambda e: (-e["year"], e["election"]))


@app.get("/api/v1/candidates/state-summary")
def read_candidate_state_summary(
    house: str = Query("Lok Sabha", description="'Lok Sabha' (all candidates) or 'Vidhan Sabha' (sitting MLAs)"),
    db: Session = Depends(get_db),
):
    """Per-state candidate totals for the map (computed in SQL)."""
    rows = db.query(
        models.Candidate.state,
        func.count(models.Candidate.id),
        func.coalesce(func.sum(models.Candidate.assets), 0.0),
        func.coalesce(func.sum(models.Candidate.criminal_cases), 0),
        func.sum(case((models.Candidate.criminal_cases > 0, 1), else_=0)),
    ).filter(models.Candidate.house == house).group_by(models.Candidate.state).all()
    return {
        state: {
            "candidate_count": count,
            "total_assets": float(assets),
            "total_cases": int(cases),
            "candidates_with_cases": int(with_cases or 0),
        }
        for state, count, assets, cases, with_cases in rows
    }


@app.get("/api/v1/ngos/state-summary/{state}")
def read_ngo_state_summary(state: str, top: int = Query(50, ge=1, le=500), db: Session = Depends(get_db)):
    """NGO totals for one state, computed in SQL, plus the top recipients."""
    in_state = models.NGO.state.ilike(state)
    ngo_count = db.query(func.count(models.NGO.id)).filter(in_state).scalar()
    total, contributions = db.query(
        func.coalesce(func.sum(models.NGODonation.amount), 0.0), func.count(models.NGODonation.id)
    ).join(models.NGO, models.NGO.id == models.NGODonation.ngo_id).filter(in_state).one()
    statuses = dict(
        db.query(models.NGO.registration_status, func.count(models.NGO.id))
        .filter(in_state).group_by(models.NGO.registration_status).all()
    )
    top_ngos, _ = crud.get_ngos(db, state=state, limit=top, offset=0)
    return {
        "state": state,
        "ngos_count": ngo_count,
        "total_funding": float(total),
        "total_donations": contributions,
        "status_counts": statuses,
        "top_ngos": top_ngos,
    }


# --- Sources / Provenance ---
@app.get("/api/v1/sources")
def read_sources():
    """Data providers, links, and licence notes."""
    return [
        {
            "id": "eci_electoral_bonds",
            "provider": "SBI disclosure to the Election Commission of India (21 Mar 2024)",
            "data_scope": "Electoral bond purchases and encashments, matched on unique bond number (Apr 2019 – Feb 2024).",
            "source_url": "https://www.eci.gov.in/disclosure-of-electoral-bonds",
            "license": "Official public disclosure (Supreme Court order)",
            "refresh_frequency": "Static historical archive (scheme struck down Feb 2024)",
            "status": "Imported",
        },
        {
            "id": "myneta_candidates",
            "provider": "MyNeta (ADR)",
            "data_scope": "Candidate self-declared affidavits: education, assets, liabilities, criminal cases.",
            "source_url": "https://myneta.info",
            "license": "Public election affidavits",
            "refresh_frequency": "Election cycles",
            "status": "Not yet imported",
        },
        {
            "id": "fcra_returns",
            "provider": "FCRA annual returns (Ministry of Home Affairs), via the fcra_repo scrape",
            "data_scope": "Foreign contribution received per NGO, FY2016-17 to FY2020-21. Registration status is only shown where verified.",
            "source_url": "https://fcraonline.nic.in",
            "license": "Official government public records",
            "refresh_frequency": "Static snapshot",
            "status": "Imported",
        },
        {
            "id": "lok_sabha_activity",
            "provider": "Vonter / india-representatives-activity (from Lok Sabha records)",
            "data_scope": "18th Lok Sabha MP attendance, debates, questions, and private member bills.",
            "source_url": "https://github.com/Vonter/india-representatives-activity",
            "license": "Public parliamentary records",
            "refresh_frequency": "Sessional",
            "status": "Imported",
        },
        {
            "id": "pib_rss",
            "provider": "Press Information Bureau (PIB) RSS",
            "data_scope": "Official government press releases.",
            "source_url": "https://pib.gov.in",
            "license": "Government press releases",
            "refresh_frequency": "Live, cached 15 minutes",
            "status": "Live",
        },
    ]


# --- PIB RSS Releases ---
@app.get("/api/v1/pib/releases", response_model=schemas.PIBReleaseListResponse)
def read_pib_releases(
    mod_id: Optional[int] = Query(6, ge=1, description="Filter by PIB ModId"),
    regid: Optional[int] = Query(3, ge=1, description="Filter by PIB Regid"),
    search: Optional[str] = Query(None, description="Search PIB title or ministry tag"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
):
    try:
        releases = get_cached_pib_releases(mod_id, regid)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to fetch PIB releases: {e}")

    if search:
        s = search.lower()
        releases = [
            r for r in releases
            if s in (r.get("title") or "").lower() or s in (r.get("ministry_tag") or "").lower()
        ]
    return paged(releases[offset:offset + limit], len(releases), limit, offset)


@app.post("/api/v1/pib/sync", response_model=schemas.PIBSyncResponse)
def sync_pib_releases():
    total_refreshed = 0
    for feed in PIB_FEEDS:
        try:
            total_refreshed += len(get_cached_pib_releases(feed["mod_id"], feed["regid"], force_refresh=True))
        except Exception:
            logger.exception("PIB sync failed for %s", feed)
    return {"feeds_polled": len(PIB_FEEDS), "releases_added_or_updated": total_refreshed}


# --- NGOs ---
@app.get("/api/v1/ngos")
def read_ngos(
    status: Optional[str] = Query(None, description="Filter by NGO registration status"),
    state: Optional[str] = Query(None, description="Filter by state"),
    sector: Optional[str] = Query(None, description="Filter by sector"),
    search: Optional[str] = Query(None, description="Search NGO name or FCRA registration number"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Search NGOs with status, state, and sector filters."""
    results, total = crud.get_ngos(
        db, status=status, state=state, sector=sector, search=search, limit=limit, offset=offset
    )
    return paged(results, total, limit, offset)


@app.get("/api/v1/ngos/stats", response_model=schemas.NGOStats)
def read_ngos_stats(db: Session = Depends(get_db)):
    """Aggregate NGO foreign funding statistics, including year-over-year spikes."""
    return crud.get_ngo_stats(db)


@app.get("/api/v1/ngos/{ngo_id}", response_model=schemas.NGODetailResponse)
def read_ngo(ngo_id: int, db: Session = Depends(get_db)):
    """A single NGO with its contribution records."""
    ngo = crud.get_ngo_by_id(db, ngo_id=ngo_id)
    if not ngo:
        raise HTTPException(status_code=404, detail="NGO not found")
    return ngo


NGO_DONATION_CSV_COLUMNS = [
    ("Donation ID", "id"), ("NGO ID", "ngo_id"), ("NGO Name", "ngo_name"),
    ("FCRA Number", "fcra_registration_number"), ("NGO State", "ngo_state"),
    ("NGO Sector (inferred from name)", "ngo_sector"), ("Registration Status", "ngo_registration_status"),
    ("Amount (INR)", "amount"), ("Fiscal Year", "year"), ("Source Name", "source_name"), ("Source URL", "source_url"),
]


@app.get("/api/v1/ngo-donations")
def read_ngo_donations(
    ngo_id: Optional[int] = Query(None, description="Filter by NGO ID"),
    year: Optional[int] = Query(None, description="Filter by fiscal year (start year)"),
    search: Optional[str] = Query(None, description="Search NGO name or registration"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    export_csv: bool = Query(False, description="Export as CSV"),
    db: Session = Depends(get_db)
):
    """Foreign contribution records with filters and CSV export."""
    filters = dict(ngo_id=ngo_id, year=year, search=search)
    if export_csv:
        results, _ = crud.get_ngo_donations(db, **filters, limit=MAX_EXPORT_ROWS, offset=0)
        return csv_response(results, NGO_DONATION_CSV_COLUMNS, "raven_ngo_foreign_funding.csv")
    results, total = crud.get_ngo_donations(db, **filters, limit=limit, offset=offset)
    return paged(results, total, limit, offset)


# --- Legislative Activity & Attendance Monitor ---
MP_ACTIVITY_CSV_COLUMNS = [
    ("MP Activity ID", "id"), ("MP Name", "mp_name"), ("Party Name", "party_name"),
    ("State", "state_represented"), ("Constituency", "constituency"), ("Attendance Pct", "attendance_pct"),
    ("Debates Count", "debates_count"), ("Questions Count", "questions_count"),
    ("Bills Introduced", "bills_introduced"), ("Source URL", "official_url"),
]


@app.get("/api/v1/mp-activity")
def read_mp_activity(
    state: Optional[str] = Query(None),
    party_name: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    outlier: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    export_csv: bool = Query(False),
    db: Session = Depends(get_db)
):
    filters = dict(state=state, party_name=party_name, search=search, outlier=outlier, sort_by=sort_by)
    if export_csv:
        results, _ = crud.get_mp_activity(db, **filters, limit=MAX_EXPORT_ROWS, offset=0)
        return csv_response(results, MP_ACTIVITY_CSV_COLUMNS, "raven_mp_activity.csv")
    results, total = crud.get_mp_activity(db, **filters, limit=limit, offset=offset)
    return paged(results, total, limit, offset)


@app.get("/api/v1/mp-activity/stats", response_model=schemas.MPActivityStats)
def read_mp_activity_stats(db: Session = Depends(get_db)):
    return crud.get_mp_activity_stats(db)


@app.get("/api/v1/legislators", deprecated=True)
def read_legislators(
    state: Optional[str] = Query(None),
    party_id: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    outlier: Optional[str] = Query(None),
    sort_by: Optional[str] = Query(None),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Deprecated alias for /api/v1/mp-activity with legacy field names."""
    results, total = crud.get_legislators(
        db, state=state, party_id=party_id, search=search,
        outlier=outlier, sort_by=sort_by, limit=limit, offset=offset
    )
    return paged(results, total, limit, offset)


@app.get("/api/v1/legislators/stats", response_model=schemas.LegislatorStats, deprecated=True)
def read_legislator_stats(db: Session = Depends(get_db)):
    return crud.get_legislator_stats(db)


@app.get("/api/v1/legislative/bills", response_model=schemas.LegislativeBillListResponse)
def read_legislative_bills(
    status: Optional[str] = Query(None, description="Filter by bill status"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    db: Session = Depends(get_db)
):
    results, total = crud.get_legislative_bills(db, status=status, limit=limit)
    return {"data": results, "total": total, "limit": limit}


@app.get("/api/v1/legislative/state/{state_name}", response_model=schemas.LegislativeStateDossierResponse)
def read_legislative_state_dossier(state_name: str, db: Session = Depends(get_db)):
    return crud.get_legislative_state_dossier(db, state_name)


# --- AI Brief ---
@app.get("/api/v1/brief/latest")
def read_latest_brief(db: Session = Depends(get_db)):
    """Latest AI-generated brief. Generation happens in the background, never on request."""
    brief = db.query(models.WeeklyBrief).order_by(models.WeeklyBrief.created_at.desc()).first()
    if not brief:
        return {"brief_unavailable": True}

    try:
        citation = json.loads(brief.source_citation) if brief.source_citation else {}
    except ValueError:
        citation = {"sources": []}

    return {
        "id": brief.id,
        "brief_text": brief.brief_text,
        "source_citation": citation,
        "created_at": brief.created_at,
    }


# --- State Dossier: map click -> party funding + candidate affidavit averages ---
@app.get("/api/v1/political/state-dossier/{state}")
def read_state_dossier(
    state: str,
    year: Optional[int] = Query(None, description="Filter affidavit year"),
    db: Session = Depends(get_db)
):
    """
    Party-wise electoral bond totals (national: the disclosure has no state field)
    plus candidate affidavit averages for the requested state.
    """
    total_bonds = func.sum(models.Donation.amount)
    party_rows = db.query(
        models.Donation.party_id,
        models.Party.name,
        total_bonds,
        func.count(models.Donation.id),
    ).join(models.Party, models.Donation.party_id == models.Party.id)\
     .filter(models.Donation.funding_type == "Electoral Bond")\
     .group_by(models.Donation.party_id, models.Party.name)\
     .order_by(desc(total_bonds))\
     .all()

    party_funding = [
        {
            "party_id": pid,
            "party_name": pname,
            "total_bonds_inr": float(total),
            "total_bonds_crore": round(float(total) / 1e7, 2),
            "bond_transactions": cnt,
        }
        for pid, pname, total, cnt in party_rows
    ]

    cand_filter = [models.Candidate.state.ilike(state)]
    if year:
        cand_filter.append(models.Candidate.year == year)

    count, avg_assets, avg_liabilities, avg_criminal = db.query(
        func.count(models.Candidate.id),
        func.coalesce(func.avg(models.Candidate.assets), 0.0),
        func.coalesce(func.avg(models.Candidate.liabilities), 0.0),
        func.coalesce(func.avg(models.Candidate.criminal_cases), 0.0),
    ).filter(*cand_filter).one()

    party_candidate_rows = db.query(
        models.Candidate.party_id,
        models.Party.name,
        func.count(models.Candidate.id).label("candidate_count"),
        func.avg(models.Candidate.assets),
        func.avg(models.Candidate.criminal_cases),
    ).join(models.Party, models.Candidate.party_id == models.Party.id)\
     .filter(*cand_filter)\
     .group_by(models.Candidate.party_id, models.Party.name)\
     .order_by(desc("candidate_count"))\
     .all()

    party_candidates = [
        {
            "party_id": pid,
            "party_name": pname,
            "candidate_count": cnt,
            "avg_assets_crore": round(float(avg or 0) / 1e7, 2),
            "avg_criminal_cases": round(float(crim or 0), 2),
        }
        for pid, pname, cnt, avg, crim in party_candidate_rows
    ]

    return {
        "state": state,
        "year_filter": year,
        "total_candidates": count,
        "avg_net_worth_crore": round((avg_assets - avg_liabilities) / 1e7, 2),
        "avg_assets_crore": round(avg_assets / 1e7, 2),
        "avg_liabilities_crore": round(avg_liabilities / 1e7, 2),
        "avg_criminal_cases": round(avg_criminal, 2),
        "party_funding_national": party_funding,
        "party_candidates_state": party_candidates,
        "data_sources": [
            {
                "label": "Electoral Bond Encashment",
                "note": "National-level totals; the disclosure has no state field",
                "url": "https://www.eci.gov.in/disclosure-of-electoral-bonds",
            },
            {
                "label": "Candidate Affidavits",
                "note": "Self-declared in election nomination forms (ADR/MyNeta)",
                "url": "https://myneta.info",
            },
        ],
    }


# --- Electoral Bonds Raw Archive ---
@app.get("/api/v1/electoral-bonds")
def read_electoral_bonds(
    party_name: Optional[str] = Query(None, description="Filter by party name (partial match)"),
    donor_name: Optional[str] = Query(None, description="Filter by donor name (partial match)"),
    year: Optional[int] = Query(None, description="Filter by fiscal year"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Raw electoral bond archive: donor_name, party_name, amount, date, bank_branch."""
    q = db.query(models.ElectoralBond)
    if party_name:
        q = q.filter(models.ElectoralBond.party_name.ilike(f"%{party_name}%"))
    if donor_name:
        q = q.filter(models.ElectoralBond.donor_name.ilike(f"%{donor_name}%"))
    if year:
        q = q.filter(models.ElectoralBond.fiscal_year == year)
    total = q.order_by(None).with_entities(func.count(models.ElectoralBond.id)).scalar()
    rows = q.order_by(models.ElectoralBond.amount.desc()).offset(offset).limit(limit).all()
    data = [
        {
            "id": r.id,
            "donor_name": r.donor_name,
            "party_name": r.party_name,
            "amount": r.amount,
            "date": r.date,
            "bank_branch": r.bank_branch,
            "fiscal_year": r.fiscal_year,
            "source_name": r.source_name,
        }
        for r in rows
    ]
    return paged(data, total, limit, offset)


# --- Admin ---
@app.post("/api/v1/admin/ingest-electoral-bonds", dependencies=[Depends(require_admin)])
def trigger_electoral_bond_ingest():
    """Re-import electoral bonds (requires X-Admin-Key header) and regenerate the brief."""
    from .import_electoral_bonds import run_import
    try:
        summary = run_import()
    except FileNotFoundError as e:
        raise HTTPException(status_code=500, detail=str(e))

    threading.Thread(target=generate_and_save_weekly_brief, daemon=True).start()
    return {"status": "ok", "message": "Electoral bond import complete. Brief regeneration triggered.", "summary": summary}


# --- Donor profile: merged spellings, party split, timeline, sourced events ---
@app.get("/api/v1/donors/{donor_id}")
def read_donor_profile(donor_id: int, db: Session = Depends(get_db)):
    donor = db.get(models.Donor, donor_id)
    if not donor:
        raise HTTPException(status_code=404, detail="Donor not found")

    eb = models.Donation.funding_type == "Electoral Bond"
    by_party = db.query(
        models.Party.id, models.Party.name, func.sum(models.Donation.amount), func.count(models.Donation.id)
    ).join(models.Donation, models.Donation.party_id == models.Party.id)\
     .filter(models.Donation.donor_id == donor_id, eb)\
     .group_by(models.Party.id, models.Party.name)\
     .order_by(desc(func.sum(models.Donation.amount))).all()

    month = func.substr(models.Donation.date, 1, 7)
    timeline = db.query(month, models.Donation.party_id, func.sum(models.Donation.amount))\
        .filter(models.Donation.donor_id == donor_id, eb, models.Donation.date.isnot(None))\
        .group_by(month, models.Donation.party_id).order_by(month).all()

    aliases = db.query(models.DonorAlias.raw_name, models.DonorAlias.bond_count)\
        .filter(models.DonorAlias.donor_id == donor_id).order_by(desc(models.DonorAlias.bond_count)).all()
    events = db.query(models.EntityEvent).filter(models.EntityEvent.donor_id == donor_id)\
        .order_by(models.EntityEvent.event_date).all()
    named_in = db.query(models.ParliamentQuestion, models.QuestionMention.matched_text)\
        .join(models.QuestionMention, models.QuestionMention.question_id == models.ParliamentQuestion.id)\
        .filter(models.QuestionMention.donor_name == donor.name)\
        .order_by(desc(models.ParliamentQuestion.date)).limit(100).all()

    return {
        "id": donor.id,
        "name": donor.name,
        "industry": donor.industry,
        "total_amount": sum(float(t) for _, _, t, _ in by_party),
        "bond_count": sum(c for *_, c in by_party),
        "spellings_in_source": [{"raw_name": n, "bond_count": c} for n, c in aliases],
        "by_party": [
            {"party_id": pid, "party_name": name, "amount": float(t), "bond_count": c}
            for pid, name, t, c in by_party
        ],
        "monthly_encashments": [
            {"month": m, "party_id": pid, "amount": float(t)} for m, pid, t in timeline
        ],
        "events": [
            {
                "id": e.id, "event_date": e.event_date, "event_type": e.event_type,
                "description": e.description, "source_name": e.source_name, "source_url": e.source_url,
            }
            for e in events
        ],
        "questions_naming": [{**_question_dict(q), "matched_text": t} for q, t in named_in],
        "note": "Dates are encashment dates. Events are loaded from a sourced CSV and shown for "
                "reference only; a date overlap is not evidence of a connection.",
    }


# --- Party profile: money in, representatives, affidavits, parliament ---
@app.get("/api/v1/parties/{party_id}/profile")
def read_party_profile(party_id: str, db: Session = Depends(get_db)):
    party = db.get(models.Party, party_id)
    if not party:
        raise HTTPException(status_code=404, detail="Party not found")
    D, C = models.Donation, models.Candidate
    eb = [D.party_id == party_id, D.funding_type == "Electoral Bond"]
    amount = func.sum(D.amount)

    bond_total, bond_count = db.query(func.coalesce(amount, 0.0), func.count(D.id)).filter(*eb).one()
    by_year = db.query(D.year, amount, func.count(D.id)).filter(*eb).group_by(D.year).order_by(D.year).all()
    top = db.query(models.Donor.id, models.Donor.name, amount, func.count(D.id))\
        .join(D, D.donor_id == models.Donor.id).filter(*eb)\
        .group_by(models.Donor.id, models.Donor.name).order_by(desc(amount)).limit(16).all()
    undisclosed = next((float(t) for _, n, t, _ in top if n == "UNKNOWN DONOR"), 0.0)

    def reps(*flt):
        return db.query(C).filter(C.party_id == party_id, *flt)

    mps = reps(C.house == "Lok Sabha", C.is_winner.is_(True)).order_by(C.state, C.constituency).all()
    mla_by_state = db.query(C.state, C.election, func.count(C.id))\
        .filter(C.party_id == party_id, C.house == "Vidhan Sabha")\
        .group_by(C.state, C.election).order_by(desc(func.count(C.id))).all()
    ls_count, ls_with_cases, ls_avg_assets = db.query(
        func.count(C.id), func.sum(case((C.criminal_cases > 0, 1), else_=0)), func.avg(C.assets),
    ).filter(C.party_id == party_id, C.house == "Lok Sabha").one()
    mla_count, mla_with_cases = db.query(
        func.count(C.id), func.sum(case((C.criminal_cases > 0, 1), else_=0)),
    ).filter(C.party_id == party_id, C.house == "Vidhan Sabha").one()

    attendance, mp_rows = db.query(func.avg(models.MPActivity.attendance_pct), func.count(models.MPActivity.id))\
        .filter(models.MPActivity.party_name == party.name).one()

    return {
        "id": party.id,
        "name": party.name,
        "bonds": {
            "total": float(bond_total), "count": bond_count, "undisclosed_purchaser_amount": undisclosed,
            "by_fiscal_year": [{"year": y, "amount": float(a), "count": n} for y, a, n in by_year],
            "top_purchasers": [{"id": i, "name": n, "amount": float(a), "count": c}
                               for i, n, a, c in top if n != "UNKNOWN DONOR"][:15],
        },
        "lok_sabha_2024": {
            "candidates": ls_count, "winners": len(mps),
            "candidates_declaring_cases": int(ls_with_cases or 0),
            "avg_declared_assets": float(ls_avg_assets or 0),
            "mps": [{"id": m.id, "name": m.name, "constituency": m.constituency, "state": m.state,
                     "assets": m.assets, "criminal_cases": m.criminal_cases, "source_url": m.source_url} for m in mps],
        },
        "assemblies": {
            "mlas": mla_count, "mlas_declaring_cases": int(mla_with_cases or 0),
            "by_state": [{"state": st, "election": e, "mlas": n} for st, e, n in mla_by_state],
        },
        "parliament": {"mps_with_activity_data": mp_rows,
                       "avg_attendance_pct": round(float(attendance), 1) if attendance is not None else None},
        "notes": [
            "Bond totals are encashments into this party's accounts (Apr 2019 - Feb 2024).",
            "Representatives are matched by MyNeta's party label; post-split factions are separate parties.",
            "'Declaring cases' means pending criminal cases declared in the affidavit, not convictions.",
        ],
    }


# --- Search across every dataset ---
@app.get("/api/v1/search")
def search_everything(
    q: str = Query(..., min_length=2, max_length=100),
    per_group: int = Query(5, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """One query across purchasers (incl. raw SBI spellings), candidates, NGOs, MPs and questions."""
    like = f"%{q.strip()}%"
    out = {}

    party_hits = db.query(models.Party).filter(or_(models.Party.name.ilike(like), models.Party.id.ilike(like)))
    out["parties"] = {
        "total": party_hits.order_by(None).count(),
        "items": [{"id": p.id, "name": p.name} for p in party_hits.order_by(models.Party.name).limit(per_group)],
    }

    alias_hits = db.query(models.DonorAlias.donor_id).filter(models.DonorAlias.raw_name.ilike(like))
    donors = db.query(models.Donor).filter(
        models.Donor.name != "UNKNOWN DONOR",
        or_(models.Donor.name.ilike(like), models.Donor.id.in_(alias_hits)),
    )
    out["purchasers"] = {
        "total": donors.order_by(None).count(),
        "items": [{"id": d.id, "name": d.name} for d in donors.order_by(models.Donor.name).limit(per_group)],
    }

    cands = db.query(models.Candidate).filter(
        or_(models.Candidate.name.ilike(like), models.Candidate.constituency.ilike(like)))
    out["candidates"] = {
        "total": cands.order_by(None).count(),
        "items": [
            {"id": c.id, "name": c.name, "constituency": c.constituency, "state": c.state,
             "election": c.election, "is_winner": c.is_winner, "source_url": c.source_url}
            for c in cands.order_by(desc(models.Candidate.is_winner), desc(models.Candidate.assets)).limit(per_group)
        ],
    }

    ngos = db.query(models.NGO).filter(
        or_(models.NGO.name.ilike(like), models.NGO.fcra_registration_number.ilike(like)))
    out["ngos"] = {
        "total": ngos.order_by(None).count(),
        "items": [{"id": n.id, "name": n.name, "state": n.state, "fcra_registration_number": n.fcra_registration_number}
                  for n in ngos.order_by(models.NGO.name).limit(per_group)],
    }

    mps = db.query(models.MPActivity).filter(
        or_(models.MPActivity.mp_name.ilike(like), models.MPActivity.constituency.ilike(like)))
    out["mps"] = {
        "total": mps.order_by(None).count(),
        "items": [{"id": m.id, "name": m.mp_name, "constituency": m.constituency, "state": m.state_represented,
                   "party": m.party_name} for m in mps.order_by(models.MPActivity.mp_name).limit(per_group)],
    }

    questions = db.query(models.ParliamentQuestion).filter(models.ParliamentQuestion.title.ilike(like))
    out["questions"] = {
        "total": questions.order_by(None).count(),
        "items": [_question_dict(x) for x in
                  questions.order_by(desc(models.ParliamentQuestion.date)).limit(per_group)],
    }
    return out


# --- Lok Sabha questions ---
QUESTION_CSV_COLUMNS = [
    ("Lok Sabha", "lok_sabha"), ("Date", "date"), ("Title", "title"), ("Type", "question_type"),
    ("Ministry", "ministry"), ("Asked by", "representative"), ("Official answer (PDF)", "official_url"),
]


def _question_dict(q):
    return {
        "id": q.id, "lok_sabha": q.lok_sabha, "date": q.date, "title": q.title,
        "question_type": q.question_type, "ministry": q.ministry,
        "representative": q.representative, "official_url": q.official_url,
    }


@app.get("/api/v1/questions")
def read_questions(
    search: Optional[str] = Query(None, description="Words in the question title"),
    ministry: Optional[str] = Query(None),
    representative: Optional[str] = Query(None, description="Member name (partial match)"),
    lok_sabha: Optional[int] = Query(None, ge=15, le=18),
    donor_name: Optional[str] = Query(None, description="Questions whose title names this bond purchaser"),
    limit: int = Query(50, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    export_csv: bool = Query(False),
    db: Session = Depends(get_db),
):
    """Lok Sabha questions (15th-18th), newest first, each linked to its official answer."""
    Q = models.ParliamentQuestion
    q = db.query(Q)
    if search:
        for word in search.split()[:6]:
            q = q.filter(Q.title.ilike(f"%{word}%"))
    if ministry:
        q = q.filter(Q.ministry == ministry)
    if representative:
        q = q.filter(Q.representative.ilike(f"%{representative}%"))
    if lok_sabha:
        q = q.filter(Q.lok_sabha == lok_sabha)
    if donor_name:
        q = q.join(models.QuestionMention, models.QuestionMention.question_id == Q.id)\
             .filter(models.QuestionMention.donor_name == donor_name)
    total = q.order_by(None).with_entities(func.count(Q.id)).scalar()
    ordered = q.order_by(desc(Q.date), Q.id)
    if export_csv:
        rows = (_question_dict(x) for x in ordered.limit(MAX_EXPORT_ROWS).yield_per(5000))
        return csv_response(rows, QUESTION_CSV_COLUMNS, "raven_lok_sabha_questions.csv")
    return paged([_question_dict(x) for x in ordered.offset(offset).limit(limit)], total, limit, offset)


@app.get("/api/v1/questions/stats")
def read_question_stats(lok_sabha: Optional[int] = Query(None, ge=15, le=18), db: Session = Depends(get_db)):
    Q = models.ParliamentQuestion
    flt = [Q.lok_sabha == lok_sabha] if lok_sabha else []
    n = func.count(Q.id)
    year = func.substr(Q.date, 1, 4)
    return {
        "total": db.query(n).filter(*flt).scalar(),
        "date_range": db.query(func.min(Q.date), func.max(Q.date)).filter(*flt).one(),
        "by_ministry": [{"ministry": m, "count": c} for m, c in
                        db.query(Q.ministry, n).filter(*flt).group_by(Q.ministry).order_by(desc(n)).limit(15)],
        "by_year": [{"year": y, "count": c} for y, c in
                    db.query(year, n).filter(*flt).group_by(year).order_by(year)],
        "top_askers": [{"representative": r, "count": c} for r, c in
                       db.query(Q.representative, n).filter(*flt).group_by(Q.representative).order_by(desc(n)).limit(10)],
        "purchasers_named": db.query(func.count(func.distinct(models.QuestionMention.donor_name))).scalar(),
    }


@app.get("/api/v1/questions/ministries")
def read_question_ministries(db: Session = Depends(get_db)):
    Q = models.ParliamentQuestion
    return [m for (m,) in db.query(Q.ministry).filter(Q.ministry.isnot(None)).distinct().order_by(Q.ministry)]


# --- Data quality: coverage and freshness of every dataset ---
@app.get("/api/v1/data-quality")
def read_data_quality(db: Session = Depends(get_db)):
    def last_loaded(model):
        ts = db.query(func.max(model.created_at)).scalar()
        return ts.isoformat() if ts else None

    eb = models.Donation.funding_type == "Electoral Bond"
    bonds, bond_total = db.query(func.count(models.Donation.id), func.coalesce(func.sum(models.Donation.amount), 0.0))\
        .filter(eb).one()
    unknown_q = db.query(func.count(models.Donation.id), func.coalesce(func.sum(models.Donation.amount), 0.0))\
        .join(models.Donor, models.Donor.id == models.Donation.donor_id)\
        .filter(eb, models.Donor.name == "UNKNOWN DONOR")
    unknown_count, unknown_amount = unknown_q.one()
    donors = db.query(func.count(models.Donor.id)).filter(models.Donor.name != "UNKNOWN DONOR").scalar()
    donors_with_industry = db.query(func.count(models.Donor.id)).filter(models.Donor.industry != "Unknown").scalar()
    spellings = db.query(func.count(models.DonorAlias.id)).scalar()

    ngos = db.query(func.count(models.NGO.id)).scalar()
    ngo_verified = db.query(func.count(models.NGO.id)).filter(models.NGO.registration_status != "Unknown").scalar()
    ngo_years = [y for (y,) in db.query(models.NGODonation.year).distinct().order_by(models.NGODonation.year)]

    ls = models.Candidate.house == "Lok Sabha"
    candidates = db.query(func.count(models.Candidate.id)).filter(ls).scalar()
    cand_no_state = db.query(func.count(models.Candidate.id)).filter(ls, models.Candidate.state == "Unknown").scalar()
    cand_states = db.query(func.count(func.distinct(models.Candidate.state))).filter(ls).scalar()
    ls_winners = db.query(func.count(models.Candidate.id)).filter(ls, models.Candidate.is_winner.is_(True)).scalar()
    vs = models.Candidate.house == "Vidhan Sabha"
    mlas = db.query(func.count(models.Candidate.id)).filter(vs).scalar()
    assemblies = db.query(func.count(func.distinct(models.Candidate.election))).filter(vs).scalar()
    mlas_with_cases = db.query(func.count(models.Candidate.id)).filter(vs, models.Candidate.criminal_cases > 0).scalar()
    mla_loaded = db.query(func.max(models.Candidate.created_at)).filter(vs).scalar()

    mps = db.query(func.count(models.MPActivity.id)).scalar()
    mps_no_attendance = db.query(func.count(models.MPActivity.id)).filter(models.MPActivity.attendance_pct.is_(None)).scalar()
    bills = db.query(func.count(models.LegislativeBill.id)).scalar()
    bills_no_state = db.query(func.count(models.LegislativeBill.id))\
        .filter(models.LegislativeBill.state_represented == "Unknown").scalar()

    events = db.query(func.count(models.EntityEvent.id)).scalar()
    events_unmatched = db.query(func.count(models.EntityEvent.id)).filter(models.EntityEvent.donor_id.is_(None)).scalar()

    brief = db.query(models.WeeklyBrief).order_by(models.WeeklyBrief.created_at.desc()).first()
    brief_model = None
    if brief and brief.source_citation:
        try:
            brief_model = json.loads(brief.source_citation).get("model")
        except ValueError:
            pass

    def pct(part, whole):
        return round(100 * part / whole, 1) if whole else None

    return [
        {
            "id": "electoral_bonds", "label": "Electoral bonds",
            "rows": bonds, "last_loaded": last_loaded(models.Donation),
            "metrics": [
                {"label": "Bonds matched to a purchaser", "value": pct(bonds - unknown_count, bonds), "unit": "%"},
                {"label": "Amount with no disclosed purchaser", "value": round(unknown_amount / 1e7, 2), "unit": "₹ Cr"},
                {"label": "Purchaser spellings → companies", "value": f"{spellings} → {donors}"},
                {"label": "Purchasers with sourced industry", "value": pct(donors_with_industry, donors), "unit": "%"},
            ],
            "total_crore": round(bond_total / 1e7, 2),
        },
        {
            "id": "fcra", "label": "FCRA foreign contributions",
            "rows": ngos, "last_loaded": last_loaded(models.NGO),
            "metrics": [
                {"label": "NGOs with verified registration status", "value": pct(ngo_verified, ngos), "unit": "%"},
                {"label": "Fiscal years covered", "value": f"FY{ngo_years[0]}–FY{ngo_years[-1]}" if ngo_years else "—"},
            ],
        },
        {
            "id": "candidates", "label": "Candidate affidavits (Lok Sabha 2024)",
            "rows": candidates, "last_loaded": last_loaded(models.Candidate),
            "metrics": [
                {"label": "States / UTs covered", "value": cand_states},
                {"label": "Winners (sitting MPs)", "value": ls_winners},
                {"label": "Candidates without a state", "value": cand_no_state},
            ],
        },
        {
            "id": "mlas", "label": "Sitting MLAs (latest assembly elections)",
            "rows": mlas, "last_loaded": mla_loaded.isoformat() if mla_loaded else None,
            "metrics": [
                {"label": "Assemblies covered", "value": f"{assemblies} of 31"},
                {"label": "MLAs declaring pending cases", "value": pct(mlas_with_cases, mlas), "unit": "%"},
            ],
        },
        {
            "id": "mp_activity", "label": "Lok Sabha MP activity",
            "rows": mps, "last_loaded": last_loaded(models.MPActivity),
            "metrics": [
                {"label": "MPs without attendance data", "value": mps_no_attendance},
                {"label": "Private member bills", "value": bills},
                {"label": "Bills with no state", "value": bills_no_state},
            ],
        },
        {
            "id": "questions", "label": "Lok Sabha questions (15th-18th)",
            "rows": db.query(func.count(models.ParliamentQuestion.id)).scalar(),
            "last_loaded": last_loaded(models.ParliamentQuestion),
            "metrics": [
                {"label": "Date range", "value": " – ".join(d for d in db.query(
                    func.min(models.ParliamentQuestion.date), func.max(models.ParliamentQuestion.date)).one() if d) or "—"},
                {"label": "Bond purchasers named in titles", "value": db.query(
                    func.count(func.distinct(models.QuestionMention.donor_name))).scalar()},
            ],
        },
        {
            "id": "entity_events", "label": "Sourced purchaser events",
            "rows": events, "last_loaded": last_loaded(models.EntityEvent),
            "metrics": [{"label": "Events not matched to a purchaser", "value": events_unmatched}],
        },
        {
            "id": "brief", "label": "AI brief",
            "rows": db.query(func.count(models.WeeklyBrief.id)).scalar(),
            "last_loaded": brief.created_at.isoformat() if brief else None,
            "metrics": [{"label": "Model", "value": brief_model or "—"}],
        },
    ]
