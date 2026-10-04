"""
Polite poller for the live sources.

- robots.txt is checked (and cached for a day) before every fetch; disallowed sources are skipped
- conditional requests (ETag / Last-Modified) so unchanged feeds cost the publisher almost nothing
- each source has a minimum interval; failures back off exponentially (up to 6 hours)
- publishers are fetched in parallel, each one's feeds one after another; results are stored by one thread
- stores headline, link and time only, deduplicated by URL; old items are pruned
"""
import calendar
import concurrent.futures
import datetime
import email.utils
import html
import logging
import os
import re
import time
import urllib.parse
import urllib.robotparser

import feedparser
import requests

from ..database import SessionLocal, ensure_schema
from .. import models
from .sources import SOURCES, Source
from .tagger import Tagger

logger = logging.getLogger("raven.live")
USER_AGENT = "Raven/1.2 (+https://github.com/kart747/Raven; open-data research; respects robots.txt)"
TIMEOUT = 25
RETENTION_DAYS = int(os.getenv("LIVE_RETENTION_DAYS", "60"))
_robots: dict[str, tuple[float, urllib.robotparser.RobotFileParser | None]] = {}
_TRACKING = re.compile(r"^(utm_|at_|fbclid|gclid|ref$|cmp$|from$)")   # at_*: BBC feed tracking


def now() -> datetime.datetime:
    return datetime.datetime.now(datetime.UTC).replace(tzinfo=None)


def clean_url(url: str) -> str:
    """Drop tracking parameters and fragments so the same article is stored once."""
    parts = urllib.parse.urlsplit(url.strip())
    query = [(k, v) for k, v in urllib.parse.parse_qsl(parts.query, keep_blank_values=True) if not _TRACKING.match(k.lower())]
    return urllib.parse.urlunsplit((parts.scheme, parts.netloc.lower(), parts.path, urllib.parse.urlencode(query), ""))


def robots_allows(url: str, agent: str) -> bool:
    host = urllib.parse.urlsplit(url)
    origin = f"{host.scheme}://{host.netloc}"
    cached = _robots.get(origin)
    if not cached or time.time() - cached[0] > 86400:
        parser = urllib.robotparser.RobotFileParser()
        try:
            r = requests.get(f"{origin}/robots.txt", headers={"User-Agent": agent}, timeout=TIMEOUT)
            if r.status_code >= 500:
                parser = None          # unknown: be cautious, skip this round
            else:
                parser.parse(r.text.splitlines() if r.status_code == 200 else [])
        except requests.RequestException:
            parser = None
        _robots[origin] = cached = (time.time(), parser)
    parser = cached[1]
    return bool(parser) and parser.can_fetch(agent, url)


IST = datetime.timezone(datetime.timedelta(hours=5, minutes=30))


_DATE_ONLY = re.compile(r"^(\d{1,2})\s+([A-Za-z]{3})[a-z]*,?\s+(\d{4})(?:\s+[+-]\d{4})?$")


def _when(entry) -> tuple[datetime.datetime | None, bool]:
    """(publication time in UTC, date_only). Feeds that omit the timezone (e.g. RBI) are Indian sources: read as
    IST. Feeds that give only a date (e.g. SEBI: "01 Oct, 2026 +0530") return midnight IST of that date."""
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            return datetime.datetime.fromtimestamp(calendar.timegm(value), datetime.UTC).replace(tzinfo=None), False
    for field in ("published", "updated"):
        raw = (entry.get(field) or "").strip()
        if not raw:
            continue
        day = _DATE_ONLY.match(raw)
        if day:
            try:
                date = datetime.datetime.strptime(" ".join(day.groups()), "%d %b %Y")
            except ValueError:
                continue
            return date.replace(tzinfo=IST).astimezone(datetime.UTC).replace(tzinfo=None), True
        try:
            dt = email.utils.parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt.astimezone(datetime.UTC).replace(tzinfo=None), False
    return None, False


# A PAN (Indian tax ID) is personal data; some government feeds print it in titles. Never store it.
_PAN = re.compile(r"\s*\(?\s*(?:PAN\s*(?:No\.?)?\s*[:\-]?\s*)?\b[A-Z]{5}[0-9]{4}[A-Z]\b\s*\)?")


def clean_title(title: str) -> str:
    return re.sub(r"\s{2,}", " ", _PAN.sub(" ", title)).strip()


def parse_rss(content: bytes) -> list[dict]:
    items = []
    for e in feedparser.parse(content).entries:
        title = clean_title(html.unescape(re.sub(r"<[^>]+>", "", (e.get("title") or ""))))
        link = (e.get("link") or "").strip()
        if title and link.startswith("http"):
            published, date_only = _when(e)
            items.append({"title": title[:500], "url": clean_url(link), "published_at": published, "date_only": date_only})
    return items


def parse_gdelt(payload: dict) -> list[dict]:
    items = []
    for a in payload.get("articles", []):
        try:
            seen = datetime.datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ")
        except (KeyError, ValueError):
            seen = None
        if a.get("title") and a.get("url", "").startswith("http"):
            items.append({"title": clean_title(a["title"])[:500], "url": clean_url(a["url"]), "published_at": seen})
    return items


def _due(row: models.LiveSource, source: Source) -> bool:
    if row.last_fetch_at is None:
        return True
    backoff = min(source.min_interval_minutes * (2 ** row.consecutive_failures), 360)
    return now() - row.last_fetch_at >= datetime.timedelta(minutes=backoff)


def fetch(source: Source, etag: str | None = None, last_modified: str | None = None) -> tuple[str, list[dict], str | None, str | None]:
    """(status, items, etag, last_modified). Touches no database state, so sources can be fetched in parallel."""
    agent = source.user_agent or USER_AGENT
    if not robots_allows(source.url, agent):
        return "robots-disallowed", [], etag, last_modified
    headers = {"User-Agent": agent}
    if source.kind == "rss":
        if etag:
            headers["If-None-Match"] = etag
        if last_modified:
            headers["If-Modified-Since"] = last_modified
    r = requests.get(source.url, params=source.params or None, headers=headers, timeout=TIMEOUT)
    if r.status_code == 304:
        return "not-modified", [], etag, last_modified
    if r.status_code != 200:
        return f"http-{r.status_code}", [], etag, last_modified
    etag, last_modified = r.headers.get("ETag"), r.headers.get("Last-Modified")
    if source.kind == "gdelt":
        try:
            return "ok", parse_gdelt(r.json()), etag, last_modified
        except ValueError:
            return "error: non-JSON reply (rate limited?)", [], etag, last_modified
    return "ok", parse_rss(r.content), etag, last_modified


def _fetch_safely(source: Source, etag: str | None, last_modified: str | None):
    try:
        return fetch(source, etag, last_modified)
    except requests.RequestException as e:
        return f"error: {type(e).__name__}", [], etag, last_modified


def _published(item: dict, seen: datetime.datetime) -> tuple[datetime.datetime, bool]:
    """(time to sort and show by, time_estimated). A date-only item sorts at the time first seen if that was on
    its date, else at the end of its date; the UI shows only the date."""
    when = item["published_at"]
    if not when or when > seen + datetime.timedelta(minutes=10):   # allow a little clock skew
        return seen, True
    if item.get("date_only"):
        return min(seen, when + datetime.timedelta(days=1, seconds=-1)), False
    return min(when, seen), False


def poll(force: bool = False, only: list[str] | None = None) -> dict:
    """Fetch every due source once. Returns per-source results."""
    ensure_schema()
    db = SessionLocal()
    report = {}
    try:
        rows = {r.key: r for r in db.query(models.LiveSource)}
        for s in SOURCES:
            row = rows.get(s.key)
            if row is None:
                row = models.LiveSource(key=s.key, consecutive_failures=0, items_total=0)
                db.add(row)
            elif row.category != s.category:   # a source moved category: move what it already collected
                db.query(models.LiveItem).filter(models.LiveItem.source_key == s.key)\
                    .update({models.LiveItem.category: s.category}, synchronize_session=False)
            row.name, row.category, row.url, row.homepage, row.language = s.name, s.category, s.url, s.homepage, s.language
        db.commit()
        rows = {r.key: r for r in db.query(models.LiveSource)}

        due = [s for s in SOURCES if (not only or s.key in only) and (force or _due(rows[s.key], s))]
        validators = {s.key: (rows[s.key].etag, rows[s.key].last_modified) for s in due}
        by_host: dict[str, list[Source]] = {}
        for s in due:   # one request at a time per publisher; different publishers in parallel
            by_host.setdefault(urllib.parse.urlsplit(s.url).netloc, []).append(s)

        def fetch_host(sources):
            return [(s, _fetch_safely(s, *validators[s.key])) for s in sources]

        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            results = [r for batch in pool.map(fetch_host, by_host.values()) for r in batch]

        tagger = None
        for s, (status, items, etag, last_modified) in results:
            row = rows[s.key]
            row.last_fetch_at, row.last_status = now(), status
            row.etag, row.last_modified = etag, last_modified
            ok = status in ("ok", "not-modified")
            row.consecutive_failures = 0 if ok else (row.consecutive_failures or 0) + 1
            if ok:
                row.last_ok_at = row.last_fetch_at
            added = 0
            if items:
                known = {u for (u,) in db.query(models.LiveItem.url).filter(
                    models.LiveItem.url.in_([i["url"] for i in items]))}
                tagger = tagger or Tagger.from_db(db)
                skip = re.compile(s.skip_titles, re.I) if s.skip_titles else None
                for i in items:
                    if i["url"] in known or (skip and skip.search(i["title"])):
                        continue
                    known.add(i["url"])
                    published, estimated = _published(i, row.last_fetch_at)
                    item = models.LiveItem(source_key=s.key, url=i["url"], title=i["title"], published_at=published,
                                           fetched_at=row.last_fetch_at, time_estimated=estimated,
                                           date_only=bool(i.get("date_only")) and not estimated,
                                           category=s.category, language=s.language)
                    db.add(item)
                    db.flush()
                    for kind, ref, label in tagger.tag(i["title"]):
                        db.add(models.LiveMention(item_id=item.id, kind=kind, ref=ref, label=label))
                    added += 1
                row.items_total = (row.items_total or 0) + added
            db.commit()
            report[s.key] = {"status": status, "new_items": added}

        cutoff = now() - datetime.timedelta(days=RETENTION_DAYS)
        old = [i for (i,) in db.query(models.LiveItem.id).filter(models.LiveItem.published_at < cutoff)]
        if old:
            db.query(models.LiveMention).filter(models.LiveMention.item_id.in_(old)).delete(synchronize_session=False)
            db.query(models.LiveItem).filter(models.LiveItem.id.in_(old)).delete(synchronize_session=False)
            db.commit()
        return report
    finally:
        db.close()


def retag() -> dict:
    """Re-run the tagger over every stored headline (after tagging rules or entity data change)."""
    ensure_schema()
    db = SessionLocal()
    try:
        tagger = Tagger.from_db(db)
        db.query(models.LiveMention).delete(synchronize_session=False)
        n = 0
        for item_id, title in db.query(models.LiveItem.id, models.LiveItem.title):
            for kind, ref, label in tagger.tag(title):
                db.add(models.LiveMention(item_id=item_id, kind=kind, ref=ref, label=label))
                n += 1
        db.commit()
        return {"mentions": n}
    finally:
        db.close()
