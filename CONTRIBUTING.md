# Contributing to Raven

Thanks for helping. Raven is only as good as its sources, so most of this guide is about adding data
correctly.

## Ground rules

- **Every record must have a source URL.** No estimated, guessed or placeholder values for real people or
  organisations. If a field isn't in the source, leave it empty and let the UI show the gap.
- **Public role only.** Don't import personal contact details, family information or anything about
  private individuals beyond what an official disclosure lists about their public role.
- **Respect the source.** Check robots.txt and terms, rate-limit requests, cache responses locally, and
  identify Raven in the user-agent. Record the source's licence in the importer docstring.
- **Show your matching.** If you link records across datasets, store how each match was made.

## Setup

Follow the Quick start in [README.md](README.md). Run the tests before and after your change:

```bash
cd backend && venv/bin/python -m pytest
cd frontend && npm run build
```

## Adding a dataset

1. **Open an issue first** with the source URL, its licence, and what you plan to import.
2. **Model:** add a table in `backend/app/models.py` with `source_name`, `source_url` and `created_at`.
   New tables are created automatically; for changes to existing tables, describe the migration in your PR.
3. **Importer:** create `backend/app/import_<name>.py` with a `run_import()` that:
   - fetches with a polite user-agent and a delay (see `import_myneta.py` for caching and rate limiting),
   - parses into plain dicts with small, testable helper functions,
   - normalises states with `app/states.py` and parties with `app/parties.py`,
   - replaces the dataset's rows in one transaction so re-runs are safe,
   - returns a summary dict (rows imported, skipped, unmatched).
4. **CLI:** register it in `backend/app/cli.py` and add it to `ingest-all` if it needs no manual input.
5. **Tests:** add parsing tests to `backend/tests/` using small inline samples of the real format.
6. **API and UI:** add endpoints in `main.py` and data hooks in `frontend/src/lib/queries.js`.
7. **Data quality:** add the dataset to `/api/v1/data-quality` with its coverage and gaps.
8. **Docs:** add the source to the README's data table and its known gaps to "Data quality and known gaps".

## Adding a live feed

Live sources are listed in `backend/app/live/sources.py`. To add one:

1. Use the **publisher's own** RSS/Atom feed or an open API. No aggregators that forbid reuse (e.g. Google News),
   no scraping of article pages, and nothing behind a login or paywall.
2. Check the site's `robots.txt` allows the feed URL (the poller also checks, and skips the source if not).
3. Add a `Source(key, name, url, category, homepage, language)`. Use an existing category if one fits, and a
   `min_interval_minutes` of 10 or more.
4. Run `python -m app.cli live-poll --only <key>` and check the headlines, times and links look right. If the
   feed has no dates, items are shown as "seen" at the time Raven first saw them; say so in the PR.
5. If the source names people, parties or companies in a way the tagger misses (abbreviations, nicknames),
   add an alias in `backend/app/live/tagger.py`, then run `python -m app.cli live-retag`.

Only the headline, link and time are stored. Don't add fields that copy article text.

## Translations

Interface text lives in `frontend/src/lib/i18n.js` as key → string per language. To add a language, copy the
`en` block, translate it, and add the language to `LANGS`. Don't translate data (names, parties, figures).

## Pull requests

- Keep each PR to one dataset or one feature.
- Include the importer's summary output from a real run.
- Describe any known limitations of the data honestly; they belong in the README, not hidden.

## Reporting errors in the data

Open an issue with the record, what's wrong, and a link to the official source with the correct value.
