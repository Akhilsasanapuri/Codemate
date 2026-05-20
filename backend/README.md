# CodeMate — Backend (Phase 1)

FastAPI service powering the CodeMate AI coding assistant. Phase 1 ships three
agents — **Explain Error**, **Generate Code**, **Review Code** — plus a
history endpoint, all backed by SQLite.

Defaults to **Google Gemini** (free tier) via its OpenAI-compatible endpoint,
but swappable to any OpenAI-compatible provider (OpenAI, Groq, OpenRouter,
Ollama, etc.) by changing 3 env vars.

## Quick start

```powershell
cd C:\Users\t-akhils\projects\codemate\backend

# 1. Create venv & install deps
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2. Configure env
Copy-Item .env.example .env
# Get a free Gemini key at https://aistudio.google.com/apikey
# Edit .env and set LLM_API_KEY=<your key>

# 3. Run
uvicorn app.main:app --reload --port 8000
```

Open http://localhost:8000/docs for interactive Swagger UI.

## Endpoints

| Method | Path | Body |
|---|---|---|
| GET  | `/health` | — |
| POST | `/api/explain-error` | `{error_message, code?, language?}` |
| POST | `/api/generate-code` | `{prompt, language?, framework?}` |
| POST | `/api/review-code`   | `{code, language?}` |
| GET  | `/api/history`       | `?limit=20&type=explain_error` |
| GET  | `/api/history/{id}`  | — |

### Example: Explain Error
```bash
curl -X POST http://localhost:8000/api/explain-error \
  -H "Content-Type: application/json" \
  -d '{
    "error_message": "TypeError: NoneType has no attribute strip",
    "code": "name = lookup_user(id)\nprint(name.strip())",
    "language": "python"
  }'
```

### Example: Generate Code
```bash
curl -X POST http://localhost:8000/api/generate-code \
  -H "Content-Type: application/json" \
  -d '{"prompt":"FastAPI endpoint that returns current time","language":"python","framework":"fastapi"}'
```

### Example: Review Code
```bash
curl -X POST http://localhost:8000/api/review-code \
  -H "Content-Type: application/json" \
  -d '{"code":"def add(a,b):return a+b","language":"python"}'
```

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `LLM_API_KEY` | — | **Required.** Your provider API key |
| `LLM_BASE_URL` | Gemini's OpenAI-compat endpoint | Switch provider here |
| `LLM_MODEL` | `gemini-2.0-flash` | Model name (provider-specific) |
| `LLM_TIMEOUT_SECONDS` | `30` | HTTP client timeout |
| `DB_URL` | `sqlite:///./codemate.db` | SQLAlchemy URL |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated |

### Swapping providers
Any OpenAI-compatible API works — just set these three vars:

| Provider | `LLM_BASE_URL` | `LLM_MODEL` |
|---|---|---|
| **Gemini** (default, free) | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.0-flash` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Groq (free) | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | `deepseek/deepseek-chat:free` |
| Ollama (local) | `http://localhost:11434/v1` | `qwen2.5-coder` |

## Tests

```powershell
pip install -r requirements.txt
pytest -q
```

Tests mock the LLM client — no real API calls or key required.

## Project layout

```
app/
├── main.py            FastAPI app + CORS + router wiring
├── config.py          Pydantic Settings
├── db.py              SQLite engine + session dep
├── models.py          Interaction table
├── schemas.py         Request/response Pydantic models
├── prompts.py         Per-agent prompt templates
├── llm.py             OpenAI-compatible client wrapper (json_object mode)
├── services/agent.py  Shared runner: call LLM, validate, persist
└── routers/           One file per endpoint group
tests/                 Pytest with mocked LLM
```

## Architecture notes

- **Provider-agnostic LLM layer**: uses the official `openai` SDK pointed at any
  OpenAI-compatible `base_url`. Swap providers with env vars, no code changes.
- **Structured outputs**: every agent uses `response_format=json_object` and
  validates the result against a Pydantic schema. If validation fails the
  client gets a `502` and the failure is logged to the `interactions` table.
- **Persistence**: every call writes one row to `interactions` (request, response,
  latency, model, error). Powers Phase-2 chat history features.
- **Routing**: each feature is its own router under `/api`. Adds room for
  per-feature middleware later (rate limits, intent detection, etc.).

## Roadmap (per PRD)

- **Phase 1** ✅ Backend + 3 agents + history (this PR)
- **Phase 2** Frontend (React + Monaco) integration
- **Phase 3** RAG over uploaded repos (Chroma + embeddings)
- **Phase 4** Auto-routing intent agent
- **Phase 5** Deployment (Render/Railway + Vercel)
