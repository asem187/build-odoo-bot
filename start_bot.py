import os
import subprocess
from pathlib import Path
from apscheduler.schedulers.background import BackgroundScheduler


def ingest_docs():
    """Run the documentation ingestion script."""
    subprocess.run(["python", "scripts/ingest_docs.py"], check=True)


def main():
    index_path = Path(os.getenv("INDEX_PATH", "data/index"))
    if not index_path.exists():
        ingest_docs()

    interval = float(os.getenv("INGEST_INTERVAL_HOURS", "0"))
    scheduler = None
    if interval > 0:
        scheduler = BackgroundScheduler()
        scheduler.add_job(ingest_docs, "interval", hours=interval)
        scheduler.start()

    host = os.getenv("HOST", "0.0.0.0")
    port = os.getenv("PORT", "8000")
    try:
        subprocess.run([
            "uvicorn",
            "src.main:app",
            "--host",
            host,
            "--port",
            str(port),
        ])
    finally:
        if scheduler:
            scheduler.shutdown()


if __name__ == "__main__":
    main()
