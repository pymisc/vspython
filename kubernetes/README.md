# Kubernetes Security & Compliance

This directory contains production-ready Kubernetes manifests designed to pass strict security and compliance scans (specifically [Checkov](https://www.checkov.io/)). 

By default, Kubernetes prioritizes ease-of-use over security, often running containers as `root` with infinite resource limits. The files in this repository demonstrate how to explicitly lock down Kubernetes workloads using a "Zero Trust" and least-privilege approach.

## 📁 Files in this Directory

### 1. `simple_pod_with_compliance.yml`
This manifest deploys a standard Nginx pod, but it has been heavily hardened against container escape vulnerabilities and resource exhaustion.

**Key Security Features:**
* **Non-Root Execution:** The pod is forced to run as user `10001`. It explicitly forbids privilege escalation (`allowPrivilegeEscalation: false`).
* **Dropped Capabilities:** Standard Linux capabilities (like `NET_RAW`) are entirely dropped, preventing the container from tampering with the host network or executing advanced system calls.
* **Read-Only Root Filesystem:** The container's root filesystem is set to read-only (`readOnlyRootFilesystem: true`). This prevents attackers from downloading malware or altering system binaries if the container is compromised. 
  * *Note:* An ephemeral `emptyDir` volume is mounted to `/tmp` to allow Nginx to write temporary PID and cache files without compromising the root filesystem.
* **Resource Boundaries:** Strict memory and CPU `requests` and `limits` are defined to prevent the pod from starving the host node of resources.
* **Automount Service Token Disabled:** Kubernetes automatically mounts a highly privileged API token into every pod. This is explicitly disabled (`automountServiceAccountToken: false`) since this pod does not need to communicate with the Kubernetes API.
* **Health Probes:** Both `livenessProbe` and `readinessProbe` are configured to ensure traffic is only routed to the pod when it is genuinely healthy.

### 2. `network_policy.yml`
This manifest acts as a firewall for the pod, satisfying Checkov's multi-resource graph checks (e.g., `CKV2_K8S_6`).

**Key Security Features:**
* **Default Deny (Egress):** By default, Kubernetes allows pods to communicate with the outside world. This policy explicitly drops all outbound traffic by leaving the `egress.to` block empty.
* **Strict Ingress:** It only allows incoming TCP traffic on the specific port the container is listening on (Port 8080).
* **Dynamic Linking:** The policy binds to the pod dynamically using the `podSelector` matching the `app: test` label.

## 🚀 Running Compliance Scans locally

To verify the security posture of these manifests, you can run Checkov locally before committing your code:

1. Install Checkov:
   ```bash
   pip install checkov
   