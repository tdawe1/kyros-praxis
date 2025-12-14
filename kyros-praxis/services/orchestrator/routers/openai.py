"""
OpenAI API Router

Provides endpoints for interacting with the OpenAI Agent SDK.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from app.core.openai_agent import get_sync_agent, get_async_agent
from auth import get_current_user

router = APIRouter()

class PromptRequest(BaseModel):
    prompt: str
    system_message: Optional[str] = None
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class StructuredPromptRequest(BaseModel):
    messages: List[Dict[str, str]]
    temperature: float = 0.7
    max_tokens: Optional[int] = None

class OpenAIResponse(BaseModel):
    content: str
    role: str
    finish_reason: str
    usage: Dict[str, Any]
    model: str
    created: int

@router.post("/openai/prompt", response_model=OpenAIResponse, summary="Send prompt to OpenAI")
async def send_prompt_to_openai(
    request: PromptRequest,
    current_user: dict = Depends(get_current_user)  # noqa: F841
) -> Dict[str, Any]:
    """
    Send a prompt to the OpenAI model and return the response.
    """
    try:
        agent = get_sync_agent()
        response = agent.send_prompt(
            prompt=request.prompt,
            system_message=request.system_message,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with OpenAI: {str(e)}"
        )

@router.post("/openai/structured-prompt", response_model=OpenAIResponse, summary="Send structured prompt to OpenAI")
async def send_structured_prompt_to_openai(
    request: StructuredPromptRequest,
    current_user: dict = Depends(get_current_user)  # noqa: F841
) -> Dict[str, Any]:
    """
    Send a structured prompt (list of messages) to the OpenAI model and return the response.
    """
    try:
        agent = get_sync_agent()
        response = agent.send_structured_prompt(
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens
        )
        return response
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error communicating with OpenAI: {str(e)}"
        )
