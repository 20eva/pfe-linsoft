import sys
import os
import json
import requests

sys.path.insert(0, os.path.abspath('.'))

from extractor.ansible_extractor import extract_features as ansible_features
from extractor.terraform_extractor import extract_features as terraform_features
from extractor.k8s_extractor import extract_features as k8s_features

# ─────────────────────────────────────────────
# What this file does:
# This is what GitLab CI runs on every commit.
# It scans all changed files, calls the API,
# and exits with code 1 if anything is HIGH
# (which tells GitLab to block the pipeline).
# ─────────────────────────────────────────────

API_URL = os.environ.get('AIOPS_API_URL', 'http://127.0.0.1:8000')

BLOCK_ON_HIGH  = True   # exit 1 if HIGH risk found
ALERT_ON_MEDIUM = True  # print warning but don't block

results   = []
has_block = False
has_alert = False


def predict(layer, features):
    try:
        response = requests.post(
            f"{API_URL}/predict",
            json={"layer": layer, "features": features},
            timeout=10
        )
        return response.json()
    except Exception as e:
        print(f"  [ERROR] Could not reach API at {API_URL}: {e}")
        return None


def scan_file(filepath):
    """Detect layer from file extension and scan."""
    ext  = os.path.splitext(filepath)[1].lower()
    name = os.path.basename(filepath).lower()

    try:
        if filepath.endswith('.tf'):
            feats  = terraform_features(filepath)
            result = predict('terraform', feats)
            return result

        elif filepath.endswith(('.yml', '.yaml')):
            # Detect if it's K8s, Ansible, or CI
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()

            # K8s manifests have apiVersion and kind
            if 'apiVersion' in content and 'kind' in content:
                feats  = k8s_features(filepath)
                result = predict('k8s', feats)
                return result

            # GitLab CI files
            elif name in ('.gitlab-ci.yml', 'gitlab-ci.yml'):
                print(f"  [SKIP] CI file itself — skipping {filepath}")
                return None

            # Everything else is treated as Ansible
            else:
                feats  = ansible_features(filepath)
                result = predict('ansible', feats)
                return result

    except Exception as e:
        print(f"  [ERROR] Failed to scan {filepath}: {e}")
        return None

    return None


def print_result(filepath, result):
    risk   = result['risk']
    action = result['action']
    score  = result['final_score']
    icon   = {'HIGH': '🔴', 'MEDIUM': '🟡', 'LOW': '🟢'}.get(risk, '⚪')

    print(f"\n  {icon} {os.path.basename(filepath)}")
    print(f"     Risk   : {risk} ({score})")
    print(f"     Action : {action.upper()}")
    if result['reasons'] and result['reasons'][0] != 'No specific issues detected':
        print(f"     Issues :")
        for r in result['reasons']:
            print(f"       → {r}")


# ── Main scan logic ────────────────────────────
print("=" * 55)
print("  AIOps Security Scanner")
print(f"  API: {API_URL}")
print("=" * 55)

# Get files to scan — from CLI args or scan everything
if len(sys.argv) > 1:
    # GitLab CI passes changed files as arguments
    files_to_scan = sys.argv[1:]
else:
    # Local mode — scan all relevant files in project
    files_to_scan = []
    scan_dirs = ['.']
    skip_dirs = {'.git', 'real_data', '__pycache__', '.pytest_cache'}

    for scan_dir in scan_dirs:
        for root, dirs, files in os.walk(scan_dir):
            # Skip irrelevant directories
            dirs[:] = [d for d in dirs if d not in skip_dirs]
            for fname in files:
                if fname.endswith(('.tf', '.yml', '.yaml')):
                    files_to_scan.append(os.path.join(root, fname))

print(f"\nFiles to scan: {len(files_to_scan)}")

for filepath in files_to_scan:
    result = scan_file(filepath)

    if result is None:
        continue

    results.append({'file': filepath, 'result': result})
    print_result(filepath, result)

    if result['action'] == 'block':
        has_block = True
    elif result['action'] == 'alert':
        has_alert = True

# ── Final verdict ──────────────────────────────
print("\n" + "=" * 55)
print("  SCAN SUMMARY")
print("=" * 55)

total   = len(results)
blocked = sum(1 for r in results if r['result']['action'] == 'block')
alerted = sum(1 for r in results if r['result']['action'] == 'alert')
passed  = sum(1 for r in results if r['result']['action'] == 'pass')

print(f"  Total scanned : {total}")
print(f"  🔴 BLOCK      : {blocked}")
print(f"  🟡 ALERT      : {alerted}")
print(f"  🟢 PASS       : {passed}")

# Save results as JSON for GitLab CI artifact
os.makedirs('ci_scanner', exist_ok=True)
report_path = 'ci_scanner/scan_report.json'
with open(report_path, 'w') as f:
    json.dump(results, f, indent=2)
print(f"\n  Report saved : {report_path}")

if has_block and BLOCK_ON_HIGH:
    print("\n  ❌ PIPELINE BLOCKED — HIGH risk files detected.")
    print("     Fix the issues above before merging.")
    print("=" * 55)
    sys.exit(1)
elif has_alert:
    print("\n  ⚠️  PIPELINE PASSED WITH WARNINGS.")
    print("     Review MEDIUM risk files before merging.")
    print("=" * 55)
    sys.exit(0)
else:
    print("\n  ✅ ALL CLEAR — pipeline can proceed.")
    print("=" * 55)
    sys.exit(0)