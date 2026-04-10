# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent (interactive REPL)
./run-agent.sh
LLM_PROVIDER=openai ./run-agent.sh

# Run the agent as an HTTP API
python server_api.py

# Run the MCP server (from mcp_servers/example/)
./mcp_servers/example/run-server.sh

# Run tests
pytest -s
pytest -s -k <test_name>
```

## Architecture

The project has three entry points: an interactive REPL (`agent.py`), an HTTP API (`server_api.py`), and an optional MCP server (`mcp_servers/example/`).

### Agent (`agent.py`)

An async interactive REPL that:
1. Attempts to connect to each MCP server listed in `mcp_servers/config.py` (skips unreachable ones)
2. Loads local function tools from `functions/config.py`
3. Builds a LangGraph `StateGraph` with an agent node and a `ToolNode`
4. Loops on `input()` and streams responses via `app.astream`

### HTTP API (`server_api.py`)

A FastAPI app that wraps the same agent logic:
- `POST /chat` — returns the final agent reply as JSON
- `POST /chat/stream` — streams each agent step as plain text

The agent and MCP sessions are initialized once at startup via FastAPI lifespan and reused across requests.

### LLM Factory (`llm_factory.py`)

Maps the `LLM_PROVIDER` env var to the correct LangChain chat model. Supported providers: `ollama` (default, OpenAI-compat mode), `ollama_native`, `openai`, `gemini`, `openrouter`. Each provider has sensible defaults for `temperature` and `max_tokens`.

### Local Tools (`functions/`)

- `functions/machine.py` — filesystem and network tools (`list_files`, `read_file`, `run_df`, `run_du`, `run_hostname`, `run_ifconfig`, `run_netstat`, `get_current_user`)
- `functions/web.py` — `search` via DuckDuckGo
- `functions/math.py` — `calculate_math_expression` using safe AST evaluation (no `eval`)
- `functions/bash.py` — `run_bash` executes arbitrary shell commands with a 30s timeout
- `functions/config.py` — `get_local_tools()` returns the full list

**Pattern for adding a local tool:** define a function in the appropriate module, add it to `get_local_tools()` in `functions/config.py`.

### MCP Server (`mcp_servers/example/`)

A FastAPI app that mounts two independent FastMCP sub-apps:

- `/math_mcp` — served by `tools/math_tools.py`
- `/perf-mcp` — served by `tools/perf_tools.py`

Both MCP servers also expose their tools as plain FastAPI REST routes (auto-registered via a loop over the `math_tools` / `perf_tools` lists). The server runs on port `58080`.

**Pattern for adding an MCP tool:** define a private function `_fn(...)`, register it with `mcp.tool()(_fn)`, and append it to the module's `*_tools` list.

### Environment Variables

| Variable             | Default                  | Purpose                          |
|----------------------|--------------------------|----------------------------------|
| `LLM_PROVIDER`       | `ollama`                 | LLM backend for the agent        |
| `MCP_SERVER_URL`     | `http://localhost:58080`  | MCP server base URL             |
| `OPENAI_API_KEY`     | —                        | Required when using `openai`     |
| `GEMINI_API_KEY`     | —                        | Required when using `gemini`     |
| `OPENROUTER_API_KEY` | —                        | Required when using `openrouter` |
