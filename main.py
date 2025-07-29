# main.py

import argparse
import logging
from pathlib import Path

from fetch import fetch_game_pks
from game import fetch_hydrated_game_data, fetch_boxscore_data, save_boxscore_csvs
from processor import extract_pitch_by_pitch

def parse_args():
    parser = argparse.ArgumentParser(description="Fetch MLB GUMBO data and boxscores with filters.")
    parser.add_argument("--season", type=str, required=True, help="Season year (e.g. 2023)")
    parser.add_argument("--start_date", type=str, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--end_date", type=str, help="End date (YYYY-MM-DD)")
    parser.add_argument("--use_date_range", action="store_true", help="Use date range filter instead of full season")
    parser.add_argument("--regular_season", action="store_true", help="Include regular season games")
    parser.add_argument("--include_postseason", action="store_true", help="Include postseason games")
    parser.add_argument("--team_id", type=int, help="Filter by team ID")
    parser.add_argument("--venue_id", type=int, help="Filter by venue (stadium) ID")
    parser.add_argument("--home_only", action="store_true", help="Only include games where team is home")
    parser.add_argument("--away_only", action="store_true", help="Only include games where team is away")
    parser.add_argument("--output_dir", type=str, default="output", help="Directory to save outputs")
    parser.add_argument("--league_id", type=int, default=103, help="League ID (e.g. 103 = AL, 104 = NL)")
    parser.add_argument("--sport_id", type=int, default=1, help="Sport ID (default 1 = MLB)")
    return parser.parse_args()

def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    args = parse_args()

    Path(args.output_dir).mkdir(exist_ok=True)

    game_infos = fetch_game_pks(args)

    for game_info in game_infos:
        game_pk = game_info["gamePk"]
        game_date = game_info["date"]
        logging.info(f"Processing gamePk {game_pk} on {game_date}")

        game_json = fetch_hydrated_game_data(game_pk)
        if not game_json:
            continue

        extract_pitch_by_pitch(game_json, game_pk, game_date, args.output_dir)

        boxscore_json = fetch_boxscore_data(game_pk)
        if boxscore_json:
            save_boxscore_csvs(boxscore_json, game_pk, game_date, args.output_dir)

if __name__ == "__main__":
    main()
