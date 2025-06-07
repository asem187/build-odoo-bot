from fastapi.testclient import TestClient
import src.main as main

app = main.app
client = TestClient(app)

def test_voice_ws(monkeypatch):
    monkeypatch.setattr(main, 'get_cached_agent', lambda: type('A', (), {'run': lambda self, m: 'hi'})())
    monkeypatch.setattr(main.openai.Audio, 'transcribe', lambda model, data: {'text': 'hello'}, raising=False)
    monkeypatch.setenv("API_TOKEN", "test")
    with client.websocket_connect('/ws/voice', headers={"Authorization": "Bearer test"}) as ws:
        ws.send_bytes(b'0')
        ws.send_text('END')
        data = ws.receive_json()
    assert data['response'] == 'hi'
    assert data['transcript'] == 'hello'
