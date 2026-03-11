# Cómo Conectar el BookingAgent a un LLM

Para conectar el `BookingAgent` a un LLM (Large Language Model) y que pueda mantener una conversación natural, necesitaríamos una arquitectura que separe el frontend (la interfaz de chat) del backend (el cerebro del chatbot).

A continuación, te explico la arquitectura y el código necesario.

## Arquitectura General

La arquitectura sería la siguiente:

1.  **Frontend (React)**: La interfaz de usuario (`BookingAgent.jsx`) que envía los mensajes del usuario al backend.
2.  **Backend (Python/FastAPI)**: Un servidor que recibe los mensajes, los procesa con un LLM y devuelve la respuesta.
3.  **LLM (Ollama/Mistral)**: El modelo de lenguaje que genera las respuestas y decide qué herramientas usar.

## Implementación del Backend

El backend se encargaría de la lógica principal. Usaríamos FastAPI por su simplicidad y rendimiento.

**1. `backend/app/services/llm_agent_explained.py`:**

Este archivo contendría la lógica para interactuar con el LLM.

```python
from ollama import Client

# Almacenamiento de sesiones en memoria (para producción se usaría una base de datos como Redis)
sessions = {}
client = Client(host='http://127.0.0.1:11434') # Asegúrate de que Ollama esté corriendo en este host

def handle_message_with_llm(session_id, message):
    if session_id not in sessions:
        sessions[session_id] = []
    
    # Añadir mensaje del usuario al historial
    sessions[session_id].append({"role": "user", "content": message})
    
    # Prompt del sistema para guiar al modelo
    system_prompt = """
    Eres un asistente de reservas para un estudio de fotografía.
    Tu objetivo es ayudar al usuario a agendar una cita.
    Puedes preguntar por la fecha y la hora.
    Sé amable y conversacional.
    No puedes ver la disponibilidad, pero puedes preguntar al usuario si quiere que la consultes.
    Si el usuario quiere cancelar, simplemente responde 'Ok, he cancelado la operación.' y finaliza.
    """
    
    messages_with_prompt = [
        {"role": "system", "content": system_prompt},
        *sessions[session_id]
    ]

    try:
        # Llamada al LLM
        response = client.chat(
            model="mistral", # Asegúrate de tener este modelo
            messages=messages_with_prompt
        )
        
        full_response = response['message']['content']

        # Añadir respuesta del bot al historial
        sessions[session_id].append({"role": "assistant", "content": full_response})
        
        return {"response": full_response}

    except Exception as e:
        print(f"Error de conexión con Ollama: {e}")
        return {"response": "Lo siento, mi sistema de inteligencia artificial está fuera de línea."}

```

**2. `backend/app/main_llm.py`:**

Este sería el punto de entrada del servidor.

```python
from fastapi import FastAPI
from pydantic import BaseModel
from app.services.llm_agent_explained import handle_message_with_llm

app = FastAPI(title="LLM Booking Agent")

class ChatRequest(BaseModel):
    session_id: str
    message: str

@app.post("/chat_llm")
def chat(request: ChatRequest):
    return handle_message_with_llm(
        session_id=request.session_id,
        message=request.message
    )
```

## Implementación del Frontend

El frontend se conectaría a este nuevo backend.

**`src/components/BookingAgent_llm.jsx`:**

Este es el componente de React modificado.

```javascript
import React, { useState, useEffect, useRef } from "react";
import { MessageSquare, X, Send, Calendar, Clock, User } from 'lucide-react';

export default function FloatingBookingAgentLLM({ sessionId }) {
  const [open, setOpen] = useState(false);
  const [messages, setMessages] = useState([
    { from: "bot", text: "¡Hola! ¿Cómo puedo ayudarte a reservar tu cita hoy?" }
  ]);
  const [userInput, setUserInput] = useState("");
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => { scrollToBottom(); }, [messages]);

  const sendMessage = async () => {
    if (!userInput.trim()) return;

    const newMessages = [...messages, { from: "user", text: userInput }];
    setMessages(newMessages);
    const messageToSend = userInput;
    setUserInput("");

    try {
      const res = await fetch("http://localhost:8000/chat_llm", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: sessionId, message: messageToSend }),
      });

      if (!res.ok) throw new Error("El servidor del backend no responde.");

      const data = await res.json();
      setMessages(prev => [...prev, { from: "bot", text: data.response }]);

    } catch (error) {
      console.error("Error connecting to backend:", error);
      setMessages(prev => [...prev, { from: "bot", text: "Lo siento, el sistema de reservas está fuera de línea." }]);
    }
  };

  return (
    <div style={styles.container}>
      {/* ... (El resto de la UI es igual que en la versión elegante) ... */}
    </div>
  );
}

// ... (Los estilos son los mismos) ...
```

## Pasos para Ejecutar

1.  **Instalar y ejecutar Ollama**: Sigue las instrucciones de [Ollama](https://ollama.ai/) para instalarlo y luego ejecuta `ollama run mistral` en tu terminal.
2.  **Instalar dependencias del backend**: En la carpeta `backend`, ejecuta `pip install -r requirements.txt`. Asegúrate de que `ollama` está en el archivo.
3.  **Ejecutar el backend**: Desde la carpeta `backend`, ejecuta `uvicorn app.main_llm:app --reload`.
4.  **Usar el nuevo componente**: En tu aplicación de React, usa `<FloatingBookingAgentLLM sessionId="una-id-unica" />` en lugar del `BookingAgent` anterior.

Esta arquitectura te daría un chatbot mucho más potente y flexible.
