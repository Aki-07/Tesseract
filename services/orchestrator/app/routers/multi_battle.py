# services/orchestrator/app/routers/multi_battle.py
import asyncio
import json
import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Capsule as CapsuleModel
from ..metrics import (
    BATTLE_ROUNDS,
    BATTLE_BREACHES,
    BATTLE_ACTIVE,
    BREACH_RATE,
)
from ..state import battle_tasks, battle_states
from ..storage import save_battle_state, load_battle_state
from datetime import datetime
import httpx
import structlog

log = structlog.get_logger(__name__)
router = APIRouter(prefix="/battle", tags=["battle"])

from pydantic import BaseModel


class ManualPair(BaseModel):
    attacker_url: str
    defender_url: str
    attacker_tool: Optional[str] = "generate_attack"
    defender_tool: Optional[str] = "evaluate_defense"
    rounds: Optional[int] = 20
    interval_seconds: Optional[float] = 1.0


class StartMultiRequest(BaseModel):
    mode: str = "manual_pairs"
    manual_pairs: Optional[List[ManualPair]] = None
    attacker_role: Optional[str] = "attack"
    defender_role: Optional[str] = "defense"
    rounds: Optional[int] = 20
    interval_seconds: Optional[float] = 1.0
    num_matches: Optional[int] = 10
    concurrency: Optional[int] = 4
    attacker_tool: Optional[str] = "generate_attack"
    defender_tool: Optional[str] = "evaluate_defense"


def _capsule_to_dict(capsule: CapsuleModel) -> dict:
    def _loads(val, default):
        if not val:
            return default
        try:
            return json.loads(val)
        except Exception:
            return default

    return {
        "id": capsule.id,
        "name": capsule.name,
        "role": capsule.role.value if hasattr(capsule.role, "value") else capsule.role,
        "env": _loads(capsule.env, {}),
        "config": _loads(capsule.config, {}),
        "tags": _loads(capsule.tags, []),
        "image": capsule.image,
        "entrypoint": capsule.entrypoint,
    }


def resolve_service_url(capsule: CapsuleModel) -> Optional[str]:
    """Priority: config.service_url -> env.SERVICE_URL -> fallback http://{name}:9000"""
    try:
        cfg = json.loads(capsule.config) if capsule.config else {}
    except Exception:
        cfg = {}
    try:
        env = json.loads(capsule.env) if capsule.env else {}
    except Exception:
        env = {}

    if "service_url" in cfg:
        return cfg["service_url"]
    if "SERVICE_URL" in env:
        return env["SERVICE_URL"]
    return f"http://{capsule.name}:9000"


async def call_capsule_tool(url: str, name: str, arguments: dict, timeout=15):
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(f"{url}/call_tool", json={"name": name, "arguments": arguments})
        resp.raise_for_status()
        return resp.json()


# Single-runner (per-run) 
async def single_battle_runner(
    run_id: str,
    rounds: int,
    interval_seconds: float,
    attacker_url: str,
    defender_url: str,
    attacker_tool: str = "generate_attack",
    defender_tool: str = "evaluate_defense",
):
    """Runner that persistently saves state to disk via save_battle_state."""
    state = battle_states[run_id]
    state["status"] = "running"
    state["started_at"] = datetime.utcnow().isoformat()
    save_battle_state(run_id)  # persist initial queued->running

    BATTLE_ACTIVE.inc()

    try:
        for r in range(1, rounds + 1):
            if state.get("stop_requested"):
                log.info("multi_battle.stop_requested", run_id=run_id)
                break

            try:
                att_resp = await call_capsule_tool(attacker_url, attacker_tool, {"prompt": f"round-{r}"})
                att_text = ""
                if isinstance(att_resp, list):
                    att_text = " ".join([it.get("text", "") for it in att_resp])
                elif isinstance(att_resp, dict):
                    att_text = att_resp.get("text", "")
                else:
                    att_text = str(att_resp)

                def_resp = await call_capsule_tool(defender_url, defender_tool, {"prompt": att_text})
                def_text = ""
                if isinstance(def_resp, list):
                    def_text = " ".join([it.get("text", "") for it in def_resp])
                elif isinstance(def_resp, dict):
                    def_text = def_resp.get("text", "")
                else:
                    def_text = str(def_resp)

                lowered = def_text.lower()
                breach = any(
                    token in lowered for token in ("safe=false", "safe: false", "allowed=false", "breach=true")
                )

                round_entry = {
                    "round": r,
                    "timestamp": datetime.utcnow().isoformat(),
                    "attacker_output": att_text,
                    "defender_output": def_text,
                    "breach": breach,
                    "attacker_url": attacker_url,
                    "defender_url": defender_url,
                }
                state["rounds"].append(round_entry)
                state["total_rounds"] = r
                if breach:
                    state["breaches"] += 1
                    BATTLE_BREACHES.inc()

                BATTLE_ROUNDS.inc()
                state["breach_rate"] = state["breaches"] / state["total_rounds"] if state["total_rounds"] else 0.0
                BREACH_RATE.set(state["breach_rate"])

                # persist after each round
                save_battle_state(run_id)
                log.info("multi_battle.round", run_id=run_id, round=r, breach=breach)

            except Exception as e:
                log.error("multi_battle.round_error", run_id=run_id, round=r, error=str(e))
                state["errors"].append({"round": r, "error": str(e)})
                save_battle_state(run_id)

            await asyncio.sleep(interval_seconds)

        state["status"] = "stopped" if state.get("stop_requested") else "completed"
        state["finished_at"] = datetime.utcnow().isoformat()
        save_battle_state(run_id)  # persist final state
        log.info("multi_battle.finished", run_id=run_id, status=state["status"])
    finally:
        BATTLE_ACTIVE.dec()


# Endpoint: start_multi
@router.post("/start_multi")
async def start_multi(req: StartMultiRequest, db: Session = Depends(get_db)):
    pairs = []

    if req.mode == "manual_pairs":
        if not req.manual_pairs:
            raise HTTPException(status_code=400, detail="manual_pairs required for mode manual_pairs")
        for p in req.manual_pairs:
            pairs.append(
                {
                    "attacker_url": p.attacker_url,
                    "defender_url": p.defender_url,
                    "attacker_tool": p.attacker_tool,
                    "defender_tool": p.defender_tool,
                    "rounds": p.rounds,
                    "interval_seconds": p.interval_seconds,
                }
            )
    elif req.mode == "from_registry":
        attackers = db.query(CapsuleModel).filter(CapsuleModel.role == req.attacker_role).all()
        defenders = db.query(CapsuleModel).filter(CapsuleModel.role == req.defender_role).all()
        if not attackers or not defenders:
            raise HTTPException(status_code=400, detail="Not enough capsules found for specified roles")
        for i in range(req.num_matches):
            a = attackers[i % len(attackers)]
            d = defenders[i % len(defenders)]
            a_url = resolve_service_url(a)
            d_url = resolve_service_url(d)
            pairs.append(
                {
                    "attacker_url": a_url,
                    "defender_url": d_url,
                    "attacker_tool": req.attacker_tool,
                    "defender_tool": req.defender_tool,
                    "rounds": req.rounds,
                    "interval_seconds": req.interval_seconds,
                }
            )
    else:
        raise HTTPException(status_code=400, detail="Unsupported mode")

    concurrency = max(1, getattr(req, "concurrency", 4))
    sem = asyncio.Semaphore(concurrency)

    async def run_pair(pair):
        run_id = (str(uuid.uuid4())[:8])
        battle_states[run_id] = {
            "run_id": run_id,
            "created_at": datetime.utcnow().isoformat(),
            "status": "queued",
            "rounds": [],
            "errors": [],
            "breaches": 0,
            "total_rounds": 0,
            "breach_rate": 0.0,
            "stop_requested": False,
            "meta": {
                "attacker_url": pair["attacker_url"],
                "defender_url": pair["defender_url"],
                "attacker_tool": pair.get("attacker_tool"),
                "defender_tool": pair.get("defender_tool"),
            },
        }

        # persist queued state
        save_battle_state(run_id)

        async with sem:
            task = asyncio.create_task(
                single_battle_runner(
                    run_id=run_id,
                    rounds=pair["rounds"],
                    interval_seconds=pair["interval_seconds"],
                    attacker_url=pair["attacker_url"],
                    defender_url=pair["defender_url"],
                    attacker_tool=pair.get("attacker_tool", "generate_attack"),
                    defender_tool=pair.get("defender_tool", "evaluate_defense"),
                )
            )
            battle_tasks[run_id] = task
            log.info("started multi battle", run_id=run_id, attacker=pair["attacker_url"], defender=pair["defender_url"])
            return run_id

    start_tasks = [asyncio.create_task(run_pair(p)) for p in pairs]
    run_ids = await asyncio.gather(*start_tasks)
    return {"started_run_ids": run_ids, "num_requested": len(pairs)}
