# game.py

import requests
import logging
import json
from pathlib import Path

BASE_URL = "https://statsapi.mlb.com"

def fetch_hydrated_game_data(game_pk):
    """
    Fetch the hydrated live data feed for a given gamePk.
    """
    hydrations = "credits,alignment,flags,officials,preState"
    url = f"{BASE_URL}/api/v1.1/game/{game_pk}/feed/live?hydrate={hydrations}"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Could not fetch game data for gamePk {game_pk}: {e}")
    except json.JSONDecodeError:
        logging.error(f"JSON decode failed for gamePk {game_pk}")
    return None

def fetch_boxscore_data(game_pk):
    """
    Fetch the boxscore JSON for a given gamePk.
    """
    url = f"{BASE_URL}/api/v1/game/{game_pk}/boxscore"

    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        logging.error(f"Could not fetch boxscore for gamePk {game_pk}: {e}")
    except json.JSONDecodeError:
        logging.error(f"JSON decode failed for boxscore of gamePk {game_pk}")
    return None

def save_boxscore_csvs(boxscore_json, game_pk, game_date, output_dir="output"):
    """
    Save hitter and pitcher stats from a boxscore JSON to separate CSV files.
    """
    hitters = []
    pitchers = []

    teams = ["home", "away"]
    for team_key in teams:
        team_data = boxscore_json.get("teams", {}).get(team_key, {})
        players = team_data.get("players", {})
        team_id = team_data.get("team", {}).get("id")
        team_name = team_data.get("team", {}).get("name")

        for player_id, player in players.items():
            stats = player.get("stats", {})
            if not stats:
                continue

            common_data = {
                "gamePk": game_pk,
                "date": game_date,
                "teamId": team_id,
                "teamName": team_name,
                "playerId": player.get("person", {}).get("id"),
                "playerName": player.get("person", {}).get("fullName"),
                "position": player.get("position", {}).get("abbreviation"),
                "battingOrder": player.get("battingOrder"),
                "isSubstitute": player.get("isSubstitute"),
                "side": team_key
            }

            if "batting" in stats:
                hitters.append({**common_data, **stats["batting"]})

            if "pitching" in stats:
                pitchers.append({**common_data, **stats["pitching"]})

    # Ensure output path
    Path(output_dir).mkdir(exist_ok=True)
    hit_file = Path(output_dir) / f"{game_date}_gamePk_{game_pk}_hitters.csv"
    pit_file = Path(output_dir) / f"{game_date}_gamePk_{game_pk}_pitchers.csv"

    import pandas as pd
    if hitters:
        pd.DataFrame(hitters).to_csv(hit_file, index=False)
        logging.info(f"Saved hitters boxscore: {hit_file}")
    if pitchers:
        pd.DataFrame(pitchers).to_csv(pit_file, index=False)
        logging.info(f"Saved pitchers boxscore: {pit_file}")
