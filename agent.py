import asyncio
import logging
from contextlib import AsyncExitStack

import httpx
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from functions.config import get_local_tools
from functions.guardrails import GuardrailError, is_safe, validate_input, validate_output
from functions.machine import get_current_user
from llm_factory import create_llm
from mcp_servers import mcp_servers

logger = logging.getLogger(__name__)


def build_app(tools: list):
    llm = create_llm().bind_tools(tools)

    async def call_model(state: MessagesState):
        return {"messages": [await llm.ainvoke(state["messages"])]}

    def should_call_tools(state: MessagesState):
        return "tools" if state["messages"][-1].tool_calls else END

    workflow = StateGraph(MessagesState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_call_tools)
    workflow.add_edge("tools", "agent")
    return workflow.compile(checkpointer=MemorySaver())


async def load_mcp_tools_from_servers(stack: AsyncExitStack) -> list:
    tools = []
    async with httpx.AsyncClient() as client:
        for mcp in mcp_servers:
            url = mcp["url"]
            try:
                await client.get(url, timeout=2)
            except Exception:
                logger.warning("MCP server not reachable, skipping: %s", url)
                continue
            try:
                read, write, _ = await stack.enter_async_context(
                    streamable_http_client(url)
                )
                session = await stack.enter_async_context(ClientSession(read, write))
                await session.initialize()
                tools.extend(await load_mcp_tools(session))
                logger.info("Connected to MCP: %s", url)
            except Exception as e:
                logger.warning("Could not connect to %s: %s", url, e)
    return tools


async def main():
    async with AsyncExitStack() as stack:
        mcp_tools = await load_mcp_tools_from_servers(stack)
        app = build_app(get_local_tools() + mcp_tools)

        config = {"configurable": {"thread_id": "repl"}}
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
                break
            try:
                validate_input(user_input)
            except GuardrailError as e:
                print(f"Blocked: {e}")
                continue
            if not await is_safe(user_input):
                print("Blocked: input flagged as unsafe.")
                continue
            inputs = {"messages": [HumanMessage(content=user_input)]}
            async for output in app.astream(inputs, config=config):
                for _, value in output.items():
                    content = validate_output(value["messages"][-1].content)
                    if content:
                        print(content)
                        print("---")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    print(f"Welcome to langgraph-example {get_current_user()}!")
    asyncio.run(main())
