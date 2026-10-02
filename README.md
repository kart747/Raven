<div align="center">

# Raven

**Follow the money in Indian politics, from the public record.**

An open-source OSINT dashboard that joins electoral bonds, NGO foreign contributions,
candidate affidavits and parliamentary activity into one searchable, source-linked view.

![Python](https://img.shields.io/badge/python-3.13-blue)
![FastAPI](https://img.shields.io/badge/FastAPI-009688)
![React](https://img.shields.io/badge/React-18-61dafb)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL%20%7C%20SQLite-336791)

</div>

---

## Why Raven

Indian political and foreign-funding data is public but scattered across PDFs, government portals and
volunteer datasets, in inconsistent formats. Raven pulls it into one place, cleans it, and keeps a link
back to the original source on every record.

**One rule:** no figure is generated, estimated or guessed. If a value isn't in a source, Raven shows a gap
(for example *"Unverified"* or *"Purchaser not disclosed"*) instead of filling it in. The
[Sources & Data Quality](#data-quality-and-known-gaps) page reports coverage live.

## Features

| Area | What you get |
|---|---|
| **Electoral bonds** | All 20,384 encashed bonds (Apr 2019 – Feb 2024), joined to purchasers on the unique bond number. Search, filter by party, year or purchaser, export CSV. |
| **Purchaser profiles** | Each company's total, the parties it funded, monthly encashments, and every spelling SBI printed for the name. Optional sourced events (court orders, raids, contract awards) can be shown on the same timeline. |
| **Candidate affidavits** | Lok Sabha 2024 candidates from MyNeta: declared assets, liabilities, pending cases, education. Per-state totals drive the map. |
| **NGO foreign funding** | About 25,000 NGOs and 87,000 annual FCRA returns (FY2016-17 to FY2020-21), with sector breakdowns, flows and year-over-year increases. |
| **Parliament activity** | Attendance, debates, questions and private member bills for the 18th Lok Sabha, plus per-state views. |
| **State map** | Click a state to see its candidates, NGOs and MPs side by side. |
| **AI brief** | A short weekly summary. The model is given only the database figures and told to use nothing else, and the exact input is shown next to the text so you can check it. |
| **Data quality** | Live report of match rates, gaps and last-loaded times for every dataset. |

## Data sources

| Dataset | Source | How it is loaded |
|---|---|---|
| Electoral bonds | SBI disclosure to the Election Commission, 21 Mar 2024 ([cvrajeesh/electoral-bond-data](https://github.com/cvrajeesh/electoral-bond-data)) | Local clone |
| FCRA foreign contributions | MHA annual returns ([mkonchady/fcra](https://github.com/mkonchady/fcra)) | Local clone |
| Candidate affidavits | [MyNeta](https://myneta.info/LokSabha2024/) (ADR) | Scraped, rate-limited, cached |
| MP activity & bills | [Vonter/india-representatives-activity](https://github.com/Vonter/india-representatives-activity) | Downloaded on import |
| Press releases | PIB RSS (English national feed) | Live, cached 15 minutes |
| Optional: FCRA status, purchaser industry and events | Your own sourced CSVs, see [data/README.md](data/README.md) | `data/*.csv` |

Each source keeps its own licence. Raven stores derived records, not copies of the source repositories.

## Quick start

You need Python 3.13+, Node 20+, and git.

```bash
git clone https://github.com/kart747/Raven.git && cd Raven

# 1. Source datasets (not included in this repo)
git clone https://github.com/cvrajeesh/electoral-bond-data cvrajeesh_repo
git clone https://github.com/mkonchady/fcra fcra_repo

# 2. Backend
cd backend
python -m venv venv
venv/bin/pip install -r requirements.txt
cp .env.example .env                       # optional: add GROQ_API_KEY for the AI brief
venv/bin/python -m app.cli ingest-all      # loads everything (~15-20 min, mostly the MyNeta scrape)
venv/bin/python run.py                     # API on http://127.0.0.1:8000/docs

# 3. Frontend (new terminal)
cd frontend
npm install
cp .env.example .env
npm run dev                                # UI on http://localhost:5173
```

To load one dataset at a time:

```bash
python -m app.cli seed                # party reference list
python -m app.cli ingest-bonds        # electoral bonds
python -m app.cli ingest-fcra         # NGO foreign contributions
python -m app.cli ingest-candidates   # MyNeta affidavits (slow, ~460 pages, resumable)
python -m app.cli ingest-legislative  # Lok Sabha activity and bills
python -m app.cli ingest-events       # sourced purchaser events
python -m app.cli brief               # regenerate the AI brief
python -m app.cli ingest-fcra-status LIST.xlsx --status Cancelled --source-url URL
```

### Docker (Postgres)

```bash
cp backend/.env.example backend/.env
docker compose up -d --build
docker compose run --rm ingest         # first data load
```

UI at http://localhost:8080, API docs at http://localhost:8000/docs. Set `POSTGRES_PASSWORD` in your
environment before exposing this anywhere.

## Configuration

Set in `backend/.env` (see `.env.example`):

| Variable | Purpose |
|---|---|
| `GROQ_API_KEY` | Enables the weekly AI brief. Without it the brief is simply unavailable. |
| `GROQ_MODEL` | Model used for the brief (default `openai/gpt-oss-120b`). |
| `ADMIN_API_KEY` | Enables the admin import endpoint, sent as an `X-Admin-Key` header. Off when unset. |
| `ALLOWED_ORIGINS` | Comma-separated browser origins allowed to call the API. |
| `DATABASE_URL` | Postgres URL. Empty means a local SQLite file. |
| `ENABLE_SCHEDULED_INGEST` | `1` re-imports Lok Sabha activity weekly inside the API process. |

Frontend: `VITE_API_URL` points the UI at the API.

## How it works

```
 cvrajeesh_repo ─┐
 fcra_repo ──────┤                    ┌──────────────┐     ┌────────────────┐
 MyNeta (HTML) ──┼─► app/import_*.py ─►  SQLite or   ├─►   │ FastAPI        │ ─► React + Vite
 Vonter CSVs ────┤   (cleaning,       │  Postgres    │     │ /api/v1/...    │    (TanStack Query,
 data/*.csv ─────┘    matching)       └──────────────┘     └────────────────┘     Recharts, Leaflet)
```

- **Bond matching:** bonds are joined on prefix + serial number, which gives an exact purchaser-to-party link.
- **Name merging:** SBI printed purchaser names inconsistently (`VEDANTA LTD` / `VEDANTA LIMITED`, names cut at 35 characters). Spellings are merged only when they differ in spacing, punctuation, "&"/"AND", the legal suffix, or truncation. Individuals and their HUFs are never merged, and every raw spelling is kept.
- **Fiscal years** use the April–March start year everywhere (FY2019 = Apr 2019 – Mar 2020).
- **States** use one canonical list so filters, imports and the map agree.

Layout:

```
backend/app/        importers, API (main.py), queries (crud.py), entity resolution, CLI
backend/tests/      importer and parsing tests
frontend/src/       React app: components/, lib/queries.js (data hooks), api.js
data/               optional hand-curated, source-cited CSVs
docker-compose.yml  Postgres + API + web
```

## Data quality and known gaps

- About 10% of encashed bonds (≈ ₹870 Cr) were bought before 12 Apr 2019, and the disclosure names no purchaser for them. They show as *"Purchaser not disclosed"*.
- Bond data has no state field, so state views show national party totals.
- NGO **registration status** is not in the FCRA returns data. It shows *"Unverified"* until you load an official MHA list.
- NGO **sector** is inferred from the organisation's name with keyword rules and can be wrong for individual NGOs.
- Purchaser **industry** is empty until you add a sourced `data/donor_industry.csv`.
- Candidate figures are self-declared. **"Criminal cases" are pending cases declared in the affidavit, not convictions.**
- A date overlap between a bond and an event is **not** evidence of a connection, and the UI says so.

## Development

```bash
cd backend && venv/bin/python -m pytest      # importer and parsing tests
cd frontend && npm run build                 # production build
```

Contributions that add a **sourced** dataset are especially welcome: write an importer in
`backend/app/`, give every row a source URL, and add tests for the parsing. Please don't add placeholder or
estimated values for real people or organisations.

## Corrections

This site names real people and organisations. If you find an error, please open an issue with a link to the
official source showing the correct value, and it will be fixed promptly.

## Licence

No licence has been chosen yet. Until one is added (MIT is a common choice), the code is all rights reserved.
