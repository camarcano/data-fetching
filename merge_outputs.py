import pandas as pd
import argparse
import os
import glob
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Folder where CSVs are stored
OUTPUT_FOLDER = "output"

def merge_csv_files(file_pattern, output_filename):
    """
    Merges all CSV files matching a pattern into a single CSV.
    """
    files = glob.glob(os.path.join(OUTPUT_FOLDER, file_pattern))
    if not files:
        logging.warning(f"No files matched pattern: {file_pattern}")
        return

    logging.info(f"Found {len(files)} files matching pattern: {file_pattern}")
    all_data = []
    for file in files:
        logging.info(f"Reading: {file}")
        df = pd.read_csv(file)
        all_data.append(df)

    merged_df = pd.concat(all_data, ignore_index=True)
    merged_path = os.path.join(OUTPUT_FOLDER, output_filename)
    merged_df.to_csv(merged_path, index=False)
    logging.info(f"Saved merged file to: {merged_path} with {len(merged_df)} total rows")


def main(args):
    if not os.path.exists(OUTPUT_FOLDER):
        logging.error(f"Output folder '{OUTPUT_FOLDER}' does not exist.")
        return

    # Build file patterns based on actual naming convention
    season_str = f"*{args.season}*" if args.season else "*"

    if args.all or args.merge_pbp:
        # Look for pitch by pitch files: {date}_gamePk_{pk}_pitch_by_pitch.csv
        pattern = f"{season_str}*_gamePk_*_pitch_by_pitch.csv"
        output_name = f"merged_pitch_by_pitch_{args.season or 'all'}.csv"
        logging.info(f"Merging pitch-by-pitch files with pattern: {pattern}")
        merge_csv_files(pattern, output_name)

    if args.all or args.merge_hitters:
        # Look for hitters files: {date}_gamePk_{pk}_hitters.csv
        pattern = f"{season_str}*_gamePk_*_hitters.csv"
        output_name = f"merged_hitters_boxscore_{args.season or 'all'}.csv"
        logging.info(f"Merging hitters files with pattern: {pattern}")
        merge_csv_files(pattern, output_name)

    if args.all or args.merge_pitchers:
        # Look for pitchers files: {date}_gamePk_{pk}_pitchers.csv
        pattern = f"{season_str}*_gamePk_*_pitchers.csv"
        output_name = f"merged_pitchers_boxscore_{args.season or 'all'}.csv"
        logging.info(f"Merging pitchers files with pattern: {pattern}")
        merge_csv_files(pattern, output_name)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Merge MLB data CSV outputs.")
    parser.add_argument('--all', action='store_true', help="Merge all pitch-by-pitch, hitters, and pitchers CSVs.")
    parser.add_argument('--merge-pbp', action='store_true', help="Merge pitch-by-pitch CSVs.")
    parser.add_argument('--merge-hitters', action='store_true', help="Merge hitters boxscore CSVs.")
    parser.add_argument('--merge-pitchers', action='store_true', help="Merge pitchers boxscore CSVs.")
    parser.add_argument('--season', type=str, help="Optional season filter (e.g., '2024') to match files.")

    args = parser.parse_args()
    main(args)