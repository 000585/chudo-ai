from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import uuid
import time

router = APIRouter()

class OpenAIMessage(BaseModel):
    role: str
    content: str

class OpenAIRequest(BaseModel):
    model: str
    messages: List[OpenAIMessage]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = 1024

@router.post("/v1/chat/completions")
async def openai_compatible(request: OpenAIRequest):
    """OpenAI-compatible endpoint for OpenClaw and other tools"""
    
    # Extract user message from messages array
    user_message = ""
    for msg in reversed(request.messages):
        if msg.role == "user":
            user_message = msg.content
            break
    
    if not user_message:
        raise HTTPException(status_code=400, detail="No user message found")
    
    # Call existing chat service
    from app.services.chat import process_chat_message
    
    result = await process_chat_message(
        message=user_message,
        user_id=f"openclaw_{uuid.uuid4().hex[:8]}",
        model=request.model
    )
    
    # Format OpenAI-compatible response
    return {
        "id": f"chatcmpl-{uuid.uuid4().hex}",
        "object": "chat.completion",
        "created": int(time.time()),
        "model": request.model,
        "choices": [{
            "index": 0,
            "message": {
                "role": "assistant",
                "content": result.get("response", "No response")
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(result.get("response", "").split()),
            "total_tokens": len(user_message.split()) + len(result.get("response", "").split())
        }
    }