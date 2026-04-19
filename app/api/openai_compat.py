from fastapi import APIRouter, HTTPException
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
    
    # Import and call existing chat function
    from app.api.chat import ChatRequest, chat as chat_func
    
    chat_request = ChatRequest(message=user_message, model=request.model)
    result = await chat_func(chat_request)
    
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
                "content": result.response if hasattr(result, 'response') else str(result)
            },
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": len(user_message.split()),
            "completion_tokens": len(result.response.split()) if hasattr(result, 'response') else 0,
            "total_tokens": len(user_message.split()) + (len(result.response.split()) if hasattr(result, 'response') else 0)
        }
    }