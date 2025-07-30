import pandas as pd
import numpy as np

def calculate_hitter_metrics_from_boxscore(player_id, start_date, end_date, side=None, team_id=None, position=None):
    """
    Calculates baseball metrics for a given hitter from box score data
    over a specified timeframe with optional filters.

    This function is more reliable for summary statistics as it uses pre-aggregated
    data from game box scores. This version includes logic to prevent double-counting
    stats for players with multiple entries in a single game.

    Args:
        player_id (int): The ID of the player.
        start_date (str): The start date of the period (YYYY-MM-DD).
        end_date (str): The end date of the period (YYYY-MM-DD).
        side (str, optional): Filter by 'home' or 'away'. Defaults to None.
        team_id (int, optional): Filter by team ID. Defaults to None.
        position (str, optional): Filter by player position. Defaults to None.

    Returns:
        dict: A dictionary containing the calculated metrics.
    """
    try:
        # Load the dataset from the reliable box score file
        df = pd.read_csv('output/merged_hitters_boxscore_all.csv', low_memory=False)
        # Convert 'date' column to datetime objects for proper filtering
        df['date'] = pd.to_datetime(df['date'])
    except FileNotFoundError:
        return {"error": "The data file 'merged_hitters_boxscore_all.csv' was not found."}

    # --- Step 1: Filter the DataFrame based on the provided criteria ---
    filtered_df = df[
        (df['playerId'] == player_id) &
        (df['date'] >= start_date) &
        (df['date'] <= end_date)
    ]

    # Apply optional filters if they are provided
    if side:
        filtered_df = filtered_df[filtered_df['side'] == side]
    if team_id:
        filtered_df = filtered_df[filtered_df['teamId'] == team_id]
    if position:
        filtered_df = filtered_df[filtered_df['position'] == position]

    if filtered_df.empty:
        return {"message": f"No data found for player {player_id} in the selected timeframe."}

    # --- Step 2: De-duplicate entries to get one final stat line per game ---
    # A player can have multiple rows per game (e.g., substitutions).
    # We find the index of the row with the maximum plate appearances for each game,
    # as this represents the player's final, cumulative stat line.
    # .dropna() is added to handle cases where a player has game entries but no plate appearances.
    final_stats_per_game_idx = filtered_df.groupby('gamePk')['plateAppearances'].idxmax().dropna()
    
    if final_stats_per_game_idx.empty:
        return {"message": f"No games with plate appearances found for player {player_id} in the selected timeframe."}

    deduplicated_df = filtered_df.loc[final_stats_per_game_idx]

    # --- Step 3: Aggregate the stats from the de-duplicated data ---
    # Summing the columns now gives the correct totals for the selected period.
    stats = deduplicated_df[[
        'runs', 'doubles', 'triples', 'homeRuns', 'strikeOuts', 'baseOnBalls',
        'intentionalWalks', 'hits', 'hitByPitch', 'atBats', 'caughtStealing',
        'stolenBases', 'plateAppearances', 'totalBases', 'rbi', 'sacBunts', 
        'sacFlies'
    ]].sum()

    # --- Step 4: Calculate the final metrics ---
    metrics = {}
    
    # Extract summed values for easier use in formulas
    at_bats = stats['atBats']
    hits = stats['hits']
    walks = stats['baseOnBalls']
    hbp = stats['hitByPitch']
    sac_flies = stats['sacFlies']
    plate_appearances = stats['plateAppearances']
    total_bases = stats['totalBases']
    strikeouts = stats['strikeOuts']
    stolen_bases = stats['stolenBases']
    caught_stealing = stats['caughtStealing']
    home_runs = stats['homeRuns']

    # Standard Metrics
    metrics['AVG'] = hits / at_bats if at_bats > 0 else 0
    obp_denominator = at_bats + walks + hbp + sac_flies
    metrics['OBP'] = (hits + walks + hbp) / obp_denominator if obp_denominator > 0 else 0
    metrics['SLG'] = total_bases / at_bats if at_bats > 0 else 0
    metrics['OPS'] = metrics['OBP'] + metrics['SLG']

    # Counting Stats
    metrics['PlateAppearances'] = int(plate_appearances)
    metrics['AtBats'] = int(at_bats)
    metrics['Hits'] = int(hits)
    metrics['Runs'] = int(stats['runs'])
    metrics['RBI'] = int(stats['rbi'])
    metrics['Doubles'] = int(stats['doubles'])
    metrics['Triples'] = int(stats['triples'])
    metrics['HomeRuns'] = int(home_runs)
    metrics['Walks'] = int(walks)
    metrics['Strikeouts'] = int(strikeouts)
    metrics['StolenBases'] = int(stolen_bases)
    
    # Advanced Metrics
    metrics['ISO'] = metrics['SLG'] - metrics['AVG']
    metrics['BB/K'] = walks / strikeouts if strikeouts > 0 else float('inf') if walks > 0 else 0
    sb_attempts = stolen_bases + caught_stealing
    metrics['SB%'] = stolen_bases / sb_attempts if sb_attempts > 0 else 0
    metrics['HR%'] = home_runs / plate_appearances if plate_appearances > 0 else 0
    metrics['K%'] = strikeouts / plate_appearances if plate_appearances > 0 else 0
    metrics['BB%'] = walks / plate_appearances if plate_appearances > 0 else 0

    return metrics

# --- Example of How to Use the Function ---

if __name__ == "__main__":
    # --- Input Parameters for the player in question ---
    player_id_to_analyze = 606299 
    start_date_str = '2024-10-01'
    end_date_str = '2025-01-25'

    # --- Calculation ---
    player_stats = calculate_hitter_metrics_from_boxscore(
        player_id=player_id_to_analyze,
        start_date=start_date_str,
        end_date=end_date_str
    )

    # --- Display Results ---
    print(f"Hitter Metrics for Player ID: {player_id_to_analyze} (from Box Score Data)")
    print(f"From: {start_date_str} to {end_date_str}\n")

    if 'error' in player_stats or 'message' in player_stats:
        print(player_stats.get('error') or player_stats.get('message'))
    else:
        for stat, value in player_stats.items():
            if isinstance(value, float):
                print(f"{stat}: {value:.3f}")
            else:
                print(f"{stat}: {value}")
