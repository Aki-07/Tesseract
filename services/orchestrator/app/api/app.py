"""Application factory for the orchestrator service."""

from __future__ import annotations

from contextlib import asynccontextmanager

import structlog
from fastapi import FastAPI, Request

from ..core.metrics import http_metrics_middleware, metrics_endpoint
from ..db import init_db
from .routes import router as api_router
from fastapi.middleware.cors import CORSMiddleware


log = structlog.get_logger(__name__)


def _name_endpoint(req: Request) -> str:
    path = req.url.path
    if path.startswith("/battle/status/"):
        return "/battle/status/{id}"
    if path.startswith("/battle/get/"):
        return "/battle/get/{id}"
    return path


@asynccontextmanager
async def lifespan(app: FastAPI):  # noqa: D401 - FastAPI requires signature
    """Run startup and shutdown tasks."""
    log.info("orchestrator.startup")
    init_db()
    yield
    log.info("orchestrator.shutdown")


def create_app() -> FastAPI:
    app = FastAPI(title="Tesseract Orchestrator", version="0.2.0", lifespan=lifespan)

    app.middleware("http")(http_metrics_middleware(_name_endpoint))
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # UI port
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(api_router)
    app.get("/metrics")(metrics_endpoint())

    return app
