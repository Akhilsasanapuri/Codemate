# CodeMate

An AI coding-assistant web app that helps you **explain errors**, **generate
code**, **review code**, and **ask questions about your own codebase (RAG)** —
built around Google Gemini (free tier) with a provider-agnostic design that
also supports OpenAI, Groq, OpenRouter, and Ollama by changing 3 env vars.

```
codemate/
├── backend/    FastAPI + SQLite + ChromaDB + OpenAI-compatible LLM client
└── frontend/   React 19 + Vite + Tailwind v4 + Monaco
```

See [`backend/README.md`](backend/README.md) and
[`frontend/README.md`](frontend/README.md) for component-level docs.

---

## Prerequisites

Install once on any new machine:

- **Python 3.10+** — https://www.python.org/downloads/ (tick "Add to PATH")
- **Node.js 18+** — https://nodejs.org/
- **Git** — https://git-scm.com/

Then get a **free Gemini API key**:

1. Visit https://aistudio.google.com/apikey
2. Click *Create API key* → copy it

---

## Quick start

### 1. Clone

```bash
git clone https://github.com/<your-user>/codemate.git
cd codemate
```

### 2. Backend

```bash
cd backend

# Create & activate a virtualenv
python -m venv .venv
# Windows PowerShell:
.\.venv\Scripts\Activate.ps1
# macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure
cp .env.example .env          # macOS/Linux
# or: Copy-Item .env.example .env    # Windows PowerShell
# Then edit .env and set:
#   LLM_API_KEY=<paste your Gemini key>

# Run
uvicorn app.main:app --reload --port 8000
```

Backend is now live at http://127.0.0.1:8000 (Swagger UI at `/docs`).

### 3. Frontend (in a second terminal)

```bash
cd frontend
npm install
npm run dev
```

Frontend is now live at http://localhost:5173. The Vite dev server proxies
`/api` and `/health` to the backend, so you don't need to configure CORS.

---

## Configuration (env vars)

Edit `backend/.env`:

| Variable | Default | Purpose |
|---|---|---|
| `LLM_API_KEY` | — | **Required** — your provider API key |
| `LLM_BASE_URL` | Gemini's OpenAI-compat endpoint | Switch providers here |
| `LLM_MODEL` | `gemini-2.5-flash-lite` | Provider-specific model name |
| `DB_URL` | `sqlite:///./codemate.db` | SQLAlchemy URL |
| `CORS_ORIGINS` | `http://localhost:3000,http://localhost:5173` | Comma-separated |
| `LLM_TIMEOUT_SECONDS` | `30` | HTTP client timeout |

### Switching LLM provider

Set these three vars to any OpenAI-compatible endpoint:

| Provider | `LLM_BASE_URL` | `LLM_MODEL` |
|---|---|---|
| **Gemini** (default, free) | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash-lite` |
| OpenAI | `https://api.openai.com/v1` | `gpt-4o-mini` |
| Groq (free) | `https://api.groq.com/openai/v1` | `llama-3.3-70b-versatile` |
| OpenRouter | `https://openrouter.ai/api/v1` | `deepseek/deepseek-chat:free` |
| Ollama (local) | `http://localhost:11434/v1` | `qwen2.5-coder` |

---

## Tests

```bash
cd backend
pytest -q
```

Tests mock the LLM — no real API call or key needed.

---

## Tech stack

**Backend:** FastAPI · SQLModel · SQLite · OpenAI SDK (Gemini target) · Pydantic v2 · Uvicorn

**Frontend:** React 19 · TypeScript · Vite · Tailwind CSS v4 · Monaco Editor · react-syntax-highlighter · lucide-react

---

## Roadmap

- ✅ **Phase 1** — FastAPI backend with 3 agents + history
- ✅ **Phase 2** — React frontend (tabs, Monaco, dark theme)
- ✅ **Phase 3** — RAG: zip-upload codebases, Gemini embeddings, ChromaDB, "Ask Codebase" tab with cited sources
- ⬜ **Phase 4** — Intent-routing agent (single chat input, auto-picks tool)
- ⬜ **Phase 5** — Deployment (Vercel for frontend, Render/Railway for backend)

---

## Phase 3: Ask Codebase (RAG)

Upload a `.zip` of any project, and CodeMate will:

1. Walk every text file (skipping `node_modules`, `.git`, lockfiles, binaries, files > 100 KB)
2. Split each file into ~1500-char chunks with line-range metadata
3. Embed every chunk via Gemini's `gemini-embedding-001` (768-dim)
4. Store vectors in a local **ChromaDB** at `./backend/chroma_db/`

Then ask questions. Each answer cites the exact files + line ranges it used,
and the **Sources** panel lets you expand each retrieved chunk with syntax
highlighting.

**Safety caps** (in `.env`): 100 KB / file · 500 files / project · 2000 chunks / project.

---

## License

Personal / educational project.
