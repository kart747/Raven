"""
Entity resolution for electoral bond purchaser names.

SBI printed purchaser names inconsistently: "VEDANTA LTD" / "VEDANTA LIMITED",
"MEGHA ... LI MITED", "B G SHIRKE ... PVT L TD", and names cut off at ~35 characters.
This module groups spellings of the same purchaser conservatively:

1. Exact match on a compact key (case, spacing, punctuation, &/AND, legal suffix ignored).
2. A name of 30+ characters that is a prefix of exactly one other key is treated as
   truncated and merged into it, unless the longer name is an HUF (a separate legal entity).
"""
import re
from collections import Counter, defaultdict

_SUFFIX_PVT = re.compile(r"(PRIVATELIMITED|PVTLIMITED|PRIVATELTD|PVTLTD|PVTL)$")
_SUFFIX_LTD = re.compile(r"(LIMITED|LTD|LIMITE|LIMIT)$")
TRUNCATION_MIN_LEN = 30


def entity_key(name: str) -> str:
    n = name.upper().replace("&", " AND ")
    n = re.sub(r"\bINDS\b", "INDUSTRIES", n)
    n = re.sub(r"[^A-Z0-9]", "", n)
    n = _SUFFIX_PVT.sub("PVTLTD", n)
    return _SUFFIX_LTD.sub("LTD", n)


def _compact(name: str) -> str:
    """Letters and digits only, with "&" read as AND; no suffix normalisation."""
    return re.sub(r"[^A-Z0-9]", "", name.upper().replace("&", " AND "))


def clean_display(name: str) -> str:
    """Tidy spacing artefacts without changing the words."""
    n = " ".join(name.upper().split())
    n = re.sub(r"\bLI MITED\b", "LIMITED", n)
    n = re.sub(r"\bL TD\b", "LTD", n)
    n = re.sub(r"\bL L P\b", "LLP", n)
    return n


def resolve(name_counts: Counter) -> dict[str, str]:
    """Map each raw name -> canonical display name."""
    groups: dict[str, list[str]] = defaultdict(list)
    for raw in name_counts:
        groups[entity_key(raw)].append(raw)

    keys = sorted(groups)
    # Truncation is checked on the raw letters, before legal suffixes are normalised:
    # "...SERVICES PR" is a cut-off "...SERVICES PRIVATE LIMITED", but not a prefix of "...SERVICESPVTLTD".
    compact = {k: {_compact(r) for r in groups[k]} for k in keys}
    merged_into: dict[str, str] = {}
    for key in keys:
        shortest = min(groups[key], key=len)
        if len(shortest) < TRUNCATION_MIN_LEN:
            continue
        short = _compact(shortest)
        longer = [
            k for k in keys
            if k != key
            and any(c != short and c.startswith(short) for c in compact[k])
            and not any(r.rstrip().endswith("HUF") for r in groups[k])
        ]
        if len(longer) == 1:
            merged_into[key] = longer[0]

    def root(key: str) -> str:
        while key in merged_into:
            key = merged_into[key]
        return key

    clusters: dict[str, list[str]] = defaultdict(list)
    for key, raws in groups.items():
        clusters[root(key)].extend(raws)

    mapping = {}
    for raws in clusters.values():
        # Most-used spelling, but never a truncated one when a fuller spelling exists
        longest_key = max(len(entity_key(r)) for r in raws)
        full = [r for r in raws if len(entity_key(r)) == longest_key]
        display = clean_display(max(full, key=lambda r: name_counts[r]))
        for raw in raws:
            mapping[raw] = display
    return mapping
