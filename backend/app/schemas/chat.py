# backend/app/schemas/chat.py
from pydantic import BaseModel

class ChatRequest(BaseModel):
    business_id: str
    session_id: str
    message: str

class ChatResponse(BaseModel):
    reply: str
    status: str
