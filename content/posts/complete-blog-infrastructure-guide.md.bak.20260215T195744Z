+++
title = "The Complete Guide: Building a Full-Stack Blog Infrastructure with Lightning, Nostr, and Email Publishing"
date = 2024-08-26T15:45:00Z
draft = false
tags = ["infrastructure", "bitcoin", "nostr", "automation", "devops", "lightning", "email", "hugo"]
categories = ["tutorial", "web-development"]
+++

## What We Built: A Complete Modern Blog Infrastructure

This comprehensive guide documents the creation of a fully-featured, decentralized blog platform with cutting-edge features including Bitcoin Lightning payments, Nostr integration, email-to-blog publishing, and automated GitHub deployments.

## Infrastructure Overview

### Core Components
- **Server**: Hetzner Ubuntu VPS (188.34.194.25)
- **Static Site Generator**: Hugo with PaperMod theme
- **Web Server**: Nginx with SSL (Let's Encrypt)
- **Domain**: emino.app (via Porkbun DNS)
- **Version Control**: GitHub with automated deployments
- **Email Server**: Postfix + Dovecot for email-to-blog
- **Containers**: Docker for services (Alby Hub, Nostr relay)

## Features Implemented

### 1. Lightning Bitcoin Tips ⚡
- **Address**: emin@nuri.com
- **Design**: Minimalist typography-focused interface
- **Colors**: Bitcoin orange (#f7931a), black, and white only
- **WebLN Support**: Full integration with Alby browser extension
- **Payment Options**:
  - One-click WebLN payments for Alby users
  - Lightning URI deep links for mobile wallets
  - Fallback modal for manual payments

### 2. Nostr Integration 📡
- **Personal Relay**: Running at `wss://relay.emino.app`
- **Long-form Content**: Posts published as NIP-23 events
- **Publishing Script**: Automatic cross-posting to Nostr
- **Media Handling**: Compressed images and videos
- **Docker Container**: nostr-rs-relay for reliability

### 3. Email-to-Blog Publishing 📧
- **Email Address**: post@emino.app
- **Authorized Senders**:
  - emin@nuri.com
  - emin@emin.de
  - eminhenri@gmail.com
- **Features**:
  - Markdown file attachments supported
  - Automatic image compression (max 1920x1080)
  - Video compression with FFmpeg (H.264)
  - GitHub sync for every email post
  - Cron job checks every 15 minutes

### 4. DNS Configuration 🌐
The following DNS records were configured at Porkbun:

```
A Record:
  Host: @
  Answer: 188.34.194.25
  TTL: 600

A Record:
  Host: www
  Answer: 188.34.194.25
  TTL: 600

MX Record:
  Host: (blank)
  Answer: emino.app
  Priority: 10
  TTL: 600

TXT Record (SPF):
  Host: (blank)
  Answer: v=spf1 ip4:188.34.194.25 ~all
  TTL: 600

TXT Record (DMARC):
  Host: _dmarc
  Answer: v=DMARC1; p=none; rua=mailto:post@emino.app
  TTL: 600
```

### 5. GitHub Actions Auto-Deployment 🚀
- **Trigger**: Any push to main branch
- **Actions**:
  - Pull latest changes
  - Clean build directory (removes deleted posts)
  - Rebuild with Hugo
  - Deploy with rsync (--delete flag)
- **Workflow File**: `.github/workflows/deploy.yml`

### 6. Security & Authentication 🔒
- **SSH Keys**: Ed25519 for secure server access
- **Email Authentication**: Whitelist of authorized senders
- **SSL/TLS**: Let's Encrypt certificates
- **Firewall**: UFW configured for web and email
- **Nostr**: Optional NSEC environment variable

### 7. Media & Asset Handling 🖼️
- **Favicon**: Bitcoin-themed with multiple sizes
- **Image Compression**: Pillow (Python) for optimization
- **Video Compression**: FFmpeg with H.264 codec
- **Static Assets**: Served from `/static/media/`
- **PWA Support**: Site manifest with theme colors

## Technical Implementation Details

### Hugo Configuration (config.toml)
```toml
baseURL = "https://emino.app/"
languageCode = "en-us"
title = "emino.app"
theme = "PaperMod"

[params]
env = "production"
defaultTheme = "auto"
ShowShareButtons = true
ShowReadingTime = true
ShowToc = true
ShowBreadCrumbs = true
ShowPostNavLinks = true
ShowCodeCopyButtons = true
```

### Build Script (build.sh)
```bash
#!/bin/bash
echo "Cleaning old build..."
rm -rf public/*
echo "Building site with Hugo..."
hugo --minify
echo "Syncing to web root..."
rsync -av --delete public/ /var/www/apps/main/
echo "Build complete!"
```

### Email Processing Flow
1. Email sent to post@emino.app with subject "BLOG: Title"
2. Cron job runs email_to_blog.py every 15 minutes
3. Script checks sender authorization
4. Processes markdown or plain text content
5. Compresses and embeds media files
6. Creates Hugo-formatted markdown post
7. Rebuilds site and syncs to GitHub
8. Optionally publishes to Nostr

### Nostr Publishing Flow
1. Parse Hugo markdown post
2. Create NIP-23 long-form content event
3. Add tags (title, published_at, d-tag for replaceability)
4. Sign with private key (NSEC)
5. Publish to multiple relays:
   - wss://relay.emino.app (own relay)
   - wss://relay.damus.io
   - wss://nos.lol
   - wss://relay.nostr.band

## Services Running

### Docker Containers
```bash
# Alby Hub (Lightning)
docker run -d --name alby-hub \
  -p 8080:8080 -p 9735:9735 \
  ghcr.io/getalby/hub:latest

# Nostr Relay
docker run -d --name nostr-relay \
  -p 8081:8080 \
  scsibug/nostr-rs-relay:latest
```

### Nginx Virtual Hosts
- **emino.app**: Main blog (port 443/80)
- **hub.emino.app**: Alby Hub interface (proxy to 8080)
- **relay.emino.app**: Nostr relay WebSocket (proxy to 8081)

### Cron Jobs
```bash
# Email checking every 15 minutes
*/15 * * * * cd /var/www/emino-blog && \
  ./nostr-env/bin/python scripts/email_to_blog.py \
  >> /var/log/email-to-blog.log 2>&1
```

## File Structure
```
/var/www/emino-blog/
├── config.toml
├── build.sh
├── content/posts/
├── themes/PaperMod/
├── static/
│   ├── media/
│   ├── favicon.ico
│   └── site.webmanifest
├── scripts/
│   ├── email_to_blog.py
│   ├── nostr_publisher.py
│   └── email_auth.txt
├── nostr-env/ (Python venv)
└── .github/workflows/deploy.yml

/var/www/apps/main/ (deployed site)
/var/www/nostr-relay/ (relay config)
/var/www/alby-hub/ (Lightning hub)
```

## Environment Variables Required
```bash
# For email-to-blog
BLOG_EMAIL="post@emino.app"
BLOG_EMAIL_PASSWORD="Kilimanjaro##8"

# For Nostr publishing (optional)
NOSTR_NSEC="your-nostr-private-key"
```

## Monitoring & Maintenance

### Health Checks
- Blog availability: `curl -I https://emino.app`
- Lightning tips: Check address at hub.emino.app
- Nostr relay: `wss://relay.emino.app` connection test
- Email: Check `/var/log/email-to-blog.log`

### Common Tasks
```bash
# Manual rebuild
cd /var/www/emino-blog && ./build.sh

# Check email processing
./nostr-env/bin/python scripts/email_to_blog.py

# View Docker containers
docker ps

# Check Nginx status
systemctl status nginx
```

## Security Considerations

1. **Email Whitelist**: Only authorized senders can post
2. **No Public Email Relay**: Server only accepts mail for configured domains
3. **SSL Everything**: All services use HTTPS/WSS
4. **Key Management**: NSEC keys stored as environment variables
5. **Regular Updates**: Automated security updates enabled

## Performance Optimizations

1. **Static Site**: No database, instant loading
2. **Image Compression**: All images optimized before serving
3. **Video Compression**: H.264 with web-optimized settings
4. **CDN Ready**: Static files can be easily CDN-cached
5. **Minified Output**: Hugo minification enabled

## Future Enhancements Possible

- [ ] Automated image generation with AI
- [ ] Nostr comments system
- [ ] Lightning paywall for premium content
- [ ] IPFS backup and distribution
- [ ] Analytics without tracking
- [ ] Automated social media cross-posting

## Conclusion

This infrastructure represents a modern, decentralized approach to blogging that combines:
- **Traditional web** (Hugo static site)
- **Web3 payments** (Lightning Bitcoin)
- **Decentralized social** (Nostr protocol)
- **Email convenience** (post-by-email)
- **Developer workflow** (GitHub CI/CD)

The entire stack is self-hosted, privacy-respecting, and built with open-source technologies. It demonstrates how individual creators can own their complete publishing infrastructure while maintaining modern conveniences and integrations.

## Resources & Links

- **Live Site**: [emino.app](https://emino.app)
- **Lightning Address**: emin@nuri.com
- **Nostr Relay**: wss://relay.emino.app
- **GitHub**: [github.com/eminogrande/emino-blog](https://github.com/eminogrande/emino-blog)

---

*This post was created to document the complete infrastructure build process. If you can read this, all systems are working correctly!* ⚡🚀
