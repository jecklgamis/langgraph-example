import asyncio
import json
import logging
import os
import signal
import sys
from contextlib import AsyncExitStack
from typing import Optional

import httpx
import typer
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from langgraph.graph import END, MessagesState, StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import Command
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

from functions.config import get_local_tools
from functions.guardrails import (
    GuardrailError,
    guardrails_enabled,
    validate_input,
    validate_output, is_safe,
)
from llm_factory import create_llm
from mcp_servers import mcp_servers
from tracing import setup_logging, setup_tracing

logger = logging.getLogger(__name__)


def human_in_loop_enabled() -> bool:
    return os.environ.get("HUMAN_IN_LOOP", "false").lower() != "false"


class AgentState(MessagesState):
    user_id: str
    session_metadata: Optional[dict]


def build_app(tools: list, checkpointer=None, human_in_loop: bool = False):
    llm = create_llm().bind_tools(tools)

    async def call_model(state: AgentState):
        try:
            return {"messages": [await llm.ainvoke(state["messages"])]}
        except Exception as e:
            if isinstance(e, httpx.ConnectError) or "connection" in str(e).lower():
                logger.error("Could not connect to LLM: %s", e)
                return {
                    "messages": [
                        AIMessage(content="I am unable to connect to a language model.")
                    ]
                }
            logger.error("Model invocation failed: %s", e)
            return {
                "messages": [
                    AIMessage(content=f"I'm sorry, I encountered an error: {e}")
                ]
            }

    def should_call_tools(state: AgentState):
        return "tools" if state["messages"][-1].tool_calls else END

    workflow = StateGraph(AgentState)
    workflow.add_node("agent", call_model)
    workflow.add_node("tools", ToolNode(tools))
    workflow.set_entry_point("agent")
    workflow.add_conditional_edges("agent", should_call_tools)
    workflow.add_edge("tools", "agent")
    interrupt_before = ["tools"] if human_in_loop else []
    return workflow.compile(
        checkpointer=checkpointer, interrupt_before=interrupt_before
    )


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


def _extract_text(content) -> str:
    """Normalizes LangChain message content to a plain string.

    Some providers (e.g. Anthropic) return content as a list of typed blocks
    like [{"type": "text", "text": "..."}] instead of a bare string.
    """
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            block.get("text", "")
            for block in content
            if isinstance(block, dict) and block.get("type") == "text"
        )
    return ""


async def stream_tokens(app, inputs_or_command, config: dict) -> str:
    """Streams tokens from the model and returns the full response."""
    buffer = []
    async for event in app.astream_events(
            inputs_or_command, config=config, version="v2"
    ):
        if event["event"] == "on_chat_model_stream":
            text = _extract_text(event["data"]["chunk"].content)
            if text:
                print(text, end="", flush=True)
                buffer.append(text)
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
                ToolMessage(
                    content="Tool call rejected by user.", tool_call_id=tc["id"]
                )
                for tc in last_msg.tool_calls
            ]
            await app.aupdate_state(
                config, {"messages": tool_messages}, as_node="tools"
            )
            await stream_tokens(app, None, config)
        state = await app.aget_state(config)


async def main(thread_id: str):
    setup_tracing()
    async with AsyncExitStack() as stack:
        checkpointer = await stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string("checkpoints.db")
        )
        mcp_tools = await load_mcp_tools_from_servers(stack)
        app = build_app(
            get_local_tools() + mcp_tools,
            checkpointer=checkpointer,
            human_in_loop=human_in_loop_enabled(),
        )

        config = {"configurable": {"thread_id": thread_id}}
        inputs_base = {"user_id": os.getenv("USER", "user"), "session_metadata": {}}
        while True:
            try:
                user_input = input("> ").strip()
            except EOFError:
                break
            if not user_input:
                continue
            if user_input.lower() in ("quit", "exit", "bye"):
                print("See ya!")
                break
            if guardrails_enabled():
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


cli = typer.Typer()


@cli.command()
def chat(
    provider: Optional[str] = typer.Option(None, "--provider", "-p", help="LLM provider (ollama, openai, gemini, anthropic, groq, mistral, openrouter, cohere, together, fireworks, deepseek, xai)"),
    model: Optional[str] = typer.Option(None, "--model", "-m", help="Override the default model for the selected provider"),
    thread_id: str = typer.Option("repl", "--thread-id", "-t", help="Conversation thread ID for memory persistence"),
    guardrails: bool = typer.Option(True, "--guardrails/--no-guardrails", help="Enable or disable input/output guardrails"),
    human_in_loop: bool = typer.Option(False, "--human-in-loop", "-H", help="Prompt for confirmation before each tool call"),
):
    if provider:
        os.environ["LLM_PROVIDER"] = provider
    if model:
        os.environ["LLM_MODEL"] = model
    if not guardrails:
        os.environ["GUARDRAILS_ENABLED"] = "false"
    if human_in_loop:
        os.environ["HUMAN_IN_LOOP"] = "true"

    def _sigint_handler(sig, frame):
        print("\nSee you next time!")
        sys.exit(0)

    signal.signal(signal.SIGINT, _sigint_handler)
    setup_logging()
    print(f"Hello {os.getenv('USER', 'user')}! What can I do for you today?")
    asyncio.run(main(thread_id=thread_id))


if __name__ == "__main__":
    cli()
