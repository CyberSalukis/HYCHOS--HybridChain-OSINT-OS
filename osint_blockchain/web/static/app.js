/* OSINT Evidence Blockchain - frontend logic */
const API = "/api";
let TOKEN = localStorage.getItem("osint_token") || null;
let ME = null;

/* ---------------- helpers ---------------- */
function authHeaders(extra = {}) {
  const h = { ...extra };
  if (TOKEN) h["Authorization"] = "Bearer " + TOKEN;
  return h;
}
async function api(path, opts = {}) {
  const res = await fetch(API + path, {
    ...opts,
    headers: authHeaders(opts.headers || (opts.body && !(opts.body instanceof FormData) ? { "Content-Type": "application/json" } : {})),
  });
  const text = await res.text();
  let data;
  try { data = text ? JSON.parse(text) : {}; } catch { data = { raw: text }; }
  if (!res.ok) throw Object.assign(new Error(data.error || res.statusText), { status: res.status, data });
  return data;
}
function el(id) { return document.getElementById(id); }
function esc(s) { return String(s == null ? "" : s).replace(/[&<>"]/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c])); }
function short(h) { return h ? h.slice(0, 12) + "…" : ""; }

/* ---------------- auth ---------------- */
el("login-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  el("login-error").textContent = "";
  try {
    const data = await api("/auth/login", {
      method: "POST",
      body: JSON.stringify({ username: el("login-username").value, password: el("login-password").value }),
    });
    TOKEN = data.token;
    localStorage.setItem("osint_token", TOKEN);
    ME = data.user;
    enterApp();
  } catch (err) {
    el("login-error").textContent = err.message || "login failed";
  }
});
el("logout").addEventListener("click", () => {
  TOKEN = null; ME = null; localStorage.removeItem("osint_token");
  el("app-view").classList.add("hidden");
  el("login-view").classList.remove("hidden");
});

async function enterApp() {
  el("login-view").classList.add("hidden");
  el("app-view").classList.remove("hidden");
  el("who").textContent = ME.username;
  const badge = el("role-badge");
  badge.textContent = ME.role;
  badge.className = "badge " + ME.role;
  document.querySelectorAll(".admin-only").forEach(n => {
    n.style.display = ME.role === "admin" ? "" : "none";
  });
  // viewers cannot submit
  document.querySelector('[data-tab="submit"]').style.display =
    (ME.role === "viewer") ? "none" : "";
  loadEvidence();
}

/* ---------------- tabs ---------------- */
document.querySelectorAll(".tab").forEach(btn => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".tab").forEach(b => b.classList.remove("active"));
    btn.classList.add("active");
    const tab = btn.dataset.tab;
    document.querySelectorAll(".tab-panel").forEach(p => p.classList.add("hidden"));
    el("tab-" + tab).classList.remove("hidden");
    if (tab === "browse") loadEvidence();
    if (tab === "users") loadUsers();
  });
});

/* ---------------- submit evidence ---------------- */
el("evidence-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const form = e.target;
  const fd = new FormData();
  const meta = {};
  ["case_id", "operation_id", "title", "source_type", "classification", "platform", "author_handle", "source_url", "description", "chain_of_custody_note"].forEach(k => {
    const v = form.elements[k]?.value?.trim();
    if (v) meta[k] = v;
  });
  const tags = form.elements["tags"].value.trim();
  if (tags) meta.tags = tags.split(",").map(t => t.trim()).filter(Boolean);
  fd.append("metadata", JSON.stringify(meta));
  for (const f of form.elements["files"].files) fd.append("files", f);
  const out = el("submit-result");
  out.textContent = "Committing...";
  try {
    const blk = await api("/evidence", { method: "POST", body: fd });
    out.innerHTML = `<span class="ok">✔ Committed block #${blk.index}</span>\nBlock ID: <span class="mono">${blk.block_id}</span>\nMerkle root: <span class="mono">${short(blk.merkle_root)}</span>\nSignature: <span class="mono">${short(blk.signature)}</span>`;
    form.reset();
  } catch (err) {
    out.innerHTML = `<span class="bad">✘ ${esc(err.message)}</span>` +
      (err.data?.details ? "\n- " + err.data.details.map(esc).join("\n- ") : "");
  }
});

/* ---------------- browse ---------------- */
el("search-btn").addEventListener("click", loadEvidence);
el("refresh-btn").addEventListener("click", () => { el("f-case").value = ""; el("f-q").value = ""; el("f-source").value = ""; loadEvidence(); });

async function loadEvidence() {
  const params = new URLSearchParams();
  if (el("f-case").value) params.set("case_id", el("f-case").value);
  if (el("f-q").value) params.set("q", el("f-q").value);
  if (el("f-source").value) params.set("source_type", el("f-source").value);
  const list = el("evidence-list");
  list.innerHTML = "Loading...";
  try {
    const items = await api("/evidence?" + params.toString());
    if (!items.length) { list.innerHTML = "<p class='subtitle'>No evidence found.</p>"; return; }
    list.innerHTML = "";
    items.forEach(b => {
      const m = b.payload.metadata || {};
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `<h4>${esc(m.title || "(untitled)")}</h4>
        <div class="meta">
          <span class="pill">${esc(b.block_type)}</span>
          <span class="pill">${esc(m.source_type || "?")}</span>
          <span class="pill">${esc(m.classification || "")}</span>
          <span>case: ${esc(m.case_id || "")}</span>
          <span>by ${esc(b.collector_username)}</span>
          <span>${esc((b.timestamp || {}).iso || "")}</span>
          <span>${b.payload.item_count} file(s)</span>
        </div>`;
      div.addEventListener("click", () => showBlock(b.block_id));
      list.appendChild(div);
    });
  } catch (err) { list.innerHTML = `<span class="bad">${esc(err.message)}</span>`; }
}

async function showBlock(id) {
  try {
    const b = await api("/evidence/" + id);
    const m = b.payload.metadata || {};
    let html = `<h2>${esc(m.title || "Evidence")}</h2>
      <p class="subtitle">Block #${b.index} · ${esc(b.block_type)} · by ${esc(b.collector_username)}</p>
      <table>
        <tr><th>Block ID</th><td class="mono">${esc(b.block_id)}</td></tr>
        <tr><th>Case</th><td>${esc(m.case_id || "")}</td></tr>
        <tr><th>Source</th><td>${esc(m.source_type || "")} ${m.platform ? "· " + esc(m.platform) : ""}</td></tr>
        <tr><th>Classification</th><td>${esc(m.classification || "")}</td></tr>
        <tr><th>Captured</th><td>${esc(b.timestamp.iso)} <span class="pill">auth: ${esc(b.timestamp.authority)}</span></td></tr>
        <tr><th>Merkle root</th><td class="mono">${esc(b.merkle_root || "")}</td></tr>
        <tr><th>Block hash</th><td class="mono">${esc(b.block_hash)}</td></tr>
        <tr><th>Signature</th><td class="mono">${short(b.signature)}</td></tr>
        ${m.source_url ? `<tr><th>Source URL</th><td><a href="${esc(m.source_url)}" target="_blank" rel="noopener">${esc(m.source_url)}</a></td></tr>` : ""}
        ${m.description ? `<tr><th>Description</th><td>${esc(m.description)}</td></tr>` : ""}
      </table>
      <h3>Files</h3><table>`;
    b.payload.items.forEach(it => {
      const canExport = ME.role !== "viewer";
      html += `<tr><td>${esc(it.original_filename)}</td>
        <td class="mono">${short(it.file_hash)}</td>
        <td>${(it.size/1024).toFixed(1)} KB</td>
        <td>${canExport ? `<a href="${API}/evidence/${b.block_id}/download/${it.file_hash}?token=${TOKEN}">download</a>` : ""}</td></tr>`;
    });
    html += "</table>";
    if (b.derived && b.derived.length) {
      html += "<h3>Derived artifacts</h3><table>";
      b.derived.forEach(d => {
        html += `<tr><td>${esc(d.payload.derivation_type)}</td><td>${esc((d.payload.metadata||{}).title||"")}</td><td class="mono">${short(d.block_id)}</td></tr>`;
      });
      html += "</table>";
    }
    el("modal-content").innerHTML = html;
    el("modal").classList.remove("hidden");
  } catch (err) { alert(err.message); }
}
el("modal-close").addEventListener("click", () => el("modal").classList.add("hidden"));
el("modal").addEventListener("click", (e) => { if (e.target.id === "modal") el("modal").classList.add("hidden"); });

/* ---------------- verify ---------------- */
el("verify-btn").addEventListener("click", async () => {
  const out = el("verify-result");
  out.textContent = "Verifying...";
  try {
    const r = await api("/chain/verify");
    if (r.valid) out.innerHTML = `<span class="ok">✔ Chain is VALID</span>\nHeight: ${r.height} · Blocks checked: ${r.checked}`;
    else out.innerHTML = `<span class="bad">✘ Chain INVALID (${r.errors.length} issue(s))</span>\n- ` + r.errors.map(esc).join("\n- ");
  } catch (err) { out.innerHTML = `<span class="bad">${esc(err.message)}</span>`; }
});
el("verify-file-btn").addEventListener("click", async () => {
  const out = el("verify-file-result");
  const h = el("verify-hash").value.trim();
  if (!h) return;
  out.textContent = "Checking...";
  try {
    const r = await api("/verify/file/" + h);
    if (r.intact) out.innerHTML = `<span class="ok">✔ File INTACT — matches on-chain hash</span>`;
    else out.innerHTML = `<span class="bad">✘ ${r.found ? "TAMPERED / mismatch" : "Not found / missing"}</span>\nActual: <span class="mono">${esc(r.actual_hash||"")}</span>`;
  } catch (err) { out.innerHTML = `<span class="bad">${esc(err.message)}</span>`; }
});

/* ---------------- audit ---------------- */
el("audit-btn").addEventListener("click", loadAudit);
async function loadAudit() {
  const params = new URLSearchParams();
  if (el("audit-target").value) params.set("target_block_id", el("audit-target").value);
  const list = el("audit-list");
  list.innerHTML = "Loading...";
  try {
    const items = await api("/audit?" + params.toString());
    if (!items.length) { list.innerHTML = "<p class='subtitle'>No audit records.</p>"; return; }
    list.innerHTML = "";
    items.reverse().forEach(b => {
      const p = b.payload;
      const div = document.createElement("div");
      div.className = "item";
      div.innerHTML = `<div class="meta">
        <span class="pill">${esc(p.action)}</span>
        <span>by ${esc(b.collector_username)}</span>
        <span>target: <span class="mono">${short(p.target_block_id)}</span></span>
        <span>${esc(b.timestamp.iso)}</span>
      </div>`;
      list.appendChild(div);
    });
  } catch (err) { list.innerHTML = `<span class="bad">${esc(err.message)}</span>`; }
}

/* ---------------- users ---------------- */
el("user-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const f = e.target;
  const body = {
    username: f.elements.username.value,
    password: f.elements.password.value,
    full_name: f.elements.full_name.value,
    role: f.elements.role.value,
  };
  const cases = f.elements.cases.value.trim();
  if (cases) body.cases = cases.split(",").map(c => c.trim()).filter(Boolean);
  const out = el("user-result");
  try {
    await api("/users", { method: "POST", body: JSON.stringify(body) });
    out.innerHTML = `<span class="ok">✔ User created</span>`;
    f.reset(); loadUsers();
  } catch (err) { out.innerHTML = `<span class="bad">${esc(err.message)}</span>`; }
});
async function loadUsers() {
  const list = el("user-list");
  list.innerHTML = "Loading...";
  try {
    const users = await api("/users");
    list.innerHTML = "<table><tr><th>User</th><th>Role</th><th>Cases</th><th>Public key</th><th>Active</th><th></th></tr>" +
      users.map(u => `<tr>
        <td>${esc(u.username)}<br><span class="subtitle">${esc(u.full_name||"")}</span></td>
        <td><span class="badge ${esc(u.role)}">${esc(u.role)}</span></td>
        <td>${esc((u.cases||[]).join(", "))}</td>
        <td class="mono">${short(u.public_key)}</td>
        <td>${u.active ? "yes" : "no"}</td>
        <td><button class="secondary" data-uid="${u.id}" data-act="${u.active?'deactivate':'activate'}">${u.active?'deactivate':'activate'}</button></td>
      </tr>`).join("") + "</table>";
    list.querySelectorAll("button[data-uid]").forEach(btn => {
      btn.addEventListener("click", async () => {
        await api("/users/" + btn.dataset.uid, { method: "PATCH", body: JSON.stringify({ active: btn.dataset.act === "activate" }) });
        loadUsers();
      });
    });
  } catch (err) { list.innerHTML = `<span class="bad">${esc(err.message)}</span>`; }
}

/* ---------------- boot ---------------- */
(async function boot() {
  if (TOKEN) {
    try { ME = await api("/auth/me"); enterApp(); }
    catch { TOKEN = null; localStorage.removeItem("osint_token"); }
  }
})();
