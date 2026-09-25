"""Runs daily and reports exactly what happened in the trailing 24 hours:
posts published, podcast candidates discovered, pitches drafted. Both bots
now also run daily, so an empty section here means something's actually
wrong (a failed run), not just "not their day yet."

This deliberately does NOT try to report install numbers or revenue — see
README for why that's a separate, harder problem. This is an activity log,
not a results dashboard.
"""

import csv
import json
import os
import smtplib
from datetime import date, timedelta
from email.message import EmailMessage
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from common.claude_client import call_fable_json

SUMMARY_SYSTEM_PROMPT = """You write a 2-3 sentence, plain-language summary \
at the top of a daily automation report for Selah, a Bible reading app. \
Be factual and specific about what did or didn't happen — don't pad or \
oversell quiet days. No marketing tone.

Respond with ONLY valid JSON: {"summary": "..."}"""


def _today_str() -> str:
    return date.today().isoformat()


def _seo_activity(today: str) -> list[dict]:
    topics_path = Path("seo/topics.json")
    if not topics_path.exists():
        return []
    state = json.loads(topics_path.read_text())
    return [p for p in state.get("published", []) if p.get("date") == today]


def _outreach_activity(today: str) -> tuple[list[dict], list[dict]]:
    targets_path = Path("outreach/targets.csv")
    if not targets_path.exists() or targets_path.stat().st_size == 0:
        return [], []
    with open(targets_path, newline="") as f:
        rows = list(csv.DictReader(f))
    discovered_today = [r for r in rows if r.get("discovered_date") == today]
    drafted_today = [r for r in rows if r.get("drafted_date") == today]
    return discovered_today, drafted_today


def build_report() -> str:
    today = _today_str()
    weekday = date.today().strftime("%A")

    new_posts = _seo_activity(today)
    discovered, drafted = _outreach_activity(today)

    lines = [f"# Selah Growth Bot — Daily Report — {today} ({weekday})", ""]

    activity_for_summary = {
        "posts_published": len(new_posts),
        "podcasts_discovered": len(discovered),
        "pitches_drafted": len(drafted),
    }
    summary = call_fable_json(
        SUMMARY_SYSTEM_PROMPT,
        json.dumps(activity_for_summary),
        max_tokens=300,
    )
    lines += [summary["summary"], ""]

    lines.append("## SEO blog")
    if new_posts:
        for p in new_posts:
            lines.append(f"- Published: **{p['title']}** (`/posts/{p['slug']}/`)")
    else:
        lines.append("⚠️ No new post today. Both bots run daily now — check the Actions tab for a failed run.")
    lines.append("")

    lines.append("## Podcast outreach")
    if discovered:
        lines.append(f"- {len(discovered)} new candidate(s) discovered, awaiting your review in `targets.csv`.")
    if drafted:
        for d in drafted:
            lines.append(f"- Pitch drafted for **{d['name']}** ({d['notes']})")
    if not discovered and not drafted:
        lines.append("⚠️ No new candidates or drafts today. Check the Actions tab for a failed run.")
    lines.append("")

    # Running totals, so the report is useful even on quiet days
    with open("outreach/targets.csv", newline="") as f:
        all_rows = list(csv.DictReader(f))
    status_counts = {}
    for r in all_rows:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    topics_state = json.loads(Path("seo/topics.json").read_text())

    lines.append("## Running totals")
    lines.append(f"- Blog posts published all-time: {len(topics_state.get('published', []))}")
    lines.append(f"- Topics still queued: {len(topics_state.get('queue', []))}")
    lines.append(f"- Outreach targets by status: {status_counts or 'none yet'}")
    lines.append(f"- Outreach candidates still needing a contact_email + review: {status_counts.get('candidate', 0)}")

    queue_days_left = len(topics_state.get("queue", [])) / max(int(os.environ.get("POSTS_PER_DAY", "3")), 1)
    if queue_days_left < 3:
        lines.append(
            f"- ⚠️ Topic queue is low (~{queue_days_left:.1f} days left at current pace) — "
            "Fable will lean harder on brainstorming fresh angles soon, worth skimming the next few posts for quality."
        )

    return "\n".join(lines)


def maybe_email_report(report: str) -> None:
    to_addr = os.environ.get("REPORT_EMAIL_TO", "").strip()
    if not to_addr:
        return
    msg = EmailMessage()
    msg["Subject"] = f"Selah growth bot — daily report — {_today_str()}"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = to_addr
    msg.set_content(report)
    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ.get("SMTP_PORT", 587))) as s:
        s.starttls()
        s.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        s.send_message(msg)


def run() -> None:
    report = build_report()
    print(report)

    reports_dir = Path("reports")
    reports_dir.mkdir(exist_ok=True)
    (reports_dir / f"{_today_str()}.md").write_text(report)

    maybe_email_report(report)


if __name__ == "__main__":
    run()
