"""Health endpoint."""

from fastapi import APIRouter

from ...core.battle import ATTACKER_URL, DEFENDER_URL

router = APIRouter()


@router.get("/health")
async def health() -> dict:
    return {
        "service": "orchestrator",
        "ok": True,
        "attacker_url": ATTACKER_URL,
        "defender_url": DEFENDER_URL,
    }
