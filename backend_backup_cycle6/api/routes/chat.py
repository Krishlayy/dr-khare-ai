import json
import uuid

from fastapi import APIRouter, Depends, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from backend.api.dependencies import get_current_user
from backend.core.config import settings
from backend.core.rate_limit import limiter
from backend.database.database import get_db
from backend.database.models import ChatHistory, User
from backend.database.schemas import ChatRequest, ChatResponse
from backend.services.chat_service import process_chat, stream_chat

router = APIRouter()


async def _save_message(
    db: Session,
    session_id: str,
    role: str,
    message: str,
    user_id: int | None = None,
    sources: dict | list | None = None,
) -> None:
    import asyncio
    def do_save():
        db.add(
            ChatHistory(
                user_id=user_id,
                session_id=session_id,
                role=role,
                message=message,
                sources=sources or [],
            )
        )
        db.commit()
    await asyncio.to_thread(do_save)


@router.post("/stream")
@limiter.limit(settings.CHAT_RATE_LIMIT)
async def chat_endpoint(
    request: Request,
    body: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
):
    session_id = body.session_id or str(uuid.uuid4())
    user_id = current_user.id if current_user else None

    await _save_message(db, session_id, "user", body.text, user_id=user_id)

    if body.stream:

        async def event_generator():
            full_text = ""
            meta: dict = {}
            async for event in stream_chat(db, body.text, session_id, user_id, mode=body.mode):
                if event["type"] == "meta":
                    meta = event
                elif event["type"] == "token":
                    full_text += event["content"]
                elif event["type"] == "done":
                    await _save_message(
                        db,
                        session_id,
                        "assistant",
                        event.get("full_response", full_text),
                        user_id=user_id,
                        sources={
                            "citations": meta.get("sources", []),
                            "answer_source": meta.get("answer_source"),
                            "confidence": meta.get("confidence"),
                            "response_time_ms": event.get("response_time_ms"),
                            "model": event.get("model"),
                            "bypassed_llm": meta.get("bypassed_llm", False),
                        },
                    )
                    event["session_id"] = session_id
                yield f"data: {json.dumps(event)}\n\n"

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    result = await process_chat(db, body.text, session_id, user_id, mode=body.mode)

    await _save_message(
        db,
        session_id,
        "assistant",
        result["response"],
        user_id=user_id,
        sources={
            "citations": result["sources"],
            "answer_source": result["answer_source"],
            "confidence": result["confidence"],
            "response_time_ms": result["response_time_ms"],
            "model": result["model"],
            "bypassed_llm": result.get("bypassed_llm", False),
        },
    )

    return ChatResponse(
        response=result["response"],
        sources=result["sources"],
        session_id=session_id,
        answer_source=result["answer_source"],
        confidence=result["confidence"],
        response_time_ms=result["response_time_ms"],
        model=result["model"],
        bypassed_llm=result.get("bypassed_llm", False),
    )
