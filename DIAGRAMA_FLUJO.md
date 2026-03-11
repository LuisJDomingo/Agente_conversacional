# Diagrama de flujo del agente de reservas

```mermaid
flowchart TD
    A[Usuario: Web o WhatsApp] --> B{Canal de entrada}
    B -->|Web| C[POST /agent/chat]
    B -->|WhatsApp| D[POST /whatsapp/webhook]

    D --> E[Extrae phone_number y message]
    E --> C

    C --> F[handle_chat(business_id, session_id, message)]
    F --> G[Recuperar sesión en Redis]
    G --> H[Construir mensajes: system prompt + historial + user]
    H --> I[Llamada a Ollama /chat]
    I --> J[Respuesta JSON del LLM]

    J --> K[Actualizar estado: intent/date/time/datos cliente]
    K --> L{Intent}

    L -->|check_availability| M[Calcular huecos disponibles]
    M --> N{¿Hay slots?}
    N -->|Sí| O[Responder horarios libres]
    N -->|No| P[Responder cierre/festivo/agenda completa]

    L -->|book| Q[Validar fecha/hora + disponibilidad]
    Q --> R{¿Slot válido?}
    R -->|No| S[Solicitar nueva hora/fecha]
    R -->|Sí| T{¿Datos cliente completos?}
    T -->|No| U[Pedir siguiente dato faltante]
    T -->|Sí| V[Crear reserva en BD]

    V --> W[Enviar email cliente (si SMTP)]
    V --> X[Enviar notificación a socios]
    V --> Y[Limpiar sesión y confirmar cita]

    L -->|smalltalk/unknown| Z[Responder texto conversacional]

    O --> AA[Guardar sesión en Redis]
    P --> AA
    S --> AA
    U --> AA
    Y --> AA
    Z --> AA
    AA --> AB[Respuesta al usuario]
```
