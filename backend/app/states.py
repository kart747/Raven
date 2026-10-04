"""Canonical Indian state / UT names, shared by every importer so filters and the map line up."""

CANONICAL_STATES = [
    "Andaman and Nicobar Islands", "Andhra Pradesh", "Arunachal Pradesh", "Assam", "Bihar",
    "Chandigarh", "Chhattisgarh", "Dadra and Nagar Haveli and Daman and Diu", "Delhi", "Goa",
    "Gujarat", "Haryana", "Himachal Pradesh", "Jammu and Kashmir", "Jharkhand", "Karnataka",
    "Kerala", "Ladakh", "Lakshadweep", "Madhya Pradesh", "Maharashtra", "Manipur", "Meghalaya",
    "Mizoram", "Nagaland", "Odisha", "Puducherry", "Punjab", "Rajasthan", "Sikkim", "Tamil Nadu",
    "Telangana", "Tripura", "Uttar Pradesh", "Uttarakhand", "West Bengal",
]

_ALIASES = {
    "NEW DELHI": "Delhi",
    "NCT OF DELHI": "Delhi",
    "NATIONAL CAPITAL TERRITORY OF DELHI": "Delhi",
    "KERALAM": "Kerala",   # official name since 2026; Raven keeps "Kerala" so older datasets still join
    "DELHI (NCT)": "Delhi",
    "TAMILNADU": "Tamil Nadu",
    "WESTBENGAL": "West Bengal",
    "W.BENGAL": "West Bengal",
    "ANDHRAPRADESH": "Andhra Pradesh",
    "A.P.": "Andhra Pradesh",
    "UTTARPRADESH": "Uttar Pradesh",
    "U.P.": "Uttar Pradesh",
    "MADHYAPRADESH": "Madhya Pradesh",
    "M.P.": "Madhya Pradesh",
    "HIMACHALPRADESH": "Himachal Pradesh",
    "H.P.": "Himachal Pradesh",
    "ARUNACHALPRADESH": "Arunachal Pradesh",
    "J & K": "Jammu and Kashmir",
    "J&K": "Jammu and Kashmir",
    "ORISSA": "Odisha",
    "PONDICHERRY": "Puducherry",
    "UTTARANCHAL": "Uttarakhand",
    "CHATTISGARH": "Chhattisgarh",
    "ANDAMAN AND NICOBAR": "Andaman and Nicobar Islands",
    "DADRA AND NAGAR HAVELI": "Dadra and Nagar Haveli and Daman and Diu",
    "DAMAN AND DIU": "Dadra and Nagar Haveli and Daman and Diu",
    "DNH AND DD": "Dadra and Nagar Haveli and Daman and Diu",
}

_LOOKUP = {s.upper(): s for s in CANONICAL_STATES}


def canonical_state(raw: str | None) -> str:
    if not raw or not isinstance(raw, str):
        return "Unknown"
    key = " ".join(raw.replace("&", " AND ").upper().split())
    if key in _LOOKUP:
        return _LOOKUP[key]
    compact = raw.strip().upper()
    if compact in _ALIASES:
        return _ALIASES[compact]
    if key in _ALIASES:
        return _ALIASES[key]
    return raw.strip().title()
