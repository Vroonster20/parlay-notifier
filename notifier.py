import os
import requests
from dotenv import load_dotenv

load_dotenv()

def send_notification(parlay, title="Today's Safe Parlay"):
    if not parlay:
        message = "No qualifying games today."
    else:
        lines = [f"-\u2003{g['team']} @ {g['price']}" for g in parlay]
        message = "\n".join(lines)  

    topic = os.environ.get("NTFY_TOPIC")
    url = f"https://ntfy.sh/{topic}"

    response = requests.post(url, data=message.encode('utf-8'), headers= { "Markdown": "yes", "Title": title, "Priority": "5", "Tags": "baseball"})
    response.raise_for_status()