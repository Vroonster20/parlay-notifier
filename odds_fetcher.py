import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta, date
import statistics

load_dotenv()
SNAPSHOT_PATH = "snapshot_odds.json"
SPORTS_PATH = "sports.json"

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

    now = datetime.now(timezone.utc)
    local_offset = timedelta(hours=-5)
    local_now = now + local_offset
    end_of_today_local = local_now.replace(hour=23, minute=59, second=59, microsecond=0)
    end_of_today_utc = end_of_today_local - local_offset

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
        #'basketball_ncaab',
    }

    params = {
        "apiKey": api_key,
        "regions": regions,
        "markets": markets,
        "oddsFormat": format,
    }

    for key in selected_sports:
        today = datetime.now(timezone.utc).date()
        should_call = False

        probe_month_day = {
            "baseball_mlb": (3, 1),
            "americanfootball_nfl": (8, 15),
            "basketball_nba": (9, 15),
            "icehockey_nhl": (9, 1),
        }
        end_month_day = {
            "baseball_mlb": (11, 1),
            "americanfootball_nfl": (3, 15),
            "basketball_nba": (7, 15),
            "icehockey_nhl": (5, 1),
        }
        probe_dates = {k: date(today.year, m, d) for k, (m, d) in probe_month_day.items()}
        probe = probe_dates.get(key, today)
        end_dates = {k: date(today.year, m, d) for k, (m, d) in end_month_day.items()}
        end = end_dates.get(key, today)

        file_path = os.path.join("sports_odds", key, "snapshot_odds.json")

        if not os.path.exists(file_path):
            if today >= probe_dates.get(key, today):
                should_call = True
        else:
            with open(file_path, 'r', encoding='utf-8') as f:
                saved_data = json.load(f)
            if saved_data:
                start_date = datetime.fromisoformat(saved_data[0]["commence_time"].replace("Z", "+00:00")).date()
                if today >= start_date - timedelta(days=3):
                    should_call = True
            else:
                if probe < end:
                    if (today >= probe) and (today <= end): 
                        should_call = True
                else:
                    if (today >= probe) or (today <= end):
                        should_call = True

        if should_call:
            SNAPSHOT_PATH = f"sports_odds/{key}/snapshot_odds.json"
            response = requests.get(f"{BASE_URL}/sports/{key}/odds", params=params)                           
            response.raise_for_status()

            print(f"[{key}] Last call cost:", response.headers.get("x-requests-last"))
                                        
            data = response.json()
            if SNAPSHOT_PATH:
                path = Path(SNAPSHOT_PATH)
                path.parent.mkdir(parents=True, exist_ok=True)
                with path.open("w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
            all_games.extend(data)

    print("\nRemaining:", response.headers.get("x-requests-remaining"))
    print("Used:", response.headers.get("x-requests-used"))

    return all_games

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