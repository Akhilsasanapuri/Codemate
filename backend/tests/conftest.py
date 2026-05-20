import os
import tempfile

import pytest


@pytest.fixture(autouse=True)
def _isolated_env(monkeypatch, tmp_path):
    """Each test gets a fresh SQLite DB and a dummy API key."""
    db_path = tmp_path / "test.db"
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("DB_URL", f"sqlite:///{db_path.as_posix()}")
    monkeypatch.setenv("LLM_MODEL", "gemini-2.0-flash")
    # Clear cached settings so env overrides take effect
    from app.config import get_settings
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def client(monkeypatch):
    """TestClient with a fresh app (so lifespan creates a fresh DB)."""
    # Import after env is patched so engine uses the test DB
    from fastapi.testclient import TestClient
    from app.main import create_app

    # Need to also reset the module-level engine in app.db
    import importlib
    import app.db as db_module
    importlib.reload(db_module)
    import app.services.agent as agent_module
    importlib.reload(agent_module)
    import app.routers.explain_error as r1
    import app.routers.generate_code as r2
    import app.routers.review_code as r3
    import app.routers.history as r4
    for r in (r1, r2, r3, r4):
        importlib.reload(r)
    import app.main as main_module
    importlib.reload(main_module)

    app = main_module.create_app()
    with TestClient(app) as c:
        yield c
