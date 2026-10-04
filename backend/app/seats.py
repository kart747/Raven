"""Lok Sabha seat name crosswalk between sources (DataMeet / Lok Sabha records / MyNeta)."""
import re

# Same seat, different spelling across sources: (state, normalised alternative name) -> MyNeta name
SEAT_ALIASES = {
    ("West Bengal", "bardhamandurgapur"): "Burdwan - Durgapur",
    ("Chhattisgarh", "janjgir"): "Janjgir-Champa (Sc)",
    ("Telangana", "bhuvanagiri"): "Bhongir",
    ("Karnataka", "belagavi"): "Belgaum",
}

# DataMeet's 2019 file names both Maharashtra PC 30 and 31 "Mumbai South"; per ECI numbering 30 is Mumbai South Central
SEAT_BY_NUMBER = {
    ("Maharashtra", 30): "Mumbai South - Central",
    ("Maharashtra", 31): "Mumbai South",
}

# Seats renamed and redrawn by later delimitations; 2008 boundaries don't describe the 2024 seat
REDRAWN = {"Assam": "2023 delimitation", "Jammu and Kashmir": "2022 delimitation"}


def seat_key(name: str | None) -> str:
    return re.sub(r"[^a-z]", "", re.sub(r"\((sc|st)\)", "", (name or "").lower()))


def alias(state: str, name: str | None) -> str | None:
    return SEAT_ALIASES.get((state, seat_key(name)))
