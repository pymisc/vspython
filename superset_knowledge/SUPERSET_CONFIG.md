# Apache Superset — Docker Desktop Kubernetes + Ubuntu Apache Reverse Proxy

## Purpose

This document records the working configuration used to run **Apache Superset inside Docker Desktop Kubernetes on a Windows system** and expose it externally as:

```text
https://superset.aaravsharma.net
```

The important design point is that Superset does **not** run on the Ubuntu laptop. The Windows system hosts Docker Desktop, Kubernetes, Superset, and ingress-nginx. The Ubuntu ThinkPad runs Apache2 and acts as the HTTPS/public reverse proxy.

This is intended as a quick-recall / rebuild guide months later.

---

## 1. Working Architecture

```text
Internet / Browser
        |
        |  https://superset.aaravsharma.net
        v
Route 53 DNS
        |
        v
Ubuntu ThinkPad
192.168.86.35
Apache2 :443
TLS certificate terminates here
        |
        | HTTP reverse proxy
        | Host: superset.aaravsharma.net
        v
Windows system
192.168.86.45
Docker Desktop + Kubernetes
        |
        | TCP 30080
        v
ingress-nginx Controller
NodePort 30080 -> port 80
        |
        | Kubernetes Ingress rule
        v
Superset Service
ClusterIP 10.109.59.180:8088
        |
        v
Apache Superset Pods
```

Docker Desktop's internal Kubernetes node IP was observed as:

```text
192.168.65.3
```

That internal address is **not** what the Ubuntu Apache proxy uses. Ubuntu connects to the Windows LAN address:

```text
192.168.86.45:30080
```

---

## 2. Machine / Network Reference

| Component | Address / Port | Purpose |
|---|---|---|
| Ubuntu ThinkPad | `192.168.86.35` | Apache2 public/reverse-proxy host |
| Windows system | `192.168.86.45` | Docker Desktop host |
| Docker Desktop K8s node | `192.168.65.3` | Docker Desktop internal Kubernetes node |
| ingress-nginx HTTP NodePort | `30080` | Entry point from Ubuntu to Windows Kubernetes |
| ingress-nginx HTTPS NodePort | `30443` | Kubernetes HTTPS NodePort, available if needed |
| Superset Service | `10.109.59.180:8088` | Kubernetes ClusterIP service |
| Public hostname | `superset.aaravsharma.net` | Browser-facing URL |

> **Key reminder:** `10.109.59.180` is a Kubernetes ClusterIP and is not expected to be reachable directly from the Ubuntu laptop. Apache reaches the Kubernetes application through the Windows host's ingress NodePort.

---

## 3. Superset Installation

Superset was installed into the Docker Desktop Kubernetes cluster with Helm.

### Add the Superset Helm repository

```bash
helm repo add superset https://apache.github.io/superset
helm repo update
```

### Create the namespace

```bash
kubectl create namespace superset
```

### Superset Helm values

The installation used a `values.yaml` with Superset `4.1.3`, bundled PostgreSQL and Redis, a configured `SECRET_KEY`, and proxy awareness enabled.

Representative configuration:

```yaml
image:
  tag: "4.1.3"

configOverrides:
  secret: |
    SECRET_KEY = "<YOUR-SUPERSET-SECRET-KEY>"
    ENABLE_PROXY_FIX = True
```

PostgreSQL and Redis supplied by the chart were used for this lab installation.

> Do not commit the real Superset `SECRET_KEY` to a public Git repository. Keep secrets in a local values file, Kubernetes Secret, or another secret-management mechanism.

### Install Superset

```bash
helm install superset superset/superset \
  --namespace superset \
  -f values.yaml
```

Useful validation commands:

```bash
kubectl get pods -n superset
kubectl get svc -n superset
kubectl get all -n superset
kubectl get jobs -n superset
```

If a pod is failing:

```bash
kubectl logs -n superset <pod-name>
```

During initial testing, Superset could also be accessed without ingress by using:

```bash
kubectl port-forward svc/superset -n superset 8088:8088
```

and opening:

```text
http://localhost:8088
```

This is useful for proving that Superset itself works before debugging ingress, Windows networking, Apache, DNS, or TLS.

---

## 4. Install ingress-nginx in Docker Desktop Kubernetes

The ingress controller was deliberately exposed as a **NodePort** so the separate Ubuntu system could reach it through the Windows LAN IP.

```bash
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
```

Install:

```bash
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace \
  --set controller.service.type=NodePort \
  --set controller.service.nodePorts.http=30080 \
  --set controller.service.nodePorts.https=30443
```

Verify:

```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
kubectl get ingressclass
```

The controller service should show ports similar to:

```text
80:30080/TCP
443:30443/TCP
```

and the ingress class should be:

```text
nginx
```

---

## 5. Superset Kubernetes Ingress

The Kubernetes Ingress uses the hostname to decide that requests belong to Superset.

Create an ingress similar to:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: superset
  namespace: superset
spec:
  ingressClassName: nginx
  rules:
    - host: superset.aaravsharma.net
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: superset
                port:
                  number: 8088
```

Apply it:

```bash
kubectl apply -f superset-ingress.yaml
```

Verify:

```bash
kubectl get ingress -n superset
kubectl describe ingress -n superset superset
```

The critical routing relationship is:

```text
Host: superset.aaravsharma.net
             |
             v
        ingress-nginx
             |
             v
     svc/superset:8088
```

---

## 6. Windows Firewall

The Windows firewall must permit the Ubuntu Apache host to reach ingress-nginx's HTTP NodePort.

For better isolation, the rule was restricted to the Ubuntu laptop rather than opening port `30080` to the entire LAN.

Run in an elevated PowerShell session on Windows:

```powershell
New-NetFirewallRule `
  -DisplayName "K8s Ingress HTTP from Ubuntu Laptop" `
  -Direction Inbound `
  -Protocol TCP `
  -LocalPort 30080 `
  -RemoteAddress 192.168.86.35 `
  -Profile Private `
  -Action Allow
```

The important relationship is therefore:

```text
192.168.86.35  --->  192.168.86.45:30080
Ubuntu               Windows / ingress-nginx
```

Useful Windows check:

```powershell
Get-NetFirewallRule -DisplayName "K8s Ingress HTTP from Ubuntu Laptop"
```

---

## 7. Test Kubernetes Ingress Before Apache

Before changing Apache, test the path directly from the Ubuntu laptop.

Because ingress-nginx routes based on the HTTP `Host` header, include the Superset hostname:

```bash
curl -v \
  -H 'Host: superset.aaravsharma.net' \
  http://192.168.86.45:30080/
```

If this succeeds, the following pieces are already proven:

```text
Ubuntu network
    -> Windows firewall
    -> Windows LAN interface
    -> NodePort 30080
    -> ingress-nginx
    -> Superset Ingress
    -> Superset Service
    -> Superset Pod
```

This is one of the most useful troubleshooting boundaries in the entire setup.

---

## 8. Ubuntu Apache2 Reverse Proxy

Apache2 on the Ubuntu ThinkPad is the front door for `superset.aaravsharma.net`.

The backend is **not** the Superset ClusterIP and is **not** Docker Desktop's internal node IP.

The backend is:

```text
http://192.168.86.45:30080/
```

A key requirement is preserving the original hostname because Kubernetes ingress uses that hostname to select the Superset route.

### Required Apache modules

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod ssl
```

### HTTP virtual host

Example `/etc/apache2/sites-available/superset.aaravsharma.net.conf`:

```apache
<VirtualHost *:80>
    ServerName superset.aaravsharma.net

    ProxyPreserveHost On
    ProxyPass        / http://192.168.86.45:30080/
    ProxyPassReverse / http://192.168.86.45:30080/
</VirtualHost>
```

Enable it:

```bash
sudo a2ensite superset.aaravsharma.net.conf
sudo apache2ctl configtest
sudo systemctl reload apache2
```

### Why `ProxyPreserveHost On` matters

Without it, Apache can send the backend host as something similar to:

```text
Host: 192.168.86.45:30080
```

But the Kubernetes Ingress rule expects:

```text
Host: superset.aaravsharma.net
```

With:

```apache
ProxyPreserveHost On
```

Apache forwards the browser's original hostname, allowing ingress-nginx to match the correct Ingress rule.

---

## 9. HTTPS / TLS

TLS terminates on the Ubuntu Apache server.

Conceptually:

```text
Browser
   |
   | HTTPS :443
   v
Ubuntu Apache2
   |
   | HTTP :30080
   v
Windows ingress-nginx
```

This means the internal Ubuntu-to-Windows hop does not need its own public certificate for this home-lab design.

The HTTPS virtual host follows the same proxy pattern:

```apache
<IfModule mod_ssl.c>
<VirtualHost *:443>
    ServerName superset.aaravsharma.net

    ProxyPreserveHost On
    ProxyPass        / http://192.168.86.45:30080/
    ProxyPassReverse / http://192.168.86.45:30080/

    SSLEngine on

    # Use the existing certificate paths configured for aaravsharma.net
    # / *.aaravsharma.net on this Apache host.
    SSLCertificateFile    <certificate-path>
    SSLCertificateKeyFile <private-key-path>
</VirtualHost>
</IfModule>
```

Do not blindly replace working certificate paths. Check the currently installed Apache SSL vhosts and Certbot configuration first.

Useful commands:

```bash
sudo apachectl -S
sudo apache2ctl configtest
sudo certbot certificates
```

---

## 10. DNS

`superset.aaravsharma.net` must resolve to the public IP that reaches the Ubuntu Apache2 host, just like the other externally exposed `aaravsharma.net` applications.

The public DNS flow is:

```text
superset.aaravsharma.net
          |
          v
Public IP / home entry point
          |
          v
Ubuntu Apache2
```

It should **not** point directly to:

```text
192.168.86.45
192.168.65.3
10.109.59.180
```

Those are private/internal addresses.

Useful DNS checks:

```bash
dig superset.aaravsharma.net
nslookup superset.aaravsharma.net
```

---

## 11. End-to-End Verification

### A. Verify Superset itself

On Windows / against the Docker Desktop cluster:

```bash
kubectl get pods -n superset
kubectl get svc -n superset
```

Optional isolation test:

```bash
kubectl port-forward svc/superset -n superset 8088:8088
```

Then test:

```text
http://localhost:8088
```

### B. Verify ingress-nginx

```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
kubectl get ingress -n superset
```

### C. Verify Windows NodePort from Ubuntu

```bash
curl -v \
  -H 'Host: superset.aaravsharma.net' \
  http://192.168.86.45:30080/
```

### D. Verify Apache locally while forcing hostname resolution

The final troubleshooting test used Apache locally while preserving the real hostname:

```bash
curl -vk \
  --resolve superset.aaravsharma.net:443:127.0.0.1 \
  https://superset.aaravsharma.net/
```

This forces `superset.aaravsharma.net` to `127.0.0.1` for that curl request while still sending the correct TLS SNI and HTTP Host header.

It is extremely useful because it tests:

```text
Apache HTTPS vhost
    -> certificate/TLS
    -> ProxyPreserveHost
    -> Windows :30080
    -> ingress-nginx host rule
    -> Superset
```

without depending on external DNS/NAT behavior.

### E. Final browser test

```text
https://superset.aaravsharma.net
```

---

## 12. Troubleshooting Order

When the site stops working, troubleshoot **inside-out** rather than changing multiple layers at once.

### Layer 1 — Superset

```bash
kubectl get pods -n superset
kubectl get svc -n superset
kubectl get jobs -n superset
kubectl logs -n superset <pod-name>
```

If necessary:

```bash
kubectl port-forward svc/superset -n superset 8088:8088
```

If localhost port-forward works, Superset itself is probably healthy.

### Layer 2 — Kubernetes Ingress

```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
kubectl get ingress -n superset
kubectl describe ingress -n superset superset
```

Confirm NodePort `30080` still exists.

### Layer 3 — Windows firewall / LAN connectivity

From Ubuntu:

```bash
curl -v \
  -H 'Host: superset.aaravsharma.net' \
  http://192.168.86.45:30080/
```

If this cannot connect, investigate:

```text
Windows system powered on?
Windows LAN IP still 192.168.86.45?
Docker Desktop running?
Kubernetes enabled/running?
ingress-nginx service still NodePort 30080?
Windows firewall rule still present?
Ubuntu IP still allowed by firewall rule?
```

### Layer 4 — Apache

```bash
sudo apachectl -S
sudo apache2ctl configtest
sudo systemctl status apache2
```

Then:

```bash
curl -vk \
  --resolve superset.aaravsharma.net:443:127.0.0.1 \
  https://superset.aaravsharma.net/
```

### Layer 5 — DNS / external access

```bash
dig superset.aaravsharma.net
```

Finally test from a browser or a device outside the local network.

---

## 13. Common Failure Patterns

### `404 Not Found` from nginx

Likely cause: ingress-nginx received the request, but the `Host` header did not match the Superset Ingress rule.

Check:

```apache
ProxyPreserveHost On
```

and verify:

```bash
kubectl get ingress -n superset
```

The hostname should be exactly:

```text
superset.aaravsharma.net
```

### Apache returns `502 Bad Gateway`

Apache cannot successfully reach its backend.

Test directly from Ubuntu:

```bash
curl -v \
  -H 'Host: superset.aaravsharma.net' \
  http://192.168.86.45:30080/
```

Then verify Windows networking, Docker Desktop, Kubernetes, ingress-nginx, and the firewall.

### Connection refused / timeout to `192.168.86.45:30080`

Check:

```text
1. Windows is online.
2. Its IP has not changed.
3. Docker Desktop is running.
4. Docker Desktop Kubernetes is running.
5. ingress-nginx controller is running.
6. Service still exposes NodePort 30080.
7. Windows firewall permits Ubuntu 192.168.86.35.
```

### Superset works via port-forward but not through ingress

That strongly narrows the issue to:

```text
ingress object
    -> ingress-nginx
    -> NodePort
    -> Windows firewall / network
```

rather than Superset itself.

### Direct ingress curl works but public hostname fails

That strongly narrows the issue to:

```text
Apache vhost
TLS certificate
DNS
public NAT / forwarding
```

---

## 14. Important Design Decisions to Remember

### Why use the Windows LAN IP instead of Docker Desktop's node IP?

Docker Desktop's Kubernetes networking is internal to the Windows/Docker Desktop environment. The stable network boundary visible to the Ubuntu laptop is the Windows machine's LAN interface.

Therefore:

```text
CORRECT:
Ubuntu -> 192.168.86.45:30080

NOT the intended path:
Ubuntu -> 192.168.65.3:30080
```

### Why use ingress instead of proxying directly to Superset?

It keeps this application consistent with the Kubernetes architecture used for the other home-lab services:

```text
external proxy -> Kubernetes ingress -> service -> pods
```

It also makes host-based routing available when more applications are added to the Windows Docker Desktop cluster.

### Why terminate TLS on Ubuntu?

Ubuntu Apache2 is already the centralized external entry point for the `aaravsharma.net` services and already handles certificates. This avoids duplicating public TLS management inside every Kubernetes environment.

### Why restrict the Windows firewall rule?

Only the Ubuntu reverse proxy needs to reach the Kubernetes ingress NodePort. Restricting the source to `192.168.86.35` avoids unnecessarily exposing port `30080` to every system on the LAN.

---

## 15. Fast Six-Month Recall

If everything has been forgotten, remember this one line:

```text
Browser -> Route53 -> Ubuntu Apache HTTPS -> Windows 192.168.86.45:30080 -> nginx Ingress -> Superset svc:8088 -> Superset pod
```

The three most important configuration details are:

```text
Windows ingress NodePort: 30080
Ubuntu Apache backend:    http://192.168.86.45:30080/
Ingress hostname:         superset.aaravsharma.net
```

and Apache must contain:

```apache
ProxyPreserveHost On
```

---

## 16. Quick Health Checklist

```text
[ ] Windows system is running and still has 192.168.86.45
[ ] Docker Desktop is running
[ ] Docker Desktop Kubernetes is running
[ ] Superset pods are Running/Ready
[ ] Superset service exists on port 8088
[ ] ingress-nginx controller is Running
[ ] ingress-nginx service exposes HTTP NodePort 30080
[ ] Superset Ingress host is superset.aaravsharma.net
[ ] Windows firewall allows 192.168.86.35 -> TCP/30080
[ ] Ubuntu can curl 192.168.86.45:30080 with the Superset Host header
[ ] Apache vhost uses ProxyPreserveHost On
[ ] Apache proxies to http://192.168.86.45:30080/
[ ] apache2ctl configtest returns Syntax OK
[ ] superset.aaravsharma.net DNS points to the public Ubuntu entry point
[ ] HTTPS certificate covers superset.aaravsharma.net
[ ] https://superset.aaravsharma.net loads successfully
```

---

## 17. Useful Command Cheat Sheet

### Kubernetes / Superset

```bash
kubectl get pods -n superset
kubectl get svc -n superset
kubectl get ingress -n superset
kubectl describe ingress -n superset superset
kubectl get jobs -n superset
```

### ingress-nginx

```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
kubectl get ingressclass
```

### Ubuntu -> Windows ingress test

```bash
curl -v \
  -H 'Host: superset.aaravsharma.net' \
  http://192.168.86.45:30080/
```

### Apache

```bash
sudo apachectl -S
sudo apache2ctl configtest
sudo systemctl status apache2
sudo systemctl reload apache2
```

### Local HTTPS end-to-end test

```bash
curl -vk \
  --resolve superset.aaravsharma.net:443:127.0.0.1 \
  https://superset.aaravsharma.net/
```

### DNS

```bash
dig superset.aaravsharma.net
```

---

## Final Working URL

```text
https://superset.aaravsharma.net
```

