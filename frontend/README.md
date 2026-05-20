# CodeMate — Frontend (Phase 2)

React + TypeScript + Vite SPA powering the CodeMate UI. Talks to the FastAPI
backend in `../backend`. Dark, VS-Code-inspired look with Monaco code editor +
Prism syntax-highlighted output.

## Stack

- **Vite + React 19 + TypeScript**
- **Tailwind CSS v4** (via `@tailwindcss/vite` plugin)
- **@monaco-editor/react** — VS-Code editor for code input
- **react-syntax-highlighter** — Prism + One Dark output blocks
- **lucide-react** — icons

## Run it

```powershell
# In one terminal — start the backend
cd ..\backend
.\.venv\Scripts\Activate.ps1
uvicorn app.main:app --reload --port 8000

# In another terminal — start the frontend
cd frontend
npm install   # only the first time
npm run dev
```

Open http://localhost:5173. The dev server proxies `/api` and `/health` to the
backend, so you don't need to worry about CORS during development.

## Features

| Tab | What it does |
|---|---|
| **Explain Error** | Paste an error + optional code → root cause, fix, corrected snippet |
| **Generate Code** | Describe a task → runnable code + explanation + assumptions |
| **Review Code**   | Paste code → bug/style/security issues + improved version |
| **History**       | Browse every past interaction (success + failure) with full request/response JSON |

UI niceties:
- Monaco editor in every code input (auto-resize, dark theme)
- Copy-to-clipboard on every output code block
- Per-severity color coding for review issues
- Live "backend connected · model name" indicator in the header
- Empty states and loading spinners
- Responsive 2-column layout on `lg` screens, stacked below

## Scripts

```bash
npm run dev      # dev server with HMR
npm run build    # type-check + production bundle
npm run preview  # serve the production bundle
```

## Project layout

```
src/
├── App.tsx                       # header + tabs + active panel
├── main.tsx                      # React root
├── index.css                     # Tailwind + global styles
├── api.ts                        # typed fetch wrappers for /api/*
├── types.ts                      # mirrors backend Pydantic schemas
├── lib/cn.ts                     # className helper
└── components/
    ├── Tabs.tsx
    ├── CodeEditor.tsx            # Monaco wrapper
    ├── CodeBlock.tsx             # Prism + copy button
    ├── Form.tsx                  # Field / TextInput / TextArea / LanguageSelect
    ├── SubmitButton.tsx
    ├── ErrorBanner.tsx
    ├── ExplainErrorPanel.tsx
    ├── GenerateCodePanel.tsx
    ├── ReviewCodePanel.tsx
    └── HistoryPanel.tsx
```

## Configuration

The dev-server proxy lives in `vite.config.ts`. To point at a backend on a
different host/port, edit the `proxy.target` value. For production deploys,
either co-host (reverse-proxy `/api` to FastAPI) or add an env-driven base
URL in `api.ts`.
