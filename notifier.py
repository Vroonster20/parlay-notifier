import os
import requests
from dotenv import load_dotenv

load_dotenv()

sports = {
    "baseball_mlb": "⚾ BASEBALL PARLAY",
    "americanfootball_nfl": "🏈 FOOTBALL PARLAY",
    "basketball_nba": "🏀 BASKETBALL PARLAY",
    "icehockey_nhl": "🏒 HOCKEY PARLAY",
}

def send_notification(parlay, title="Today's Safe Parlays!"):
    final_message = ""
    for sport in parlay:
        sport_title = sports.get(sport)
        if not parlay[sport]:
            message = f"{sport_title}\nNo qualifying games today."
        else:            
            lines = [f"-\u2003{g['team']} @ {g['price']}" for g in parlay[sport]]
            message = (sport_title + "\n" + "\n".join(lines))

        final_message += message + "\n\n"

    topic = os.environ.get("NTFY_TOPIC")
    url = f"https://ntfy.sh/{topic}"

    response = requests.post(url, data=final_message.encode('utf-8'), headers= {"Title": title, "Priority": "5", "Tags": "money_with_wings"})
    response.raise_for_status()