# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the agent (interactive REPL)
./run-agent.sh
LLM_PROVIDER=openai ./run-agent.sh

# Run the MCP server (from mcp_servers/example/)
./mcp_servers/example/run-server.sh

# Run tests
pytest -s
pytest -s -k <test_name>
```

## Architecture

The project has two layers: an optional MCP **server** and a LangGraph-based **agent**.

### Agent (`agent.py`)

`agent.py` is an async interactive REPL that:
1. Attempts to connect to each MCP server listed in `mcp_servers/config.py` (skips unreachable ones)
2. Loads local function tools from `functions/config.py`
3. Builds a LangGraph `StateGraph` with an agent node and a `ToolNode`
4. Loops on `input()` and streams responses via `app.astream`

`llm_factory.py` maps the `LLM_PROVIDER` env var to the correct LangChain chat model. Supported providers: `ollama` (default, OpenAI-compat mode), `ollama_native`, `openai`, `gemini`, `openrouter`.

### Local Tools (`functions/`)

- `functions/machine.py` — filesystem and network tools (`list_files`, `read_file`, `run_df`, `run_du`, `run_hostname`, `run_ifconfig`, `run_netstat`, `get_current_user`)
- `functions/web.py` — `search_web` via DuckDuckGo
- `functions/config.py` — `get_local_tools()` returns the full list

### MCP Server (`mcp_servers/example/`)

`server.py` is a FastAPI app that mounts two independent FastMCP sub-apps:

- `/math_mcp` — served by `tools/math_tools.py`
- `/perf-mcp` — served by `tools/perf_tools.py`

Both MCP servers also expose their tools as plain FastAPI REST routes (auto-registered via a loop over the `math_tools` / `perf_tools` lists). The server runs on port `58080`.

**Pattern for adding a new tool:** define a private function `_fn(...)`, register it with `mcp.tool()(_fn)`, and append it to the module's `*_tools` list. It will then be available as both an MCP tool and a REST endpoint.

### Environment Variables

| Variable             | Default                  | Purpose                          |
|----------------------|--------------------------|----------------------------------|
| `LLM_PROVIDER`       | `ollama`                 | LLM backend for the agent        |
| `MCP_SERVER_URL`     | `http://localhost:58080`  | MCP server base URL             |
| `OPENAI_API_KEY`     | —                        | Required when using `openai`     |
| `GEMINI_API_KEY`     | —                        | Required when using `gemini`     |
| `OPENROUTER_API_KEY` | —                        | Required when using `openrouter` |
