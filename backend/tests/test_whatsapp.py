from fastapi.testclient import TestClient

from app.main import app
from app.api import whatsapp


def test_whatsapp_webhook_ignores_other_events():
    client = TestClient(app)

    payload = {
        "instance": "BookingAgent",
        "webhook": "http://example.com",
        "event": "messages.update",
        "data": {"messages": []},
    }

    response = client.post("/whatsapp/webhook", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"


def test_whatsapp_webhook_processes_text_message(monkeypatch):
    client = TestClient(app)

    sent = {}

    def fake_handle_chat(business_id, session_id, message):
        sent["chat_args"] = (business_id, session_id, message)
        return {"reply": "Perfecto, te ayudo", "status": "success"}

    async def fake_send_whatsapp_message(phone_number, message):
        sent["send_args"] = (phone_number, message)

    monkeypatch.setattr("app.api.whatsapp.handle_chat", fake_handle_chat)
    monkeypatch.setattr("app.api.whatsapp.send_whatsapp_message", fake_send_whatsapp_message)

    payload = {
        "instance": "BookingAgent",
        "webhook": "http://example.com",
        "event": "messages.upsert",
        "data": {
            "messages": [
                {
                    "key": {
                        "remoteJid": "34600111222@s.whatsapp.net",
                        "fromMe": False,
                        "id": "abc123",
                    },
                    "message": {"conversation": "Hola"},
                    "pushName": "Cliente",
                    "messageTimestamp": "1720000000",
                }
            ]
        },
    }

    response = client.post("/whatsapp/webhook", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert sent["chat_args"] == ("demo", "34600111222", "Hola")
    assert sent["send_args"] == ("34600111222", "Perfecto, te ayudo")


def test_whatsapp_webhook_skips_messages_from_bot(monkeypatch):
    client = TestClient(app)

    called = {"chat": False, "send": False}

    def fake_handle_chat(*args, **kwargs):
        called["chat"] = True
        return {"reply": "x", "status": "success"}

    async def fake_send_whatsapp_message(*args, **kwargs):
        called["send"] = True

    monkeypatch.setattr("app.api.whatsapp.handle_chat", fake_handle_chat)
    monkeypatch.setattr("app.api.whatsapp.send_whatsapp_message", fake_send_whatsapp_message)

    payload = {
        "instance": "BookingAgent",
        "webhook": "http://example.com",
        "event": "messages.upsert",
        "data": {
            "messages": [
                {
                    "key": {
                        "remoteJid": "34600111222@s.whatsapp.net",
                        "fromMe": True,
                        "id": "abc123",
                    },
                    "message": {"conversation": "Hola"},
                    "pushName": "Bot",
                    "messageTimestamp": "1720000000",
                }
            ]
        },
    }

    response = client.post("/whatsapp/webhook", json=payload)

    assert response.status_code == 200
    assert response.json()["status"] == "success"
    assert called["chat"] is False
    assert called["send"] is False


def test_compute_human_delay_is_within_bounds(monkeypatch):
    monkeypatch.setattr(whatsapp, "WHATSAPP_MIN_DELAY_MS", 900)
    monkeypatch.setattr(whatsapp, "WHATSAPP_MAX_DELAY_MS", 1500)

    delay = whatsapp._compute_human_delay_ms("Mensaje breve")

    assert 900 <= delay <= 1500


def test_can_send_now_enforces_min_interval(monkeypatch):
    monkeypatch.setattr(whatsapp, "WHATSAPP_MIN_SECONDS_BETWEEN_MESSAGES", 2.5)
    whatsapp._last_sent_by_number.clear()

    assert whatsapp._can_send_now("34600111222", now_ts=100.0) is True
    assert whatsapp._can_send_now("34600111222", now_ts=101.0) is False
    assert whatsapp._can_send_now("34600111222", now_ts=103.0) is True


def test_whatsapp_webhook_rejects_invalid_token(monkeypatch):
    client = TestClient(app)

    monkeypatch.setattr(whatsapp, "WEBHOOK_VERIFY_TOKEN", "super-secret")

    payload = {
        "instance": "BookingAgent",
        "webhook": "http://example.com",
        "event": "messages.upsert",
        "data": {"messages": []},
    }

    response = client.post("/whatsapp/webhook", json=payload, headers={"x-webhook-token": "wrong"})

    assert response.status_code == 401


def test_whatsapp_webhook_accepts_valid_token(monkeypatch):
    client = TestClient(app)

    monkeypatch.setattr(whatsapp, "WEBHOOK_VERIFY_TOKEN", "super-secret")

    payload = {
        "instance": "BookingAgent",
        "webhook": "http://example.com",
        "event": "messages.update",
        "data": {"messages": []},
    }

    response = client.post("/whatsapp/webhook", json=payload, headers={"x-webhook-token": "super-secret"})

    assert response.status_code == 200
    assert response.json()["status"] == "ignored"
