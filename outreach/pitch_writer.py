"""For every targets.csv row with status "ready" (meaning Collin has added
a contact_email — see README), asks Fable to draft a short, specific pitch.
Delivers the draft as a real Gmail draft if configured, otherwise as a
markdown file in outreach/drafts/. Either way, nothing sends itself.
"""

import csv
from datetime import date
from pathlib import Path

from common.claude_client import call_fable_json

TARGETS_PATH = Path(__file__).parent / "targets.csv"
DRAFTS_DIR = Path(__file__).parent / "drafts"
FIELDNAMES = ["name", "type", "description", "link", "contact_email", "status", "discovered_date", "drafted_date", "notes"]

PITCH_SYSTEM_PROMPT = """You write short, specific outreach pitches for Selah, \
a minimal, silence-first, non-gamified Bible reading app for men, to podcast \
hosts and newsletter writers in Christian / men's ministry spaces.

Rules:
- 100-150 words. No generic PR-speak, no "I hope this finds you well."
- Reference the specific show/newsletter by name and something specific \
  about its description or focus — this must not read as a form letter.
- State plainly what you're asking for: a mention, a review copy, or being \
  a guest to talk about building a distraction-free Bible reading habit — \
  pick whichever fits the target's description best.
- Warm but brief. End with a low-pressure, specific ask (not "let me know!").
- Never invent download numbers, user counts, or quotes from reviews.

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
    path.write_text(f"To: {to}\nSubject: {subject}\n\n{body}\n")
    return str(path)
