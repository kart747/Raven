"""
Answer a few questions from a Raven data release, using only the Python standard library.

    # a release folder (GitHub Releases, or `python -m app.cli export-release`)
    python examples/quickstart.py path/to/raven-YYYY-MM-DD

Every number printed here comes straight from the release CSVs; see manifest.json for sources and caveats.
"""
import csv
import gzip
import json
import os
import sys
from collections import Counter, defaultdict


def rows(release: str, table: str):
    with gzip.open(os.path.join(release, f"{table}.csv.gz"), "rt", encoding="utf-8", newline="") as f:
        yield from csv.DictReader(f)


def crore(x: float) -> str:
    return f"₹{x / 1e7:,.0f} Cr"


def main(release: str) -> None:
    manifest = json.load(open(os.path.join(release, "manifest.json"), encoding="utf-8"))
    print(manifest["name"], "\n")

    parties = {r["id"]: r["name"] for r in rows(release, "parties")}
    donors = {r["id"]: r["name"] for r in rows(release, "donors")}

    # 1. Which parties received the most electoral bond money, and from whom?
    by_party, by_pair = Counter(), Counter()
    for d in rows(release, "donations"):
        if d["funding_type"] != "Electoral Bond":
            continue
        amount = float(d["amount"])
        by_party[d["party_id"]] += amount
        by_pair[(d["party_id"], d["donor_id"])] += amount
    print("Electoral bonds received (top 5 parties)")
    for pid, amount in by_party.most_common(5):
        # "UNKNOWN DONOR" holds bonds bought before Apr 2019, whose purchaser the disclosure doesn't name
        top = max((v, k[1]) for k, v in by_pair.items() if k[0] == pid and donors[k[1]] != "UNKNOWN DONOR")
        print(f"  {parties.get(pid, pid):<35} {crore(amount):>12}   largest identified purchaser: {donors[top[1]]}")

    # 2. Share of 2024 MPs who declared pending criminal cases, by party
    mps = [c for c in rows(release, "candidates") if c["election"] == "Lok Sabha 2024" and c["is_winner"] in ("1", "True", "true")]
    with_cases = defaultdict(lambda: [0, 0])
    for c in mps:
        with_cases[c["party_id"]][1] += 1
        with_cases[c["party_id"]][0] += int(c["criminal_cases"]) > 0
    print(f"\nLok Sabha 2024 winners: {len(mps)}  (cases are pending cases declared in affidavits, not convictions)")
    for pid, (k, n) in sorted(with_cases.items(), key=lambda x: -x[1][1])[:6]:
        print(f"  {parties.get(pid, pid):<35} {k:>3} of {n:<3} declared cases ({100 * k / n:.0f}%)")

    # 3. Which ministries did the 18th Lok Sabha ask about most?
    ministries = Counter(q["ministry"] for q in rows(release, "parliament_questions") if q["lok_sabha"] == "18")
    if ministries:
        print("\nMost-questioned ministries, 18th Lok Sabha")
        for m, n in ministries.most_common(5):
            print(f"  {m:<45} {n:>5}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    main(sys.argv[1])
