#!/usr/bin/env python3
"""
Simple test to verify MLB Stats API connectivity for LIDOM
"""

import requests
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s - %(message)s')

def test_api_connection():
    """Test basic API connectivity"""
    print("🔍 Testing MLB Stats API connectivity...")
    
    # Simple test endpoint
    test_url = "https://statsapi.mlb.com/api/v1/league/131"
    
    try:
        response = requests.get(test_url, timeout=(5, 10))
        if response.status_code == 200:
            print("✅ Basic API connection successful")
            return True
        else:
            print(f"❌ API returned status code: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection failed: {e}")
        return False

def test_schedule_endpoint():
    """Test the specific schedule endpoint for LIDOM 2024"""
    print("\n🔍 Testing LIDOM 2024 schedule endpoint...")
    
    params = {
        "sportId": 17,
        "leagueId": 131,
        "season": "2024"
    }
    
    url = "https://statsapi.mlb.com/api/v1/schedule"
    
    for attempt in range(3):
        try:
            print(f"  Attempt {attempt + 1}/3...")
            response = requests.get(url, params=params, timeout=(10, 30))
            
            if response.status_code == 200:
                data = response.json()
                dates = data.get('dates', [])
                total_games = sum(len(date.get('games', [])) for date in dates)
                print(f"✅ Schedule endpoint successful: {len(dates)} dates, {total_games} games")
                
                if total_games > 0:
                    # Show sample game
                    first_game = dates[0]['games'][0] if dates and dates[0].get('games') else None
                    if first_game:
                        home_team = first_game.get('teams', {}).get('home', {}).get('team', {}).get('name')
                        away_team = first_game.get('teams', {}).get('away', {}).get('team', {}).get('name')
                        game_date = dates[0].get('date')
                        print(f"  📅 Sample game: {away_team} @ {home_team} on {game_date}")
                
                return True
            else:
                print(f"❌ Schedule endpoint returned status: {response.status_code}")
                
        except requests.exceptions.ConnectTimeout:
            print(f"⚠️ Connection timeout on attempt {attempt + 1}")
            if attempt < 2:
                wait_time = 2 * (attempt + 1)
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
        except requests.exceptions.ReadTimeout:
            print(f"⚠️ Read timeout on attempt {attempt + 1}")
            if attempt < 2:
                wait_time = 2 * (attempt + 1)
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
                
        except Exception as e:
            print(f"❌ Request failed on attempt {attempt + 1}: {e}")
            if attempt < 2:
                wait_time = 2 * (attempt + 1)
                print(f"⏳ Waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
    
    print("❌ All attempts failed for schedule endpoint")
    return False

def main():
    print("🧪 MLB Stats API Connectivity Test")
    print("=" * 50)
    
    # Test basic connectivity
    basic_ok = test_api_connection()
    
    if basic_ok:
        # Test specific endpoint
        schedule_ok = test_schedule_endpoint()
        
        if schedule_ok:
            print("\n🎉 All tests passed! Your API connection is working.")
            print("💡 You can now run: python main.py --season 2024 --league_id 131 --regular_season")
        else:
            print("\n⚠️ Basic connection works but schedule endpoint is having issues.")
            print("💡 This might be temporary. Try again in a few minutes.")
    else:
        print("\n❌ Basic API connection failed.")
        print("💡 Check your internet connection and try again.")
    
    print("\n" + "=" * 50)

if __name__ == "__main__":
    main()