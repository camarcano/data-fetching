# config.py

import argparse
from datetime import datetime

def parse_arguments():
    parser = argparse.ArgumentParser(description="LVBP Data Fetcher")

    parser.add_argument('--season', type=str, default='2024', help='Season year (e.g. 2024)')
    parser.add_argument('--league_id', type=int, default=135, help='League ID (default: 135 for LVBP)')
    parser.add_argument('--sport_id', type=int, default=17, help='Sport ID (default: 17 for baseball)')

    parser.add_argument('--use_date_range', action='store_true', help='Enable date range filter')
    parser.add_argument('--start_date', type=str, help='Start date (YYYY-MM-DD)')
    parser.add_argument('--end_date', type=str, help='End date (YYYY-MM-DD)')

    parser.add_argument('--include_postseason', action='store_true', help='Include postseason games')
    parser.add_argument('--regular_season', action='store_true', help='Include regular season games')

    parser.add_argument('--team_id', type=int, help='Filter by team ID')
    parser.add_argument('--venue_id', type=int, help='Filter by stadium (venue) ID')
    parser.add_argument('--home_only', action='store_true', help='Fetch only home games')
    parser.add_argument('--away_only', action='store_true', help='Fetch only away games')

    parser.add_argument('--output_dir', type=str, default='output', help='Folder for output files')

    return parser.parse_args()

def validate_date_format(date_str):
    try:
        datetime.strptime(date_str, '%Y-%m-%d')
        return True
    except ValueError:
        return False
