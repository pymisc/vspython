# Argo CD + ingress-nginx on a Vagrant Kubernetes Cluster

This README documents the current homelab architecture used to expose **Argo CD** over the network through **Apache2 + ingress-nginx**, while keeping the Argo CD application itself internal to Kubernetes as a `ClusterIP` service.

It captures the setup as it exists today and leaves room for a future **MetalLB** enhancement.

---

## 1. Starting point

Argo CD was installed in the `argocd` namespace using the standard Argo CD manifest:

```bash
kubectl create namespace argocd

kubectl apply -n argocd --server-side --force-conflicts \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
```

Verify Argo CD:

```bash
kubectl get pods -n argocd
kubectl get svc -n argocd
```

The important service is:

```text
argocd-server
```

By default, Argo CD uses a Kubernetes `ClusterIP` service.

---

## 2. Verify Argo CD locally first

Before exposing Argo CD externally, verify that the service itself works.

One easy test is port-forwarding:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then browse to:

```text
https://localhost:8080
```

or:

```text
https://127.0.0.1:8080
```

A browser certificate warning is expected because Argo CD uses an internal/self-signed certificate.

The purpose of this test is simply to confirm:

```text
Argo CD pod/service works
        ↓
External networking can be added afterward
```

---

## 3. Temporary direct exposure with NodePort

Before installing an Ingress Controller, `argocd-server` was temporarily changed from:

```text
ClusterIP
```

to:

```text
NodePort
```

with fixed ports:

```text
HTTP  -> 32080
HTTPS -> 32443
```

This created a temporary path:

```text
Apache
   |
   | HTTPS :32443
   v
argocd-server NodePort
   |
   v
Argo CD pod
```

This was useful for proving that Apache could reach the Kubernetes cluster.

It was only an intermediate step and is **not** the final design.

---

## 4. Apache2 on Ubuntu as the external front door

The Ubuntu host runs Apache2 and handles the externally trusted TLS connection for:

```text
argocd.aaravsharma.net
```

The Let's Encrypt wildcard certificate is stored at:

```text
/etc/letsencrypt/live/aaravsharma.net/fullchain.pem
/etc/letsencrypt/live/aaravsharma.net/privkey.pem
```

Useful Apache modules include:

```bash
a2enmod proxy
a2enmod proxy_http
a2enmod ssl
```

The original Apache configuration proxied directly to the Argo CD NodePort:

```apache
<VirtualHost *:80>
    ServerName argocd.aaravsharma.net
    Redirect permanent / https://argocd.aaravsharma.net/
</VirtualHost>

<VirtualHost *:443>
    ServerName argocd.aaravsharma.net

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/aaravsharma.net/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/aaravsharma.net/privkey.pem

    ProxyPreserveHost On
    SSLProxyEngine On

    SSLProxyVerify none
    SSLProxyCheckPeerCN off
    SSLProxyCheckPeerName off

    ProxyPass        / https://192.168.56.10:32443/
    ProxyPassReverse / https://192.168.56.10:32443/
</VirtualHost>
```

This proved that external HTTPS access to Argo CD was working.

---

## 5. Why move to Ingress?

Without Ingress, each application could require its own externally exposed NodePort:

```text
Argo CD       -> NodePort
Grafana       -> NodePort
Dashboard     -> NodePort
Future app    -> NodePort
```

Instead, the goal was to use one Ingress Controller as the Kubernetes entry point:

```text
One externally reachable Ingress Controller
            |
            +--> Argo CD
            +--> Grafana
            +--> Dashboard
            +--> Future applications
```

Each application can then remain a normal internal Kubernetes service:

```text
ClusterIP
```

---

## 6. Confirm no Ingress Controller existed

The cluster was checked before installation:

```bash
kubectl get pods -A | grep -i ingress
kubectl get svc -A | grep -i ingress
kubectl get ingressclass
kubectl get ingress -A
```

No Ingress Controller or IngressClass existed at that point.

MetalLB was also not installed:

```bash
kubectl get pods -n metallb-system
```

---

## 7. Install ingress-nginx

Because this is a Vagrant/bare-metal-style Kubernetes cluster, the ingress-nginx bare-metal manifest was used:

```bash
kubectl apply -f \
https://raw.githubusercontent.com/kubernetes/ingress-nginx/controller-v1.13.2/deploy/static/provider/baremetal/deploy.yaml
```

Verify the deployment:

```bash
kubectl get all -n ingress-nginx
```

Important resources include:

```text
ingress-nginx-controller pod
ingress-nginx-controller service
ingress-nginx-controller-admission service
```

Verify the IngressClass:

```bash
kubectl get ingressclass
```

Expected:

```text
NAME    CONTROLLER
nginx   k8s.io/ingress-nginx
```

---

## 8. Ingress Controller Service type

The ingress-nginx **bare-metal** manifest creates the controller service as:

```text
TYPE = NodePort
```

This was automatic; the NodePort service type was not manually created.

Kubernetes initially assigned dynamic NodePorts. The service was then edited:

```bash
kubectl edit svc ingress-nginx-controller -n ingress-nginx
```

The NodePorts were changed to fixed values:

```text
HTTP  -> 30080
HTTPS -> 30443
```

Current controller service:

```text
service/ingress-nginx-controller

TYPE:
NodePort

PORTS:
80:30080/TCP
443:30443/TCP
```

This allows the Ingress Controller to be reached through a Kubernetes node IP such as:

```text
192.168.56.10:30443
```

---

## 9. Test the Ingress Controller itself

Before creating any application-specific Ingress rule, test the controller:

```bash
curl -kI https://192.168.56.10:30443
```

A response similar to this is expected:

```text
HTTP/2 404
```

That `404` is actually useful. It proves:

```text
Network path works
        ↓
Ingress Controller is listening
        ↓
No Host/Path rule matched
        ↓
Default 404 response
```

---

## 10. Create the Argo CD Ingress resource

Create an Ingress resource in the `argocd` namespace:

```yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd
  namespace: argocd
  annotations:
    nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
spec:
  ingressClassName: nginx
  rules:
    - host: argocd.aaravsharma.net
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: argocd-server
                port:
                  number: 443
```

Apply it:

```bash
kubectl apply -f argocd-ingress.yaml
```

Verify:

```bash
kubectl get ingress -n argocd
kubectl describe ingress argocd -n argocd
```

The important routing rule is:

```text
Host:
argocd.aaravsharma.net

Path:
/

Backend:
argocd-server:443
```

---

## 11. Why the HTTPS backend annotation is important

This annotation:

```yaml
nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
```

tells ingress-nginx to use HTTPS when connecting to Argo CD:

```text
Ingress Controller
       |
       | HTTPS
       v
argocd-server:443
```

Without this annotation, ingress-nginx would normally assume HTTP for the backend.

---

## 12. Test the Argo CD Ingress rule

A request to the controller without the correct hostname returns the default `404`:

```bash
curl -kI https://192.168.56.10:30443
```

Now test with the hostname that matches the Ingress rule:

```bash
curl -kI \
  -H "Host: argocd.aaravsharma.net" \
  https://192.168.56.10:30443
```

A successful result is:

```text
HTTP/2 200
```

This proves the full Kubernetes-side path:

```text
Ingress Controller reachable
        ↓
Host rule matched
        ↓
argocd-server selected
        ↓
Argo CD responded successfully
```

---

## 13. Modify Apache to point to the Ingress Controller

Once the Ingress route was working, Apache no longer needed to proxy directly to the Argo CD NodePort.

The Apache backend changed from:

```text
https://192.168.56.10:32443/
```

to:

```text
https://192.168.56.10:30443/
```

Final Apache configuration:

```apache
<VirtualHost *:80>
    ServerName argocd.aaravsharma.net
    Redirect permanent / https://argocd.aaravsharma.net/
</VirtualHost>

<VirtualHost *:443>
    ServerName argocd.aaravsharma.net

    SSLEngine on

    SSLCertificateFile /etc/letsencrypt/live/aaravsharma.net/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/aaravsharma.net/privkey.pem

    ProxyPreserveHost On
    SSLProxyEngine On

    SSLProxyVerify none
    SSLProxyCheckPeerCN off
    SSLProxyCheckPeerName off

    ProxyPass        / https://192.168.56.10:30443/
    ProxyPassReverse / https://192.168.56.10:30443/

    ErrorLog ${APACHE_LOG_DIR}/argocd-error.log
    CustomLog ${APACHE_LOG_DIR}/argocd-access.log combined
</VirtualHost>
```

### Why `ProxyPreserveHost On` matters

Apache preserves the original Host header:

```text
Host: argocd.aaravsharma.net
```

The Ingress Controller uses that hostname to select the correct Ingress rule.

Without the correct Host header, ingress-nginx would not know that the request belongs to the Argo CD route.

---

## 14. Validate Apache configuration

Check syntax:

```bash
apachectl configtest
```

Expected:

```text
Syntax OK
```

Reload Apache:

```bash
systemctl reload apache2
```

Then test from the Windows client:

```text
https://argocd.aaravsharma.net
```

Argo CD should load normally.

---

## 15. Convert Argo CD back to ClusterIP

Once the Ingress Controller was working, the Argo CD application itself no longer needed a NodePort.

`argocd-server` was converted back to:

```text
ClusterIP
```

Current service state:

```text
NAME            TYPE        CLUSTER-IP
argocd-server   ClusterIP   10.98.8.227
```

with service ports:

```text
80/TCP
443/TCP
```

This is the desired architecture.

---

## 16. Current final traffic path

```text
User
 |
 v
Windows laptop
 |
 v
Chrome browser
 |
 | https://argocd.aaravsharma.net
 |
 v
DNS
 |
 v
Ubuntu host
Apache2
 |
 | HTTPS :443
 | Trusted Let's Encrypt wildcard certificate
 |
 v
Apache reverse proxy
 |
 | HTTPS
 | 192.168.56.10:30443
 |
 v
Kubernetes NodePort Service
ingress-nginx-controller
 |
 v
ingress-nginx controller pod
 |
 | Host = argocd.aaravsharma.net
 |
 v
Ingress resource
name: argocd
namespace: argocd
 |
 | backend = argocd-server:443
 |
 v
argocd-server
ClusterIP: 10.98.8.227
 |
 | targetPort 8080
 |
 v
Argo CD server pod
10.244.2.49:8080
```

---

## 17. Current resource summary

### Ingress Controller

```bash
kubectl get all -n ingress-nginx
```

Important service:

```text
ingress-nginx-controller
Type: NodePort

80   -> 30080
443  -> 30443
```

### Argo CD Ingress

```bash
kubectl get ingress -n argocd
```

### Argo CD Service

```bash
kubectl get svc argocd-server -n argocd
```

Expected type:

```text
ClusterIP
```

---

## 18. Useful verification commands

### Ingress Controller

```bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
kubectl get ingressclass
```

### Argo CD Ingress

```bash
kubectl get ingress -n argocd
kubectl describe ingress argocd -n argocd
kubectl get ingress argocd -n argocd -o yaml
```

### Argo CD service and endpoints

```bash
kubectl get pods -n argocd
kubectl get svc argocd-server -n argocd
kubectl get endpoints argocd-server -n argocd
```

or with EndpointSlice:

```bash
kubectl get endpointslice -n argocd \
  -l kubernetes.io/service-name=argocd-server
```

### Test the Ingress rule directly

```bash
curl -kI \
  -H "Host: argocd.aaravsharma.net" \
  https://192.168.56.10:30443
```

### Apache

```bash
apachectl configtest
systemctl status apache2
```

---

## 19. Important design principle

Applications should normally remain internal Kubernetes services:

```text
ClusterIP
```

Only the Ingress Controller needs external reachability.

Instead of:

```text
Argo CD   -> NodePort
Grafana   -> NodePort
Dashboard -> NodePort
```

we now have:

```text
Ingress Controller -> one NodePort gateway

Argo CD   -> ClusterIP
Grafana   -> ClusterIP
Dashboard -> ClusterIP
```

This is the main architectural improvement.

---

## 20. TLS architecture

There are currently three HTTPS legs.

### 1. Chrome -> Apache

```text
Chrome
  |
  | HTTPS
  v
Apache
```

This uses the trusted Let's Encrypt wildcard certificate.

### 2. Apache -> ingress-nginx

```text
Apache
  |
  | HTTPS
  v
ingress-nginx :30443
```

Apache currently does not validate the Ingress Controller's internal certificate because of:

```apache
SSLProxyVerify none
SSLProxyCheckPeerCN off
SSLProxyCheckPeerName off
```

### 3. ingress-nginx -> Argo CD

```text
ingress-nginx
  |
  | HTTPS
  v
argocd-server:443
```

This happens because of:

```yaml
nginx.ingress.kubernetes.io/backend-protocol: "HTTPS"
```

So traffic is encrypted across all three legs, while certificate verification on the internal homelab paths is intentionally relaxed.

---

## 21. Understanding `Default backend: <default>`

Running:

```bash
kubectl describe ingress argocd -n argocd
```

may show:

```text
Default backend:  <default>
```

The Argo CD Ingress does **not** explicitly define a `spec.defaultBackend`.

The actual configured rule is:

```text
Host: argocd.aaravsharma.net
Path: /
Backend: argocd-server:443
```

If a request does not match a configured Host/Path rule, ingress-nginx falls back to its default handling and normally returns `404`.

This is why:

```bash
curl -kI https://192.168.56.10:30443
```

returns a `404`, while:

```bash
curl -kI \
  -H "Host: argocd.aaravsharma.net" \
  https://192.168.56.10:30443
```

returns a successful response.

---

## 22. Adding another application later

The same Ingress Controller can expose additional applications without creating a new NodePort for every application.

For example:

```text
grafana.aaravsharma.net
```

Grafana can remain a `ClusterIP` service.

Its Ingress rule would look conceptually like:

```yaml
rules:
  - host: grafana.aaravsharma.net
```

Apache can proxy that hostname to the same Ingress Controller endpoint:

```text
192.168.56.10:30443
```

The Ingress Controller then selects the correct application based on the hostname.

Example future routing:

```text
argocd.aaravsharma.net
        |
        +--> argocd-server

grafana.aaravsharma.net
        |
        +--> grafana

k8s-dashboard.aaravsharma.net
        |
        +--> Kubernetes Dashboard
```

---

## 23. Optional future enhancement: MetalLB

MetalLB is **not required** for the current architecture.

Current design:

```text
Apache
   |
   v
Ingress NodePort :30443
```

This works because the Ubuntu host can directly reach the Kubernetes node network.

A future MetalLB-based design could look like:

```text
Apache
   |
   v
MetalLB-assigned IP
   |
   v
ingress-nginx
Service type: LoadBalancer
```

At that point, the ingress-nginx service could change from:

```text
NodePort
```

to:

```text
LoadBalancer
```

MetalLB would provide a Kubernetes-managed IP reachable from outside the cluster.

This should be treated as a **future learning enhancement**, not as something required to fix the current setup.

---

## 24. Final architecture

```text
                HOME / CLIENT SIDE

                  User
                    |
                    v
             Windows Laptop
                    |
                    v
              Chrome Browser
                    |
                    | HTTPS
                    v
        argocd.aaravsharma.net
                    |
                    v

               UBUNTU HOST

                  Apache2
        Let's Encrypt TLS termination
                    |
                    | HTTPS
                    | :30443
                    v

            KUBERNETES CLUSTER

       ingress-nginx NodePort Service
          30080 / 30443
                    |
                    v
       ingress-nginx Controller Pod
                    |
                    | Host matching
                    v
          Ingress resource: argocd
                    |
                    | argocd-server:443
                    v
          argocd-server ClusterIP
             10.98.8.227
                    |
                    | targetPort 8080
                    v
           Argo CD Server Pod
           10.244.2.49:8080
```

---

## 25. Key takeaway

The final architecture has moved from **direct application exposure** to a proper **Ingress-based routing model**.

The Kubernetes application itself remains internal:

```text
argocd-server = ClusterIP
```

while ingress-nginx provides the cluster gateway:

```text
ingress-nginx-controller = NodePort
```

and Apache provides the externally trusted HTTPS front door:

```text
Windows / Chrome
      ↓
Apache2
      ↓
ingress-nginx
      ↓
Ingress rule
      ↓
ClusterIP service
      ↓
Argo CD pod
```

This same pattern can now be reused for additional applications in the cluster.
