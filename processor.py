# processor.py

import pandas as pd
import logging
from pathlib import Path

def extract_pitch_by_pitch(game_json, game_pk, game_date, output_dir="output"):
    """
    Extracts pitch-by-pitch data, including hit locations when available.
    """
    all_pitches = []
    all_plays = game_json.get("liveData", {}).get("plays", {}).get("allPlays", [])

    for play in all_plays:
        play_events = play.get("playEvents", [])
        batter = play.get("matchup", {}).get("batter", {}).get("fullName")
        pitcher = play.get("matchup", {}).get("pitcher", {}).get("fullName")
        batter_id = play.get("matchup", {}).get("batter", {}).get("id")
        pitcher_id = play.get("matchup", {}).get("pitcher", {}).get("id")
        inning = play.get("about", {}).get("inning")
        top_bottom = play.get("about", {}).get("halfInning")

        for event in play_events:
            pitch_data = {
                "gamePk": game_pk,
                "date": game_date,
                "inning": inning,
                "halfInning": top_bottom,
                "batter": batter,
                "batterId": batter_id,
                "pitcher": pitcher,
                "pitcherId": pitcher_id,
                "eventType": event.get("type"),
                "description": event.get("details", {}).get("description"),
                "pitchType": event.get("details", {}).get("type", {}).get("description"),
                "isInPlay": event.get("details", {}).get("isInPlay"),
                "isStrike": event.get("details", {}).get("isStrike"),
                "isBall": event.get("details", {}).get("isBall"),
                "startSpeed": event.get("pitchData", {}).get("startSpeed"),
                "endSpeed": event.get("pitchData", {}).get("endSpeed"),
                "strikeZoneTop": event.get("pitchData", {}).get("strikeZoneTop"),
                "strikeZoneBottom": event.get("pitchData", {}).get("strikeZoneBottom"),
                "zone": event.get("pitchData", {}).get("zone"),
                "coordinates_x": event.get("hitData", {}).get("coordinates", {}).get("coordX"),
                "coordinates_y": event.get("hitData", {}).get("coordinates", {}).get("coordY"),
                "launchAngle": event.get("hitData", {}).get("launchAngle"),
                "launchSpeed": event.get("hitData", {}).get("launchSpeed"),
                "totalDistance": event.get("hitData", {}).get("totalDistance")
            }

            all_pitches.append(pitch_data)

    if all_pitches:
        Path(output_dir).mkdir(exist_ok=True)
        file_path = Path(output_dir) / f"{game_date}_gamePk_{game_pk}_pitch_by_pitch.csv"
        df = pd.DataFrame(all_pitches)
        df.to_csv(file_path, index=False)
        logging.info(f"Saved pitch-by-pitch data: {file_path}")

