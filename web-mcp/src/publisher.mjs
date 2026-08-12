import { createHash, timingSafeEqual } from "node:crypto";
import { execFile } from "node:child_process";
import { mkdir, readFile, readdir, rename, stat, writeFile } from "node:fs/promises";
import { basename, dirname, extname, join, relative, resolve, sep } from "node:path";
import { promisify } from "node:util";

const execFileAsync = promisify(execFile);
const DEFAULT_KINDS = ["writing", "film", "photography", "code", "music"];

function text(value, fallback = "") {
  return typeof value === "string" ? value.trim() : fallback;
}

export function slugify(value) {
  return text(value, "untitled")
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, "-")
    .replace(/^-+|-+$/g, "") || "untitled";
}

function quote(value) {
  return JSON.stringify(String(value));
}

function parseScalar(raw) {
  const value = raw.trim();
  if (value === "true") return true;
  if (value === "false") return false;
  if (value.startsWith("[") && value.endsWith("]")) {
    try { return JSON.parse(value.replace(/'/g, '"')); } catch { return []; }
  }
  return value.replace(/^['"]|['"]$/g, "");
}

export function parseDocument(source) {
  const match = source.match(/^\+\+\+\s*\n([\s\S]*?)\n\+\+\+\s*\n?([\s\S]*)$/);
  if (!match) return { meta: {}, body: source.trim() };
  const meta = {};
  for (const line of match[1].split("\n")) {
    const found = line.match(/^([A-Za-z0-9_-]+)\s*=\s*(.*)$/);
    if (found) meta[found[1]] = parseScalar(found[2]);
  }
  return { meta, body: match[2].trim() };
}

export function renderDocument(article) {
  const tags = Array.isArray(article.tags) ? article.tags.map(String) : [];
  const date = text(article.date) || new Date().toISOString();
  return [
    "+++",
    `title = ${quote(article.title)}`,
    `date = ${date}`,
    `draft = ${article.draft !== false}`,
    `slug = ${quote(article.slug)}`,
    `language = ${quote(article.language || "en")}`,
    `kind = ${quote(article.kind || "writing")}`,
    `summary = ${quote(article.summary || "")}`,
    `tags = ${JSON.stringify(tags)}`,
    "+++",
    "",
    text(article.body),
    "",
  ].join("\n");
}

function assertInside(root, target) {
  const rootPath = resolve(root);
  const targetPath = resolve(target);
  if (targetPath !== rootPath && !targetPath.startsWith(`${rootPath}${sep}`)) {
    throw new Error("Path escapes the configured content directory");
  }
  return targetPath;
}

async function exists(path) {
  try { await stat(path); return true; } catch { return false; }
}

async function walkMarkdown(root) {
  if (!(await exists(root))) return [];
  const output = [];
  for (const entry of await readdir(root, { withFileTypes: true })) {
    const path = join(root, entry.name);
    if (entry.isDirectory()) output.push(...await walkMarkdown(path));
    else if (entry.isFile() && extname(entry.name) === ".md") output.push(path);
  }
  return output;
}

function publicArticle(article) {
  return {
    id: article.id,
    title: article.title,
    slug: article.slug,
    language: article.language,
    kind: article.kind,
    summary: article.summary,
    tags: article.tags,
    date: article.date,
    draft: article.draft,
    body: article.body,
    path: article.path,
  };
}

export function createPublisher(options = {}) {
  const root = resolve(options.root || process.env.WEB_MCP_ROOT || process.cwd());
  const contentDir = assertInside(root, options.contentDir || process.env.WEB_MCP_CONTENT_DIR || join(root, "content", "posts"));
  const configPath = assertInside(root, options.configPath || process.env.WEB_MCP_CONFIG || join(root, "web-mcp.config.json"));
  const buildCommand = text(options.buildCommand || process.env.WEB_MCP_BUILD_COMMAND, "hugo --minify --gc");

  async function siteGet() {
    let config = {};
    if (await exists(configPath)) config = JSON.parse(await readFile(configPath, "utf8"));
    return {
      name: config.name || "Web MCP Publisher",
      description: config.description || "A site humans and agents can browse and publish.",
      baseUrl: config.baseUrl || "http://localhost:8787",
      defaultLanguage: config.defaultLanguage || "en",
      languages: config.languages || ["en"],
      kinds: config.kinds || DEFAULT_KINDS,
      contentDir: relative(root, contentDir),
      buildCommand,
    };
  }

  async function siteUpdate(input) {
    const current = await siteGet();
    const next = {
      name: text(input.name, current.name),
      description: text(input.description, current.description),
      baseUrl: text(input.baseUrl, current.baseUrl),
      defaultLanguage: text(input.defaultLanguage, current.defaultLanguage),
      languages: Array.isArray(input.languages) && input.languages.length ? [...new Set(input.languages.map(String))] : current.languages,
      kinds: Array.isArray(input.kinds) && input.kinds.length ? [...new Set(input.kinds.map(String))] : current.kinds,
    };
    await mkdir(dirname(configPath), { recursive: true });
    await writeFile(configPath, `${JSON.stringify(next, null, 2)}\n`, "utf8");
    return { updated: true, site: await siteGet() };
  }

  async function readArticle(path) {
    const source = await readFile(path, "utf8");
    const { meta, body } = parseDocument(source);
    const rel = relative(contentDir, path);
    const slug = text(meta.slug, basename(path, ".md").replace(/^\d{4}-\d{2}-\d{2}-\d{6}-/, ""));
    return publicArticle({
      id: `${meta.kind || "writing"}:${meta.language || "en"}:${slug}`,
      title: text(meta.title, slug),
      slug,
      language: text(meta.language, "en"),
      kind: text(meta.kind, "writing"),
      summary: text(meta.summary),
      tags: Array.isArray(meta.tags) ? meta.tags : [],
      date: text(meta.date),
      draft: meta.draft !== false,
      body,
      path: rel,
    });
  }

  async function articleList(filters = {}) {
    const files = await walkMarkdown(contentDir);
    const articles = await Promise.all(files.map(readArticle));
    const query = text(filters.query).toLowerCase();
    return articles
      .filter((article) => !filters.kind || article.kind === filters.kind)
      .filter((article) => !filters.language || article.language === filters.language)
      .filter((article) => filters.includeDrafts || !article.draft)
      .filter((article) => !query || `${article.title}\n${article.summary}\n${article.body}\n${article.tags.join(" ")}`.toLowerCase().includes(query))
      .sort((a, b) => b.date.localeCompare(a.date))
      .map((article) => {
        if (filters.includeBody) return article;
        const { body, ...metadata } = article;
        const excerpt = body.replace(/<[^>]*>/g, " ").replace(/[#*_>`!\[\]()]/g, " ").replace(/\s+/g, " ").trim().slice(0, 240);
        return { ...metadata, excerpt };
      });
  }

  async function articleGet(input) {
    const wanted = text(input.id || input.slug);
    if (!wanted) throw new Error("id or slug is required");
    const articles = await articleList({ includeDrafts: true, includeBody: true });
    const article = articles.find((item) => item.id === wanted || item.slug === wanted || item.path === wanted);
    if (!article) throw new Error(`Article not found: ${wanted}`);
    return article;
  }

  async function articleSave(input) {
    const unsafeSegments = [input.slug, input.language, input.kind].filter(Boolean).map(String);
    if (unsafeSegments.some((value) => value.includes("..") || value.includes("/") || value.includes("\\"))) {
      throw new Error("slug, language and kind must be path-safe names");
    }
    const title = text(input.title);
    if (!title) throw new Error("title is required");
    const body = text(input.body);
    if (!body) throw new Error("body is required");
    const slug = slugify(input.slug || title);
    const language = slugify(input.language || "en");
    const kind = slugify(input.kind || "writing");
    const target = assertInside(contentDir, join(contentDir, language, kind, `${slug}.md`));
    await mkdir(dirname(target), { recursive: true });
    const existing = await exists(target) ? await readArticle(target) : {};
    const article = {
      title,
      slug,
      language,
      kind,
      summary: text(input.summary, existing.summary || ""),
      tags: Array.isArray(input.tags) ? input.tags : existing.tags || [],
      date: text(existing.date) || new Date().toISOString(),
      draft: true,
      body,
    };
    const temporary = `${target}.${process.pid}.tmp`;
    await writeFile(temporary, renderDocument(article), "utf8");
    await rename(temporary, target);
    return { saved: true, article: await readArticle(target) };
  }

  async function articlePublish(input) {
    const article = await articleGet(input);
    const target = assertInside(contentDir, join(contentDir, article.path));
    await writeFile(target, renderDocument({ ...article, draft: false }), "utf8");
    return { published: true, article: await readArticle(target) };
  }

  async function siteBuild() {
    const [command, ...args] = buildCommand.split(/\s+/).filter(Boolean);
    const result = await execFileAsync(command, args, { cwd: root, timeout: 120_000, maxBuffer: 5_000_000 });
    return { built: true, command: buildCommand, stdout: result.stdout.trim(), stderr: result.stderr.trim() };
  }

  return { root, contentDir, siteGet, siteUpdate, articleList, articleGet, articleSave, articlePublish, siteBuild };
}

export function authorized(request, secret = process.env.WEB_MCP_TOKEN || "") {
  if (!secret) return false;
  const supplied = request.headers.get("authorization")?.replace(/^Bearer\s+/i, "") || "";
  const expectedHash = createHash("sha256").update(secret).digest();
  const suppliedHash = createHash("sha256").update(supplied).digest();
  return timingSafeEqual(expectedHash, suppliedHash);
}
