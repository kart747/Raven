from pydantic import BaseModel, ConfigDict
from typing import List, Optional
from datetime import datetime

# --- Party ---
class PartyBase(BaseModel):
    id: str
    name: str
    symbol_url: Optional[str] = None

class PartyCreate(PartyBase):
    pass

class PartyResponse(PartyBase):
    model_config = ConfigDict(from_attributes=True)

class PartyStatsResponse(PartyBase):
    total_donations: float
    donation_count: int
    model_config = ConfigDict(from_attributes=True)


# --- Donor ---
class DonorBase(BaseModel):
    name: str
    industry: Optional[str] = "Unknown"

class DonorCreate(DonorBase):
    pass

class DonorResponse(DonorBase):
    id: int
    model_config = ConfigDict(from_attributes=True)

class DonorStatsResponse(DonorResponse):
    total_donated: float
    donation_count: int
    model_config = ConfigDict(from_attributes=True)


# --- Donation ---
class DonationBase(BaseModel):
    party_id: str
    amount: float
    date: Optional[str] = None
    year: int
    funding_type: str
    source_name: str
    source_url: str

class DonationCreate(DonationBase):
    donor_name: str
    donor_industry: Optional[str] = "Unknown"

class DonationResponse(DonationBase):
    id: int
    donor_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class DonationDetailResponse(DonationResponse):
    party_name: str
    donor_name: str
    donor_industry: str
    model_config = ConfigDict(from_attributes=True)


# --- Candidate ---
class CandidateBase(BaseModel):
    name: str
    party_id: str
    state: str
    constituency: str
    year: int
    assets: float
    liabilities: float
    criminal_cases: int
    education: str
    source_name: str
    source_url: str

class CandidateCreate(CandidateBase):
    pass

class CandidateResponse(CandidateBase):
    id: int
    created_at: datetime
    party_name: str
    model_config = ConfigDict(from_attributes=True)


# --- Aggregate Stats ---
class YearlyStats(BaseModel):
    year: int
    total_amount: float
    donation_count: int

class PartyShare(BaseModel):
    party_id: str
    party_name: str
    amount: float
    percentage: float

class SectorShare(BaseModel):
    sector: str
    amount: float
    percentage: float

class DashboardStats(BaseModel):
    total_funding: float
    total_donations_count: int
    total_donors_count: int
    total_candidates_count: int
    party_shares: List[PartyShare]
    sector_shares: List[SectorShare]
    yearly_trends: List[YearlyStats]
    top_donors: List[DonorStatsResponse]


# --- NGO & Foreign Funding Tracker ---
class NGODonationResponse(BaseModel):
    id: int
    ngo_id: int
    amount: float
    year: int
    source_name: str
    source_url: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class NGOResponse(BaseModel):
    id: int
    name: str
    fcra_registration_number: str
    state: str
    sector: str
    registration_status: str
    data_as_of: Optional[str] = None
    created_at: datetime
    total_foreign_funding: float
    donation_count: int
    model_config = ConfigDict(from_attributes=True)

class NGODetailResponse(BaseModel):
    id: int
    name: str
    fcra_registration_number: str
    state: str
    sector: str
    registration_status: str
    data_as_of: Optional[str] = None
    created_at: datetime
    donations: List[NGODonationResponse]
    model_config = ConfigDict(from_attributes=True)

class NGOSpike(BaseModel):
    ngo_id: int
    ngo_name: str
    fcra_registration_number: str
    state: str
    previous_amount: float
    current_amount: float
    year: int
    percentage_increase: float

class NGOTopShare(BaseModel):
    ngo_id: int
    ngo_name: str
    fcra_registration_number: str
    state: str
    sector: str
    total_funding: float

class NGOStats(BaseModel):
    total_funding: float
    total_ngos_count: int
    total_donations_count: int
    active_ngos_count: int
    suspended_ngos_count: int
    cancelled_ngos_count: int
    sector_shares: List[SectorShare]
    top_ngos: List[NGOTopShare]
    yearly_trends: List[YearlyStats]
    flagged_spikes: List[NGOSpike]


# --- Legislative Activity & Attendance Monitor ---
class LegislatorResponse(BaseModel):
    id: int
    name: str
    party_id: str
    party_name: str
    state: str
    constituency: str
    attendance_pct: float
    debates_count: int
    questions_count: int
    bills_introduced: int
    session_year: int
    source_name: str
    source_url: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)

class LegislatorStats(BaseModel):
    national_average_attendance: float
    total_debates: int
    total_questions: int
    total_bills: int
    total_legislators_count: int
    low_attendance_outliers: List[LegislatorResponse]
    top_debates_outliers: List[LegislatorResponse]
    top_questions_outliers: List[LegislatorResponse]


class MPActivityResponse(BaseModel):
    id: int
    mp_name: str
    constituency: str
    party_name: str
    state_represented: str
    attendance_pct: Optional[float] = None
    debates_count: int
    questions_count: int
    bills_introduced: int
    official_url: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class MPActivityListResponse(BaseModel):
    data: List[MPActivityResponse]
    total: int
    limit: int
    offset: int


class MPActivityStats(BaseModel):
    national_average_attendance: float
    total_debates: int
    total_questions: int
    total_bills: int
    total_mps: int
    low_attendance_outliers: List[MPActivityResponse]
    top_debates_outliers: List[MPActivityResponse]
    top_questions_outliers: List[MPActivityResponse]


class LegislativeBillResponse(BaseModel):
    id: int
    bill_title: str
    ministry: str
    current_status: str
    state_represented: str
    introduced_by: str
    introduced_on: Optional[str] = None
    official_url: str
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class LegislativeBillListResponse(BaseModel):
    data: List[LegislativeBillResponse]
    total: int
    limit: int


class LegislativeStateDossierResponse(BaseModel):
    state: str
    mps: List[MPActivityResponse]
    bills: List[LegislativeBillResponse]
    total_mps: int
    total_bills: int


# --- PIB RSS Releases ---
class SourceCitation(BaseModel):
    source_name: str
    source_url: str
    last_updated: datetime

class PIBReleaseResponse(BaseModel):
    id: int
    mod_id: int
    regid: int
    title: str
    ministry_tag: Optional[str] = None
    published_at: Optional[datetime] = None
    created_at: datetime
    source_citation: SourceCitation
    model_config = ConfigDict(from_attributes=True)


class PIBReleaseListResponse(BaseModel):
    data: List[PIBReleaseResponse]
    total: int
    limit: int
    offset: int


class PIBSyncResponse(BaseModel):
    feeds_polled: int
    releases_added_or_updated: int


