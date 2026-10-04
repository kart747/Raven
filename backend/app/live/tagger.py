"""
Links live headlines to Raven entities by exact phrase match on the headline only.

Conservative by design: MPs need a full name of two or more significant words that no other MP shares;
parties use a curated list of names and common abbreviations; purchasers use the same distinctive-name
rule as parliamentary questions; states use their canonical names. Indian-language names come from the
curated lists in `aliases.py`. A match means "named in the headline", nothing more.
"""
import re
import unicodedata
from collections import Counter

from .. import models
from ..import_member_terms import name_tokens
from ..import_questions import distinctive_name
from ..states import CANONICAL_STATES
from .aliases import MP_ALIASES, PARTY_ALIASES, STATE_ALIASES, STATE_DEMONYM_VOWELS

# Spelling variants that should compare equal: nukta (ड़/ड), chandrabindu (गाँधी/गांधी), zero-width joiners,
# and Malayalam chillu letters (ൺ) versus the older consonant + virama spelling (ണ്)
_FOLD = {**dict.fromkeys(map(ord, "़়਼઼଼಼‌‍")),
         0x0901: "ं",
         0x0d7a: "ണ്", 0x0d7b: "ന്", 0x0d7c: "ര്",
         0x0d7d: "ല്", 0x0d7e: "ള്", 0x0d7f: "ക്"}
# Latin letters and digits, and the Indic scripts from Devanagari to Malayalam (without the danda)
_WORD = re.compile(r"[a-z0-9ऀ-ॣ०-ൿ]+")


def normalise(text: str) -> str:
    text = unicodedata.normalize("NFC", (text or "").lower()).translate(_FOLD)
    return " " + " ".join(_WORD.findall(text)) + " "


class Tagger:
    def __init__(self, parties=(), mps=(), donors=(), states=CANONICAL_STATES):
        """parties: ids; mps: (id, name); donors: (id, name); states: canonical names."""
        self.exact: dict[str, list[tuple[str, str, str]]] = {}
        self.stems: dict[str, list[tuple[str, str, str]]] = {}
        party_ids = set(parties)
        for alias, pid in PARTY_ALIASES.items():
            if pid is None:
                self._add(alias, None)   # recognised so it can't match a shorter party name, but not tagged
            elif pid in party_ids:
                self._add(alias, ("party", pid, pid))

        mps = list(mps)
        keys = Counter(" ".join(sorted(name_tokens(n))) for _, n in mps)
        for mp_id, name in mps:
            tokens = [w for w in re.findall(r"[a-z]+", name.lower()) if w in name_tokens(name)]
            if len(tokens) >= 2 and keys[" ".join(sorted(name_tokens(name)))] == 1:
                self._add(" ".join(tokens), ("mp", str(mp_id), name))
        by_name = {n: i for i, n in mps}
        for alias, name in MP_ALIASES.items():
            if name in by_name:
                self._add(alias, ("mp", str(by_name[name]), name))

        for donor_id, name in donors:
            core = distinctive_name(name)
            if core:
                self._add(core.lower(), ("purchaser", str(donor_id), name))

        states = set(states)
        for state in states:
            self._add(state.lower(), ("state", state, state))
        for alias, state in STATE_ALIASES.items():
            if state in states:
                self._add(alias, ("state", state, state))

        alternatives = [(len(p), re.escape(p)) for p in self.exact]
        alternatives += [(len(s), re.escape(s) + "[^ ]*") for s in self.stems]
        alternatives.sort(key=lambda a: -a[0])   # longest first, so "trinamool congress" wins over "congress"
        self.pattern = re.compile(" (" + "|".join(a for _, a in alternatives) + ")(?= )") if alternatives else None
        self._stems_longest_first = sorted(self.stems, key=len, reverse=True)

    @classmethod
    def from_db(cls, db) -> "Tagger":
        return cls(parties=[p for (p,) in db.query(models.Party.id)],
                   mps=list(db.query(models.MPActivity.id, models.MPActivity.mp_name)),
                   donors=list(db.query(models.Donor.id, models.Donor.name)))

    def _add(self, phrase: str, entity: tuple[str, str, str] | None) -> None:
        stem = phrase.endswith("*")
        key = normalise(phrase.rstrip("*")).strip()
        if not key:
            return
        if stem:
            assert len(key) >= 4, f"stem too short to be safe: {phrase}"
        target = (self.stems if stem else self.exact).setdefault(key, [])
        if entity is not None:
            target.append(entity)

    def _entities(self, hit: str) -> list[tuple[str, str, str]]:
        if hit in self.exact:
            return self.exact[hit]
        for stem in self._stems_longest_first:
            if hit.startswith(stem):
                ending = hit[len(stem):]
                return [e for e in self.stems[stem] if not (e[0] == "state" and ending[:1] in STATE_DEMONYM_VOWELS)]
        return []

    def tag(self, title: str) -> list[tuple[str, str, str]]:
        if not self.pattern:
            return []
        text, found, pos = normalise(title), [], 0
        while m := self.pattern.search(text, pos):
            found.extend(self._entities(m.group(1)))
            pos = m.end()
        seen, out = set(), []
        for kind, ref, label in found:
            if (kind, ref) not in seen:
                seen.add((kind, ref))
                out.append((kind, ref, label))
        return out
