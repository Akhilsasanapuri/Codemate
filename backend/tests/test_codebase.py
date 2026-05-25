"""Tests for the RAG codebase endpoints (with mocked embeddings + LLM)."""
import io
import zipfile

import pytest


def make_zip(files: dict[str, str]) -> bytes:
    """Build an in-memory zip from {filename: content} mapping."""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for name, content in files.items():
            zf.writestr(name, content)
    return buf.getvalue()


@pytest.fixture
def mock_embeddings(monkeypatch):
    """Return deterministic 8-dim fake embeddings (no network calls)."""
    def fake_embed_texts(texts, *, task_type="RETRIEVAL_DOCUMENT"):
        # very simple: hash-based pseudo-embedding; same text -> same vector
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
    # rag.py imported `embeddings` as a module — patch is already visible.


@pytest.fixture
def mock_llm_ask(monkeypatch):
    """Mock chat_json for the ask-codebase endpoint."""
    def fake_chat_json(system, user, *, model=None, temperature=0.2):
        return {
            "answer": "The project entry point is `app/main.py` which creates a FastAPI app.",
            "used_sources": ["app/main.py"],
        }
    import app.llm as llm_module
    monkeypatch.setattr(llm_module, "chat_json", fake_chat_json)


def test_upload_and_ask_flow(client, mock_embeddings, mock_llm_ask):
    zip_bytes = make_zip({
        "myproj/app/main.py": "from fastapi import FastAPI\napp = FastAPI()\n",
        "myproj/README.md": "# Demo\nA tiny project.\n",
        # noise that should be filtered
        "myproj/node_modules/lib/index.js": "module.exports = 1;",
        "myproj/yarn.lock": "lockfile-content",
        "myproj/image.png": "binary-data",
    })

    # upload
    r = client.post(
        "/api/codebase/upload",
        files={"file": ("demo.zip", zip_bytes, "application/zip")},
        data={"name": "demo"},
    )
    assert r.status_code == 200, r.text
    project = r.json()
    assert project["name"] == "demo"
    assert project["file_count"] >= 2  # main.py + README.md, node_modules/lockfile filtered
    assert project["chunk_count"] >= 2
    project_id = project["id"]

    # list
    r = client.get("/api/codebase/projects")
    assert r.status_code == 200
    assert any(p["id"] == project_id for p in r.json())

    # ask
    r = client.post(
        "/api/codebase/ask",
        json={"project_id": project_id, "question": "where is the entry point?"},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert "main.py" in body["answer"]
    assert isinstance(body["sources"], list)
    assert len(body["sources"]) >= 1
    assert {"file_path", "line_start", "line_end", "score", "snippet"} <= set(body["sources"][0].keys())

    # history records the ask
    r = client.get("/api/history", params={"type": "ask_codebase"})
    assert r.status_code == 200
    assert len(r.json()) == 1

    # delete
    r = client.delete(f"/api/codebase/projects/{project_id}")
    assert r.status_code == 200

    r = client.get("/api/codebase/projects")
    assert all(p["id"] != project_id for p in r.json())


def test_upload_rejects_non_zip(client, mock_embeddings):
    r = client.post(
        "/api/codebase/upload",
        files={"file": ("notes.txt", b"hello", "text/plain")},
        data={"name": "demo"},
    )
    assert r.status_code == 400


def test_upload_rejects_empty_project(client, mock_embeddings):
    # zip containing only filtered-out files
    zip_bytes = make_zip({
        "node_modules/x.js": "x",
        "image.png": "p",
        "yarn.lock": "l",
    })
    r = client.post(
        "/api/codebase/upload",
        files={"file": ("empty.zip", zip_bytes, "application/zip")},
        data={"name": "empty"},
    )
    assert r.status_code == 400


def test_ask_missing_project(client, mock_embeddings, mock_llm_ask):
    r = client.post(
        "/api/codebase/ask",
        json={"project_id": 9999, "question": "anything"},
    )
    assert r.status_code == 404


def test_chunker_splits_long_file():
    from app.services.chunker import chunk_file
    content = "\n".join(f"line {i}" for i in range(1, 401))  # ~ many lines
    chunks = chunk_file("foo.py", content)
    assert len(chunks) >= 2
    # First chunk starts at line 1
    assert chunks[0].line_start == 1
    # Subsequent chunks have monotonically increasing starts
    for prev, curr in zip(chunks, chunks[1:]):
        assert curr.line_start >= prev.line_start
