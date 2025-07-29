import requests
import pandas as pd
import time
from datetime import datetime
import logging
import json
from tqdm import tqdm

# --- CONFIGURATION ---
SEASON = "2024"
LEAGUE_ID = 135 
SPORT_ID = 17
BASE_URL = "https://statsapi.mlb.com"

# Toggle this to True if you want to fetch a specific date range instead of the whole season
USE_DATE_RANGE = False
START_DATE = "2024-12-01"
END_DATE = "2024-12-15"


# --- LOGGING SETUP ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_season_game_pks_with_dates(season, league_id, sport_id):
    if USE_DATE_RANGE:
        url = f"{BASE_URL}/api/v1/schedule?startDate={START_DATE}&endDate={END_DATE}&sportId={sport_id}&leagueId={league_id}"
        logger.info(f"Fetching games from {START_DATE} to {END_DATE}")
    else:
        url = f"{BASE_URL}/api/v1/schedule?season={season}&sportId={sport_id}&leagueId={league_id}"
        logger.info(f"Fetching full-season games for {season}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        schedule_data = response.json()
        games = []
        for date_data in schedule_data.get('dates', []):
            game_date = date_data.get('date')
            for game in date_data.get('games', []):
                games.append((game['gamePk'], game_date))
        logger.info(f"Found {len(games)} games.")
        return games
    except Exception as e:
        logger.error(f"Failed to fetch schedule: {e}")
        return []

def fetch_hydrated_game_data(game_pk):
    url = f"{BASE_URL}/api/v1.1/game/{game_pk}/feed/live"
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        logger.error(f"Error fetching game {game_pk}: {e}")
        return None

def fetch_boxscore(game_pk, game_date):
    url = f"{BASE_URL}/api/v1/game/{game_pk}/boxscore"
    try:
        response = requests.get(url)
        response.raise_for_status()
        raw = response.json()
        raw["gamePk"] = game_pk

        away = extract_team_box(raw, "away")
        home = extract_team_box(raw, "home")

        return {
            "gamePk": game_pk,
            "date": game_date,
            "awayTeam": raw.get("teams", {}).get("away", {}).get("team", {}).get("name"),
            "homeTeam": raw.get("teams", {}).get("home", {}).get("team", {}).get("name"),
            "hitters": [dict(p, date=game_date) for p in away["hitters"] + home["hitters"]],
            "pitchers": [dict(p, date=game_date) for p in away["pitchers"] + home["pitchers"]],
        }

    except Exception as e:
        logger.error(f"Error fetching boxscore for game {game_pk}: {e}")
        return None

def extract_team_box(data, team_key):
    team_data = data.get('teams', {}).get(team_key, {})
    players = team_data.get('players', {})
    hitters, pitchers = [], []

    for pid, player in players.items():
        person = player.get('person', {})
        position = player.get('position', {}).get('abbreviation')
        stats = player.get('stats', {})
        batting = stats.get("batting")
        pitching = stats.get("pitching")

        player_common = {
            "gamePk": data.get("gamePk"),
            "team": team_data.get("team", {}).get("name"),
            "playerId": pid,
            "fullName": person.get("fullName"),
            "position": position,
        }

        if batting:
            hitters.append({**player_common, **batting})
        if pitching:
            pitchers.append({**player_common, **pitching})

    return {"hitters": hitters, "pitchers": pitchers}

def process_and_load_data(all_game_data):
    all_pitch_events = []
    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    logger.info("Processing pitch-by-pitch data...")

    for game_data in tqdm(all_game_data, desc="Processing games"):
        game_pk = game_data.get('gamePk')
        game_date = game_data.get('gameData', {}).get('datetime', {}).get('originalDate')
        plays = game_data.get('liveData', {}).get('plays', {}).get('allPlays', [])

        for play in plays:
            about = play.get('about', {})
            result = play.get('result', {})
            matchup = play.get('matchup', {})

            at_bat_context = {
                'gamePk': game_pk,
                'date': game_date,
                'atBatIndex': about.get('atBatIndex'),
                'inning': about.get('inning'),
                'halfInning': about.get('halfInning'),
                'batterId': matchup.get('batter', {}).get('id'),
                'batterName': matchup.get('batter', {}).get('fullName'),
                'pitcherId': matchup.get('pitcher', {}).get('id'),
                'pitcherName': matchup.get('pitcher', {}).get('fullName'),
                'atBatResultEvent': result.get('event'),
                'atBatResultType': result.get('eventType'),
                'atBatResultDescription': result.get('description'),
                'rbi': result.get('rbi'),
            }

            if not play.get('playEvents'):
                continue

            for event in play.get('playEvents'):
                pitch_record = at_bat_context.copy()
                pitch_details = event.get('details', {})
                pitch_data = event.get('pitchData', {})
                hit_data = pitch_data.get('hitData', {}) if pitch_data else {}

                pitch_record.update({
                    'pitchNumber': event.get('pitchNumber'),
                    'isPitch': event.get('isPitch'),
                    'type': event.get('type'),
                    'callDescription': pitch_details.get('call', {}).get('description'),
                    'pitchType': pitch_details.get('type', {}).get('description'),
                    'isInPlay': event.get('isInPlay'),
                    'isStrike': event.get('isStrike'),
                    'isBall': event.get('isBall'),
                    'startSpeed': pitch_data.get('startSpeed'),
                    'spinRate': pitch_data.get('breaks', {}).get('spinRate'),
                    'hitLaunchSpeed': hit_data.get('launchSpeed'),
                    'hitLaunchAngle': hit_data.get('launchAngle'),
                    'hitDistance': hit_data.get('totalDistance'),
                    'hitTrajectory': hit_data.get('trajectory'),
                })

                all_pitch_events.append(pitch_record)

    if all_pitch_events:
        df = pd.DataFrame(all_pitch_events)
        filename = f"lvbp_{SEASON}_unified_pitch_log_{now}.csv"
        df.to_csv(filename, index=False)
        logger.info(f"✅ Saved {len(df)} pitch events to {filename}")
    else:
        logger.warning("No pitch data extracted.")

def save_boxscore_json(boxscore_data, season):
    now = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lvbp_{season}_boxscores_{now}.json"
    with open(filename, "w") as f:
        json.dump(boxscore_data, f, indent=2)
    logger.info(f"✅ Saved all box scores to JSON: {filename}")

def save_boxscore_csvs(boxscore_data_dict, season):
    all_hitters = []
    all_pitchers = []

    for box in boxscore_data_dict.values():
        all_hitters.extend(box["hitters"])
        all_pitchers.extend(box["pitchers"])

    now = datetime.now().strftime("%Y%m%d_%H%M%S")

    if all_hitters:
        hitters_df = pd.DataFrame(all_hitters)
        hitters_df.to_csv(f"lvbp_{season}_hitters_boxscore_{now}.csv", index=False)
        logger.info(f"✅ Saved {len(hitters_df)} hitter lines to CSV.")

    if all_pitchers:
        pitchers_df = pd.DataFrame(all_pitchers)
        pitchers_df.to_csv(f"lvbp_{season}_pitchers_boxscore_{now}.csv", index=False)
        logger.info(f"✅ Saved {len(pitchers_df)} pitcher lines to CSV.")

# --- MAIN ---
if __name__ == "__main__":
    logger.info(f"🚀 Starting LVBP {SEASON} Game Data Collection")

    game_info_list = get_season_game_pks_with_dates(SEASON, LEAGUE_ID, SPORT_ID)
    all_game_data = []
    boxscore_data = {}

    for game_pk, game_date in tqdm(game_info_list, desc="Fetching games"):
        game_data = fetch_hydrated_game_data(game_pk)
        if game_data:
            all_game_data.append(game_data)

        box = fetch_boxscore(game_pk, game_date)
        if box:
            boxscore_data[str(game_pk)] = box

        time.sleep(1)


    if all_game_data:
        process_and_load_data(all_game_data)

    if boxscore_data:
        save_boxscore_json(boxscore_data, SEASON)
        save_boxscore_csvs(boxscore_data, SEASON)

    logger.info("🎉 Data collection complete.")
