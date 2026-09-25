"""Finds candidate podcasts via Apple's public iTunes Search API (no auth
needed — this is the same API that powers App Store search). Appends new,
deduplicated candidates to targets.csv with status "candidate" and no
contact_email.

Deliberately does NOT try to scrape or guess contact emails. Finding the
right person to pitch is a judgment call — a host's "contact" page, a
show's producer, a network's PR inbox all differ — so that step stays
manual. Fill in contact_email and change status to "ready" once you've
found and want to pitch that contact.
"""

import csv
from datetime import date
from pathlib import Path

import requests

TARGETS_PATH = Path(__file__).parent / "targets.csv"
FIELDNAMES = ["name", "type", "description", "link", "contact_email", "status", "discovered_date", "drafted_date", "notes"]

SEARCH_TERMS = [
    "christian men bible study podcast",
    "men's devotional podcast",
    "daily bible reading podcast for men",
    "christian fatherhood podcast",
    "men's discipleship podcast",
    "christian men's ministry podcast",
    "bible study podcast for men",
    "men's bible reading plan podcast",
    "christian dad podcast",
    "faith and manhood podcast",
    "christian men's group podcast",
    "biblical manhood podcast",
    "men's morning devotional podcast",
    "husband and father bible podcast",
    "christian men's accountability podcast",
    "men's prayer podcast",
    "daily devotional podcast men",
    "christian leadership podcast for men",
    "scripture and manhood podcast",
    "men's faith and family podcast",
]


def _load_targets() -> list[dict]:
    if not TARGETS_PATH.exists() or TARGETS_PATH.stat().st_size == 0:
        return []
    with open(TARGETS_PATH, newline="") as f:
        return list(csv.DictReader(f))


def _save_targets(rows: list[dict]) -> None:
    with open(TARGETS_PATH, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)
        writer.writeheader()
        writer.writerows(rows)


def discover(limit_per_term: int = 15) -> int:
    existing = _load_targets()
    known_links = {row["link"] for row in existing}
    added = 0

    for term in SEARCH_TERMS:
        resp = requests.get(
            "https://itunes.apple.com/search",
            params={"term": term, "media": "podcast", "limit": limit_per_term},
            timeout=20,
        )
        resp.raise_for_status()
        for result in resp.json().get("results", []):
            link = result.get("collectionViewUrl", "")
            if not link or link in known_links:
                continue
            description = f"Hosted by {result.get('artistName', 'unknown')} — {result.get('primaryGenreName', '')}"
            existing.append(
                {
                    "name": result.get("collectionName", ""),
                    "type": "podcast",
                    "description": description,
                    "link": link,
                    "contact_email": "",
                    "status": "candidate",
                    "discovered_date": date.today().isoformat(),
                    "drafted_date": "",
                    "notes": "",
                }
            )
            known_links.add(link)
            added += 1

    _save_targets(existing)
    return added


if __name__ == "__main__":
    n = discover()
    print(f"Added {n} new candidate(s) to targets.csv")
