# Daily Parlay Notifier

A small automation that runs every day: it pulls current sports odds across multiple
leagues, builds a "safe" parlay per sport out of the day's biggest favorites, and
pushes it to your phone as a notification. Nothing places bets automatically — it
just prepares the suggestion.

## Tech Stack

- Python 3.13
- [The Odds API](https://the-odds-api.com/) — live sports odds (moneyline/h2h market, American odds format), averaged across bookmakers
- [ntfy.sh](https://ntfy.sh/) — free push-notification relay to your phone
- GitHub Actions — free daily cron automation, runs in the cloud with no computer needed
- `requests` / `python-dotenv` — API calls and local env var loading

## Project Structure

```
parlay-bot/
├── main.py                      # entry point — orchestrates the daily run
├── odds_fetcher.py              # fetches odds per sport (live API or saved snapshots), handles seasonal scheduling
├── parlay_builder.py            # filters/ranks each sport's games into a "safe" parlay
├── notifier.py                  # formats and sends one push notification per sport
├── requirements.txt
├── sports_odds/                 # per-sport cached snapshots (used in snapshot mode)
│   └── <sport_key>/snapshot_odds.json
├── .env                         # local-only secrets (never committed)
└── .github/workflows/daily.yml  # scheduled GitHub Actions run
```

**Flow:** `odds_fetcher.py` fetches today's games for each tracked sport (skipping
sports that are out of season) and averages prices across bookmakers → `parlay_builder.py`
picks the favorite side of each game per sport, filters by risk threshold, and trims to
a max number of legs → `notifier.py` formats and pushes a labeled section per sport to
your phone. GitHub Actions triggers this whole chain daily.

**Seasonal scheduling:** each sport has a rough start/end date. Before its season, the
script checks in periodically at low cost (empty responses are free); once real games
appear, it checks against the actual first game date instead of the hardcoded guess;
after the season ends, it goes back to periodic low-cost checks until next year — no
manual toggling required.

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

## Usage

**Run locally:** `python main.py` — fetches odds, builds each sport's parlay, sends real notifications. Good for testing.

`RUN_MODE` in `.env` toggles `live` (calls the API for sports currently due, refreshes their snapshots) vs. `snapshot` (reuses all saved data, no API quota used).

**Automatic runs:** once secrets are set and the workflow is pushed, it runs on its own schedule (see the `cron` line in `daily.yml`). Trigger it manually anytime via the repo's Actions tab → Run workflow.

**The notification:** one labeled section per sport, listing that day's parlay legs (team + American odds), soonest-starting favorites first. A sport with nothing qualifying that day shows "no qualifying games" instead of a forced pick. Placing the bet is still manual — this only prepares the suggestion.

**Tuning risk:** in `parlay_builder.py`, `build_safe_parlay()` exposes `max_favorite_price` (American-odds ceiling for "safe," e.g. `-150`) and `min_legs`/`max_legs`.

**Adding/removing sports:** edit `selected_sports` and the paired `probe_month_day`/`end_month_day` entries in `odds_fetcher.py`.

## Roadmap

- Add a stat‑tracking feature/website that logs each day’s picks and parlays, showing win/loss history, per‑sport accuracy, average parlay odds, and long‑term performance metrics.

- Build a machine learning model trained on historical odds, actual outcomes, and other contextual data (team stats, injuries, etc.) to generate predictions and parlays from learned patterns rather than current market odds alone.
