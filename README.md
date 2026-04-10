# langgraph-example

A LangGraph agent with local function tools, guardrails, memory, human-in-the-loop, and optional MCP server connections.

## Features

- Local tools: filesystem, network, web search, math, bash
- Optional MCP server connections (math, perf)
- Configurable LLM providers: Ollama (default), OpenAI, Gemini, OpenRouter
- Conversation memory via LangGraph checkpointing (SQLite)
- Guardrails: input validation, LLM-as-judge, output PII redaction, bash command denylist
- Human-in-the-loop tool call confirmation
- Graceful error handling for LLM connection failures
- HTTP API via FastAPI with streaming support
- Playground UI at `/playground`
- React frontend under `frontend/`
- LangSmith tracing support

## Getting Started

```bash
pip install -r requirements.txt
./run-agent.sh
```

For a different LLM provider:

```bash
export OPENAI_API_KEY=your-api-key
LLM_PROVIDER=openai ./run-agent.sh
```

## HTTP API

```bash
python server_api.py

# Single response
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "what is 2 + 2?", "thread_id": "session-1"}'

# Streaming response
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "list files in /tmp", "thread_id": "session-1"}'
```

Use the same `thread_id` across requests to maintain conversation history.

## React Frontend

```bash
cd frontend
npm install
npm run dev   # http://localhost:5173
```

Requires `server_api.py` running on port 8000. Vite proxies `/chat` to the backend automatically.

## MCP Servers

```bash
./mcp_servers/example/run-mcp-server.sh
./run-agent.sh
```

## Environment Variables

| Variable             | Default              | Purpose                                           |
|----------------------|----------------------|---------------------------------------------------|
| `LLM_PROVIDER`       | `ollama`             | LLM backend                                       |
| `LLM_MODEL`          | _(provider default)_ | Override the model name for the selected provider |
| `OPENAI_API_KEY`     | —                    | Required when using `openai`                      |
| `GEMINI_API_KEY`     | —                    | Required when using `gemini`                      |
| `GUARDRAILS_ENABLED` | `false`              | Enable input/output guardrails                    |
| `HUMAN_IN_LOOP`      | `false`              | Prompt user to confirm tool calls before exec     |
| `LANGCHAIN_API_KEY`  | —                    | Enables LangSmith tracing when set                |
