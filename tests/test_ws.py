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


def test_voice_ws_stream(monkeypatch):
    class DummyAgent:
        def stream(self, message):
            for t in ['h', 'i']:
                yield t
    monkeypatch.setattr(main, 'get_cached_agent', lambda: DummyAgent())
    monkeypatch.setattr(main.openai.Audio, 'transcribe', lambda model, data: {'text': 'hello'}, raising=False)
    monkeypatch.setenv("API_TOKEN", "test")
    with client.websocket_connect('/ws/voice', headers={"Authorization": "Bearer test", "X-Stream": "1"}) as ws:
        ws.send_bytes(b'0')
        ws.send_text('END')
        t1 = ws.receive_text()
        t2 = ws.receive_text()
        data = ws.receive_json()
    assert t1 == 'h'
    assert t2 == 'i'
    assert data['response'] == 'hi'
