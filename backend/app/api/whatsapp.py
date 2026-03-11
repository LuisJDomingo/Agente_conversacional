from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import httpx
import random
import time
import redis
from app.services.llm_agent import handle_chat

router = APIRouter()

EVOLUTION_API_BASE_URL = os.getenv("EVOLUTION_API_BASE_URL")
EVOLUTION_INSTANCE_NAME = os.getenv("EVOLUTION_INSTANCE_NAME")
EVOLUTION_API_KEY = os.getenv("EVOLUTION_API_KEY")
WEBHOOK_VERIFY_TOKEN = os.getenv("EVOLUTION_WEBHOOK_VERIFY_TOKEN")
REDIS_URL = os.getenv("REDIS_URL")

# Anti-automatización para MVP: delay variable + límite por contacto.
WHATSAPP_MIN_DELAY_MS = int(os.getenv("WHATSAPP_MIN_DELAY_MS", "900"))
WHATSAPP_MAX_DELAY_MS = int(os.getenv("WHATSAPP_MAX_DELAY_MS", "2800"))
WHATSAPP_MIN_SECONDS_BETWEEN_MESSAGES = float(os.getenv("WHATSAPP_MIN_SECONDS_BETWEEN_MESSAGES", "2.5"))

# Registro en memoria del último envío por número (fallback si Redis no está disponible).
_last_sent_by_number: Dict[str, float] = {}
_redis_client = redis.from_url(REDIS_URL) if REDIS_URL else None


def _compute_human_delay_ms(message: str) -> int:
    """
    Calcula un delay pseudo-humano basado en longitud del texto y jitter.
    """
    text = (message or "").strip()
    # Base por longitud: aprox 15 ms por carácter + ruido.
    length_factor = max(0, len(text)) * 15
    jitter = random.randint(120, 650)
    delay = WHATSAPP_MIN_DELAY_MS + length_factor + jitter
    return max(WHATSAPP_MIN_DELAY_MS, min(delay, WHATSAPP_MAX_DELAY_MS))


def _can_send_now(phone_number: str, now_ts: Optional[float] = None) -> bool:
    """
    Controla la cadencia mínima de mensajes por contacto.
    Usa Redis cuando está disponible para soportar múltiples instancias.
    """
    now_ts = now_ts if now_ts is not None else time.time()
    ttl_seconds = int(WHATSAPP_MIN_SECONDS_BETWEEN_MESSAGES)

    if _redis_client:
        key = f"wa:last_sent:{phone_number}"
        try:
            # SETNX + EX para reservar ventana; si ya existe, no se puede enviar.
            created = _redis_client.set(key, str(now_ts), ex=max(1, ttl_seconds), nx=True)
            return bool(created)
        except Exception:
            # Fallback silencioso al control local si Redis falla.
            pass

    last_sent = _last_sent_by_number.get(phone_number)
    if last_sent is None:
        _last_sent_by_number[phone_number] = now_ts
        return True

    if (now_ts - last_sent) < WHATSAPP_MIN_SECONDS_BETWEEN_MESSAGES:
        return False

    _last_sent_by_number[phone_number] = now_ts
    return True


async def send_whatsapp_message(phone_number: str, message: str):
    if not EVOLUTION_API_BASE_URL or not EVOLUTION_INSTANCE_NAME or not EVOLUTION_API_KEY:
        print("Error: Missing Evolution API configuration.")
        return

    if not _can_send_now(phone_number):
        print(f"Rate limit activado para {phone_number}. Se omite envío para evitar patrón automático.")
        return

    url = f"{EVOLUTION_API_BASE_URL}/message/sendText/{EVOLUTION_INSTANCE_NAME}"
    adaptive_delay = _compute_human_delay_ms(message)
    headers = {
        "Content-Type": "application/json",
        "apikey": EVOLUTION_API_KEY
    }
    payload = {
        "number": phone_number,
        "options": {"delay": adaptive_delay},
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
    data: Dict[str, List[EvolutionIncomingMessage]]  # 'messages' is a list of EvolutionIncomingMessage
    event: str


@router.post("/webhook")
async def whatsapp_webhook(
    payload: EvolutionWebhookPayload,
    x_webhook_token: Optional[str] = Header(default=None)
):
    if WEBHOOK_VERIFY_TOKEN and x_webhook_token != WEBHOOK_VERIFY_TOKEN:
        raise HTTPException(status_code=401, detail="Invalid webhook token")

    if payload.event == "messages.upsert":
        for msg_data in payload.data.get("messages", []):
            # Filter out messages sent by the bot itself
            if msg_data.key.fromMe:
                continue

            phone_number = msg_data.key.remoteJid.split('@')[0]  # Extract phone number from JID
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
