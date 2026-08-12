const api = "./api";
const staticMode = location.protocol === "https:" && location.hostname === "emino.app";
const results = document.querySelector("#results");
const count = document.querySelector("#article-count");

function escapeHtml(value = "") {
  return value.replace(/[&<>"']/g, (character) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[character]);
}

function render(items) {
  count.textContent = items.length;
  results.innerHTML = items.length ? items.slice(0, 20).map((item) => `
    <article class="result">
      <div><h3>${escapeHtml(item.title)}</h3><p>${escapeHtml(item.summary || item.excerpt || "")}</p></div>
      <span class="badge">${escapeHtml(item.language)} · ${escapeHtml(item.kind)}</span>
    </article>`).join("") : "<p>No published articles matched.</p>";
}

async function load(query = "") {
  if (staticMode) {
    const response = await fetch("/index.json");
    if (!response.ok) throw new Error(`Search failed: ${response.status}`);
    const needle = query.toLowerCase();
    const items = (await response.json())
      .filter((item) => !needle || `${item.title}\n${item.summary}\n${item.content}`.toLowerCase().includes(needle))
      .map((item) => ({ title: item.title, summary: item.summary.replace(/<[^>]*>/g, " ").replace(/\s+/g, " ").trim().slice(0, 240), language: "en", kind: "writing" }));
    render(items);
    return;
  }
  const response = await fetch(`${api}/articles?query=${encodeURIComponent(query)}`);
  if (!response.ok) throw new Error(`Search failed: ${response.status}`);
  render(await response.json());
}

document.querySelector("#search-form").addEventListener("submit", (event) => {
  event.preventDefault();
  load(new FormData(event.currentTarget).get("query")).catch((error) => { results.textContent = error.message; });
});

document.querySelector("#draft-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  const output = document.querySelector("#draft-output");
  if (staticMode) {
    output.textContent = "Draft writes activate after server SSH access is repaired. MCP, API and CLI code are already open source.";
    return;
  }
  const data = Object.fromEntries(new FormData(event.currentTarget));
  const token = data.token;
  delete data.token;
  output.textContent = "Saving…";
  const response = await fetch(`${api}/articles`, {
    method: "POST",
    headers: { "content-type": "application/json", authorization: `Bearer ${token}` },
    body: JSON.stringify(data),
  });
  const value = await response.json();
  output.textContent = response.ok ? `Draft saved: ${value.article.id}` : value.error;
});

load().catch((error) => { results.textContent = error.message; });
