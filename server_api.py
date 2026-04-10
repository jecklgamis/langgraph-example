import logging
from contextlib import AsyncExitStack, asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel

from agent import build_app, human_in_loop_enabled, load_mcp_tools_from_servers
from functions.config import get_local_tools
from functions.guardrails import (
    GuardrailError,
    guardrails_enabled,
    is_safe,
    validate_input,
    validate_output,
)
from tracing import setup_tracing

logger = logging.getLogger(__name__)

_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    setup_tracing()
    async with AsyncExitStack() as stack:
        checkpointer = await stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string("checkpoints.db")
        )
        mcp_tools = await load_mcp_tools_from_servers(stack)
        _agent = build_app(
            get_local_tools() + mcp_tools,
            checkpointer=checkpointer,
            human_in_loop=human_in_loop_enabled(),
        )
        yield


app = FastAPI(title="LangGraph Agent", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    user_id: str = "anonymous"
    session_metadata: dict = {}


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    user_id: str


async def check_guardrails(message: str) -> None:
    if not guardrails_enabled():
        return
    try:
        validate_input(message)
    except GuardrailError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not await is_safe(message):
        raise HTTPException(status_code=400, detail="Input flagged as unsafe.")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Returns the final agent reply."""
    await check_guardrails(request.message)
    inputs = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": request.user_id,
        "session_metadata": request.session_metadata,
    }
    config = {"configurable": {"thread_id": request.thread_id}}
    result = await _agent.ainvoke(inputs, config=config)
    response = result["messages"][-1].content
    return ChatResponse(
        response=validate_output(response) if guardrails_enabled() else response,
        thread_id=request.thread_id,
        user_id=request.user_id,
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streams tokens as they are generated."""
    await check_guardrails(request.message)

    async def generate():
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": request.user_id,
            "session_metadata": request.session_metadata,
        }
        config = {"configurable": {"thread_id": request.thread_id}}
        try:
            async for event in _agent.astream_events(
                inputs, config=config, version="v2"
            ):
                if event["event"] == "on_chat_model_stream":
                    chunk = event["data"]["chunk"]
                    if isinstance(chunk.content, str) and chunk.content:
                        content = chunk.content
                        yield (
                            validate_output(content)
                            if guardrails_enabled()
                            else content
                        )
        except Exception as e:
            logger.error("Stream error: %s", e)
            yield f"\n[Error: {e}]"

    return StreamingResponse(generate(), media_type="text/plain")


@app.get("/playground", response_class=HTMLResponse)
async def playground():
    """Simple chat playground UI."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>LangGraph Agent Playground</title>
  <style>
    * { box-sizing: border-box; margin: 0; padding: 0; }
    body { font-family: system-ui, sans-serif; background: #f5f5f5; display: flex; justify-content: center; padding: 40px 16px; }
    .container { width: 100%; max-width: 760px; }
    h1 { font-size: 1.4rem; margin-bottom: 20px; color: #111; }
    .config { display: flex; gap: 10px; margin-bottom: 14px; }
    .config input { flex: 1; padding: 8px 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 0.85rem; }
    .messages { background: #fff; border: 1px solid #ddd; border-radius: 8px; padding: 16px; min-height: 400px; max-height: 540px; overflow-y: auto; margin-bottom: 14px; display: flex; flex-direction: column; gap: 12px; }
    .msg { padding: 10px 14px; border-radius: 8px; max-width: 85%; line-height: 1.5; font-size: 0.9rem; white-space: pre-wrap; word-break: break-word; }
    .msg.user { background: #0070f3; color: #fff; align-self: flex-end; }
    .msg.agent { background: #f0f0f0; color: #111; align-self: flex-start; }
    .msg.error { background: #fee; color: #c00; align-self: flex-start; }
    .input-row { display: flex; gap: 10px; }
    textarea { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 6px; font-size: 0.9rem; resize: none; height: 60px; font-family: inherit; }
    button { padding: 0 20px; background: #0070f3; color: #fff; border: none; border-radius: 6px; font-size: 0.9rem; cursor: pointer; }
    button:disabled { background: #aaa; cursor: not-allowed; }
    .thinking { color: #999; font-style: italic; font-size: 0.85rem; }
  </style>
</head>
<body>
<div class="container">
  <h1>LangGraph Agent Playground</h1>
  <div class="config">
    <input id="threadId" placeholder="Thread ID (default)" value="playground" />
    <input id="userId" placeholder="User ID (anonymous)" value="user" />
  </div>
  <div class="messages" id="messages"></div>
  <div class="input-row">
    <textarea id="input" placeholder="Type a message and press Enter or click Send..." onkeydown="handleKey(event)"></textarea>
    <button id="sendBtn" onclick="send()">Send</button>
  </div>
</div>
<script>
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
</script>
</body>
</html>
"""


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    uvicorn.run(app, host="0.0.0.0", port=8000)
