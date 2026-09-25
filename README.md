# Selah Growth Bot

## What this does, simply

Three jobs, all running daily, no server to babysit:

1. **Writes ~3 blog posts a day** (configurable — see "On volume" below).
   Fable writes on things people actually search for, publishes to a
   simple website, every post links to Selah's App Store page.
2. **Finds podcast candidates daily.** Searches Apple's podcast directory
   across 20 search terms — a couple hundred candidates on a typical run.
   You pick which are worth pitching, add a contact email, and the bot
   drafts a pitch for you to send.
3. **Emails/saves a report every day** — exactly what got published,
   found, and drafted. Since both bots now run daily, an empty report is
   a signal something broke, not just "not their day."

## On volume — read this before you turn AUTO_PUBLISH on

You asked for high volume, so here's what's actually true about that,
not just what's easy to build:

**The blog side has a real ceiling, and it's not about effort or cost —
it's Google.** Their "scaled content abuse" policy (reinforced again in
the March and June 2026 core updates) specifically targets sites that
mass-publish pages to capture search rankings rather than genuinely help
readers — and it applies no matter how the content is produced. Sites
caught by it have lost 50-80% of their traffic overnight. A brand-new,
single-topic blog is closer to that pattern than a large news site is,
because there's a real limit to how many genuinely distinct angles exist
on "Bible reading habits" before posts start repeating themselves with a
different headline.

So: `POSTS_PER_DAY` defaults to **3** — about 21x the original plan,
real volume — and the topic brainstorming prompt explicitly refuses to
pad with reworded duplicates once genuinely distinct angles run out (it'll
generate fewer posts that day rather than filler; the daily report flags
this). You can raise `POSTS_PER_DAY` further, but you're trading against
that ceiling as you do, and I'd watch Search Console for a ranking drop
rather than assuming more is always better.

**Outreach has a different ceiling, on purpose, and I'm not removing
it.** The bot can now find hundreds of podcast candidates a day — that
part scales however far you want. But drafting a pitch still requires
you to add a `contact_email` and mark a row `ready` first. That step
isn't a rate limit I could lift for you; it's what makes a pitch an
actual pitch instead of a form letter to a stranger. Mass-drafting to
unvetted contacts wouldn't get you more replies, it'd get lower ones —
and if you're sending from a personal Gmail, Google and Yahoo's bulk-
sender rules can flag or throttle an account with a high spam-complaint
rate. The genuinely bigger lever here is the size of the discovery pool,
which is now real and large — the bottleneck is your research time
choosing who's worth pitching, which no bot should really remove.

## What you need to get this running

- [ ] An **Anthropic API key** (console.anthropic.com)
- [ ] A **free GitHub account**, to host it and run it on a schedule
- [ ] **Selah's App Store link**
- [ ] **GitHub Pages turned on** for the repo (free, one checkbox)

Optional: Gmail integration for real drafts, SMTP for an emailed report,
a custom domain.

## Review points

| Step | Automatic? |
|---|---|
| Writing blog posts | Yes, ~3/day |
| Publishing blog posts live | **No by default** — `AUTO_PUBLISH=false` until you trust it |
| Finding podcast candidates | Yes, daily, ~hundreds/week |
| Finding a contact email for one | **No, always manual** — the anti-spam gate |
| Drafting a pitch once you add an email | Yes, uncapped |
| Sending that pitch | **No, never** — it's a draft, you click send |
| Daily report | Yes |

## Setup

### 1. Get the basics working locally
```bash
pip install -r requirements.txt
cp .env.example .env
# fill in ANTHROPIC_API_KEY, SITE_URL (see step 3), APP_STORE_URL

python main_seo.py        # writes POSTS_PER_DAY posts, builds seo/site/
python main_outreach.py   # populates outreach/targets.csv — expect 100+ candidates
python report.py          # writes today's report to reports/
```

### 2. Podcast outreach — the manual step
Open `outreach/targets.csv`. For candidates worth pitching: research and
add `contact_email`, change `status` to `ready`, run `python
main_outreach.py` again — it drafts and flips status to `drafted`.
With hundreds of candidates now, sort/filter the CSV by whatever signals
matter to you (name, description keywords) rather than trying to vet
every row.

### 3. GitHub Pages
Push to GitHub → Settings → Pages → source = `seo/site` on the branch the
workflow pushes to → update `SITE_URL` to match the assigned (or custom) domain.

### 4. Schedule it
Repo Settings → Secrets and variables → Actions:
- **Secrets:** `ANTHROPIC_API_KEY`, plus Gmail/SMTP secrets if using those.
- **Variables:** `SITE_URL`, `APP_STORE_URL`, `POSTS_PER_DAY`, `AUTO_PUBLISH`, `GMAIL_ENABLED`.

All three workflows (`seo.yml`, `outreach.yml`, `report.yml`) run daily,
staggered (12:00, 12:10, 13:00 UTC) so they don't collide, and each has a
manual "Run workflow" button in the Actions tab.

### 5. Optional: real Gmail drafts / emailed report
See `outreach/gmail_drafts.py`'s header comment for the one-time OAuth
setup, and `.env.example`'s `SMTP_*` fields for the emailed report.

## What this doesn't do

- Doesn't guarantee rankings or replies — it removes busywork, not the
  actual work of writing well and building relationships.
- Doesn't measure results yet, only activity — see the earlier
  conversation about Search Console for the next real step there.
- Doesn't touch paid ads, organic social, or App Store metadata —
  separate builds if you want them.
