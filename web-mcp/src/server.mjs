import { McpServer } from "@modelcontextprotocol/sdk/server/mcp.js";
import { z } from "zod";
import { createPublisher } from "./publisher.mjs";

function response(value) {
  return {
    content: [{ type: "text", text: JSON.stringify(value, null, 2) }],
    structuredContent: value,
  };
}

const articleRef = z.object({
  id: z.string().optional(),
  slug: z.string().optional(),
});

export function createServer(options = {}) {
  const publisher = options.publisher || createPublisher(options);
  const server = new McpServer({
    name: "web-mcp-publisher",
    version: "0.1.0",
    instructions: "Read the site before editing. Save creates a draft. Publish only after explicit user approval.",
  });

  server.registerTool("site_get", {
    description: "Read site identity, languages, content kinds and build settings.",
    inputSchema: z.object({}),
  }, async () => response(await publisher.siteGet()));

  server.registerTool("site_update", {
    description: "Update site identity, languages and content kinds.",
    inputSchema: z.object({
      name: z.string().optional(),
      description: z.string().optional(),
      baseUrl: z.string().url().optional(),
      defaultLanguage: z.string().optional(),
      languages: z.array(z.string()).optional(),
      kinds: z.array(z.string()).optional(),
    }),
  }, async (args) => response(await publisher.siteUpdate(args)));

  server.registerTool("article_list", {
    description: "List or full-text search articles.",
    inputSchema: z.object({
      query: z.string().optional(),
      kind: z.string().optional(),
      language: z.string().optional(),
      includeDrafts: z.boolean().optional(),
      includeBody: z.boolean().optional().describe("Include full article bodies. Defaults to metadata and excerpts."),
    }),
  }, async (args) => response(await publisher.articleList(args)));

  server.registerTool("article_get", {
    description: "Read one article by stable id, slug or relative path.",
    inputSchema: articleRef,
  }, async (args) => response(await publisher.articleGet(args)));

  server.registerTool("article_save", {
    description: "Create or update an article as a draft. Never publishes.",
    inputSchema: z.object({
      title: z.string().min(1),
      body: z.string().min(1),
      slug: z.string().optional(),
      summary: z.string().optional(),
      language: z.string().optional(),
      kind: z.string().optional(),
      tags: z.array(z.string()).optional(),
    }),
  }, async (args) => response(await publisher.articleSave(args)));

  server.registerTool("article_publish", {
    description: "Publish an existing draft. Call only after explicit approval.",
    inputSchema: articleRef,
  }, async (args) => response(await publisher.articlePublish(args)));

  server.registerTool("site_build", {
    description: "Run the configured static-site build and return real output.",
    inputSchema: z.object({}),
  }, async () => response(await publisher.siteBuild()));

  return server;
}
