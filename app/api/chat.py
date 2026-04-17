from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.core.config import settings
import logging

logger = logging.getLogger("chudo_ai")
router = APIRouter(prefix="/chat", tags=["Chat"])

class ChatRequest(BaseModel):
    message: str
    model: str = "llama3-70b-8192"  # дефолт GROQ

class ChatResponse(BaseModel):
    response: str
    model: str | None = None

@router.post("", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Принимает сообщение от пользователя.
    Если задан GROQ_API_KEY — проксирует туда.
    Иначе возвращает echo (демо-режим).
    """
    user_msg = request.message.strip()
    if not user_msg:
        raise HTTPException(status_code=422, detail="Empty message")
    
    # Если есть GROQ ключ — реальный AI-запрос
    if settings.GROQ_API_KEY:
        try:
            import httpx
            async with httpx.AsyncClient(timeout=30.0) as client:
                r = await client.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={
                        "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": request.model,
                        "messages": [{"role": "user", "content": user_msg}],
                        "temperature": 0.7
                    }
                )
                data = r.json()
                ai_text = data["choices"][0]["message"]["content"]
                return ChatResponse(response=ai_text, model=request.model)
        except Exception as e:
            logger.error(f"GROQ error: {e}")
            raise HTTPException(status_code=502, detail="AI service unavailable")
    
    # Демо-режим (если GROQ_API_KEY не задан)
    logger.info(f"Demo mode: echo for '{user_msg[:50]}...'")
    return ChatResponse(
        response=f"ДЕМО-РЕЖИМ: Вы написали — {user_msg}",
        model=None
    )
