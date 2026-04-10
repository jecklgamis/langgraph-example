import logging
from contextlib import AsyncExitStack, asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langchain_mcp_adapters.tools import load_mcp_tools
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client
from pydantic import BaseModel

from agent import build_app, is_reachable
from functions.config import get_local_tools
from mcp_servers import mcp_servers

logger = logging.getLogger(__name__)

_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    async with AsyncExitStack() as stack:
        mcp_tools = []
        for mcp in mcp_servers:
            url = mcp["url"]
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

        _agent = build_app(get_local_tools() + mcp_tools)
        yield


app = FastAPI(title="LangGraph Agent", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str


@app.post("/chat")
async def chat(request: ChatRequest):
    """Returns the final agent reply."""
    inputs = {"messages": [HumanMessage(content=request.message)]}
    result = await _agent.ainvoke(inputs)
    return {"response": result["messages"][-1].content}


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streams each agent step as it arrives."""

    async def generate():
        inputs = {"messages": [HumanMessage(content=request.message)]}
        async for output in _agent.astream(inputs):
            for value in output.values():
                content = value["messages"][-1].content
                if content:
                    yield content + "\n"

    return StreamingResponse(generate(), media_type="text/plain")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="0.0.0.0", port=8000)
