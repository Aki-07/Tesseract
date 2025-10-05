"""ASGI entrypoint for the orchestrator service."""

from .api.app import create_app

app = create_app()

__all__ = ["app"]
