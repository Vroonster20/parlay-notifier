from odds_fetcher import fetch_odds
from parlay_builder import build_safe_parlay
from notifier import send_notification


def main():
    # TODO: get today's games
    games = fetch_odds()
    # TODO: build the safe parlay from those games
    parlay = build_safe_parlay(games=games)
    # TODO: send the notification
    send_notification(parlay=parlay)
    pass


if __name__ == "__main__":
    main()