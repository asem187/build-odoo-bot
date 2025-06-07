import src.main as main
from fastapi.testclient import TestClient


class BadAgent:
    def run(self, message):
        raise ValueError("boom")


def test_global_error_handler(monkeypatch):
    monkeypatch.setattr(main, "get_cached_agent", lambda: BadAgent())
    monkeypatch.setenv("API_TOKEN", "test")
    with TestClient(main.app, raise_server_exceptions=False) as client:
        response = client.post(
            "/chat",
            json={"message": "hi"},
            headers={"Authorization": "Bearer test"},
        )
    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}

