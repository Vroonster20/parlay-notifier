import requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo
import re
import unicodedata

ESPN_BASE = "https://site.api.espn.com/apis/site/v2/sports"

# Odds API sport key -> ESPN URL path
ESPN_SPORTS = {
    "baseball_mlb": "baseball/mlb",
    "americanfootball_nfl": "football/nfl",
    "basketball_nba": "basketball/nba",
    "icehockey_nhl": "hockey/nhl",
    "americanfootball_ncaaf": "football/college-football",
}


def espn_date_for(commence_time):
    clean_iso = commence_time.replace('Z', '+00:00')
    dt_utc = datetime.fromisoformat(clean_iso)

    ny_tz =  ZoneInfo("America/New_York")
    dt_ny = dt_utc.astimezone(ny_tz)

    return dt_ny.strftime('%Y%m%d')


def fetch_results(sport_key, date_str):
    sport = ESPN_SPORTS.get(sport_key)
    if sport is None:
        raise ValueError(f"Unsupported sport: {sport_key}")

    url = f"{ESPN_BASE}/{sport}/scoreboard?dates={date_str}"

    response = requests.get(url)
    response.raise_for_status()

    data = response.json()

    results = []

    for event in data.get("events", []):
        competition = event["competitions"][0]
        competitors = competition["competitors"]

        home = next(c for c in competitors if c["homeAway"] == "home")
        away = next(c for c in competitors if c["homeAway"] == "away")

        results.append({
            "home": home["team"]["displayName"],
            "away": away["team"]["displayName"],
            "home_score": int(home["score"]),
            "away_score": int(away["score"]),
            "completed": competition["status"]["type"]["completed"],
        })

    return results


def grade_leg(leg, games):
    team = normalize(leg["team"])

    game = next((g for g in games if team in (normalize(g["home"]), normalize(g["away"]))), None)

    if game is None:
        print(f"[results] No game found for '{leg['team']}', check for a name mismatch")
        return "pending"

    if not game["completed"]:
        return "pending"

    if team == normalize(game["home"]):
        team_score, opp_score = game["home_score"], game["away_score"]
    else:
        team_score, opp_score = game["away_score"], game["home_score"]

    if team_score > opp_score:
        return "win"
    if team_score < opp_score:
        return "loss"
    return "push"

def grade_history(history):
    cache = {}

    for parlay in history:
        # Check every parlay that still has an ungraded leg, even one already lost,
        # so each leg ends up with a final result on the website
        if not any(leg["result"] == "pending" for leg in parlay["legs"]):
            continue

        for leg in parlay["legs"]:
            if leg["result"] != "pending":
                continue

            date_str = espn_date_for(leg["commence_time"])
            key = (leg["sport"], date_str)
            if key not in cache:
                cache[key] = fetch_results(leg["sport"], date_str)

            leg["result"] = grade_leg(leg, cache[key])

            start = datetime.fromisoformat(leg["commence_time"])
            if leg["result"] == "pending" and datetime.now(timezone.utc) - start > timedelta(days=3):
                leg["result"] = "void"

        parlay["status"] = parlay_status(parlay["legs"])

    return history

def parlay_status(legs):
    results = [leg["result"] for leg in legs]
    if "loss" in results:
        return "lost"
    if "pending" in results:
        return "pending"
    return "won"

# Names that differ between The Odds API and ESPN beyond punctuation/accents.
# Add an entry whenever "No game found" shows up in the logs.
ALIASES = {
    "la clippers": "los angeles clippers",
}


def normalize(name):
    """Compare team names ignoring accents, punctuation, capitalization and extra spaces.
    "St. Louis Blues" and "St Louis Blues" both become "st louis blues"."""
    no_accents = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    no_punctuation = re.sub(r"[^\w\s]", "", no_accents)
    cleaned = " ".join(no_punctuation.lower().split())
    return ALIASES.get(cleaned, cleaned)