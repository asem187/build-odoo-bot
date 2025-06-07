from fastapi import (
    FastAPI,
    UploadFile,
    File,
    WebSocket,
    WebSocketDisconnect,
    Header,
    HTTPException,
    Depends,
    Request,
)
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import openai
from dotenv import load_dotenv
import asyncio
from contextlib import asynccontextmanager
import os
import logging

from .agent import get_agent
from .odoo_client import get_connection

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("odoo_bot")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize agent and Odoo connection once."""
    try:
        get_cached_agent()
    except Exception:
        pass
    try:
        get_cached_odoo()
    except Exception:
        pass
    yield


app = FastAPI(title="Odoo Chatbot", lifespan=lifespan)


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Return 500 and log unhandled exceptions."""
    logger.exception("Unhandled error", exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

# Cached agent and Odoo connection
agent_cache = None
odoo_cache = None


API_TOKEN = os.getenv("API_TOKEN")


def authorize(authorization: str = Header("")):
    """Simple token check using Authorization header."""
    token_env = os.getenv("API_TOKEN", API_TOKEN)
    if token_env:
        token = authorization.replace("Bearer ", "").strip()
        if token != token_env:
            raise HTTPException(status_code=401, detail="Unauthorized")

def get_cached_agent():
    global agent_cache
    if agent_cache is None:
        agent_cache = get_agent()
    return agent_cache


def get_cached_odoo():
    global odoo_cache
    if odoo_cache is None:
        odoo_cache = get_connection()
    return odoo_cache


class Query(BaseModel):
    model: str
    query: str


class Message(BaseModel):
    message: str


@app.post("/chat")
async def chat(msg: Message, auth: None = Depends(authorize)):
    agent = get_cached_agent()
    response = await asyncio.to_thread(agent.run, msg.message)
    return {"response": response}


@app.post("/voice")
async def voice_chat(file: UploadFile = File(...), auth: None = Depends(authorize)):
    """Accept an audio file and respond using the chat agent."""
    transcript = await asyncio.to_thread(openai.Audio.transcribe, "whisper-1", file.file)
    agent = get_cached_agent()
    response = await asyncio.to_thread(agent.run, transcript["text"])
    return {"transcript": transcript["text"], "response": response}


@app.websocket("/ws/voice")
async def voice_ws(ws: WebSocket):
    """WebSocket endpoint to stream audio and receive responses."""
    token = ws.headers.get("authorization", "").replace("Bearer ", "").strip()
    if API_TOKEN and token != API_TOKEN:
        await ws.close(code=4401)
        return
    await ws.accept()
    chunks = bytearray()
    try:
        while True:
            data = await ws.receive()
            if "bytes" in data and data["bytes"]:
                chunks.extend(data["bytes"])
            elif data.get("text") == "END":
                break
    except WebSocketDisconnect:
        return
    transcript = await asyncio.to_thread(openai.Audio.transcribe, "whisper-1", bytes(chunks))
    agent = get_cached_agent()
    response = await asyncio.to_thread(agent.run, transcript["text"])
    await ws.send_json({"transcript": transcript["text"], "response": response})
    await ws.close()


@app.post("/search")
async def search_record(q: Query, auth: None = Depends(authorize)):
    """Simple search tool for Odoo."""
    odoo = get_cached_odoo()
    model = odoo.env[q.model]
    ids = await asyncio.to_thread(model.search, [("name", "ilike", q.query)])
    records = await asyncio.to_thread(model.read, ids)
    return {"results": records}


@app.get("/")
async def read_root():
    return {"message": "Odoo bot is running"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)
