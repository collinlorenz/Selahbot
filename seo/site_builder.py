"""Builds the static site from every post JSON file in seo/posts/. Safe to
re-run — it regenerates the whole site/ folder from source each time, so
there's no drift between the posts and the rendered pages."""

import json
from pathlib import Path

import markdown as md
from jinja2 import Template

SEO_DIR = Path(__file__).parent
POSTS_DIR = SEO_DIR / "posts"
SITE_DIR = SEO_DIR / "site"
TEMPLATE_PATH = SEO_DIR / "template.html"

INDEX_TEMPLATE = Template("""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Selah Blog</title>
<meta name="description" content="Practical writing on Bible reading habits, quiet time, and distraction-free faith.">
<style>
 body { font-family: -apple-system, Georgia, serif; max-width: 640px; margin: 3rem auto; padding: 0 1.25rem; color: #1c1c1c; }
 li { margin-bottom: 1rem; }
 a { color: #1c1c1c; }
</style></head><body>
<h1>Selah Blog</h1>
<ul>
{% for post in posts %}
  <li><a href="/posts/{{ post.slug }}/">{{ post.title }}</a><br><small>{{ post.date }}</small></li>
{% endfor %}
</ul>
</body></html>
""")

SITEMAP_TEMPLATE = Template("""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
<url><loc>{{ site_url }}/</loc></url>
{% for post in posts %}<url><loc>{{ site_url }}/posts/{{ post.slug }}/</loc><lastmod>{{ post.date }}</lastmod></url>
{% endfor %}
</urlset>
""")


def _related_posts(post: dict, all_posts: list[dict], n: int = 3) -> list[dict]:
    """Simple keyword-overlap heuristic — good enough for a handful of related
    links, no need for real embeddings here. Falls back to most-recent-other
    posts if there isn't enough keyword overlap to fill n slots."""
    words = set(post.get("keyword", "").lower().split())
    others = [p for p in all_posts if p["slug"] != post["slug"]]

    def overlap(p):
        return len(words & set(p.get("keyword", "").lower().split()))

    others.sort(key=lambda p: (-overlap(p), all_posts.index(p)))
    return others[:n]


def build(site_url: str, app_store_url: str) -> int:
    post_template = Template(TEMPLATE_PATH.read_text())
    posts = sorted(
        (json.loads(p.read_text()) for p in POSTS_DIR.glob("*.json")),
        key=lambda p: p["date"],
        reverse=True,
    )

    SITE_DIR.mkdir(exist_ok=True)
    for post in posts:
        post_dir = SITE_DIR / "posts" / post["slug"]
        post_dir.mkdir(parents=True, exist_ok=True)
        body_html = md.markdown(post["body_markdown"])
        html = post_template.render(
            title=post["title"],
            meta_description=post["meta_description"],
            slug=post["slug"],
            date=post["date"],
            body_html=body_html,
            site_url=site_url,
            app_store_url=app_store_url,
            related=_related_posts(post, posts),
        )
        (post_dir / "index.html").write_text(html)

    (SITE_DIR / "index.html").write_text(INDEX_TEMPLATE.render(posts=posts))
    (SITE_DIR / "sitemap.xml").write_text(SITEMAP_TEMPLATE.render(posts=posts, site_url=site_url))
    (SITE_DIR / ".nojekyll").write_text("")  # tells GitHub Pages not to run Jekyll on this

    print(f"Built {len(posts)} post(s) into {SITE_DIR}/")
    return len(posts)
