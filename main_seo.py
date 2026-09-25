import os

from dotenv import load_dotenv

load_dotenv()

from seo.content_generator import generate_posts
from seo.site_builder import build


def run() -> None:
    site_url = os.environ["SITE_URL"].rstrip("/")
    app_store_url = os.environ["APP_STORE_URL"]
    posts_per_day = int(os.environ.get("POSTS_PER_DAY", "3"))

    posts = generate_posts(posts_per_day)
    for post in posts:
        print(f"Published: {post['title']} (/posts/{post['slug']}/)")
    if len(posts) < posts_per_day:
        print(
            f"Requested {posts_per_day}, generated {len(posts)} — Fable ran out of genuinely "
            "distinct topics rather than padding with near-duplicates. See seo/topics.json."
        )

    count = build(site_url, app_store_url)
    print(f"Site rebuilt with {count} total post(s).")
    print(
        "AUTO_PUBLISH is "
        + ("true — the workflow will commit and push seo/site/ live."
           if os.environ.get("AUTO_PUBLISH", "false").lower() == "true"
           else "false — seo/site/ was rebuilt locally/as a CI artifact only, nothing went live.")
    )


if __name__ == "__main__":
    run()
