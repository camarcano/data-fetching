import pandas as pd

def calculate_hitter_metrics(player_id, start_date, end_date, side=None, team_id=None, position=None):
    """
    Calculates baseball metrics for a given hitter over a specified timeframe with optional filters.

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
    # Load the dataset and convert 'date' column
    df = pd.read_csv('output\merged_hitters_boxscore_all.csv')
    df['date'] = pd.to_datetime(df['date'])
    
    # Filter the DataFrame based on the provided criteria
    filtered_df = df[
        (df['playerId'] == player_id) &
        (df['date'] >= start_date) &
        (df['date'] <= end_date)
    ]

    if side:
        filtered_df = filtered_df[filtered_df['side'] == side]
    if team_id:
        filtered_df = filtered_df[filtered_df['teamId'] == team_id]
    if position:
        filtered_df = filtered_df[filtered_df['position'] == position]

    # Aggregate the stats
    aggregated_stats = filtered_df[[
        'runs', 'doubles', 'triples', 'homeRuns', 'strikeOuts', 'baseOnBalls',
        'intentionalWalks', 'hits', 'hitByPitch', 'atBats', 'caughtStealing',
        'stolenBases', 'groundIntoDoublePlay', 'plateAppearances', 'totalBases',
        'rbi', 'leftOnBase', 'sacBunts', 'sacFlies'
    ]].sum()

    # Calculate the metrics
    metrics = {}
    at_bats = aggregated_stats['atBats']
    hits = aggregated_stats['hits']
    walks = aggregated_stats['baseOnBalls']
    hbp = aggregated_stats['hitByPitch']
    sac_flies = aggregated_stats['sacFlies']
    plate_appearances = aggregated_stats['plateAppearances']
    total_bases = aggregated_stats['totalBases']
    strikeouts = aggregated_stats['strikeOuts']
    stolen_bases = aggregated_stats['stolenBases']
    caught_stealing = aggregated_stats['caughtStealing']
    home_runs = aggregated_stats['homeRuns']

    # Batting Average (AVG)
    metrics['AVG'] = hits / at_bats if at_bats > 0 else 0

    # On-Base Percentage (OBP)
    obp_denominator = at_bats + walks + hbp + sac_flies
    metrics['OBP'] = (hits + walks + hbp) / obp_denominator if obp_denominator > 0 else 0

    # Slugging Percentage (SLG)
    metrics['SLG'] = total_bases / at_bats if at_bats > 0 else 0

    # On-Base Plus Slugging (OPS)
    metrics['OPS'] = metrics['OBP'] + metrics['SLG']
    
    # Other stats
    metrics['RBI'] = aggregated_stats['rbi']
    metrics['Runs'] = aggregated_stats['runs']
    metrics['Doubles'] = aggregated_stats['doubles']
    metrics['Triples'] = aggregated_stats['triples']
    metrics['HomeRuns'] = home_runs
    metrics['StolenBases'] = stolen_bases

    # Advanced Metrics
    metrics['BB/K'] = walks / strikeouts if strikeouts > 0 else float('inf') if walks > 0 else 0
    sb_attempts = stolen_bases + caught_stealing
    metrics['SB%'] = stolen_bases / sb_attempts if sb_attempts > 0 else 0
    metrics['ISO'] = metrics['SLG'] - metrics['AVG']
    metrics['HR%'] = home_runs / plate_appearances if plate_appearances > 0 else 0
    metrics['K%'] = strikeouts / plate_appearances if plate_appearances > 0 else 0
    metrics['BB%'] = walks / plate_appearances if plate_appearances > 0 else 0

    return metrics

# --- Example of How to Use the Function ---

if __name__ == "__main__":
    # --- Input Parameters ---
    player_id_to_analyze = 600524
    start_date_str = '2024-10-01'
    end_date_str = '2025-01-25'

    # --- Calculation ---
    player_stats = calculate_hitter_metrics(
        player_id=player_id_to_analyze,
        start_date=start_date_str,
        end_date=end_date_str
    )

    # --- Display Results ---
    print(f"Hitter Metrics for Player ID: {player_id_to_analyze}")
    print(f"From: {start_date_str} to {end_date_str}\n")

    for stat, value in player_stats.items():
        if isinstance(value, float):
            print(f"{stat}: {value:.3f}")
        else:
            print(f"{stat}: {value}")

    # --- Example with Optional Filters (Home Games Only) ---
    player_stats_home = calculate_hitter_metrics(
        player_id=player_id_to_analyze,
        start_date=start_date_str,
        end_date=end_date_str,
        side='home'
    )
    
    print(f"\n--- Metrics for Home Games Only ---")
    for stat, value in player_stats_home.items():
        if isinstance(value, float):
            print(f"{stat}: {value:.3f}")
        else:
            print(f"{stat}: {value}")