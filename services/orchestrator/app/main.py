import asyncio
import os
import uuid
import json
from datetime import datetime
from typing import Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks, Request, Response
import httpx
import structlog
from app.routers import capsules
from contextlib import asynccontextmanager
from app.db import init_db

from .metrics import (
    metrics_endpoint,
    http_metrics_middleware,
    BATTLE_ROUNDS,
    BATTLE_BREACHES,
    BATTLE_ACTIVE,
    BREACH_RATE,
)

from pydantic import BaseModel

log = structlog.get_logger(__name__)
app = FastAPI(title="Tesseract Orchestrator", version="0.2.0")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup and shutdown."""
    print("Starting Tesseract Orchestrator...")
    init_db()  # create DB + tables
    yield
    print("🧩 Shutting down Orchestrator...")


def _name_endpoint(req: Request) -> str:
    # Small, low-cardinality name for metrics
    path = req.url.path
    # Optionally collapse run_id in paths like /battle/status/{id}
    if path.startswith("/battle/status/"):
        return "/battle/status/{id}"
    if path.startswith("/battle/get/"):
        return "/battle/get/{id}"
    return path


app.middleware("http")(http_metrics_middleware(_name_endpoint))
app.include_router(capsules.router)
app.get("/metrics")(metrics_endpoint())

# ---- Config via env ----
ATTACKER_URL = os.getenv("CAPSULE_ATTACKER_URL", "http://attacker-demo:9000")
DEFENDER_URL = os.getenv("CAPSULE_DEFENDER_URL", "http://defender-demo:9000")
DATA_DIR = os.getenv("DATA_DIR", "/data")
BATTLES_DIR = os.path.join(DATA_DIR, "battles")
os.makedirs(BATTLES_DIR, exist_ok=True)

battle_tasks: dict[str, asyncio.Task] = {}
battle_states: dict[str, dict] = {}


class StartBattleRequest(BaseModel):
    rounds: int = 20
    interval_seconds: float = 1.0
    attacker_tool: str = "generate_attack"
    defender_tool: str = "evaluate_defense"
    run_id: Optional[str] = None


async def call_capsule_tool(url: str, name: str, arguments: dict, timeout=15):
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(
            f"{url}/call_tool", json={"name": name, "arguments": arguments}
        )
        resp.raise_for_status()
        return resp.json()


def save_battle_state(run_id: str):
    path = os.path.join(BATTLES_DIR, f"{run_id}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(battle_states[run_id], f, indent=2, default=str)


def load_battle_state(run_id: str):
    path = os.path.join(BATTLES_DIR, f"{run_id}.json")
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


async def battle_runner(
    run_id: str,
    rounds: int,
    interval_seconds: float,
    attacker_tool: str,
    defender_tool: str,
):
    state = battle_states[run_id]
    state["status"] = "running"
    state["started_at"] = datetime.utcnow().isoformat()
    save_battle_state(run_id)

    # metrics: active runs +1
    BATTLE_ACTIVE.inc()

    try:
        for r in range(1, rounds + 1):
            if state.get("stop_requested"):
                log.info("battle.stop_requested", run_id=run_id)
                break

            try:
                att_resp = await call_capsule_tool(
                    ATTACKER_URL, attacker_tool, {"prompt": f"round-{r}"}
                )
                att_text = ""
                if isinstance(att_resp, list):
                    att_text = " ".join([it.get("text", "") for it in att_resp])
                elif isinstance(att_resp, dict):
                    att_text = att_resp.get("text", "")
                else:
                    att_text = str(att_resp)

                def_resp = await call_capsule_tool(
                    DEFENDER_URL, defender_tool, {"prompt": att_text}
                )
                def_text = ""
                if isinstance(def_resp, list):
                    def_text = " ".join([it.get("text", "") for it in def_resp])
                elif isinstance(def_resp, dict):
                    def_text = def_resp.get("text", "")
                else:
                    def_text = str(def_resp)

                lowered = def_text.lower()
                breach = any(
                    token in lowered
                    for token in (
                        "safe=false",
                        "safe: false",
                        "allowed=false",
                        "breach=true",
                    )
                )

                round_entry = {
                    "round": r,
                    "timestamp": datetime.utcnow().isoformat(),
                    "attacker_output": att_text,
                    "defender_output": def_text,
                    "breach": breach,
                }
                state["rounds"].append(round_entry)
                state["total_rounds"] = r
                if breach:
                    state["breaches"] += 1
                    # metrics: breach count +1
                    BATTLE_BREACHES.inc()

                # metrics: rounds +1
                BATTLE_ROUNDS.inc()

                state["breach_rate"] = state["breaches"] / state["total_rounds"]
                # metrics: gauge updated
                BREACH_RATE.set(state["breach_rate"])

                save_battle_state(run_id)
                log.info("battle.round", run_id=run_id, round=r, breach=breach)

            except Exception as e:
                log.error("battle.round_error", run_id=run_id, round=r, error=str(e))
                state["errors"].append({"round": r, "error": str(e)})
                save_battle_state(run_id)

            await asyncio.sleep(interval_seconds)

        state["status"] = "stopped" if state.get("stop_requested") else "completed"
        state["finished_at"] = datetime.utcnow().isoformat()
        save_battle_state(run_id)
        log.info("battle.finished", run_id=run_id, status=state["status"])
    finally:
        # metrics: active runs -1
        BATTLE_ACTIVE.dec()


@app.get("/health")
async def health():
    return {
        "service": "orchestrator",
        "ok": True,
        "attacker_url": ATTACKER_URL,
        "defender_url": DEFENDER_URL,
    }


@app.post("/battle/start")
async def start_battle(req: StartBattleRequest, background_tasks: BackgroundTasks):
    run_id = req.run_id or str(uuid.uuid4())[:8]
    if run_id in battle_tasks:
        raise HTTPException(status_code=400, detail=f"run_id {run_id} already exists")

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
    }
    save_battle_state(run_id)

    task = asyncio.create_task(
        battle_runner(
            run_id,
            req.rounds,
            req.interval_seconds,
            req.attacker_tool,
            req.defender_tool,
        )
    )
    battle_tasks[run_id] = task

    return {"run_id": run_id, "status": "started"}


@app.post("/battle/stop/{run_id}")
async def stop_battle(run_id: str):
    state = battle_states.get(run_id) or load_battle_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run not found")
    state["stop_requested"] = True
    battle_states[run_id] = state
    save_battle_state(run_id)
    return {"run_id": run_id, "status": "stop_requested"}


@app.get("/battle/status/{run_id}")
async def battle_status(run_id: str):
    state = battle_states.get(run_id) or load_battle_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run not found")
    task = battle_tasks.get(run_id)
    state_copy = dict(state)
    state_copy["task_active"] = bool(task and not task.done())
    return state_copy


@app.get("/battle/list")
async def list_battles():
    files = [f for f in os.listdir(BATTLES_DIR) if f.endswith(".json")]
    return {"runs": [f[:-5] for f in files]}


@app.get("/battle/get/{run_id}")
async def get_battle(run_id: str):
    state = load_battle_state(run_id)
    if not state:
        raise HTTPException(status_code=404, detail="run not found")
    return state
