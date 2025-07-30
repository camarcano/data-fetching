#!/usr/bin/env python3
"""
Debug script to test LIDOM (league 131) parameters and find available seasons/games
"""

import requests
import json
from datetime import datetime

BASE_URL = "https://statsapi.mlb.com"

def test_league_info():
    """Test basic league information"""
    print("=== Testing League Information ===")
    
    # Get league info
    try:
        response = requests.get(f"{BASE_URL}/api/v1/league/131")
        if response.status_code == 200:
            league_data = response.json()
            print(f"League 131 found: {json.dumps(league_data, indent=2)}")
        else:
            print(f"League 131 API call failed: {response.status_code}")
    except Exception as e:
        print(f"Error getting league info: {e}")

def test_teams_for_league():
    """Test teams in the league"""
    print("\n=== Testing Teams for League 131 ===")
    
    try:
        response = requests.get(f"{BASE_URL}/api/v1/teams", params={"leagueIds": 131})
        if response.status_code == 200:
            teams_data = response.json()
            teams = teams_data.get('teams', [])
            print(f"Found {len(teams)} teams in league 131:")
            for team in teams:
                print(f"  - {team.get('name')} (ID: {team.get('id')})")
        else:
            print(f"Teams API call failed: {response.status_code}")
    except Exception as e:
        print(f"Error getting teams: {e}")

def test_schedule_variations():
    """Test different parameter combinations for schedule"""
    print("\n=== Testing Schedule API Variations ===")
    
    # Different parameter combinations to try
    test_cases = [
        {"sportId": 17, "leagueId": 131, "season": "2024"},
        {"sportId": 1, "leagueId": 131, "season": "2024"},
        {"sportId": 17, "leagueId": 131, "season": "2024", "gameTypes": "R"},
        {"sportId": 17, "leagueId": 131, "season": "2023"},
        {"sportId": 17, "leagueId": 131, "season": "2025"},
        # Try with date ranges for winter league (Oct 2024 - Feb 2025)
        {"sportId": 17, "leagueId": 131, "startDate": "2024-10-01", "endDate": "2025-02-28"},
        {"sportId": 17, "leagueId": 131, "startDate": "2023-10-01", "endDate": "2024-02-28"},
    ]
    
    for i, params in enumerate(test_cases):
        print(f"\nTest case {i+1}: {params}")
        try:
            response = requests.get(f"{BASE_URL}/api/v1/schedule", params=params)
            print(f"  Status: {response.status_code}")
            print(f"  URL: {response.url}")
            
            if response.status_code == 200:
                data = response.json()
                dates = data.get('dates', [])
                total_games = sum(len(date.get('games', [])) for date in dates)
                print(f"  Result: {len(dates)} dates, {total_games} total games")
                
                if total_games > 0:
                    print("  ✅ SUCCESS - Found games with these parameters!")
                    # Show sample game info
                    first_game = dates[0]['games'][0] if dates and dates[0].get('games') else None
                    if first_game:
                        home_team = first_game.get('teams', {}).get('home', {}).get('team', {}).get('name')
                        away_team = first_game.get('teams', {}).get('away', {}).get('team', {}).get('name')
                        game_date = dates[0].get('date')
                        print(f"    Sample game: {away_team} @ {home_team} on {game_date}")
                else:
                    print("  ❌ No games found")
            else:
                print(f"  ❌ Failed: {response.status_code} - {response.text[:200]}")
                
        except Exception as e:
            print(f"  ❌ Error: {e}")

def test_specific_season_info():
    """Test season-specific endpoints"""
    print("\n=== Testing Season Information ===")
    
    try:
        # Try to get season info
        response = requests.get(f"{BASE_URL}/api/v1/seasons", params={"sportId": 17})
        if response.status_code == 200:
            seasons_data = response.json()
            seasons = seasons_data.get('seasons', [])
            print(f"Available seasons for sport 17 (baseball):")
            for season in seasons[-10:]:  # Show last 10 seasons
                print(f"  - {season.get('seasonId')} ({season.get('regularSeasonStartDate')} to {season.get('regularSeasonEndDate')})")
    except Exception as e:
        print(f"Error getting season info: {e}")

if __name__ == "__main__":
    print("LIDOM (League 131) Debug Script")
    print("=" * 50)
    
    test_league_info()
    test_teams_for_league()
    test_specific_season_info()
    test_schedule_variations()
    
    print("\n" + "=" * 50)
    print("Debug complete. Look for ✅ SUCCESS messages above to find working parameters.")