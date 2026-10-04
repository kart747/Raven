"""
Links live headlines to Raven entities by exact phrase match on the headline only.

Conservative by design: MPs need a full name of two or more significant words that no other MP shares;
parties use a curated list of names and common abbreviations; purchasers use the same distinctive-name
rule as parliamentary questions; states use their canonical names. A match means "named in the headline",
nothing more.
"""
import re
from collections import Counter

from .. import models
from ..import_member_terms import name_tokens
from ..import_questions import distinctive_name
from ..states import CANONICAL_STATES

# Party names / abbreviations as they appear in Indian headlines -> Raven party id
PARTY_ALIASES = {
    "bjp": "BJP", "bharatiya janata party": "BJP",
    "congress": "INC", "indian national congress": "INC",
    "aap": "AAP", "aam aadmi party": "AAP",
    "tmc": "AITC", "trinamool": "AITC", "trinamool congress": "AITC",
    "samajwadi party": "SP", "akhilesh yadav's sp": "SP",
    "dmk": "DMK", "aiadmk": "AIADMK",
    "tdp": "TDP", "telugu desam": "TDP",
    "jdu": "JDU", "jd u": "JDU", "janata dal united": "JDU",
    "rjd": "RJD", "rashtriya janata dal": "RJD",
    "bjd": "BJD", "biju janata dal": "BJD",
    "ysrcp": "YSRCP", "ysr congress": "YSRCP",
    "brs": "BRS", "bharat rashtra samithi": "BRS",
    "bsp": "BSP", "bahujan samaj party": "BSP",
    "jmm": "JMM", "jharkhand mukti morcha": "JMM",
    "aimim": "AIMIM", "shiromani akali dal": "SAD", "akali dal": "SAD",
    "shiv sena ubt": "SS(UBT)", "sena ubt": "SS(UBT)",
    "ncp sp": "NCP(SP)", "ncp sharadchandra pawar": "NCP(SP)",
    "cpi m": "CPI(M)", "cpm": "CPI(M)",
}


# How headlines commonly refer to particular MPs: alias -> exact MP name (matched to the record, never guessed)
MP_ALIASES = {
    "pm modi": "Narendra Modi",
    "prime minister modi": "Narendra Modi",
    "prime minister narendra modi": "Narendra Modi",
}


def normalise(text: str) -> str:
    return " " + " ".join(re.findall(r"[a-z0-9]+", (text or "").lower())) + " "


class Tagger:
    def __init__(self, db):
        self.phrases: dict[str, list[tuple[str, str, str]]] = {}
        party_ids = {p for (p,) in db.query(models.Party.id)}
        for alias, pid in PARTY_ALIASES.items():
            if pid in party_ids:
                self._add(alias, "party", pid, pid)

        mps = list(db.query(models.MPActivity.id, models.MPActivity.mp_name))
        keys = Counter(" ".join(sorted(name_tokens(n))) for _, n in mps)
        for mp_id, name in mps:
            tokens = [w for w in re.findall(r"[a-z]+", name.lower()) if w in name_tokens(name)]
            if len(tokens) >= 2 and keys[" ".join(sorted(name_tokens(name)))] == 1:
                self._add(" ".join(tokens), "mp", str(mp_id), name)

        by_name = {n: i for i, n in mps}
        for alias, name in MP_ALIASES.items():
            if name in by_name:
                self._add(alias, "mp", str(by_name[name]), name)

        for donor_id, name in db.query(models.Donor.id, models.Donor.name):
            core = distinctive_name(name)
            if core:
                self._add(core.lower(), "purchaser", str(donor_id), name)

        for state in CANONICAL_STATES:
            self._add(state.lower(), "state", state, state)

        alternation = "|".join(re.escape(p) for p in sorted(self.phrases, key=len, reverse=True))
        self.pattern = re.compile(rf" ({alternation}) ") if self.phrases else None

    def _add(self, phrase: str, kind: str, ref: str, label: str) -> None:
        key = normalise(phrase).strip()
        if key:
            self.phrases.setdefault(key, []).append((kind, ref, label))

    def tag(self, title: str) -> list[tuple[str, str, str]]:
        if not self.pattern:
            return []
        text, found, pos = normalise(title), [], 0
        while True:
            m = self.pattern.search(text, pos)
            if not m:
                break
            found.extend(self.phrases[m.group(1)])
            pos = m.end() - 1   # allow the next phrase to reuse the separating space
        seen, out = set(), []
        for kind, ref, label in found:
            if (kind, ref) not in seen:
                seen.add((kind, ref))
                out.append((kind, ref, label))
        return out
