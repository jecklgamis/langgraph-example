"""
Entry point for LangGraph Platform.
The platform injects its own checkpointer and serves the graph via its REST API.
MCP tools are skipped here since they require a separately running MCP server.
"""
from agent import build_app
from functions.config import get_local_tools

graph = build_app(get_local_tools())
