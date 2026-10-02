# Local data files

Optional, hand-curated inputs. Every row must cite a source URL; rows without one are rejected.
`*.csv` here is git-ignored so unpublished research stays local.

| File | Columns | Loaded by |
|---|---|---|
| `fcra_status_overrides.csv` | `fcra_registration_number,status,source_url` (status: Active / Suspended / Cancelled) | `python -m app.cli ingest-fcra-status FILE --status S --source-url URL` writes it; `ingest-fcra` re-applies it |
| `donor_industry.csv` | `donor_name,industry,source_url` | `python -m app.cli ingest-bonds` |
| `entity_events.csv` | `entity_name,event_date,event_type,description,source_name,source_url` | `python -m app.cli ingest-events` (also re-linked after every bond import) |

Names in `donor_industry.csv` and `entity_events.csv` can be any spelling of a bond purchaser;
they are matched with the same rules that merge SBI's spelling variants (`backend/app/entities.py`).

Suggested sources:
- FCRA status: fcraonline.nic.in → "Cancelled / suspended associations" lists (the portal may only be reachable from India).
- Industry: the company's MCA master data ("Principal business activity") or annual report.
- Events: court orders, agency press releases, CPPP / GeM contract award notices, or reputable news reports.
  Showing an event next to bond dates is not evidence of a link between them; the UI says so.
