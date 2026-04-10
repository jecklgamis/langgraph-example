import logging
from contextlib import AsyncExitStack, asynccontextmanager

import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from pydantic import BaseModel

from agent import build_app, load_mcp_tools_from_servers, setup_tracing
from functions.config import get_local_tools
from functions.guardrails import GuardrailError, is_safe, validate_input, validate_output

logger = logging.getLogger(__name__)

_agent = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _agent
    setup_tracing()
    async with AsyncExitStack() as stack:
        checkpointer = await stack.enter_async_context(
            AsyncSqliteSaver.from_conn_string("checkpoints.db")
        )
        mcp_tools = await load_mcp_tools_from_servers(stack)
        _agent = build_app(get_local_tools() + mcp_tools, checkpointer=checkpointer)
        yield


app = FastAPI(title="LangGraph Agent", lifespan=lifespan)


class ChatRequest(BaseModel):
    message: str
    thread_id: str = "default"
    user_id: str = "anonymous"
    session_metadata: dict = {}


class ChatResponse(BaseModel):
    response: str
    thread_id: str
    user_id: str


async def check_guardrails(message: str) -> None:
    try:
        validate_input(message)
    except GuardrailError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not await is_safe(message):
        raise HTTPException(status_code=400, detail="Input flagged as unsafe.")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Returns the final agent reply."""
    await check_guardrails(request.message)
    inputs = {
        "messages": [HumanMessage(content=request.message)],
        "user_id": request.user_id,
        "session_metadata": request.session_metadata,
    }
    config = {"configurable": {"thread_id": request.thread_id}}
    result = await _agent.ainvoke(inputs, config=config)
    return ChatResponse(
        response=validate_output(result["messages"][-1].content),
        thread_id=request.thread_id,
        user_id=request.user_id,
    )


@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """Streams tokens as they are generated."""
    await check_guardrails(request.message)

    async def generate():
        inputs = {
            "messages": [HumanMessage(content=request.message)],
            "user_id": request.user_id,
            "session_metadata": request.session_metadata,
        }
        config = {"configurable": {"thread_id": request.thread_id}}
        async for event in _agent.astream_events(inputs, config=config, version="v2"):
            if event["event"] == "on_chat_model_stream":
                chunk = event["data"]["chunk"]
                if isinstance(chunk.content, str) and chunk.content:
                    yield validate_output(chunk.content)

    return StreamingResponse(generate(), media_type="text/plain")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    uvicorn.run(app, host="0.0.0.0", port=8000)
