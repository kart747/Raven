import json
import logging
import os

import requests
from sqlalchemy import func

from .database import SessionLocal
from . import models, crud
from .pib_ingest import get_cached_pib_releases

logger = logging.getLogger(__name__)

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL = os.environ.get("GROQ_MODEL", "openai/gpt-oss-120b")

SOURCES = [
    {"name": "SBI electoral bond disclosure (ECI, Mar 2024)", "url": "https://www.eci.gov.in/disclosure-of-electoral-bonds"},
    {"name": "FCRA annual returns (MHA)", "url": "https://fcraonline.nic.in"},
    {"name": "Press Information Bureau RSS", "url": "https://pib.gov.in"},
    {"name": "Lok Sabha activity (Vonter dataset)", "url": "https://github.com/Vonter/india-representatives-activity"},
]


def _crore(amount) -> str:
    return f"₹{(amount or 0) / 1e7:,.2f} Cr"


def build_context(db) -> str:
    """Collect only the figures we hold; the model is told to use nothing else."""
    bond_count, bond_total = db.query(
        func.count(models.Donation.id), func.coalesce(func.sum(models.Donation.amount), 0.0)
    ).filter(models.Donation.funding_type == "Electoral Bond").one()

    unknown_total = db.query(func.coalesce(func.sum(models.Donation.amount), 0.0))\
        .join(models.Donor, models.Donor.id == models.Donation.donor_id)\
        .filter(models.Donation.funding_type == "Electoral Bond", models.Donor.name == "UNKNOWN DONOR")\
        .scalar()

    parties = [
        f"- {p['name']}: {_crore(p['total_donations'])} ({p['donation_count']} bonds)"
        for p in crud.get_parties(db)[:10] if p["donation_count"]
    ]
    top_donors = [
        f"- {d['name']}: {_crore(d['total_donated'])}"
        for d in crud.get_dashboard_stats(db)["top_donors"] if d["name"] != "UNKNOWN DONOR"
    ][:10]

    ngo_years = db.query(
        models.NGODonation.year, func.sum(models.NGODonation.amount), func.count(func.distinct(models.NGODonation.ngo_id))
    ).group_by(models.NGODonation.year).order_by(models.NGODonation.year).all()
    ngo_total, ngo_unique = db.query(
        func.coalesce(func.sum(models.NGODonation.amount), 0.0), func.count(func.distinct(models.NGODonation.ngo_id))
    ).one()
    ngo_lines = [f"- All years combined: {_crore(ngo_total)} received by {ngo_unique} unique NGOs"] + [
        f"- FY{yr}-{(yr + 1) % 100:02d}: {_crore(amt)} received by {n} NGOs" for yr, amt, n in ngo_years
    ]

    try:
        pib = [f"- {r['title']} ({r['published_at']:%Y-%m-%d})" for r in get_cached_pib_releases(6, 3)[:10]]
    except Exception:
        pib = ["- (PIB feed unavailable)"]

    bills, _ = crud.get_legislative_bills(db, limit=10)
    bill_lines = [f"- {b['bill_title']} — {b['introduced_by']} ({b['current_status']})" for b in bills]

    return f"""ELECTORAL BONDS (encashed Apr 2019 – Feb 2024, matched to purchasers by bond number):
- Bonds: {bond_count}, total {_crore(bond_total)}
- Of which purchaser not disclosed (bought before Apr 2019): {_crore(unknown_total)}
Top receiving parties:
{chr(10).join(parties) or "- none loaded"}
Top identified purchasers:
{chr(10).join(top_donors) or "- none loaded"}

NGO FOREIGN CONTRIBUTIONS (FCRA annual returns, by fiscal year):
{chr(10).join(ngo_lines) or "- none loaded"}

RECENT PIB PRESS RELEASES:
{chr(10).join(pib)}

RECENT PRIVATE MEMBER BILLS (18th Lok Sabha):
{chr(10).join(bill_lines) or "- none loaded"}
"""


PROMPT = """Write a short, neutral data brief from the CONTEXT below.

Rules:
- Use ONLY numbers and facts present in CONTEXT, copied exactly. Do not add, sum, or derive new figures.
- Do not add outside knowledge, motives, or speculation.
- If a section has no data, say "No data loaded." for it.
- Do not characterise any party, person, or organisation; report figures only.

Sections (markdown):
## Summary
## Electoral Bonds
## NGO Foreign Contributions
## Government Press Releases & Bills

CONTEXT:
{context}"""


def generate_and_save_weekly_brief():
    """Generate a brief and store it. On failure the previous brief stays in place."""
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        logger.warning("GROQ_API_KEY not set; skipping brief generation.")
        return

    db = SessionLocal()
    try:
        context = build_context(db)
        response = requests.post(
            GROQ_URL,
            headers={"Authorization": f"Bearer {api_key}"},
            json={
                "model": GROQ_MODEL,
                "messages": [
                    {"role": "system", "content": "You summarise datasets factually and never add information that is not provided."},
                    {"role": "user", "content": PROMPT.format(context=context)},
                ],
                "temperature": 0.2,
                "max_tokens": 4000,
            },
            timeout=60,
        )
        response.raise_for_status()
        brief_text = response.json()["choices"][0]["message"]["content"]

        db.add(models.WeeklyBrief(
            brief_text=brief_text,
            # Keep the exact figures the model saw so readers can check the brief against them
            source_citation=json.dumps({"sources": SOURCES, "input_data": context, "model": GROQ_MODEL}),
        ))
        db.commit()
        logger.info("Brief generated and saved.")
    except Exception:
        logger.exception("Brief generation failed; keeping previous brief.")
    finally:
        db.close()
