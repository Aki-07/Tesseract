# services/orchestrator/app/api/routes/evolution.py
import asyncio
import logging
import traceback
from typing import Optional, Dict, Any

from fastapi import APIRouter, HTTPException, Body

from ...core.evolution import evaluate_and_mutate, evaluate_run

logger = logging.getLogger("tesseract.evolution.router")
router = APIRouter(prefix="/evolve", tags=["evolution"])


@router.get("/status/{run_id}")
async def eval_status(run_id: str) -> Dict[str, Any]:
    """
    Return evaluation metrics for a completed run.
    Runs DB read in thread to avoid blocking event loop.
    """
    try:
        res = await asyncio.to_thread(evaluate_run, run_id)
        return res
    except Exception as e:
        logger.exception("evaluate_run_failed: %s", run_id)
        # return 404 for not found, 500 for other errors
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/{run_id}")
async def trigger_evolution(
    run_id: str,
    payload: Optional[dict] = Body(
        default=None,
        description='Optional JSON: {"capsule_id":"...", "target_role":"defense", "strategy":"defense_harden"}'
    ),
) -> Dict[str, Any]:
    """
    Trigger evolution for run_id.
    Executes evaluate_and_mutate in a thread (non-blocking on event loop).
    Returns the evaluation and mutated capsule info (if any).
    """
    capsule_id = None
    target_role = None
    strategy = "defense_harden"

    if payload:
        if not isinstance(payload, dict):
            raise HTTPException(status_code=400, detail="payload must be a JSON object")
        capsule_id = payload.get("capsule_id")
        target_role = payload.get("target_role")
        strategy = payload.get("strategy", strategy)

    try:
        result = await asyncio.to_thread(evaluate_and_mutate, run_id, capsule_id, target_role, strategy)
        return result
    except Exception as e:
        logger.error("trigger_evolution_failed run=%s error=%s", run_id, str(e))
        traceback.print_exc()
        # 500: something unexpected happened
        raise HTTPException(status_code=500, detail=str(e))
