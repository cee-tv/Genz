// Minimal helpers
const $ = (id) => document.getElementById(id);

function setStatus(el, msg, ok = true) {
  el.textContent = msg || "";
  el.classList.toggle("ok", !!ok);
  el.classList.toggle("err", !ok);
}

async function triggerWorkflow({owner, repo, ref, workflow, token, inputs}) {
  // POST https://api.github.com/repos/{owner}/{repo}/actions/workflows/{workflow_id}/dispatches
  const url = `https://api.github.com/repos/cee-tv/Genz/actions/workflows/generate-keys.yml/dispatches`;
  const res = await fetch(url, {
    method: "POST",
    headers: {
      "Accept": "application/vnd.github+json",
      "Authorization": `Bearer ${token}`,
      "X-GitHub-Api-Version": "2022-11-28",
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ ref, inputs })
  });
  if (!res.ok) {
    const text = await res.text();
    throw new Error(`GitHub API error (${res.status}): ${text}`);
  }
  return true;
}

function fillTable(data) {
  const table = $("table");
  const tbody = table.querySelector("tbody");
  tbody.innerHTML = "";

  if (!data || !Array.isArray(data.keys)) {
    table.classList.add("hidden");
    return;
  }

  data.keys.forEach((k, i) => {
    const tr = document.createElement("tr");
    tr.innerHTML = `
      <td>${i + 1}</td>
      <td><code>${k}</code></td>
      <td>${data.expires_at_pht}</td>
      <td>${data.expires_at_unix}</td>
      <td>${data.tag || ""}</td>
    `;
    tbody.appendChild(tr);
  });

  table.classList.remove("hidden");
}

$("runBtn").addEventListener("click", async () => {
  const unit = $("unit").value.trim();
  const amount = $("amount").value.trim();
  const count = $("count").value.trim();
  const tag = $("tag").value.trim();

  const owner = $("owner").value.trim();
  const repo = $("repo").value.trim();
  const ref = $("ref").value.trim() || "main";
  const workflow = $("workflow").value.trim() || "generate-keys.yml";
  const token = $("token").value.trim();

  const statusEl = $("runStatus");
  setStatus(statusEl, "Triggering workflow...");

  if (!owner || !repo || !token) {
    setStatus(statusEl, "Owner, repo, and token are required to trigger.", false);
    return;
  }

  try {
    await triggerWorkflow({
      owner, repo, ref, workflow, token,
      inputs: { unit, amount, count, tag }
    });
    setStatus(statusEl, "Workflow triggered! Check GitHub Actions for progress.");
  } catch (err) {
    console.error(err);
    setStatus(statusEl, err.message, false);
  }
});

$("fetchBtn").addEventListener("click", async () => {
  const url = $("jsonUrl").value.trim();
  const statusEl = $("fetchStatus");
  const outEl = $("output");

  if (!url) {
    setStatus(statusEl, "Please provide the raw URL to keys/latest.json", false);
    return;
  }
  setStatus(statusEl, "Fetching...");

  try {
    const res = await fetch(url, { cache: "no-store" });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const json = await res.json();
    outEl.textContent = JSON.stringify(json, null, 2);
    fillTable(json);
    setStatus(statusEl, "Loaded.");
  } catch (err) {
    console.error(err);
    setStatus(statusEl, err.message, false);
  }
});
