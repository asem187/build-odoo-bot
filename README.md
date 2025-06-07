# build-odoo-bot

This project provides a starting point for a multi‑agent chatbot that can interact with an Odoo instance. It uses **LangChain** (with the `langchain-openai` package) for LLM orchestration and exposes a small **FastAPI** service. Documentation embeddings can be stored locally so the bot can reference Odoo docs while answering questions. A simple voice endpoint demonstrates how to transcribe audio with OpenAI's API. A WebSocket version enables lower‑latency voice chat.

The agent layer now includes a lightweight router that dispatches messages to specialized CRM or accounting agents based on the query.

## Features
- LangChain agent with tool calling
- Odoo RPC integration via `odoorpc`
- FastAPI server with `/chat`, `/search`, `/voice` and `/ws/voice` endpoints
- Tools for creating and updating Odoo records with permission checks
- Optional local vector index for documentation
- Built-in multi-agent orchestrator routing messages to CRM or accounting agents
- Centralized logging and global error handling for stable operation
- Optional streaming responses via WebSocket when using the `X-Stream` header

## Folder Structure
- `src/` – application modules
- `scripts/` – data ingestion helpers
- `tests/` – unit tests
- `data/` – local storage for embeddings (ignored by git)

## Setup
1. Create a Python virtual environment and activate it.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in API keys and Odoo credentials.
   Set `API_TOKEN` to a secret value; clients must include
   `Authorization: Bearer <token>` in requests. The file also contains optional
   variables like `OPENAI_MODEL` or `OPENROUTER_API_KEY` if you want to use a
   different provider or endpoint.
4. (Optional) Ingest documentation to build the vector index. The ingestion script
   can automatically clone the Odoo repository and now processes ``.txt``, ``.md``
   and ``.rst`` files for broader coverage:
   ```bash
   python scripts/ingest_docs.py
   ```
   This creates a FAISS index under `data/index` which is used at runtime.
5. Start the bot. The `start_bot.py` helper will ingest documentation if the index is missing and then launch the API server. You can customize the host and port via the `HOST` and `PORT` environment variables:
   ```bash
   HOST=0.0.0.0 PORT=8000 python start_bot.py
   ```

### Voice Chat
Send an audio file (e.g., MP3) to the `/voice` endpoint or stream audio frames
to `/ws/voice`. The service uses OpenAI's Whisper API to transcribe the audio
before passing it to the chatbot.

The WebSocket endpoint optionally streams responses token by token. Set the
`X-Stream: 1` header when opening the WebSocket connection to receive partial
messages before the final JSON payload.

### Running Tests
The project includes a small test suite. After installing requirements run:
```bash
pytest -q
```

### Docker Deployment
Build and run the container with:
```bash
docker build -t odoo-bot .
docker run -p 8000:8000 --env-file .env odoo-bot
```

### Customizing the Multi-Agent Router
The `MultiAgent` class in `src/agent.py` determines which specialist handles a
message. By default it uses simple keyword matching, but you can enable
embedding-based intent detection by setting `CLASSIFIER_MODE=embedding` in your
environment. This uses OpenAI embeddings to decide which agent should respond.
You can also subclass `MultiAgent` or extend `classify()` to add more agents or
custom logic.

### Language Model Configuration
The agent uses `ChatOpenAI` by default. You can point it to an alternative
endpoint (like OpenRouter) or change the model name via environment variables:

```
OPENAI_MODEL=gpt-4-turbo-preview
OPENAI_BASE_URL=https://api.openai.com/v1
OPENROUTER_API_KEY=<your-key>
OPENROUTER_BASE_URL=https://openrouter.ai/api/v1
```

Set `LLM_STREAMING=true` to allow streaming responses from the language model.

These variables are defined in `.env.example` and can be adjusted to use other
providers.

### Authentication
All endpoints expect an `Authorization` header with a bearer token. Set the
`API_TOKEN` value in your `.env` file and include `Authorization: Bearer <token>`
in every request (including the WebSocket handshake).

## Security
Never commit real API keys or credentials. Use the `.env` file (which is git‑ignored) to store sensitive information locally.

## License
This project is licensed under the [MIT License](LICENSE).
