# SSL with Argo CD on Kubernetes — Apache Reverse Proxy

This document describes how to expose an **Argo CD instance running inside a Kubernetes cluster on Vagrant VMs** to the home network using an **Apache reverse proxy** running on the Ubuntu host.

The final URL used in this setup is:

```text
https://argocd.aaravsharma.net
```

---

## 1. Architecture

The environment consists of:

- Ubuntu laptop acting as the physical host
- Apache2 running on the Ubuntu host
- Kubernetes running inside Vagrant VMs
- Argo CD running inside Kubernetes
- Apache acting as the reverse proxy
- Let's Encrypt wildcard SSL certificate
- `aaravsharma.net` DNS domain

Final traffic flow:

```text
Home Network Client
        |
        | HTTPS
        | https://argocd.aaravsharma.net
        v
+----------------------------------+
| Ubuntu Host                      |
|                                  |
| Apache2 Reverse Proxy            |
| Let's Encrypt SSL Certificate    |
+----------------+-----------------+
                 |
                 | HTTPS
                 | 192.168.56.10:32443
                 v
+----------------------------------+
| Vagrant Kubernetes Controller    |
| 192.168.56.10                    |
|                                  |
| NodePort :32443                  |
|        |                         |
|        v                         |
| argocd-server Service            |
|        |                         |
|        v                         |
| Argo CD Server Pod               |
+----------------------------------+
```

---

## 2. Verify Argo CD

Check the Argo CD pods:

```bash
kubectl get pods -n argocd
```

Example:

```text
NAME                                                READY   STATUS
argocd-application-controller-0                     1/1     Running
argocd-applicationset-controller-xxxxxxxxxx-xxxxx   1/1     Running
argocd-dex-server-xxxxxxxxxx-xxxxx                  1/1     Running
argocd-notifications-controller-xxxxxxxxxx-xxxxx    1/1     Running
argocd-redis-xxxxxxxxxx-xxxxx                       1/1     Running
argocd-repo-server-xxxxxxxxxx-xxxxx                 1/1     Running
argocd-server-xxxxxxxxxx-xxxxx                      1/1     Running
```

Check the services:

```bash
kubectl get svc -n argocd
```

Initially, `argocd-server` was configured as:

```text
TYPE: ClusterIP
PORTS: 80/TCP, 443/TCP
```

A `ClusterIP` service is intended for access from inside the Kubernetes cluster.

---

## 3. Check Kubernetes Node Addresses

Run:

```bash
kubectl get nodes -o wide
```

The Vagrant Kubernetes cluster used in this setup:

```text
NAME         INTERNAL-IP
controller   192.168.56.10
worker1      192.168.56.11
worker2      192.168.56.12
```

The Ubuntu host can communicate directly with these Vagrant private-network addresses.

The controller address used by the Apache reverse proxy is:

```text
192.168.56.10
```

---

## 4. Expose Argo CD Using NodePort

The `argocd-server` service originally used:

```yaml
type: ClusterIP
```

Edit the service:

```bash
kubectl edit svc argocd-server -n argocd
```

Change the service to `NodePort` and assign fixed NodePort values.

Example:

```yaml
spec:
  ports:
  - name: http
    port: 80
    protocol: TCP
    targetPort: 8080
    nodePort: 32080

  - name: https
    port: 443
    protocol: TCP
    targetPort: 8080
    nodePort: 32443

  type: NodePort
```

Verify:

```bash
kubectl get svc argocd-server -n argocd
```

Expected result:

```text
NAME            TYPE       CLUSTER-IP   EXTERNAL-IP   PORT(S)
argocd-server   NodePort   10.x.x.x     <none>        80:32080/TCP,443:32443/TCP
```

---

## 5. Test NodePort from Ubuntu Host

Before configuring Apache, verify that the Ubuntu host can reach Argo CD directly:

```bash
curl -kI https://192.168.56.10:32443
```

The `-k` option is required because Argo CD uses an internal TLS certificate that is not trusted by the Ubuntu host.

Successful communication confirms this portion of the path:

```text
Ubuntu Host
     |
     v
192.168.56.10:32443
     |
     v
Kubernetes NodePort
     |
     v
argocd-server
```

NodePort should normally also be reachable through other healthy Kubernetes nodes:

```bash
curl -kI https://192.168.56.11:32443
curl -kI https://192.168.56.12:32443
```

However, this setup uses the controller's stable Vagrant address:

```text
192.168.56.10
```

---

## 6. Enable Required Apache Modules

Apache requires the SSL and reverse-proxy modules.

Enable them if they are not already enabled:

```bash
sudo a2enmod proxy
sudo a2enmod proxy_http
sudo a2enmod ssl
```

Verify:

```bash
apache2ctl -M | grep -E 'ssl|proxy|proxy_http'
```

Expected modules include:

```text
ssl_module
proxy_module
proxy_http_module
```

---

## 7. Initial Apache HTTP Reverse Proxy

An initial HTTP VirtualHost was created to verify Apache-to-Argo-CD connectivity.

File:

```text
/etc/apache2/sites-available/argocd.aaravsharma.net.conf
```

Initial configuration:

```apache
<VirtualHost *:80>
    ServerName argocd.aaravsharma.net

    ProxyPreserveHost On
    SSLProxyEngine On

    SSLProxyVerify none
    SSLProxyCheckPeerCN off
    SSLProxyCheckPeerName off

    ProxyPass        / https://192.168.56.10:32443/
    ProxyPassReverse / https://192.168.56.10:32443/

    ErrorLog ${APACHE_LOG_DIR}/argocd-error.log
    CustomLog ${APACHE_LOG_DIR}/argocd-access.log combined
</VirtualHost>
```

Enable the site:

```bash
sudo a2ensite argocd.aaravsharma.net.conf
```

Check Apache configuration:

```bash
sudo apachectl configtest
```

Expected:

```text
Syntax OK
```

Reload Apache:

```bash
sudo systemctl reload apache2
```

At this point the Argo CD login page became accessible at:

```text
http://argocd.aaravsharma.net
```

---

## 8. Argo CD Default Username and Initial Password

For a standard Argo CD installation, the initial administrator username is:

```text
admin
```

The initial password can be retrieved from the Kubernetes secret:

```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d
```

> **Security Note:** Do not save the resulting password in documentation, shell scripts, Git repositories, screenshots, or other public locations.

A direct Argo CD test can also be performed with port forwarding:

```bash
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

Then browse to:

```text
https://localhost:8080
```

Login using:

```text
Username: admin
Password: <initial-admin-password>
```

This test confirmed that the Argo CD credentials themselves were valid.

---

## 9. Troubleshooting — Login Worked Through Port Forward but Failed Through Apache

An interesting authentication issue occurred during the initial HTTP reverse-proxy test.

The login worked through:

```text
https://localhost:8080
```

but appeared not to work through:

```text
http://argocd.aaravsharma.net
```

Apache access logs were examined:

```bash
tail -f /var/log/apache2/argocd-access.log
```

The important pattern was:

```text
POST /api/v1/session       200
GET  /api/v1/applications  401
GET  /api/v1/clusters      401
```

This was a very useful clue.

### What Was Happening?

The password was actually being accepted.

The initial architecture was:

```text
Browser
   |
   | HTTP
   v
Apache
   |
   | HTTPS
   v
Argo CD
```

The login request succeeded:

```text
POST /api/v1/session
        |
        v
      200 OK
```

But subsequent authenticated API calls returned:

```text
401 Unauthorized
```

The authentication session needed to operate correctly over HTTPS.

Rather than weakening the Argo CD security configuration to make authentication work over plain HTTP, the correct solution for this setup was to enable HTTPS on the Apache frontend.

---

## 10. Verify Existing Wildcard Certificate

An existing Let's Encrypt wildcard certificate was already available:

```text
/etc/letsencrypt/live/aaravsharma.net/
```

The certificate can be inspected using:

```bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -ext subjectAltName
```

For a wildcard certificate, the SANs should include entries similar to:

```text
DNS:aaravsharma.net
DNS:*.aaravsharma.net
```

The wildcard:

```text
*.aaravsharma.net
```

covers:

```text
argocd.aaravsharma.net
jenkins.aaravsharma.net
site1.aaravsharma.net
site2.aaravsharma.net
```

Therefore, there is no need to issue a separate certificate specifically for Argo CD.

---

## 11. Final Apache HTTPS Configuration

The final Apache configuration terminates public/client-facing TLS on Apache and proxies the request over HTTPS to Argo CD.

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

    ErrorLog ${APACHE_LOG_DIR}/argocd-error.log
    CustomLog ${APACHE_LOG_DIR}/argocd-access.log combined
</VirtualHost>
```

The HTTP VirtualHost now performs only one job:

```text
HTTP → HTTPS redirect
```

The HTTPS VirtualHost performs the actual reverse proxy.

---

## 12. Validate and Reload Apache

Always validate the configuration before reloading Apache:

```bash
sudo apachectl configtest
```

Expected:

```text
Syntax OK
```

Reload Apache:

```bash
sudo systemctl reload apache2
```

A restart is normally unnecessary for VirtualHost configuration changes.

Check status if required:

```bash
systemctl status apache2
```

---

## 13. Test HTTPS

From a client:

```bash
curl -I https://argocd.aaravsharma.net
```

Then browse to:

```text
https://argocd.aaravsharma.net
```

The final login flow is:

```text
Browser
   |
   | HTTPS :443
   v
Apache2
   |
   | HTTPS :32443
   v
Kubernetes Node
   |
   v
argocd-server
```

The Argo CD login should now work normally.

---

## 14. DNS / Home Network Consideration

The DNS name:

```text
argocd.aaravsharma.net
```

must resolve from home-network clients to the **Ubuntu host's LAN IP**.

Do not point home clients directly at:

```text
192.168.56.10
```

because that address belongs to the Vagrant private network.

The intended path is:

```text
Home Client
     |
     | argocd.aaravsharma.net
     v
Ubuntu Host LAN IP
     |
     | Apache
     v
192.168.56.10:32443
     |
     v
Argo CD
```

---

## 15. Why Only `argocd-server` Is Exposed

Argo CD consists of several services, including:

```text
argocd-server
argocd-repo-server
argocd-redis
argocd-dex-server
argocd-application-controller
argocd-applicationset-controller
```

Only:

```text
argocd-server
```

needs to be exposed for the Web UI.

Internal components such as Redis, repo-server, controllers, and Dex should remain Kubernetes `ClusterIP` services unless there is a specific reason to expose them.

This minimizes unnecessary exposure.

---

## 16. Useful Troubleshooting Commands

### Check Argo CD pods

```bash
kubectl get pods -n argocd
```

### Check Argo CD services

```bash
kubectl get svc -n argocd
```

### Inspect `argocd-server`

```bash
kubectl get svc argocd-server -n argocd -o yaml
```

### Check Kubernetes nodes

```bash
kubectl get nodes -o wide
```

### Test NodePort directly

```bash
curl -kI https://192.168.56.10:32443
```

### Test external HTTPS endpoint

```bash
curl -I https://argocd.aaravsharma.net
```

### Validate Apache

```bash
sudo apachectl configtest
```

### Reload Apache

```bash
sudo systemctl reload apache2
```

### Check Apache status

```bash
systemctl status apache2
```

### Watch Argo CD Apache access log

```bash
tail -f /var/log/apache2/argocd-access.log
```

### Watch Argo CD Apache error log

```bash
tail -f /var/log/apache2/argocd-error.log
```

### Check certificate SANs

```bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -ext subjectAltName
```

### Check certificate validity dates

```bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -dates
```

---

## 17. Security Follow-Up

After confirming that Argo CD is accessible, change the initial `admin` password.

The initial password should not be treated as a permanent administrative credential.

After the password has been changed and verified, the initial password secret can be removed:

```bash
kubectl -n argocd delete secret argocd-initial-admin-secret
```

Do this **only after confirming that the new administrator password works**.

---

## 18. Final Architecture Summary

```text
                HOME NETWORK

 Windows / Linux / Mac Client
              |
              | DNS
              | argocd.aaravsharma.net
              |
              | HTTPS :443
              v
+--------------------------------------+
| Ubuntu Laptop                       |
|                                      |
| Apache2                              |
|                                      |
| Let's Encrypt wildcard certificate  |
| *.aaravsharma.net                    |
+------------------+-------------------+
                   |
                   | HTTPS
                   | 192.168.56.10:32443
                   v
+--------------------------------------+
| Vagrant VM                           |
| Kubernetes Controller               |
| 192.168.56.10                        |
|                                      |
| NodePort :32443                      |
|         |                            |
|         v                            |
| argocd-server                        |
|         |                            |
|         v                            |
| Argo CD                              |
+--------------------------------------+
```

Final endpoint:

```text
https://argocd.aaravsharma.net
```

---

## 19. Key Learning Points

This exercise demonstrates several infrastructure concepts working together:

- Kubernetes `ClusterIP` vs `NodePort`
- Kubernetes service exposure
- Vagrant private networking
- Host-to-VM networking
- Apache VirtualHosts
- Apache reverse proxying
- TLS termination
- Backend TLS
- Let's Encrypt wildcard certificates
- Certificate SAN validation
- HTTP-to-HTTPS redirects
- Secure browser authentication sessions
- Troubleshooting HTTP `200` vs `401` responses
- Using Apache access logs to isolate authentication problems
- Limiting external exposure to only the required Kubernetes service

The resulting design provides a convenient way to access an internal Kubernetes-hosted application from the home network while maintaining HTTPS end-to-end:

```text
Browser --HTTPS--> Apache --HTTPS--> Argo CD
```