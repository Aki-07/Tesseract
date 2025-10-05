"""Route registrations for the orchestrator API."""

from fastapi import APIRouter

from . import battle, capsules, evolution, health, multi_battle

router = APIRouter()
router.include_router(battle.router)
router.include_router(capsules.router)
router.include_router(evolution.router)
router.include_router(health.router)
router.include_router(multi_battle.router)

__all__ = ["router"]
