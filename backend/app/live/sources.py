"""
Catalog of live sources. Every entry is a publisher's own syndication feed or an open API.

Rules for adding a source (see CONTRIBUTING.md):
- it must be an RSS/Atom feed or an API published for reuse, allowed by the site's robots.txt;
- Raven stores only headline, link and time, and always links to the publisher;
- no aggregator scraping (e.g. Google News), no paywall or login bypass, no source that blocks bots.
"""
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Source:
    key: str
    name: str
    url: str
    category: str               # government | politics | national | courts | factcheck | hindi | global
    homepage: str
    language: str = "en"
    kind: str = "rss"           # rss | gdelt
    min_interval_minutes: int = 10
    # Some government firewalls reject user-agents containing a contact URL; we still identify as Raven
    user_agent: str | None = None
    params: dict = field(default_factory=dict)


SOURCES = [
    # Government and regulators
    Source("pib", "Press Information Bureau", "https://www.pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3&reg=3",
           "government", "https://pib.gov.in", user_agent="Raven/1.2"),
    Source("rbi-press", "RBI press releases", "https://www.rbi.org.in/pressreleases_rss.xml", "government", "https://www.rbi.org.in",
           min_interval_minutes=30),
    Source("rbi-notifications", "RBI notifications", "https://www.rbi.org.in/notifications_rss.xml", "government",
           "https://www.rbi.org.in", min_interval_minutes=30),
    # Politics desks
    Source("ie-political-pulse", "Indian Express: Political Pulse", "https://indianexpress.com/section/political-pulse/feed/",
           "politics", "https://indianexpress.com"),
    Source("theprint-politics", "ThePrint: Politics", "https://theprint.in/category/politics/feed/", "politics", "https://theprint.in"),
    Source("mint-politics", "Mint: Politics", "https://www.livemint.com/rss/politics", "politics", "https://www.livemint.com"),
    Source("et-politics", "Economic Times: Politics & Nation",
           "https://economictimes.indiatimes.com/news/politics-and-nation/rssfeeds/1052732854.cms", "politics",
           "https://economictimes.indiatimes.com"),
    Source("news18-politics", "News18: Politics", "https://www.news18.com/rss/politics.xml", "politics", "https://www.news18.com"),
    # National news
    Source("thehindu-national", "The Hindu: National", "https://www.thehindu.com/news/national/feeder/default.rss", "national",
           "https://www.thehindu.com"),
    Source("ie-india", "Indian Express: India", "https://indianexpress.com/section/india/feed/", "national", "https://indianexpress.com"),
    Source("ndtv-india", "NDTV: India", "https://feeds.feedburner.com/ndtvnews-india-news", "national", "https://www.ndtv.com"),
    Source("toi-india", "Times of India: India", "https://timesofindia.indiatimes.com/rssfeeds/-2128936835.cms", "national",
           "https://timesofindia.indiatimes.com"),
    Source("ht-india", "Hindustan Times: India", "https://www.hindustantimes.com/feeds/rss/india-news/rssfeed.xml", "national",
           "https://www.hindustantimes.com"),
    Source("scroll", "Scroll", "https://feeds.feedburner.com/ScrollinArticles.rss", "national", "https://scroll.in"),
    Source("tnm", "The News Minute", "https://www.thenewsminute.com/feed", "national", "https://www.thenewsminute.com"),
    # Courts
    Source("barandbench", "Bar & Bench", "https://www.barandbench.com/feed", "courts", "https://www.barandbench.com"),
    Source("sc-observer", "Supreme Court Observer", "https://www.scobserver.in/feed/", "courts", "https://www.scobserver.in",
           min_interval_minutes=60),
    # Fact-checking
    Source("altnews", "Alt News", "https://www.altnews.in/feed/", "factcheck", "https://www.altnews.in", min_interval_minutes=30),
    # Hindi
    Source("bbc-hindi", "BBC Hindi", "https://feeds.bbci.co.uk/hindi/rss.xml", "hindi", "https://www.bbc.com/hindi", language="hi"),
    Source("ndtv-khabar", "NDTV Khabar", "https://feeds.feedburner.com/ndtvkhabar-latest", "hindi", "https://ndtv.in", language="hi"),
    # Open global news database (rate limit: one request per 5 seconds; we poll every 15 minutes)
    Source("gdelt-india", "GDELT: Indian politics coverage", "https://api.gdeltproject.org/api/v2/doc/doc", "global",
           "https://www.gdeltproject.org", kind="gdelt", min_interval_minutes=15,
           params={"query": '(election OR parliament OR "Lok Sabha" OR "Rajya Sabha" OR minister OR "Supreme Court" '
                            'OR "Election Commission") sourcecountry:IN sourcelang:english',
                   "mode": "artlist", "format": "json", "maxrecords": "75", "timespan": "6h", "sort": "datedesc"}),
]

BY_KEY = {s.key: s for s in SOURCES}
CATEGORIES = ["government", "politics", "national", "courts", "factcheck", "hindi", "global"]
