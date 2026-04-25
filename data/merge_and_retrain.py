import pandas as pd
import pickle
import os
from sklearn.ensemble import RandomForestClassifier, IsolationForest
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report

# ─────────────────────────────────────────────
# What this file does:
# 1. Loads synthetic + real data
# 2. Merges them together
# 3. Retrains all models on the combined dataset
# 4. Saves updated .pkl files (overwrites old ones)
# ─────────────────────────────────────────────

SYNTHETIC_PATH = 'data/synthetic/training_data.csv'
REAL_PATH      = 'data/real/real_data.csv'
MODELS_DIR     = 'model/models'

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

# ── Load and merge ─────────────────────────────
print("Loading datasets...")
df_synthetic = pd.read_csv(SYNTHETIC_PATH)
df_real      = pd.read_csv(REAL_PATH)

df_synthetic['source'] = 'synthetic'

# Merge — pandas aligns columns automatically, fills missing with NaN
df_combined = pd.concat([df_synthetic, df_real], ignore_index=True)

print(f"  Synthetic rows : {len(df_synthetic)}")
print(f"  Real rows      : {len(df_real)}")
print(f"  Combined total : {len(df_combined)}")
print(f"\nLabel distribution (combined):")
print(df_combined['label'].value_counts())
print(f"\nSource breakdown:")
print(df_combined['source'].value_counts())

# Save combined dataset for reference
combined_path = 'data/combined_training_data.csv'
df_combined.to_csv(combined_path, index=False)
print(f"\nCombined dataset saved to: {combined_path}")

# ── Retrain per layer ──────────────────────────
print(f"\n{'─'*50}")
print("Retraining models on combined data...")

for layer, features in LAYER_FEATURES.items():

    print(f"\n{'─'*50}")
    print(f"Layer: {layer.upper()}")

    layer_df = df_combined[
        df_combined['layer'] == layer
    ][features + ['label']].dropna()

    print(f"  Total rows available : {len(layer_df)}")
    print(f"  Risky (1)            : {(layer_df['label']==1).sum()}")
    print(f"  Safe  (0)            : {(layer_df['label']==0).sum()}")

    if len(layer_df) < 10:
        print(f"  Skipping — not enough data")
        continue

    X = layer_df[features]
    y = layer_df['label']

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # Random Forest
    rf = RandomForestClassifier(
        n_estimators=100,
        random_state=42,
        class_weight='balanced',
    )
    rf.fit(X_train, y_train)

    y_pred = rf.predict(X_test)
    report = classification_report(
        y_test, y_pred, target_names=['safe', 'risky']
    )
    print(f"\n  Random Forest results:")
    print(report)

    # Top features
    importances = zip(features, rf.feature_importances_)
    sorted_imp  = sorted(importances, key=lambda x: x[1], reverse=True)
    print(f"  Top 3 features:")
    for fname, score in sorted_imp[:3]:
        print(f"    {fname}: {score:.3f}")

    # Save RF
    rf_path = os.path.join(MODELS_DIR, f'rf_{layer}.pkl')
    with open(rf_path, 'wb') as f:
        pickle.dump({'model': rf, 'features': features, 'layer': layer}, f)

    # Isolation Forest
    iso = IsolationForest(
        n_estimators=100,
        contamination=0.2,
        random_state=42,
    )
    iso.fit(X_train)

    iso_path = os.path.join(MODELS_DIR, f'iso_{layer}.pkl')
    with open(iso_path, 'wb') as f:
        pickle.dump({'model': iso, 'features': features, 'layer': layer}, f)

    print(f"  Models saved: rf_{layer}.pkl + iso_{layer}.pkl")

print(f"\n{'─'*50}")
print("All models retrained on combined real + synthetic data.")