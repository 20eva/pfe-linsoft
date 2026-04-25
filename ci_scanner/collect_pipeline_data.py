import csv
import os
import json
from datetime import datetime, timezone

# ─────────────────────────────────────────────
# What this file does:
# Every time GitLab CI runs, this script saves
# one row of real pipeline data to a CSV.
# Over time this builds your real CI dataset.
# ─────────────────────────────────────────────

REAL_CI_PATH = 'data/real/ci_pipeline_runs.csv'

FIELDNAMES = [
    'timestamp',
    'commit_sha',
    'branch',
    'vuln_count',
    'sonar_score',
    'lines_changed',
    'prev_failed',
    'commit_freq',
    'new_files',
    'deleted_files',
    'critical_vulns',
    'build_time_seconds',
    'is_friday',
    'pipeline_result',  # passed / failed
    'label',            # 1=risky, 0=safe (based on result)
]


def collect(data: dict):
    """
    Save one pipeline run to the CSV.
    Call this at the end of every CI run.
    """
    os.makedirs('data/real', exist_ok=True)

    file_exists = os.path.exists(REAL_CI_PATH)

    with open(REAL_CI_PATH, 'a', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=FIELDNAMES)

        if not file_exists:
            writer.writeheader()

        # Auto-label: failed pipeline = risky
        label = 1 if data.get('pipeline_result') == 'failed' else 0

        row = {
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'commit_sha':         data.get('commit_sha', 'unknown'),
            'branch':             data.get('branch', 'unknown'),
            'vuln_count':         data.get('vuln_count', 0),
            'sonar_score':        data.get('sonar_score', 100),
            'lines_changed':      data.get('lines_changed', 0),
            'prev_failed':        data.get('prev_failed', 0),
            'commit_freq':        data.get('commit_freq', 1.0),
            'new_files':          data.get('new_files', 0),
            'deleted_files':      data.get('deleted_files', 0),
            'critical_vulns':     data.get('critical_vulns', 0),
            'build_time_seconds': data.get('build_time_seconds', 60),
            'is_friday':          data.get('is_friday', 0),
            'pipeline_result':    data.get('pipeline_result', 'passed'),
            'label':              label,
        }

        writer.writerow(row)
        print(f"Pipeline run saved to {REAL_CI_PATH}")
        return row


def retrain_if_enough_data(min_rows=50):
    """
    Once we have enough real CI rows,
    trigger a retrain automatically.
    """
    if not os.path.exists(REAL_CI_PATH):
        return

    with open(REAL_CI_PATH, 'r') as f:
        row_count = sum(1 for _ in f) - 1  # subtract header

    print(f"Real CI rows collected: {row_count}")

    if row_count >= min_rows:
        print(f"Enough data — triggering retrain...")
        os.system(
            'C:\\Users\\Eva\\AppData\\Local\\Programs\\'
            'Python\\Python313\\python.exe '
            'data\\merge_and_retrain.py'
        )
    else:
        remaining = min_rows - row_count
        print(f"Need {remaining} more runs before retraining.")


if __name__ == '__main__':
    # Simulate a real GitLab CI pipeline run
    # In production, GitLab passes these as env variables
    import sys

    test_run = {
        'commit_sha':         os.environ.get('CI_COMMIT_SHA', 'abc123'),
        'branch':             os.environ.get('CI_COMMIT_BRANCH', 'main'),
        'vuln_count':         int(os.environ.get('VULN_COUNT', 2)),
        'sonar_score':        float(os.environ.get('SONAR_SCORE', 88.0)),
        'lines_changed':      int(os.environ.get('LINES_CHANGED', 45)),
        'prev_failed':        int(os.environ.get('PREV_FAILED', 0)),
        'commit_freq':        float(os.environ.get('COMMIT_FREQ', 2.0)),
        'new_files':          int(os.environ.get('NEW_FILES', 1)),
        'deleted_files':      int(os.environ.get('DELETED_FILES', 0)),
        'critical_vulns':     int(os.environ.get('CRITICAL_VULNS', 0)),
        'build_time_seconds': int(os.environ.get('BUILD_TIME', 120)),
        'is_friday':          int(os.environ.get('IS_FRIDAY', 0)),
        'pipeline_result':    os.environ.get('PIPELINE_RESULT', 'passed'),
    }

    row = collect(test_run)
    print(f"Saved row: {json.dumps(row, indent=2)}")
    retrain_if_enough_data()