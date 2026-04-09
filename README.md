# langgraph-example

A LangGraph agent example with local function tools and optional MCP server connections.

## What's In The Box?

- Local function tools (filesystem, network, web search)
- Multiple MCP server connections (math, perf)
- Configurable LLM providers (Ollama, OpenAI, Gemini, OpenRouter). Uses Ollama by default.
- Standard Python logging throughout

## Getting Started

Install required Python modules:

```bash
pip install -r requirements.txt
```

This uses Ollama as the default LLM provider. Ensure Ollama is up and running before starting the agent.

```bash
./run-agent.sh
```

For a different provider, export the appropriate API key first:

```bash
export OPENAI_API_KEY=your-api-key
LLM_PROVIDER=openai ./run-agent.sh
```

## Using MCP Servers

From the `mcp_servers/example` directory, start the MCP server:

```bash
./run-server.sh
```

Then run the agent — it will automatically connect to the MCP server and load its tools.

```bash
./run-agent.sh
```

## Environment Variables

| Variable             | Default                 | Purpose                          |
|----------------------|-------------------------|----------------------------------|
| `LLM_PROVIDER`       | `ollama`                | LLM backend                      |
| `MCP_SERVER_URL`     | `http://localhost:58080` | MCP server base URL             |
| `OPENAI_API_KEY`     | —                       | Required when using `openai`     |
| `GEMINI_API_KEY`     | —                       | Required when using `gemini`     |
| `OPENROUTER_API_KEY` | —                       | Required when using `openrouter` |
