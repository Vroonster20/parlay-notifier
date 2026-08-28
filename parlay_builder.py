import os
import json
import requests
from pathlib import Path
from odds_fetcher import fetch_odds


def build_safe_parlay(games=None, min_legs=2, max_legs=4, max_favorite_price=1.8):
    if games is None:
        games = fetch_odds()
    picks = []

    for match in games:
        try:
            home_price = float(match["home_price"])
            away_price = float(match["away_price"])

            if home_price < away_price:
                favorite_team = (match["home_team"])
                favorite_price = home_price
            elif away_price < home_price:
                favorite_team = (match["away_team"])
                favorite_price = away_price
            else:
                continue

            if favorite_price > max_favorite_price:
                continue

            picks.append({
                "team": favorite_team,
                "price": favorite_price
            })

        except KeyError as e:
            print(f"Missing key {e}")
        except ValueError:
            print(f"Price values must be numeric.")
        except Exception as e:
            print(f"Unexpected error - {e}")

    if len(selected_picks) < min_legs:
        return []

    sorted_picks = sorted(picks, key=lambda item: item["price"])
    selected_picks = sorted_picks[:max_legs]
    return selected_picks


if __name__ == "__main__":
    parlay = build_safe_parlay()
    print(parlay)