"""Legacy single-battle endpoints."""

from __future__ import annotations

import asyncio
import uuid

from fastapi import APIRouter, BackgroundTasks, HTTPException

from ...core import battle as battle_core
from ...core.state import battle_tasks
from ...core.storage import load_battle_state
from ..schemas import StartBattleRequest

router = APIRouter(prefix="/battle", tags=["battle"])


@router.post("/start")
async def start_battle(req: StartBattleRequest, background_tasks: BackgroundTasks) -> dict:
    run_id = req.run_id or str(uuid.uuid4())[:8]
    if run_id in battle_tasks:
        raise HTTPException(status_code=400, detail=f"run_id {run_id} already exists")

    battle_core.create_initial_state(run_id)
    task = asyncio.create_task(
        battle_core.battle_runner(
            run_id,
            rounds=req.rounds,
            interval_seconds=req.interval_seconds,
            attacker_tool=req.attacker_tool,
            defender_tool=req.defender_tool,
        ),
        name=f"battle-{run_id}",
    )
    battle_core.register_task(run_id, task)
    return {"run_id": run_id, "status": "started"}


@router.post("/stop/{run_id}")
async def stop_battle(run_id: str) -> dict:
    try:
        battle_core.stop_run(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="run not found") from None
    return {"run_id": run_id, "status": "stop_requested"}


@router.get("/status/{run_id}")
async def battle_status(run_id: str) -> dict:
    state = battle_core.get_run_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run not found")
    task = battle_tasks.get(run_id)
    state_copy = dict(state)
    state_copy["task_active"] = bool(task and not task.done())
    return state_copy

@router.get("/list")
async def list_battles():
    """Return list of all runs with metrics summary."""
    return {"runs": battle_core.list_runs()}

@router.get("/get/{run_id}")
async def get_battle(run_id: str) -> dict:
    state = load_battle_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run not found")
    return state
