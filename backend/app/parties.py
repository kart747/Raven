"""Canonical party reference data shared by the seeder and importers."""

# Internal party ID -> display name
PARTIES_MASTER: dict[str, str] = {
    "BJP":    "Bharatiya Janata Party",
    "INC":    "Indian National Congress",
    "AITC":   "All India Trinamool Congress",
    "BRS":    "Bharat Rashtra Samithi",
    "DMK":    "Dravida Munnetra Kazhagam",
    "YSRCP":  "YSR Congress Party",
    "TDP":    "Telugu Desam Party",
    "SHS":    "Shiv Sena",
    "AAP":    "Aam Aadmi Party",
    "NCP":    "Nationalist Congress Party",
    "SAD":    "Shiromani Akali Dal",
    "BJD":    "Biju Janata Dal",
    "RJD":    "Rashtriya Janata Dal",
    "JDS":    "Janata Dal (Secular)",
    "SKM":    "Sikkim Krantikari Morcha",
    "JSP":    "Janasena Party",
    "SP":     "Samajwadi Party",
    "JDU":    "Janata Dal (United)",
    "JMM":    "Jharkhand Mukti Morcha",
    "AIADMK": "All India Anna Dravida Munnetra Kazhagam",
    "SDF":    "Sikkim Democratic Front",
    "MGP":    "Maharashtrawadi Gomantak Party",
    "JKNC":   "Jammu and Kashmir National Conference",
    "GFP":    "Goa Forward Party",
    "AIMIM":  "All India Majlis-E-Ittehadul Muslimeen",
    "RSP":    "Revolutionary Socialist Party",
    "BSP":    "Bahujan Samaj Party",
}

# Party account names as they appear in the SBI/ECI redemption disclosure -> party ID.
# Lookups should go through normalize_party_name() so spacing variants still match.
_DISCLOSURE_NAME_TO_ID: dict[str, str] = {
    "BHARATIYA JANATA PARTY":                                     "BJP",
    "BHARTIYA JANTA PARTY":                                       "BJP",
    "PRESIDENT, ALL INDIA CONGRESS COMMITTEE":                    "INC",
    "ALL INDIA TRINAMOOL CONGRESS":                               "AITC",
    "BHARAT RASHTRA SAMITHI":                                     "BRS",
    "BIJU JANATA DAL":                                            "BJD",
    "DRAVIDA MUNNETRA KAZHAGAM (DMK)":                            "DMK",
    "DMK PARTY IN PARLIAMENT":                                    "DMK",
    "YSR CONGRESS PARTY (YUVAJANA SRAMIKA RYTHU CONGRESS PARTY)": "YSRCP",
    "TELUGU DESAM PARTY":                                         "TDP",
    "SHIVSENA":                                                   "SHS",
    "SHIVSENA (POLITICAL PARTY)":                                 "SHS",
    "RASHTRIYA JANTA DAL":                                        "RJD",
    "RASTRIYA JANTA DAL":                                         "RJD",
    "AAM AADMI PARTY":                                            "AAP",
    "JANATA DAL ( SECULAR )":                                     "JDS",
    "SIKKIM KRANTIKARI MORCHA":                                   "SKM",
    "NATIONALIST CONGRESS PARTY MAHARASHTRA PRADESH":             "NCP",
    "NATIONALIST CONGRESS PARTY PARLIAMENT OF":                   "NCP",
    "JANASENA PARTY":                                             "JSP",
    "ADYAKSHA SAMAJVADI PARTY":                                   "SP",
    "BIHAR PRADESH JANTA DAL(UNITED)":                            "JDU",
    "JHARKHAND MUKTI MORCHA":                                     "JMM",
    "SHIROMANI AKALI DAL":                                        "SAD",
    "ALL INDIA ANNA DRAVIDA MUNNETRA KAZHAGAM":                   "AIADMK",
    "SIKKIM DEMOCRATIC FRONT":                                    "SDF",
    "MAHARASHTRAWADI GOMNTAK PARTY":                              "MGP",
    "JAMMU AND KASHMIR NATIONAL CONFERENCE":                      "JKNC",
    "GOA FORWARD PARTY":                                          "GFP",
}


def normalize_party_name(raw: str) -> str:
    return " ".join(raw.upper().split())


PARTY_NAME_TO_ID: dict[str, str] = {
    normalize_party_name(name): pid for name, pid in _DISCLOSURE_NAME_TO_ID.items()
}


def party_id_for(raw_name: str) -> str | None:
    return PARTY_NAME_TO_ID.get(normalize_party_name(raw_name))
