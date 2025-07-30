# fetch.py

import requests
import logging
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

BASE_URL = "https://statsapi.mlb.com"

def create_session_with_retries():
    """Create a requests session with retry strategy"""
    session = requests.Session()
    
    # Define retry strategy
    retry_strategy = Retry(
        total=5,  # Total number of retries
        backoff_factor=2,  # Wait time between retries (exponential backoff)
        status_forcelist=[429, 500, 502, 503, 504],  # HTTP status codes to retry on
        allowed_methods=["HEAD", "GET", "OPTIONS"]  # HTTP methods to retry
    )
    
    # Mount adapter with retry strategy
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount("http://", adapter)
    session.mount("https://", adapter)
    
    return session

def make_api_request(url, params, max_retries=3, delay=2):
    """Make API request with custom retry logic for connection timeouts"""
    session = create_session_with_retries()
    
    for attempt in range(max_retries):
        try:
            logging.info(f"Attempt {attempt + 1}/{max_retries} - Making request to: {url}")
            logging.info(f"Parameters: {params}")
            
            # Set reasonable timeout (connect_timeout, read_timeout)
            response = session.get(url, params=params, timeout=(10, 30))
            response.raise_for_status()
            
            logging.info(f"✅ Request successful on attempt {attempt + 1}")
            return response.json()
            
        except requests.exceptions.ConnectTimeout as e:
            logging.warning(f"⚠️ Connection timeout on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)  # Exponential backoff
                logging.info(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logging.error(f"❌ All {max_retries} attempts failed due to connection timeout")
                raise
                
        except requests.exceptions.ReadTimeout as e:
            logging.warning(f"⚠️ Read timeout on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                logging.info(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logging.error(f"❌ All {max_retries} attempts failed due to read timeout")
                raise
                
        except requests.exceptions.RequestException as e:
            logging.warning(f"⚠️ Request error on attempt {attempt + 1}: {e}")
            if attempt < max_retries - 1:
                wait_time = delay * (2 ** attempt)
                logging.info(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                logging.error(f"❌ All {max_retries} attempts failed due to request error")
                raise
    
    return None

def fetch_game_pks(args):
    """
    Fetches gamePks for the given filters in args.
    """
    game_pks = []
    
    # Base parameters
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

    # Determine game types - but some leagues don't support gameTypes parameter
    game_types = []
    if args.regular_season:
        game_types.append("R")
    if args.include_postseason:
        game_types.append("P")

    if not game_types:
        game_types = ["R"]  # Default to regular season if nothing is specified

    # Special handling for leagues that don't support gameTypes parameter
    # Based on testing, LIDOM (131) and potentially other non-MLB leagues have issues with gameTypes
    problematic_leagues = [131, 135, 130, 134]  # LIDOM, LVBP, DSL, etc.
    use_game_types = args.league_id not in problematic_leagues

    logging.info(f"Using parameters: {params}")
    logging.info(f"Game types: {game_types}")
    logging.info(f"Will use gameTypes parameter: {use_game_types}")

    if use_game_types:
        # Use separate requests for each game type (original behavior for MLB)
        for game_type in game_types:
            temp_params = params.copy()
            temp_params["gameTypes"] = game_type
            schedule_url = f"{BASE_URL}/api/v1/schedule"

            try:
                schedule_data = make_api_request(schedule_url, temp_params)
                if not schedule_data:
                    continue

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

            except Exception as e:
                logging.error(f"Error fetching schedule for type {game_type}: {e}")
                continue

    else:
        # Make single request without gameTypes parameter (for problematic leagues)
        schedule_url = f"{BASE_URL}/api/v1/schedule"

        try:
            schedule_data = make_api_request(schedule_url, params)
            if not schedule_data:
                logging.error("Failed to fetch schedule data after all retries")
                return game_pks

            total_dates = len(schedule_data.get('dates', []))
            logging.info(f"📅 Received {total_dates} dates from API")

            for date_data in schedule_data.get('dates', []):
                games_on_date = len(date_data.get('games', []))
                if games_on_date > 0:
                    logging.info(f"📅 {date_data.get('date')}: {games_on_date} games")
                
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

                    # Filter by game type manually if needed
                    game_type = game.get('gameType', 'R')
                    if args.regular_season and game_type != 'R':
                        continue
                    if args.include_postseason and game_type != 'P':
                        if not args.regular_season:  # Only skip if we're not also including regular season
                            continue

                    game_pks.append({
                        "gamePk": game["gamePk"],
                        "date": date_data["date"]
                    })

        except Exception as e:
            logging.error(f"Failed to fetch schedule after all retries: {e}")
            return game_pks

    logging.info(f"🎯 Fetched {len(game_pks)} gamePks for season {args.season}")
    return game_pks