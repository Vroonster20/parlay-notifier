import os
import json
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
SNAPSHOT_PATH = "snapshot_odds.json"

def fetch_odds():
    run_mode = os.environ.get("RUN_MODE", "snapshot")

    if run_mode == "live":
        return _fetch_live_odds()
    elif run_mode == "snapshot":
        return _fetch_snapshot_odds()
    else:
        raise ValueError(f"Unknown RUN_MODE: {run_mode}")


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