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
from sqlalchemy import case, desc, func
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
    ("Election Year", "year"), ("Total Assets (INR)", "assets"), ("Liabilities (INR)", "liabilities"),
    ("Criminal Cases Declared", "criminal_cases"), ("Education", "education"),
    ("Source Name", "source_name"), ("Source URL", "source_url"),
]


@app.get("/api/v1/candidates")
def read_candidates(
    state: Optional[str] = Query(None, description="Filter by candidate state"),
    party_id: Optional[str] = Query(None, description="Filter by party ID"),
    search: Optional[str] = Query(None, description="Search candidate name or constituency"),
    sort_by: Optional[str] = Query(None, description="Sort candidates by 'assets' or 'criminal_cases'"),
    limit: int = Query(100, ge=1, le=MAX_PAGE),
    offset: int = Query(0, ge=0),
    export_csv: bool = Query(False, description="Export as CSV"),
    db: Session = Depends(get_db)
):
    """Candidate affidavit dossiers with filtering, sorting, and CSV export."""
    filters = dict(state=state, party_id=party_id, search=search, sort_by=sort_by)
    if export_csv:
        results, _ = crud.get_candidates(db, **filters, limit=MAX_EXPORT_ROWS, offset=0)
        return csv_response(results, CANDIDATE_CSV_COLUMNS, "raven_candidates.csv")
    results, total = crud.get_candidates(db, **filters, limit=limit, offset=offset)
    return paged(results, total, limit, offset)


@app.get("/api/v1/candidates/state-summary")
def read_candidate_state_summary(db: Session = Depends(get_db)):
    """Per-state candidate totals for the map (computed in SQL over all candidates)."""
    rows = db.query(
        models.Candidate.state,
        func.count(models.Candidate.id),
        func.coalesce(func.sum(models.Candidate.assets), 0.0),
        func.coalesce(func.sum(models.Candidate.criminal_cases), 0),
        func.sum(case((models.Candidate.criminal_cases > 0, 1), else_=0)),
    ).group_by(models.Candidate.state).all()
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
        "note": "Dates are encashment dates. Events are loaded from a sourced CSV and shown for "
                "reference only; a date overlap is not evidence of a connection.",
    }


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

    candidates = db.query(func.count(models.Candidate.id)).scalar()
    cand_no_state = db.query(func.count(models.Candidate.id)).filter(models.Candidate.state == "Unknown").scalar()
    cand_states = db.query(func.count(func.distinct(models.Candidate.state))).scalar()

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
                {"label": "Candidates without a state", "value": cand_no_state},
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
