#!/usr/bin/env python3
"""
batch_clone_and_scan.py

Reads Dalla Palma's collected-repositories.csv, picks a batch of N
repositories, clones each one, and runs GLITCH on it, saving one
result CSV per repository.

Usage:
    python batch_clone_and_scan.py collected-repositories.csv --n 20 --out-dir ./scan-results --clone-dir ./cloned-repos

Notes:
  - Skips a repo if it's already cloned (safe to re-run / resume).
  - Skips a repo if its GLITCH scan output already exists (safe to
    re-run / resume after an interruption).
  - Uses a shallow clone (--depth 1) to save time/disk space, since
    we only need the current state of the files, not full history.
  - Adjust GLITCH_CMD below if your `glitch` executable needs a
    different invocation on your system.
"""

import argparse
import csv
import subprocess
import sys
from pathlib import Path

GLITCH_CMD = "glitch"  # change if you need e.g. "python -m glitch"


def run(cmd, cwd=None, timeout=None):
    print(f"  $ {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        return result.returncode, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("repo_csv", help="Path to collected-repositories.csv")
    parser.add_argument("--n", type=int, default=20, help="How many repos to process")
    parser.add_argument("--out-dir", default="./scan-results")
    parser.add_argument("--clone-dir", default="./cloned-repos")
    parser.add_argument("--min-iac-ratio", type=float, default=0.3,
                         help="Skip repos with less IaC content than this (0-1)")
    args = parser.parse_args()

    out_dir = Path(args.out_dir)
    clone_dir = Path(args.clone_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    clone_dir.mkdir(parents=True, exist_ok=True)

    with open(args.repo_csv, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    # Prefer repos with a decent amount of actual IaC content
    rows = [r for r in rows if float(r.get("iac_ratio", 0) or 0) >= args.min_iac_ratio]
    batch = rows[: args.n]

    print(f"Selected {len(batch)} repositories (iac_ratio >= {args.min_iac_ratio}).\n")

    succeeded, failed, skipped = [], [], []

    for i, row in enumerate(batch, start=1):
        full_name = row["full_name"]
        safe_name = full_name.replace("/", "__")
        repo_path = clone_dir / safe_name
        result_csv = out_dir / f"{safe_name}.csv"

        print(f"[{i}/{len(batch)}] {full_name}")

        if result_csv.exists():
            print("  already scanned, skipping.")
            skipped.append(full_name)
            continue

        if not repo_path.exists():
            url = f"https://github.com/{full_name}.git"
            code, out, err = run(
                ["git", "clone", "--depth", "1", url, str(repo_path)],
                timeout=120,
            )
            if code != 0:
                print(f"  CLONE FAILED: {err.strip()[:200]}")
                failed.append(full_name)
                continue
        else:
            print("  already cloned.")

        code, out, err = run(
            [GLITCH_CMD, "--tech", "ansible", "--csv", "--linter", "--module",
            str(repo_path), str(result_csv)],
            timeout=180,
        )
        # GLITCH prints warnings/misclassification notices to stderr even
        # on success, so treat "result file was created" as the real check.
        if result_csv.exists() and result_csv.stat().st_size > 0:
            print(f"  scanned OK -> {result_csv.name}")
            succeeded.append(full_name)
        else:
            print(f"  SCAN FAILED (return code {code}). Full stderr below:")
            print("  ----")
            print(err.strip() or "(no stderr output)")
            print("  ----")
            if out.strip():
                print("  stdout was:")
                print(out.strip())
            failed.append(full_name)

    print("\n---- Summary ----")
    print(f"Succeeded: {len(succeeded)}")
    print(f"Failed:    {len(failed)}")
    print(f"Skipped (already done): {len(skipped)}")
    if failed:
        print("\nFailed repos:")
        for f in failed:
            print(f"  - {f}")


if __name__ == "__main__":
    main()
