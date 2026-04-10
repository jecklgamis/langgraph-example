import asyncio
import logging
from contextlib import AsyncExitStack
from typing import Optional

import httpx
from langchain_core.messages import HumanMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from functions.config import get_local_tools
from functions.guardrails import GuardrailError, is_safe, validate_input, validate_output
from functions.machine import get_current_user
from llm_factory import create_llm
from mcp_servers import mcp_servers
from tracing import setup_tracing

logger = logging.getLogger(__name__)


class AgentState(MessagesState):
    user_id: str
    session_metadata: Optional[dict]



def build_app(tools: list, checkpointer=None, human_in_loop: bool = False):
    llm = create_llm().bind_tools(tools)

    async def call_model(state: AgentState):
        return {"messages": [await llm.ainvoke(state["messages"])]}

    def should_call_tools(state: AgentState):
        return "tools" if state["messages"][-1].tool_calls else END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_call_tools)
    workflow.add_edge("tools", "agent")
    interrupt_before = ["tools"] if human_in_loop else []
    return workflow.compile(checkpointer=checkpointer, interrupt_before=interrupt_before)


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


async def stream_tokens(app, inputs_or_command, config: dict) -> str:
    """Streams tokens from the model and returns the full response."""
    buffer = []
    async for event in app.astream_events(inputs_or_command, config=config, version="v2"):
        if event["event"] == "on_chat_model_stream":
            chunk = event["data"]["chunk"]
            if isinstance(chunk.content, str) and chunk.content:
                print(chunk.content, end="", flush=True)
                buffer.append(chunk.content)
    print()
    return validate_output("".join(buffer))


async def handle_interrupt(app, config: dict) -> None:
    """Handles human-in-the-loop interrupts: shows pending tool calls and asks for confirmation."""
    state = await app.aget_state(config)
    while state.next:
        last_msg = state.values["messages"][-1]
        print("\n[Pending tool calls]")
        for tc in last_msg.tool_calls:
            print(f"  {tc['name']}({tc['args']})")
        confirm = input("Allow? [y/N] ").strip().lower()
        if confirm == "y":
            await stream_tokens(app, Command(resume=True), config)
        else:
            tool_messages = [
                ToolMessage(content="Tool call rejected by user.", tool_call_id=tc["id"])
                for tc in last_msg.tool_calls
            ]
            await app.aupdate_state(config, {"messages": tool_messages}, as_node="tools")
            await stream_tokens(app, None, config)
        state = await app.aget_state(config)


async def main():
    setup_tracing()
    async with AsyncExitStack() as stack:
        checkpointer = await stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string("checkpoints.db")
        )
        mcp_tools = await load_mcp_tools_from_servers(stack)
        app = build_app(get_local_tools() + mcp_tools, checkpointer=checkpointer, human_in_loop=True)

        config = {"configurable": {"thread_id": "repl"}}
        inputs_base = {"user_id": get_current_user(), "session_metadata": {}}
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
            inputs = {**inputs_base, "messages": [HumanMessage(content=user_input)]}
            await stream_tokens(app, inputs, config)
            await handle_interrupt(app, config)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    print(f"Welcome to langgraph-example {get_current_user()}!")
    asyncio.run(main())
