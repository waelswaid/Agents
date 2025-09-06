import logging
from typing import AsyncIterator, cast
from fastapi import APIRouter, HTTPException, Request, Depends
from fastapi.responses import StreamingResponse
from app.schemas.chat import ChatRequest, ChatResponse
from app.api.deps import get_memory_store
from app.services.memory import MemoryStore
from app.core import config
from app.providers.base import ProviderError
from app.services.chat_service import prepare_and_generate

router = APIRouter(tags=["chat"])
logger = logging.getLogger(__name__)
ALLOWED_AGENTS = {"general"}

@router.post("/chat", response_model=ChatResponse)
async def chat(req: ChatRequest, request: Request, memory: MemoryStore = Depends(get_memory_store)):
    if req.agent not in ALLOWED_AGENTS:
        raise HTTPException(status_code=400, detail="unknown agent")

    try:
        convo_id, _prompt, result = await prepare_and_generate(
            message=req.message,
            agent=req.agent,
            conversation_id=req.conversation_id,
            memory=memory if config.ENABLE_MEMORY else None,
            stream=req.stream,
        )
    except ProviderError as e:
        raise HTTPException(status_code=502, detail=str(e))

    # Non-stream path
    if not req.stream:
        reply = cast(str, result)
        if config.ENABLE_MEMORY:
            await memory.append(convo_id, "user", req.message)
            await memory.append(convo_id, "assistant", reply)
        return ChatResponse(
            reply=reply,
            conversation_id=convo_id,
            model=config.OLLAMA_MODEL_GENERAL,
            provider=config.PROVIDER,
        )

    # Stream path
    gen = cast(AsyncIterator[str], result)

    async def streamer():
        acc: list[str] = []
        try:
            async for chunk in gen:
                acc.append(chunk)
                if await request.is_disconnected():
                    logger.info("client disconnected, stopping stream")
                    break
                yield chunk.encode("utf-8")
        except Exception as e:
            logger.exception("streaming error occurred: %s", e)
        finally:
            if config.ENABLE_MEMORY:
                await memory.append(convo_id, "user", req.message)
                if acc:
                    await memory.append(convo_id, "assistant", "".join(acc))

    headers = {"X-Conversation-Id": convo_id}
    return StreamingResponse(streamer(), media_type="text/plain; charset=utf-8", headers=headers)
