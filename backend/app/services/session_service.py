# backend/app/services/session_service.py
import redis
import json
import os
from typing import Dict

# Conexión a Redis. La URL se toma de una variable de entorno.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_redis_client = redis.from_url(REDIS_URL)

# Fallback en memoria para entornos donde Redis no está disponible.
_fallback_sessions: Dict[str, dict] = {}


def _safe_redis_get(key: str):
    try:
        return _redis_client.get(key)
    except Exception:
        return None


def _safe_redis_set(key: str, value: str, ex: int | None = None):
    try:
        if ex is not None:
            _redis_client.set(key, value, ex=ex)
        else:
            _redis_client.set(key, value)
        return True
    except Exception:
        return False


def _safe_redis_delete(key: str):
    try:
        _redis_client.delete(key)
        return True
    except Exception:
        return False


def get_session(session_id: str) -> dict:
    """
    Devuelve el estado de la conversación desde Redis.
    Si Redis no está disponible, usa un almacenamiento en memoria.
    """
    session_key = f"session:{session_id}"
    session_data = _safe_redis_get(session_key)

    if session_data:
        return json.loads(session_data)

    # Fallback local si Redis no responde.
    if session_key in _fallback_sessions:
        return _fallback_sessions[session_key]

    new_session = {"history": []}
    if not _safe_redis_set(session_key, json.dumps(new_session)):
        _fallback_sessions[session_key] = new_session
    return new_session


def save_session(session_id: str, session_data: dict):
    """
    Guarda el estado de la conversación en Redis.
    Si Redis no está disponible, guarda en memoria.
    """
    session_key = f"session:{session_id}"
    if not _safe_redis_set(session_key, json.dumps(session_data), ex=86400):
        _fallback_sessions[session_key] = session_data


def clear_session(session_id: str):
    """
    Resetea la sesión tras confirmar una cita.
    """
    session_key = f"session:{session_id}"
    _safe_redis_delete(session_key)
    _fallback_sessions.pop(session_key, None)
