from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.core.config import settings
from app.models.message import Message
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, desc
import httpx
import logging

logger = logging.getLogger("chudo_ai")
router = APIRouter(prefix="/chat", tags=["Chat Context"])

# inline async engine (no dependency on existing session.py)
_db_url = settings.DATABASE_URL
if _db_url.startswith("postgresql://"):
    _db_url = _db_url.replace("postgresql://", "postgresql+asyncpg://", 1)
elif _db_url.startswith("postgres://"):
    _db_url = _db_url.replace("postgres://", "postgresql+asyncpg://", 1)

engine = create_async_engine(_db_url, pool_pre_ping=True)
async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

class ChatContextRequest(BaseModel):
    message: str
    user_id: str
    max_history: int = 10
    model: Optional[str] = None

class ChatContextResponse(BaseModel):
    response: str
    model: str
    context_used: int

def _trim(msgs, max_chars=12000):
    total = 0
    result = []
    for m in reversed(msgs):
        total += len(m.get("content", ""))
        if total > max_chars:
            break
        result.append(m)
    result.reverse()
    return result

@router.post("/context", response_model=ChatContextResponse)
async def chat_context(request: ChatContextRequest):
    user_msg = request.message.strip()
    if not user_msg:
        raise HTTPException(status_code=422, detail="Empty message")

    model = request.model or settings.GROQ_MODEL

    async with async_session() as db:
        # save user message
        db.add(Message(user_id=request.user_id, role="user", content=user_msg, model=None))
        await db.commit()

        # load history (newest first, then reverse to old->new)
        res = await db.execute(
            select(Message)
            .where(Message.user_id == request.user_id)
            .order_by(desc(Message.created_at))
            .limit(request.max_history * 2)
        )
        rows = res.scalars().all()
        rows.reverse()

        # build prompt
        groq_msgs = [{"role": "system", "content": "Ты — CHUDO AI, полезный и дружелюбный ассистент."}]
        for r in rows:
            groq_msgs.append({"role": r.role, "content": r.content})

        groq_msgs = _trim(groq_msgs)
        groq_msgs.append({"role": "user", "content": user_msg})

        # call groq
        if not settings.GROQ_API_KEY:
            raise HTTPException(status_code=503, detail="GROQ not configured")

        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={"Authorization": f"Bearer {settings.GROQ_API_KEY}", "Content-Type": "application/json"},
                json={"model": model, "messages": groq_msgs, "temperature": 0.7}
            )
            if r.status_code != 200:
                logger.error(f"GROQ HTTP {r.status_code}: {r.text}")
                raise HTTPException(status_code=502, detail="AI service unavailable")

            ai_text = r.json()["choices"][0]["message"]["content"]

            # save assistant message
            db.add(Message(user_id=request.user_id, role="assistant", content=ai_text, model=model))
            await db.commit()

            return ChatContextResponse(response=ai_text, model=model, context_used=len(groq_msgs)-1)
