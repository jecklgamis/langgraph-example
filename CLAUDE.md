# CLAUDE.md

## Project Overview

This is a FastAPI MCP (Model Context Protocol) server built with FastMCP. It exposes math and performance testing tools over streamable-http transport on port 8080. Includes LangChain-based clients for interacting with the server via an LLM agent.

## Tech Stack

- Python 3.13+
- FastMCP
- FastAPI / Uvicorn
- LangChain / LangGraph (client)
- langchain-mcp-adapters (client)

## Project Structure

- `server.py` — FastAPI app entry point with REST routes and MCP mount
- `server/` — MCP server definitions
  - `math_tools.py` — Math MCP server with tool definitions
  - `perf_tools.py` — Perf MCP server with load testing tool
- `client/` — LangChain agent clients
  - `math_client.py` — LangChain agent client for math MCP
  - `perf_client.py` — LangChain agent client for perf MCP
  - `llm_factory.py` — LLM provider factory (ollama, openai, gemini)
- `requirements.txt` — Pinned Python dependencies
- `Dockerfile` — Container image definition (port 8080)
- `.github/workflows/build.yaml` — CI/CD pipeline (build, test, Docker push)
- `deployment/k8s/helm/mcp-server-example/` — Helm chart for Kubernetes deployment

## Running

```bash
pip install -r requirements.txt
python server.py
```

## Docker

```bash
docker build -t mcp-server-example .
docker run -p 8080:8080 mcp-server-example
```
