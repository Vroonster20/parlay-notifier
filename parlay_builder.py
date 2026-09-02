import os
import json
import requests
from pathlib import Path

def build_safe_parlay(games, min_legs=2, max_legs=4, max_favorite_price=1.8):
    picks = []

    for idx, match in enumerate(games):
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
                "price": favorite_price,
                "idx": idx,
            })

        except KeyError as e:
            print(f"Missing key {e}")
        except ValueError:
            print(f"Price values must be numeric.")
        except Exception as e:
            print(f"Unexpected error - {e}")

    top_by_price = sorted(picks, key=lambda item: item["price"])[:max_legs]
    final_picks = sorted(top_by_price, key=lambda item: item["idx"])

    if len(final_picks) < min_legs:
        return []

    return final_picks