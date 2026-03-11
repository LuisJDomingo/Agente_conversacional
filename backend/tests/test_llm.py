from fastapi.testclient import TestClient

from app.main import app


def test_root_healthcheck():
    client = TestClient(app)
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "API corriendo correctamente"}


def test_agent_chat_delegates_to_handle_chat(monkeypatch):
    client = TestClient(app)

    calls = {}

    def fake_handle_chat(business_id, session_id, message):
        calls["args"] = (business_id, session_id, message)
        return {"reply": "ok", "status": "success"}

    monkeypatch.setattr("app.api.agent.handle_chat", fake_handle_chat)

    payload = {
        "business_id": "demo",
        "session_id": "web-123",
        "message": "Hola, quiero reservar",
    }
    response = client.post("/agent/chat", json=payload)

    assert response.status_code == 200
    assert response.json() == {"reply": "ok", "status": "success"}
    assert calls["args"] == ("demo", "web-123", "Hola, quiero reservar")


def test_agent_chat_validates_required_fields():
    client = TestClient(app)
    response = client.post("/agent/chat", json={"business_id": "demo", "message": "hola"})

    assert response.status_code == 422
