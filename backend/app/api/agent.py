from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.services.llm_agent import handle_chat

router = APIRouter()

class ChatRequest(BaseModel):
    business_id: str
    session_id: str
    message: str

@router.post("/chat")
async def chat(request: ChatRequest):
    # Llama a la lógica del agente (llm_agent.py)
    response = handle_chat(request.business_id, request.session_id, request.message)
    return response