"""File walker + chunker for uploaded codebases.

Walks an extracted zip, filters out junk (binaries, node_modules, lockfiles,
oversized files), then splits each file's text into ~1500 char chunks with
~200 char overlap. Each chunk carries its file path and line range as metadata
so we can show the user *where* an answer came from.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List

from ..config import get_settings

# Directories we never want to index.
SKIP_DIRS = frozenset(
    {
        ".git",
        ".hg",
        ".svn",
        "node_modules",
        ".venv",
        "venv",
        "env",
        "__pycache__",
        "dist",
        "build",
        ".next",
        ".nuxt",
        ".cache",
        ".idea",
        ".vscode",
        "target",
        "coverage",
        ".pytest_cache",
        ".mypy_cache",
        ".tox",
        ".gradle",
        "out",
        "bin",
        "obj",
    }
)

# File extensions we never index (binaries, media, lockfiles, ...).
SKIP_EXTS = frozenset(
    {
        # binaries / artifacts
        ".pyc", ".pyo", ".class", ".jar", ".war", ".so", ".dll", ".dylib",
        ".exe", ".bin", ".o", ".a", ".lib", ".obj",
        # archives
        ".zip", ".tar", ".gz", ".tgz", ".bz2", ".7z", ".rar",
        # images / media
        ".png", ".jpg", ".jpeg", ".gif", ".bmp", ".ico", ".webp", ".svg",
        ".pdf", ".psd", ".ai",
        ".mp3", ".wav", ".flac", ".ogg",
        ".mp4", ".mov", ".avi", ".mkv", ".webm",
        # fonts
        ".woff", ".woff2", ".ttf", ".otf", ".eot",
        # data dumps
        ".sqlite", ".db", ".csv", ".parquet",
        # IDE / OS noise
        ".ds_store",
    }
)

# Lockfile basenames (extension-less or with non-skip extensions).
SKIP_BASENAMES = frozenset(
    {
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "poetry.lock",
        "Pipfile.lock",
        "Cargo.lock",
        "composer.lock",
        "Gemfile.lock",
        "go.sum",
    }
)

CHUNK_CHAR_SIZE = 1500
CHUNK_CHAR_OVERLAP = 200


@dataclass
class Chunk:
    file_path: str  # relative to project root, forward slashes
    line_start: int  # 1-indexed inclusive
    line_end: int  # 1-indexed inclusive
    text: str


def iter_indexable_files(root: Path) -> Iterable[Path]:
    """Yield files under root that pass the filter."""
    settings = get_settings()
    for dirpath, dirnames, filenames in os.walk(root):
        # prune skip dirs in-place so we don't descend into them
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS and not d.startswith(".")]
        for name in filenames:
            if name in SKIP_BASENAMES:
                continue
            ext = Path(name).suffix.lower()
            if ext in SKIP_EXTS:
                continue
            full = Path(dirpath) / name
            try:
                size = full.stat().st_size
            except OSError:
                continue
            if size == 0 or size > settings.max_file_bytes:
                continue
            yield full


def read_text(path: Path) -> str | None:
    """Read a file as UTF-8 text, or None if it looks binary."""
    try:
        raw = path.read_bytes()
    except OSError:
        return None
    # Heuristic: if there's a NUL byte in the first 4KB, treat as binary.
    if b"\x00" in raw[:4096]:
        return None
    try:
        return raw.decode("utf-8")
    except UnicodeDecodeError:
        try:
            return raw.decode("latin-1")
        except Exception:
            return None


def chunk_file(rel_path: str, content: str) -> List[Chunk]:
    """Split a file into overlapping char-window chunks with line ranges."""
    if not content.strip():
        return []

    # Pre-compute char index -> line number map (1-indexed).
    line_at_char: List[int] = []
    current_line = 1
    for ch in content:
        line_at_char.append(current_line)
        if ch == "\n":
            current_line += 1
    # add a sentinel for the position just past the last char
    line_at_char.append(current_line)

    chunks: List[Chunk] = []
    n = len(content)
    start = 0
    step = max(CHUNK_CHAR_SIZE - CHUNK_CHAR_OVERLAP, 1)
    while start < n:
        end = min(start + CHUNK_CHAR_SIZE, n)
        text = content[start:end]
        line_start = line_at_char[start]
        line_end = line_at_char[end - 1] if end - 1 < len(line_at_char) else line_at_char[-1]
        chunks.append(Chunk(file_path=rel_path, line_start=line_start, line_end=line_end, text=text))
        if end == n:
            break
        start += step
    return chunks


def collect_chunks(root: Path) -> tuple[List[Chunk], int, int]:
    """Walk root, read files, chunk them. Returns (chunks, file_count, total_bytes)."""
    settings = get_settings()
    chunks: List[Chunk] = []
    file_count = 0
    total_bytes = 0

    for path in iter_indexable_files(root):
        if file_count >= settings.max_files_per_project:
            break
        text = read_text(path)
        if text is None:
            continue
        rel = path.relative_to(root).as_posix()
        file_chunks = chunk_file(rel, text)
        if not file_chunks:
            continue
        # respect the global chunk cap
        remaining = settings.max_chunks_per_project - len(chunks)
        if remaining <= 0:
            break
        chunks.extend(file_chunks[:remaining])
        file_count += 1
        total_bytes += len(text.encode("utf-8"))

    return chunks, file_count, total_bytes
