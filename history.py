import json
from pathlib import Path
from datetime import datetime
from zoneinfo import ZoneInfo

HISTORY_PATH = Path("history/parlays.json")
LOCAL_TZ = ZoneInfo("America/Chicago")

def load_history():
    if not HISTORY_PATH.exists():
        return []
    with HISTORY_PATH.open("r", encoding="utf-8") as f:
        return json.load(f)

def save_history(history):
    HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with HISTORY_PATH.open("w", encoding="utf-8") as f:
        json.dump(history, f, indent=2)

def add_parlays(history, parlays):
    today = datetime.now(LOCAL_TZ).strftime("%Y-%m-%d")
    already_logged = {(p["date"], p["sport"]) for p in history}

    for sport, legs in parlays.items():
        if (today, sport) in already_logged:
            print(f"[history] {sport} parlay for {today} already logged, skipping")
            continue
        history.append({
            "date": today,
            "sport": sport,
            "status": "pending",
            "legs": legs,
        })
    return history