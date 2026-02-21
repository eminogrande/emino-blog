+++
title = "How Email‑to‑Blog Publishing Works on emino.app"
date = 2025-12-02T09:10:01Z
draft = false
tags = ["email-post"]
categories = ["blog"]
slug = "how-email-to-blog-publishing-works-on-emino-app"
+++

This is the full, technical path from an email sent to post@emino.app to a
published post, including DNS/TLS, SMTP/IMAP, filtering/
  validation, and the importer internals. The flowchart now includes sender
checks and parsing.

  ## Pipeline at a Glance

  - DNS: A record emino.app → 188.34.194.25; MX record 0 emino.app.
  - TLS: Let’s Encrypt cert at /etc/letsencrypt/live/emino.app/ used by
Nginx, Postfix (STARTTLS), Dovecot (IMAPS); certbot.timer auto-
    renews.
  - SMTP inbound: Postfix on :25, virtual mailbox post@emino.app → Maildir
/var/mail/vhosts/emino.app/post/.
  - IMAP access (for importer/clients): Dovecot on :993 with the same LE
cert.
  - Firewall: ufw open for 22, 80, 443, 25; 993 if IMAP access is needed.
  - Importer: polls Maildir/IMAP, validates sender, parses/sanitizes,
converts to Markdown, writes to posts/ (or your content dir),
    triggers build/deploy.
  - Web: Nginx serves the static blog on HTTPS.

  ## Importer: Technical Behavior

  - Polling: runs on a timer (systemd timer/cron) or long-lived watcher;
reads Maildir new/ and cur/ or IMAP inbox.
  - Sender validation: checks From: against an allowlist (e.g., your
addresses). Unknown senders are skipped/logged.
  - Parsing:
      - Subject → title/slug; body → Markdown body.
      - Attachments: can be ignored or saved; filter to text/image types if
enabled.
  - Sanitization: strip dangerous HTML, normalize encodings, optional
link/emoji cleanup.
  - Conversion: build frontmatter (title, date, tags, author) + body in
Markdown; filename into content/posts/ (or configured path).
  - Publishing: optionally runs a build/deploy hook (static site generator,
cache refresh) after writing the file.
  - Logging: importer logs to its own file; failures should log and leave
messages in Maildir for retry.

  ## Configuration Checklist

  1. DNS
      - A emino.app 188.34.194.25
      - MX 0 emino.app.
  2. TLS
      - certbot --nginx -d emino.app -d www.emino.app --redirect
      - Verify certbot.timer (systemctl list-timers | grep certbot)
  3. Postfix (virtual mailbox)
      - /etc/postfix/vmailbox:

        post@emino.app emino.app/post/
      - postmap /etc/postfix/vmailbox
      - postconf -e "virtual_mailbox_domains=emino.app"
      - postconf -e "virtual_mailbox_maps=hash:/etc/postfix/vmailbox"
      - TLS:

        postconf -e "smtpd_tls_cert_file=/etc/letsencrypt/live/
emino.app/fullchain.pem"
        postconf -e "smtpd_tls_key_file=/etc/letsencrypt/live/
emino.app/privkey.pem"
        systemctl reload postfix
  4. Dovecot (IMAP/IMAPS)
      - /etc/dovecot/conf.d/10-ssl.conf:

        ssl_cert = </etc/letsencrypt/live/emino.app/fullchain.pem
        ssl_key  = </etc/letsencrypt/live/emino.app/privkey.pem
      - systemctl reload dovecot
  5. Maildir permissions
      - /var/mail/vhosts/emino.app/post/ owned by vmail:vmail, mode 700/600.
  6. Firewall (ufw)
      - ufw allow 25/tcp
      - ufw allow 993/tcp (if IMAP access needed)
      - ufw allow 80,443/tcp
  7. Importer job
      - Read from Maildir or IMAP for post@emino.app.
      - Allowlist sender addresses.
      - Write posts into your blog content path (e.g., content/posts/ or
posts/).
      - Run via systemd timer/cron; log to a dedicated file; trigger
build/deploy if required.
  8. Nginx
      - Port 80 → return 301 https://$host$request_uri;
      - Port 443 with LE cert paths; root at your blog directory; serve
static site.

  ## Monitoring & Reliability

  - TLS expiry: openssl x509 -in /etc/letsencrypt/live/
emino.app/fullchain.pem -noout -enddate
  - Mail flow: /var/log/mail.log (Postfix/Dovecot)
  - Importer: its dedicated log; alert on failures
  - Renewals: journalctl -u certbot if renewals misbehave
  - Health checks: periodic test mail to post@emino.app, confirm file lands
in Maildir and importer publishes.

  ## Common Failure Modes (and fixes)

  - Expired cert → use nginx HTTP challenge + certbot.timer (already in
place).
  - Port 25 blocked → open in ufw (done).
  - Importer down → ensure timer/service is active; check logs.
  - Maildir perms → keep vmail ownership and 700/600 modes.
  - Unknown sender → email skipped; add to allowlist if desired.

  This covers the complete, reproducible “email to blog” setup on
emino.app—from
DNS/TLS through SMTP/IMAP and sender validation to
  Markdown generation and publishing.

![sequenceDiagram_2025-12-02T09-05-40](/media/how-email-to-blog-publishing-works-on-emino-app/sequenceDiagram_2025-12-02T09-05-40.svg)

---
*Post created via email from emin@nuri.com*
