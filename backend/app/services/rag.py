"""RAG orchestration: ingest a zip into Chroma + query it.

Single ChromaDB collection (`codebase_chunks`) holds chunks from ALL projects,
distinguished by a `project_id` metadata field. This keeps things simple and
lets us add/remove projects with a single `delete(where={...})` call.

Chunk IDs are deterministic strings: `proj-{project_id}-{index}` so deletes
are reliable.
"""
from __future__ import annotations

import io
import logging
import tempfile
import zipfile
from pathlib import Path
from typing import List

import chromadb
from sqlmodel import Session, select

from ..config import get_settings
from ..models import Project
from . import embeddings
from .chunker import collect_chunks

logger = logging.getLogger(__name__)

_COLLECTION_NAME = "codebase_chunks"
_client: chromadb.api.ClientAPI | None = None


def _get_collection():
    """Get-or-create the single shared collection. Lazy + cached."""
    global _client
    if _client is None:
        settings = get_settings()
        Path(settings.chroma_dir).mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=settings.chroma_dir)
    # cosine distance is best for embeddings; lower = more similar
    return _client.get_or_create_collection(
        name=_COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )


def reset_client_for_tests() -> None:
    """Test hook: drop the cached client so a fresh chroma_dir is picked up."""
    global _client
    _client = None


# ---------------------------------------------------------------------------
# Ingest
# ---------------------------------------------------------------------------
def ingest_zip(*, session: Session, name: str, zip_bytes: bytes) -> Project:
    """Extract the zip, chunk all eligible files, embed them, store in Chroma,
    and create a Project row. Raises ValueError on bad input."""
    settings = get_settings()

    if not zip_bytes:
        raise ValueError("Empty upload.")
    try:
        zf = zipfile.ZipFile(io.BytesIO(zip_bytes))
    except zipfile.BadZipFile as exc:
        raise ValueError(f"Invalid zip file: {exc}") from exc

    # Reject obviously malicious paths (zip slip).
    for member in zf.namelist():
        if member.startswith("/") or ".." in Path(member).parts:
            raise ValueError(f"Unsafe path in zip: {member}")

    with tempfile.TemporaryDirectory(prefix="codemate_ingest_") as tmpdir:
        root = Path(tmpdir)
        zf.extractall(root)

        # If the zip contains a single top-level dir (common when zipping a folder),
        # treat that as the root so file paths stay clean.
        entries = list(root.iterdir())
        if len(entries) == 1 and entries[0].is_dir():
            root = entries[0]

        chunks, file_count, total_bytes = collect_chunks(root)

    if not chunks:
        raise ValueError(
            "No indexable files found. Make sure your zip contains source files "
            "(not just binaries/lockfiles), and individual files are under "
            f"{settings.max_file_bytes // 1024} KB."
        )

    # Create the project row first so we get an ID.
    project = Project(
        name=name,
        file_count=file_count,
        chunk_count=len(chunks),
        total_bytes=total_bytes,
        embedding_model=settings.embedding_model,
    )
    session.add(project)
    session.commit()
    session.refresh(project)

    try:
        texts = [c.text for c in chunks]
        vectors = embeddings.embed_texts(texts, task_type="RETRIEVAL_DOCUMENT")

        ids = [f"proj-{project.id}-{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "project_id": project.id,
                "file_path": c.file_path,
                "line_start": c.line_start,
                "line_end": c.line_end,
            }
            for c in chunks
        ]

        coll = _get_collection()
        coll.add(ids=ids, embeddings=vectors, documents=texts, metadatas=metadatas)
    except Exception:
        # rollback project row if embedding/storage failed
        session.delete(project)
        session.commit()
        raise

    return project


# ---------------------------------------------------------------------------
# Query
# ---------------------------------------------------------------------------
def query(*, project_id: int, question: str, top_k: int | None = None) -> List[dict]:
    """Return top-K most relevant chunks for a question, scoped to one project."""
    settings = get_settings()
    k = top_k or settings.rag_top_k
    coll = _get_collection()
    qvec = embeddings.embed_query(question)
    result = coll.query(
        query_embeddings=[qvec],
        n_results=k,
        where={"project_id": project_id},
    )

    out: List[dict] = []
    docs = result.get("documents", [[]])[0]
    metas = result.get("metadatas", [[]])[0]
    dists = result.get("distances", [[]])[0] if result.get("distances") else [0.0] * len(docs)
    for doc, meta, dist in zip(docs, metas, dists):
        out.append(
            {
                "file_path": meta.get("file_path", ""),
                "line_start": int(meta.get("line_start", 0)),
                "line_end": int(meta.get("line_end", 0)),
                "score": float(dist),
                "text": doc,
            }
        )
    return out


# ---------------------------------------------------------------------------
# Delete
# ---------------------------------------------------------------------------
def delete_project(*, session: Session, project_id: int) -> bool:
    """Remove project row + all its vectors. Returns True if anything deleted."""
    project = session.get(Project, project_id)
    if project is None:
        return False

    coll = _get_collection()
    try:
        coll.delete(where={"project_id": project_id})
    except Exception as exc:  # noqa: BLE001 - chroma raises if collection empty etc.
        logger.warning("Chroma delete for project %s failed: %s", project_id, exc)

    session.delete(project)
    session.commit()
    return True


def list_projects(session: Session) -> List[Project]:
    return list(session.exec(select(Project).order_by(Project.created_at.desc())))


# ---------------------------------------------------------------------------
# High-level "answer a question about a project" helper.
# Used by both the /api/codebase/ask endpoint and the Phase 4 router.
# ---------------------------------------------------------------------------
def answer_question(*, project_id: int, question: str, top_k: int | None = None):
    """Retrieve top-K chunks, ask the LLM, return (AskCodebaseResponse, raw_llm_dict).

    Raises ValueError if the project has no indexed chunks.
    """
    from .. import llm as llm_module
    from ..config import get_settings
    from ..prompts import ask_codebase_prompt
    from ..schemas import AskCodebaseResponse, CodebaseSource

    retrieved = query(project_id=project_id, question=question, top_k=top_k)
    if not retrieved:
        raise ValueError(f"No indexed chunks found for project_id={project_id}")

    system, user = ask_codebase_prompt(question, retrieved)
    raw = llm_module.chat_json(system, user, model=get_settings().llm_model)
    answer = str(raw.get("answer", "")).strip()
    used_sources = [str(s) for s in raw.get("used_sources", []) if isinstance(s, str)]
    sources = [
        CodebaseSource(
            file_path=r["file_path"],
            line_start=r["line_start"],
            line_end=r["line_end"],
            score=r["score"],
            snippet=r["text"][:600],
        )
        for r in retrieved
    ]
    return AskCodebaseResponse(answer=answer, used_sources=used_sources, sources=sources), raw
