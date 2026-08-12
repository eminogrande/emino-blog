import assert from "node:assert/strict";
import { spawn } from "node:child_process";
import { mkdtemp, mkdir, readFile, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import { join } from "node:path";
import { once } from "node:events";
import { createPublisher } from "./src/publisher.mjs";

const root = await mkdtemp(join(tmpdir(), "web-mcp-"));
await mkdir(join(root, "content", "posts"), { recursive: true });
await writeFile(join(root, "web-mcp.config.json"), JSON.stringify({ name: "Test Site", languages: ["en", "tr"] }));
const publisher = createPublisher({ root, buildCommand: "node --version" });

const site = await publisher.siteGet();
assert.equal(site.name, "Test Site");
assert.deepEqual(site.languages, ["en", "tr"]);
console.log("ok site_get reads configuration");

const saved = await publisher.articleSave({ title: "Hello agents", body: "# Hello\n\nOne source for humans and machines.", kind: "writing", language: "en", tags: ["mcp"] });
assert.equal(saved.article.draft, true);
assert.equal(saved.article.slug, "hello-agents");
console.log("ok article_save creates a draft");

assert.equal((await publisher.articleList()).length, 0);
assert.equal((await publisher.articleList({ includeDrafts: true })).length, 1);
console.log("ok article_list hides drafts by default");

const published = await publisher.articlePublish({ slug: "hello-agents" });
assert.equal(published.article.draft, false);
assert.equal((await publisher.articleList()).length, 1);
console.log("ok article_publish exposes the article");

await assert.rejects(() => publisher.articleGet({ path: "../../secret" }), /required|not found/i);
await assert.rejects(() => publisher.articleSave({ title: "../../secret", slug: "../../secret", body: "x" }), /path-safe/);
console.log("ok traversal is rejected");

const build = await publisher.siteBuild();
assert.match(build.stdout, /^v\d+/);
console.log("ok site_build returns real output");

const child = spawn(process.execPath, [join(import.meta.dirname, "src", "stdio.mjs")], {
  cwd: root,
  stdio: ["pipe", "pipe", "inherit"],
});
let buffer = "";
child.stdout.setEncoding("utf8");
child.stdout.on("data", (chunk) => { buffer += chunk; });

async function rpc(message) {
  buffer = "";
  child.stdin.write(`${JSON.stringify(message)}\n`);
  for (let tries = 0; tries < 100 && !buffer.includes("\n"); tries += 1) await new Promise((resolve) => setTimeout(resolve, 10));
  return JSON.parse(buffer.trim().split("\n").at(-1));
}

const initialized = await rpc({ jsonrpc: "2.0", id: 1, method: "initialize", params: { protocolVersion: "2024-11-05", capabilities: {}, clientInfo: { name: "selfcheck", version: "1" } } });
assert.equal(initialized.result.serverInfo.name, "web-mcp-publisher");
child.stdin.write(`${JSON.stringify({ jsonrpc: "2.0", method: "notifications/initialized" })}\n`);
const listed = await rpc({ jsonrpc: "2.0", id: 2, method: "tools/list", params: {} });
assert.deepEqual(listed.result.tools.map((tool) => tool.name), ["site_get", "site_update", "article_list", "article_get", "article_save", "article_publish", "site_build"]);
console.log("ok MCP initializes and exposes seven tools");

child.kill();
await once(child, "exit");
await rm(root, { recursive: true, force: true });
console.log("PASS 7/7");
