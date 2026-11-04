# Daily Parlay Notifier

A small automation that runs every day: it pulls current sports odds across multiple
leagues, builds a "safe" 4-leg parlay per sport out of the day's favorites, pushes it to
your phone as a notification, and grades yesterday's parlays against final scores. A
website tracks the full history and per-sport stats. Nothing places bets automatically —
it just prepares the suggestion.

**Live site:** https://vroonster20.github.io/parlay-notifier/

## Tech Stack

- Python 3.13
- [The Odds API](https://the-odds-api.com/) — live sports odds (moneyline/h2h market, American odds format), averaged across bookmakers
- [ESPN scoreboard API](https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard) (unofficial, free) — final scores for grading
- [ntfy.sh](https://ntfy.sh/) — free push-notification relay to your phone
- GitHub Actions — free daily cron automation, runs in the cloud with no computer needed
- GitHub Pages — free static hosting for the stats website (HTML/CSS/JS, no server or database)
- `requests` / `python-dotenv` / `tzdata` — API calls, local env vars, and timezone data on Windows

## Project Structure

```
main branch (code)
parlay-notifier/
├── main.py                      # entry point — orchestrates the daily run
├── odds_fetcher.py              # fetches today's odds per in-season sport, averages across bookmakers
├── parlay_builder.py            # picks favorites within an odds band, builds a 4-leg parlay per sport
├── results.py                   # grades pending legs against ESPN final scores
├── history.py                   # loads, saves, and appends to the parlay history file
├── notifier.py                  # formats and sends the push notification
├── requirements.txt
├── docs/                        # stats website, served by GitHub Pages
│   ├── index.html
│   ├── style.css
│   └── app.js                   # loads history from the data branch, computes stats, renders
├── sports_odds/                 # local per-sport odds cache (snapshot mode)
├── .env                         # local-only secrets (never committed)
└── .github/workflows/daily.yml  # scheduled GitHub Actions run

data branch (bot only)
└── parlays.json                 # every parlay ever made, with leg results
```

**Daily flow:** load history → grade yesterday's pending legs (ESPN) → fetch today's odds
(The Odds API) → build each sport's parlay → append to history → send the notification →
the bot commits `parlays.json` to the `data` branch → the website picks up the new data
within a few minutes.

**Saving API credits:** each sport is skipped outside its rough season dates, and a free
`/events` check confirms there are games today before spending a credit on odds. Grading
uses ESPN, which costs no credits.

**Why a separate `data` branch:** the bot commits history every day, so keeping it on its
own branch leaves `main` with only code commits. Never merge `data` into `main`.

## Setup

1. Get a free API key from [The Odds API](https://the-odds-api.com/).
2. Install the [ntfy app](https://ntfy.sh/) and subscribe to a unique topic name (keep it obscure — anyone who knows it can read or send to it).
3. Clone the repo, then create a `.env` file:
   ```
   THE_ODDS_KEY=your_real_api_key
   NTFY_TOPIC=your_chosen_topic_name
   RUN_MODE=live
   ```
4. `pip install -r requirements.txt`
5. Add `THE_ODDS_KEY` and `NTFY_TOPIC` as GitHub repo secrets too (Settings → Secrets and variables → Actions) — the scheduled workflow needs its own copies.
6. Create the `data` branch once (an orphan branch containing just `parlays.json`, or an empty commit).
7. Enable GitHub Pages: Settings → Pages → Deploy from a branch → `main` / `/docs`. The repo must be public on a free account.

## Usage

**Run locally:** `python main.py` — fetches odds, builds parlays, sends real notifications. Locally, history is written to `history/parlays.json`, a gitignored scratch file; the real history lives only on the `data` branch.

`RUN_MODE` in `.env` toggles `live` (calls the API, refreshes snapshots) vs. `snapshot` (reuses saved odds, no API quota used).

**Automatic runs:** the workflow runs on the schedule in `daily.yml` (cron times are UTC). Trigger it manually anytime via the repo's Actions tab → Run workflow. Manual runs use API credits and send a notification.

**The notification:** one section per sport listing the parlay legs (team + American odds). A sport with fewer than 4 qualifying favorites shows "no qualifying games" instead of a forced pick. Tap the notification to open the website.

**The website:** per-sport tabs, the hypothetical profit of betting $1 on every parlay, parlay and leg hit rates, a 0/4–4/4 breakdown, today's active parlays, and the full graded history. Add `?data=file.json` to the URL to test against a local file.

**Void legs:** postponed or tied games are dropped like a sportsbook would, reducing the parlay (e.g. to 3 legs). Reduced parlays count in the record and profit, but not in the 0/4–4/4 chart.

**Tuning risk:** in `parlay_builder.py`, `build_safe_parlay()` exposes `min_favorite_price` / `max_favorite_price` (the American-odds band for a "safe" favorite, e.g. `-500` to `-120`) and `min_legs` / `max_legs` (both 4).

**Adding a sport:** add its key to `selected_sports`, `probe_month_day`, and `end_month_day` in `odds_fetcher.py`; `ESPN_SPORTS` in `results.py`; and the `sports` dict in `notifier.py` (the run crashes if either of the last two is missing). Optionally add a name and icon to `SPORTS` in `docs/app.js`. Only sports with two outcomes (no draws) are supported.

## Roadmap

- Build a machine learning model trained on historical odds, actual outcomes, and other contextual data (team stats, injuries, etc.) to generate predictions and parlays from learned patterns rather than current market odds alone.
- Add a Safe / Model switch to the website, running both strategies on the same days for a head-to-head comparison.
- Add month, year, and season filters to the website stats.