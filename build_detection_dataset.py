#!/usr/bin/env python3
"""
build_detection_dataset.py

Turns your GLITCH findings (which only contain PROBLEM lines) into a
full detection dataset by adding CLEAN lines from the same repos -
lines GLITCH did NOT flag. This lets a model learn the actual
difference between "fine" and "has a problem", not just categorize
problems that were already found.

Steps:
  1. Load your findings CSV -> build a set of (repo, file, line) that
     are already known-flagged.
  2. Walk every .yml/.yaml file inside cloned-repos/ -> every line NOT
     in the flagged set is a candidate "clean" example.
  3. Randomly sample clean lines (capped, so the dataset stays balanced
     rather than 99% clean / 1% flagged).
  4. Save one combined CSV: repository, file, line, snippet, is_issue,
     smell_code ("no_issue" for clean rows), category.

Usage:
    python build_detection_dataset.py --findings glitch_findings_full.csv --clone-dir cloned-repos --out detection_dataset.csv --clean-ratio 2
"""

import argparse
import csv
import random
from pathlib import Path

import pandas as pd


def load_flagged_lines(findings_path):
    """Returns dict: repo_folder_name -> set of (relative_file_path, line_number)
    that are already known to be flagged by GLITCH."""
    df = pd.read_csv(findings_path)
    flagged = {}
    for _, row in df.iterrows():
        repo = row["repository"]
        # repo names use "owner/name" - the cloned folder uses "owner__name"
        folder_name = repo.replace("/", "__")
        file_path = str(row["file"]).replace("\\", "/")
        # keep only the part of the path after the repo folder name
        if folder_name in file_path:
            rel_path = file_path.split(folder_name, 1)[1].lstrip("/")
        else:
            rel_path = file_path
        line_no = int(row["line"]) if not pd.isna(row["line"]) else -1
        flagged.setdefault(folder_name, set()).add((rel_path, line_no))
    return flagged


def is_blank_or_trivial(line):
    stripped = line.strip()
    return len(stripped) == 0 or stripped in ("---", "...")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--findings", default="glitch_findings_full.csv")
    parser.add_argument("--clone-dir", default="cloned-repos")
    parser.add_argument("--out", default="detection_dataset.csv")
    parser.add_argument("--clean-ratio", type=float, default=2.0,
                         help="How many clean lines to sample per flagged "
                              "line, on average (2.0 = twice as many clean "
                              "as flagged, a common realistic imbalance)")
    parser.add_argument("--max-per-repo", type=int, default=150,
                         help="Cap clean lines taken from any single repo, "
                              "so a large repo can't dominate the sample")
    parser.add_argument("--scan-results-dir", default="scan-results",
                         help="Only sample clean lines from repos that have "
                              "a real, non-empty scan result here - a repo "
                              "with no scan result was never actually "
                              "checked by GLITCH, so its lines are NOT "
                              "reliably 'clean', just unexamined.")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    random.seed(args.seed)

    # Only trust repos that were ACTUALLY scanned successfully (a non-empty
    # CSV exists for them). A repo with a failed/partial clone or a failed
    # scan has NO real findings on record - treating its lines as "clean"
    # by default would be wrong, since they were never actually checked.
    scan_dir = Path(args.scan_results_dir)
    successfully_scanned = {
        p.stem for p in scan_dir.glob("*.csv") if p.stat().st_size > 0
    }
    print(f"{len(successfully_scanned)} repos were successfully scanned and "
          f"are eligible as a source of clean lines.")

    print("Loading flagged findings...")
    flagged = load_flagged_lines(args.findings)
    total_flagged = sum(len(v) for v in flagged.values())
    print(f"Loaded {total_flagged} flagged (file, line) locations across {len(flagged)} repos.")

    clone_root = Path(args.clone_dir)
    target_clean_count = int(total_flagged * args.clean_ratio)
    print(f"Target clean examples to sample: ~{target_clean_count}")

    clean_candidates = []  # (repo_folder, rel_path, line_no, snippet)

    for repo_dir in clone_root.iterdir():
        if not repo_dir.is_dir():
            continue
        folder_name = repo_dir.name

        if folder_name not in successfully_scanned:
            continue  # skip repos that were never actually scanned

        repo_flagged = flagged.get(folder_name, set())
        repo_clean_lines = []

        for yml_path in list(repo_dir.rglob("*.yml")) + list(repo_dir.rglob("*.yaml")):
            rel_path = str(yml_path.relative_to(repo_dir)).replace("\\", "/")
            try:
                with open(yml_path, "r", encoding="utf-8", errors="replace") as f:
                    lines = f.readlines()
            except Exception:
                continue

            for i, line in enumerate(lines, start=1):
                if is_blank_or_trivial(line):
                    continue
                if (rel_path, i) in repo_flagged:
                    continue
                repo_clean_lines.append((folder_name, rel_path, i, line.strip()))

        # Cap how many clean lines any single repo can contribute
        if len(repo_clean_lines) > args.max_per_repo:
            repo_clean_lines = random.sample(repo_clean_lines, args.max_per_repo)

        clean_candidates.extend(repo_clean_lines)

    print(f"Found {len(clean_candidates)} clean candidate lines across all repos.")

    sample_size = min(target_clean_count, len(clean_candidates))
    clean_sample = random.sample(clean_candidates, sample_size)
    print(f"Sampled {len(clean_sample)} clean lines.")

    # Build the combined output
    findings_df = pd.read_csv(args.findings)

    with open(args.out, "w", newline="", encoding="utf-8") as out_f:
        writer = csv.writer(out_f)
        writer.writerow(["repository", "file", "line", "snippet", "is_issue", "smell_code"])

        for _, row in findings_df.iterrows():
            writer.writerow([
                row["repository"], row["file"], row["line"],
                row["snippet"], 1, row["smell_code"],
            ])

        for folder_name, rel_path, line_no, snippet in clean_sample:
            repo_name = folder_name.replace("__", "/")
            writer.writerow([repo_name, rel_path, line_no, snippet, 0, "no_issue"])

    print(f"\nSaved combined detection dataset to {args.out}")
    print(f"  Flagged (is_issue=1): {len(findings_df)}")
    print(f"  Clean   (is_issue=0): {len(clean_sample)}")


if __name__ == "__main__":
    main()