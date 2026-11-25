const chatMessages = document.getElementById("chat-messages");
const chatForm = document.getElementById("chat-form");
const chatInput = document.getElementById("chat-input");
const sendBtn = document.getElementById("send-btn");

let selectedAgent = "";

// Load initial system status
async function loadStatus() {
  try {
    const res = await fetch("/api/status");
    const data = await res.json();
    document.getElementById("stat-rows").textContent = `${data.dataset.rows.toLocaleString()} orders`;
    document.getElementById("stat-ontime").textContent = `${data.dataset.on_time_delivery_pct}%`;
    document.getElementById("stat-delayed").textContent = data.dataset.delayed_orders;
    document.getElementById("stat-ai").textContent =
      data.ai.gemini_configured ? `Gemini (${data.ai.model})` : "Offline Fallback";
  } catch (err) {
    document.getElementById("stat-rows").textContent = "Error";
  }
}

// Agent selector buttons
document.querySelectorAll(".agent-pill").forEach((btn) => {
  btn.addEventListener("click", () => {
    document.querySelectorAll(".agent-pill").forEach((b) => b.classList.remove("active"));
    btn.classList.add("active");
    selectedAgent = btn.dataset.agent || "";
  });
});

// Quick query buttons
document.querySelectorAll(".quick-btn").forEach((btn) => {
  btn.addEventListener("click", () => {
    chatInput.value = btn.dataset.query;
    chatForm.dispatchEvent(new Event("submit"));
  });
});

function appendUserMessage(text) {
  const div = document.createElement("div");
  div.className = "message user-message";
  div.textContent = text;
  chatMessages.appendChild(div);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function formatKey(key) {
  return key.replace(/_/g, " ");
}

function renderComputedBlock(computed) {
  const block = document.createElement("div");
  block.className = "provenance-block block-computed";

  const title = document.createElement("div");
  title.className = "block-title";
  title.textContent = "🟢 [COMPUTED] Verified Dataset Calculations";
  block.appendChild(title);

  const scalars = [];
  const complex = {};

  for (const [k, v] of Object.entries(computed)) {
    if (v === null || typeof v !== "object") {
      scalars.push([k, v]);
    } else {
      complex[k] = v;
    }
  }

  if (scalars.length > 0) {
    const grid = document.createElement("div");
    grid.className = "computed-grid";
    scalars.slice(0, 12).forEach(([k, v]) => {
      const card = document.createElement("div");
      card.className = "metric-card";
      card.innerHTML = `<div class="metric-key">${formatKey(k)}</div><div class="metric-val">${v}</div>`;
      grid.appendChild(card);
    });
    block.appendChild(grid);
  }

  if (Object.keys(complex).length > 0) {
    const details = document.createElement("details");
    details.className = "computed-details";
    const summary = document.createElement("summary");
    summary.textContent = `View detailed breakdown (${Object.keys(complex).join(", ")})`;
    const pre = document.createElement("pre");
    pre.textContent = JSON.stringify(complex, null, 2);
    details.appendChild(summary);
    details.appendChild(pre);
    block.appendChild(details);
  }

  return block;
}

function renderApprovalBlock(data) {
  const block = document.createElement("div");
  block.className = "provenance-block block-approval";

  const title = document.createElement("div");
  title.className = "block-title";
  title.textContent = "🟡 [REQUIRES APPROVAL] Human Decision Gate";
  block.appendChild(title);

  const desc = document.createElement("div");
  desc.textContent = data.approval_item || "Please review and approve this operational action.";
  block.appendChild(desc);

  const actions = document.createElement("div");
  actions.className = "approval-actions";

  const approveBtn = document.createElement("button");
  approveBtn.className = "btn-approve";
  approveBtn.textContent = "Approve Action";

  const rejectBtn = document.createElement("button");
  rejectBtn.className = "btn-reject";
  rejectBtn.textContent = "Reject";

  const statusLine = document.createElement("div");
  statusLine.className = "approval-status";

  async function submitDecision(decision) {
    approveBtn.disabled = true;
    rejectBtn.disabled = true;
    try {
      const res = await fetch("/api/approve", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          approval_item: data.approval_item || "Recommendation",
          decision,
          agent: data.agent,
        }),
      });
      const out = await res.json();
      statusLine.textContent =
        decision === "approved"
          ? `✅ Approved and logged at ${out.record.timestamp.slice(0, 19)}`
          : `❌ Rejected and logged at ${out.record.timestamp.slice(0, 19)}`;
    } catch (err) {
      statusLine.textContent = "⚠️ Failed to record decision.";
    }
  }

  approveBtn.addEventListener("click", () => submitDecision("approved"));
  rejectBtn.addEventListener("click", () => submitDecision("rejected"));

  actions.appendChild(approveBtn);
  actions.appendChild(rejectBtn);
  block.appendChild(actions);
  block.appendChild(statusLine);
  return block;
}

function appendAgentResponse(data) {
  const msg = document.createElement("div");
  msg.className = "message agent-message";

  const header = document.createElement("div");
  header.className = "msg-header";
  header.innerHTML = `<span class="agent-name">${data.agent}</span><span class="msg-time">${(data.timestamp || "").slice(11, 19)}</span>`;
  msg.appendChild(header);

  if (data.error) {
    const errBlock = document.createElement("div");
    errBlock.className = "provenance-block block-error";
    errBlock.innerHTML = `<div class="block-title">🔴 [ERROR]</div><div>${data.error}</div>`;
    msg.appendChild(errBlock);
  } else {
    if (data.computed && Object.keys(data.computed).length > 0) {
      msg.appendChild(renderComputedBlock(data.computed));
    }

    if (data.ai_narrative) {
      const aiBlock = document.createElement("div");
      aiBlock.className = "provenance-block block-ai";
      const modeNote = data.gemini_active ? "" : " (Offline Fallback)";
      aiBlock.innerHTML = `<div class="block-title">🔵 [AI ANALYSIS]${modeNote}</div><div class="ai-text"></div>`;
      aiBlock.querySelector(".ai-text").textContent = data.ai_narrative;
      msg.appendChild(aiBlock);
    }

    if (data.requires_approval) {
      msg.appendChild(renderApprovalBlock(data));
    }

    if (data.chart_urls && data.chart_urls.length > 0) {
      const gallery = document.createElement("div");
      gallery.className = "chart-gallery";
      data.chart_urls.forEach((url) => {
        const img = document.createElement("img");
        img.src = `${url}?t=${Date.now()}`;
        img.alt = "Generated Warehouse Chart";
        gallery.appendChild(img);
      });
      msg.appendChild(gallery);
    }
  }

  chatMessages.appendChild(msg);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

chatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const query = chatInput.value.trim();
  if (!query) return;

  appendUserMessage(query);
  chatInput.value = "";
  sendBtn.disabled = true;
  sendBtn.textContent = "...";

  try {
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        query,
        agent: selectedAgent || null,
      }),
    });
    const data = await res.json();
    appendAgentResponse(data);
  } catch (err) {
    appendAgentResponse({
      agent: "System",
      error: "Failed to reach the Control Tower API.",
    });
  } finally {
    sendBtn.disabled = false;
    sendBtn.textContent = "Send";
  }
});

loadStatus();
