"""For every targets.csv row with status "ready", asks Claude to draft a short,
personalized outreach message sharing Selah with that media source.
Delivers the draft as a markdown file in outreach/drafts/. Nothing sends itself.
"""

import csv
from datetime import date
from pathlib import Path

from common.claude_client import call_fable_json

TARGETS_PATH = Path(__file__).parent / "targets.csv"
DRAFTS_DIR = Path(__file__).parent / "drafts"
FIELDNAMES = ["name", "type", "description", "link", "contact_email", "status", "discovered_date", "drafted_date", "notes"]

PITCH_SYSTEM_PROMPT = """You write short, personalized outreach messages for Selah, \
a minimal, silence-first, non-gamified Bible reading app for men.

Context: Selah is a free iOS app. No streaks, no badges, no push notifications. \
Just the Bible text and a moment of silence before each reading. Built for men \
who want to read Scripture without their phone fighting for their attention. \
App Store link: https://apps.apple.com/us/app/selah-daily-bible/id6798871785

You are reaching out to Christian media sources — podcasts, blogs, newsletters, \
influencers, churches — to let them know Selah exists and offer them a look at it. \
You are NOT asking to be a guest on their show. You are sharing a product that \
their audience would genuinely benefit from.

Rules:
- 80-120 words. No generic PR-speak, no "I hope this finds you well."
- Reference the specific source by name and something specific about their \
  focus or audience — this must not read as a mass email.
- Ask plainly: would they be open to checking out Selah and sharing it with \
  their audience if they think it fits? Offer to send more info or a promo code.
- Warm but brief. One short paragraph of context, one short paragraph of ask.
- Never invent download numbers, user counts, or quotes from reviews.
- Sign off as "Collin Lorenz" (the builder of Selah).

Respond with ONLY valid JSON: {"subject": "...", "body": "..."}"""


def _load_targets() -> list[dict]:
    with open(TARGETS_PATH, newline="") as f:
        return list(csv.DictReader(f))


def _save_targets(rows: list[dict]) -> None:
    with open(TARGETS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def draft_pending_pitches(create_draft_fn) -> int:
    """create_draft_fn(to, subject, body) -> str describing where the draft landed.
    Passed in so this module doesn't need to know if it's Gmail or a markdown file."""
    rows = _load_targets()
    drafted = 0

    for row in rows:
        if row["status"] != "ready":
            continue

        pitch = call_fable_json(
            PITCH_SYSTEM_PROMPT,
            f"Target: {row['name']} ({row['type']})\nDescription: {row['description']}\nLink: {row['link']}",
        )
        location = create_draft_fn(row["contact_email"], pitch["subject"], pitch["body"])

        row["status"] = "drafted"
        row["drafted_date"] = date.today().isoformat()
        row["notes"] = (row["notes"] + f" | draft: {location}").strip(" |")
        drafted += 1
        print(f"Drafted pitch to {row['name']} -> {location}")

    _save_targets(rows)
    return drafted


def markdown_draft(to: str, subject: str, body: str) -> str:
    """Fallback when Gmail isn't configured: writes the draft to a file for manual send."""
    DRAFTS_DIR.mkdir(exist_ok=True)
    label = to or subject
    safe_name = "".join(c if c.isalnum() else "-" for c in label)[:60]
    path = DRAFTS_DIR / f"{date.today().isoformat()}-{safe_name}.md"
    path.write_text(f"To: {to}\nSubject: {subject}\n\n{body}\n")
    return str(path)
