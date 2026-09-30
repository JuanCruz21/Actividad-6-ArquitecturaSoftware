import pytest
from fastapi.testclient import TestClient

from labcloud import config


@pytest.fixture
def cliente(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "prueba.db")
    from labcloud.main import app

    with TestClient(app) as c:
        yield c


def _login(cliente, correo, password):
    r = cliente.post("/api/auth/login", json={"correo": correo, "password": password})
    assert r.status_code == 200, r.text
    return {"Authorization": f"Bearer {r.json()['token']}"}


@pytest.fixture
def recepcion(cliente):
    return _login(cliente, "recepcion@labcloud.test", "recepcion123")


@pytest.fixture
def analista(cliente):
    return _login(cliente, "analista@labcloud.test", "analista123")


@pytest.fixture
def admin(cliente):
    return _login(cliente, "admin@labcloud.test", "admin123")
