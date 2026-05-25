"""Tests for Phase 4 intent routing endpoint."""
import io
import zipfile

import pytest


def _make_zip(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


@pytest.fixture
def mock_embeddings(monkeypatch):
    def fake_embed_texts(texts, *, task_type="RETRIEVAL_DOCUMENT"):
        out = []
        for t in texts:
            h = abs(hash(t))
            out.append([((h >> (i * 4)) & 0xF) / 16.0 for i in range(8)])
        return out

    def fake_embed_query(text):
        return fake_embed_texts([text], task_type="RETRIEVAL_QUERY")[0]

    from app.services import embeddings
    monkeypatch.setattr(embeddings, "embed_texts", fake_embed_texts)
    monkeypatch.setattr(embeddings, "embed_query", fake_embed_query)


def _patch_chat_json(monkeypatch, responder):
    """Patch the LLM with a callable that gets the system+user prompts."""
    import app.llm as llm_module

    def fake(system, user, *, model=None, temperature=0.2):
        return responder(system, user)

    monkeypatch.setattr(llm_module, "chat_json", fake)


def test_route_to_explain_error(client, monkeypatch):
    text = "TypeError: 'NoneType' object is not iterable at user.py line 12"

    def responder(system, user):
        if "intent router" in system.lower():
            return {
                "tool": "explain_error",
                "reason": "Message contains a Python TypeError stack trace.",
                "extracted": {"error_message": text, "code": None, "language": "python"},
            }
        # explain_error agent response
        return {
            "explanation": "You called iter() on None.",
            "root_cause": "Some function returned None when an iterable was expected.",
            "suggested_fix": "Add a None check before iterating.",
            "corrected_code": "if x: ...",
        }

    _patch_chat_json(monkeypatch, responder)
    r = client.post("/api/route", json={"text": text})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["routed_to"] == "explain_error"
    assert body["reason"]
    assert body["explain_error"]["explanation"] == "You called iter() on None."
    assert body["generate_code"] is None
    assert body["ask_codebase"] is None


def test_route_to_generate_code(client, monkeypatch):
    text = "Write me a Python function that reverses a string"

    def responder(system, user):
        if "intent router" in system.lower():
            return {
                "tool": "generate_code",
                "reason": "User is asking to write new code.",
                "extracted": {"prompt": text, "language": "python"},
            }
        return {
            "code": "def reverse(s):\n    return s[::-1]\n",
            "language": "python",
            "explanation": "Slice with step -1.",
            "assumptions": ["s is a string"],
        }

    _patch_chat_json(monkeypatch, responder)
    r = client.post("/api/route", json={"text": text})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["routed_to"] == "generate_code"
    assert "def reverse" in body["generate_code"]["code"]


def test_route_to_review_code(client, monkeypatch):
    text = "Review this:\ndef add(a,b):\n  return a+b"

    def responder(system, user):
        if "intent router" in system.lower():
            return {
                "tool": "review_code",
                "reason": "User pasted code with no error message.",
                "extracted": {"code": "def add(a,b):\n  return a+b", "language": "python"},
            }
        return {
            "summary": "Minor style issues.",
            "issues": [
                {"type": "style", "severity": "info", "description": "Missing spaces."},
            ],
            "improved_code": "def add(a, b):\n    return a + b\n",
            "language": "python",
        }

    _patch_chat_json(monkeypatch, responder)
    r = client.post("/api/route", json={"text": text})
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["routed_to"] == "review_code"
    assert body["review_code"]["issues"][0]["severity"] == "info"


def test_route_to_ask_codebase(client, monkeypatch, mock_embeddings):
    # 1) upload a tiny project
    zip_bytes = _make_zip({
        "demo/app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "demo/README.md": "# Demo\nentry point is app/main.py\n",
    })

    def upload_responder(system, user):
        # Not called during upload, but keep a safe default.
        return {"answer": "n/a", "used_sources": []}

    _patch_chat_json(monkeypatch, upload_responder)
    r = client.post(
        "/api/codebase/upload",
        files={"file": ("demo.zip", zip_bytes, "application/zip")},
        data={"name": "demo"},
    )
    assert r.status_code == 200, r.text
    project_id = r.json()["id"]

    # 2) now route a question to ask_codebase
    def route_responder(system, user):
        if "intent router" in system.lower():
            return {
                "tool": "ask_codebase",
                "reason": "User is asking about the uploaded project.",
                "extracted": {"question": "what is the entry point?"},
            }
        # ask_codebase prompt
        return {
            "answer": "Entry point is app/main.py.",
            "used_sources": ["demo/app/main.py"],
        }

    _patch_chat_json(monkeypatch, route_responder)
    r = client.post(
        "/api/route",
        json={"text": "what is the entry point of this project?", "project_id": project_id},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["routed_to"] == "ask_codebase"
    assert "main.py" in body["ask_codebase"]["answer"]
    assert len(body["ask_codebase"]["sources"]) >= 1


def test_route_rejects_ask_codebase_without_project(client, monkeypatch):
    def responder(system, user):
        return {
            "tool": "ask_codebase",
            "reason": "wanted project",
            "extracted": {"question": "x"},
        }

    _patch_chat_json(monkeypatch, responder)
    r = client.post("/api/route", json={"text": "tell me about the project"})
    assert r.status_code == 400
    assert "project_id" in r.json()["detail"]


def test_route_rejects_unknown_tool(client, monkeypatch):
    def responder(system, user):
        return {"tool": "do_my_taxes", "reason": "", "extracted": {}}

    _patch_chat_json(monkeypatch, responder)
    r = client.post("/api/route", json={"text": "hello"})
    assert r.status_code == 502
