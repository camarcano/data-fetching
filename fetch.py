# fetch.py

import requests
import logging

BASE_URL = "https://statsapi.mlb.com"

def fetch_game_pks(args):
    """
    Fetches gamePks for the given filters in args.
    """
    game_pks = []
    params = {
        "sportId": args.sport_id,
        "leagueId": args.league_id,
        "season": args.season,
    }

    # Add date range if specified
    if args.use_date_range:
        if args.start_date and args.end_date:
            params["startDate"] = args.start_date
            params["endDate"] = args.end_date

    # Determine game types
    game_types = []
    if args.regular_season:
        game_types.append("R")
    if args.include_postseason:
        game_types.append("P")

    if not game_types:
        game_types = ["R"]  # Default to regular season if nothing is specified

    for game_type in game_types:
        params["gameTypes"] = game_type
        schedule_url = f"{BASE_URL}/api/v1/schedule"

        try:
            response = requests.get(schedule_url, params=params)
            response.raise_for_status()
            schedule_data = response.json()

            for date_data in schedule_data.get('dates', []):
                for game in date_data.get('games', []):
                    # Apply team and stadium filtering
                    if args.team_id and args.team_id not in [game.get("teams", {}).get("home", {}).get("team", {}).get("id"),
                                                             game.get("teams", {}).get("away", {}).get("team", {}).get("id")]:
                        continue

                    if args.venue_id and game.get("venue", {}).get("id") != args.venue_id:
                        continue

                    if args.home_only and args.team_id and args.team_id != game.get("teams", {}).get("home", {}).get("team", {}).get("id"):
                        continue

                    if args.away_only and args.team_id and args.team_id != game.get("teams", {}).get("away", {}).get("team", {}).get("id"):
                        continue

                    game_pks.append({
                        "gamePk": game["gamePk"],
                        "date": date_data["date"]
                    })

        except requests.RequestException as e:
            logging.error(f"Error fetching schedule for type {game_type}: {e}")

    logging.info(f"Fetched {len(game_pks)} gamePks for season {args.season}")
    return game_pks
