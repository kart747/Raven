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
    category: str               # one of CATEGORIES
    homepage: str
    language: str = "en"
    kind: str = "rss"           # rss | gdelt
    min_interval_minutes: int = 10
    # Some government firewalls reject user-agents containing a contact URL; we still identify as Raven
    user_agent: str | None = None
    params: dict = field(default_factory=dict)
    # Titles to leave out (case-insensitive regex), e.g. items that are about private individuals, not institutions
    skip_titles: str = ""


SOURCES = [
    # Government and regulators
    Source("pib", "Press Information Bureau", "https://www.pib.gov.in/RssMain.aspx?ModId=6&Lang=1&Regid=3&reg=3",
           "government", "https://pib.gov.in", user_agent="Raven/1.2"),
    Source("rbi-press", "RBI press releases", "https://www.rbi.org.in/pressreleases_rss.xml", "government", "https://www.rbi.org.in",
           min_interval_minutes=30),
    Source("rbi-notifications", "RBI notifications", "https://www.rbi.org.in/notifications_rss.xml", "government",
           "https://www.rbi.org.in", min_interval_minutes=30),
    Source("pib-hindi", "पत्र सूचना कार्यालय (PIB Hindi)", "https://www.pib.gov.in/RssMain.aspx?ModId=6&Lang=2&Regid=3&reg=48",
           "government", "https://pib.gov.in", language="hi", user_agent="Raven/1.2"),
    # SEBI's feed gives the date of each order or circular but no time. Debt-recovery orders and RTI appeals are
    # left out: they are mostly about private individuals (some print PAN numbers), not market institutions.
    Source("sebi", "SEBI: orders, circulars and press releases", "https://www.sebi.gov.in/sebirss.xml", "government",
           "https://www.sebi.gov.in", min_interval_minutes=60,
           skip_titles=r"^appeal no\.|remittance|release order|recovery certificate|\brc no\."),
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
    Source("indiatoday", "India Today", "https://www.indiatoday.in/rss/1206578", "national", "https://www.indiatoday.in"),
    # State news in English
    Source("hindu-tn", "The Hindu: Tamil Nadu", "https://www.thehindu.com/news/national/tamil-nadu/feeder/default.rss",
           "states", "https://www.thehindu.com"),
    Source("hindu-kerala", "The Hindu: Kerala", "https://www.thehindu.com/news/national/kerala/feeder/default.rss",
           "states", "https://www.thehindu.com"),
    Source("hindu-karnataka", "The Hindu: Karnataka", "https://www.thehindu.com/news/national/karnataka/feeder/default.rss",
           "states", "https://www.thehindu.com"),
    Source("hindu-ap", "The Hindu: Andhra Pradesh", "https://www.thehindu.com/news/national/andhra-pradesh/feeder/default.rss",
           "states", "https://www.thehindu.com"),
    Source("hindu-telangana", "The Hindu: Telangana", "https://www.thehindu.com/news/national/telangana/feeder/default.rss",
           "states", "https://www.thehindu.com"),
    Source("hindu-other-states", "The Hindu: Other states", "https://www.thehindu.com/news/national/other-states/feeder/default.rss",
           "states", "https://www.thehindu.com", min_interval_minutes=30),
    Source("deccan-herald", "Deccan Herald", "https://www.deccanherald.com/stories.rss", "states", "https://www.deccanherald.com"),
    Source("nie", "The New Indian Express", "https://www.newindianexpress.com/stories.rss", "states",
           "https://www.newindianexpress.com"),
    Source("odishatv", "OdishaTV", "https://odishatv.in/feed", "states", "https://odishatv.in"),
    Source("pratidin-time", "Pratidin Time (Assam)", "https://www.pratidintime.com/stories.rss", "states",
           "https://www.pratidintime.com"),
    Source("nenow", "Northeast Now", "https://nenow.in/feed", "states", "https://nenow.in"),
    Source("eastmojo", "EastMojo", "https://www.eastmojo.com/feed/", "states", "https://www.eastmojo.com", min_interval_minutes=30),
    Source("kashmir-observer", "Kashmir Observer", "https://kashmirobserver.net/feed/", "states", "https://kashmirobserver.net",
           min_interval_minutes=30),
    # Courts
    Source("barandbench", "Bar & Bench", "https://www.barandbench.com/feed", "courts", "https://www.barandbench.com"),
    Source("sc-observer", "Supreme Court Observer", "https://www.scobserver.in/feed/", "courts", "https://www.scobserver.in",
           min_interval_minutes=60),
    # Fact-checking
    Source("altnews", "Alt News", "https://www.altnews.in/feed/", "factcheck", "https://www.altnews.in", min_interval_minutes=30),
    Source("factly", "Factly", "https://factly.in/feed/", "factcheck", "https://factly.in", min_interval_minutes=30),
    Source("newschecker", "Newschecker", "https://newschecker.in/feed", "factcheck", "https://newschecker.in", min_interval_minutes=30),
    Source("vishvas", "Vishvas News", "https://www.vishvasnews.com/feed/", "factcheck", "https://www.vishvasnews.com",
           language="hi", min_interval_minutes=30),
    # Indian languages
    Source("bbc-hindi", "BBC Hindi", "https://feeds.bbci.co.uk/hindi/rss.xml", "languages", "https://www.bbc.com/hindi", language="hi"),
    Source("ndtv-khabar", "NDTV Khabar", "https://feeds.feedburner.com/ndtvkhabar-latest", "languages", "https://ndtv.in", language="hi"),
    Source("amarujala", "Amar Ujala", "https://www.amarujala.com/rss/breaking-news.xml", "languages", "https://www.amarujala.com",
           language="hi"),
    Source("abp-live", "ABP Live (Hindi)", "https://www.abplive.com/home/feed", "languages", "https://www.abplive.com", language="hi"),
    Source("bbc-marathi", "BBC Marathi", "https://feeds.bbci.co.uk/marathi/rss.xml", "languages", "https://www.bbc.com/marathi",
           language="mr"),
    Source("esakal", "Sakal", "https://www.esakal.com/stories.rss", "languages", "https://www.esakal.com", language="mr"),
    Source("abp-majha", "ABP Majha", "https://marathi.abplive.com/home/feed", "languages", "https://marathi.abplive.com", language="mr"),
    Source("bbc-gujarati", "BBC Gujarati", "https://feeds.bbci.co.uk/gujarati/rss.xml", "languages", "https://www.bbc.com/gujarati",
           language="gu"),
    Source("iamgujarat", "I am Gujarat", "https://www.iamgujarat.com/rssfeedsdefault.cms", "languages", "https://www.iamgujarat.com",
           language="gu"),
    Source("bbc-punjabi", "BBC Punjabi", "https://feeds.bbci.co.uk/punjabi/rss.xml", "languages", "https://www.bbc.com/punjabi",
           language="pa"),
    Source("abp-ananda", "ABP Ananda", "https://bengali.abplive.com/home/feed", "languages", "https://bengali.abplive.com",
           language="bn"),
    Source("sangbad-pratidin", "Sangbad Pratidin", "https://www.sangbadpratidin.in/feed/", "languages",
           "https://www.sangbadpratidin.in", language="bn"),
    Source("bbc-tamil", "BBC Tamil", "https://feeds.bbci.co.uk/tamil/rss.xml", "languages", "https://www.bbc.com/tamil", language="ta"),
    Source("dinamani", "Dinamani", "https://www.dinamani.com/stories.rss", "languages", "https://www.dinamani.com", language="ta"),
    Source("bbc-telugu", "BBC Telugu", "https://feeds.bbci.co.uk/telugu/rss.xml", "languages", "https://www.bbc.com/telugu",
           language="te"),
    Source("sakshi", "Sakshi", "https://www.sakshi.com/rss.xml", "languages", "https://www.sakshi.com", language="te"),
    Source("prajavani", "Prajavani", "https://www.prajavani.net/stories.rss", "languages", "https://www.prajavani.net", language="kn"),
    Source("mathrubhumi", "Mathrubhumi", "https://www.mathrubhumi.com/rss", "languages", "https://www.mathrubhumi.com", language="ml"),
    # Open global news database (rate limit: one request per 5 seconds; we poll every 15 minutes)
    Source("gdelt-india", "GDELT: Indian politics coverage", "https://api.gdeltproject.org/api/v2/doc/doc", "global",
           "https://www.gdeltproject.org", kind="gdelt", min_interval_minutes=15,
           params={"query": '(election OR parliament OR "Lok Sabha" OR "Rajya Sabha" OR minister OR "Supreme Court" '
                            'OR "Election Commission") sourcecountry:IN sourcelang:english',
                   "mode": "artlist", "format": "json", "maxrecords": "75", "timespan": "6h", "sort": "datedesc"}),
]

BY_KEY = {s.key: s for s in SOURCES}
CATEGORIES = ["government", "politics", "national", "states", "courts", "factcheck", "languages", "global"]
LANGUAGES = {"en": "English", "hi": "हिन्दी", "mr": "मराठी", "gu": "ગુજરાતી", "pa": "ਪੰਜਾਬੀ", "bn": "বাংলা",
             "ta": "தமிழ்", "te": "తెలుగు", "kn": "ಕನ್ನಡ", "ml": "മലയാളം"}
assert all(s.category in CATEGORIES and s.language in LANGUAGES for s in SOURCES)
assert len(BY_KEY) == len(SOURCES), "duplicate source key"
