import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta, date
import statistics
from zoneinfo import ZoneInfo

load_dotenv()
SNAPSHOT_PATH = "snapshot_odds.json"
SPORTS_PATH = "sports.json"

LOCAL_TZ = ZoneInfo("America/Chicago")
API_TIME_FMT = "%Y-%m-%dT%H:%M:%SZ"

def _today_window_utc():
    now_utc = datetime.now(timezone.utc)
    local_now = now_utc.astimezone(LOCAL_TZ)
    end_local = local_now.replace(hour=23, minute=59, second=59, microsecond=0)
    return now_utc, end_local.astimezone(timezone.utc)

def fetch_odds():
    run_mode = os.environ.get("RUN_MODE", "snapshot")

    if run_mode == "live":
        raw = _fetch_live_odds()
    elif run_mode == "snapshot":
        raw = _fetch_snapshot_odds()
    else:
        raise ValueError(f"Unknown RUN_MODE: {run_mode}")

    return flatten_games(raw)

def flatten_games(raw_games):
    flat = {}

    now, end_of_today_utc = _today_window_utc()

    for game in raw_games:
        commence_time = datetime.fromisoformat(game["commence_time"]. replace("Z", "+00:00"))

        if (now < commence_time < end_of_today_utc):
            prices = get_prices(game)
            sport = game.get("sport_key")
            home_team = game["home_team"]
            away_team = game["away_team"]
            home_price = prices.get(game["home_team"])
            away_price = prices.get(game["away_team"])

            entry = {
                #"sport": sport,
                "home_team": home_team,
                "away_team": away_team,
                "home_price": home_price,
                "away_price": away_price,
                "commence_time": commence_time.isoformat(),
            }

            if sport not in flat:
                flat[sport] = []

            flat[sport].append(entry)
    return flat

def get_prices(game):
    info = {}
    for bookmaker in game.get('bookmakers', []):
        for market in bookmaker.get('markets', []):
            if market.get('key') == 'h2h':
                for outcome in market.get('outcomes', []):
                    team = outcome.get('name', 'Unknown')
                    price = outcome.get('price', 'N/A')

                    if team not in info:
                        info[team] = []
                    info[team].append(price)
    results = {}
    for team, values in info.items():
        avg = round(statistics.mean(values))
        count = len(values)
        stdev = round(statistics.pstdev(values), 3)
        results[team] = {
            "avg": avg,
            "count": count,
            "stdev": stdev,
        }
    return results

def _fetch_live_odds():
    all_games = []
    api_key = os.environ.get("THE_ODDS_KEY")
    BASE_URL = "https://api.the-odds-api.com/v4"

    if api_key is None:
        raise ValueError("Missing the api key")

    regions: str = "us"
    markets: str = "h2h"
    format: str = "american"

    params = {"apiKey": api_key}
    call = requests.get(f"{BASE_URL}/sports", params=params)
    call.raise_for_status()
    sports_list = call.json()
    if SPORTS_PATH:
        path = Path(SPORTS_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(sports_list, f, indent=2)

    selected_sports = {
        'baseball_mlb',
        'americanfootball_nfl', 
        'basketball_nba', 
        'icehockey_nhl',
        'americanfootball_ncaaf',
        #'basketball_ncaab',
    }

    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": format,
    }

    probe_month_day = {
        "baseball_mlb": (3, 1),
        "americanfootball_nfl": (8, 15),
        "basketball_nba": (9, 15),
        "icehockey_nhl": (9, 1),
        "americanfootball_ncaaf": (7, 20),
    }
    end_month_day = {
        "baseball_mlb": (11, 1),
        "americanfootball_nfl": (3, 15),
        "basketball_nba": (7, 15),
        "icehockey_nhl": (5, 1),
        "americanfootball_ncaaf": (2, 20),
    }

    today = datetime.now(timezone.utc).date()
    window_start, window_end = _today_window_utc()
    window = {
        "commenceTimeFrom": window_start.strftime(API_TIME_FMT),
        "commenceTimeTo": window_end.strftime(API_TIME_FMT),
    }

    for key in selected_sports:
        m, d = probe_month_day.get(key, (today.month, today.day))
        probe = date(today.year, m, d)
        m, d = end_month_day.get(key, (today.month, today.day))
        end = date(today.year, m, d)

        if not in_season(today, probe, end):
            continue

        # Free check: any games today?
        events_resp = requests.get(
            f"{BASE_URL}/sports/{key}/events",
            params={"apiKey": api_key, **window},
        )
        events_resp.raise_for_status()

        if not events_resp.json():
            print(f"[{key}] no games today, skipping odds call")
            continue

        # Paid call: 1 credit with h2h + us
        response = requests.get(
            f"{BASE_URL}/sports/{key}/odds",
            params={**params, **window},
        )
        response.raise_for_status()
        print(f"[{key}] odds call cost:", response.headers.get("x-requests-last"))

        data = response.json()
        path = Path(f"sports_odds/{key}/snapshot_odds.json")
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        all_games.extend(data)

    print("\nRemaining:", response.headers.get("x-requests-remaining"))
    print("Used:", response.headers.get("x-requests-used"))

    return all_games

def in_season(today, probe, end):
    if probe <= end:
        return probe <= today <= end
    else:
        return today >= probe or today <= end

def _fetch_snapshot_odds():
    all_games = []
    base = Path("sports_odds")

    if not base.exists():
        raise FileNotFoundError("No sports_odds folder found!")

    for sport_folder in base.iterdir():
        snapshot_file = sport_folder / "snapshot_odds.json"
        if snapshot_file.exists():
            with snapshot_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
            all_games.extend(data)

    return all_games


# if __name__ == "__main__":
#     test = []
#     games = flatten_games(test)
#     print(games)