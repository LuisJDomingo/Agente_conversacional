# Guía de despliegue e integración

## Opción A (recomendada): despliegue con Docker Compose

### 1. Prerrequisitos

- Docker y Docker Compose instalados.
- Puertos libres: `80`, `8000`, `8080`, `11434`.

### 2. Variables y configuración

Revisa `docker-compose.yml` y ajusta, como mínimo:

- `EVOLUTION_API_KEY`
- `EVOLUTION_INSTANCE_NAME`
- `OLLAMA_MODEL`
- `WHATSAPP_MIN_DELAY_MS` (ej. 900)
- `WHATSAPP_MAX_DELAY_MS` (ej. 2800)
- `WHATSAPP_MIN_SECONDS_BETWEEN_MESSAGES` (ej. 2.5)
- Credenciales SMTP en backend (si quieres correos reales).

> Nota: actualmente el backend usa SQLite local (`bookings.db`) desde código. Si quieres PostgreSQL real para reservas del backend, hay que adaptar `backend/app/database.py` para leer `DATABASE_URL`.

### 3. Levantar servicios

Desde la raíz del repo:

```bash
docker compose up --build -d
```

### 4. Verificar salud

```bash
curl http://localhost:8000/
```

Debe devolver:

```json
{"message":"API corriendo correctamente"}
```

### 5. Probar chat por API

```bash
curl -X POST http://localhost:8000/agent/chat \
  -H "Content-Type: application/json" \
  -d '{
    "business_id": "demo",
    "session_id": "test-user-1",
    "message": "Hola, quiero reservar una cita"
  }'
```

---

## Opción B: integración del backend en otro frontend (no React)

Tu app (web, móvil o bot) solo necesita consumir `POST /agent/chat`.

### Contrato de petición

```json
{
  "business_id": "demo",
  "session_id": "id-estable-por-usuario",
  "message": "texto del usuario"
}
```

### Contrato de respuesta

```json
{
  "reply": "respuesta del agente",
  "status": "success | need_info | error"
}
```

### Recomendaciones de integración

1. Mantén `session_id` estable por usuario/conversación.
2. Muestra `reply` tal cual al usuario.
3. Si `status=need_info`, espera más datos del usuario y vuelve a llamar al endpoint.
4. Implementa reintentos si falla red/timeout del backend.

---

## Opción C: despliegue por componentes (producción)

1. **Backend FastAPI** en contenedor o VM (con Uvicorn/Gunicorn).
2. **Redis gestionado** para sesiones.
3. **Ollama** en nodo con recursos suficientes para el modelo elegido.
4. **Reverse proxy** (Nginx/Traefik) con TLS.
5. **Observabilidad**: logs centralizados y healthchecks.

---

## Problemas habituales

- **El frontend carga pero no responde el chat**: revisar CORS y proxy hacia backend.
- **Respuesta de error del LLM**: revisar `OLLAMA_API_BASE`, modelo cargado y latencia.
- **No guarda contexto**: comprobar conexión a Redis (`REDIS_URL`).
- **No llegan correos**: validar `SMTP_USER`, `SMTP_PASSWORD`, servidor/puerto.

---

## Comandos útiles

```bash
# Levantar stack
docker compose up --build -d

# Ver logs del backend
docker compose logs -f backend

# Reiniciar backend
docker compose restart backend

# Apagar stack
docker compose down
```
