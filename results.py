import requests
from datetime import datetime
from zoneinfo import ZoneInfo

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
    team = leg["team"]

    game = next((g for g in games if team in (g["home"], g["away"])), None)

    if game is None:
        print(f"[results] No game found for '{team}', check for a name mismatch")
        return "pending"

    if not game["completed"]:
        return "pending"

    if team == game["home"]:
        team_score, opp_score = game["home_score"], game["away_score"]
    else:
        team_score, opp_score = game["away_score"], game["home_score"]

    if team_score > opp_score:
        return "win"
    if team_score < opp_score:
        return "loss"
    return "push"
