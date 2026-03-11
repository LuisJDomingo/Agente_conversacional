# Plan de trabajo — Fase 1 (Días 1–30)

Este documento deja persistido el contexto acordado para continuar el proyecto del agente conversacional en modo comercializable.

## Objetivo de Fase 1

Llevar el MVP actual a un estado de **producción básica segura**, con foco en:

1. Seguridad de acceso y tenant básico.
2. Persistencia y gobierno de datos.
3. Observabilidad operativa mínima.

---

## Alcance acordado

### 1) Seguridad API y tenants

- Añadir autenticación a `POST /agent/chat` (API key o JWT).
- Eliminar dependencias hardcodeadas de tenant/cuenta (`business_id="demo"` en canal WhatsApp).
- Aplicar limitación de tasa por tenant y canal.

### 2) Persistencia y gobierno de datos

- Definir política de retención para sesiones y datos personales.
- Automatizar backups y validar restauración.
- Mantener `DATABASE_URL` como fuente principal para entorno productivo (PostgreSQL).

### 3) Observabilidad mínima

- Sustituir `print` por logging estructurado (JSON).
- Añadir correlación por request/session (`request_id`, `session_id`, `business_id`).
- Exponer métricas básicas:
  - latencia por endpoint,
  - tasa de error del LLM,
  - ratio de conversación→reserva.

---

## Backlog técnico (orden sugerido)

1. **Auth middleware / dependency** para `/agent/chat`.
2. **Modelo de API keys por tenant** (tabla + validación).
3. **Resolución de tenant en WhatsApp webhook** (sin hardcode de `demo`).
4. **Rate limiting por tenant+canal**.
5. **Logger estructurado** en backend.
6. **Métricas técnicas y de negocio** (promedio latencia, errores LLM, reservas confirmadas).
7. **Runbook de backup/restore** y prueba de restauración.

---

## Criterios de “done” de Fase 1

- `/agent/chat` responde solo con credenciales válidas.
- Cada mensaje queda trazable con `request_id` y `session_id`.
- Existen métricas mínimas visibles para operación.
- Se demuestra backup y restore exitoso en entorno de pruebas.
- WhatsApp deja de depender de `business_id` fijo.

---

## Arranque de mañana (primer bloque de trabajo)

1. Diseñar esquema de autenticación (API key por tenant).
2. Implementar validación en endpoint `/agent/chat`.
3. Crear pruebas automáticas de acceso autorizado/no autorizado.
4. Empezar sustitución progresiva de `print` por logger.

---

## Nota de continuidad

Este archivo sirve como “memoria persistente” del plan. Aunque el contexto de chat no se conserve entre sesiones, el plan queda guardado en el repositorio para continuar exactamente desde aquí.
