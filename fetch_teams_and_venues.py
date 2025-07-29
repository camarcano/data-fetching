import requests
import json
import os
from datetime import datetime

# Output folder
OUTPUT_DIR = "output/meta"
os.makedirs(OUTPUT_DIR, exist_ok=True)

API_BASE = "https://statsapi.mlb.com/api/v1"


def fetch_leagues():
    response = requests.get(f"{API_BASE}/league")
    response.raise_for_status()
    leagues = response.json().get("leagues", [])
    return [{
        "id": l["id"],
        "name": l["name"],
        "abbreviation": l.get("abbreviation"),
        "sportId": l.get("sport", {}).get("id"),
        "sportName": l.get("sport", {}).get("name")
    } for l in leagues]


def fetch_teams(league_id=None, sport_id=None):
    params = {}
    if league_id:
        params["leagueIds"] = league_id
    if sport_id:
        params["sportId"] = sport_id

    response = requests.get(f"{API_BASE}/teams", params=params)
    response.raise_for_status()
    teams = response.json().get("teams", [])
    return [{
        "id": team["id"],
        "name": team["name"],
        "abbreviation": team.get("abbreviation"),
        "location": team.get("locationName"),
        "leagueId": team.get("league", {}).get("id"),
        "leagueName": team.get("league", {}).get("name"),
        "sportId": team.get("sport", {}).get("id"),
        "sportName": team.get("sport", {}).get("name")
    } for team in teams]


def fetch_venues():
    response = requests.get(f"{API_BASE}/venues")
    response.raise_for_status()
    venues = response.json().get("venues", [])
    return [{
        "id": venue["id"],
        "name": venue["name"],
        "location": f"{venue.get('city', '')}, {venue.get('state', venue.get('country', ''))}"
    } for venue in venues]


def save_json(data, filename):
    with open(os.path.join(OUTPUT_DIR, filename), "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def save_csv(data, filename):
    import pandas as pd
    df = pd.DataFrame(data)
    df.to_csv(os.path.join(OUTPUT_DIR, filename), index=False)


def main():
    print("Fetching all available leagues...")
    leagues = fetch_leagues()
    save_json(leagues, "leagues.json")
    print(f"Saved {len(leagues)} leagues to leagues.json")

    print("Fetching all venues...")
    venues = fetch_venues()
    save_json(venues, "venues.json")
    print(f"Saved {len(venues)} venues to venues.json")

    print("Fetching teams for common leagues...")
    league_ids = [103, 104, 135, 131, 130, 134]  # MLB, MiLB, LVBP, LIDOM, DSL, LigaMayor
    all_teams = []
    for lid in league_ids:
        try:
            teams = fetch_teams(league_id=lid)
            for team in teams:
                team["fetchedFromLeagueId"] = lid
            all_teams.extend(teams)
            print(f"Fetched {len(teams)} teams for league {lid}")
        except Exception as e:
            print(f"Failed to fetch teams for league {lid}: {e}")

    save_json(all_teams, "teams.json")
    print(f"Saved {len(all_teams)} teams to teams.json")


if __name__ == "__main__":
    main()
