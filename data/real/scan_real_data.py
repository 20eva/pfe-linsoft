import sys
import os
import pandas as pd

sys.path.insert(0, os.path.abspath('.'))

from extractor.ansible_extractor import extract_features as ansible_features
from extractor.terraform_extractor import extract_features as terraform_features
from extractor.k8s_extractor import extract_features as k8s_features

REAL_DATA_DIR = 'real_data'
rows   = []
errors = []

SKIP_DIRS = {'.git', '__pycache__', 'screenshots', 'node_modules'}

def is_k8s(content):
    return 'apiVersion' in content and 'kind' in content

def scan_yaml(fpath, default_label=None):
    try:
        with open(fpath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()

        if is_k8s(content):
            feats = k8s_features(fpath)
            layer = 'k8s'
            if default_label is not None:
                label = default_label
            else:
                label = 1 if (
                    feats['runs_as_root'] or feats['privileged'] or
                    feats['dangerous_cap_count'] > 0 or
                    feats['no_resource_limits'] or feats['latest_tag_count'] > 0
                ) else 0
        else:
            feats = ansible_features(fpath)
            layer = 'ansible'
            if default_label is not None:
                label = default_label
            else:
                label = 1 if (
                    feats['secret_count'] > 0 or
                    feats['dangerous_module_count'] > 1 or
                    feats['no_log_false'] > 0 or
                    feats['is_broken'] == 1
                ) else 0

        feats['layer']    = layer
        feats['label']    = label
        feats['source']   = 'real'
        feats['filename'] = os.path.basename(fpath)
        return feats

    except Exception as e:
        errors.append(f"YAML error {fpath}: {e}")
        return None

def scan_tf(fpath, default_label=None):
    try:
        feats = terraform_features(fpath)
        if default_label is not None:
            label = default_label
        else:
            label = 1 if (
                feats['secret_count'] > 0 or
                feats['port_issue_count'] > 0 or
                feats['privilege_count'] > 0 or
                feats['dangerous_deletion_count'] > 0 or
                feats['has_lifecycle_protect'] == 0
            ) else 0
        feats['layer']    = 'terraform'
        feats['label']    = label
        feats['source']   = 'real'
        feats['filename'] = os.path.basename(fpath)
        return feats
    except Exception as e:
        errors.append(f"TF error {fpath}: {e}")
        return None

# ── 1. TerraGoat — all BAD ─────────────────────
print("Scanning TerraGoat (terraform - all bad)...")
count = 0
for root, dirs, files in os.walk(os.path.join(REAL_DATA_DIR, 'terragoat')):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if f.endswith('.tf'):
            r = scan_tf(os.path.join(root, f), default_label=1)
            if r: rows.append(r); count += 1
print(f"  → {count} files")

# ── 2. aws-eks-base — REAL terraform (auto-label)
print("Scanning aws-eks-base (terraform - real)...")
count = 0
for root, dirs, files in os.walk(os.path.join(REAL_DATA_DIR, 'aws-eks-base')):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if f.endswith('.tf'):
            r = scan_tf(os.path.join(root, f))
            if r: rows.append(r); count += 1
        elif f.endswith(('.yml', '.yaml')):
            r = scan_yaml(os.path.join(root, f))
            if r: rows.append(r); count += 1
print(f"  → {count} files")

# ── 3. cfngoat — BAD ──────────────────────────
print("Scanning cfngoat (bad)...")
count = 0
for root, dirs, files in os.walk(os.path.join(REAL_DATA_DIR, 'cfngoat')):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if f.endswith(('.yml', '.yaml')):
            r = scan_yaml(os.path.join(root, f), default_label=1)
            if r: rows.append(r); count += 1
print(f"  → {count} files")

# ── 4. k8s-security-lab — BAD ─────────────────
print("Scanning k8s-security-lab (k8s - bad)...")
count = 0
for root, dirs, files in os.walk(os.path.join(REAL_DATA_DIR, 'k8s-security-lab')):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if f.endswith(('.yml', '.yaml')) and 'artifacts' in root:
            r = scan_yaml(os.path.join(root, f), default_label=1)
            if r: rows.append(r); count += 1
print(f"  → {count} files")

# ── 5. kubernetes/examples — REAL (auto-label) ─
print("Scanning kubernetes/examples (k8s - real)...")
count = 0
for root, dirs, files in os.walk(os.path.join(REAL_DATA_DIR, 'examples')):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if f.endswith(('.yml', '.yaml')):
            r = scan_yaml(os.path.join(root, f))
            if r: rows.append(r); count += 1
print(f"  → {count} files")

# ── 6. ansible-examples — REAL (auto-label) ────
print("Scanning ansible-examples (ansible - real)...")
count = 0
for root, dirs, files in os.walk(os.path.join(REAL_DATA_DIR, 'ansible-examples')):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if f.endswith(('.yml', '.yaml')):
            r = scan_yaml(os.path.join(root, f))
            if r: rows.append(r); count += 1
print(f"  → {count} files")

# ── 7. workshop-examples — REAL (auto-label) ───
print("Scanning workshop-examples (ansible - real)...")
count = 0
for root, dirs, files in os.walk(os.path.join(REAL_DATA_DIR, 'workshop-examples')):
    dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
    for f in files:
        if f.endswith(('.yml', '.yaml')):
            r = scan_yaml(os.path.join(root, f))
            if r: rows.append(r); count += 1
print(f"  → {count} files")

# ── Save ───────────────────────────────────────
df = pd.DataFrame(rows)
os.makedirs('data/real', exist_ok=True)
output_path = 'data/real/real_data.csv'
df.to_csv(output_path, index=False)

print(f"\n{'─'*40}")
print(f"Total files scanned : {len(df)}")
print(f"\nLabel distribution:")
print(df['label'].value_counts())
print(f"\nLayer distribution:")
print(df['layer'].value_counts())
if errors:
    print(f"\nErrors: {len(errors)}")
    for e in errors[:5]:
        print(f"  {e}")
print(f"\nSaved to: {output_path}")