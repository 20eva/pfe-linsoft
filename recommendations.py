"""
recommendations.py

Rule-based (not ML) module that, given a line already flagged as an
issue by the detector, guesses which SPECIFIC type of problem it is
using simple keyword/pattern matching, then looks up a human-readable
recommendation. No dataset or training needed - exactly the "simple
two-column sheet" approach the original planning guide recommended.

Import and use:
    from recommendations import classify_and_recommend
    smell_code, recommendation = classify_and_recommend(snippet_text)
"""

import re

# ---------------------------------------------------------------------
# Recommendation text per smell_code, written from GLITCH's own smell
# descriptions and standard Ansible/ansible-lint best practices.
# ---------------------------------------------------------------------
RECOMMENDATIONS = {
    "sec_hard_secr": (
        "Hard-coded secret. Move this value into HashiCorp Vault (or "
        "another secret manager) and reference it via a templated "
        "variable, e.g. {{ vault_secret_name }} - never commit the "
        "raw value to source control."
    ),
    "sec_hard_pass": (
        "Hard-coded password. Store it in Vault/an encrypted vars file "
        "(ansible-vault) and inject it at runtime instead of writing it "
        "in plaintext."
    ),
    "sec_hard_user": (
        "Hard-coded username. Move it to a variable file so it can be "
        "changed per-environment without editing the playbook itself."
    ),
    "sec_def_admin": (
        "Defaulting to an admin/root account. Create a dedicated, "
        "least-privilege user for this task instead of relying on an "
        "administrative account by default."
    ),
    "sec_https": (
        "Plain HTTP without TLS. Use https:// instead of http:// so "
        "traffic (including any credentials in transit) is encrypted."
    ),
    "sec_empty_pass": (
        "Empty password detected. Set a real, non-empty password, "
        "ideally generated and stored in Vault, not left blank."
    ),
    "sec_weak_crypto": (
        "Weak cryptographic algorithm (e.g. MD5, SHA-1, DES, RC4). "
        "Replace it with a modern, strong algorithm (e.g. SHA-256 or "
        "better, AES for encryption)."
    ),
    "sec_invalid_ip_bind": (
        "Binding to 0.0.0.0 exposes the service to every network "
        "interface. Bind to a specific, intended interface/IP instead, "
        "unless public exposure is genuinely required."
    ),
    "sec_no_integrity_check": (
        "A file is downloaded without verifying its integrity. Add a "
        "checksum (e.g. the 'checksum' parameter on get_url) to confirm "
        "the downloaded file hasn't been tampered with."
    ),
    "sec_susp_comm": (
        "Suspicious comment (TODO/HACK/FIXME). Review and resolve the "
        "underlying issue before this reaches production, or document "
        "why it's intentionally deferred."
    ),
    "design_duplicate_block": (
        "This block duplicates logic found elsewhere. Consider "
        "extracting it into a shared role, task file, or template to "
        "reduce repetition and maintenance risk."
    ),
    "implementation_long_statement": (
        "This statement is unusually long/complex. Break it into "
        "multiple simpler tasks or variables for readability and "
        "easier debugging."
    ),
    "sec_privilege_escalation": (
        "This task escalates privileges (become/become_user/root). "
        "Confirm this elevation is actually necessary, and scope it as "
        "narrowly as possible rather than defaulting to root."
    ),
    "sec_hard_user_generic": (
        "A specific username is hard-coded here. Move it to a variable "
        "so it can differ per environment without editing this file, "
        "and confirm it isn't a shared/generic account (e.g. 'guests')."
    ),
    "unknown": (
        "Flagged by the detector as a likely issue, but the specific "
        "type could not be determined automatically. Review the line "
        "manually."
    ),
}


# ---------------------------------------------------------------------
# Ordered keyword/pattern rules. Checked top to bottom; the first rule
# that matches wins. Order matters - more specific checks come first.
# ---------------------------------------------------------------------
def classify_and_recommend(snippet: str):
    text = snippet.lower()

    # Empty password: key present but value is empty/blank quotes
    if re.search(r'(password|passwd|pwd)\s*[:=]\s*["\']?\s*["\']?\s*$', text) or \
       re.search(r'(password|passwd|pwd)\s*[:=]\s*["\']{2}', text):
        return "sec_empty_pass", RECOMMENDATIONS["sec_empty_pass"]

    # Weak crypto algorithms
    if re.search(r'\b(md5|sha1|des|rc4)\b', text):
        return "sec_weak_crypto", RECOMMENDATIONS["sec_weak_crypto"]

    # Invalid IP binding
    if "0.0.0.0" in text:
        return "sec_invalid_ip_bind", RECOMMENDATIONS["sec_invalid_ip_bind"]

    # Suspicious comments
    if re.search(r'\b(todo|hack|fixme|xxx)\b', text):
        return "sec_susp_comm", RECOMMENDATIONS["sec_susp_comm"]

    # Hard-coded password (a real-looking value, not empty)
    if re.search(r'(password|passwd|pwd)\s*[:=]\s*["\']?\S+', text):
        return "sec_hard_pass", RECOMMENDATIONS["sec_hard_pass"]

    # Hard-coded secret / token / key
    if re.search(r'(secret|token|api_key|private_key|vault_root_token)\s*[:=]\s*["\']?\S+', text):
        return "sec_hard_secr", RECOMMENDATIONS["sec_hard_secr"]

    # Admin by default
    if re.search(r'(user|username)\s*[:=]\s*["\']?admin["\']?', text) or \
       re.search(r'\badmin\b.*\badmin\b', text):
        return "sec_def_admin", RECOMMENDATIONS["sec_def_admin"]

    # Hard-coded username (generic)
    if re.search(r'(user|username|db_user)\s*[:=]\s*["\']?\w+', text):
        return "sec_hard_user", RECOMMENDATIONS["sec_hard_user"]

    # Privilege escalation (become / become_user / explicit root)
    if re.search(r'\bbecome_user\b', text) or re.search(r'\bbecome\s*:\s*true\b', text) or \
       re.search(r'\broot\b', text):
        return "sec_privilege_escalation", RECOMMENDATIONS["sec_privilege_escalation"]

    # Generic shared/hard-coded account names (guests, service accounts, etc.)
    if re.search(r'\b(guests?|db_user|service_account)\b', text):
        return "sec_hard_user_generic", RECOMMENDATIONS["sec_hard_user_generic"]

    # HTTP without TLS
    if "http://" in text and "https://" not in text:
        return "sec_https", RECOMMENDATIONS["sec_https"]

    # Download without integrity check
    if "get_url" in text and "checksum" not in text:
        return "sec_no_integrity_check", RECOMMENDATIONS["sec_no_integrity_check"]

    # Long statement (heuristic: long line)
    if len(snippet) > 150:
        return "implementation_long_statement", RECOMMENDATIONS["implementation_long_statement"]

    # No specific rule matched
    return "unknown", RECOMMENDATIONS["unknown"]