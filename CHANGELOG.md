# Changelog

## 2026-10-14 — [RELEASE] v0.1.0 — hermes-agent for emino

First tagged release. Tag `v0.1.0` targets default-branch HEAD `86379ef6` (main).

State at `86379ef6`:

- Hugo blog for `https://emino.app` with Flask admin, Maildir email-to-post pipeline and cron health checks.
- `web-mcp/` publishing harness: MCP (stdio + HTTP), HTTP API, CLI and browser playground, bearer-gated writes.
- `platform/` Cloudflare Pages + D1 writing site for `writing.emin.de` with admin CRUD, MCP and agent discovery.
- Deploy: `.github/workflows/deploy.yml` builds and SSH-deploys on push to `main`.
- Docs: README rewritten with Logs, Status, Architecture, User flow, Components, API and Run sections. PROMPTLOG.md added. No code changed.

## 2026-08-13

- `86379ef6` fix: Lighthouse failures on the writing platform cleared: favicon 404, accent contrast, llms.txt links (#8).
- `3d85805e` fix: OAuth and auth.md discovery metadata now match the request origin, valid on Pages preview and writing.emin.de (#7).
- `f12adb07` feat: agent-native publishing platform in `platform/`: Cloudflare Pages + D1 site, shadcn admin, legacy content import, authenticated CRUD, MCP, WebMCP and agent discovery (#6).

## 2026-08-12

### Added

- Added a static `/web-mcp/` playground shell so the existing server cron can publish and browse live content before SSH-based service activation.
- Fixed the repository ignore rule that omitted the browser assets from clean clones and Docker builds.
- Open-source Web MCP Publisher harness under `web-mcp/`.
- Shared file-backed operations exposed through MCP, HTTP API, CLI, and browser playground.
- Draft-first article creation with explicit publishing.
- Bearer-token protection for all write operations.
- Docker/nginx route for `https://emino.app/web-mcp/`.
- CI self-check for content operations, build execution, path safety, and MCP tool discovery.

### Commits

- `8ab0750f` fix: Web MCP playground published through Hugo (#4).
- `b1f9cde0` fix: PaperMod theme installed in clean deployment builds (#3).
- `bd70f402` feat: open-source Web MCP publishing harness (#2).

### Rationale

The publishing system needs one source of truth that works equally well for people, agents, scripts, and command-line workflows. Keeping all interfaces on the same operations prevents content and behavior from drifting.

## Earlier history

- `203df555` 2026-07-17 Docker multi-stage build (Hugo + nginx + Flask admin) and GitHub Actions deploy. First commit `1a07d318` 2025-08-26 "Initial AI-optimized Hugo blog setup".
