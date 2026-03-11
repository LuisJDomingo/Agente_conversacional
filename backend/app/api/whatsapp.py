from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import httpx
from app.services.llm_agent import handle_chat

router = APIRouter()

EVOLUTION_API_BASE_URL = os.getenv("EVOLUTION_API_BASE_URL")
EVOLUTION_INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")

async def send_whatsapp_message(phone_number: str, message: str):
    if not EVOLUTION_API_BASE_URL or not EVOLUTION_INSTANCE_NAME or not EVOLUTION_API_KEY:
        print("Error: Missing Evolution API configuration.")
        return

    url = f"{EVOLUTION_API_BASE_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    payload = {
        "number": phone_number,
        "options": {"delay": 1200},
        "textMessage": {"text": message}
    }
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(url, headers=headers, json=payload)
            response.raise_for_status()
            print(f"WhatsApp message sent to {phone_number}: {message}")
        except httpx.HTTPStatusError as e:
            print(f"Error sending WhatsApp message: {e.response.status_code} - {e.response.text}")
        except httpx.RequestError as e:
            print(f"Network error sending WhatsApp message: {e}")

# Pydantic models for Evolution API webhook payload
class MessageKey(BaseModel):
    remoteJid: str
    fromMe: bool
    id: str
    participant: Optional[str] = None

class MessageContent(BaseModel):
    conversation: Optional[str] = None
    extendedTextMessage: Optional[Dict[str, Any]] = None
    # Add other message types as needed

class EvolutionIncomingMessage(BaseModel):
    key: MessageKey
    message: MessageContent
    pushName: Optional[str] = None
    messageTimestamp: str
    # Add other fields if necessary

class EvolutionWebhookPayload(BaseModel):
    instance: str
    webhook: str
    data: Dict[str, List[EvolutionIncomingMessage]] # 'messages' is a list of EvolutionIncomingMessage
    event: str

@router.post("/webhook")
async def whatsapp_webhook(payload: EvolutionWebhookPayload):
    if payload.event == "messages.upsert":
        for msg_data in payload.data.get("messages", []):
            # Filter out messages sent by the bot itself
            if msg_data.key.fromMe:
                continue

            phone_number = msg_data.key.remoteJid.split('@')[0] # Extract phone number from JID
            user_message = msg_data.message.conversation

            if not user_message:
                # Handle other message types if necessary (e.g., images, documents)
                print(f"Received non-text WhatsApp message from {phone_number}: {msg_data.message}")
                continue

            print(f"Received WhatsApp message from {phone_number}: {user_message}")

            # Use phone number as session_id for the LLM agent
            # Assuming business_id is static for now, or can be derived from instance
            business_id = "demo"
            llm_response = handle_chat(
                business_id=business_id,
                session_id=phone_number,
                message=user_message
            )

            reply_text = llm_response.get("reply", "Lo siento, no pude procesar tu solicitud.")
            await send_whatsapp_message(phone_number, reply_text)

        return {"status": "success", "message": "Webhook received and processed"}
    
    print(f"Ignored Evolution API event: {payload.event}")
    return {"status": "ignored", "message": f"Event {payload.event} not handled"}
