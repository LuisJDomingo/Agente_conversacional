from datetime import date, timedelta, time

from app.services import llm_agent


class DummyDBSession:
    def close(self):
        return None


class DummySessionFactory:
    def __call__(self):
        return DummyDBSession()


def _patch_common(monkeypatch, session_data):
    saved = {}

    monkeypatch.setattr(llm_agent, "SessionLocal", DummySessionFactory())
    monkeypatch.setattr(llm_agent, "get_session", lambda _sid: session_data)
    monkeypatch.setattr(
        llm_agent,
        "save_session",
        lambda sid, data: saved.update({"session_id": sid, "data": data.copy()}),
    )
    return saved


def test_handle_chat_returns_error_if_llm_is_down(monkeypatch):
    saved = _patch_common(monkeypatch, {"history": []})

    def _raise_cloud_chat(*args, **kwargs):
        raise RuntimeError("Ollama caído")

    monkeypatch.setattr(llm_agent, "cloud_chat", _raise_cloud_chat)

    result = llm_agent.handle_chat("demo", "sess-1", "hola")

    assert result["status"] == "error"
    assert "no está respondiendo" in result["reply"]
    assert saved["session_id"] == "sess-1"


def test_handle_chat_returns_error_if_llm_json_is_invalid(monkeypatch):
    _patch_common(monkeypatch, {"history": []})

    monkeypatch.setattr(
        llm_agent,
        "cloud_chat",
        lambda **kwargs: {"message": {"content": "respuesta sin json"}},
    )

    result = llm_agent.handle_chat("demo", "sess-2", "hola")

    assert result == {"reply": "Error procesando la respuesta.", "status": "error"}


def test_handle_chat_check_availability_without_date_requests_more_info(monkeypatch):
    _patch_common(monkeypatch, {"history": []})

    monkeypatch.setattr(
        llm_agent,
        "cloud_chat",
        lambda **kwargs: {
            "message": {
                "content": '{"intent":"check_availability","date":null,"time":null,'
                '"event_details":null,"customer_name":null,"customer_email":null,'
                '"customer_phone":null,"event_date":null,'
                '"message":"¿Qué fecha te viene bien?"}'
            }
        },
    )

    result = llm_agent.handle_chat("demo", "sess-3", "quiero saber disponibilidad")

    assert result["status"] == "need_info"
    assert result["reply"] == "¿Qué fecha te viene bien?"


def test_handle_chat_slot_taken_suggests_alternative_hours(monkeypatch):
    session_data = {"history": []}
    saved = _patch_common(monkeypatch, session_data)

    target_date = (date.today() + timedelta(days=2)).strftime("%Y-%m-%d")

    monkeypatch.setattr(
        llm_agent,
        "cloud_chat",
        lambda **kwargs: {
            "message": {
                "content": '{"intent":"book","date":"'
                + target_date
                + '","time":"10:00","event_details":null,'
                '"customer_name":null,"customer_email":null,"customer_phone":null,'
                '"event_date":null,"message":"Perfecto"}'
            }
        },
    )
    monkeypatch.setattr(llm_agent, "is_slot_available", lambda *args, **kwargs: False)
    monkeypatch.setattr(llm_agent, "is_holiday", lambda _date: False)
    monkeypatch.setattr(llm_agent, "get_available_slots", lambda *args, **kwargs: [time(9, 0), time(11, 0)])

    result = llm_agent.handle_chat("demo", "sess-4", "reserva")

    assert result["status"] == "need_info"
    assert "09:00, 11:00" in result["reply"]
    assert saved["data"]["time"] is None


def test_handle_chat_creates_booking_when_all_data_is_complete(monkeypatch):
    session_data = {"history": []}
    saved = _patch_common(monkeypatch, session_data)

    called = {"clear": None, "create": False}
    target_date = (date.today() + timedelta(days=3)).strftime("%Y-%m-%d")

    monkeypatch.setattr(
        llm_agent,
        "cloud_chat",
        lambda **kwargs: {
            "message": {
                "content": '{"intent":"book","date":"'
                + target_date
                + '","time":"12:00","event_details":"Boda íntima",'
                '"customer_name":"Ana Pérez","customer_email":"ana@mail.com",'
                '"customer_phone":"600112233","event_date":"2026-06-20",'
                '"message":"Genial"}'
            }
        },
    )
    monkeypatch.setattr(llm_agent, "is_slot_available", lambda *args, **kwargs: True)
    monkeypatch.setattr(
        llm_agent,
        "create_event",
        lambda *args, **kwargs: called.update({"create": True}) or True,
    )
    monkeypatch.setattr(llm_agent, "clear_session", lambda sid: called.update({"clear": sid}))

    result = llm_agent.handle_chat("demo", "sess-5", "quiero cerrar reserva")

    assert result["status"] == "success"
    assert "¡Cita confirmada!" in result["reply"]
    assert called["create"] is True
    assert called["clear"] == "sess-5"
    assert saved["data"].get("customer_name") == "Ana Pérez"


def test_handle_chat_rejects_booking_in_past(monkeypatch):
    session_data = {"history": []}
    saved = _patch_common(monkeypatch, session_data)

    past_date = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")

    monkeypatch.setattr(
        llm_agent,
        "cloud_chat",
        lambda **kwargs: {
            "message": {
                "content": '{"intent":"book","date":"'
                + past_date
                + '","time":"10:00","event_details":null,'
                '"customer_name":null,"customer_email":null,"customer_phone":null,'
                '"event_date":null,"message":"Vale"}'
            }
        },
    )
    monkeypatch.setattr(llm_agent, "is_slot_available", lambda *args, **kwargs: False)

    result = llm_agent.handle_chat("demo", "sess-6", "reserva")

    assert result["status"] == "need_info"
    assert "pasado" in result["reply"]
    assert saved["data"]["time"] is None


def test_handle_chat_rejects_holiday_booking(monkeypatch):
    session_data = {"history": []}
    saved = _patch_common(monkeypatch, session_data)

    future_date = (date.today() + timedelta(days=5)).strftime("%Y-%m-%d")

    monkeypatch.setattr(
        llm_agent,
        "cloud_chat",
        lambda **kwargs: {
            "message": {
                "content": '{"intent":"book","date":"'
                + future_date
                + '","time":"10:00","event_details":null,'
                '"customer_name":null,"customer_email":null,"customer_phone":null,'
                '"event_date":null,"message":"Vale"}'
            }
        },
    )
    monkeypatch.setattr(llm_agent, "is_slot_available", lambda *args, **kwargs: False)
    monkeypatch.setattr(llm_agent, "is_holiday", lambda _date: True)

    result = llm_agent.handle_chat("demo", "sess-7", "reserva")

    assert result["status"] == "need_info"
    assert "festivo" in result["reply"]
    assert saved["data"]["time"] is None


def test_handle_chat_availability_sorts_slots_around_17(monkeypatch):
    _patch_common(monkeypatch, {"history": []})

    target_date = (date.today() + timedelta(days=4)).strftime("%Y-%m-%d")

    monkeypatch.setattr(
        llm_agent,
        "cloud_chat",
        lambda **kwargs: {
            "message": {
                "content": '{"intent":"check_availability","date":"'
                + target_date
                + '","time":null,"event_details":null,'
                '"customer_name":null,"customer_email":null,"customer_phone":null,'
                '"event_date":null,"message":"Te cuento"}'
            }
        },
    )
    monkeypatch.setattr(
        llm_agent,
        "get_available_slots",
        lambda *args, **kwargs: [time(9, 0), time(17, 0), time(16, 0)],
    )

    result = llm_agent.handle_chat("demo", "sess-8", "¿qué tienes?")

    assert result["status"] == "success"
    assert result["reply"] == "Hay disponibilidad a las 17:00, 16:00, 09:00. ¿Cuál prefieres?"
