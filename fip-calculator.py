import pandas as pd
import numpy as np

def calculate_fip_without_hbp(hr, bb, k, ip, fip_constant):
    """
    Calculate FIP without HBP using the formula:
    FIP = ((13 × HR) + (3 × BB) - (2 × K)) / IP + constant
    """
    if ip == 0:
        return np.nan
    
    return ((13 * hr) + (3 * bb) - (2 * k)) / ip + fip_constant

def calculate_fip_constant(league_hr, league_bb, league_k, league_ip, league_era):
    """
    Calculate the FIP constant to normalize FIP to league ERA
    Constant = League ERA - ((13 × lgHR + 3 × lgBB - 2 × lgK) / lgIP)
    """
    if league_ip == 0:
        return 0
    
    return league_era - ((13 * league_hr + 3 * league_bb - 2 * league_k) / league_ip)

def main():
    # Read the CSV files
    try:
        team_data = pd.read_csv('2024-teams-lvbp.csv')
        individual_data = pd.read_csv('2024-individual-lvbp.csv')
        print("Files loaded successfully!")
    except FileNotFoundError as e:
        print(f"Error loading files: {e}")
        return
    
    # Display basic info about the data
    print(f"\nTeam data: {len(team_data)} teams")
    print(f"Individual data: {len(individual_data)} pitchers")
    
    # Calculate league totals from team data
    league_totals = {
        'IP': team_data['IP'].sum(),
        'HR': team_data['HR'].sum(),
        'BB': team_data['BB'].sum(),
        'K': team_data['K'].sum(),
        'CL': team_data['CL'].sum()  # CL = Earned Runs
    }
    
    # Calculate league ERA
    league_era = (league_totals['CL'] * 9) / league_totals['IP'] if league_totals['IP'] > 0 else 0
    
    # Calculate FIP constant
    fip_constant = calculate_fip_constant(
        league_totals['HR'], 
        league_totals['BB'], 
        league_totals['K'], 
        league_totals['IP'], 
        league_era
    )
    
    print(f"\n=== LEAGUE STATISTICS ===")
    print(f"Total Innings Pitched: {league_totals['IP']:.1f}")
    print(f"Total Home Runs: {league_totals['HR']}")
    print(f"Total Walks: {league_totals['BB']}")
    print(f"Total Strikeouts: {league_totals['K']}")
    print(f"Total Earned Runs: {league_totals['CL']}")
    print(f"League ERA: {league_era:.3f}")
    print(f"FIP Constant: {fip_constant:.3f}")
    
    # Calculate league FIP
    league_fip = calculate_fip_without_hbp(
        league_totals['HR'],
        league_totals['BB'], 
        league_totals['K'],
        league_totals['IP'],
        fip_constant
    )
    print(f"League FIP: {league_fip:.3f}")
    
    # Calculate FIP for each team
    print(f"\n=== TEAM FIP CALCULATIONS ===")
    team_results = []
    
    for _, team in team_data.iterrows():
        team_fip = calculate_fip_without_hbp(
            team['HR'], 
            team['BB'], 
            team['K'], 
            team['IP'], 
            fip_constant
        )
        
        team_era = (team['CL'] * 9) / team['IP'] if team['IP'] > 0 else 0
        
        team_results.append({
            'Team': team['EQUIPO'],
            'IP': team['IP'],
            'ERA': team_era,
            'FIP': team_fip,
            'FIP-ERA': team_fip - team_era,
            'HR': team['HR'],
            'BB': team['BB'],
            'K': team['K']
        })
        
        print(f"{team['EQUIPO']:<15} ERA: {team_era:.3f}  FIP: {team_fip:.3f}  Diff: {team_fip - team_era:+.3f}")
    
    # Calculate FIP for individual pitchers
    print(f"\n=== INDIVIDUAL PITCHER FIP CALCULATIONS ===")
    individual_results = []
    
    for _, pitcher in individual_data.iterrows():
        pitcher_fip = calculate_fip_without_hbp(
            pitcher['HR'], 
            pitcher['BB'], 
            pitcher['K'], 
            pitcher['IP'], 
            fip_constant
        )
        
        # Calculate pitcher ERA if CL column exists
        pitcher_era = pitcher['EFE '] if 'EFE ' in individual_data.columns else np.nan
        
        individual_results.append({
            'Pitcher': pitcher['JUGADOR'],
            'Team': pitcher['TEAM'],
            'IP': pitcher['IP'],
            'ERA': pitcher_era,
            'FIP': pitcher_fip,
            'FIP-ERA': pitcher_fip - pitcher_era if not pd.isna(pitcher_era) else np.nan,
            'HR': pitcher['HR'],
            'BB': pitcher['BB'],
            'K': pitcher['K']
        })
    
    # Sort pitchers by FIP (minimum 10 IP for qualified pitchers)
    qualified_pitchers = [p for p in individual_results if p['IP'] >= 10.0]
    qualified_pitchers.sort(key=lambda x: x['FIP'] if not pd.isna(x['FIP']) else 999)
    
    print("Top 15 Qualified Pitchers by FIP (min 10 IP):")
    print("-" * 80)
    print(f"{'Pitcher':<20} {'Team':<8} {'IP':<6} {'ERA':<6} {'FIP':<6} {'Diff':<6} {'K':<3} {'BB':<3} {'HR'}")
    print("-" * 80)
    
    for i, pitcher in enumerate(qualified_pitchers[:15]):
        era_str = f"{pitcher['ERA']:.2f}" if not pd.isna(pitcher['ERA']) else "N/A"
        fip_str = f"{pitcher['FIP']:.2f}" if not pd.isna(pitcher['FIP']) else "N/A"
        diff_str = f"{pitcher['FIP-ERA']:+.2f}" if not pd.isna(pitcher['FIP-ERA']) else "N/A"
        
        print(f"{pitcher['Pitcher']:<20} {pitcher['Team']:<8} {pitcher['IP']:<6.1f} "
              f"{era_str:<6} {fip_str:<6} {diff_str:<6} {pitcher['K']:<3} {pitcher['BB']:<3} {pitcher['HR']}")
    
    # Create summary DataFrames and save to CSV
    team_df = pd.DataFrame(team_results)
    individual_df = pd.DataFrame(individual_results)
    
    # Save results
    team_df.to_csv('2024_lvbp_team_fip.csv', index=False)
    individual_df.to_csv('2024_lvbp_individual_fip.csv', index=False)
    
    print(f"\n=== SUMMARY ===")
    print(f"Results saved to:")
    print(f"- 2024_lvbp_team_fip.csv")
    print(f"- 2024_lvbp_individual_fip.csv")
    
    # Basic statistics
    avg_team_fip = team_df['FIP'].mean()
    print(f"\nAverage Team FIP: {avg_team_fip:.3f}")
    print(f"FIP Standard Deviation (Teams): {team_df['FIP'].std():.3f}")
    
    qualified_fips = [p['FIP'] for p in qualified_pitchers if not pd.isna(p['FIP'])]
    if qualified_fips:
        print(f"Average Qualified Pitcher FIP: {np.mean(qualified_fips):.3f}")
        print(f"FIP Standard Deviation (Qualified Pitchers): {np.std(qualified_fips):.3f}")

if __name__ == "__main__":
    main()