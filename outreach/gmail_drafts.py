"""Optional. If GMAIL_ENABLED=true and credentials are configured, pitch
drafts land directly in Collin's Gmail Drafts folder instead of markdown
files — nothing this module does can send an email, drafts.create only
ever creates an unsent draft.

One-time setup (do this locally, not in CI):
  1. Create a Google Cloud project, enable the Gmail API, create an OAuth
     Client ID (type "Desktop app"), download it as client_secret.json
     into this outreach/ folder.
  2. Run:  python outreach/gmail_drafts.py --authorize
     This opens a browser for one-time consent (scope: gmail.compose only —
     it cannot read or send mail, only create drafts) and prints a token
     JSON blob.
  3. Put that blob in .env as GMAIL_TOKEN_JSON (or as a GitHub secret of
     the same name for the scheduled workflow), and set GMAIL_ENABLED=true.

Tokens can expire if left unused or revoked in your Google account — if
draft creation starts failing with an auth error, redo step 2.
"""

import base64
import json
import os
from email.mime.text import MIMEText

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.compose"]


def _load_credentials() -> Credentials:
    token_json = os.environ["GMAIL_TOKEN_JSON"]
    creds = Credentials.from_authorized_user_info(json.loads(token_json), SCOPES)
    if creds.expired and creds.refresh_token:
        creds.refresh(Request())
    return creds


def create_draft(to: str, subject: str, body: str) -> str:
    creds = _load_credentials()
    service = build("gmail", "v1", credentials=creds)

    message = MIMEText(body)
    message["to"] = to
    message["subject"] = subject
    raw = base64.urlsafe_b64encode(message.as_bytes()).decode()

    draft = service.users().drafts().create(userId="me", body={"message": {"raw": raw}}).execute()
    return f"gmail draft {draft['id']}"


def _authorize_locally() -> None:
    flow = InstalledAppFlow.from_client_secrets_file("outreach/client_secret.json", SCOPES)
    creds = flow.run_local_server(port=0)
    print("\nPaste this into .env as GMAIL_TOKEN_JSON (one line):\n")
    print(creds.to_json())


if __name__ == "__main__":
    import sys

    if "--authorize" in sys.argv:
        _authorize_locally()
    else:
        print("Run with --authorize to do the one-time local OAuth setup.")
