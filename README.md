# langgraph-example

An langgraph agent example.

## What's In The Box?
* Function calls
* Multiple MCP connections
* Configurable LLM providers (Ollama, Gemini, OpenAPI, etc.). Uses Ollama by default.

## Getting started
Install required Python modules

```bash
pip install -r requirements.txt
```

This uses Ollama as default LLM provider. Ensure Ollama it is up and running. If you're using a different provider,
export the appropriate API key before running `run-agent.sh`
```bash
export OPENAI_API_KEY=some-api-key
./run-agent.sh
```

## Using MCP Servers
in `mcp_servers/example directory`, run

```bash
./run-server.sh
```

Re-run `run-agent.sh`

