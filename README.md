# Emino.app Blog

Static Hugo blog that powers [https://emino.app](https://emino.app) together with a lightweight Flask admin surface, cron-powered health checks, and a Maildir ingestion pipeline that converts authorized emails into posts.

## Repository layout

- `content/` – Markdown sources for Hugo posts.
- `static/` – Static assets that are copied verbatim during builds (`static/media/<slug>` holds post images and email attachments).
- `scripts/` – Operational helpers (email ingestion, GitHub sync, SEO / health automation).
- `admin_server.py` – Flask admin used for manual operations (trigger email ingestion, rebuilds, log tailing).
- `public/` – Hugo build output served by nginx.
- `.dev/` – Local-only helpers for Docker Compose (dummy Maildir + log mounts).

## How email posting works

1. `post@emino.app` receives mail via Postfix, which stores it inside `/var/mail/vhosts/emino.app/post`.
2. A cron job runs `scripts/process_maildir.py` every 5 minutes. The script now:
   - reads authorized senders from `scripts/email_auth.txt`,
   - parses each Maildir message (preferring plain text but falling back to HTML),
   - saves inline image attachments to `static/media/<slug>/`,
   - writes a Hugo post inside `content/posts/<timestamp>-<slug>.md`,
   - rebuilds the site once per batch with `hugo --minify`,
   - runs `git add/commit/push` so the new posts (and generated `public/` files) are safely stored on GitHub.
3. Processed emails are moved from `new/` to `cur/` so they are not reprocessed.

Because posts are now committed immediately, the GitHub sync script no longer wipes out newly created posts.

### Adding or removing authorized senders

Edit `scripts/email_auth.txt` (one address per line, comments are allowed) and the cron job / admin panel will pick up the new list automatically.

## Cron jobs on the server

```
*/5 * * * * /usr/bin/python3 /var/www/emino-blog/scripts/process_maildir.py   >> /var/log/email_processing.log 2>&1
*/5 * * * * /var/www/emino-blog/scripts/sync_from_github.sh                   >> /var/log/github-sync.log 2>&1
0  3 * * *  /var/www/emino-blog/seo-optimizer.sh                              >  /var/log/blog-seo.log 2>&1
0  */6 * * * /var/www/emino-blog/health-check.sh                              >  /var/log/blog-health.log 2>&1
```

## Admin dashboard

`admin_server.py` exposes `/admin` (proxied behind nginx). It now respects:

```
EMINO_BLOG_DIR   # defaults to the directory containing admin_server.py
EMINO_MAILDIR    # defaults to /var/mail/vhosts/emino.app/post
EMINO_MAIL_SCRIPT, EMINO_SYNC_SCRIPT, EMINO_HUGO_BIN
EMINO_EMAIL_LOG, EMINO_SYNC_LOG
```

These knobs make it easy to run the panel from Docker or on a workstation. Each action (`Check Emails`, `Sync GitHub`, `Rebuild Hugo`) executes the corresponding script inside the configured blog directory and streams stdout/stderr back to the UI.

## Docker / local development

```
docker compose up admin
docker compose up hugo
```

- `admin` builds the Flask app, mounts the repo at `/app`, and points the email ingestor at `./.dev/maildir`.
  Drop `.eml` files into `.dev/maildir/new/` to simulate incoming messages. Logs are stored under `.dev/logs/`.
- `hugo` runs `hugo server` (via `klakegg/hugo`) for quick previews at http://localhost:1313.

You can override any of the `EMINO_*` environment variables in `docker-compose.yml` if you want to point the container at a different Maildir or log directory. When testing locally, set `EMINO_SKIP_GIT=1` so the ingestor skips `git add/commit/push`.

## Git / deployments

- `scripts/sync_from_github.sh` now performs a safe fast-forward sync (`git fetch`, `git pull --ff-only`) and refuses to run if there are uncommitted changes. This keeps server edits intact while still pulling upstream updates.
- `build.sh` / `deploy.sh` are available for manual Hugo builds and rsync deployments if you need to publish outside of cron/admin.
- Logs from cron lives in `/var/log/email_processing.log`, `/var/log/github-sync.log`, `/var/log/blog-health.log`, and `/var/log/blog-seo.log`. You can tail them via the admin UI or directly over SSH.

## Operational tips

- Always run `scripts/process_maildir.py` manually after changing its configuration to ensure it can read the Maildir and has git access.
- When updating Hugo/config/theme files, commit to GitHub and either run the admin “Sync GitHub” action or wait for the cron job.
- Keep the root `.gitconfig` authenticated via `gh auth login` so automated commits from the ingestor can push successfully.
