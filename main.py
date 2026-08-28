from odds_fetcher import fetch_odds
from parlay_builder import build_safe_parlay
from notifier import send_notification


def main():
    games = fetch_odds()
    parlay = build_safe_parlay(games=games)
    send_notification(parlay=parlay)
    pass

if __name__ == "__main__":
    main()