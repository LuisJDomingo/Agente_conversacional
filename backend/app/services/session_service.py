# backend/app/services/session_service.py
import redis
import json
import os
from typing import Dict

# Conexión a Redis. La URL se toma de una variable de entorno.
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")
_redis_client = redis.from_url(REDIS_URL)


def get_session(session_id: str) -> dict:
    """
    Devuelve el estado de la conversación desde Redis.
    Crea una nueva sesión si no existe.
    """
    session_key = f"session:{session_id}"
    session_data = _redis_client.get(session_key)

    if session_data:
        return json.loads(session_data)

    # Si no existe, crea una sesión vacía con un historial
    new_session = {"history": []}
    _redis_client.set(session_key, json.dumps(new_session))
    return new_session


def save_session(session_id: str, session_data: dict):
    """
    Guarda el estado de la conversación en Redis.
    """
    session_key = f"session:{session_id}"
    # Guardar la sesión con un tiempo de expiración (ej: 24 horas)
    _redis_client.set(session_key, json.dumps(session_data), ex=86400)


def clear_session(session_id: str):
    """
    Resetea la sesión tras confirmar una cita.
    """
    session_key = f"session:{session_id}"
    _redis_client.delete(session_key)
