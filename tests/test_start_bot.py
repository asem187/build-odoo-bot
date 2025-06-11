import start_bot
import os

class DummyScheduler:
    def __init__(self):
        self.jobs = []
        self.started = False
        self.stopped = False
    def add_job(self, func, trigger, hours):
        self.jobs.append((func, trigger, hours))
    def start(self):
        self.started = True
    def shutdown(self):
        self.stopped = True

def test_scheduler(monkeypatch):
    monkeypatch.setattr(start_bot, "BackgroundScheduler", DummyScheduler)
    calls = []
    monkeypatch.setattr(start_bot, "ingest_docs", lambda: calls.append("ingest"))
    monkeypatch.setenv("INGEST_INTERVAL_HOURS", "0.01")
    monkeypatch.setenv("HOST", "127.0.0.1")
    monkeypatch.setenv("PORT", "8001")
    monkeypatch.setattr(start_bot.subprocess, "run", lambda *a, **k: calls.append(a))
    start_bot.main()
    assert calls[0] == "ingest" or calls == []
