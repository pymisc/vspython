# Headlamp on Kubernetes with NGINX Ingress, Apache Reverse Proxy, Route 53, and HTTPS

This document captures the end-to-end installation and configuration of
**Headlamp** on a kubeadm Kubernetes home-lab cluster running in Vagrant
on Ubuntu.

It also documents the troubleshooting encountered along the way,
including:

-   Why Kubernetes Dashboard was not used
-   Headlamp installation with Helm
-   Headlamp ServiceAccount authentication
-   JWT token generation and inspection
-   Kubernetes RBAC and the `headlamp-admin` ClusterRoleBinding
-   NGINX Ingress configuration
-   Apache2 reverse proxy configuration on the Ubuntu host
-   Route 53 DNS
-   Why HTTP-01 certificate validation is unsuitable when DNS resolves
    to a private RFC1918 address
-   Switching Certbot to Route 53 DNS-01 validation
-   Let's Encrypt certificate installation
-   Certificate CN, SAN, issuer, and expiration checks
-   Wildcard vs dedicated certificates
-   Useful troubleshooting commands

------------------------------------------------------------------------

## 1. Final Architecture

The completed request path is:

``` text
Browser
   |
   | HTTPS
   v
headlamp.aaravsharma.net
   |
   | DNS A record
   v
192.168.86.81
Ubuntu host
   |
   | Apache2 :443
   | TLS termination
   | Reverse proxy
   v
192.168.56.11:30080
   |
   | ingress-nginx NodePort
   v
NGINX Ingress Controller
   |
   | Host rule:
   | headlamp.aaravsharma.net
   v
Headlamp Service :80
   |
   v
Headlamp Pod
   |
   | Bearer JWT
   v
Kubernetes API Server
   |
   v
Kubernetes RBAC
```

Important addresses and ports in this lab:

``` text
Ubuntu LAN address:              192.168.86.81
Kubernetes/Vagrant address:      192.168.56.11
Ingress HTTP NodePort:           30080
Ingress HTTPS NodePort:          30443
Headlamp hostname:               headlamp.aaravsharma.net
Headlamp namespace:              headlamp
IngressClass:                    nginx
```

TLS terminates at Apache2 in this design. Traffic from Apache to the
Kubernetes ingress controller remains HTTP on the private lab network.

------------------------------------------------------------------------

## 2. Verify the Existing Ingress Environment

Before installing Headlamp, the existing ingress configuration was
checked:

``` bash
kubectl get ingressclass
kubectl get ingress -A
kubectl get svc -A | grep -i ingress
kubectl get pods -A | grep -i ingress
```

Relevant results:

``` text
IngressClass:
NAME    CONTROLLER
nginx   k8s.io/ingress-nginx

Ingress controller Service:
80:30080/TCP
443:30443/TCP
```

An existing Argo CD ingress already confirmed that the ingress
controller was functional.

------------------------------------------------------------------------

## 3. Why Headlamp Instead of Kubernetes Dashboard?

The original plan was to install Kubernetes Dashboard.

The old Dashboard Helm repository command failed:

``` bash
helm repo add kubernetes-dashboard https://kubernetes.github.io/dashboard/
```

with:

``` text
404 Not Found
```

Kubernetes Dashboard has been deprecated/archived, so Headlamp was
selected as the Kubernetes web UI instead.

------------------------------------------------------------------------

## 4. Install Headlamp with Helm

Add the Headlamp Helm repository:

``` bash
helm repo add headlamp https://kubernetes-sigs.github.io/headlamp/
helm repo update
```

Verify:

``` bash
helm search repo headlamp
```

Create the namespace:

``` bash
kubectl create namespace headlamp
```

Install Headlamp:

``` bash
helm install headlamp headlamp/headlamp \
  --namespace headlamp
```

Verify the pod:

``` bash
kubectl get pods -n headlamp
```

Example:

``` text
NAME                        READY   STATUS    RESTARTS
headlamp-74d7b5b595-7zkbz   1/1     Running   0
```

Verify the service:

``` bash
kubectl get svc -n headlamp
```

Example:

``` text
NAME       TYPE        CLUSTER-IP      EXTERNAL-IP   PORT(S)
headlamp   ClusterIP   10.105.78.133   <none>        80/TCP
```

The service remains a `ClusterIP`. It does not need to be directly
exposed outside Kubernetes because ingress handles access to it.

------------------------------------------------------------------------

## 5. Test Headlamp Before Configuring Ingress

A port-forward is useful for proving that Headlamp itself works before
introducing ingress or Apache:

``` bash
kubectl port-forward -n headlamp svc/headlamp 8080:80
```

Then browse to:

``` text
http://localhost:8080
```

If the Headlamp login screen appears, the application and Service are
functioning.

This isolates troubleshooting:

``` text
Browser
   |
localhost:8080
   |
kubectl port-forward
   |
Headlamp Service
   |
Headlamp Pod
```

------------------------------------------------------------------------

# 6. Headlamp Authentication, ServiceAccounts, JWT, and RBAC

Headlamp can authenticate to the Kubernetes API using a ServiceAccount
token.

The Helm installation created a ServiceAccount named:

``` text
headlamp
```

Check it with:

``` bash
kubectl get serviceaccount -n headlamp
```

The Helm chart also created a ClusterRoleBinding named:

``` text
headlamp-admin
```

This naming caused an important troubleshooting lesson.

## 6.1 Inspect the ClusterRoleBinding

Run:

``` bash
kubectl get clusterrolebinding headlamp-admin -o yaml
```

The relevant configuration was:

``` yaml
roleRef:
  apiGroup: rbac.authorization.k8s.io
  kind: ClusterRole
  name: cluster-admin

subjects:
- kind: ServiceAccount
  name: headlamp
  namespace: headlamp
```

Or inspect it with:

``` bash
kubectl describe clusterrolebinding headlamp-admin
```

The important distinction is:

``` text
ClusterRoleBinding name:  headlamp-admin
ServiceAccount name:      headlamp
Namespace:                headlamp
ClusterRole:              cluster-admin
```

The binding being called `headlamp-admin` does **not** mean that the
ServiceAccount is called `headlamp-admin`.

------------------------------------------------------------------------

## 6.2 RBAC Troubleshooting Lesson

Initially, an additional ServiceAccount was created:

``` bash
kubectl -n headlamp create serviceaccount headlamp-admin
```

Testing it returned:

``` bash
kubectl auth can-i '*' '*' \
  --as=system:serviceaccount:headlamp:headlamp-admin
```

Result:

``` text
no
```

The reason became clear after inspecting the ClusterRoleBinding: it
referenced the Helm-created `headlamp` ServiceAccount, not
`headlamp-admin`.

Testing the correct identity:

``` bash
kubectl auth can-i '*' '*' \
  --as=system:serviceaccount:headlamp:headlamp
```

should return:

``` text
yes
```

The unnecessary ServiceAccount was removed:

``` bash
kubectl delete serviceaccount headlamp-admin -n headlamp
```

This is an important Kubernetes concept:

``` text
ServiceAccount
      |
      | identity
      v
ClusterRoleBinding
      |
      | binds identity to permissions
      v
ClusterRole
```

A valid ServiceAccount does not automatically have permissions.

------------------------------------------------------------------------

# 7. Generate a Headlamp Login Token

Generate a token for the correct ServiceAccount:

``` bash
kubectl create token headlamp \
  --namespace headlamp
```

A longer requested lifetime can be specified:

``` bash
kubectl create token headlamp \
  --namespace headlamp \
  --duration=720h
```

`720h` is approximately 30 days.

The API server determines the lifetime it actually grants.

The lab was also tested with:

``` bash
TOKEN=$(kubectl create token headlamp \
  -n headlamp \
  --duration=8760h)
```

The resulting JWT showed:

``` text
8760 hours
365 days
```

so this cluster accepted a one-year requested lifetime.

For normal use, a 30-day token was selected.

> **Security:** Do not paste a ServiceAccount token into documentation,
> Git, screenshots, chat messages, or shell history unnecessarily. A
> `cluster-admin` token is a highly privileged credential.

------------------------------------------------------------------------

# 8. Is the Headlamp Token a JWT?

Yes. `kubectl create token` returns a **JSON Web Token (JWT)**.

A JWT has three dot-separated sections:

``` text
HEADER.PAYLOAD.SIGNATURE
```

Conceptually:

``` text
xxxxx.yyyyy.zzzzz
  |     |     |
Header Payload Signature
```

The payload can be inspected locally.

For example:

``` bash
TOKEN=$(kubectl create token headlamp \
  -n headlamp \
  --duration=720h)
```

Then:

``` bash
echo "$TOKEN" | cut -d. -f2 | \
  base64 -d 2>/dev/null | jq
```

Useful JWT claims include:

``` text
iss  = issuer
sub  = subject / Kubernetes identity
aud  = audience
iat  = issued-at time
exp  = expiration time
```

The subject is expected to resemble:

``` text
system:serviceaccount:headlamp:headlamp
```

This leads to an important distinction:

``` text
JWT
 |
 | Authentication
 | "Who are you?"
 v
system:serviceaccount:headlamp:headlamp
 |
 | RBAC authorization
 | "What are you allowed to do?"
 v
ClusterRoleBinding: headlamp-admin
 |
 v
ClusterRole: cluster-admin
```

The JWT establishes identity. The ClusterRoleBinding/RBAC configuration
grants permissions.

------------------------------------------------------------------------

## 8.1 Check the Actual JWT Lifetime

To inspect issue and expiration times:

``` bash
echo "$TOKEN" | cut -d. -f2 | \
  base64 -d 2>/dev/null | \
  jq '{
    issued: (.iat | todate),
    expires: (.exp | todate),
    hours: ((.exp - .iat) / 3600),
    days: ((.exp - .iat) / 86400)
  }'
```

Example from the one-year test:

``` json
{
  "issued": "2026-09-14T00:51:07Z",
  "expires": "2027-09-14T00:51:07Z",
  "hours": 8760,
  "days": 365
}
```

After testing, remove the token from the shell variable:

``` bash
unset TOKEN
```

------------------------------------------------------------------------

## 8.2 TokenRequest Token vs Kubernetes Secret

This command:

``` bash
kubectl create token headlamp -n headlamp
```

uses the Kubernetes TokenRequest API.

It does **not** normally create a Kubernetes Secret object containing
that JWT.

Therefore, if the token is lost, simply generate another:

``` bash
kubectl create token headlamp \
  -n headlamp \
  --duration=720h
```

This is different from a manually created long-lived ServiceAccount
token Secret.

In short:

``` text
kubectl create token
       |
       v
TokenRequest API
       |
       v
API server signs JWT
       |
       v
JWT returned to caller
```

Do not confuse:

``` text
Kubernetes Secret object
```

with:

``` text
ServiceAccount JWT
```

They are related concepts but are not the same thing.

------------------------------------------------------------------------

# 9. Create the Headlamp Ingress

Create:

``` text
headlamp-ingress.yaml
```

with:

``` yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: headlamp
  namespace: headlamp

spec:
  ingressClassName: nginx

  rules:
    - host: headlamp.aaravsharma.net
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: headlamp
                port:
                  number: 80
```

Apply it:

``` bash
kubectl apply -f headlamp-ingress.yaml
```

Verify:

``` bash
kubectl get ingress -n headlamp
```

Actual result:

``` text
NAME       CLASS   HOSTS                       ADDRESS         PORTS
headlamp   nginx   headlamp.aaravsharma.net    192.168.56.11   80
```

------------------------------------------------------------------------

# 10. Test Kubernetes Ingress Directly

Before configuring Apache, test ingress-nginx directly from the Ubuntu
host:

``` bash
curl -I \
  -H 'Host: headlamp.aaravsharma.net' \
  http://192.168.56.11:30080
```

Actual result:

``` text
HTTP/1.1 200 OK
Content-Type: text/html; charset=utf-8
```

This proved that all of the following were working:

``` text
Ubuntu host
    |
    | HTTP :30080
    v
ingress-nginx
    |
    | Host: headlamp.aaravsharma.net
    v
Headlamp Ingress
    |
    v
Headlamp Service :80
    |
    v
Headlamp Pod
```

This test is extremely useful because it isolates Kubernetes from the
outer Apache/DNS/TLS configuration.

------------------------------------------------------------------------

# 11. Configure Apache2 as the Reverse Proxy

The Ubuntu host uses **Apache2**, not NGINX, as its external reverse
proxy.

Create:

``` bash
sudo vi /etc/apache2/sites-available/headlamp.aaravsharma.net.conf
```

Initial HTTP configuration:

``` apache
<VirtualHost *:80>
    ServerName headlamp.aaravsharma.net

    ProxyPreserveHost On

    ProxyPass / http://192.168.56.11:30080/
    ProxyPassReverse / http://192.168.56.11:30080/

    ErrorLog ${APACHE_LOG_DIR}/headlamp_error.log
    CustomLog ${APACHE_LOG_DIR}/headlamp_access.log combined
</VirtualHost>
```

Enable the required Apache modules:

``` bash
sudo a2enmod proxy
sudo a2enmod proxy_http
```

Enable the site:

``` bash
sudo a2ensite headlamp.aaravsharma.net.conf
```

Validate:

``` bash
sudo apache2ctl configtest
```

Expected:

``` text
Syntax OK
```

Reload Apache:

``` bash
sudo systemctl reload apache2
```

Test through Apache:

``` bash
curl -I \
  -H 'Host: headlamp.aaravsharma.net' \
  http://127.0.0.1
```

A `200 OK` confirms:

``` text
Apache2
   |
   v
ingress-nginx
   |
   v
Headlamp
```

------------------------------------------------------------------------

# 12. Why `ProxyPreserveHost On` Matters

The Kubernetes Ingress routes by hostname:

``` yaml
host: headlamp.aaravsharma.net
```

Apache therefore needs to preserve the original HTTP `Host` header:

``` apache
ProxyPreserveHost On
```

This allows ingress-nginx to receive:

``` text
Host: headlamp.aaravsharma.net
```

and select the correct Ingress rule.

Without the expected host header, the request may hit the ingress
controller's default backend instead.

------------------------------------------------------------------------

# 13. Route 53 DNS

An A record was created for:

``` text
headlamp.aaravsharma.net
```

which resolves to the Ubuntu host's private LAN address:

``` text
192.168.86.81
```

Verification:

``` bash
dig +short headlamp.aaravsharma.net
```

Result:

``` text
192.168.86.81
```

Compare with another lab service:

``` bash
dig +short argocd.aaravsharma.net
```

Result:

``` text
192.168.86.81
```

Public recursive resolvers were also checked:

``` bash
dig @8.8.8.8 headlamp.aaravsharma.net A +short
dig @1.1.1.1 headlamp.aaravsharma.net A +short
```

Both returned:

``` text
192.168.86.81
```

The authoritative Route 53 nameservers were found with:

``` bash
dig aaravsharma.net NS +short
```

and queried directly:

``` bash
dig @<route53-authoritative-nameserver> \
  headlamp.aaravsharma.net A +short
```

This confirmed that Route 53 itself contained the expected record.

------------------------------------------------------------------------

# 14. Important: Public DNS Can Contain a Private IP

`192.168.86.81` belongs to the RFC1918 private address range.

It is not routable from the public Internet.

This configuration can still be useful:

``` text
Public DNS:
headlamp.aaravsharma.net
        |
        v
192.168.86.81
        |
        v
reachable from home LAN
```

However, an external Certificate Authority cannot connect to that
private IP from the Internet.

This distinction became important during certificate issuance.

------------------------------------------------------------------------

# 15. Initial Certbot Attempt --- HTTP-01

The first certificate attempt used Certbot's Apache authenticator:

``` bash
certbot --apache \
  -d headlamp.aaravsharma.net
```

It failed with:

``` text
Certbot failed to authenticate some domains

Identifier: headlamp.aaravsharma.net
Type: dns
Detail: no valid A records found for headlamp.aaravsharma.net;
        no valid AAAA records found for headlamp.aaravsharma.net
```

At that moment, Let's Encrypt could not see a usable DNS record for the
HTTP validation attempt.

After DNS became visible, the hostname resolved to:

``` text
192.168.86.81
```

But this introduced the more fundamental issue: **192.168.86.81 is
private and cannot be reached by Let's Encrypt's HTTP-01 validators over
the public Internet.**

HTTP-01 conceptually requires:

``` text
Let's Encrypt
      |
      | public Internet HTTP :80
      v
headlamp.aaravsharma.net
      |
      v
Apache
      |
      v
/.well-known/acme-challenge/...
```

That path cannot work when the hostname resolves only to an RFC1918
private address.

Therefore, the validation method was changed from **HTTP-01** to
**DNS-01**.

------------------------------------------------------------------------

# 16. DNS-01: The Correct Certificate Method for This Lab

DNS-01 proves domain ownership through a DNS TXT record instead of
requiring the Certificate Authority to connect to the web server.

Conceptually:

``` text
HTTP-01
Let's Encrypt
      |
      v
Web server :80
```

versus:

``` text
DNS-01
Let's Encrypt
      |
      v
DNS TXT record
_acme-challenge.headlamp.aaravsharma.net
```

This makes DNS-01 ideal when the service itself uses a private IP.

------------------------------------------------------------------------

# 17. Verify the Certbot Route 53 Plugin

Check:

``` bash
certbot plugins | grep -A3 route53
```

Result:

``` text
* dns-route53
Description: Obtain certificates using a DNS TXT record
(if you are using AWS Route53 for DNS).
Interfaces: Authenticator, Plugin
```

The Route 53 plugin can create the temporary DNS challenge record needed
by Let's Encrypt.

------------------------------------------------------------------------

# 18. Issue the Certificate Using Route 53 DNS-01

Instead of:

``` bash
certbot --apache -d headlamp.aaravsharma.net
```

use:

``` bash
certbot certonly \
  --dns-route53 \
  -d headlamp.aaravsharma.net
```

This succeeded:

``` text
Successfully received certificate.

Certificate is saved at:
  /etc/letsencrypt/live/headlamp.aaravsharma.net/fullchain.pem

Key is saved at:
  /etc/letsencrypt/live/headlamp.aaravsharma.net/privkey.pem
```

Certificate expiration:

``` text
2026-12-13
```

Certbot also configured scheduled renewal.

During DNS-01 validation, Certbot temporarily manages a TXT record
conceptually similar to:

``` text
_acme-challenge.headlamp.aaravsharma.net
```

Let's Encrypt checks that DNS record rather than connecting to
`192.168.86.81`.

------------------------------------------------------------------------

# 19. Configure Apache HTTPS

After obtaining the certificate, Apache can use:

``` text
/etc/letsencrypt/live/headlamp.aaravsharma.net/fullchain.pem
/etc/letsencrypt/live/headlamp.aaravsharma.net/privkey.pem
```

An SSL virtual host is conceptually:

``` apache
<VirtualHost *:443>
    ServerName headlamp.aaravsharma.net

    SSLEngine on
    SSLCertificateFile /etc/letsencrypt/live/headlamp.aaravsharma.net/fullchain.pem
    SSLCertificateKeyFile /etc/letsencrypt/live/headlamp.aaravsharma.net/privkey.pem

    ProxyPreserveHost On

    ProxyPass / http://192.168.56.11:30080/
    ProxyPassReverse / http://192.168.56.11:30080/

    ErrorLog ${APACHE_LOG_DIR}/headlamp_ssl_error.log
    CustomLog ${APACHE_LOG_DIR}/headlamp_ssl_access.log combined
</VirtualHost>
```

Enable SSL if necessary:

``` bash
sudo a2enmod ssl
```

Validate:

``` bash
sudo apache2ctl configtest
```

Expected:

``` text
Syntax OK
```

Reload:

``` bash
sudo systemctl reload apache2
```

The HTTP virtual host can optionally redirect all traffic to HTTPS:

``` apache
<VirtualHost *:80>
    ServerName headlamp.aaravsharma.net
    Redirect permanent / https://headlamp.aaravsharma.net/
</VirtualHost>
```

------------------------------------------------------------------------

# 20. Verify the Headlamp Certificate

Check the certificate presented by Apache:

``` bash
openssl s_client \
  -connect headlamp.aaravsharma.net:443 \
  -servername headlamp.aaravsharma.net \
  </dev/null 2>/dev/null |
openssl x509 -noout -subject -issuer -dates
```

Actual result:

``` text
subject=CN = headlamp.aaravsharma.net
issuer=C = US, O = Let's Encrypt, CN = YE2
notBefore=Sep 14 00:59:24 2026 GMT
notAfter=Dec 13 00:59:23 2026 GMT
```

This confirms:

``` text
Certificate subject: headlamp.aaravsharma.net
CA:                  Let's Encrypt
Issuing CA:          YE2
Valid from:          Sep 14, 2026
Valid until:         Dec 13, 2026
```

------------------------------------------------------------------------

# 21. Check Subject Alternative Names (SAN)

Modern TLS hostname validation relies on the certificate's **Subject
Alternative Name (SAN)** extension.

To inspect SANs:

``` bash
openssl s_client \
  -connect headlamp.aaravsharma.net:443 \
  -servername headlamp.aaravsharma.net \
  </dev/null 2>/dev/null |
openssl x509 -noout -text |
grep -A2 "Subject Alternative Name"
```

For another lab service, Jenkins, this showed:

``` text
X509v3 Subject Alternative Name:
    DNS:*.aaravsharma.net, DNS:aaravsharma.net
```

That confirms Jenkins is using a wildcard certificate.

------------------------------------------------------------------------

# 22. CN vs SAN

Two certificate fields are useful to understand:

``` text
CN   = Common Name
SAN  = Subject Alternative Name
```

Example dedicated Headlamp certificate:

``` text
CN = headlamp.aaravsharma.net
```

Example wildcard certificate SANs:

``` text
DNS:*.aaravsharma.net
DNS:aaravsharma.net
```

For hostname validation, the SAN extension is the important field used
by modern clients.

Therefore, checking only:

``` bash
openssl x509 -noout -subject
```

does not always tell you every hostname covered by a certificate.

Check SAN as well.

------------------------------------------------------------------------

# 23. Wildcard Certificate Behavior

A wildcard such as:

``` text
*.aaravsharma.net
```

matches:

``` text
jenkins.aaravsharma.net
argocd.aaravsharma.net
headlamp.aaravsharma.net
site1.aaravsharma.net
```

It does **not** match a deeper hostname such as:

``` text
foo.bar.aaravsharma.net
```

because `*.aaravsharma.net` covers one hostname label.

Wildcard certificates require DNS-based ACME validation.

------------------------------------------------------------------------

# 24. Dedicated vs Wildcard Certificate

This lab currently demonstrates both approaches.

## Dedicated certificate

Headlamp:

``` text
headlamp.aaravsharma.net
```

Advantages:

-   Smaller certificate scope
-   Clear service-specific certificate
-   Independent renewal/lifecycle

## Wildcard certificate

Example SANs:

``` text
*.aaravsharma.net
aaravsharma.net
```

Advantages:

-   One certificate can serve many first-level subdomains
-   Convenient when adding many home-lab services

Both approaches are valid.

------------------------------------------------------------------------

# 25. Useful OpenSSL Certificate Commands

## Subject, issuer, and dates

``` bash
openssl s_client \
  -connect headlamp.aaravsharma.net:443 \
  -servername headlamp.aaravsharma.net \
  </dev/null 2>/dev/null |
openssl x509 -noout -subject -issuer -dates
```

## Expiration only

``` bash
echo | openssl s_client \
  -connect headlamp.aaravsharma.net:443 \
  -servername headlamp.aaravsharma.net \
  2>/dev/null |
openssl x509 -noout -enddate
```

## SANs

``` bash
openssl s_client \
  -connect headlamp.aaravsharma.net:443 \
  -servername headlamp.aaravsharma.net \
  </dev/null 2>/dev/null |
openssl x509 -noout -text |
grep -A2 "Subject Alternative Name"
```

## Full certificate details

``` bash
openssl s_client \
  -connect headlamp.aaravsharma.net:443 \
  -servername headlamp.aaravsharma.net \
  </dev/null 2>/dev/null |
openssl x509 -noout -text
```

------------------------------------------------------------------------

# 26. Useful Certbot Commands

List certificates:

``` bash
certbot certificates
```

List available plugins:

``` bash
certbot plugins
```

Check specifically for Route 53:

``` bash
certbot plugins | grep -A3 route53
```

Request a dedicated DNS-01 certificate:

``` bash
certbot certonly \
  --dns-route53 \
  -d headlamp.aaravsharma.net
```

Test renewal:

``` bash
certbot renew --dry-run
```

Normal renewal:

``` bash
certbot renew
```

------------------------------------------------------------------------

# 27. Useful Headlamp/Kubernetes Troubleshooting Commands

Check Headlamp:

``` bash
kubectl get pods -n headlamp
kubectl get svc -n headlamp
kubectl get ingress -n headlamp
```

Check ServiceAccounts:

``` bash
kubectl get serviceaccount -n headlamp
```

Inspect the admin binding:

``` bash
kubectl describe clusterrolebinding headlamp-admin
```

or:

``` bash
kubectl get clusterrolebinding headlamp-admin -o yaml
```

Check permissions:

``` bash
kubectl auth can-i '*' '*' \
  --as=system:serviceaccount:headlamp:headlamp
```

Generate a 30-day login JWT:

``` bash
kubectl create token headlamp \
  -n headlamp \
  --duration=720h
```

Test ingress directly:

``` bash
curl -I \
  -H 'Host: headlamp.aaravsharma.net' \
  http://192.168.56.11:30080
```

Check ingress controller:

``` bash
kubectl get pods -n ingress-nginx
kubectl get svc -n ingress-nginx
kubectl get ingressclass
```

------------------------------------------------------------------------

# 28. Useful Apache Troubleshooting Commands

Check configuration:

``` bash
apache2ctl configtest
```

Show virtual-host mapping:

``` bash
apache2ctl -S
```

Check service:

``` bash
systemctl status apache2
```

Reload:

``` bash
systemctl reload apache2
```

Check logs:

``` bash
tail -f /var/log/apache2/headlamp_access.log
```

``` bash
tail -f /var/log/apache2/headlamp_error.log
```

------------------------------------------------------------------------

# 29. Layer-by-Layer Troubleshooting Strategy

When Headlamp is unavailable, troubleshoot from the inside out.

### Layer 1 --- Pod

``` bash
kubectl get pods -n headlamp
```

### Layer 2 --- Service

``` bash
kubectl get svc -n headlamp
```

### Layer 3 --- Port-forward

``` bash
kubectl port-forward -n headlamp svc/headlamp 8080:80
```

Test:

``` text
http://localhost:8080
```

### Layer 4 --- Ingress

``` bash
curl -I \
  -H 'Host: headlamp.aaravsharma.net' \
  http://192.168.56.11:30080
```

### Layer 5 --- Apache

``` bash
curl -I \
  -H 'Host: headlamp.aaravsharma.net' \
  http://127.0.0.1
```

### Layer 6 --- DNS

``` bash
dig +short headlamp.aaravsharma.net
dig @8.8.8.8 headlamp.aaravsharma.net A +short
dig @1.1.1.1 headlamp.aaravsharma.net A +short
```

### Layer 7 --- HTTPS

``` bash
curl -I https://headlamp.aaravsharma.net
```

### Layer 8 --- Certificate

``` bash
openssl s_client \
  -connect headlamp.aaravsharma.net:443 \
  -servername headlamp.aaravsharma.net \
  </dev/null 2>/dev/null |
openssl x509 -noout -subject -issuer -dates
```

This approach makes it much easier to identify exactly which layer is
failing.

------------------------------------------------------------------------

# 30. Key Lessons Learned

This exercise covered considerably more than simply installing a
Kubernetes dashboard.

### Kubernetes

``` text
Helm
Namespaces
Pods
ClusterIP Services
ServiceAccounts
TokenRequest API
JWT authentication
RBAC authorization
ClusterRoles
ClusterRoleBindings
Ingress
IngressClass
NGINX Ingress Controller
NodePort
```

### Linux / Networking

``` text
Apache2
Reverse proxy
Host headers
Private RFC1918 addresses
DNS resolution
TLS termination
```

### AWS / PKI

``` text
Route 53
A records
Authoritative DNS
ACME
HTTP-01
DNS-01
Let's Encrypt
Certbot
Certificate CN
Certificate SAN
Wildcard certificates
Certificate expiration
Automatic renewal
```

Perhaps the most useful conceptual flow is:

``` text
Browser
   |
   | HTTPS
   v
Apache2
   |
   | reverse proxy
   v
NGINX Ingress
   |
   | host-based routing
   v
Headlamp
   |
   | ServiceAccount JWT
   v
Kubernetes Authentication
   |
   v
RBAC Authorization
```

And the most useful certificate lesson is:

``` text
Private IP service
        |
        X
HTTP-01 from Internet
        |
        v
Use DNS-01 instead
        |
        v
Route 53 TXT challenge
        |
        v
Let's Encrypt certificate
```

------------------------------------------------------------------------

# 31. Final Status

``` text
Headlamp Helm installation       WORKING
Headlamp Pod                     RUNNING
Headlamp ClusterIP Service       WORKING
ServiceAccount JWT login         WORKING
RBAC / cluster-admin             WORKING
NGINX Ingress                    WORKING
Apache2 reverse proxy            WORKING
Route 53 DNS                     WORKING
Let's Encrypt DNS-01             WORKING
HTTPS                            WORKING
Certificate verification         WORKING
```

Final URL:

``` text
https://headlamp.aaravsharma.net
```

------------------------------------------------------------------------

## Security Note

The Headlamp ServiceAccount in this lab is bound to `cluster-admin`.
This is convenient for learning but grants extremely broad Kubernetes
permissions.

For a production environment:

-   Avoid exposing a cluster-admin dashboard unnecessarily.
-   Prefer least-privilege RBAC.
-   Use short-lived credentials where practical.
-   Protect all dashboard traffic with HTTPS.
-   Consider additional authentication controls in front of
    administrative interfaces.
-   Never commit ServiceAccount JWTs or private certificate keys to Git.

For this isolated learning environment, the current configuration is
useful for exploring Kubernetes resources and understanding
authentication, authorization, ingress, reverse proxies, DNS, and TLS.
