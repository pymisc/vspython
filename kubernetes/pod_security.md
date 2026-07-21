# Kubernetes Pod Security & Best Practices Checklist 

Use this checklist as a quick reminder when creating Kubernetes Pods. Following these practices helps build workloads that are **more secure, reliable, and production-ready**. 

| ✔ | Best Practice | Why it matters | 
|---|---------------|----------------| 
| ✅ | **Dedicated Namespace** | Avoid deploying applications into the `default` namespace. Namespaces provide logical isolation and make it easier to manage security, quotas, RBAC, and network policies. | 
| ✅ | **Dedicated ServiceAccount** | Use a dedicated ServiceAccount instead of the default one. This allows fine-grained RBAC permissions following the principle of least privilege. | 
| ✅ | **Disable ServiceAccount Token (if not needed)** | Set `automountServiceAccountToken: false` when the application doesn't need to call the Kubernetes API, reducing the attack surface. | 
| ✅ | **Run as Non-Root User** | Containers should never run as `root` unless absolutely necessary. Running as a non-root user limits the impact of a container compromise. | 
| ✅ | **Use RuntimeDefault Seccomp Profile** | Restrict the Linux system calls available to the container, helping reduce the kernel attack surface. | 
| ✅ | **Disable Privilege Escalation** | Prevent processes inside the container from gaining additional privileges, even if they contain setuid/setgid binaries. | 
| ✅ | **Drop Linux Capabilities** | Remove unnecessary Linux capabilities (preferably `ALL`) so the container only has the minimum privileges required. | 
| ✅ | **Read-Only Root Filesystem** | Prevent applications or attackers from modifying the container image at runtime. Use writable volumes (such as `emptyDir`) only where necessary. | 
| ✅ | **Use Immutable Image Digest** | Pin container images using a SHA256 digest instead of mutable tags like `latest` to ensure reproducible and predictable deployments. | 
| ✅ | **Define CPU & Memory Requests/Limits** | Requests help the scheduler place Pods correctly, while limits prevent a single container from consuming excessive node resources. | 
| ✅ | **Configure Health Probes** | Use **Startup**, **Readiness**, and **Liveness** probes so Kubernetes knows when to start routing traffic, detect unhealthy applications, and recover failed containers automatically. | 
| ✅ | **Apply Network Policies** | Follow the principle of least privilege by allowing only the required ingress and egress traffic instead of permitting unrestricted network access. | 

--- 

## Goal A secure Kubernetes Pod should follow the **Principle of Least Privilege**: 
- Minimal permissions 
- Minimal filesystem access 
- Minimal Linux capabilities 
- Minimal network access 
- Minimal Kubernetes API access 

These practices form a strong baseline for building secure, reliable, and production-ready Kubernetes workloads.

