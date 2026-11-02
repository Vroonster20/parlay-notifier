import os
import json
import requests
from pathlib import Path

def build_safe_parlay(games, min_legs=4, max_legs=4, max_favorite_price=-120, min_favorite_price=-500):
    top_sport = {}

    for sport, sport_games in games.items():
        picks = []
        for idx, match in enumerate(sport_games):
            try:
                home_price = float(match["home_price"]["avg"])
                away_price = float(match["away_price"]["avg"])

                if home_price < away_price:
                    favorite_team = match["home_team"]
                    opponent = match["away_team"]
                    favorite_price = home_price
                elif away_price < home_price:
                    favorite_team = match["away_team"]
                    opponent = match["home_team"]
                    favorite_price = away_price
                else:
                    continue

                
                if favorite_price < min_favorite_price or favorite_price > max_favorite_price:
                    continue

                picks.append({
                    "event_id": match.get("event_id"),
                    "sport": sport,
                    "team": favorite_team,
                    "opponent": opponent,
                    "price": favorite_price,
                    "commence_time": match["commence_time"],
                    "result": "pending",
                    "idx": idx,
                })

            except KeyError as e:
                print(f"Missing key {e}")
            except (TypeError, ValueError) as e:
                print(f"Bad price data for {match.get('home_team')}: {e}")

        top_by_price = sorted(picks, key=lambda item: item["price"])[:min_legs]
        final_picks = sorted(top_by_price, key=lambda item: item["idx"])

        if len(final_picks) < min_legs:
            continue

        for pick in final_picks:
            pick.pop("idx")

        top_sport[sport] = final_picks

    return top_sport