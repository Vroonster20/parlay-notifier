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
    # TODO: open SNAPSHOT_PATH, load the JSON, return it
    # TODO: what should happen if the file doesn't exist yet?
    #       (hint: this is a good first bug to hit and fix yourself)
    return "not working"

if __name__ == "__main__":
    games = fetch_odds()
    print(games)