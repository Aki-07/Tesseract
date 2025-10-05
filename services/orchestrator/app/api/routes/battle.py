# app/api/routes/battle.py
from __future__ import annotations

import asyncio
from asyncio import log
import uuid
from typing import Optional
import json, pathlib 
from fastapi import APIRouter, BackgroundTasks, HTTPException

from ...core import battle as battle_core
from ...core.state import battle_tasks
from ...core.storage import load_battle_state
from ..schemas import StartBattleRequest
from ...core.spawner import spawn_capsule, stop_capsule
from ...core.storage import save_battle_state

router = APIRouter(prefix="/battle", tags=["battle"])

@router.post("/start")
async def start_battle(
    req: StartBattleRequest, background_tasks: BackgroundTasks
) -> dict:
    """
    Start a single battle run.
    Automatically spawns attacker & defender capsules if URLs not provided.
    """
    run_id = req.run_id or str(uuid.uuid4())[:8]
    if run_id in battle_tasks:
        raise HTTPException(status_code=400, detail=f"run_id {run_id} already exists")

    # initialize state on disk/in-memory
    battle_core.create_initial_state(run_id)

    # Extract user-provided or default model info
    attacker_url: Optional[str] = getattr(req, "attacker_url", None)
    defender_url: Optional[str] = getattr(req, "defender_url", None)
    attacker_model: Optional[str] = getattr(req, "attacker_model", None)
    defender_model: Optional[str] = getattr(req, "defender_model", None)

    # 🔥 Auto-spawn capsules if URLs not provided
    attacker_container = None
    defender_container = None

    try:
        if not attacker_url and attacker_model:
            spawn_res = spawn_capsule(attacker_model, "attacker")
            # If you updated spawn_capsule to return dict
            if isinstance(spawn_res, dict):
                attacker_url = spawn_res["url"]
                attacker_container = spawn_res["container_name"]
            else:
                attacker_url = spawn_res

        if not defender_url and defender_model:
            spawn_res = spawn_capsule(defender_model, "defender")
            if isinstance(spawn_res, dict):
                defender_url = spawn_res["url"]
                defender_container = spawn_res["container_name"]
            else:
                defender_url = spawn_res

    except Exception as e:
        log.error("capsule_spawn_failed", error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to spawn capsules: {e}")

    # Create background task
    task = asyncio.create_task(
        battle_core.battle_runner(
            run_id,
            rounds=req.rounds,
            interval_seconds=req.interval_seconds,
            attacker_tool=req.attacker_tool,
            defender_tool=req.defender_tool,
            attacker_url=attacker_url,
            defender_url=defender_url,
            attacker_model=attacker_model,
            defender_model=defender_model,
        ),
        name=f"battle-{run_id}",
    )

    # Register task
    battle_core.register_task(run_id, task)

    # Save container metadata for cleanup
    state = battle_core.get_run_state(run_id)
    state["meta"] = state.get("meta", {})
    state["meta"]["attacker_container"] = attacker_container
    state["meta"]["defender_container"] = defender_container
    battle_core.set_run_state(run_id, state)
    save_battle_state(run_id)

    return {
        "run_id": run_id,
        "status": "started",
        "attacker_url": attacker_url,
        "defender_url": defender_url,
    }



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


@router.get("/mcp/manifest") 
def mcp_manifest(): 
    p = pathlib.Path(__file__).resolve().parents[2] / "mcp_manifest.json" 
    return json.loads(p.read_text())