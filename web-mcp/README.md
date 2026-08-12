# Web MCP Publisher

Open-source publishing harness for sites that humans and agents can browse, search, update, and publish through the same content files.

## What works

- Browser playground at `/web-mcp/`
- MCP over stdio and Streamable HTTP
- HTTP JSON API
- CLI
- Draft-first article workflow
- Hugo-compatible Markdown files
- Token-gated write operations

## Run it

```bash
cd web-mcp
npm ci
WEB_MCP_ROOT=.. WEB_MCP_TOKEN=change-me npm start
```

Open `http://127.0.0.1:8787/web-mcp/`.

MCP endpoint: `http://127.0.0.1:8787/web-mcp/mcp`

## Connect an MCP client

Stdio:

```json
{
  "mcpServers": {
    "web-publisher": {
      "command": "node",
      "args": ["/absolute/path/to/web-mcp/src/stdio.mjs"],
      "env": {
        "WEB_MCP_ROOT": "/absolute/path/to/site"
      }
    }
  }
}
```

HTTP clients use `/web-mcp/mcp`. Public read tools need no token. Write tools require `Authorization: Bearer <WEB_MCP_TOKEN>`.

## Tools

- `site_get`
- `site_update`
- `article_list`
- `article_get`
- `article_save`
- `article_publish`
- `site_build`

`article_save` always creates a draft. Publishing is a separate explicit call.

## CLI

```bash
WEB_MCP_ROOT=.. node src/cli.mjs article:list
WEB_MCP_ROOT=.. node src/cli.mjs article:save --title "Hello" --body "First draft"
WEB_MCP_ROOT=.. node src/cli.mjs article:publish --slug hello
```

## Content layout

```text
content/posts/{language}/{kind}/{slug}.md
```

Default kinds: `writing`, `film`, `photography`, `code`, `music`.

## Verify

```bash
npm run selfcheck
```

The check exercises configuration, draft creation, draft visibility, publishing, path safety, real build execution, MCP initialization, and all seven tools.

## Security

- Reads are public.
- Writes require a bearer token.
- Slugs/languages/kinds cannot contain path separators or `..`.
- Draft and publish are separate operations.
- Configure `WEB_MCP_TOKEN` outside source control.

## License

MIT
