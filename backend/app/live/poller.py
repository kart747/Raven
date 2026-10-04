"""
Polite poller for the live sources.

- robots.txt is checked (and cached for a day) before every fetch; disallowed sources are skipped
- conditional requests (ETag / Last-Modified) so unchanged feeds cost the publisher almost nothing
- each source has a minimum interval; failures back off exponentially (up to 6 hours)
- stores headline, link and time only, deduplicated by URL; old items are pruned
"""
import calendar
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


def _when(entry) -> datetime.datetime | None:
    """Publication time in UTC. Feeds that omit the timezone (e.g. RBI) are Indian sources: read as IST."""
    for field in ("published_parsed", "updated_parsed"):
        value = entry.get(field)
        if value:
            return datetime.datetime.fromtimestamp(calendar.timegm(value), datetime.UTC).replace(tzinfo=None)
    for field in ("published", "updated"):
        raw = (entry.get(field) or "").strip()
        if not raw:
            continue
        try:
            dt = email.utils.parsedate_to_datetime(raw)
        except (TypeError, ValueError):
            continue
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=IST)
        return dt.astimezone(datetime.UTC).replace(tzinfo=None)
    return None


def parse_rss(content: bytes) -> list[dict]:
    items = []
    for e in feedparser.parse(content).entries:
        title = html.unescape(re.sub(r"<[^>]+>", "", (e.get("title") or ""))).strip()
        link = (e.get("link") or "").strip()
        if title and link.startswith("http"):
            items.append({"title": title[:500], "url": clean_url(link), "published_at": _when(e)})
    return items


def parse_gdelt(payload: dict) -> list[dict]:
    items = []
    for a in payload.get("articles", []):
        try:
            seen = datetime.datetime.strptime(a["seendate"], "%Y%m%dT%H%M%SZ")
        except (KeyError, ValueError):
            seen = None
        if a.get("title") and a.get("url", "").startswith("http"):
            items.append({"title": a["title"].strip()[:500], "url": clean_url(a["url"]), "published_at": seen})
    return items


def _due(row: models.LiveSource, source: Source) -> bool:
    if row.last_fetch_at is None:
        return True
    backoff = min(source.min_interval_minutes * (2 ** row.consecutive_failures), 360)
    return now() - row.last_fetch_at >= datetime.timedelta(minutes=backoff)


def fetch(source: Source, row: models.LiveSource) -> tuple[str, list[dict]]:
    agent = source.user_agent or USER_AGENT
    if not robots_allows(source.url, agent):
        return "robots-disallowed", []
    headers = {"User-Agent": agent}
    if source.kind == "rss":
        if row.etag:
            headers["If-None-Match"] = row.etag
        if row.last_modified:
            headers["If-Modified-Since"] = row.last_modified
    r = requests.get(source.url, params=source.params or None, headers=headers, timeout=TIMEOUT)
    if r.status_code == 304:
        return "not-modified", []
    if r.status_code != 200:
        return f"http-{r.status_code}", []
    row.etag, row.last_modified = r.headers.get("ETag"), r.headers.get("Last-Modified")
    if source.kind == "gdelt":
        try:
            return "ok", parse_gdelt(r.json())
        except ValueError:
            return "error: non-JSON reply (rate limited?)", []
    return "ok", parse_rss(r.content)


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
            row.name, row.category, row.url, row.homepage, row.language = s.name, s.category, s.url, s.homepage, s.language
        db.commit()
        rows = {r.key: r for r in db.query(models.LiveSource)}

        tagger = None
        for s in SOURCES:
            if only and s.key not in only:
                continue
            row = rows[s.key]
            if not force and not _due(row, s):
                continue
            try:
                status, items = fetch(s, row)
            except requests.RequestException as e:
                status, items = f"error: {type(e).__name__}", []
            row.last_fetch_at, row.last_status = now(), status
            ok = status in ("ok", "not-modified")
            row.consecutive_failures = 0 if ok else (row.consecutive_failures or 0) + 1
            if ok:
                row.last_ok_at = row.last_fetch_at
            added = 0
            if items:
                known = {u for (u,) in db.query(models.LiveItem.url).filter(
                    models.LiveItem.url.in_([i["url"] for i in items]))}
                tagger = tagger or Tagger(db)
                for i in items:
                    if i["url"] in known:
                        continue
                    known.add(i["url"])
                    # Allow a little clock skew; otherwise fall back to the time we first saw it, and say so
                    usable = i["published_at"] and i["published_at"] <= now() + datetime.timedelta(minutes=10)
                    published = min(i["published_at"], row.last_fetch_at) if usable else row.last_fetch_at
                    item = models.LiveItem(source_key=s.key, url=i["url"], title=i["title"], published_at=published,
                                           fetched_at=row.last_fetch_at, time_estimated=not usable,
                                           category=s.category, language=s.language)
                    db.add(item)
                    db.flush()
                    for kind, ref, label in tagger.tag(i["title"]):
                        db.add(models.LiveMention(item_id=item.id, kind=kind, ref=ref, label=label))
                    added += 1
                row.items_total = (row.items_total or 0) + added
            db.commit()
            report[s.key] = {"status": status, "new_items": added}
            if s.kind == "gdelt":
                time.sleep(5)  # GDELT asks for at most one request every 5 seconds

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
        tagger = Tagger(db)
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
