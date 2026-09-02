import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta
import statistics

load_dotenv()
SNAPSHOT_PATH = "snapshot_odds.json"

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
    flat = []

    now = datetime.now(timezone.utc)
    local_offset = timedelta(hours=-5)
    local_now = now + local_offset
    end_of_today_local = local_now.replace(hour=23, minute=59, second=59, microsecond=0)
    end_of_today_utc = end_of_today_local - local_offset

    for game in raw_games:
        commence_time = datetime.fromisoformat(game["commence_time"]. replace("Z", "+00:00"))

        if (now < commence_time < end_of_today_utc):
            prices = get_prices(game)
            home_team = game["home_team"]
            away_team = game["away_team"]
            home_price = prices.get(game["home_team"])
            away_price = prices.get(game["away_team"])

            flat.append({
                "home_team": home_team,
                "away_team": away_team,
                "home_price": home_price,
                "away_price": away_price,
                "commence_time": commence_time.isoformat(),
            })        
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
        avg = round(statistics.mean(values), 3)
        count = len(values)
        stdev = round(statistics.pstdev(values), 3)
        results[team] = {
            "avg": avg,
            "count": count,
            "stdev": stdev,
        }
    return results

def _fetch_live_odds():
    api_key = os.environ.get("THE_ODDS_KEY")
    BASE_URL = "https://api.the-odds-api.com/v4"

    if api_key is None:
        raise ValueError("Missing the api key")

    #TODO: to access multiple sports for parlays, I will need to change these hardcoded values
    sport: str = "baseball_mlb"
    regions: str = "us"
    markets: str = "h2h"

    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
    }

    response = requests.get(f"{BASE_URL}/sports/{sport}/odds", params=params)

    response.raise_for_status()

    data = response.json()
    if SNAPSHOT_PATH:
        path = Path(SNAPSHOT_PATH)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    print("Remaining:", response.headers.get("x-requests-remaining"))
    print("Used:", response.headers.get("x-requests-used"))
    print("Last call cost:", response.headers.get("x-requests-last"))

    return data

def _fetch_snapshot_odds():
    if not os.path.exists(SNAPSHOT_PATH):
        raise FileNotFoundError(f"File not found: {SNAPSHOT_PATH}")
    if not os.path.isfile(SNAPSHOT_PATH):
        raise ValueError(f"Path is not a file: {SNAPSHOT_PATH}")

    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data

# if __name__ == "__main__":
#     test = []
#     games = flatten_games(test)
#     print(games)