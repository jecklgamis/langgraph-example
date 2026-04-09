# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt
# or
make install-deps

# Run the server
python config.py

# Run tests
make check        # runs: pytest -s
pytest -s -k <test_name>   # single test

# Run a client (interactive REPL)
python -m client.math_client
python -m client.perf_client
LLM_PROVIDER=openai python -m client.math_client

# Docker
make image        # build image
make run          # run container on :8080
make up           # check + image + run
```

## Architecture

The project has two layers: an MCP **server** and LangChain-based **clients**.

### Server (`server.py` + `server/`)

`server.py` is a FastAPI app that mounts two independent FastMCP sub-apps:

- `/math_mcp` — served by `server/math_tools.py`
- `/perf-mcp` — served by `server/perf_tools.py`

The MCP apps share their lifespan with the FastAPI app via a nested `asynccontextmanager`. Both MCP servers also expose their tools as plain FastAPI REST routes (auto-registered via a loop over the `math_tools` / `perf_tools` lists).

**Pattern for adding a new tool:** define a private function `_fn(...)`, register it with `mcp.tool()(_fn)`, and append it to the module's `*_tools` list. The function is then automatically available as both an MCP tool and a REST endpoint.

### Clients (`client/`)

Each client (`math_client.py`, `perf_client.py`) is an async interactive REPL that:
1. Opens a streamable-http MCP session to the server
2. Loads MCP tools via `langchain_mcp_adapters`
3. Creates a LangChain agent (`create_agent`) with those tools
4. Loops on `input()` and calls `agent.ainvoke`

`llm_factory.py` maps the `LLM_PROVIDER` env var to the correct LangChain chat model. Supported providers: `ollama` (default, OpenAI-compat mode), `ollama_native`, `openai`, `gemini`, `openrouter`.

### Environment Variables

| Variable        | Default                  | Purpose                        |
|-----------------|--------------------------|--------------------------------|
| `LLM_PROVIDER`  | `ollama`                 | LLM backend for clients        |
| `MCP_SERVER_URL`| `http://localhost:8080`  | MCP server base URL for clients|
| `OPENAI_API_KEY`| —                        | Required when using `openai`   |
| `GEMINI_API_KEY`| —                        | Required when using `gemini`   |
| `OPENROUTER_API_KEY` | —                   | Required when using `openrouter`|
