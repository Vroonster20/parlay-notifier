# Daily Parlay Notifier

A small automation that runs every day: it pulls current sports odds, builds a "safe" parlay out of the day's biggest favorites, and pushes it to your phone as a notification. Nothing places bets automatically — it just prepares the suggestion.

## Tech Stack

- **Python 3.13**
- **[The Odds API](https://the-odds-api.com/)** — live sports odds (moneyline/h2h market)
- **[ntfy.sh](https://ntfy.sh/)** — free push-notification relay to your phone
- **GitHub Actions** — free daily cron automation, runs in the cloud with no computer needed
- **`requests`** / **`python-dotenv`** — API calls and local env var loading

## Project Structure

```
parlay-bot/
├── main.py                      # entry point — orchestrates the daily run
├── odds_fetcher.py              # fetches odds (live API or saved snapshot)
├── parlay_builder.py            # filters/ranks games into a "safe" parlay
├── notifier.py                  # formats and sends the push notification
├── requirements.txt
├── snapshot_odds.json           # cached last live pull (used in snapshot mode)
├── .env                         # local-only secrets (never committed)
└── .github/workflows/daily.yml  # scheduled GitHub Actions run
```

**Flow:** `odds_fetcher.py` pulls today's games → `parlay_builder.py` picks the favorite side of each, filters by risk threshold, and trims to a max number of legs → `notifier.py` formats and pushes the result to your phone. GitHub Actions triggers this whole chain daily.

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

**Run locally:** `python main.py` — fetches odds, builds the parlay, sends a real notification. Good for testing.

`RUN_MODE` in `.env` toggles `live` (calls the API, refreshes the snapshot) vs. `snapshot` (reuses the last saved data, no API quota used).

**Automatic runs:** once secrets are set and the workflow is pushed, it runs on its own schedule (see the `cron` line in `daily.yml`). Trigger it manually anytime via the repo's **Actions** tab → **Run workflow**.

**The notification:** lists the day's parlay legs (team + decimal odds), soonest-starting favorites first. If nothing qualifies that day, you get a "no qualifying games" message instead of a forced pick. Placing the bet is still manual — this only prepares the suggestion.

**Tuning risk:** in `parlay_builder.py`, `build_safe_parlay()` exposes `max_favorite_price` (odds ceiling for "safe") and `min_legs`/`max_legs`.

## Roadmap

- Expand beyond baseball to additional sports/leagues.
- Build a machine learning model trained on historical odds, actual outcomes, and other contextual data (team stats, injuries, etc.) to generate predictions and parlays from learned patterns rather than current market odds alone.
