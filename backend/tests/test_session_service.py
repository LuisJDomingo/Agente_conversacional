from app.services import session_service


class BrokenRedis:
    def get(self, *args, **kwargs):
        raise RuntimeError("redis down")

    def set(self, *args, **kwargs):
        raise RuntimeError("redis down")

    def delete(self, *args, **kwargs):
        raise RuntimeError("redis down")


class HealthyRedis:
    def __init__(self):
        self.store = {}

    def get(self, key):
        return self.store.get(key)

    def set(self, key, value, ex=None):
        self.store[key] = value

    def delete(self, key):
        self.store.pop(key, None)


def test_session_service_fallback_when_redis_is_unavailable(monkeypatch):
    monkeypatch.setattr(session_service, "_redis_client", BrokenRedis())
    session_service._fallback_sessions.clear()

    session = session_service.get_session("abc")
    assert session == {"history": []}

    session["intent"] = "book"
    session_service.save_session("abc", session)

    loaded = session_service.get_session("abc")
    assert loaded["intent"] == "book"

    session_service.clear_session("abc")
    assert session_service.get_session("abc") == {"history": []}


def test_session_service_prefers_redis_when_available(monkeypatch):
    monkeypatch.setattr(session_service, "_redis_client", HealthyRedis())
    session_service._fallback_sessions.clear()

    session = session_service.get_session("redis-ok")
    assert session == {"history": []}

    session["foo"] = "bar"
    session_service.save_session("redis-ok", session)

    loaded = session_service.get_session("redis-ok")
    assert loaded["foo"] == "bar"
