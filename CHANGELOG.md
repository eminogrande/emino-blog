# Changelog

## 2026-08-12

### Added

- Open-source Web MCP Publisher harness under `web-mcp/`.
- Shared file-backed operations exposed through MCP, HTTP API, CLI, and browser playground.
- Draft-first article creation with explicit publishing.
- Bearer-token protection for all write operations.
- Docker/nginx route for `https://emino.app/web-mcp/`.
- CI self-check for content operations, build execution, path safety, and MCP tool discovery.

### Rationale

The publishing system needs one source of truth that works equally well for people, agents, scripts, and command-line workflows. Keeping all interfaces on the same operations prevents content and behavior from drifting.
