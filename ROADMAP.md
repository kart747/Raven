# Raven roadmap

**Goal:** the open, source-linked map of money and power in Indian public life. Who funds parties,
who wins contracts, who sits in Parliament, which NGOs receive foreign money, and how those connect,
built only from public records, with every edge traceable to a document.

Raven is today a dashboard over five datasets. The aim is a **public-interest knowledge graph** that
journalists, researchers and citizens can query, download and build on.

---

## Principles (these don't change)

1. **Every fact cites a source.** No estimates, no placeholders, no "probably". A gap is shown as a gap.
2. **Institutions and public office, not private lives.** Parties, companies, public bodies, elected
   representatives and candidates in their public role. No home addresses, phone numbers, family members,
   social-media tracking, or face recognition. Personal data is minimised in line with India's DPDP Act, 2023.
3. **Connections aren't accusations.** A shared date or shared director is shown as a fact with its source,
   never as a conclusion.
4. **Reproducible.** Anyone can rebuild the whole database from source with one command.
5. **Corrections are fast and public.** Every correction is logged.

---

## Phase 1: Wider coverage (good first contributions)

Each item is one importer in `backend/app/` plus tests. See [CONTRIBUTING.md](CONTRIBUTING.md).

| Dataset | Source | Why it matters |
|---|---|---|
| ~~State assembly MLAs~~ ✅ done (`ingest-assemblies`) | MyNeta | Sitting MLAs from all 31 assemblies |
| Rajya Sabha members; all assembly candidates (not only winners) | MyNeta (same importer) | Full picture of who stood, not only who won |
| Election results since 1962 | TCPD Lok Dhaba (unreachable from our test environment; check licence); results.eci.gov.in only hosts current counts | Who won, margins, turnout, linked to candidates |
| Electoral trust contributions | ECI annual electoral trust reports (PDFs on old.eci.gov.in, which disallows crawling, so this needs a manual-download importer) | The biggest post-bond funding channel |
| Party contribution reports (Form 24A, >₹20,000) | ECI / party filings | Named donors outside the bond scheme |
| MPLADS works | mplads.gov.in | What each MP spent their local-area fund on |
| ~~Lok Sabha questions~~ ✅ done (`ingest-questions`, 2009 onwards) | Vonter / sansad.in | Who asked about which ministry, sector or company |
| Rajya Sabha questions; full answer text | sansad.in PDFs | Search inside answers, not only titles |
| SEBI, CCI and ED orders and press releases | Regulator websites (SEBI's listing blocks automated access, so these go in via the sourced events CSV for now) | Structured, dated, sourced events for the purchaser timeline |

## Phase 2: Entity graph

- **Resolve organisations across datasets:** a company in the bond data = the same company in contract
  awards = the same company in SEBI orders. Match on registry identifiers (CIN, LEI) where available, and on
  conservative name rules plus human review otherwise. Every match records how it was made.
- **Graph view:** company → bonds → parties; company → contracts → ministries; MP → questions → companies.
- **Review queue:** proposed matches go to a public review queue before they're published.

## Phase 3: Money in, money out

- **Government procurement:** contract awards from CPPP (eprocure.gov.in) and GeM, linked to bond purchasers.
- **Public budgets:** Union and state budget lines (Open Budgets India) for context.
- **CAG audit reports:** indexed and searchable, linked to the ministries and bodies they audit.

## Phase 4: Platform

- ✅ **Search across datasets** (press `/`). Next: full-text ranking with Postgres FTS or Meilisearch.
- **Public read-only API** with keys and rate limits, plus documented, versioned endpoints.
- ✅ **Open data releases:** `export-release` writes CSV + manifest with checksums, published monthly by the
  `Data release` GitHub Action. Next: Parquet.
- ✅ **Automated refresh:** the `Data release` workflow rebuilds everything from source monthly. Next: a diff report
  of what changed between releases.
- **Source archiving:** every source document snapshotted (Wayback Machine or our own store) so citations
  survive link rot.
- 🟡 **Indian languages:** Hindi for the interface shell (navigation, notices, map, state panel, search; `#lang=hi`).
  Next: Key facts, chart and table labels, then other languages. Strings live in `frontend/src/lib/i18n.js`.

## Phase 5: For journalists and researchers

- **Alerts:** follow a company, party or MP and get notified when new records appear.
- ✅ **Shareable views:** the URL records tab, state, purchaser or NGO. Next: embeddable charts.
- **Notebooks:** Jupyter examples showing how to answer real questions with the open data.
- **Methodology pages:** for every dataset, how it's collected, cleaned and matched, and its known limits.

---

## Not planned

Tracking private individuals, scraping personal social media, facial recognition, phone or address lookups,
predictive "risk scores" for people, or anything that can't be traced to a public document.

## How to help

Pick an item from Phase 1, open an issue saying you're on it, and follow [CONTRIBUTING.md](CONTRIBUTING.md).
Data-source suggestions are welcome as issues; please include a link to the source and its licence.
