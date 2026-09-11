# Appendix: ACME, DNS-01, OpenSSL, Certificate Authority, and Certbot Toolkit

This appendix is a quick-reference companion to the main certificate
setup guide. It focuses on the concepts and commands that are useful
when validating, troubleshooting, and maintaining Let's Encrypt
certificates.

> Examples below use `aaravsharma.net` and `jenkins.aaravsharma.net`.
> Replace them as needed.

------------------------------------------------------------------------

## 1. ACME --- What Is It?

**ACME** stands for **Automatic Certificate Management Environment**.

ACME is the standardized protocol used by certificate authorities such
as Let's Encrypt and ACME clients such as Certbot to automate
certificate management.

At a high level:

``` text
Certbot (ACME client)
        |
        | ACME protocol
        v
Let's Encrypt (ACME server / Certificate Authority)
        |
        | asks: "Prove that you control this domain."
        v
ACME challenge
        |
        | successful validation
        v
Certificate issued
```

ACME is standardized as **RFC 8555**.

Certbot is therefore not the Certificate Authority. It is an **ACME
client** that communicates with a Certificate Authority such as Let's
Encrypt.

------------------------------------------------------------------------

## 2. What Does DNS-01 Mean?

**DNS** = Domain Name System.

The `01` in **DNS-01** is the name/version-style identifier for this
particular ACME challenge type; it is not an acronym that expands into
additional words.

DNS-01 is a method of proving control of a domain through DNS.

Let's Encrypt gives the ACME client a challenge. The client derives a
value from that challenge and publishes it as a TXT record under:

``` text
_acme-challenge.<domain>
```

For example:

``` text
_acme-challenge.aaravsharma.net
```

During our Route 53 workflow:

``` text
Certbot
   |
   | --dns-route53
   v
AWS Route 53
   |
   | creates temporary TXT record
   v
_acme-challenge.aaravsharma.net
   ^
   |
   | queries public DNS
   |
Let's Encrypt
```

If Let's Encrypt finds the expected value, it concludes that the
requester can control DNS for the domain and allows certificate
issuance.

### Why DNS-01 is useful

DNS-01 can issue **wildcard certificates**, for example:

``` text
*.aaravsharma.net
```

It also does not require the actual application server to be publicly
reachable from the Internet. That makes it particularly useful for
private services and home labs.

However, the ACME client still needs appropriate connectivity to the
Let's Encrypt ACME service and the DNS provider API, while Let's Encrypt
needs to be able to query the domain's public DNS.

### DNS-01 vs HTTP-01

``` text
DNS-01
------
Proves control using a DNS TXT record.
Supports wildcard certificates.
Application/web server does not need to be publicly reachable.

HTTP-01
-------
Proves control using a file served from the web server.
Uses HTTP port 80.
Does not support wildcard certificates.
```

------------------------------------------------------------------------

# 3. OpenSSL Certificate Inspection Toolkit

## Show validity dates

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -dates
```

Typical output:

``` text
notBefore=...
notAfter=...
```

`notBefore` is the beginning of the certificate's validity period.

`notAfter` is the certificate expiration time.

------------------------------------------------------------------------

## Show subject and issuer

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -subject -issuer
```

This answers:

``` text
Subject -> Who/what is this certificate for?
Issuer  -> Which CA issued/signed it?
```

------------------------------------------------------------------------

## Show Subject Alternative Names (SANs)

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -ext subjectAltName
```

For a wildcard certificate, expect something similar to:

``` text
DNS:aaravsharma.net
DNS:*.aaravsharma.net
```

This is one of the most important checks when troubleshooting a hostname
mismatch.

------------------------------------------------------------------------

## Show serial number

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -serial
```

The serial number uniquely identifies a certificate from the issuing CA
and is useful when comparing certificate versions.

------------------------------------------------------------------------

## Show SHA-256 fingerprint

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -fingerprint -sha256
```

This is very useful for answering:

> "Is Apache actually serving the same certificate that Certbot has
> installed on disk?"

------------------------------------------------------------------------

## Useful combined certificate check

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout \
  -subject \
  -issuer \
  -serial \
  -dates \
  -fingerprint -sha256 \
  -ext subjectAltName
```

This is a good general-purpose certificate inspection command.

------------------------------------------------------------------------

## Show the complete decoded certificate

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -text
```

This produces a large amount of information including:

-   certificate version
-   serial number
-   signature algorithm
-   issuer
-   validity
-   subject
-   public key information
-   X.509 extensions
-   SANs
-   certificate policies
-   signature

Use this when deeper troubleshooting is required.

------------------------------------------------------------------------

# 4. Check the Certificate Actually Served by Apache

Checking the file on disk is not enough. Apache may still have an older
certificate loaded in memory.

Query Apache directly:

``` bash
echo | openssl s_client \
  -connect 127.0.0.1:443 \
  -servername jenkins.aaravsharma.net 2>/dev/null \
  | openssl x509 \
      -noout \
      -subject \
      -issuer \
      -serial \
      -dates \
      -fingerprint -sha256
```

The important option is:

``` text
-servername jenkins.aaravsharma.net
```

This sends **SNI (Server Name Indication)** during the TLS handshake so
Apache can select the appropriate HTTPS virtual host.

Now compare it with the certificate on disk:

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -serial -dates -fingerprint -sha256
```

If the serial number and fingerprint match, Apache is serving the
current certificate.

------------------------------------------------------------------------

# 5. Certificate Authority / Trust Checks

## Check which CA issued the certificate

``` bash
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -issuer
```

The issuer identifies the CA certificate that signed the server
certificate.

------------------------------------------------------------------------

## Inspect the TLS chain presented by the server

``` bash
openssl s_client \
  -connect jenkins.aaravsharma.net:443 \
  -servername jenkins.aaravsharma.net \
  -showcerts
```

Look near the end for:

``` text
Verify return code: 0 (ok)
```

A successful verification indicates that OpenSSL was able to build and
validate the certificate chain using its configured trust store.

For a quieter verification-oriented command:

``` bash
echo | openssl s_client \
  -connect jenkins.aaravsharma.net:443 \
  -servername jenkins.aaravsharma.net \
  -verify_return_error 2>/dev/null
```

------------------------------------------------------------------------

## Verify hostname matching explicitly

On OpenSSL versions supporting `-verify_hostname`:

``` bash
echo | openssl s_client \
  -connect jenkins.aaravsharma.net:443 \
  -servername jenkins.aaravsharma.net \
  -verify_hostname jenkins.aaravsharma.net \
  -verify_return_error
```

This adds an explicit hostname verification check in addition to
certificate-chain validation.

------------------------------------------------------------------------

## Verify a certificate against the Ubuntu CA trust store

Ubuntu normally maintains trusted CA certificates under:

``` text
/etc/ssl/certs/
```

A basic verification command is:

``` bash
openssl verify \
  -CApath /etc/ssl/certs \
  /etc/letsencrypt/live/aaravsharma.net/fullchain.pem
```

For troubleshooting certificate chains, remember that `fullchain.pem`
contains the server certificate plus intermediate certificate(s), while
trust ultimately anchors at a trusted root CA in the operating
system/browser trust store.

------------------------------------------------------------------------

# 6. Optional DNS CAA Check

**CAA** stands for **Certification Authority Authorization**.

CAA is a DNS record that allows a domain owner to specify which
Certificate Authorities are permitted to issue certificates for the
domain.

Check existing CAA records:

``` bash
dig CAA aaravsharma.net
```

A CAA record permitting Let's Encrypt can look like:

``` text
aaravsharma.net. CAA 0 issue "letsencrypt.org"
```

For wildcard issuance, CAA also supports `issuewild`.

CAA is different from the Certificate Authority shown in an
already-issued certificate:

``` text
CAA DNS record -> Who MAY issue?
Certificate issuer -> Who DID issue?
```

------------------------------------------------------------------------

# 7. Certbot Must-Have Command Toolkit

## Check Certbot version

``` bash
certbot --version
```

For Snap:

``` bash
snap list certbot
```

------------------------------------------------------------------------

## Show available Certbot plugins

``` bash
certbot plugins
```

Useful for confirming that:

``` text
dns-route53
```

is installed and visible.

------------------------------------------------------------------------

## List certificates managed by Certbot

``` bash
sudo certbot certificates
```

This is probably the first Certbot command to run when investigating the
current certificate configuration.

It displays information such as:

-   certificate name
-   domains
-   expiration
-   certificate path
-   private-key path

------------------------------------------------------------------------

## Obtain a certificate without automatically installing it

Example Route 53 wildcard request:

``` bash
sudo certbot certonly \
  --dns-route53 \
  -d aaravsharma.net \
  -d '*.aaravsharma.net' \
  --agree-tos \
  --email YOUR_EMAIL_ADDRESS \
  --non-interactive
```

`certonly` means:

``` text
Obtain/manage the certificate,
but do not automatically rewrite the web-server configuration.
```

------------------------------------------------------------------------

## Test future renewal safely

``` bash
sudo certbot renew --dry-run
```

This is one of the most important operational Certbot commands.

It tests whether future automated renewal is likely to succeed without
replacing the live production certificate.

For a DNS-01/Route 53 setup, this exercises much of the real chain:

``` text
Certbot
   -> renewal configuration
   -> Route 53 plugin
   -> AWS authentication
   -> DNS challenge
   -> Let's Encrypt staging ACME service
   -> validation
```

------------------------------------------------------------------------

## Test renewal and deploy hooks

If a deploy hook is configured:

``` bash
sudo certbot renew --dry-run --run-deploy-hooks
```

This is useful for validating actions such as an Apache reload that
should occur after successful renewal.

------------------------------------------------------------------------

## Renew certificates normally

``` bash
sudo certbot renew
```

This checks Certbot-managed certificates and renews those that are
eligible/near expiry.

It does **not** normally issue a new certificate every time the command
runs.

------------------------------------------------------------------------

## Renew one named certificate

``` bash
sudo certbot renew --cert-name aaravsharma.net
```

Useful when multiple Certbot-managed certificates exist on the same
system.

------------------------------------------------------------------------

## Show Certbot help

``` bash
certbot --help
```

More detailed help:

``` bash
certbot --help all
```

Help for a particular command:

``` bash
certbot renew --help
```

------------------------------------------------------------------------

## Inspect Certbot account information

``` bash
sudo certbot show_account
```

This displays information about the ACME account Certbot is using.

------------------------------------------------------------------------

## Reconfigure a certificate

Modern Certbot provides:

``` bash
sudo certbot reconfigure --cert-name aaravsharma.net
```

Use this when intentionally changing renewal-related certificate
configuration rather than manually editing files under:

``` text
/etc/letsencrypt/renewal/
```

------------------------------------------------------------------------

## Revoke a certificate

``` bash
sudo certbot revoke --cert-name aaravsharma.net
```

Revocation is appropriate in situations such as private-key compromise
or when a certificate should no longer be trusted.

**Do not use revoke simply because a certificate is old or being
replaced during normal renewal.**

------------------------------------------------------------------------

## Delete a Certbot-managed certificate

First inspect certificate names:

``` bash
sudo certbot certificates
```

Then:

``` bash
sudo certbot delete --cert-name CERTIFICATE_NAME
```

Deleting and revoking are different operations:

``` text
delete -> removes Certbot's local certificate configuration/files
revoke -> tells the CA that the certificate should no longer be trusted
```

Do not manually `rm -rf` certificate directories under
`/etc/letsencrypt/`.

------------------------------------------------------------------------

# 8. Automatic Renewal Toolkit --- Snap Installation

Check the renewal timer:

``` bash
systemctl list-timers --all | grep -i certbot
```

For the Snap installation:

``` bash
systemctl status snap.certbot.renew.timer
```

Inspect the associated service:

``` bash
systemctl cat snap.certbot.renew.service
```

Check recent executions:

``` bash
journalctl -u snap.certbot.renew.service --since "7 days ago"
```

Inspect Certbot's own log:

``` bash
sudo less /var/log/letsencrypt/letsencrypt.log
```

Search for recent renewal-related messages:

``` bash
sudo grep -iE 'renew|success|failure|error' \
  /var/log/letsencrypt/letsencrypt.log | tail -50
```

------------------------------------------------------------------------

# 9. Certificate Files and Versions

Current/live certificate location:

``` bash
ls -l /etc/letsencrypt/live/aaravsharma.net/
```

You will normally see symbolic links such as:

``` text
cert.pem
chain.pem
fullchain.pem
privkey.pem
```

Historical certificate versions are kept under:

``` bash
ls -l /etc/letsencrypt/archive/aaravsharma.net/
```

The `live/` directory points to the currently active certificate
generation in `archive/`.

Useful mental model:

``` text
/etc/letsencrypt/archive/aaravsharma.net/
    cert1.pem
    cert2.pem
    cert3.pem
       ^
       |
       | current symlink
       |
/etc/letsencrypt/live/aaravsharma.net/cert.pem
```

Applications should normally reference the stable paths under `live/`,
not a numbered file under `archive/`.

------------------------------------------------------------------------

# 10. Quick Troubleshooting Sequence

When HTTPS/certificate behavior looks wrong, a practical order is:

``` text
1. What certificates does Certbot know about?
   certbot certificates

2. What does the certificate on disk contain?
   openssl x509 ... -subject -issuer -dates -ext subjectAltName

3. What certificate is Apache actually serving?
   openssl s_client ... | openssl x509 ...

4. Do the serial/fingerprint values match?
   Compare disk vs served certificate.

5. Does the certificate chain validate?
   openssl s_client ... -verify_return_error

6. Does the hostname match?
   openssl s_client ... -verify_hostname <hostname>

7. Will renewal work?
   certbot renew --dry-run

8. Is automatic renewal scheduled?
   systemctl status snap.certbot.renew.timer

9. Did Apache reload after renewal?
   journalctl -u apache2 --since "7 days ago"

10. What does Certbot's log say?
    /var/log/letsencrypt/letsencrypt.log
```

------------------------------------------------------------------------

# 11. Terms Worth Remembering

``` text
ACME
    Automatic Certificate Management Environment.
    Protocol used to automate certificate issuance and management.

ACME client
    Software such as Certbot.

ACME server
    CA-side service implementing ACME, such as Let's Encrypt.

DNS-01
    ACME challenge that proves domain control using a DNS TXT record.

TXT
    DNS record type used to publish arbitrary text/data.
    DNS-01 uses TXT records under _acme-challenge.

CA
    Certificate Authority.
    Organization/system that issues and signs certificates.

CAA
    Certification Authority Authorization.
    DNS record controlling which CAs may issue certificates for a domain.

SAN
    Subject Alternative Name.
    Certificate extension containing the DNS names/IP identities covered.

SNI
    Server Name Indication.
    TLS mechanism that tells a server which hostname the client wants.

TLS
    Transport Layer Security.
    Protocol providing encryption and authentication for HTTPS.

CSR
    Certificate Signing Request.
    Contains information including the public key used when requesting
    certificate issuance.

PEM
    Common text encoding/container format used for certificates and keys.
```

------------------------------------------------------------------------

## Bottom Line

For day-to-day certificate operations, remember these four commands
first:

``` bash
# What certificates do I have?
sudo certbot certificates

# What exactly is in this certificate?
openssl x509 \
  -in /etc/letsencrypt/live/aaravsharma.net/fullchain.pem \
  -noout -subject -issuer -serial -dates -fingerprint -sha256 \
  -ext subjectAltName

# What certificate is Apache really serving?
echo | openssl s_client \
  -connect 127.0.0.1:443 \
  -servername jenkins.aaravsharma.net 2>/dev/null \
  | openssl x509 -noout -subject -issuer -serial -dates \
      -fingerprint -sha256

# Will automatic renewal work?
sudo certbot renew --dry-run
```

Those four checks answer a surprisingly large percentage of real-world
certificate troubleshooting questions.
