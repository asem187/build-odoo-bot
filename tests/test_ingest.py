import os
from pathlib import Path
from importlib import reload

from scripts import ingest_docs


class DummyEmbeddings:
    def embed_documents(self, texts):
        return [[0.0] * 5 for _ in texts]

    def embed_query(self, text):
        return [0.0] * 5


def test_ingest(monkeypatch, tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "readme.md").write_text("# Title\ncontent")
    index = tmp_path / "index"
    monkeypatch.setenv("DOCS_PATH", str(docs))
    monkeypatch.setenv("INDEX_PATH", str(index))
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test")
    monkeypatch.setattr(ingest_docs, "fetch_docs", lambda dest: docs)
    reload(ingest_docs)
    monkeypatch.setattr(ingest_docs, "OpenAIEmbeddings", lambda: DummyEmbeddings())
    ingest_docs.main()
    assert (index / "index.faiss").exists()
