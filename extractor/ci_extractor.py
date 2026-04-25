import re

# ─────────────────────────────────────────────
# What this file does:
# Takes CI pipeline data (as a dictionary)
# and returns features the ML model can read.
# In real use, GitLab passes this data via
# the API call. Here we accept a plain dict.
# ─────────────────────────────────────────────

def extract_features(ci_data):
    """
    ci_data is a dictionary with raw CI pipeline info.
    Returns a dictionary of numeric features.
    """

    # ── Feature 1: vulnerability count ────────
    # From Trivy scan results
    vuln_count = int(ci_data.get('vuln_count', 0))

    # ── Feature 2: SonarQube quality score ────
    # 0-100, lower is worse
    sonar_score = float(ci_data.get('sonar_score', 100))

    # ── Feature 3: lines changed in this commit
    lines_changed = int(ci_data.get('lines_changed', 0))

    # ── Feature 4: did the previous deploy fail?
    # 1 = yes (bad signal), 0 = no
    prev_failed = 1 if ci_data.get('prev_failed', False) else 0

    # ── Feature 5: commit frequency ───────────
    # commits per day in this branch recently
    # very high = rushed work, very low = stale
    commit_freq = float(ci_data.get('commit_freq', 1.0))

    # ── Feature 6: number of new files added ──
    new_files = int(ci_data.get('new_files', 0))

    # ── Feature 7: number of files deleted ────
    deleted_files = int(ci_data.get('deleted_files', 0))

    # ── Feature 8: critical vulns specifically ─
    # Trivy separates CRITICAL from HIGH/MEDIUM
    critical_vulns = int(ci_data.get('critical_vulns', 0))

    # ── Feature 9: build time in seconds ──────
    # unusually fast builds can mean steps were skipped
    build_time_seconds = int(ci_data.get('build_time_seconds', 60))

    # ── Feature 10: is this a Friday deploy? ──
    # statistically higher failure rate
    is_friday = 1 if ci_data.get('is_friday', False) else 0

    features = {
        'vuln_count':          vuln_count,
        'sonar_score':         sonar_score,
        'lines_changed':       lines_changed,
        'prev_failed':         prev_failed,
        'commit_freq':         commit_freq,
        'new_files':           new_files,
        'deleted_files':       deleted_files,
        'critical_vulns':      critical_vulns,
        'build_time_seconds':  build_time_seconds,
        'is_friday':           is_friday,
    }

    return features


if __name__ == '__main__':

    # Simulate a risky CI run
    test_ci_data = {
        'vuln_count':         12,
        'sonar_score':        61,
        'lines_changed':      847,
        'prev_failed':        True,
        'commit_freq':        8.5,
        'new_files':          6,
        'deleted_files':      2,
        'critical_vulns':     3,
        'build_time_seconds': 12,
        'is_friday':          True,
    }

    features = extract_features(test_ci_data)

    print("\nExtracted CI features:")
    for key, value in features.items():
        print(f"  {key}: {value}")