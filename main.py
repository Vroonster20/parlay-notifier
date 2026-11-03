from odds_fetcher import fetch_odds
from parlay_builder import build_safe_parlay
from notifier import send_notification
from history import load_history, save_history, add_parlays
from results import grade_history

def main():
    history = load_history()
    history = grade_history(history)

    games = fetch_odds()
    parlay = build_safe_parlay(games)

    history = add_parlays(history, parlay)
    save_history(history)

    send_notification(parlay)

if __name__ == "__main__":
    main()