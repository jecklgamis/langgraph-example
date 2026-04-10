import asyncio
import logging
import sys
from contextlib import AsyncExitStack

import httpx
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from functions.config import get_local_tools
from functions.machine import get_current_user
from llm_factory import create_llm
from mcp_servers import mcp_servers

logger = logging.getLogger(__name__)


def build_app(tools: list):
    llm = create_llm()
    llm = llm.bind_tools(tools)

    async def call_model(state: MessagesState):
        return {"messages": [await llm.ainvoke(state["messages"])]}

    def should_call_tools(state: MessagesState):
        if state["messages"][-1].tool_calls:
            return "tools"
        return END

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_call_tools)
    workflow.add_edge("tools", "agent")
    return workflow.compile()


async def is_reachable(url: str) -> bool:
    try:
        async with httpx.AsyncClient() as client:
            await client.get(url, timeout=2)
        return True
    except Exception:
        return False


async def main():
    async with AsyncExitStack() as stack:
        mcp_tools = []
        mcp_endpoints = [mcp["url"] for mcp in mcp_servers]
        for url in mcp_endpoints:
            if not await is_reachable(url):
                logger.warning("MCP server not reachable, skipping: %s", url)
                continue
            try:
                read, write, _ = await stack.enter_async_context(
                    streamable_http_client(url)
                )
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                mcp_tools.extend(await load_mcp_tools(session))
                logger.info("Connected to MCP: %s", url)
            except Exception as e:
                logger.warning("Could not connect to %s: %s", url, e)

        tools = get_local_tools() + mcp_tools
        app = build_app(tools)

        print("Type 'quit/exit/bye' to exit")
        while True:
            try:
                user_input = input("> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                print("See ya!")
                sys.exit(0)
            inputs = {"messages": [HumanMessage(content=user_input)]}
            async for output in app.astream(inputs):
                for key, value in output.items():
                    content = value["messages"][-1].content
                    if content:
                        print(content)
                        print("---")


if __name__ == "__main__":
    print(f"Welcome to langgraph-example {get_current_user()}!")
    asyncio.run(main())
