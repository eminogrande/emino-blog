import { createReadStream } from "node:fs";
import { readFile, stat } from "node:fs/promises";
import { createServer as createHttpServer } from "node:http";
import { extname, join, normalize, resolve } from "node:path";
import { WebStandardStreamableHTTPServerTransport } from "@modelcontextprotocol/sdk/server/webStandardStreamableHttp.js";
import { authorized, createPublisher } from "./publisher.mjs";
import { createServer } from "./server.mjs";

const root = resolve(process.env.WEB_MCP_ROOT || process.cwd());
const uiRoot = resolve(import.meta.dirname, "..", "public");
const publisher = createPublisher({ root });
const port = Number(process.env.PORT || 8787);
const host = process.env.HOST || "127.0.0.1";
const writeOperations = new Set(["site_update", "article_save", "article_publish", "site_build"]);

function json(value, status = 200, headers = {}) {
  return new Response(JSON.stringify(value, null, 2), {
    status,
    headers: { "content-type": "application/json; charset=utf-8", "cache-control": "no-store", ...headers },
  });
}

async function body(request) {
  try { return await request.json(); } catch { return {}; }
}

async function api(request, url) {
  const input = request.method === "GET" ? Object.fromEntries(url.searchParams) : await body(request);
  const route = `${request.method} ${url.pathname}`;
  const routes = {
    "GET /web-mcp/api/site": () => publisher.siteGet(),
    "PATCH /web-mcp/api/site": () => publisher.siteUpdate(input),
    "GET /web-mcp/api/articles": () => publisher.articleList({ ...input, includeDrafts: input.includeDrafts === "true" }),
    "GET /web-mcp/api/article": () => publisher.articleGet(input),
    "POST /web-mcp/api/articles": () => publisher.articleSave(input),
    "POST /web-mcp/api/publish": () => publisher.articlePublish(input),
    "POST /web-mcp/api/build": () => publisher.siteBuild(),
  };
  if (!routes[route]) return json({ error: "Not found" }, 404);
  if (request.method !== "GET" && !authorized(request)) return json({ error: "Bearer token required" }, 401);
  return json(await routes[route]());
}

async function mcp(request) {
  const payload = await request.clone().json().catch(() => ({}));
  if (payload.method === "tools/call" && writeOperations.has(payload.params?.name) && !authorized(request)) {
    return json({ jsonrpc: "2.0", id: payload.id ?? null, error: { code: -32001, message: "Bearer token required for write tools" } }, 401);
  }
  const transport = new WebStandardStreamableHTTPServerTransport({ sessionIdGenerator: undefined });
  await createServer({ publisher }).connect(transport);
  return transport.handleRequest(request);
}

const contentTypes = {
  ".css": "text/css; charset=utf-8",
  ".html": "text/html; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
};

async function staticFile(url) {
  let path = url.pathname.replace(/^\/web-mcp\/?/, "") || "index.html";
  path = normalize(path).replace(/^(\.\.(\/|\\|$))+/, "");
  const target = resolve(uiRoot, path);
  if (!target.startsWith(uiRoot)) return new Response("Not found", { status: 404 });
  try {
    const info = await stat(target);
    const file = info.isDirectory() ? join(target, "index.html") : target;
    return new Response(await readFile(file), {
      headers: { "content-type": contentTypes[extname(file)] || "application/octet-stream", "cache-control": "public, max-age=300" },
    });
  } catch {
    return new Response("Not found", { status: 404 });
  }
}

async function handle(request) {
  try {
    const url = new URL(request.url);
    if (url.pathname === "/web-mcp/mcp") return await mcp(request);
    if (url.pathname.startsWith("/web-mcp/api/")) return await api(request, url);
    if (url.pathname === "/web-mcp" || url.pathname.startsWith("/web-mcp/")) return await staticFile(url);
    return new Response("Not found", { status: 404 });
  } catch (error) {
    return json({ error: error.message }, 400);
  }
}

const server = createHttpServer(async (incoming, outgoing) => {
  const chunks = [];
  for await (const chunk of incoming) chunks.push(chunk);
  const request = new Request(`http://${incoming.headers.host || `${host}:${port}`}${incoming.url}`, {
    method: incoming.method,
    headers: incoming.headers,
    body: chunks.length ? Buffer.concat(chunks) : undefined,
  });
  const response = await handle(request);
  outgoing.writeHead(response.status, Object.fromEntries(response.headers));
  outgoing.end(Buffer.from(await response.arrayBuffer()));
});

server.listen(port, host, () => console.log(`Web MCP: http://${host}:${port}/web-mcp/`));
