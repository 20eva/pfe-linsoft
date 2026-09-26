#!/usr/bin/env python3
"""
merge_scan_results.py

Combines every per-repository GLITCH CSV in scan-results/ into one
master CSV, adding a 'repository' column so we know which project
each finding came from.

Usage:
    python merge_scan_results.py --scan-dir ./scan-results --out merged_glitch_findings.csv
"""

import argparse
import csv
from pathlib import Path

COLUMNS = ["repository", "smell_description", "file", "line", "smell_code", "snippet"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scan-dir", default="./scan-results")
    parser.add_argument("--out", default="merged_glitch_findings.csv")
    parser.add_argument("--max-per-repo", type=int, default=100,
                         help="Cap findings taken from any single repository, "
                              "so one large/messy project can't dominate the dataset")
    args = parser.parse_args()

    scan_dir = Path(args.scan_dir)
    csv_files = sorted(scan_dir.glob("*.csv"))
    print(f"Found {len(csv_files)} result files to merge.")

    total_rows = 0
    empty_files = 0
    capped_repos = []

    with open(args.out, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(COLUMNS)

        for path in csv_files:
            repo_name = path.stem.replace("__", "/")
            if path.stat().st_size == 0:
                empty_files += 1
                continue
            with open(path, "r", encoding="utf-8", errors="replace") as in_f:
                reader = csv.reader(in_f)
                rows = [row for row in reader if len(row) >= 5]

            if len(rows) > args.max_per_repo:
                capped_repos.append((repo_name, len(rows)))
                rows = rows[: args.max_per_repo]

            for row in rows:
                writer.writerow([repo_name] + row[:5])
                total_rows += 1

    print(f"Merged {total_rows} findings from {len(csv_files) - empty_files} non-empty files "
          f"({empty_files} were empty/skipped).")
    if capped_repos:
        print(f"\nCapped {len(capped_repos)} repositories that exceeded {args.max_per_repo} findings:")
        for name, original_count in capped_repos:
            print(f"  {name}: {original_count} -> {args.max_per_repo}")
    print(f"\nSaved to {args.out}")


if __name__ == "__main__":
    main()