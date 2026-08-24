import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone

#TODO: check to see if snapshot_odds.json is correct with the
#new flatten_games()

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
    selected_bookmaker = "BetMGM"

    for game in raw_games:
        commence_time = datetime.fromisoformat(game["commence_time"]. replace("Z", "+00:00"))
        
        bookmakers = game.get('bookmakers', [])

        has_selected_bookmaker = any(b.get('title') == selected_bookmaker for b in bookmakers)
        if (commence_time > now) and (has_selected_bookmaker):
            selected = next(b for b in bookmakers if b.get('title') == selected_bookmaker)
            prices = get_prices(selected)
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

def get_prices(bookmaker):
    info = {}
    for market in bookmaker.get('markets', []):
        if market.get('key') == 'h2h':
            for outcome in market.get('outcomes', []):
                team = outcome.get('name', 'Unknown')
                price = outcome.get('price', 'N/A')
                info[team] = price
    return info

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

    return data

def _fetch_snapshot_odds():
    if not os.path.exists(SNAPSHOT_PATH):
        raise FileNotFoundError(f"File not found: {SNAPSHOT_PATH}")
    if not os.path.isfile(SNAPSHOT_PATH):
        raise ValueError(f"Path is not a file: {SNAPSHOT_PATH}")

    with open(SNAPSHOT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    return data

if __name__ == "__main__":
    games = fetch_odds()
    print(games)