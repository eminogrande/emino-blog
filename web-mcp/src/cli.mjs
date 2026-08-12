#!/usr/bin/env node
import { createPublisher } from "./publisher.mjs";

const [command, ...rest] = process.argv.slice(2);
const publisher = createPublisher();

function parseArgs(values) {
  const result = {};
  for (let index = 0; index < values.length; index += 2) {
    const key = values[index]?.replace(/^--/, "");
    if (!key) continue;
    const value = values[index + 1];
    result[key] = key === "tags" ? value.split(",").filter(Boolean) : value;
  }
  return result;
}

const input = parseArgs(rest);
const commands = {
  "site:get": () => publisher.siteGet(),
  "site:update": () => publisher.siteUpdate(input),
  "article:list": () => publisher.articleList({ ...input, includeDrafts: input.includeDrafts === "true" }),
  "article:get": () => publisher.articleGet(input),
  "article:save": () => publisher.articleSave(input),
  "article:publish": () => publisher.articlePublish(input),
  build: () => publisher.siteBuild(),
};

if (!commands[command]) {
  console.error("Usage: web-mcp site:get | site:update | article:list | article:get | article:save | article:publish | build [--key value]");
  process.exit(1);
}

try {
  console.log(JSON.stringify(await commands[command](), null, 2));
} catch (error) {
  console.error(error.message);
  process.exit(1);
}
