import os
import subprocess
from pathlib import Path


if __name__ == "__main__":
    index_path = Path(os.getenv("INDEX_PATH", "data/index"))
    if not index_path.exists():
        subprocess.run(["python", "scripts/ingest_docs.py"], check=True)

    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    subprocess.run([
        "uvicorn",
        "src.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ])
