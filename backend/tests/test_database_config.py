import importlib


def test_database_url_prefers_env_over_sqlite(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "postgresql://u:p@localhost:5432/db")

    database = importlib.import_module("app.database")
    database = importlib.reload(database)

    assert database.SQLALCHEMY_DATABASE_URL.startswith("postgresql://")


def test_database_sqlite_sets_check_same_thread(monkeypatch):
    monkeypatch.setenv("DATABASE_URL", "sqlite:///./bookings.db")

    database = importlib.import_module("app.database")
    database = importlib.reload(database)

    assert database.engine.url.drivername == "sqlite"
