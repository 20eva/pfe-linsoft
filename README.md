# DevSecOps Platform on OpenShift OKD 4.20

A cloud-native DevSecOps platform built entirely on open source tools, deployed on a Single Node OpenShift OKD 4.20 cluster, and provisioned end-to-end through Ansible AWX. Built during a final year engineering internship at **Linsoft Tunisia**.

---

## Platform Overview

| Component | Technology |
|-----------|------------|
| Container Platform | OpenShift OKD 4.20 SNO |
| CI/CD Pipeline | Tekton Pipelines 0.65.0 |
| GitOps | ArgoCD 2.13.0 |
| Secrets Management | HashiCorp Vault 1.18.0 + ESO 0.10.0 |
| Admission Control | Kyverno 1.13.0 + Cosign 2.4.0 |
| Security Scanning | Trivy 0.58.0 + SonarQube 10.7.0 |
| Observability | Prometheus 2.55.0 + Grafana 11.3.0 + AlertManager 0.27.0 |
| Automation | Ansible AWX 24.6.1 |
| AI Detection | Logistic Regression — Flask 3.1.0 |

---

## Infrastructure

### Host Machine

| Component | Value |
|-----------|-------|
| OS | CentOS Stream 9 |
| Hypervisor | KVM / libvirt |
| Internal Network | virbr1 — 192.168.100.0/24 |
| Cluster Domain | sno.okd.local |

### Virtual Machines

| VM | IP | Role | Status |
|----|----|------|--------|
| okd-node | 192.168.100.50 | OKD Control Plane + Worker | Running |
| bastion | 192.168.100.10 | DNS + HAProxy | Shut down post-install |
| bootstrap | 192.168.100.20 | Temporary bootstrap | Shut down post-install |

### DNS Records

api.sno.okd.local → 192.168.100.50
api-int.sno.okd.local → 192.168.100.50
*.apps.sno.okd.local → 192.168.100.50



---

## CI/CD Pipeline — 9 Stages

git push → GitHub webhook → bore tunnel → Tekton EventListener
↓
Stage 1 — Clone
Stage 2 — AI Detection & Recommendation ← security gate
Stage 3 — Build
Stage 4 — SonarQube Scan
Stage 5 — Quality Gate ← security gate
Stage 6 — Docker Build
Stage 7 — Trivy Scan ← security gate
Stage 8 — Cosign Sign ← security gate
Stage 9 — Deploy via ArgoCD
↓
Notify — HTML email + PDF security report

Each stage is a security gate. A failure at any stage blocks the pipeline immediately and triggers an email notification with a full PDF report.

---

## AI Detection & Recommendation Model

A Logistic Regression classifier trained on 125 real open-source Ansible projects, deployed as a Flask REST API inside the OKD cluster. Integrated as Stage 2 of the Tekton pipeline.

### Performance

| Metric | Value |
|--------|-------|
| Algorithm | Logistic Regression (group-split validation) |
| Training dataset | 125 real Ansible projects |
| Accuracy | 74% on unseen projects |
| Precision | 83% |
| Recall | 46% |
| Confidence threshold | 0.85 |

### Issue Types Detected

| Type | Description |
|------|-------------|
| sec_hard_secr | Hardcoded secrets |
| sec_hard_pass | Hardcoded passwords |
| sec_def_admin | Default admin accounts |
| sec_https | Insecure HTTP usage |

### Real Finding on Linsoft Project

[92%] security/roles/deploy-vault/tasks/main.yml
Type: sec_hard_secr
Line: vault_root_token: root
Fix: Store in HashiCorp Vault and reference via {{ vault_secret_name }}

Result: 39 issues detected — Pipeline BLOCKED — PDF report sent by email


---

## Security Architecture

Developer pushes code
↓
AI scans Ansible playbooks ← catches misconfigurations before build
↓
SonarQube scans source code ← catches code quality and security issues
↓
Trivy scans container image ← catches known CVEs
↓
Cosign signs the image ← creates cryptographic proof of integrity
↓
Kyverno verifies signature ← blocks unsigned images at cluster level
↓
Vault injects secrets at runtime ← zero plaintext credentials anywhere


---

## Observability

| Tool | Role |
|------|------|
| Prometheus | Metrics collection — scrapes every 15s |
| Grafana | Unified dashboards — Node, Cluster, Pod views |
| AlertManager | 14 custom alert rules with HTML email notifications |

---

## Automation — Ansible AWX

17 Ansible playbooks organized across 6 infrastructure layers, all managed through AWX.

| Layer | Content |
|-------|---------|
| Layer 1 | Infrastructure — KVM, OKD, DNS, Networking |
| Layer 2 | Security — Vault, Kyverno, Cosign, ESO |
| Layer 3 | CI/CD — Tekton, SonarQube |
| Layer 4 | GitOps — ArgoCD |
| Layer 5 | Observability — Prometheus, Grafana, AlertManager |
| Layer 6 | Recovery — Full platform recovery in under 5 minutes |

---

## Platform URLs

| Service | URL |
|---------|-----|
| OKD Console | https://console-openshift-console.apps.sno.okd.local |
| ArgoCD | https://argocd-server-argocd.apps.sno.okd.local |
| Vault | https://vault.apps.sno.okd.local |
| SonarQube | https://sonarqube-sonarqube.apps.sno.okd.local |
| Grafana | https://grafana-openshift-monitoring.apps.sno.okd.local |
| AlertManager | https://alertmanager-main-openshift-monitoring.apps.sno.okd.local |
| AWX | https://awx.apps.sno.okd.local |
| Blog API | http://blog-api-blog-app.apps.sno.okd.local |

---

## Repository Structure
pfe-linsoft/
├── branch: playbooks → Ansible playbooks + Kubernetes manifests
├── branch: sample-app → Blog API application + Tekton pipeline
└── branch: main → Documentation + README


---

## Quick Start

### Connect to OKD

```bash
/usr/local/bin/okd-login.sh
```

### Trigger Pipeline

```bash
cd /tmp/sample-app
git add .
git commit -m "feat: your change"
git push origin sample-app
```

### Check Pipeline Status

```bash
/usr/local/bin/oc get pipelinerun -n blog-app \
  --insecure-skip-tls-verify \
  --sort-by=.metadata.creationTimestamp | tail -5
```

### Platform Health Check

```bash
/usr/local/bin/oc get pods --all-namespaces \
  --insecure-skip-tls-verify | grep -v "Running\|Completed"
```

### Platform Recovery

```bash
# Recommended: AWX → Job Templates → platform-recovery → Launch

# Manual fallback
systemctl restart bore-tunnel.service
/usr/local/bin/oc rollout restart deployment -n kyverno \
  --insecure-skip-tls-verify
```

---

## Documentation

| Document | Description |
|----------|-------------|
| [Technical User Guide](docs/Guide_Utilisation_EN.pdf) | Complete platform administration and troubleshooting guide |

---

## Author

**Yefa Attia**
ESPRIT School of Engineering | Linsoft Tunisia | 2025
