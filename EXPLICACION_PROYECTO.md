# Funcionamiento del proyecto Agente Conversacional

## 1) ¿Por qué no lo ves en GitHub todavía?

Si ya existe este archivo en tu copia local pero no aparece en GitHub, suele deberse a uno de estos motivos:

1. El commit está **solo en local** y no se ha hecho `git push`.
2. Se creó una rama distinta y no está abierta/mergeada en la rama principal en GitHub.
3. El cambio está en una PR todavía sin fusionar.

En resumen: **para verlo en GitHub necesitas push (y normalmente merge si trabajas con PR)**.

---

## 2) Arquitectura del proyecto

Este proyecto implementa un **agente de reservas** para un estudio de fotografía con:

- **Frontend en React** (`Frontend/BookingAgent.jsx`) como widget de chat.
- **Backend en FastAPI** (`backend/app/main.py`) para exponer la API.
- **LLM en Ollama** (desde `backend/app/services/llm_agent.py`) para interpretar mensajes.
- **Redis** (`backend/app/services/session_service.py`) para guardar contexto de conversación por `session_id`.
- **Base de datos local SQLite** (`backend/app/database.py`) para reservas y horarios.
- **Canal opcional WhatsApp** (`backend/app/api/whatsapp.py`) mediante Evolution API.

---

## 3) Flujo funcional de extremo a extremo

1. El usuario escribe desde el widget web o por WhatsApp.
2. El backend recibe el mensaje (`/agent/chat` o `/whatsapp/webhook`).
3. `llm_agent.handle_chat(...)` recupera sesión, construye prompt + historial y llama al LLM.
4. El LLM responde en JSON estructurado (`intent`, `date`, `time`, datos cliente, `message`).
5. El backend valida reglas de negocio:
   - fecha pasada,
   - festivos,
   - cierre por horario semanal,
   - conflicto de hueco ya reservado.
6. Si está todo correcto y completos los datos, crea la reserva en BD.
7. Se envían correos (cliente + socios) si SMTP está configurado.
8. Se persiste el estado en Redis para continuar conversación.

---

## 4) ¿Es integrable en cualquier proyecto o solo React?

### Respuesta corta
Sí, el backend es **integrable con cualquier frontend** (React, Vue, Angular, app móvil, bot, etc.) siempre que puedas hacer HTTP a la API.

### Qué está acoplado y qué no
- **No acoplado a React:** el backend FastAPI y su endpoint `POST /agent/chat`.
- **Acoplado a React:** el widget visual actual (`Frontend/BookingAgent.jsx`) y su experiencia UI.

### Contrato mínimo para integrar en otro frontend
Enviar un `POST /agent/chat` con JSON:

```json
{
  "business_id": "demo",
  "session_id": "id-unico-usuario",
  "message": "Hola, quiero reservar"
}
```

Recibirás algo como:

```json
{
  "reply": "Texto para el usuario",
  "status": "success | need_info | error"
}
```

Con ese contrato puedes montar cliente en cualquier stack.

---

## 5) Endpoints clave

- `GET /` → salud básica.
- `POST /agent/chat` → canal principal para conversaciones.
- `POST /whatsapp/webhook` → entrada de mensajes WhatsApp vía Evolution API.

---

## 6) Componentes técnicos relevantes

- `backend/app/main.py`: instancia FastAPI + CORS + routers.
- `backend/app/api/agent.py`: endpoint de chat.
- `backend/app/services/llm_agent.py`: núcleo de orquestación conversacional.
- `backend/app/services/availability.py`: cálculo de huecos disponibles.
- `backend/app/services/session_service.py`: estado de sesión en Redis.
- `backend/app/api/whatsapp.py`: integración webhook + respuesta a WhatsApp.
- `docker-compose.yml`: stack completo para levantar servicios en conjunto.
