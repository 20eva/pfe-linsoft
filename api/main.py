import pickle
import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import pandas as pd

# ─────────────────────────────────────────────
# What this file does:
# Starts an HTTP server with one endpoint:
# POST /predict
# GitLab CI sends features → gets risk score back
# ─────────────────────────────────────────────

app = FastAPI(title="AIOps Risk Predictor")

MODELS_DIR = os.path.join(os.path.dirname(__file__), '..', 'model', 'models')

# ── Load all models at startup ─────────────────
# This runs once when the server starts
# All models stay in memory — predictions are fast
models = {}

for layer in ['ci', 'ansible', 'terraform', 'k8s']:
    rf_path  = os.path.join(MODELS_DIR, f'rf_{layer}.pkl')
    iso_path = os.path.join(MODELS_DIR, f'iso_{layer}.pkl')

    with open(rf_path, 'rb') as f:
        models[f'rf_{layer}'] = pickle.load(f)

    with open(iso_path, 'rb') as f:
        models[f'iso_{layer}'] = pickle.load(f)

print(f"Loaded {len(models)} models successfully")


# ── Request shape ──────────────────────────────
# This defines exactly what JSON GitLab must send
class PredictRequest(BaseModel):
    layer: str                    # which layer: ci, ansible, terraform, k8s
    features: dict                # the feature dictionary from the extractor


# ── Response shape ─────────────────────────────
class PredictResponse(BaseModel):
    layer:       str
    risk:        str              # LOW, MEDIUM, HIGH
    rf_score:    float            # 0.0 → 1.0 from Random Forest
    iso_score:   float            # 0.0 → 1.0 from Isolation Forest
    final_score: float            # combined score
    action:      str              # block or alert or pass
    reasons:     list             # human readable explanation


def score_to_risk(score: float) -> tuple:
    """Convert numeric score to risk label and action."""
    if score >= 0.70:
        return 'HIGH', 'block'
    elif score >= 0.40:
        return 'MEDIUM', 'alert'
    else:
        return 'LOW', 'pass'


def build_reasons(features: dict, layer: str) -> list:
    """Generate human-readable reasons from features."""
    reasons = []

    if layer == 'ci':
        if features.get('vuln_count', 0) > 5:
            reasons.append(f"High vulnerability count: {features['vuln_count']}")
        if features.get('critical_vulns', 0) > 0:
            reasons.append(f"Critical vulnerabilities: {features['critical_vulns']}")
        if features.get('prev_failed', 0) == 1:
            reasons.append("Previous deployment failed")
        if features.get('lines_changed', 0) > 300:
            reasons.append(f"Large diff: {features['lines_changed']} lines")
        if features.get('sonar_score', 100) < 70:
            reasons.append(f"Low SonarQube score: {features['sonar_score']}")
        if features.get('is_friday', 0) == 1:
            reasons.append("Friday deployment — higher risk")

    elif layer == 'ansible':
        if features.get('secret_count', 0) > 0:
            reasons.append(f"Hardcoded secrets detected: {features['secret_count']}")
        if features.get('privilege_count', 0) > 0:
            reasons.append(f"Privilege escalation present: {features['privilege_count']}")
        if features.get('dangerous_module_count', 0) > 0:
            reasons.append(f"Dangerous modules used: {features['dangerous_module_count']}")
        if features.get('no_log_false', 0) == 1:
            reasons.append("no_log set to false — secrets may be logged")
        if features.get('is_broken', 0) == 1:
            reasons.append("Playbook is invalid YAML")

    elif layer == 'terraform':
        if features.get('secret_count', 0) > 0:
            reasons.append(f"Hardcoded secrets: {features['secret_count']}")
        if features.get('port_issue_count', 0) > 0:
            reasons.append(f"Open port/firewall rules: {features['port_issue_count']}")
        if features.get('privilege_count', 0) > 0:
            reasons.append(f"Privilege escalation: {features['privilege_count']}")
        if features.get('dangerous_deletion_count', 0) > 0:
            reasons.append(f"Dangerous resource deletions: {features['dangerous_deletion_count']}")
        if features.get('has_lifecycle_protect', 1) == 0:
            reasons.append("No lifecycle protection on resources")

    elif layer == 'k8s':
        if features.get('runs_as_root', 0) == 1:
            reasons.append("Container runs as root")
        if features.get('privileged', 0) == 1:
            reasons.append("Privileged container detected")
        if features.get('dangerous_cap_count', 0) > 0:
            reasons.append(f"Dangerous capabilities: {features['dangerous_cap_count']}")
        if features.get('host_network', 0) == 1:
            reasons.append("Host network access enabled")
        if features.get('no_resource_limits', 0) == 1:
            reasons.append("No resource limits set")
        if features.get('latest_tag_count', 0) > 0:
            reasons.append(f"Using :latest image tag")

    if not reasons:
        reasons.append("No specific issues detected")

    return reasons


@app.get("/health")
def health():
    """Simple health check — confirms API is running."""
    return {"status": "ok", "models_loaded": len(models)}


@app.post("/predict", response_model=PredictResponse)
def predict(request: PredictRequest):
    """
    Main prediction endpoint.
    Receives layer name + features dict.
    Returns risk score + action + reasons.
    """

    layer = request.layer.lower()

    if layer not in ['ci', 'ansible', 'terraform', 'k8s']:
        raise HTTPException(status_code=400, detail=f"Unknown layer: {layer}")

    rf_bundle  = models[f'rf_{layer}']
    iso_bundle = models[f'iso_{layer}']

    rf_model       = rf_bundle['model']
    iso_model      = iso_bundle['model']
    expected_feats = rf_bundle['features']

    # Build feature row in the exact order the model expects
    row = {f: request.features.get(f, 0) for f in expected_feats}
    df  = pd.DataFrame([row])

    # Random Forest: probability of being risky (class 1)
    rf_score = float(rf_model.predict_proba(df)[0][1])

    # Isolation Forest: -1 = anomaly, 1 = normal
    # Convert to 0.0→1.0 score
    iso_raw   = iso_model.decision_function(df)[0]
    iso_score = float(1 / (1 + abs(iso_raw)))

    # Combine both scores — RF weighted more heavily
    final_score = (rf_score * 0.7) + (iso_score * 0.3)

    risk, action = score_to_risk(final_score)
    reasons      = build_reasons(request.features, layer)

    return PredictResponse(
        layer       = layer,
        risk        = risk,
        rf_score    = round(rf_score, 3),
        iso_score   = round(iso_score, 3),
        final_score = round(final_score, 3),
        action      = action,
        reasons     = reasons,
    )