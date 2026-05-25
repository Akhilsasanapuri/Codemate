from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .db import init_db
from .routers import codebase, explain_error, generate_code, history, review_code


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title="CodeMate API",
        version="0.1.0",
        description="AI coding assistant: explain errors, generate code, review code.",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", tags=["meta"])
    def health() -> dict:
        return {"status": "ok", "model": settings.llm_model, "base_url": settings.llm_base_url}

    app.include_router(explain_error.router, prefix="/api", tags=["agents"])
    app.include_router(generate_code.router, prefix="/api", tags=["agents"])
    app.include_router(review_code.router, prefix="/api", tags=["agents"])
    app.include_router(codebase.router, prefix="/api", tags=["codebase"])
    app.include_router(history.router, prefix="/api", tags=["history"])

    return app


app = create_app()
