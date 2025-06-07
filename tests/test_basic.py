from pathlib import Path
import sys

from fastapi.testclient import TestClient

# Ensure src is on path
sys.path.append(str(Path(__file__).resolve().parents[1]))

import src.main as main


def test_root(monkeypatch):
    class Dummy:
        pass
    monkeypatch.setattr(main, "get_cached_agent", lambda: Dummy())
    with TestClient(main.app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "Odoo bot" in response.json().get("message", "")


def test_chat(monkeypatch):
    class Dummy:
        def run(self, message):
            return "hi"
    monkeypatch.setattr(main, "get_cached_agent", lambda: Dummy())
    monkeypatch.setenv("API_TOKEN", "test")
    with TestClient(main.app) as client:
        response = client.post(
            "/chat",
            json={"message": "hello"},
            headers={"Authorization": "Bearer test"},
        )
    assert response.status_code == 200
    assert response.json()["response"] == "hi"


def test_chat_unauthorized(monkeypatch):
    class Dummy:
        def run(self, message):
            return "hi"
    monkeypatch.setattr(main, "get_cached_agent", lambda: Dummy())
    monkeypatch.setenv("API_TOKEN", "test")
    with TestClient(main.app) as client:
        response = client.post("/chat", json={"message": "hello"})
    assert response.status_code == 401


def test_voice(monkeypatch, tmp_path):
    class Dummy:
        def run(self, message):
            return "hi"
    monkeypatch.setattr(main, "get_cached_agent", lambda: Dummy())
    monkeypatch.setenv("API_TOKEN", "test")
    monkeypatch.setattr(main.openai.Audio, "transcribe", lambda model, file: {"text": "hello"})
    dummy_audio = tmp_path / "test.mp3"
    dummy_audio.write_bytes(b"0")
    with dummy_audio.open("rb") as f:
        with TestClient(main.app) as client:
            response = client.post(
                "/voice",
                files={"file": ("test.mp3", f, "audio/mpeg")},
                headers={"Authorization": "Bearer test"},
            )
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == "hi"
    assert data["transcript"] == "hello"


def test_search(monkeypatch):
    class DummyModel:
        def search(self, domain):
            return [1]

        def read(self, ids):
            return [{"id": 1, "name": "Test"}]

    class DummyOdoo:
        def __init__(self):
            self.env = {"res.partner": DummyModel()}

    monkeypatch.setattr(main, "get_cached_odoo", lambda: DummyOdoo())
    monkeypatch.setenv("API_TOKEN", "test")
    with TestClient(main.app) as client:
        response = client.post(
            "/search",
            json={"model": "res.partner", "query": "Test"},
            headers={"Authorization": "Bearer test"},
        )
    assert response.status_code == 200
    assert response.json()["results"] == [{"id": 1, "name": "Test"}]


def test_search_unauthorized(monkeypatch):
    class DummyModel:
        def search(self, domain):
            return [1]

        def read(self, ids):
            return [{"id": 1, "name": "Test"}]

    class DummyOdoo:
        def __init__(self):
            self.env = {"res.partner": DummyModel()}

    monkeypatch.setattr(main, "get_cached_odoo", lambda: DummyOdoo())
    monkeypatch.setenv("API_TOKEN", "test")
    with TestClient(main.app) as client:
        response = client.post(
            "/search",
            json={"model": "res.partner", "query": "Test"},
        )
    assert response.status_code == 401
