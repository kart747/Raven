import calendar
import datetime
import hashlib
import logging
import os
from typing import Optional, List, Dict, Tuple

import feedparser
import requests

logger = logging.getLogger(__name__)

PIB_FEEDS = [
    {"mod_id": 6, "regid": 3, "label": "general releases english national"},
]

PIB_RSS_URL_TEMPLATE = os.getenv(
    "PIB_RSS_URL_TEMPLATE",
    # Lang=1 + reg=3 pin the English national feed; without them PIB redirects to Hindi
    "https://www.pib.gov.in/RssMain.aspx?ModId={mod_id}&Lang=1&Regid={regid}&reg=3",
)
PIB_HTTP_TIMEOUT_SECONDS = float(os.getenv("PIB_HTTP_TIMEOUT_SECONDS", "20"))

# In-memory cache holding feed data
# Key: (mod_id, regid)
# Value: (fetched_at, list_of_releases)
_pib_cache: Dict[Tuple[int, int], Tuple[datetime.datetime, List[dict]]] = {}
CACHE_TTL = datetime.timedelta(minutes=15)


def build_pib_feed_url(mod_id: int, regid: int) -> str:
    return PIB_RSS_URL_TEMPLATE.format(mod_id=mod_id, regid=regid)


def _parse_feed_datetime(entry: object) -> Optional[datetime.datetime]:
    for field_name in ("published_parsed", "updated_parsed"):
        value = getattr(entry, field_name, None)
        if value:
            return datetime.datetime.utcfromtimestamp(calendar.timegm(value))
    return None


def _extract_ministry_tag(entry: object) -> Optional[str]:
    tags = getattr(entry, "tags", None) or []
    for tag in tags:
        term = getattr(tag, "term", None) or tag.get("term")
        if term:
            return term
    return None


def _extract_source_url(entry: object) -> Optional[str]:
    for field_name in ("link", "id", "guid"):
        value = getattr(entry, field_name, None)
        if value:
            return value
    return None


def fetch_live_pib_feed(mod_id: int, regid: int) -> List[dict]:
    """Fetches the PIB feed from live RSS url."""
    feed_url = build_pib_feed_url(mod_id=mod_id, regid=regid)
    response = requests.get(
        feed_url,
        timeout=PIB_HTTP_TIMEOUT_SECONDS,
        headers={
            # Identify honestly; PIB's firewall rejects user-agents containing a contact URL
            "User-Agent": "Raven/1.2"
        },
    )
    response.raise_for_status()

    parsed_feed = feedparser.parse(response.content)
    now = datetime.datetime.utcnow()
    source_name = "Press Information Bureau (PIB)"

    releases = []
    for entry in parsed_feed.entries:
        source_url = _extract_source_url(entry)
        title = getattr(entry, "title", None)
        if not source_url or not title:
            continue

        published_at = _parse_feed_datetime(entry) or now
        ministry_tag = _extract_ministry_tag(entry)

        # Stable across restarts (built-in hash() is salted per process)
        stable_id = int(hashlib.sha1(source_url.encode()).hexdigest()[:8], 16)

        releases.append({
            "id": stable_id,
            "mod_id": mod_id,
            "regid": regid,
            "title": title,
            "ministry_tag": ministry_tag,
            "published_at": published_at,
            "created_at": now,
            "source_citation": {
                "source_name": source_name,
                "source_url": source_url,
                "last_updated": now,
            },
        })
    
    # Sort releases by published_at desc
    releases.sort(key=lambda x: x["published_at"] or now, reverse=True)
    return releases


def get_cached_pib_releases(mod_id: int, regid: int, force_refresh: bool = False) -> List[dict]:
    """Returns PIB releases from the in-memory cache, or fetches them live if cache is stale or missing."""
    now = datetime.datetime.utcnow()
    cache_key = (mod_id, regid)

    if not force_refresh and cache_key in _pib_cache:
        fetched_at, data = _pib_cache[cache_key]
        if now - fetched_at < CACHE_TTL:
            return data

    logger.info(f"PIB Cache stale or missing for {cache_key}. Fetching live...")
    try:
        data = fetch_live_pib_feed(mod_id, regid)
        _pib_cache[cache_key] = (now, data)
        return data
    except Exception as exc:
        logger.exception(f"Failed to fetch live PIB feed for {cache_key}: {exc}")
        # If live fetch fails, fall back to stale cache if it exists
        if cache_key in _pib_cache:
            return _pib_cache[cache_key][1]
        raise exc


def clear_pib_cache():
    """Clears the in-memory PIB cache."""
    _pib_cache.clear()