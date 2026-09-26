#!/usr/bin/env python3
"""
scan_playbook.py

The real end-to-end workflow: point this at any Ansible file (yours or
anyone else's), and it runs every meaningful line through the trained
detector, reporting which lines look like real issues.

Usage:
    python scan_playbook.py path/to/some_playbook.yml
    python scan_playbook.py path/to/a/whole/project/folder
"""

import argparse
import sys
from pathlib import Path

import joblib

from recommendations import classify_and_recommend

def is_blank_or_trivial(line):
    stripped = line.strip()
    return len(stripped) < 5 or stripped in ("---", "...")


def scan_file(path, model, vectorizer, threshold):
    findings = []
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            lines = f.readlines()
    except Exception as e:
        print(f"Could not read {path}: {e}")
        return findings

    snippets, line_numbers = [], []
    for i, line in enumerate(lines, start=1):
        stripped = line.strip()
        if is_blank_or_trivial(stripped):
            continue
        snippets.append(stripped)
        line_numbers.append(i)

    if not snippets:
        return findings

    X = vectorizer.transform(snippets)
    probabilities = model.predict_proba(X)[:, 1]  # probability of class "1" (issue)

    for line_no, snippet, prob in zip(line_numbers, snippets, probabilities):
        if prob >= threshold:
            smell_code, recommendation = classify_and_recommend(snippet)
            findings.append({
                "file": str(path),
                "line": line_no,
                "snippet": snippet,
                "confidence": round(float(prob), 3),
                "smell_code": smell_code,
                "recommendation": recommendation,
            })
    return findings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("target", help="A .yml/.yaml file, or a folder to scan recursively")
    parser.add_argument("--model", default="detector_model.joblib")
    parser.add_argument("--vectorizer", default="detector_vectorizer.joblib")
    parser.add_argument("--threshold", type=float, default=0.5,
                         help="Minimum predicted probability to flag a line "
                              "as an issue (0.5 = default decision boundary; "
                              "raise it for fewer, higher-confidence flags)")
    parser.add_argument("--max-allowed", type=int, default=0,
                         help="How many findings are tolerated before this "
                              "counts as a pipeline FAILURE. Default 0 means "
                              "any finding at all blocks the job.")
    args = parser.parse_args()

    model = joblib.load(args.model)
    vectorizer = joblib.load(args.vectorizer)

    target = Path(args.target)
    if target.is_file():
        files = [target]
    else:
        files = list(target.rglob("*.yml")) + list(target.rglob("*.yaml"))

    print(f"Scanning {len(files)} file(s)...\n")

    all_findings = []
    for f in files:
        all_findings.extend(scan_file(f, model, vectorizer, args.threshold))

    if not all_findings:
        print("No issues found above the confidence threshold.")
        sys.exit(0)  # pipeline PASSES - safe to proceed

    all_findings.sort(key=lambda x: -x["confidence"])

    print(f"Found {len(all_findings)} potential issue(s):\n")
    for finding in all_findings:
        print(f"[{finding['confidence']:.0%} confidence] {finding['file']}:{finding['line']}")
        print(f"    Type: {finding['smell_code']}")
        print(f"    Line: {finding['snippet']}")
        print(f"    Recommendation: {finding['recommendation']}")
        print()

    if len(all_findings) > args.max_allowed:
        print(f"BLOCKED: {len(all_findings)} finding(s) exceed the allowed "
              f"maximum of {args.max_allowed}.")
        sys.exit(1)  # pipeline FAILS - blocks the job
    else:
        print(f"PASSED: {len(all_findings)} finding(s), within the allowed "
              f"maximum of {args.max_allowed}.")
        sys.exit(0)


if __name__ == "__main__":
    main()