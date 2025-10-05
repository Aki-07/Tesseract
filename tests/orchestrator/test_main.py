import importlib
import sys

import pytest
from fastapi import BackgroundTasks, HTTPException


@pytest.fixture
def orchestrator_modules(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    module_names = [
        "services.orchestrator.app.core.state",
        "services.orchestrator.app.core.storage",
        "services.orchestrator.app.core.battle",
        "services.orchestrator.app.api.routes.battle",
        "services.orchestrator.app.api.schemas",
    ]
    for name in module_names:
        sys.modules.pop(name, None)

    storage = importlib.import_module("services.orchestrator.app.core.storage")
    state = importlib.import_module("services.orchestrator.app.core.state")
    battle_core = importlib.import_module("services.orchestrator.app.core.battle")
    schemas = importlib.import_module("services.orchestrator.app.api.schemas")
    battle_routes = importlib.import_module(
        "services.orchestrator.app.api.routes.battle"
    )

    yield {
        "battle_core": battle_core,
        "battle_routes": battle_routes,
        "state": state,
        "storage": storage,
        "schemas": schemas,
    }

    battle_core.battle_tasks.clear()
    battle_core.battle_states.clear()


def _dummy_request(path: str):
    class _URL:
        def __init__(self, value: str):
            self.path = value

    class _Request:
        def __init__(self, value: str):
            self.url = _URL(value)

    return _Request(path)


def test_name_endpoint_sanitizes_ids():
    module = importlib.import_module("services.orchestrator.app.api.app")
    assert (
        module._name_endpoint(_dummy_request("/battle/status/abc"))
        == "/battle/status/{id}"
    )
    assert (
        module._name_endpoint(_dummy_request("/battle/get/xyz")) == "/battle/get/{id}"
    )
    assert module._name_endpoint(_dummy_request("/health")) == "/health"


@pytest.mark.asyncio
async def test_battle_runner_updates_state_and_metrics(
    orchestrator_modules, monkeypatch
):
    battle_core = orchestrator_modules["battle_core"]

    run_id = "runner"
    battle_core.battle_states[run_id] = {
        "run_id": run_id,
        "created_at": "now",
        "status": "queued",
        "rounds": [],
        "errors": [],
        "breaches": 0,
        "total_rounds": 0,
        "breach_rate": 0.0,
        "stop_requested": False,
    }

    async def fake_call(url, name, arguments, timeout=15):
        if name == "generate_attack":
            return [{"text": "round-attack"}]
        return [{"text": "safe=false"}]

    async def immediate_sleep(_):
        return None

    monkeypatch.setattr(battle_core, "call_capsule_tool", fake_call)
    monkeypatch.setattr(battle_core.asyncio, "sleep", immediate_sleep)

    await battle_core.battle_runner(
        run_id,
        rounds=1,
        interval_seconds=0,
        attacker_tool="generate_attack",
        defender_tool="evaluate_defense",
    )

    state = battle_core.battle_states[run_id]
    assert state["status"] == "completed"
    assert state["total_rounds"] == 1
    assert state["breaches"] == 1
    assert state["breach_rate"] == 1.0
    assert len(state["rounds"]) == 1


@pytest.mark.asyncio
async def test_start_battle_creates_state_and_task(orchestrator_modules, monkeypatch):
    battle_core = orchestrator_modules["battle_core"]
    battle_routes = orchestrator_modules["battle_routes"]
    schemas = orchestrator_modules["schemas"]

    class DummyTask:
        def __init__(self, coro):
            self.coro = coro
            coro.close()

        def done(self):
            return False

    def fake_create_task(coro, *args, **kwargs):
        return DummyTask(coro)

    monkeypatch.setattr(battle_routes.asyncio, "create_task", fake_create_task)

    req = schemas.StartBattleRequest(rounds=1, interval_seconds=0.0, run_id="run123")
    result = await battle_routes.start_battle(req, BackgroundTasks())

    assert result == {"run_id": "run123", "status": "started"}
    assert "run123" in battle_core.battle_states
    assert "run123" in battle_core.battle_tasks
    assert isinstance(battle_core.battle_tasks["run123"], DummyTask)

    with pytest.raises(HTTPException):
        await battle_routes.start_battle(req, BackgroundTasks())


@pytest.mark.asyncio
async def test_stop_battle_sets_stop_requested(orchestrator_modules):
    battle_core = orchestrator_modules["battle_core"]
    battle_routes = orchestrator_modules["battle_routes"]

    run_id = "stop123"
    battle_core.battle_states[run_id] = {
        "run_id": run_id,
        "created_at": "now",
        "status": "running",
        "rounds": [],
        "errors": [],
        "breaches": 0,
        "total_rounds": 0,
        "breach_rate": 0.0,
        "stop_requested": False,
    }

    result = await battle_routes.stop_battle(run_id)

    assert result == {"run_id": run_id, "status": "stop_requested"}
    assert battle_core.battle_states[run_id]["stop_requested"] is True


@pytest.mark.asyncio
async def test_battle_status_and_persistence(orchestrator_modules):
    battle_core = orchestrator_modules["battle_core"]
    battle_routes = orchestrator_modules["battle_routes"]
    storage = orchestrator_modules["storage"]

    run_id = "status123"
    battle_core.battle_states[run_id] = {
        "run_id": run_id,
        "created_at": "now",
        "status": "running",
        "rounds": [],
        "errors": [],
        "breaches": 0,
        "total_rounds": 0,
        "breach_rate": 0.0,
        "stop_requested": False,
    }

    class DummyTask:
        def done(self):
            return False

    battle_core.battle_tasks[run_id] = DummyTask()
    status = await battle_routes.battle_status(run_id)
    assert status["task_active"] is True

    storage.save_battle_state(run_id)
    listed = await battle_routes.list_battles()
    assert run_id in listed["runs"]

    loaded = await battle_routes.get_battle(run_id)
    assert loaded["run_id"] == run_id
