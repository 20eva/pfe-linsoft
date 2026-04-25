import yaml
import re
import os

# ─────────────────────────────────────────────
# What this file does:
# Takes an Ansible playbook (.yml file) and
# returns a dictionary of numbers (features)
# that the ML model can read.
# ─────────────────────────────────────────────

# These are the patterns that look like secrets
# re.compile means "prepare this pattern for searching"
SECRET_PATTERNS = [
    re.compile(r'password\s*[:=]\s*\S+', re.IGNORECASE),
    re.compile(r'secret\s*[:=]\s*\S+', re.IGNORECASE),
    re.compile(r'api_key\s*[:=]\s*\S+', re.IGNORECASE),
    re.compile(r'token\s*[:=]\s*\S+', re.IGNORECASE),
]

# These are Ansible keywords that grant elevated privilege
PRIVILEGE_KEYWORDS = [
    'become: true',
    'become: yes',
    'sudo',
]

# These are dangerous Ansible modules
DANGEROUS_MODULES = [
    'shell',
    'command',
    'raw',
]


def extract_features(filepath):
    """
    Takes the path to an Ansible playbook file.
    Returns a dictionary of features (all numbers).
    """

    # Read the raw text of the file
    with open(filepath, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    # Parse the YAML into a Python structure
    try:
        parsed = yaml.safe_load(raw_text)
    except yaml.YAMLError:
        # If the file is broken YAML, that itself is suspicious
        parsed = None

    # Count total lines
    lines = raw_text.splitlines()
    total_lines = len(lines)

    # ── Feature 1: secret patterns found ──────
    secret_count = 0
    for pattern in SECRET_PATTERNS:
        matches = pattern.findall(raw_text)
        secret_count += len(matches)

    # ── Feature 2: privilege escalation ───────
    privilege_count = 0
    for keyword in PRIVILEGE_KEYWORDS:
        privilege_count += raw_text.lower().count(keyword)

    # ── Feature 3: dangerous modules used ─────
    dangerous_module_count = 0
    for module in DANGEROUS_MODULES:
        # Match "- shell:" or "  shell:" patterns
        pattern = re.compile(r'[-\s]' + module + r'\s*:', re.IGNORECASE)
        dangerous_module_count += len(pattern.findall(raw_text))

    # ── Feature 4: file is broken / unparseable
    is_broken = 1 if parsed is None else 0

    # ── Feature 5: total lines (size signal) ──
    # Large playbooks have more surface area for issues

    # ── Feature 6: has no_log: false ──────────
    # no_log should be true when handling secrets
    # if someone explicitly sets it to false, suspicious
    no_log_false = 1 if 'no_log: false' in raw_text.lower() else 0

    # ── Feature 7: number of tasks ────────────
    task_count = raw_text.lower().count('- name:')

    # Return all features as a clean dictionary
    features = {
        'secret_count':           secret_count,
        'privilege_count':        privilege_count,
        'dangerous_module_count': dangerous_module_count,
        'is_broken':              is_broken,
        'total_lines':            total_lines,
        'no_log_false':           no_log_false,
        'task_count':             task_count,
    }

    return features


# ─────────────────────────────────────────────
# This block only runs when you execute this
# file directly — not when it's imported
# ─────────────────────────────────────────────
if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python ansible_extractor.py <path_to_playbook.yml>")
        sys.exit(1)

    path = sys.argv[1]
    features = extract_features(path)

    print("\nExtracted features:")
    for key, value in features.items():
        print(f"  {key}: {value}")