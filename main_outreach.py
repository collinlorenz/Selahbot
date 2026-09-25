import os

from dotenv import load_dotenv

load_dotenv()

from outreach.podcast_discovery import discover
from outreach.pitch_writer import draft_pending_pitches, markdown_draft


def run() -> None:
    added = discover()
    print(f"Discovery: {added} new candidate(s) added to targets.csv (status=candidate).")
    print("Add a contact_email and set status to 'ready' on any you want pitched.")

    if os.environ.get("GMAIL_ENABLED", "false").lower() == "true":
        from outreach.gmail_drafts import create_draft

        create_fn = create_draft
    else:
        create_fn = markdown_draft

    drafted = draft_pending_pitches(create_fn)
    print(f"Drafting: {drafted} pitch(es) drafted for rows marked 'ready'.")


if __name__ == "__main__":
    run()
