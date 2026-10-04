"""
Groups recent headlines that report the same story, so "what is happening now" can be read as stories ranked by
how many different outlets carry them, instead of a stream of near-duplicate headlines.

Headlines are compared by the words they share, weighted so that rare words (names, places) count more than
common ones; a headline joins the story it is most similar to, oldest first. This is automatic and approximate:
it can split one story in two or join two related ones, and the UI says so. Languages are grouped separately.
"""
import math
from collections import Counter, defaultdict

from .tagger import normalise

_STOP = set("""
a an the and or but of to in on at for from by with as is are was were be been being it its this that these those
after before over under into about against amid amidst during while than then so not no yes will would can could
should may might must has have had do does did done says said say tells told asks asked new latest live updates
update news today day week year years how why what when where who which here there all any more most some one two
three four five first second last top big full list check video watch read know ahead amid also just now out up
off his her their our your my he she they we you him them us me
""".split())
# Common Hindi/Marathi function words (other languages mostly attach them, and rarity weighting covers the rest)
_STOP |= set("के का की में से को ने पर और है हैं था थे तो भी ही यह वह ये वो लिए एक कहा नहीं अब हुआ हुई क्या कैसे बाद साथ "
             "आणि हे ते या व आहे होते".split())


def _terms(title: str) -> set[str]:
    return {w for w in normalise(title).split() if w not in _STOP and not w.isdigit() and len(w) >= 3}


def group(items: list[dict], threshold: float = 0.4) -> list[list[dict]]:
    """items: dicts with at least title, language and published_at. Returns groups, each oldest first."""
    terms = [_terms(i["title"]) for i in items]
    df = Counter(t for ts in terms for t in ts)
    n = max(len(items), 1)
    idf = {t: math.log(n / c) for t, c in df.items()}

    stories: list[dict] = []            # {"centroid": {term: weight}, "items": [...], "language": str}
    index: dict[tuple[str, str], set[int]] = defaultdict(set)   # (language, term) -> story numbers
    for k in sorted(range(len(items)), key=lambda k: items[k]["published_at"]):
        item, lang = items[k], items[k].get("language") or "en"
        vec = {t: idf[t] for t in terms[k] if df[t] > 1}   # a word seen once can't link two headlines
        norm = math.sqrt(sum(w * w for w in vec.values()))
        best, best_score = None, threshold
        if norm:
            for s in set().union(*(index[(lang, t)] for t in vec)):
                c = stories[s]["centroid"]
                if sum(1 for t in vec if t in c) < 2:   # one shared word ("murder", "army") is not a story
                    continue
                dot = sum(w * c.get(t, 0.0) for t, w in vec.items())
                score = dot / (norm * stories[s]["norm"])
                if score >= best_score:
                    best, best_score = s, score
        if best is None:
            stories.append({"centroid": {}, "norm": 0.0, "items": [], "language": lang})
            best = len(stories) - 1
        story = stories[best]
        story["items"].append(item)
        for t, w in vec.items():   # centroid = sum of unit vectors of its headlines
            story["centroid"][t] = story["centroid"].get(t, 0.0) + w / norm
            index[(lang, t)].add(best)
        story["norm"] = math.sqrt(sum(w * w for w in story["centroid"].values())) or 1.0
    return [s["items"] for s in stories]


def representative(story: list[dict]) -> dict:
    """The headline sharing the most weighted words with the rest of its story (ties: the earliest)."""
    if len(story) <= 2:
        return story[0]
    counts = Counter(t for i in story for t in _terms(i["title"]))
    return max(story, key=lambda i: sum(counts[t] - 1 for t in _terms(i["title"])))
