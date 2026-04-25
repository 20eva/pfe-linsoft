import sys
import os
import requests

sys.path.insert(0, os.path.abspath('.'))

from extractor.ansible_extractor import extract_features as ansible_features
from extractor.terraform_extractor import extract_features as terraform_features
from extractor.k8s_extractor import extract_features as k8s_features

API_URL = "http://127.0.0.1:8000/predict"

def predict(layer, features):
    response = requests.post(API_URL, json={"layer": layer, "features": features})
    return response.json()

def print_result(label, result):
    print(f"\n{'═'*50}")
    print(f"  FILE     : {label}")
    print(f"  RISK     : {result['risk']}")
    print(f"  ACTION   : {result['action'].upper()}")
    print(f"  FINAL    : {result['final_score']}")
    print(f"  REASONS:")
    for r in result['reasons']:
        print(f"    → {r}")

# Test 1: bad Ansible playbook
feats = ansible_features('test_files/test_playbook.yml')
result = predict('ansible', feats)
print_result('test_playbook.yml (bad)', result)

# Test 2: bad Terraform file
feats = terraform_features('test_files/test_main.tf')
result = predict('terraform', feats)
print_result('test_main.tf (bad)', result)

# Test 3: bad K8s manifest
feats = k8s_features('test_files/test_deployment.yml')
result = predict('k8s', feats)
print_result('test_deployment.yml (bad)', result)

# Test 4: clean Ansible (safe baseline)
clean_ansible = {
    'secret_count': 0, 'privilege_count': 0,
    'dangerous_module_count': 0, 'is_broken': 0,
    'total_lines': 30, 'no_log_false': 0, 'task_count': 3,
}
result = predict('ansible', clean_ansible)
print_result('clean ansible (safe)', result)

# Test 5: clean CI run (safe baseline)
clean_ci = {
    'vuln_count': 1, 'sonar_score': 92.0, 'lines_changed': 45,
    'prev_failed': 0, 'commit_freq': 2.0, 'new_files': 1,
    'deleted_files': 0, 'critical_vulns': 0,
    'build_time_seconds': 180, 'is_friday': 0,
}
result = predict('ci', clean_ci)
print_result('clean CI run (safe)', result)

# Test 6: risky CI run
risky_ci = {
    'vuln_count': 14, 'sonar_score': 51.0, 'lines_changed': 851,
    'prev_failed': 1, 'commit_freq': 10.0, 'new_files': 7,
    'deleted_files': 8, 'critical_vulns': 1,
    'build_time_seconds': 24, 'is_friday': 1,
}
result = predict('ci', risky_ci)
print_result('risky CI run (bad)', result)

print(f"\n{'═'*50}")
print("All tests done.")