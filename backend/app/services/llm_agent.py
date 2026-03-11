import os
import re
import json
import requests
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, time, timedelta
from dotenv import load_dotenv
from app.database import SessionLocal
from app.services.availability import get_available_slots, is_holiday
from app.models.booking import Booking
from app.models.schedule import WeeklySchedule
from app.services.session_service import get_session, save_session, clear_session


print(">>> CARGADO llm_agent.py CORRECTO")

# Cargar variables del .env
load_dotenv(dotenv_path=".env.local")
OLLAMA_API_BASE = os.getenv("OLLAMA_API_BASE", "http://127.0.0.1:11434/api")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3:8b-instruct-q4_K_M")

print(">>> OLLAMA_API_BASE:", OLLAMA_API_BASE)


# --- PERSONALIZACIÓN DEL CLIENTE ---

PERSONALITY = '''
Soy Martín, experto en atención al cliente y fotógrafo profesional.
Mi prioridad es ofrecer una experiencia de servicio impecable, escuchando al cliente y resolviendo sus dudas con eficacia y calidez.
Hablo en primera persona, de tú a tú, pero manteniendo siempre la profesionalidad.
No soy un robot; soy un asesor de confianza que guía al cliente para concertar una visita fisca comercial.
Mi objetivo es crear una conexión genuina, transmitiendo pasión por la fotografía y el compromiso con la satisfacción del cliente.
Mi objetivo es que cada cliente se sienta valorado y entienda que está en manos de un profesional dedicado a capturar sus momentos más importantes con excelencia.
Mi objetivo es concertar una visita presencial para cerrar la venta.
'''
BUSINESS_CONTEXT = """

Servicios principales:
Fotografía documental y reportajes: cubro eventos, noticias y proyectos personales. Entrego imágenes con narrativa visual, estilo auténtico y profesional. Ideal para medios, ONGs y clientes corporativos que quieren contar historias con impacto.
Sesiones de retrato: en estudio o exteriores, personalizadas según la personalidad del cliente. Trabajo luz natural y artificial para resaltar lo mejor de cada persona.
Cobertura de eventos sociales y corporativos: bodas, conferencias, inauguraciones o eventos privados. Garantizo cobertura completa, discreción y fotografías listas para redes o álbumes impresos.

Información adicional:
- Público objetivo: empresas, particulares y medios de comunicación.
- Ubicación: base en [Ciudad], desplazamiento a nivel nacional según proyecto.
- Horario de atención: Lunes a Sábado, 9:00-20:00.
- Proceso de reserva: consulta disponibilidad → confirmación de fecha y hora → reserva con pago o señal opcional.
- Política de cambios/cancelaciones: se puede reprogramar avisando con 24h de antelación.
- Filosofía: cercanía, profesionalidad y pasión por la imagen. Mi objetivo es que cada cliente se sienta escuchado y que sus recuerdos o proyectos queden reflejados de manera única.
- Diferenciadores: trato personalizado, rapidez en entrega, estilo fotoperiodístico auténtico y atención cercana.

Mi tono es cercano, profesional, educado y apasionado por la fotografía. Busco que los clientes reciban información clara, se sientan seguros y concreten citas.
Mi objetivo es concertar una visita presencial para cerrar la venta.
"""
REGLAS= '''
- Habla en español
- Se breve en tus presentaciones.
- Sé natural, cálido y conversacional. Evita sonar como un manual de instrucciones o una lista de características.
- Usa un tono cercano y amigable, con alma.
- Prioriza siempre la conexión emocional con el cliente.
- Respeta ante todo la ortografía y gramática del español.
- Confirma siempre los datos antes de reservar.
- las fechas pueden ser en cualquier formato, pero en el campo "date" usa SIEMPRE el formato YYYY-MM-DD
- Sondea primero al cliente sobre la celebración (repregnta al menos 2 veces, por ej: 'Para hacerme una idea, ¿podrías contarme un poco sobre la boda? ¿Dónde será, cuántos invitados... lo que se te ocurra!'), después confirma la disponibilidad.
- Una vez tengas algunos detalles del evento, empieza a pedir los datos del cliente en este orden: nombre completo, email, teléfono de contacto y fecha de la boda/evento.
- Pide SIEMPRE un solo dato a la vez para que la conversación sea fluida.
- Las citas duran 1 hora
- Si el usuario no especifica el año o el mes, asume el más próximo en el futuro.
- No inventes horarios
- usa muletillas naturales del español como "te cuento", "vale", "perfecto", "claro", "por supuesto", "genial", "me alegra", "guay", "muy bien", etc.
- Si falta información, pídesela al cliente
- Si el usuario quiere cambiar la fecha/hora o el contexto actual es erróneo, usa "RESET" en el campo correspondiente
- No puedes exceder los 640 caracteres en la respuesta del campo "message"
- Nunca digas cuantos años de experiencia tienes, solo menciona que eres un fotógrafo profesional
- Di los años de experiencia si y solo si el usuario te lo pregunta explícitamente.
- Enumera siempre priorizando la narrativa.
- Antes de reservar, comprueba siempre la disponibilidad usando get_available_slots()
- Si el usuario pregunta por días festivos, responde que el negocio está cerrado esos días.
- Si el usuario pregunta por servicios, explícalos con pasión y naturalidad, no copies y pegues la lista. Si es para una boda, céntrate en ese servicio.
- Si el usuario menciona una boda o evento importante, ¡felicítalo y muestra entusiasmo genuino!
- Si el usuario hace una pregunta de tipo general o de cortesía, responde como un humano normal (smalltalk).
- Siempre incluye una pregunta en tu respuesta para avanzar en la conversación, a menos que sea una despedida o agradecimiento final.
- A la hora de hacer la reserva  de la cita presencial lo primero es saber que dia y hora la quiere el cliente. despues se toman los datos personales que se necesitan mail, telefono, etc.  

- No respondas a "me caso en [fecha]" con "enhorabuena por tu boda en [fecha]", di simplemente "Enhorabuena!" o "ya me alegro!".

Ejemplos Responde siempre con un mensaje que incluya una pregunta para avanzar en la reserva.
1. Usuario: "¿Tienes disponibilidad el 2025-12-25?"
2. Negocio: {{"intent": "check_availability", "date": "2025-12-25", "time": null, "message": "El 25 de diciembre es Navidad y estamos cerrados. ¿Qué otro día te viene bien?"}}
3. Usuario: "Quiero reservar una cita para el 2025-05-10 a las 15:00."
4. Negocio: {{"intent": "book", "date": "2025-05-10", "time": "15:00", "message": "Perfecto, he reservado tu cita para el 10 de mayo de 2025 a las 15:00. ¡Te esperamos!"}}
5. Usuario: "Hola, ¿qué servicios ofreces?"
6. Negocio: {{"intent": "smalltalk", "date": null, "time": null, "message": "¡Hola! Ofrecemos servicios de fotografía y cobertura de eventos. ¿En qué puedo ayudarte hoy?"}}'''
# -----------------------------------

SYSTEM_PROMPT = f"""
{PERSONALITY}
{BUSINESS_CONTEXT}
{REGLAS}

RESPONDE SOLO con un JSON válido sin ningún texto adicional. Nada más.
El JSON debe tener el formato EXACTO:

Formato:
{{
  "intent": "smalltalk | check_availability | book | unknown",
  "date": "YYYY-MM-DD | null | RESET",
  "time": "HH:MM | null | RESET",
  "event_details": "string | null",
  "customer_name": "string | null",
  "customer_email": "string | null",
  "customer_phone": "string | null",
  "event_date": "string | null",
  "message": "respuesta al cliente"
}}

"""

def cloud_chat(model: str, messages: list):
    """
    Hace una petición de chat a Ollama y devuelve el JSON completo.
    """
    headers = {"Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": 0.5,
            "top_p": 0.9
        }
    }

    response = requests.post(
        f"{OLLAMA_API_BASE}/chat",
        headers=headers,
        json=payload,
        timeout=60  # Añadimos un timeout de 60 segundos
    )

    if not response.ok:
        raise Exception(f"Error en Ollama: {response.status_code} {response.text}")

    return response.json()

def is_slot_available(business_id, date_str, time_str):
    db = SessionLocal()
    try:
        check_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        
        if check_date < datetime.now().date():
            return False

        if is_holiday(check_date):
            return False

        check_time = datetime.strptime(time_str, "%H:%M").time()
        
        existing = db.query(Booking).filter_by(
            business_id=business_id,
            date=check_date,
            start_time=check_time
        ).first()
        return existing is None
    finally:
        db.close()

def send_confirmation_email(to_email, customer_name, date_str, time_str):
    # Configuración SMTP (Cargar desde .env para producción)
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")

    if not smtp_user or not smtp_password:
        print("⚠️ Credenciales SMTP no configuradas. No se envió el correo de confirmación.")
        return

    subject = "Confirmación de Cita - Estudio de Fotografía"
    body = f"""
    Hola {customer_name},

    Tu cita ha sido confirmada correctamente.

    📅 Fecha: {date_str}
    ⏰ Hora: {time_str}

    ¡Gracias por confiar en nosotros!
    """

    msg = MIMEMultipart()
    msg["From"] = smtp_user
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.sendmail(smtp_user, to_email, msg.as_string())
        server.quit()
        print(f"📧 Correo de confirmación enviado a {to_email}")
    except Exception as e:
        print(f"❌ Error enviando correo: {e}")

def send_admin_notification(session):
    """
    Envía un correo a los socios del negocio con los detalles de la nueva reserva.
    """
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    # Obtener emails de los socios desde el .env (separados por comas)
    # Si no está configurado, usa el mismo email de envío para probar
    admin_emails_str = os.getenv("ADMIN_EMAILS", smtp_user)
    
    if not smtp_user or not smtp_password or not admin_emails_str:
        print("⚠️ No se puede enviar notificación a socios: faltan credenciales.")
        return

    admin_emails = [e.strip() for e in admin_emails_str.split(",") if e.strip()]
    
    subject = f"🔔 Nueva Reserva: {session.get('date')} a las {session.get('time')}"
    body = f"""
    ¡Hola! Tenéis una nueva cita confirmada.

    👤 Cliente: {session.get('customer_name', 'N/A')}
    📧 Email: {session.get('customer_email', 'N/A')}
    📞 Teléfono: {session.get('customer_phone', 'N/A')}

    📅 Fecha: {session.get('date')}
    ⏰ Hora: {session.get('time')}
    
    📝 Detalles:
    {session.get('event_details', 'Sin detalles adicionales')}
    """

    try:
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        
        for email in admin_emails:
            msg = MIMEMultipart()
            msg["From"] = smtp_user
            msg["To"] = email
            msg["Subject"] = subject
            msg.attach(MIMEText(body, "plain"))
            server.sendmail(smtp_user, email, msg.as_string())
            
        server.quit()
        print(f"📧 Notificación enviada a socios: {admin_emails}")
    except Exception as e:
        print(f"❌ Error enviando notificación a socios: {e}")

def create_event(business_id, session):
    db = SessionLocal()
    try:
        new_booking = Booking(
            business_id=business_id,
            date=datetime.strptime(session["date"], "%Y-%m-%d").date(),
            start_time=datetime.strptime(session["time"], "%H:%M").time(),
            customer_name=session.get("customer_name"),
            customer_email=session.get("customer_email"),
            customer_phone=session.get("customer_phone"),
            event_date=session.get("event_date"),
            event_details=session.get("event_details")
        )
        db.add(new_booking)
        db.commit()
        print(f"✅ Cita guardada en BD: {session['date']} a las {session['time']} para {session.get('customer_name')}")
        
        # Enviar correo si tenemos el email
        if session.get("customer_email"):
            send_confirmation_email(
                session["customer_email"],
                session.get("customer_name", "Cliente"),
                session["date"],
                session["time"]
            )
        
        # Notificar a los socios (tú y tu socia)
        send_admin_notification(session)

        return True
    except Exception as e:
        print(f"❌ Error guardando cita: {e}")
        return False
    finally:
        db.close()

def handle_chat(business_id: str, session_id: str, message: str):
    session = get_session(session_id)
    db = SessionLocal()
    try:
        # Inyectar contexto actual para que el LLM sepa qué está pasando
        context_str = f"\nContexto actual: Intent={session.get('intent')}, Date={session.get('date')}, Time={session.get('time')}, CustomerName={session.get('customer_name')}"

        # Recuperar historial de la sesión
        history = session.get("history", [])

        messages = [{"role": "system", "content": SYSTEM_PROMPT + context_str}]
        messages.extend(history)
        messages.append({"role": "user", "content": message})

        # --- INICIO DE LA LLAMADA AL LLM ---
        # Este bloque es propenso a errores de red o del propio modelo.
        # Lo envolvemos en un try...except para capturar cualquier fallo.
        try:
            response = cloud_chat(model=OLLAMA_MODEL, messages=messages)
        except Exception as e:
            print(f"❌ Error crítico al contactar con Ollama: {e}")
            # Devolvemos un error claro al frontend en lugar de dejar que la app crashe.
            return {"reply": "Lo siento, mi cerebro artificial (LLM) no está respondiendo. Por favor, contacta con un administrador.", "status": "error"}
        # --- FIN DE LA LLAMADA AL LLM ---

        print(">>> Respuesta recibida del modelo LLM:")
        print(response)

        raw = response["message"]["content"].strip()
        print(">>> Texto bruto del LLM:")
        print(raw)

        # 🔹 Extraer bloque JSON del texto
        try:
            json_match = re.search(r'{.*}', raw, re.DOTALL)
            if not json_match:
                raise ValueError("No se encontró JSON en la respuesta del LLM")
            json_str = json_match.group(0)
            data = json.loads(json_str)
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            return {"reply": "Error procesando la respuesta.", "status": "error"}

        # Guardar en el historial (limitado a los últimos 10 mensajes para no saturar)
        history.append({"role": "user", "content": message})
        history.append({"role": "assistant", "content": raw}) # Guardamos el JSON crudo para que el LLM mantenga el formato
        session["history"] = history[-10:]

        # 2️⃣ Actualizar estado
        for key in ["intent", "date", "time", "event_details", "customer_name", "customer_email", "customer_phone", "event_date"]:
            val = data.get(key)
            if val == "RESET":
                session[key] = None
            elif val:
                session[key] = val

        # Si estamos consultando disponibilidad pero ya tenemos fecha y hora, pasamos a reservar
        if session.get("intent") == "check_availability" and session.get("date") and session.get("time"):
            session["intent"] = "book"
            session['slot_confirmed'] = False # Forzamos la comprobación de disponibilidad

        # 3️⃣ Flujo real
        if session.get("intent") == "check_availability":
            if not session.get("date"):
                return {"reply": data.get("message", "¿Para qué fecha?"), "status": "need_info"}

            slots = get_available_slots(
                business_id=business_id,
                date=datetime.strptime(session["date"], "%Y-%m-%d").date(),
                db=db
            )

            if not slots:
                check_date = datetime.strptime(session["date"], "%Y-%m-%d").date()
                
                # 1. Validar fecha pasada
                if check_date < datetime.now().date():
                     return {"reply": f"No puedo darte disponibilidad para el pasado ({session['date']}).", "status": "need_info"}
                
                # 2. Validar festivo
                if is_holiday(check_date):
                     return {"reply": f"El {session['date']} es festivo. ¿Buscas otro día?", "status": "need_info"}

                # 3. Validar si estamos cerrados (ej. Domingo)
                weekday = check_date.weekday()
                schedule = db.query(WeeklySchedule).filter_by(business_id=business_id, weekday=weekday).first()
                if not schedule:
                     # Buscar el siguiente día laborable
                     next_date = check_date
                     found_next = False
                     for _ in range(7):
                         next_date += timedelta(days=1)
                         next_weekday = next_date.weekday()
                         next_schedule = db.query(WeeklySchedule).filter_by(business_id=business_id, weekday=next_weekday).first()
                         if next_schedule and not is_holiday(next_date):
                             found_next = True
                             break
                     
                     if found_next:
                         original_date = session['date']
                         # Actualizamos la sesión con la fecha sugerida para romper el bucle
                         session['date'] = next_date.strftime('%Y-%m-%d')
                         return {"reply": f"El {original_date} estamos cerrados. Nuestro próximo día abierto es el {session['date']}. ¿Te encaja?", "status": "need_info"}

                     return {"reply": f"El {session['date']} estamos cerrados. Abrimos de Lunes a Sábado.", "status": "need_info"}

                return {
                    "reply": f"Lo siento, la agenda para el {session['date']} está completa.",
                    "status": "success"
                }

            # Ordenar slots priorizando las 17:00
            target_time = 17 * 60 # 17:00 en minutos
            slots.sort(key=lambda t: abs((t.hour * 60 + t.minute) - target_time))

            horarios = ", ".join(s.strftime("%H:%M") for s in slots)
            return {
                "reply": f"Hay disponibilidad a las {horarios}. ¿Cuál prefieres?",
                "status": "success"
            }

        if session.get("intent") == "book":
            if not session.get("date"):
                return {"reply": data.get("message", "¿Qué día?"), "status": "need_info"}
            if not session.get("time"):
                return {"reply": data.get("message", "¿A qué hora?"), "status": "need_info"}

            # ⛔ Comprobar disponibilidad solo una vez por intento de reserva
            if not session.get('slot_confirmed'):
                if not is_slot_available(business_id, session["date"], session["time"]):
                    date_obj = datetime.strptime(session["date"], "%Y-%m-%d").date()
                    
                    if date_obj < datetime.now().date():
                        session["time"] = None
                        return {"reply": f"No es posible reservar en el pasado ({session['date']}). Por favor, elige una fecha futura.", "status": "need_info"}

                    if is_holiday(date_obj):
                        session["time"] = None
                        return {"reply": f"El {session['date']} es festivo y estamos cerrados. ¿Qué otro día te viene bien?", "status": "need_info"}

                    slots = get_available_slots(business_id, date_obj, db)
                    session["time"] = None

                    if slots:
                        horarios = ", ".join(s.strftime("%H:%M") for s in slots)
                        return {"reply": f"Ese horario ya no está disponible. Para el {session['date']} quedan libres: {horarios}.", "status": "need_info"}
                    return {"reply": f"Lo siento, no quedan huecos libres para el {session['date']}.", "status": "need_info"}
                
                session['slot_confirmed'] = True

            # 🙋‍♂️ Recopilar datos del cliente secuencialmente
            # Primero, sondear sobre el evento
            if not session.get("event_details"):
                return {"reply": data.get("message", "¡Genial! El hueco está disponible. Para hacerme una idea, ¿me cuentas un poco sobre la boda? Dónde será, número de invitados..."), "status": "need_info"}

            if not session.get("customer_name"):
                return {"reply": data.get("message", "¡Estupendo! Para confirmar, ¿a nombre de quién hago la reserva?"), "status": "need_info"}
            if not session.get("customer_email"):
                return {"reply": data.get("message", "Perfecto, ¿me podrías dar un email de contacto?"), "status": "need_info"}
            if not session.get("customer_phone"):
                return {"reply": data.get("message", "Ya casi lo tenemos. ¿Y un teléfono?"), "status": "need_info"}
            if not session.get("event_date"):
                 return {"reply": data.get("message", "Por último, ¿cuál es la fecha de la boda o evento?"), "status": "need_info"}

            # ✅ crear evento
            if create_event(business_id, session):
                # Preservar el nombre del cliente para futuras interacciones
                saved_name = session.get("customer_name")
                clear_session(session_id)
                session.clear() # Limpia el objeto de sesión en memoria para el resto de esta ejecución
                if saved_name:
                    session["customer_name"] = saved_name

                return {
                    "reply": "¡Cita confirmada! He anotado todos los detalles. Recibirás una confirmación en breve. ¡Hablamos pronto!",
                    "status": "success"
                }
            else:
                return {
                    "reply": "Lo siento, hubo un error interno al guardar la cita. Por favor, inténtalo de nuevo.",
                    "status": "error"
                }

        return {
            "reply": data.get("message", "¿Puedes concretar un poco más?"),
            "status": "success"
        }
    except Exception as e:
        # Captura cualquier otra excepción no esperada en la lógica del agente.
        print(f"❌ Error inesperado en handle_chat: {e}")
        # Proporciona una respuesta de error genérica pero controlada.
        return {"reply": "Ha ocurrido un error interno inesperado. He notificado al equipo técnico.", "status": "error"}
    finally:
        save_session(session_id, session)
        db.close()
