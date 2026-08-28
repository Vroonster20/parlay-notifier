import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_notification(parlay, title="Today's Safe Parlay"):
    if not parlay:
        message = "No qualifying games today."
    else:
        lines = [f"{g['team']} @ {g['price']}" for g in parlay]
        message = "\n".join(lines)  

    final_message = title + "\n" + message

    topic = os.environ.get("NTFY_TOPIC")
    url = f"https://ntfy.sh/{topic}"

    response = requests.post(url, data=final_message.encode('utf-8'))
    response.raise_for_status()