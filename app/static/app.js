const form = document.querySelector("#chat-form");
const promptBox = document.querySelector("#prompt");
const messages = document.querySelector("#messages");
const send = document.querySelector("#send");
let conversationId = null;

function addBubble(text, role) {
  const element = document.createElement("div");
  element.className = "bubble " + role;
  element.textContent = text;
  messages.appendChild(element);
  messages.scrollTop = messages.scrollHeight;
}

async function refreshMetrics() {
  const response = await fetch("/api/metrics");
  const metrics = await response.json();
  document.querySelector("#requests").textContent = metrics.requests;
  document.querySelector("#latency").textContent = metrics.average_latency_ms + " ms";
  document.querySelector("#input").textContent = metrics.prompt_tokens;
  document.querySelector("#output").textContent = metrics.completion_tokens;
  document.querySelector("#cost").textContent = "$" + Number(metrics.estimated_cost).toFixed(6);
}

(async () => {
  const response = await fetch("/api/health");
  const health = await response.json();
  document.querySelector("#mode").textContent = health.mode.toUpperCase() + " · " + health.model;
  await refreshMetrics();
})();

form.addEventListener("submit", async (event) => {
  event.preventDefault();
  const message = promptBox.value.trim();
  if (!message) return;

  addBubble(message, "user");
  promptBox.value = "";
  send.disabled = true;
  send.textContent = "Thinking…";

  try {
    const response = await fetch("/api/chat", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({message, conversation_id: conversationId})
    });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "Request failed");
    conversationId = data.conversation_id;
    addBubble(data.answer, "assistant");
    await refreshMetrics();
  } catch (error) {
    addBubble("Error: " + error.message, "assistant");
  } finally {
    send.disabled = false;
    send.textContent = "Send message ↗";
  }
});

document.querySelector("#clear").addEventListener("click", () => {
  conversationId = null;
  messages.replaceChildren();
  addBubble("New conversation started. What would you like to work on?", "assistant");
});
