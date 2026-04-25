import re

# ─────────────────────────────────────────────
# What this file does:
# Takes a Terraform .tf file and returns
# numeric features the ML model can read.
# We use regex instead of hcl2 parser because
# .tf files during a git diff may be partial
# and unparseable — regex is more resilient.
# ─────────────────────────────────────────────

# Patterns that suggest a hardcoded secret
SECRET_PATTERNS = [
    re.compile(r'password\s*=\s*"[^"]{3,}"', re.IGNORECASE),
    re.compile(r'secret\s*=\s*"[^"]{3,}"', re.IGNORECASE),
    re.compile(r'api_key\s*=\s*"[^"]{3,}"', re.IGNORECASE),
    re.compile(r'token\s*=\s*"[^"]{3,}"', re.IGNORECASE),
    re.compile(r'private_key\s*=\s*"[^"]{3,}"', re.IGNORECASE),
]

# Patterns that open network access
PORT_PATTERNS = [
    re.compile(r'from_port\s*=\s*0'),
    re.compile(r'to_port\s*=\s*65535'),
    re.compile(r'cidr_blocks\s*=\s*\[?"0\.0\.0\.0/0"\]?'),
    re.compile(r'ingress'),
]

# Privilege / admin level access patterns
PRIVILEGE_PATTERNS = [
    re.compile(r'AdministratorAccess', re.IGNORECASE),
    re.compile(r'arn:aws:iam::aws:policy/Administrator', re.IGNORECASE),
    re.compile(r'"Effect"\s*:\s*"Allow".*"Action"\s*:\s*"\*"', re.IGNORECASE),
    re.compile(r'privileged\s*=\s*true', re.IGNORECASE),
]

# Resources that when deleted are dangerous
DANGEROUS_DELETIONS = [
    re.compile(r'^-.*resource\s+"aws_db_instance"', re.MULTILINE),
    re.compile(r'^-.*resource\s+"aws_s3_bucket"', re.MULTILINE),
    re.compile(r'^-.*resource\s+"aws_vpc"', re.MULTILINE),
    re.compile(r'prevent_destroy\s*=\s*false', re.IGNORECASE),
]


def extract_features(filepath):
    """
    Takes path to a Terraform .tf file.
    Returns a dictionary of numeric features.
    """

    with open(filepath, 'r', encoding='utf-8') as f:
        raw_text = f.read()

    lines = raw_text.splitlines()
    total_lines = len(lines)

    # ── Feature 1: hardcoded secrets ──────────
    secret_count = 0
    for pattern in SECRET_PATTERNS:
        secret_count += len(pattern.findall(raw_text))

    # ── Feature 2: open ports / public access ─
    port_issue_count = 0
    for pattern in PORT_PATTERNS:
        port_issue_count += len(pattern.findall(raw_text))

    # ── Feature 3: privilege escalation ───────
    privilege_count = 0
    for pattern in PRIVILEGE_PATTERNS:
        privilege_count += len(pattern.findall(raw_text))

    # ── Feature 4: dangerous resource changes ─
    dangerous_deletion_count = 0
    for pattern in DANGEROUS_DELETIONS:
        dangerous_deletion_count += len(pattern.findall(raw_text))

    # ── Feature 5: resource count ─────────────
    # how many resources are defined total
    resource_count = len(re.findall(r'^resource\s+"', raw_text, re.MULTILINE))

    # ── Feature 6: uses variables properly ────
    # hardcoded values instead of var.* = bad
    hardcoded_values = len(re.findall(r'=\s*"[^${\n]{8,}"', raw_text))

    # ── Feature 7: has lifecycle protect ──────
    # prevent_destroy = true is good practice
    has_lifecycle_protect = 1 if 'prevent_destroy = true' in raw_text else 0

    # ── Feature 8: total lines ────────────────
    # large files = more surface area

    features = {
        'secret_count':             secret_count,
        'port_issue_count':         port_issue_count,
        'privilege_count':          privilege_count,
        'dangerous_deletion_count': dangerous_deletion_count,
        'resource_count':           resource_count,
        'hardcoded_values':         hardcoded_values,
        'has_lifecycle_protect':    has_lifecycle_protect,
        'total_lines':              total_lines,
    }

    return features


if __name__ == '__main__':
    import sys

    if len(sys.argv) < 2:
        print("Usage: python terraform_extractor.py <path_to_file.tf>")
        sys.exit(1)

    path = sys.argv[1]
    features = extract_features(path)

    print("\nExtracted Terraform features:")
    for key, value in features.items():
        print(f"  {key}: {value}")