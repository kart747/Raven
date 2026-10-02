# Raven

OSINT dashboard for Indian political funding, NGO foreign contributions, and parliamentary activity.
Every figure comes from a public source dataset; nothing is generated or estimated.

## Data sources

| Dataset | Source | Location |
|---|---|---|
| Electoral bonds (bond-number matched) | SBI disclosure to ECI, 21 Mar 2024 | `git clone https://github.com/cvrajeesh/electoral-bonds cvrajeesh_repo` |
| FCRA foreign contributions FY2016-17 → FY2020-21 | MHA FCRA annual returns | `git clone https://github.com/mkonchady/fcra fcra_repo` |
| Lok Sabha MP activity & private member bills | Vonter/india-representatives-activity | fetched on import |
| Lok Sabha 2024 candidate affidavits | MyNeta (ADR) | scraped on import (rate-limited, cached in `backend/data_cache/`) |
| Press releases | PIB RSS (English) | fetched live |
| Optional sourced inputs: FCRA status, purchaser industry, purchaser events | see [data/README.md](data/README.md) | `data/*.csv` |

## Setup

```bash
# Backend
cd backend
python -m venv venv && venv/bin/pip install -r requirements.txt
cp .env.example .env           # add GROQ_API_KEY for the AI brief, ADMIN_API_KEY for admin endpoints
venv/bin/python -m app.cli ingest-all
venv/bin/python run.py         # http://127.0.0.1:8000/docs

# Frontend
cd frontend
npm install
cp .env.example .env           # VITE_API_URL
npm run dev                    # http://localhost:5173
```

Individual imports: `python -m app.cli {seed|ingest-bonds|ingest-fcra|ingest-candidates|ingest-legislative|ingest-events|brief}`.
Official FCRA status list: `python -m app.cli ingest-fcra-status list.xlsx --status Cancelled --source-url URL`.

### Docker (Postgres)

```bash
cp backend/.env.example backend/.env
docker compose up -d --build
docker compose run --rm ingest     # first data load
# UI http://localhost:8080 · API http://localhost:8000/docs
```

The API re-imports Lok Sabha activity weekly (`ENABLE_SCHEDULED_INGEST=1`) and regenerates the AI brief weekly.

Tests: `cd backend && venv/bin/python -m pytest`.

## Data caveats

- About 10% of encashed bonds (≈₹870 Cr) were bought before 12 Apr 2019 and have no purchaser in the disclosure; they appear as `UNKNOWN DONOR`.
- SBI printed purchaser names inconsistently; spellings are merged conservatively (spacing, punctuation, &/AND, legal suffix, truncated names) and every raw spelling is kept in `donor_aliases`. Individuals and their HUFs are never merged.
- Electoral bond data has no state field, so state views show national party totals.
- Candidate figures are self-declared in affidavits; "criminal cases" are pending cases declared, not convictions.
- NGO sector is inferred from the organisation name; registration status is "Unverified" unless loaded from official lists.
- Fiscal years use the April–March start year (FY2019 = Apr 2019 – Mar 2020) throughout.
