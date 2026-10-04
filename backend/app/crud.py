from sqlalchemy.orm import Session
from sqlalchemy import func, desc, or_
from . import models, schemas

# --- Parties ---
def get_party(db: Session, party_id: str):
    return db.query(models.Party).filter(models.Party.id == party_id).first()

def get_parties(db: Session):
    # Retrieve all parties with aggregate donation statistics
    results = db.query(
        models.Party,
        func.coalesce(func.sum(models.Donation.amount), 0.0).label("total_donations"),
        func.count(models.Donation.id).label("donation_count")
    ).outerjoin(models.Donation, models.Party.id == models.Donation.party_id)\
     .group_by(models.Party.id)\
     .order_by(desc("total_donations"))\
     .all()
    
    parties_list = []
    for party, total, count in results:
        # Convert to dictionary or schema format
        party_dict = {
            "id": party.id,
            "name": party.name,
            "symbol_url": party.symbol_url,
            "total_donations": total,
            "donation_count": count
        }
        parties_list.append(party_dict)
    return parties_list

# --- Donors ---
def get_donors(db: Session, search: str = None, limit: int = 100, offset: int = 0):
    query = db.query(models.Donor)
    if search:
        query = query.filter(models.Donor.name.ilike(f"%{search}%"))
    return query.offset(offset).limit(limit).all()

# --- Donations ---
def get_donations(
    db: Session,
    party_id: str = None,
    donor_id: int = None,
    year: int = None,
    funding_type: str = None,
    search: str = None,
    limit: int = 100,
    offset: int = 0
):
    query = db.query(
        models.Donation,
        models.Party.name.label("party_name"),
        models.Donor.name.label("donor_name"),
        models.Donor.industry.label("donor_industry")
    ).join(models.Party, models.Donation.party_id == models.Party.id)\
     .join(models.Donor, models.Donation.donor_id == models.Donor.id)

    if party_id:
        query = query.filter(models.Donation.party_id == party_id)
    if donor_id:
        query = query.filter(models.Donation.donor_id == donor_id)
    if year:
        query = query.filter(models.Donation.year == year)
    if funding_type:
        query = query.filter(models.Donation.funding_type == funding_type)
    if search:
        query = query.filter(
            or_(
                models.Donor.name.ilike(f"%{search}%"),
                models.Party.name.ilike(f"%{search}%"),
                models.Party.id.ilike(f"%{search}%")
            )
        )
    
    # Order by amount descending as default
    query = query.order_by(desc(models.Donation.amount))
    
    # Clone query for count
    total_count = query.order_by(None).with_entities(func.count(models.Donation.id)).scalar()
    
    # Get paginated results
    results = query.offset(offset).limit(limit).all()
    
    formatted_results = []
    for item in results:
        donation = item[0]
        formatted_results.append({
            "id": donation.id,
            "party_id": donation.party_id,
            "party_name": item.party_name,
            "donor_id": donation.donor_id,
            "donor_name": item.donor_name,
            "donor_industry": item.donor_industry,
            "amount": donation.amount,
            "date": donation.date,
            "year": donation.year,
            "funding_type": donation.funding_type,
            "source_name": donation.source_name,
            "source_url": donation.source_url,
            "created_at": donation.created_at
        })
        
    return formatted_results, total_count

# --- Candidates ---
def get_candidates(
    db: Session,
    state: str = None,
    party_id: str = None,
    search: str = None,
    sort_by: str = None, # "assets", "criminal_cases"
    limit: int = 100,
    offset: int = 0,
    house: str = None,
    election: str = None,
    winners_only: bool = False,
):
    query = db.query(
        models.Candidate,
        models.Party.name.label("party_name")
    ).join(models.Party, models.Candidate.party_id == models.Party.id)

    if house:
        query = query.filter(models.Candidate.house == house)
    if election:
        query = query.filter(models.Candidate.election == election)
    if winners_only:
        query = query.filter(models.Candidate.is_winner.is_(True))

    if state:
        query = query.filter(models.Candidate.state.ilike(state))
    if party_id:
        query = query.filter(models.Candidate.party_id == party_id)
    if search:
        query = query.filter(
            or_(
                models.Candidate.name.ilike(f"%{search}%"),
                models.Candidate.constituency.ilike(f"%{search}%")
            )
        )
        
    if sort_by == "assets":
        query = query.order_by(desc(models.Candidate.assets))
    elif sort_by == "criminal_cases":
        query = query.order_by(desc(models.Candidate.criminal_cases))
    else:
        query = query.order_by(desc(models.Candidate.year), models.Candidate.name)
        
    total_count = query.order_by(None).with_entities(func.count(models.Candidate.id)).scalar()
    results = query.offset(offset).limit(limit).all()
    
    formatted_results = []
    for candidate, party_name in results:
        formatted_results.append({
            "id": candidate.id,
            "name": candidate.name,
            "party_id": candidate.party_id,
            "party_name": party_name,
            "state": candidate.state,
            "constituency": candidate.constituency,
            "year": candidate.year,
            "election": candidate.election,
            "house": candidate.house,
            "is_winner": candidate.is_winner,
            "assets": candidate.assets,
            "liabilities": candidate.liabilities,
            "criminal_cases": candidate.criminal_cases,
            "education": candidate.education,
            "source_name": candidate.source_name,
            "source_url": candidate.source_url,
            "created_at": candidate.created_at
        })
        
    return formatted_results, total_count

# --- Aggregate Dashboard Stats ---
def get_dashboard_stats(db: Session, year: int = None):
    # Total stats
    donations_query = db.query(models.Donation)
    if year:
        donations_query = donations_query.filter(models.Donation.year == year)
        
    total_funding = donations_query.with_entities(func.coalesce(func.sum(models.Donation.amount), 0.0)).scalar()
    total_donations_count = donations_query.order_by(None).with_entities(func.count(models.Donation.id)).scalar()
    
    donors_query = db.query(models.Donation.donor_id).distinct()
    if year:
        donors_query = donors_query.filter(models.Donation.year == year)
    total_donors_count = donors_query.count()
    
    total_candidates_count = db.query(models.Candidate).filter(models.Candidate.house == "Lok Sabha").count()
    
    # Party Shares
    party_shares_query = db.query(
        models.Donation.party_id,
        models.Party.name,
        func.sum(models.Donation.amount).label("amount")
    ).join(models.Party, models.Donation.party_id == models.Party.id)
    if year:
        party_shares_query = party_shares_query.filter(models.Donation.year == year)
    party_shares_raw = party_shares_query.group_by(models.Donation.party_id, models.Party.name).order_by(desc("amount")).all()
    
    party_shares = []
    for pid, pname, amt in party_shares_raw:
        party_shares.append({
            "party_id": pid,
            "party_name": pname,
            "amount": amt,
            "percentage": (amt / total_funding * 100) if total_funding > 0 else 0.0
        })
        
    # Sector/Industry Shares
    sector_shares_query = db.query(
        models.Donor.industry.label("sector"),
        func.sum(models.Donation.amount).label("amount")
    ).join(models.Donation, models.Donor.id == models.Donation.donor_id)
    if year:
        sector_shares_query = sector_shares_query.filter(models.Donation.year == year)
    sector_shares_raw = sector_shares_query.group_by(models.Donor.industry).order_by(desc("amount")).all()
    
    sector_shares = []
    for sector, amt in sector_shares_raw:
        sector_shares.append({
            "sector": sector or "Unknown",
            "amount": amt,
            "percentage": (amt / total_funding * 100) if total_funding > 0 else 0.0
        })
        
    # Yearly Trends
    yearly_trends_raw = db.query(
        models.Donation.year,
        func.sum(models.Donation.amount).label("amount"),
        func.count(models.Donation.id).label("count")
    ).group_by(models.Donation.year).order_by(models.Donation.year).all()
    
    yearly_trends = []
    for yr, amt, cnt in yearly_trends_raw:
        yearly_trends.append({
            "year": yr,
            "total_amount": amt,
            "donation_count": cnt
        })
        
    # Top Donors
    top_donors_query = db.query(
        models.Donor,
        func.sum(models.Donation.amount).label("total_donated"),
        func.count(models.Donation.id).label("donation_count")
    ).join(models.Donation, models.Donor.id == models.Donation.donor_id)
    if year:
        top_donors_query = top_donors_query.filter(models.Donation.year == year)
    top_donors_raw = top_donors_query.group_by(models.Donor.id).order_by(desc("total_donated")).limit(10).all()
    
    top_donors = []
    for donor, total, count in top_donors_raw:
        top_donors.append({
            "id": donor.id,
            "name": donor.name,
            "industry": donor.industry,
            "total_donated": total,
            "donation_count": count
        })
        
    return {
        "total_funding": total_funding,
        "total_donations_count": total_donations_count,
        "total_donors_count": total_donors_count,
        "total_candidates_count": total_candidates_count,
        "party_shares": party_shares,
        "sector_shares": sector_shares,
        "yearly_trends": yearly_trends,
        "top_donors": top_donors
    }

# --- NGO & Foreign Funding Tracker Queries ---

def get_ngos(db: Session, status: str = None, state: str = None, sector: str = None, search: str = None, limit: int = 100, offset: int = 0):
    # Base query for aggregation
    query = db.query(
        models.NGO,
        func.coalesce(func.sum(models.NGODonation.amount), 0.0).label("total_foreign_funding"),
        func.count(models.NGODonation.id).label("donation_count")
    ).outerjoin(models.NGODonation, models.NGO.id == models.NGODonation.ngo_id)

    if status:
        query = query.filter(models.NGO.registration_status == status)
    if state:
        query = query.filter(models.NGO.state.ilike(state))
    if sector:
        query = query.filter(models.NGO.sector == sector)
    if search:
        query = query.filter(
            or_(
                models.NGO.name.ilike(f"%{search}%"),
                models.NGO.fcra_registration_number.ilike(f"%{search}%")
            )
        )

    # Count matching NGOs before paging
    count_query = db.query(models.NGO)
    if status:
        count_query = count_query.filter(models.NGO.registration_status == status)
    if state:
        count_query = count_query.filter(models.NGO.state.ilike(state))
    if sector:
        count_query = count_query.filter(models.NGO.sector == sector)
    if search:
        count_query = count_query.filter(
            or_(
                models.NGO.name.ilike(f"%{search}%"),
                models.NGO.fcra_registration_number.ilike(f"%{search}%")
            )
        )
    total_count = count_query.count()

    results = query.group_by(models.NGO.id).order_by(desc("total_foreign_funding")).offset(offset).limit(limit).all()

    formatted = []
    for ngo, total, count in results:
        formatted.append({
            "id": ngo.id,
            "name": ngo.name,
            "fcra_registration_number": ngo.fcra_registration_number,
            "state": ngo.state,
            "sector": ngo.sector,
            "registration_status": ngo.registration_status,
            "data_as_of": ngo.data_as_of,
            "created_at": ngo.created_at,
            "total_foreign_funding": total,
            "donation_count": count
        })

    return formatted, total_count

def get_ngo_by_id(db: Session, ngo_id: int):
    return db.query(models.NGO).filter(models.NGO.id == ngo_id).first()

def get_ngo_donations(db: Session, ngo_id: int = None, year: int = None, search: str = None, limit: int = 100, offset: int = 0):
    query = db.query(
        models.NGODonation,
        models.NGO.name.label("ngo_name"),
        models.NGO.fcra_registration_number.label("fcra_registration_number"),
        models.NGO.state.label("ngo_state"),
        models.NGO.sector.label("ngo_sector"),
        models.NGO.registration_status.label("ngo_registration_status")
    ).join(models.NGO, models.NGODonation.ngo_id == models.NGO.id)

    if ngo_id:
        query = query.filter(models.NGODonation.ngo_id == ngo_id)
    if year:
        query = query.filter(models.NGODonation.year == year)
    if search:
        query = query.filter(
            or_(
                models.NGO.name.ilike(f"%{search}%"),
                models.NGO.fcra_registration_number.ilike(f"%{search}%")
            )
        )

    # Order by amount descending
    query = query.order_by(desc(models.NGODonation.amount))
    
    total_count = query.order_by(None).with_entities(func.count(models.NGODonation.id)).scalar()
    results = query.offset(offset).limit(limit).all()

    formatted = []
    for item in results:
        don = item[0]
        formatted.append({
            "id": don.id,
            "ngo_id": don.ngo_id,
            "ngo_name": item.ngo_name,
            "fcra_registration_number": item.fcra_registration_number,
            "ngo_state": item.ngo_state,
            "ngo_sector": item.ngo_sector,
            "ngo_registration_status": item.ngo_registration_status,
            "amount": don.amount,
            "year": don.year,
            "source_name": don.source_name,
            "source_url": don.source_url,
            "created_at": don.created_at
        })
    return formatted, total_count

def get_ngo_stats(db: Session):
    total_funding = db.query(func.coalesce(func.sum(models.NGODonation.amount), 0.0)).scalar()
    total_ngos_count = db.query(models.NGO).count()
    total_donations_count = db.query(models.NGODonation).count()
    
    active_ngos_count = db.query(models.NGO).filter(models.NGO.registration_status == "Active").count()
    suspended_ngos_count = db.query(models.NGO).filter(models.NGO.registration_status == "Suspended").count()
    cancelled_ngos_count = db.query(models.NGO).filter(models.NGO.registration_status == "Cancelled").count()

    # Sector shares
    sector_shares_raw = db.query(
        models.NGO.sector,
        func.sum(models.NGODonation.amount).label("amount")
    ).join(models.NGODonation, models.NGO.id == models.NGODonation.ngo_id)\
     .group_by(models.NGO.sector).order_by(desc("amount")).all()

    sector_shares = []
    for sector, amt in sector_shares_raw:
        sector_shares.append({
            "sector": sector,
            "amount": amt,
            "percentage": (amt / total_funding * 100) if total_funding > 0 else 0.0
        })

    # Top NGOs by foreign funding
    top_ngos_raw = db.query(
        models.NGO.id,
        models.NGO.name,
        models.NGO.fcra_registration_number,
        models.NGO.state,
        models.NGO.sector,
        func.sum(models.NGODonation.amount).label("total_funding")
    ).join(models.NGODonation, models.NGO.id == models.NGODonation.ngo_id)\
     .group_by(models.NGO.id).order_by(desc("total_funding")).limit(5).all()

    top_ngos = []
    for ngo_id, name, fcra, state, sector, total in top_ngos_raw:
        top_ngos.append({
            "ngo_id": ngo_id,
            "ngo_name": name,
            "fcra_registration_number": fcra,
            "state": state,
            "sector": sector,
            "total_funding": total
        })

    # Yearly trends
    yearly_trends_raw = db.query(
        models.NGODonation.year,
        func.sum(models.NGODonation.amount).label("amount"),
        func.count(models.NGODonation.id).label("count")
    ).group_by(models.NGODonation.year).order_by(models.NGODonation.year).all()

    yearly_trends = []
    for yr, amt, cnt in yearly_trends_raw:
        yearly_trends.append({
            "year": yr,
            "total_amount": amt,
            "donation_count": cnt
        })

    # Flagged Year-over-Year Spikes
    # Compute annual totals per NGO
    yearly_totals = db.query(
        models.NGODonation.ngo_id,
        models.NGO.name.label("ngo_name"),
        models.NGO.fcra_registration_number.label("fcra_registration_number"),
        models.NGO.state.label("state"),
        models.NGODonation.year,
        func.sum(models.NGODonation.amount).label("amount")
    ).join(models.NGO, models.NGODonation.ngo_id == models.NGO.id)\
     .group_by(models.NGODonation.ngo_id, models.NGO.name, models.NGO.fcra_registration_number,
               models.NGO.state, models.NGODonation.year).all()

    # Map to {ngo_id: {year: amount}}
    ngo_history = {}
    ngo_details = {}
    for ngo_id, name, fcra, state, yr, amt in yearly_totals:
        if ngo_id not in ngo_history:
            ngo_history[ngo_id] = {}
            ngo_details[ngo_id] = {"name": name, "fcra": fcra, "state": state}
        ngo_history[ngo_id][yr] = amt

    flagged_spikes = []
    for ngo_id, years_dict in ngo_history.items():
        sorted_years = sorted(years_dict.keys())
        for i in range(1, len(sorted_years)):
            prev_yr = sorted_years[i-1]
            curr_yr = sorted_years[i]
            
            # Check for sequential year gap of 1
            if curr_yr == prev_yr + 1:
                prev_amt = years_dict[prev_yr]
                curr_amt = years_dict[curr_yr]
                
                # Flag if current year has doubled and the absolute increase is significant (> ₹25 Lakhs).
                # A ₹1 Lakh floor on the base year keeps near-zero bases from producing meaningless percentages.
                if prev_amt >= 100000:
                    diff = curr_amt - prev_amt
                    pct = (diff / prev_amt) * 100
                    if pct >= 100.0 and diff >= 2500000.0:
                        flagged_spikes.append({
                            "ngo_id": ngo_id,
                            "ngo_name": ngo_details[ngo_id]["name"],
                            "fcra_registration_number": ngo_details[ngo_id]["fcra"],
                            "state": ngo_details[ngo_id]["state"],
                            "previous_amount": prev_amt,
                            "current_amount": curr_amt,
                            "year": curr_yr,
                            "percentage_increase": pct
                        })

    # Largest absolute increases first; percentages from small bases are not meaningful rankings
    flagged_spikes.sort(key=lambda x: x["current_amount"] - x["previous_amount"], reverse=True)
    flagged_spikes = flagged_spikes[:100]

    return {
        "total_funding": total_funding,
        "total_ngos_count": total_ngos_count,
        "total_donations_count": total_donations_count,
        "active_ngos_count": active_ngos_count,
        "suspended_ngos_count": suspended_ngos_count,
        "cancelled_ngos_count": cancelled_ngos_count,
        "sector_shares": sector_shares,
        "top_ngos": top_ngos,
        "yearly_trends": yearly_trends,
        "flagged_spikes": flagged_spikes
    }


# --- Legislative Activity & Attendance Monitor ---
def get_mp_activity(
    db: Session,
    state: str = None,
    party_name: str = None,
    search: str = None,
    outlier: str = None,
    sort_by: str = None,
    limit: int = 100,
    offset: int = 0
):
    query = db.query(models.MPActivity)

    if state:
        query = query.filter(models.MPActivity.state_represented.ilike(state))
    if party_name:
        query = query.filter(models.MPActivity.party_name.ilike(party_name))
    if search:
        query = query.filter(
            models.MPActivity.mp_name.ilike(f"%{search}%") |
            models.MPActivity.constituency.ilike(f"%{search}%") |
            models.MPActivity.party_name.ilike(f"%{search}%")
        )

    if outlier == "low_attendance":
        query = query.filter(models.MPActivity.attendance_pct < 50.0)
    elif outlier == "top_debates":
        query = query.order_by(desc(models.MPActivity.debates_count), models.MPActivity.mp_name)
    elif outlier == "top_questions":
        query = query.order_by(desc(models.MPActivity.questions_count), models.MPActivity.mp_name)

    if sort_by == "attendance":
        query = query.order_by(desc(models.MPActivity.attendance_pct), models.MPActivity.mp_name)
    elif sort_by == "debates":
        query = query.order_by(desc(models.MPActivity.debates_count), models.MPActivity.mp_name)
    elif sort_by == "questions":
        query = query.order_by(desc(models.MPActivity.questions_count), models.MPActivity.mp_name)
    elif sort_by == "bills":
        query = query.order_by(desc(models.MPActivity.bills_introduced), models.MPActivity.mp_name)
    elif not outlier:
        # Default order
        query = query.order_by(desc(models.MPActivity.attendance_pct), models.MPActivity.mp_name)

    total_count = query.order_by(None).with_entities(func.count(models.MPActivity.id)).scalar()
    results = query.offset(offset).limit(limit).all()

    formatted = []
    for mp in results:
        formatted.append({
            "id": mp.id,
            "mp_name": mp.mp_name,
            "party_name": mp.party_name,
            "state_represented": mp.state_represented,
            "constituency": mp.constituency,
            "attendance_pct": mp.attendance_pct,
            "debates_count": mp.debates_count,
            "questions_count": mp.questions_count,
            "bills_introduced": mp.bills_introduced,
            "official_url": mp.official_url,
            "created_at": mp.created_at
        })
    return formatted, total_count

def get_mp_activity_stats(db: Session):
    total_mps = db.query(models.MPActivity).count()
    if total_mps == 0:
        return {
            "national_average_attendance": 0.0,
            "total_debates": 0,
            "total_questions": 0,
            "total_bills": 0,
            "total_mps": 0,
            "low_attendance_outliers": [],
            "top_debates_outliers": [],
            "top_questions_outliers": []
        }

    # Aggregate metric calculations
    avg_attendance = db.query(func.avg(models.MPActivity.attendance_pct)).scalar() or 0.0
    total_debates = db.query(func.sum(models.MPActivity.debates_count)).scalar() or 0
    total_questions = db.query(func.sum(models.MPActivity.questions_count)).scalar() or 0
    total_bills = db.query(func.sum(models.MPActivity.bills_introduced)).scalar() or 0

    # Low attendance outliers (<50%)
    low_attendance_query = db.query(
        models.MPActivity\
    ).filter(models.MPActivity.attendance_pct < 50.0)\
     .order_by(models.MPActivity.attendance_pct)\
     .all()

    low_attendance = []
    for mp in low_attendance_query:
        low_attendance.append({
            "id": mp.id,
            "mp_name": mp.mp_name,
            "party_name": mp.party_name,
            "state_represented": mp.state_represented,
            "constituency": mp.constituency,
            "attendance_pct": mp.attendance_pct,
            "debates_count": mp.debates_count,
            "questions_count": mp.questions_count,
            "bills_introduced": mp.bills_introduced,
            "official_url": mp.official_url,
            "created_at": mp.created_at
        })

    # Top debaters (top 5)
    top_debates_query = db.query(
        models.MPActivity
    ).order_by(desc(models.MPActivity.debates_count), models.MPActivity.mp_name)\
     .limit(5)\
     .all()

    top_debates = []
    for mp in top_debates_query:
        top_debates.append({
            "id": mp.id,
            "mp_name": mp.mp_name,
            "party_name": mp.party_name,
            "state_represented": mp.state_represented,
            "constituency": mp.constituency,
            "attendance_pct": mp.attendance_pct,
            "debates_count": mp.debates_count,
            "questions_count": mp.questions_count,
            "bills_introduced": mp.bills_introduced,
            "official_url": mp.official_url,
            "created_at": mp.created_at
        })

    # Top interrogators (top 5 questions asked)
    top_questions_query = db.query(
        models.MPActivity
    ).order_by(desc(models.MPActivity.questions_count), models.MPActivity.mp_name)\
     .limit(5)\
     .all()

    top_questions = []
    for mp in top_questions_query:
        top_questions.append({
            "id": mp.id,
            "mp_name": mp.mp_name,
            "party_name": mp.party_name,
            "state_represented": mp.state_represented,
            "constituency": mp.constituency,
            "attendance_pct": mp.attendance_pct,
            "debates_count": mp.debates_count,
            "questions_count": mp.questions_count,
            "bills_introduced": mp.bills_introduced,
            "official_url": mp.official_url,
            "created_at": mp.created_at
        })

    return {
        "national_average_attendance": float(avg_attendance),
        "total_debates": int(total_debates),
        "total_questions": int(total_questions),
        "total_bills": int(total_bills),
        "total_mps": total_mps,
        "low_attendance_outliers": low_attendance,
        "top_debates_outliers": top_debates,
        "top_questions_outliers": top_questions
    }


def get_legislators(
    db: Session,
    state: str = None,
    party_id: str = None,
    search: str = None,
    outlier: str = None,
    sort_by: str = None,
    limit: int = 100,
    offset: int = 0
):
    # Legacy compatibility wrapper around the MPActivity bulk import.
    party_name = party_id
    results, total_count = get_mp_activity(
        db,
        state=state,
        party_name=party_name,
        search=search,
        outlier=outlier,
        sort_by=sort_by,
        limit=limit,
        offset=offset,
    )

    legacy_results = []
    for item in results:
        legacy_results.append({
            "id": item["id"],
            "name": item["mp_name"],
            "party_id": item["party_name"],
            "party_name": item["party_name"],
            "state": item["state_represented"],
            "constituency": item["constituency"],
            "attendance_pct": item["attendance_pct"],
            "debates_count": item["debates_count"],
            "questions_count": item["questions_count"],
            "bills_introduced": item["bills_introduced"],
            "session_year": 2024,
            "source_name": "Vonter / India Representatives Activity",
            "source_url": item["official_url"],
            "created_at": item["created_at"],
        })

    return legacy_results, total_count


def get_legislator_stats(db: Session):
    stats = get_mp_activity_stats(db)
    return {
        "national_average_attendance": stats["national_average_attendance"],
        "total_debates": stats["total_debates"],
        "total_questions": stats["total_questions"],
        "total_bills": stats["total_bills"],
        "total_legislators_count": stats["total_mps"],
        "low_attendance_outliers": [
            {
                "id": item["id"],
                "name": item["mp_name"],
                "party_id": item["party_name"],
                "party_name": item["party_name"],
                "state": item["state_represented"],
                "constituency": item["constituency"],
                "attendance_pct": item["attendance_pct"],
                "debates_count": item["debates_count"],
                "questions_count": item["questions_count"],
                "bills_introduced": item["bills_introduced"],
                "session_year": 2024,
                "source_name": "Vonter / India Representatives Activity",
                "source_url": item["official_url"],
                "created_at": item["created_at"],
            }
            for item in stats["low_attendance_outliers"]
        ],
        "top_debates_outliers": [
            {
                "id": item["id"],
                "name": item["mp_name"],
                "party_id": item["party_name"],
                "party_name": item["party_name"],
                "state": item["state_represented"],
                "constituency": item["constituency"],
                "attendance_pct": item["attendance_pct"],
                "debates_count": item["debates_count"],
                "questions_count": item["questions_count"],
                "bills_introduced": item["bills_introduced"],
                "session_year": 2024,
                "source_name": "Vonter / India Representatives Activity",
                "source_url": item["official_url"],
                "created_at": item["created_at"],
            }
            for item in stats["top_debates_outliers"]
        ],
        "top_questions_outliers": [
            {
                "id": item["id"],
                "name": item["mp_name"],
                "party_id": item["party_name"],
                "party_name": item["party_name"],
                "state": item["state_represented"],
                "constituency": item["constituency"],
                "attendance_pct": item["attendance_pct"],
                "debates_count": item["debates_count"],
                "questions_count": item["questions_count"],
                "bills_introduced": item["bills_introduced"],
                "session_year": 2024,
                "source_name": "Vonter / India Representatives Activity",
                "source_url": item["official_url"],
                "created_at": item["created_at"],
            }
            for item in stats["top_questions_outliers"]
        ],
    }


def get_legislative_bills(db: Session, status: str = None, limit: int = 100):
    query = db.query(models.LegislativeBill)

    if status:
        query = query.filter(models.LegislativeBill.current_status.ilike(status))

    total_count = query.order_by(None).with_entities(func.count(models.LegislativeBill.id)).scalar()
    results = query.order_by(desc(models.LegislativeBill.created_at), desc(models.LegislativeBill.id)).limit(limit).all()

    formatted = []
    for bill in results:
        formatted.append({
            "id": bill.id,
            "bill_title": bill.bill_title,
            "ministry": bill.ministry,
            "current_status": bill.current_status,
            "state_represented": bill.state_represented,
            "introduced_by": bill.introduced_by,
            "introduced_on": bill.introduced_on,
            "official_url": bill.official_url,
            "created_at": bill.created_at,
        })

    return formatted, total_count


def get_legislative_state_dossier(db: Session, state_name: str):
    mp_rows = db.query(models.MPActivity).filter(models.MPActivity.state_represented.ilike(state_name))
    mp_rows = mp_rows.order_by(desc(models.MPActivity.attendance_pct), models.MPActivity.mp_name).all()

    bill_rows = db.query(models.LegislativeBill).filter(models.LegislativeBill.state_represented.ilike(state_name))
    bill_rows = bill_rows.order_by(desc(models.LegislativeBill.created_at), desc(models.LegislativeBill.id)).all()

    mps = []
    for mp in mp_rows:
        mps.append({
            "id": mp.id,
            "mp_name": mp.mp_name,
            "constituency": mp.constituency,
            "party_name": mp.party_name,
            "state_represented": mp.state_represented,
            "attendance_pct": mp.attendance_pct,
            "debates_count": mp.debates_count,
            "questions_count": mp.questions_count,
            "bills_introduced": mp.bills_introduced,
            "official_url": mp.official_url,
            "created_at": mp.created_at,
        })

    bills = []
    for bill in bill_rows:
        bills.append({
            "id": bill.id,
            "bill_title": bill.bill_title,
            "ministry": bill.ministry,
            "current_status": bill.current_status,
            "state_represented": bill.state_represented,
            "introduced_by": bill.introduced_by,
            "introduced_on": bill.introduced_on,
            "official_url": bill.official_url,
            "created_at": bill.created_at,
        })

    return {
        "state": state_name,
        "mps": mps,
        "bills": bills,
        "total_mps": len(mps),
        "total_bills": len(bills),
    }



