const messages = document.getElementById("messages");
const input = document.getElementById("input");
const sendBtn = document.getElementById("sendBtn");

function addMessage(role, text) {
  const div = document.createElement("div");
  div.className = "msg " + role;
  div.textContent = text;
  messages.appendChild(div);
  messages.scrollTop = messages.scrollHeight;
  return div;
}

function handleKey(e) {
  if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); send(); }
}

async function send() {
  const message = input.value.trim();
  if (!message) return;
  input.value = "";
  sendBtn.disabled = true;

  addMessage("user", message);
  const agentDiv = addMessage("agent", "");
  agentDiv.classList.add("thinking");
  agentDiv.textContent = "Thinking...";

  try {
    const res = await fetch("/chat/stream", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        message,
        thread_id: document.getElementById("threadId").value || "playground",
        user_id: document.getElementById("userId").value || "user",
      }),
    });

    if (!res.ok) {
      const err = await res.json();
      agentDiv.classList.remove("thinking");
      agentDiv.classList.add("error");
      agentDiv.textContent = "Blocked: " + (err.detail || res.statusText);
      return;
    }

    agentDiv.classList.remove("thinking");
    agentDiv.textContent = "";
    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      agentDiv.textContent += decoder.decode(value);
      messages.scrollTop = messages.scrollHeight;
    }
    if (!agentDiv.textContent.trim()) agentDiv.textContent = "(no response)";
  } catch (e) {
    agentDiv.classList.add("error");
    agentDiv.textContent = "Error: " + e.message;
  } finally {
    sendBtn.disabled = false;
    input.focus();
  }
}
