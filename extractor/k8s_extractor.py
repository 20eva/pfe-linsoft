import yaml
import re

# ─────────────────────────────────────────────
# What this file does:
# Takes a Kubernetes/OKD manifest (.yml) and
# returns numeric features for the ML model.
# Covers Deployments, Services, and general
# manifest security posture.
# ─────────────────────────────────────────────

DANGEROUS_CAPABILITIES = [
    'SYS_ADMIN', 'NET_ADMIN', 'ALL',
    'SYS_PTRACE', 'SYS_MODULE',
]


def extract_features(filepath):
    """
    Takes path to a Kubernetes manifest .yml file.
    Returns a dictionary of numeric features.
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # K8s files can have multiple documents separated by ---
    try:
        docs = list(yaml.safe_load_all(raw_text))
        docs = [d for d in docs if d is not None]
        is_broken = 0
    except yaml.YAMLError:
        docs = []
        is_broken = 1

    # ── Feature 1: runs as root ────────────────
    # runAsUser: 0 means root — very bad
    runs_as_root = 1 if re.search(r'runAsUser\s*:\s*0', raw_text) else 0

    # ── Feature 2: privileged container ───────
    privileged = 1 if re.search(
        r'privileged\s*:\s*true', raw_text, re.IGNORECASE
    ) else 0

    # ── Feature 3: dangerous capabilities ─────
    dangerous_cap_count = 0
    for cap in DANGEROUS_CAPABILITIES:
        if cap in raw_text:
            dangerous_cap_count += 1

    # ── Feature 4: host network access ────────
    host_network = 1 if re.search(
        r'hostNetwork\s*:\s*true', raw_text, re.IGNORECASE
    ) else 0

    # ── Feature 5: host path mounts ───────────
    # mounting host filesystem into container
    host_path_count = len(re.findall(r'hostPath', raw_text))

    # ── Feature 6: no resource limits set ─────
    # containers without limits can consume all node resources
    has_limits = 1 if 'limits' in raw_text else 0
    no_resource_limits = 1 if not has_limits else 0

    # ── Feature 7: image uses latest tag ──────
    # latest tag = unpredictable deployments
    latest_tag_count = len(re.findall(r'image:.*:latest', raw_text))

    # ── Feature 8: hardcoded secrets in env ───
    secret_in_env = len(re.findall(
        r'(?:PASSWORD|SECRET|TOKEN|KEY)\s*:\s*\S+',
        raw_text, re.IGNORECASE
    ))

    # ── Feature 9: allow privilege escalation ─
    allow_priv_esc = 1 if re.search(
        r'allowPrivilegeEscalation\s*:\s*true', raw_text
    ) else 0

    # ── Feature 10: number of documents ───────
    doc_count = len(docs)

    # ── Feature 11: is broken YAML ────────────

    features = {
        'runs_as_root':         runs_as_root,
        'privileged':           privileged,
        'dangerous_cap_count':  dangerous_cap_count,
        'host_network':         host_network,
        'host_path_count':      host_path_count,
        'no_resource_limits':   no_resource_limits,
        'latest_tag_count':     latest_tag_count,
        'secret_in_env':        secret_in_env,
        'allow_priv_esc':       allow_priv_esc,
        'doc_count':            doc_count,
        'is_broken':            is_broken,
    }

    return features


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python k8s_extractor.py <path_to_manifest.yml>")
        sys.exit(1)

    path = sys.argv[1]
    features = extract_features(path)

    print("\nExtracted K8s features:")
    for key, value in features.items():
        print(f"  {key}: {value}")