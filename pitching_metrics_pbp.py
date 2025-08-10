import pandas as pd
import numpy as np
import argparse
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")

def convert_ip_to_outs(ip):
    try:
        whole = int(float(ip))
        fraction = float(ip) - whole
        if np.isnan(fraction):
            return 0
        elif fraction == 0.1:
            return whole * 3 + 1
        elif fraction == 0.2:
            return whole * 3 + 2
        else:
            return whole * 3
    except:
        return 0

def calculate_metrics(pitcher_df):
    G = len(pitcher_df)
    GS = pitcher_df["gamesStarted"].sum()
    TBF = pitcher_df["battersFaced"].sum()
    W = pitcher_df["wins"].sum()
    L = pitcher_df["losses"].sum()
    SV = pitcher_df["saves"].sum()
    HLD = pitcher_df["holds"].sum()
    BS = pitcher_df["blownSaves"].sum()
    HR = pitcher_df["homeRuns"].sum()
    BB = pitcher_df["baseOnBalls"].sum()
    SO = pitcher_df["strikeOuts"].sum()
    H = pitcher_df["hits"].sum()
    ER = pitcher_df["earnedRuns"].sum()
    HBP = pitcher_df["hitByPitch"].sum()
    WP = pitcher_df["wildPitches"].sum()
    BK = pitcher_df["balks"].sum()
    IP = pitcher_df["inningsPitched"].sum()

    # Use actual column names from the file
    Pitches = pitcher_df.get("numberOfPitches", pd.Series([0]*len(pitcher_df))).sum()
    Balls = pitcher_df.get("balls", pd.Series([0]*len(pitcher_df))).sum()
    Strikes = pitcher_df.get("strikes", pd.Series([0]*len(pitcher_df))).sum()

    outs = pitcher_df["inningsPitched"].apply(convert_ip_to_outs).sum()
    ip_full = round(outs / 3, 1)

    ERA = round((ER * 9) / ip_full, 2) if ip_full else 0
    WHIP = round((BB + H) / ip_full, 3) if ip_full else 0

    K9 = round((SO * 9) / ip_full, 2) if ip_full else 0
    BB9 = round((BB * 9) / ip_full, 2) if ip_full else 0
    H9 = round((H * 9) / ip_full, 2) if ip_full else 0
    HR9 = round((HR * 9) / ip_full, 2) if ip_full else 0
    KBB = round(SO / BB, 2) if BB else np.nan

    K_pct = round(SO / TBF, 3) if TBF else 0
    BB_pct = round(BB / TBF, 3) if TBF else 0
    diff_pct = round(K_pct - BB_pct, 3)

    BIP = TBF - (SO + BB + HBP + HR)
    HR_per_BIP = round(HR / BIP, 3) if BIP else 0
    BABIP = round((H - HR) / BIP, 3) if BIP else 0

    return {
        "ERA": ERA, "WHIP": WHIP, "G": G, "GS": GS, "TBF": TBF,
        "Wins": W, "Losses": L, "Saves": SV, "Holds": HLD, "BS": BS,
        "InningsPitched": ip_full, "HR": HR, "Strikeouts": SO, "Walks": BB,
        "HBP": HBP, "WP": WP, "BK": BK, "Pitches": Pitches,
        "Balls": Balls, "Strikes": Strikes,
        "K/9": K9, "BB/9": BB9, "H/9": H9, "HR/9": HR9, "K/BB": KBB,
        "K%": K_pct, "BB%": BB_pct, "K%-BB%": diff_pct,
        "BIP": BIP, "HR% (BIP)": HR_per_BIP, "BABIP": BABIP
    }

def main():
    parser = argparse.ArgumentParser(description="Calculate pitching metrics from boxscore data.")
    parser.add_argument("--file", required=True, help="CSV file with pitcher boxscore data")
    parser.add_argument("-t", "--team_id", type=int, help="Filter by team ID")
    parser.add_argument("-s", "--start_date", help="Start date (YYYY-MM-DD)")
    parser.add_argument("-e", "--end_date", help="End date (YYYY-MM-DD)")
    parser.add_argument("-a", "--aggregate", action="store_true", help="Aggregate all pitchers on team")

    args = parser.parse_args()
    df = pd.read_csv(args.file, low_memory=False)

    if "inningsPitched" not in df.columns:
        raise ValueError("Column 'inningsPitched' is required in input.")

    if args.start_date:
        df = df[df["date"] >= args.start_date]
    if args.end_date:
        df = df[df["date"] <= args.end_date]

    if args.team_id:
        df = df[df["teamId"] == args.team_id]
        logging.info(f"Calculating {'aggregated' if args.aggregate else 'individual'} stats for Team ID: {args.team_id}")

        if args.aggregate:
            result = calculate_metrics(df)
            print(result)
        else:
            pitcher_stats = []

            for player_id in df["playerId"].unique():
                pitcher_df = df[df["playerId"] == player_id]
                if pitcher_df.empty:
                    continue

                metrics = calculate_metrics(pitcher_df)
                row = {
                    "playerId": player_id,
                    "name": pitcher_df.iloc[0].get("playerName", "")
                }
                row.update(metrics)
                pitcher_stats.append(row)

            out_df = pd.DataFrame(pitcher_stats)
            out_file = f"pitching_metrics_team_{args.team_id}.csv"
            out_df.to_csv(out_file, index=False)
            print(f"Saved individual pitcher stats to {out_file}")

if __name__ == "__main__":
    main()
