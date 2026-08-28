# Fliff Daily Parlay Notifier

A small automation used every day: a script pulls current MLB odds, builds
a "safe" parlay out of the day's biggest favorites, and pushes it to your phone as a
notification. Nothing places bets automatically.

## How it's set up

**Language:** Python 3.13

**Tech stack:**
- **[The Odds API](https://the-odds-api.com/)** — source of live sports odds (moneyline/h2h market, MLB)
- **[ntfy.sh](https://ntfy.sh/)** — free push-notification relay; no account needed, just subscribe to a topic in the ntfy phone app
- **GitHub Actions** — free scheduled automation (cron), runs the script once a day in the cloud with no computer needed on your end
- **`requests`** — HTTP calls to both The Odds API and ntfy
- **`python-dotenv`** — loads local environment variables from a `.env` file during development

**Project structure:**
```
fliff-parlay-bot/
├── main.py                      # entry point — orchestrates the daily run
├── odds_fetcher.py              # fetches odds (live API or saved snapshot), flattens raw data
├── parlay_builder.py            # filters/ranks games into a "safe" parlay
├── notifier.py                  # formats the parlay and sends the push notification
├── requirements.txt             # third-party dependencies
├── snapshot_odds.json           # local cache of the last live pull (used in snapshot mode)
├── .env                         # local-only secrets (never committed)
├── .gitignore
└── .github/workflows/daily.yml  # GitHub Actions schedule that runs main.py daily
```

**How the pieces connect:**
1. `main.py` calls `fetch_odds()` in `odds_fetcher.py`, which either hits The Odds API live or reads a saved snapshot, then returns a clean, flat list of today's games (team names, home/away decimal odds, start time).
2. That list is passed to `build_safe_parlay()` in `parlay_builder.py`, which picks the favorite side of each game, filters out anything riskier than a set odds threshold, sorts by safest first, and trims to a max number of legs.
3. The resulting parlay is passed to `send_notification()` in `notifier.py`, which formats it into a readable message and POSTs it to your ntfy topic, triggering a push notification on your phone.
4. GitHub Actions runs `main.py` on a daily schedule (cron), fully in the cloud — your computer doesn't need to be on.

## How to use it

### One-time setup

1. **Get an API key** from [The Odds API](https://the-odds-api.com/) (free tier).
2. **Install the [ntfy app](https://ntfy.sh/)** on your phone and subscribe to a unique topic name of your choosing (keep it obscure — anyone who knows your topic name can send you notifications or read them).
3. **Clone this repo** and open it in VS Code.
4. **Create a `.env` file** in the project root (this file is git-ignored and never uploaded) with:
   ```
   THE_ODDS_KEY=your_real_api_key
   NTFY_TOPIC=your_chosen_topic_name
   RUN_MODE=live
   ```
5. **Install dependencies:**
   ```
   pip install -r requirements.txt
   ```
6. **Add the same two secrets in GitHub** (Settings → Secrets and variables → Actions → New repository secret): `THE_ODDS_KEY` and `NTFY_TOPIC`. GitHub Actions doesn't read your local `.env` — it needs its own copies stored securely.

### Running it locally

```
python main.py
```

This fetches today's odds, builds the safe parlay, and sends a real push notification to your phone. Good for testing before trusting the automation.

**`RUN_MODE` options** (set in `.env`):
- `live` — calls The Odds API for fresh data (uses your API quota, also refreshes `snapshot_odds.json`)
- `snapshot` — reuses the last saved `snapshot_odds.json` instead of calling the API (useful for testing without burning API calls)

### Letting it run automatically

Once your secrets are set on GitHub and `.github/workflows/daily.yml` is pushed to your default branch, the workflow runs on its own schedule (see the `cron` line in that file for the exact UTC time). No further action needed — check your phone around that time each day.

To test the automation without waiting for the schedule: go to the repo's **Actions** tab on GitHub → select the workflow → **Run workflow** button.

### Reading the daily notification

Each notification lists the day's safe-parlay legs (team + decimal odds), soonest-starting favorites first. If fewer than the minimum number of qualifying favorites exist that day, you'll get a "no qualifying games today" message instead — nothing is force-picked.

To place it: open Fliff, claim your daily dollar, and manually enter the same teams as your parlay. This tool only prepares the suggestion — you always place the actual bet yourself.

### Adjusting the parlay's risk level

In `parlay_builder.py`, `build_safe_parlay()` takes a few tunable parameters:
- `max_favorite_price` — decimal-odds ceiling for what counts as a "safe" favorite (lower = safer, less payout)
- `min_legs` / `max_legs` — how many games make it into the parlay

## Notes / future ideas

- Currently MLB-only (`baseball_mlb`) and single-bookmaker (BetMGM) as the odds reference.
- Planned future addition: logging daily odds alongside actual game outcomes over a full season, to eventually train a ML model that builds parlays from historical performance instead of just current market odds.
