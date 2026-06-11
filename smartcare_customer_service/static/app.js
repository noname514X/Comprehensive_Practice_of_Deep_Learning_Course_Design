const sessionId = `demo-${new Date().toISOString().slice(0, 10)}`;

const messagesEl = document.querySelector("#messages");
const formEl = document.querySelector("#chatForm");
const inputEl = document.querySelector("#messageInput");
const traceBox = document.querySelector("#traceBox");
const toolBox = document.querySelector("#toolBox");
const citationBox = document.querySelector("#citationBox");

function appendMessage(role, content, meta = {}) {
  const node = document.createElement("div");
  node.className = `message ${role}`;
  node.textContent = content;
  if (role === "assistant" && meta.intent) {
    const metaNode = document.createElement("div");
    metaNode.className = "message-meta";
    metaNode.textContent = `意图：${meta.intent} · 情绪：${meta.emotion} · 置信度：${Number(meta.confidence).toFixed(2)}`;
    node.appendChild(metaNode);
  }
  messagesEl.appendChild(node);
  messagesEl.scrollTop = messagesEl.scrollHeight;
}

function renderTrace(trace) {
  traceBox.classList.remove("empty");
  traceBox.innerHTML = "";
  (trace || []).forEach((item) => {
    const line = document.createElement("span");
    line.textContent = item;
    traceBox.appendChild(line);
  });
}

function renderTool(toolCall) {
  toolBox.textContent = toolCall ? JSON.stringify(toolCall, null, 2) : "暂无";
}

function renderCitations(citations) {
  citationBox.innerHTML = "";
  if (!citations || citations.length === 0) {
    citationBox.className = "citations empty";
    citationBox.textContent = "暂无引用";
    return;
  }
  citationBox.className = "citations";
  citations.forEach((item) => {
    const node = document.createElement("div");
    node.className = "citation";
    node.innerHTML = `<strong>${item.source} / ${item.section} / score ${item.score}</strong><p>${item.text.slice(0, 120)}...</p>`;
    citationBox.appendChild(node);
  });
}

async function sendMessage(message) {
  if (!message.trim()) return;
  appendMessage("user", message);
  inputEl.value = "";
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
  });
  const data = await response.json();
  appendMessage("assistant", data.answer, data);
  renderTrace(data.trace);
  renderTool(data.tool_call);
  renderCitations(data.citations);
  refreshMetrics();
}

async function refreshMetrics() {
  const response = await fetch("/api/metrics");
  const data = await response.json();
  document.querySelector("#metricMessages").textContent = data.messages;
  document.querySelector("#metricSessions").textContent = data.sessions;
  document.querySelector("#metricTickets").textContent = data.tickets;
}

async function loadHealth() {
  const response = await fetch("/api/health");
  const data = await response.json();
  document.querySelector("#healthText").textContent = `知识库已加载 ${data.chunks} 个知识块`;
}

formEl.addEventListener("submit", (event) => {
  event.preventDefault();
  sendMessage(inputEl.value);
});

document.querySelectorAll(".scenario").forEach((button) => {
  button.addEventListener("click", () => sendMessage(button.dataset.message));
});

document.querySelector("#resetBtn").addEventListener("click", async () => {
  await fetch("/api/reset", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ session_id: sessionId }),
  });
  messagesEl.innerHTML = "";
  renderTrace([]);
  renderTool(null);
  renderCitations([]);
  refreshMetrics();
});

appendMessage("assistant", "您好，我是 SmartCare 智能客服。您可以咨询订单物流、退换货、产品参数、保修政策，也可以直接输入演示问题。", {
  intent: "greeting",
  emotion: "neutral",
  confidence: 1,
});
loadHealth();
refreshMetrics();
