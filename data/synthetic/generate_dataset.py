import pandas as pd
import random

random.seed(42)

# ─────────────────────────────────────────────
# What this file does:
# Generates a synthetic training dataset.
# Each row = one past CI/config event.
# Last column = label (1 = risky, 0 = safe)
# The model learns from these examples.
# ─────────────────────────────────────────────

def make_safe_ansible():
    return {
        'secret_count':           0,
        'privilege_count':        random.randint(0, 1),
        'dangerous_module_count': random.randint(0, 1),
        'is_broken':              0,
        'total_lines':            random.randint(10, 80),
        'no_log_false':           0,
        'task_count':             random.randint(1, 8),
        'layer':                  'ansible',
        'label':                  0,
    }

def make_risky_ansible():
    return {
        'secret_count':           random.randint(1, 5),
        'privilege_count':        random.randint(1, 3),
        'dangerous_module_count': random.randint(1, 4),
        'is_broken':              random.randint(0, 1),
        'total_lines':            random.randint(50, 300),
        'no_log_false':           1,
        'task_count':             random.randint(5, 20),
        'layer':                  'ansible',
        'label':                  1,
    }

def make_safe_ci():
    return {
        'vuln_count':         random.randint(0, 3),
        'sonar_score':        random.uniform(80, 100),
        'lines_changed':      random.randint(10, 200),
        'prev_failed':        0,
        'commit_freq':        random.uniform(1, 5),
        'new_files':          random.randint(0, 3),
        'deleted_files':      random.randint(0, 2),
        'critical_vulns':     0,
        'build_time_seconds': random.randint(60, 300),
        'is_friday':          0,
        'layer':              'ci',
        'label':              0,
    }

def make_risky_ci():
    return {
        'vuln_count':         random.randint(8, 20),
        'sonar_score':        random.uniform(30, 65),
        'lines_changed':      random.randint(400, 1500),
        'prev_failed':        1,
        'commit_freq':        random.uniform(6, 15),
        'new_files':          random.randint(5, 20),
        'deleted_files':      random.randint(3, 10),
        'critical_vulns':     random.randint(1, 8),
        'build_time_seconds': random.randint(5, 25),
        'is_friday':          1,
        'layer':              'ci',
        'label':              1,
    }

def make_safe_terraform():
    return {
        'secret_count':             0,
        'port_issue_count':         random.randint(0, 1),
        'privilege_count':          0,
        'dangerous_deletion_count': 0,
        'resource_count':           random.randint(1, 5),
        'hardcoded_values':         random.randint(0, 2),
        'has_lifecycle_protect':    1,
        'total_lines':              random.randint(20, 100),
        'layer':                    'terraform',
        'label':                    0,
    }

def make_risky_terraform():
    return {
        'secret_count':             random.randint(1, 4),
        'port_issue_count':         random.randint(3, 8),
        'privilege_count':          random.randint(1, 3),
        'dangerous_deletion_count': random.randint(1, 3),
        'resource_count':           random.randint(3, 15),
        'hardcoded_values':         random.randint(5, 20),
        'has_lifecycle_protect':    0,
        'total_lines':              random.randint(100, 500),
        'layer':                    'terraform',
        'label':                    1,
    }

def make_safe_k8s():
    return {
        'runs_as_root':        0,
        'privileged':          0,
        'dangerous_cap_count': 0,
        'host_network':        0,
        'host_path_count':     0,
        'no_resource_limits':  0,
        'latest_tag_count':    0,
        'secret_in_env':       0,
        'allow_priv_esc':      0,
        'doc_count':           random.randint(1, 3),
        'is_broken':           0,
        'layer':               'k8s',
        'label':               0,
    }

def make_risky_k8s():
    return {
        'runs_as_root':        random.randint(0, 1),
        'privileged':          random.randint(0, 1),
        'dangerous_cap_count': random.randint(1, 4),
        'host_network':        random.randint(0, 1),
        'host_path_count':     random.randint(1, 3),
        'no_resource_limits':  1,
        'latest_tag_count':    random.randint(1, 3),
        'secret_in_env':       random.randint(0, 2),
        'allow_priv_esc':      random.randint(0, 1),
        'doc_count':           random.randint(1, 5),
        'is_broken':           random.randint(0, 1),
        'layer':               'k8s',
        'label':               1,
    }

# ── Generate rows ──────────────────────────────
rows = []

# 150 safe + 150 risky per layer = 1200 total rows
for _ in range(150):
    rows.append(make_safe_ansible())
    rows.append(make_risky_ansible())
    rows.append(make_safe_ci())
    rows.append(make_risky_ci())
    rows.append(make_safe_terraform())
    rows.append(make_risky_terraform())
    rows.append(make_safe_k8s())
    rows.append(make_risky_k8s())

# Shuffle so safe and risky aren't grouped
random.shuffle(rows)

# Convert to a pandas DataFrame (a table)
df = pd.DataFrame(rows)

# Save to CSV
output_path = 'data/synthetic/training_data.csv'
df.to_csv(output_path, index=False)

print(f"Generated {len(df)} rows")
print(f"Saved to {output_path}")
print(f"\nLabel distribution:")
print(df['label'].value_counts())
print(f"\nLayers:")
print(df['layer'].value_counts())
print(f"\nFirst 3 rows:")
print(df.head(3).to_string()) import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report
from sklearn.preprocessing import LabelEncoder

# ─────────────────────────────────────────────
# What this file does:
# 1. Loads the synthetic dataset
# 2. Trains one RandomForest per layer
#    (for labeled data — CI and security layers)
# 3. Trains one IsolationForest per layer
#    (for anomaly detection — Ansible, K8s)
# 4. Saves all models as .pkl files
# ─────────────────────────────────────────────

DATA_PATH   = 'data/synthetic/training_data.csv'
MODELS_DIR  = 'model/models'

# Features each layer uses — NaN columns are ignored
LAYER_FEATURES = {
    'ci': [
        'vuln_count', 'sonar_score', 'lines_changed',
        'prev_failed', 'commit_freq', 'new_files',
        'deleted_files', 'critical_vulns',
        'build_time_seconds', 'is_friday',
    ],
    'ansible': [
        'secret_count', 'privilege_count',
        'dangerous_module_count', 'is_broken',
        'total_lines', 'no_log_false', 'task_count',
    ],
    'terraform': [
        'secret_count', 'port_issue_count',
        'privilege_count', 'dangerous_deletion_count',
        'resource_count', 'hardcoded_values',
        'has_lifecycle_protect', 'total_lines',
    ],
    'k8s': [
        'runs_as_root', 'privileged', 'dangerous_cap_count',
        'host_network', 'host_path_count', 'no_resource_limits',
        'latest_tag_count', 'secret_in_env',
        'allow_priv_esc', 'doc_count', 'is_broken',
    ],
}

# ── Load data ──────────────────────────────────
print("Loading dataset...")
df = pd.read_csv(DATA_PATH)
print(f"Loaded {len(df)} rows\n")

os.makedirs(MODELS_DIR, exist_ok=True)

# ── Train one model per layer ──────────────────
for layer, features in LAYER_FEATURES.items():

    print(f"{'─'*50}")
    print(f"Training layer: {layer.upper()}")

    # Filter rows for this layer only
    layer_df = df[df['layer'] == layer][features + ['label']].dropna()

    print(f"  Rows available: {len(layer_df)}")

    X = layer_df[features]
    y = layer_df['label']

    # Split: 80% train, 20% test
    # test data is held back to measure accuracy honestly
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── Random Forest (supervised) ─────────────
    # Used for predicting risk from labeled examples
    rf = RandomForestClassifier(
        n_estimators=100,   # 100 decision trees
        random_state=42,
        class_weight='balanced',  # handles uneven safe/risky split
    )
    rf.fit(X_train, y_train)

    # Measure accuracy on the held-back test set
    y_pred = rf.predict(X_test)
    print(f"\n  Random Forest results:")
    print(classification_report(y_test, y_pred,
          target_names=['safe', 'risky'], indent=4))

    # Show which features matter most
    importances = zip(features, rf.feature_importances_)
    sorted_imp = sorted(importances, key=lambda x: x[1], reverse=True)
    print(f"  Top 3 most important features:")
    for fname, score in sorted_imp[:3]:
        print(f"    {fname}: {score:.3f}")

    # Save the Random Forest model
    rf_path = os.path.join(MODELS_DIR, f'rf_{layer}.pkl')
    with open(rf_path, 'wb') as f:
        pickle.dump({
            'model':    rf,
            'features': features,
            'layer':    layer,
        }, f)
    print(f"\n  Saved: {rf_path}")

    # ── Isolation Forest (unsupervised) ────────
    # Used for anomaly detection — no labels needed
    # Learns what "normal" looks like, flags outliers
    iso = IsolationForest(
        n_estimators=100,
        contamination=0.2,  # expects ~20% of data to be anomalous
        random_state=42,
    )
    iso.fit(X_train)

    # Save the Isolation Forest model
    iso_path = os.path.join(MODELS_DIR, f'iso_{layer}.pkl')
    with open(iso_path, 'wb') as f:
        pickle.dump({
            'model':    iso,
            'features': features,
            'layer':    layer,
        }, f)
    print(f"  Saved: {iso_path}")

print(f"\n{'─'*50}")
print("All models trained and saved.")
print(f"Models directory: {MODELS_DIR}")
print("\nFiles saved:")
for fname in os.listdir(MODELS_DIR):
    print(f"  {fname}")