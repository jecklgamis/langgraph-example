# langgraph-example

A LangGraph agent with local function tools, guardrails, memory, and optional MCP server connections.

## Features

- Local tools: filesystem, network, web search, math, bash
- Optional MCP server connections (math, perf)
- Configurable LLM providers: Ollama (default), OpenAI, Gemini, OpenRouter
- Conversation memory via LangGraph checkpointing
- Guardrails: input validation, LLM-as-judge, output redaction, bash command denylist
- HTTP API via FastAPI

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

Use the same `thread_id` across requests to maintain conversation history. Omit it to use the default thread.

## MCP Servers

```bash
./mcp_servers/example/run-server.sh
./run-agent.sh
```

## Environment Variables

| Variable             | Default  | Purpose                          |
|----------------------|----------|----------------------------------|
| `LLM_PROVIDER`       | `ollama` | LLM backend                      |
| `OPENAI_API_KEY`     | —        | Required when using `openai`     |
| `GEMINI_API_KEY`     | —        | Required when using `gemini`     |
| `OPENROUTER_API_KEY` | —        | Required when using `openrouter` |
