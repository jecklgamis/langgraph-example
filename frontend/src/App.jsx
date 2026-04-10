import { useState, useRef, useEffect } from "react";

const styles = {
  container: {
    display: "flex",
    justifyContent: "center",
    padding: "40px 16px",
    minHeight: "100vh",
  },
  inner: {
    width: "100%",
    maxWidth: 760,
    display: "flex",
    flexDirection: "column",
    gap: 16,
  },
  title: {
    fontSize: "1.4rem",
    color: "#111",
  },
  config: {
    display: "flex",
    gap: 10,
  },
  configInput: {
    flex: 1,
    padding: "8px 10px",
    border: "1px solid #ddd",
    borderRadius: 6,
    fontSize: "0.85rem",
    outline: "none",
  },
  messages: {
    background: "#fff",
    border: "1px solid #ddd",
    borderRadius: 8,
    padding: 16,
    minHeight: 400,
    maxHeight: 540,
    overflowY: "auto",
    display: "flex",
    flexDirection: "column",
    gap: 12,
  },
  inputRow: {
    display: "flex",
    gap: 10,
  },
  textarea: {
    flex: 1,
    padding: 10,
    border: "1px solid #ddd",
    borderRadius: 6,
    fontSize: "0.9rem",
    resize: "none",
    height: 60,
    fontFamily: "inherit",
    outline: "none",
  },
  button: {
    padding: "0 20px",
    background: "#0070f3",
    color: "#fff",
    border: "none",
    borderRadius: 6,
    fontSize: "0.9rem",
    cursor: "pointer",
  },
  buttonDisabled: {
    background: "#aaa",
    cursor: "not-allowed",
  },
};

function Message({ role, text }) {
  const bubbleStyle = {
    padding: "10px 14px",
    borderRadius: 8,
    maxWidth: "85%",
    lineHeight: 1.5,
    fontSize: "0.9rem",
    whiteSpace: "pre-wrap",
    wordBreak: "break-word",
    alignSelf: role === "user" ? "flex-end" : "flex-start",
    background:
      role === "user" ? "#0070f3" : role === "error" ? "#fee" : "#f0f0f0",
    color: role === "user" ? "#fff" : role === "error" ? "#c00" : "#111",
    fontStyle: role === "thinking" ? "italic" : "normal",
    opacity: role === "thinking" ? 0.6 : 1,
  };

  return <div style={bubbleStyle}>{text || (role === "thinking" ? "Thinking..." : "")}</div>;
}

export default function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState("react-app");
  const [userId, setUserId] = useState("user");
  const messagesEndRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  async function send() {
    const message = input.trim();
    if (!message || loading) return;
    setInput("");
    setLoading(true);

    const userMsg = { role: "user", text: message, id: Date.now() };
    const agentId = Date.now() + 1;
    const thinkingMsg = { role: "thinking", text: "", id: agentId };

    setMessages((prev) => [...prev, userMsg, thinkingMsg]);

    try {
      const res = await fetch("/chat/stream", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          message,
          thread_id: threadId || "react-app",
          user_id: userId || "user",
        }),
      });

      if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        setMessages((prev) =>
          prev.map((m) =>
            m.id === agentId
              ? { ...m, role: "error", text: "Blocked: " + (err.detail || res.statusText) }
              : m
          )
        );
        return;
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let accumulated = "";

      setMessages((prev) =>
        prev.map((m) => (m.id === agentId ? { ...m, role: "agent", text: "" } : m))
      );

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        accumulated += decoder.decode(value, { stream: true });
        const current = accumulated;
        setMessages((prev) =>
          prev.map((m) => (m.id === agentId ? { ...m, text: current } : m))
        );
      }

      if (!accumulated.trim()) {
        setMessages((prev) =>
          prev.map((m) => (m.id === agentId ? { ...m, text: "(no response)" } : m))
        );
      }
    } catch (e) {
      setMessages((prev) =>
        prev.map((m) =>
          m.id === agentId ? { ...m, role: "error", text: "Error: " + e.message } : m
        )
      );
    } finally {
      setLoading(false);
    }
  }

  function handleKey(e) {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      send();
    }
  }

  return (
    <div style={styles.container}>
      <div style={styles.inner}>
        <h1 style={styles.title}>LangGraph Agent</h1>

        <div style={styles.config}>
          <input
            style={styles.configInput}
            placeholder="Thread ID"
            value={threadId}
            onChange={(e) => setThreadId(e.target.value)}
          />
          <input
            style={styles.configInput}
            placeholder="User ID"
            value={userId}
            onChange={(e) => setUserId(e.target.value)}
          />
        </div>

        <div style={styles.messages}>
          {messages.length === 0 && (
            <div style={{ color: "#999", fontSize: "0.85rem", margin: "auto" }}>
              Start a conversation...
            </div>
          )}
          {messages.map((m) => (
            <Message key={m.id} role={m.role} text={m.text} />
          ))}
          <div ref={messagesEndRef} />
        </div>

        <div style={styles.inputRow}>
          <textarea
            style={styles.textarea}
            placeholder="Type a message and press Enter..."
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKey}
            disabled={loading}
          />
          <button
            style={{ ...styles.button, ...(loading ? styles.buttonDisabled : {}) }}
            onClick={send}
            disabled={loading}
          >
            Send
          </button>
        </div>
      </div>
    </div>
  );
}
