const API = "/api/v1";
let sessionId = localStorage.getItem("darukaa_session") || null;

const messagesEl = document.getElementById("messages");
const stateEl = document.getElementById("state");
const evidenceEl = document.getElementById("evidence");
const pipelineEl = document.getElementById("pipeline");
const inputEl = document.getElementById("input");
const welcomeEl = document.getElementById("welcome");
const sessionStatusEl = document.getElementById("session-status");
const turnCountEl = document.getElementById("turn-count");
const sendButton = document.getElementById("send-button");
const profileCountEl = document.getElementById("profile-count");
const evidenceCountEl = document.getElementById("evidence-count");
const reasoningCardEl = document.getElementById("reasoning-card");
const recommendationsCardEl = document.getElementById("recommendations-card");
const reasoningEl = document.getElementById("reasoning");
const recommendationsEl = document.getElementById("recommendations");

const escapeHtml = (value) => String(value ?? "")
  .replaceAll("&", "&amp;")
  .replaceAll("<", "&lt;")
  .replaceAll(">", "&gt;")
  .replaceAll('"', "&quot;")
  .replaceAll("'", "&#039;");

function setStatus(label, active = false) {
  sessionStatusEl.innerHTML = `<span class="status-dot${active ? " active" : ""}"></span>${escapeHtml(label)}`;
}

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = `msg ${role}`;
  const label = role === "user" ? "You" : "Darukaa";
  div.innerHTML = `<div class="message-label">${label}<span>${role === "user" ? "FIELD NOTE" : "ANALYSIS"}</span></div><div class="message-copy"></div>`;
  div.querySelector(".message-copy").textContent = text;
  messagesEl.appendChild(div);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  welcomeEl.classList.add("hidden");
  updateTurnCount();
  return div;
}

function formatState(state) {
  const groups = [
    ["Soil", [["Organic carbon", state?.soil?.organic_carbon_pct], ["pH", state?.soil?.ph], ["Moisture", state?.soil?.moisture]]],
    ["Land & climate", [["Crop", state?.land?.crop], ["Cropping system", state?.land?.cropping_system], ["Rainfall", state?.climate?.rainfall], ["Fragmentation", state?.land?.fragmentation]]],
    ["Biodiversity & pressure", [["Species richness", state?.biodiversity?.species_richness], ["Habitat diversity", state?.biodiversity?.habitat_diversity], ["Pollution", state?.human_impact?.pollution], ["Deforestation", state?.human_impact?.deforestation]]],
  ];
  const known = groups.flatMap(([, fields]) => fields).filter(([, value]) => value?.value !== undefined);
  profileCountEl.textContent = `${known.length} known`;
  if (!known.length) return '<p class="empty-state">Your observed conditions will settle here as we talk.</p>';
  return groups.map(([title, fields]) => {
    const visible = fields.filter(([, value]) => value?.value !== undefined);
    if (!visible.length) return "";
    return `<div class="state-group"><h3>${title}</h3>${visible.map(([label, value]) => `<div class="state-row"><span>${label}</span><strong>${escapeHtml(value.value)}${value.unit ? ` <small>${escapeHtml(value.unit)}</small>` : ""}</strong></div>`).join("")}</div>`;
  }).join("");
}

function renderEvidence(items) {
  evidenceCountEl.textContent = `${items?.length || 0} source${items?.length === 1 ? "" : "s"}`;
  if (!items || !items.length) {
    evidenceEl.innerHTML = '<p class="empty-state">Retrieved sources will appear after the assessment has enough context.</p>';
    return;
  }
  evidenceEl.innerHTML = items
    .map(
      (item, i) => `<article class="evidence-item"><div class="evidence-index">0${i + 1}</div><div><strong>${escapeHtml(item.title)}</strong><span class="evidence-meta">${escapeHtml(item.publisher || item.source || "Source")} ${item.year || ""}</span><em>${escapeHtml((item.text || "").slice(0, 220))}${item.text?.length > 220 ? "..." : ""}</em></div></article>`
    )
    .join("");
}

function renderReasoning(reasoning) {
  if (!reasoning) { reasoningCardEl.classList.add("hidden"); return; }
  reasoningCardEl.classList.remove("hidden");
  reasoningEl.innerHTML = `<p class="mini-label">ACTIVATED VARIABLES</p><div class="tag-list">${(reasoning.activated_variables || []).map((item) => `<span>${escapeHtml(item.split(".").pop().replaceAll("_", " "))}</span>`).join("")}</div><p class="mini-label pathway-label">PATHWAYS</p>${(reasoning.pathways || []).slice(0, 3).map((path) => `<div class="pathway">${path.map((step) => `<span>${escapeHtml(step.replaceAll("_", " "))}</span>`).join("<b>&rarr;</b>")}</div>`).join("")}`;
}

function renderRecommendations(items) {
  if (!items?.length) { recommendationsCardEl.classList.add("hidden"); return; }
  recommendationsCardEl.classList.remove("hidden");
  recommendationsEl.innerHTML = items.map((item, index) => `<article class="recommendation-item"><span class="recommendation-number">0${index + 1}</span><div><strong>${escapeHtml(item.action)}</strong><p>${escapeHtml(item.time_horizon)} <span class="confidence">${escapeHtml(item.confidence)}</span></p></div></article>`).join("");
}

function renderPipeline(pipeline) {
  pipelineEl.innerHTML = (pipeline || []).map((step, index) => `<span class="pipeline-step done"><i>${index + 1}</i>${escapeHtml(step)}</span>`).join('<b class="pipeline-arrow">&#8594;</b>');
}

function updateTurnCount() {
  const count = messagesEl.querySelectorAll(".msg.user").length;
  turnCountEl.textContent = `${count} turn${count === 1 ? "" : "s"}`;
}

function showThinking() {
  const thinking = document.createElement("div");
  thinking.className = "msg assistant thinking";
  thinking.innerHTML = '<div class="message-label">Darukaa<span>WORKING</span></div><div class="thinking-dots"><i></i><i></i><i></i><span>Reading the current landscape...</span></div>';
  messagesEl.appendChild(thinking);
  messagesEl.scrollTop = messagesEl.scrollHeight;
  setStatus("Analyzing", true);
  return thinking;
}

async function ensureSession() {
  if (sessionId) return sessionId;
  const res = await fetch(`${API}/session`, { method: "POST", headers: { "Content-Type": "application/json" }, body: "{}" });
  const data = await res.json();
  sessionId = data.session_id;
  localStorage.setItem("darukaa_session", sessionId);
  return sessionId;
}

async function restoreSession() {
  if (!sessionId) return;
  try {
    const res = await fetch(`${API}/session/${sessionId}`);
    if (!res.ok) throw new Error("session unavailable");
    const data = await res.json();
    (data.messages || []).forEach((message) => addMessage(message.role, message.content));
    stateEl.innerHTML = formatState(data.environmental_state);
  } catch (error) {
    localStorage.removeItem("darukaa_session");
    sessionId = null;
  }
}

document.getElementById("new-session").onclick = async () => {
  localStorage.removeItem("darukaa_session");
  sessionId = null;
  messagesEl.innerHTML = "";
  stateEl.innerHTML = '<p class="empty-state">Your observed conditions will settle here as we talk.</p>';
  evidenceEl.innerHTML = '<p class="empty-state">Retrieved sources will appear after the assessment has enough context.</p>';
  evidenceCountEl.textContent = "0 sources";
  profileCountEl.textContent = "0 known";
  pipelineEl.innerHTML = "";
  reasoningCardEl.classList.add("hidden");
  recommendationsCardEl.classList.add("hidden");
  welcomeEl.classList.remove("hidden");
  updateTurnCount();
  setStatus("Ready");
  await ensureSession();
};

document.getElementById("composer").onsubmit = async (event) => {
  event.preventDefault();
  const text = inputEl.value.trim();
  if (!text) return;
  addMessage("user", text);
  inputEl.value = "";
  inputEl.disabled = true;
  sendButton.disabled = true;
  const thinking = showThinking();
  const sid = await ensureSession();
  let environment = null;
  if (text.startsWith("{")) {
    try { environment = JSON.parse(text); } catch (err) { environment = null; }
  }
  try {
    const res = await fetch(`${API}/agent/query`, { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify({ session_id: sid, message: text, environment }) });
    if (!res.ok) throw new Error("The agent could not complete this turn.");
    const data = await res.json();
    sessionId = data.session_id;
    localStorage.setItem("darukaa_session", sessionId);
    thinking.remove();
    addMessage("assistant", data.message || JSON.stringify(data, null, 2));
    stateEl.innerHTML = formatState(data.environmental_state);
    renderEvidence(data.evidence);
    renderPipeline(data.pipeline);
    renderReasoning(data.reasoning);
    renderRecommendations(data.recommendations);
    setStatus(data.status === "recommendation_ready" ? "Assessment ready" : "More detail needed");
  } catch (error) {
    thinking.remove();
    addMessage("assistant", error.message || "Something went wrong. Please try again.");
    setStatus("Connection issue");
  } finally {
    inputEl.disabled = false;
    sendButton.disabled = false;
    inputEl.focus();
  }
};

document.querySelectorAll(".prompt-chip").forEach((button) => button.addEventListener("click", () => { inputEl.value = button.dataset.prompt; inputEl.focus(); }));
inputEl.addEventListener("keydown", (event) => { if (event.key === "Enter" && !event.shiftKey) { event.preventDefault(); document.getElementById("composer").requestSubmit(); } });
restoreSession().then(ensureSession);
