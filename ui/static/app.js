"use strict";

// ---- tiny helpers ---------------------------------------------------------
const $ = (id) => document.getElementById(id);
const el = (t, cls, txt) => { const e = document.createElement(t); if (cls) e.className = cls; if (txt != null) e.textContent = txt; return e; };
const esc = (s) => (s == null ? "" : String(s));
const SEV_ORDER = ["critical", "high", "medium", "low", "info", "informational", "unknown"];
const sevClass = (s) => "sev-" + (s || "unknown").toLowerCase();

let org = "";
const page = { findings: 0, assets: 0 };
const PAGE = 100;

async function api(path, params) {
  const u = new URL(path, location.origin);
  Object.entries(params || {}).forEach(([k, v]) => { if (v) u.searchParams.set(k, v); });
  const r = await fetch(u);
  if (!r.ok) throw new Error(`${path} → ${r.status}`);
  return r.json();
}

function banner(msg) {
  const b = $("banner");
  if (!msg) { b.style.display = "none"; return; }
  b.textContent = msg; b.style.display = "block";
}

// ---- stat tiles + bars ----------------------------------------------------
function renderTiles(s) {
  const t = $("tiles"); t.innerHTML = "";
  const sev = s.findings_by_severity || {};
  const crit = (sev.critical || 0) + (sev.high || 0);
  const tiles = [
    ["Assets", s.total_assets, null],
    ["Subdomains", (s.assets_by_type || {}).subdomain || 0, null],
    ["Live hosts", s.live_hosts, null],
    ["Open findings", s.open_findings, null],
    ["Critical + High", crit, crit > 0 ? "crit" : null],
  ];
  for (const [label, value, flag] of tiles) {
    const d = el("div", "tile");
    d.append(el("div", "label", label));
    const v = el("div", "value", String(value ?? 0));
    if (flag === "crit") v.style.color = "var(--crit)";
    d.append(v);
    t.append(d);
  }
}

function renderBars(container, data, order) {
  const c = $(container); c.innerHTML = "";
  const entries = Object.entries(data || {});
  if (!entries.length) { c.append(el("div", "muted", "No data")); return; }
  entries.sort((a, b) => {
    const ia = order ? order.indexOf(a[0].toLowerCase()) : -1;
    const ib = order ? order.indexOf(b[0].toLowerCase()) : -1;
    if (order && ia !== ib) return (ia < 0 ? 99 : ia) - (ib < 0 ? 99 : ib);
    return b[1] - a[1];
  });
  const max = Math.max(...entries.map((e) => e[1]), 1);
  for (const [name, count] of entries) {
    const row = el("div", "bar-row");
    row.append(el("div", "name", name));
    const track = el("div", "bar-track");
    const fill = el("div", "bar-fill " + sevClass(name));
    fill.style.width = (count / max * 100) + "%";
    track.append(fill);
    row.append(track);
    row.append(el("div", "num", String(count)));
    c.append(row);
  }
}

async function loadStats() {
  try {
    const s = await api("/api/stats", { org });
    renderTiles(s);
    renderBars("sevBars", s.findings_by_severity, SEV_ORDER);
    const combined = {};
    Object.entries(s.findings_by_status || {}).forEach(([k, v]) => combined[k] = v);
    renderBars("statusBars", s.findings_by_type || {});
  } catch (e) { banner("Cannot load stats: " + e.message); }
}

// ---- tables ---------------------------------------------------------------
function pill(text, cls) { const s = el("span", "pill " + cls, text); return s; }

async function loadFindings() {
  const params = {
    org, q: $("fSearch").value.trim(), severity: $("fSeverity").value,
    status: $("fStatus").value, type: $("fType").value,
    limit: PAGE, skip: page.findings * PAGE,
  };
  try {
    const d = await api("/api/findings", params);
    const b = $("fBody"); b.innerHTML = "";
    if (!d.rows.length) { b.innerHTML = `<tr><td colspan="7" class="empty">No findings</td></tr>`; }
    for (const f of d.rows) {
      const tr = el("tr");
      const sc = el("td"); sc.append(pill(f.severity || "unknown", (f.severity || "unknown").toLowerCase())); tr.append(sc);
      tr.append(el("td", null, esc(f.title)));
      const h = el("td", "mono", esc(f.host_with_protocol || f.host)); tr.append(h);
      tr.append(el("td", null, esc(f.type)));
      const st = el("td"); st.append(pill(f.status || "Open", (f.status || "open").toLowerCase())); tr.append(st);
      tr.append(el("td", "mono", f.cve_id && f.cve_id !== "null" ? f.cve_id : "—"));
      tr.append(el("td", "mono", esc(f.tool_source)));
      b.append(tr);
    }
    $("fCount").textContent = `${d.total} findings · showing ${d.skip + 1}–${Math.min(d.skip + d.limit, d.total)}`;
    banner("");
  } catch (e) { banner("Cannot load findings: " + e.message); }
}

async function loadAssets() {
  const params = { org, q: $("aSearch").value.trim(), asset_type: $("aType").value, limit: PAGE, skip: page.assets * PAGE };
  try {
    const d = await api("/api/assets", params);
    const b = $("aBody"); b.innerHTML = "";
    if (!d.rows.length) { b.innerHTML = `<tr><td colspan="7" class="empty">No assets</td></tr>`; }
    for (const a of d.rows) {
      const tr = el("tr");
      tr.append(el("td", "mono", esc(a.asset)));
      tr.append(el("td", null, esc(a.asset_type)));
      tr.append(chips(a.ports));
      tr.append(chips(a.technologies));
      tr.append(el("td", "mono", fmt(a.waf)));
      tr.append(el("td", "mono", fmt(a.cdn_names)));
      const live = (a.active_hosts && a.active_hosts.length) ? "●" : "";
      const lc = el("td", "mono", live); lc.style.color = "var(--accent)"; tr.append(lc);
      b.append(tr);
    }
    $("aCount").textContent = `${d.total} assets · showing ${d.skip + 1}–${Math.min(d.skip + d.limit, d.total)}`;
    banner("");
  } catch (e) { banner("Cannot load assets: " + e.message); }
}

function fmt(v) {
  if (v == null || v === "" || (Array.isArray(v) && !v.length)) return "—";
  return Array.isArray(v) ? v.join(", ") : String(v);
}
function chips(v) {
  const td = el("td", "chips");
  const arr = Array.isArray(v) ? v.flat() : (v ? [v] : []);
  if (!arr.length) { td.textContent = "—"; td.className = "mono"; return td; }
  arr.slice(0, 8).forEach((x) => td.append(el("span", null, String(x))));
  if (arr.length > 8) td.append(el("span", "muted", `+${arr.length - 8}`));
  return td;
}

// ---- wiring ---------------------------------------------------------------
function debounce(fn, ms) { let t; return () => { clearTimeout(t); t = setTimeout(fn, ms); }; }

function tab(name) {
  document.querySelectorAll(".tab").forEach((t) => t.classList.toggle("active", t.dataset.tab === name));
  $("tab-findings").hidden = name !== "findings";
  $("tab-assets").hidden = name !== "assets";
}

function init() {
  document.querySelectorAll(".tab").forEach((t) => t.addEventListener("click", () => tab(t.dataset.tab)));
  $("themeBtn").addEventListener("click", () => {
    const r = document.documentElement;
    r.dataset.theme = r.dataset.theme === "dark" ? "light" : "dark";
  });
  $("refreshBtn").addEventListener("click", refreshAll);
  $("orgSelect").addEventListener("change", (e) => { org = e.target.value; page.findings = 0; page.assets = 0; refreshAll(); });

  const fReload = () => { page.findings = 0; loadFindings(); };
  $("fSearch").addEventListener("input", debounce(fReload, 300));
  ["fSeverity", "fStatus", "fType"].forEach((id) => $(id).addEventListener("change", fReload));
  $("fPrev").addEventListener("click", () => { if (page.findings > 0) { page.findings--; loadFindings(); } });
  $("fNext").addEventListener("click", () => { page.findings++; loadFindings(); });

  const aReload = () => { page.assets = 0; loadAssets(); };
  $("aSearch").addEventListener("input", debounce(aReload, 300));
  $("aType").addEventListener("change", aReload);
  $("aPrev").addEventListener("click", () => { if (page.assets > 0) { page.assets--; loadAssets(); } });
  $("aNext").addEventListener("click", () => { page.assets++; loadAssets(); });

  bootstrap();
}

async function bootstrap() {
  try {
    const orgs = await api("/api/orgs");
    const sel = $("orgSelect");
    orgs.forEach((o) => { const opt = el("option", null, o); opt.value = o; sel.append(opt); });
  } catch (e) { banner("Cannot reach Mantis API: " + e.message); }
  refreshAll();
}

function refreshAll() { loadStats(); loadFindings(); loadAssets(); }

document.addEventListener("DOMContentLoaded", init);
