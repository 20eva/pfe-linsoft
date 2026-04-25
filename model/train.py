import pandas as pd
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
    report = classification_report(y_test, y_pred, target_names=['safe', 'risky'])
    print(report)

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