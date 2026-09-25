"""Generates POSTS_PER_DAY posts in one run, picking topics off the queue.
Brainstorms more topics itself once the queue runs low, so this doesn't
need Collin to keep feeding it ideas — but the brainstorm prompt is
explicit about needing genuinely distinct angles, not reworded duplicates,
since that's exactly the pattern Google's scaled-content-abuse policy
targets (see README)."""

import json
import re
from datetime import date
from pathlib import Path

from common.claude_client import call_fable_json

TOPICS_PATH = Path(__file__).parent / "topics.json"
POSTS_DIR = Path(__file__).parent / "posts"

WRITE_SYSTEM_PROMPT = """You write SEO-minded blog content for Selah, a minimal, \
silence-first Bible reading app for men. Selah is deliberately non-gamified — no \
streaks, no badges — positioned against gamified Bible apps. Its tone is calm, \
direct, and substantive, never preachy or salesy.

Write a complete blog post for the given title and target keyword. It should:
- Genuinely help the reader (practical, specific, no filler) — the keyword \
  target should feel natural, not stuffed.
- Run 500-800 words.
- Mention Selah naturally once or twice, not as a hard sell.
- Use short paragraphs and subheadings (as markdown ##).
- Avoid making up statistics, studies, or quotes you can't back up.
- Take a genuinely distinct angle from a generic "how to read your Bible" \
  post — a specific situation, question, or tension, not a listicle that \
  could describe any Bible-reading app.

Respond with ONLY valid JSON:
{"title": "...", "meta_description": "...(under 155 chars)...",
 "slug": "url-safe-slug", "body_markdown": "## Subheading\\n\\ncontent..."}"""

BRAINSTORM_SYSTEM_PROMPT = """You generate blog topic ideas for Selah, a \
minimal, non-gamified, silence-first Bible reading app for men. Ideas should \
target real search intent (things men actually search for around Bible \
reading, quiet time, spiritual discipline, distraction, fatherhood + faith, \
prayer, specific books of the Bible) without being generic.

Each topic must represent a genuinely distinct angle or reader situation —
not a reworded version of an already-covered title (e.g. don't submit
"5 Tips for a Better Quiet Time" if "Quiet Time Ideas for Men" already
exists — that's the same page wearing a different headline, and is exactly
the kind of thin, templated variation that gets a site penalized for scaled
content abuse rather than helping it rank). If you can't think of enough
genuinely distinct angles, return fewer than requested rather than padding
with near-duplicates.

Respond with ONLY valid JSON: {"topics": [{"title": "...", "keyword": "..."}]}"""


def _load_state() -> dict:
    return json.loads(TOPICS_PATH.read_text())


def _save_state(state: dict) -> None:
    TOPICS_PATH.write_text(json.dumps(state, indent=2))


def _slugify(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def _ensure_queue_depth(state: dict, needed: int) -> None:
    if len(state["queue"]) >= needed:
        return
    print(f"Topic queue low ({len(state['queue'])} left) — asking Fable to brainstorm more...")
    covered = [p["title"] for p in state["published"]] + [t["title"] for t in state["queue"]]
    result = call_fable_json(
        BRAINSTORM_SYSTEM_PROMPT,
        json.dumps({"already_covered": covered, "count_needed": max(15, needed * 3)}),
    )
    new_topics = result["topics"]
    state["queue"].extend(new_topics)
    _save_state(state)
    if len(state["queue"]) < needed:
        print(
            f"Fable could only find {len(state['queue'])} genuinely distinct topic(s) — "
            "generating fewer posts this run rather than padding with near-duplicates."
        )


def _generate_one(state: dict) -> dict:
    topic = state["queue"].pop(0)
    print(f"Generating post: {topic['title']}")
    post = call_fable_json(WRITE_SYSTEM_PROMPT, json.dumps(topic))

    post["date"] = date.today().isoformat()
    post["keyword"] = topic.get("keyword", "")

    POSTS_DIR.mkdir(exist_ok=True)
    (POSTS_DIR / f"{post['slug']}.json").write_text(json.dumps(post, indent=2))

    state["published"].append({"title": topic["title"], "slug": post["slug"], "date": post["date"]})
    _save_state(state)
    return post


def generate_posts(count: int) -> list[dict]:
    """Generates up to `count` posts. May return fewer if Fable can't find
    that many genuinely distinct topics — see _ensure_queue_depth."""
    state = _load_state()
    _ensure_queue_depth(state, count)

    n = min(count, len(state["queue"]))
    return [_generate_one(state) for _ in range(n)]
