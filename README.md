
# OKD DevSecOps Platform — Infrastructure as Code



> **Status:** Layer 1 (Ansible) ✅ | Layer 2 (OKD SNO) 🔄 In Progress | Layers 3–8 ⏳ Pending



A full-stack DevSecOps platform built on OKD 4.21, provisioned with Ansible, running on KVM/libvirt.



## Architecture



\`\`\`

Layer 8 — AI/ML (AIOps)       FastAPI · Scikit-learn · Prophet

Layer 7 — Auto-scaling         KEDA · TimescaleDB

Layer 6 — Observability        Prometheus · Loki · Tempo · Grafana

Layer 5 — GitOps               ArgoCD · Helm · Kustomize · Flagger

Layer 4 — Security             SonarQube · Trivy · Cosign · Kyverno · Vault

Layer 3 — CI/CD                GitLab · ArgoCD

Layer 2 — OKD                  Single Node OKD 4.21 on SCOS

Layer 1 — Ansible              VM provisioning · Bootstrap

\`\`\`



## Infrastructure



### Host

| Component | Value |

|-----------|-------|

| Host IP | 192.168.100.1 |

| RAM | 40 GB |

| Hypervisor | KVM / libvirt |



### Storage (sdb 931G — vg-okd)

| Volume | Size | Mount | Purpose |

|--------|------|-------|---------|

| lv-isos | 50G | /storage/isos | ISOs |

| lv-vm-images | 200G | /storage/vm-images | VM disks |

| lv-ocp-data | 600G | /storage/ocp-data | OKD PVs |



### Virtual Machines

| VM | IP | vCPU | RAM | OS |

|----|----|------|-----|----|

| bastion | 192.168.100.10 | 2 | 4G | Rocky Linux 9 |

| okd-node | 192.168.100.50 | 8 | 16G | SCOS 10.0 |



### Network — okd-net (virbr1)

- Subnet: 192.168.100.0/24

- Gateway: 192.168.100.1

- Mode: NAT with static DHCP reservations



### Bastion Services

| Service | Port | Purpose |

|---------|------|---------|

| BIND | 53 | DNS for okd.local |

| HAProxy | 6443 | Kubernetes API |

| HAProxy | 22623 | Machine Config |

| HAProxy | 80/443 | Ingress |

| httpd | 8080 | Ignition files |



### DNS Records

\`\`\`

api.sno.okd.local      → 192.168.100.50

api-int.sno.okd.local  → 192.168.100.50

*.apps.sno.okd.local   → 192.168.100.50

bastion.okd.local      → 192.168.100.10

\`\`\`



## OKD Cluster

| Property | Value |

|----------|-------|

| Version | 4.21.0-okd-scos.1 |

| Type | Single Node OKD (SNO) |

| Install | UPI |

| API | https://api.sno.okd.local:6443 |

| Console | https://console-openshift-console.apps.sno.okd.local |



## Project Structure

\`\`\`

okd-ansible/

├── site.yml

├── create-vm.yml

├── vars/main.yml

├── inventory/hosts.ini

└── roles/

    ├── create-bastion/

    ├── create-okd-node/

    ├── configure-bastion/

    ├── generate-ignition/

    ├── embed-iso/

    ├── boot-okd-node/

    └── monitor-sno/

\`\`\`



## Quick Start



### 1. Create okd-node VM

\`\`\`bash

ansible-playbook create-vm.yml

\`\`\`



### 2. Configure bastion

\`\`\`bash

ansible-playbook site.yml --tags configure-bastion

\`\`\`



### 3. Generate ignition (on bastion)

\`\`\`bash

cd /home/admin/okd-install/sno

openshift-install create ignition-configs --dir .

sudo cp bootstrap.ign master.ign /var/www/html/ignition/

\`\`\`



### 4. Install SCOS (in node console)

\`\`\`bash

curl -s http://192.168.100.10:8080/install.sh | sudo bash

\`\`\`



### 5. Monitor bootstrap

\`\`\`bash

export KUBECONFIG=/home/admin/okd-install/sno/auth/kubeconfig

openshift-install wait-for bootstrap-complete --dir /home/admin/okd-install/sno

\`\`\`



## Progress

| Layer | Status |

|-------|--------|

| Storage (sdb LVM) | ✅ Done |

| Bastion VM | ✅ Running |

| okd-node VM | ✅ Running |

| BIND DNS | ✅ Configured |

| HAProxy | ✅ Configured |

| httpd | ✅ Configured |

| SCOS installed | ✅ Done |

| OKD Bootstrap | 🔄 In Progress |

| Cluster API | ⏳ Pending |

| Layers 3-8 | ⏳ Pending |



## Troubleshooting



### Bootkube stuck

\`\`\`bash

ssh core@192.168.100.50 "sudo systemctl restart bootkube.service"

\`\`\`



### Check API

\`\`\`bash

curl -sk https://192.168.100.50:6443/version | head -3

\`\`\`



### quay.io speed (needs 100KB/s minimum)

\`\`\`bash

curl -sk --max-time 5 -w 'Speed: %{speed_download} bytes/sec\n' -o /dev/null https://quay.io/v2/

\`\`\`



## Author

PFE Project — Linsoft | 2025–2026

