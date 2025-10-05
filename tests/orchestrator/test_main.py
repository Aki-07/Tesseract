import importlib
import sys

import pytest
from fastapi import BackgroundTasks, HTTPException


@pytest.fixture
def orchestrator(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    module_name = "services.orchestrator.app.main"
    sys.modules.pop(module_name, None)
    module = importlib.import_module(module_name)
    yield module
    # clean up between tests
    for task in list(module.battle_tasks.values()):
        cancel = getattr(task, "cancel", None)
        if callable(cancel):
            cancel()
    module.battle_tasks.clear()
    module.battle_states.clear()


def _dummy_request(path: str):
    class _URL:
        def __init__(self, value: str):
            self.path = value

    class _Request:
        def __init__(self, value: str):
            self.url = _URL(value)

    return _Request(path)


def test_name_endpoint_sanitizes_ids(orchestrator):
    assert orchestrator._name_endpoint(_dummy_request("/battle/status/abc")) == "/battle/status/{id}"
    assert orchestrator._name_endpoint(_dummy_request("/battle/get/xyz")) == "/battle/get/{id}"
    assert orchestrator._name_endpoint(_dummy_request("/health")) == "/health"


@pytest.mark.asyncio
async def test_battle_runner_updates_state_and_metrics(orchestrator, monkeypatch):
    run_id = "runner"
    orchestrator.battle_states[run_id] = {
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

    monkeypatch.setattr(orchestrator, "call_capsule_tool", fake_call)
    monkeypatch.setattr(orchestrator.asyncio, "sleep", immediate_sleep)

    await orchestrator.battle_runner(
        run_id,
        rounds=1,
        interval_seconds=0,
        attacker_tool="generate_attack",
        defender_tool="evaluate_defense",
    )

    state = orchestrator.battle_states[run_id]
    assert state["status"] == "completed"
    assert state["total_rounds"] == 1
    assert state["breaches"] == 1
    assert state["breach_rate"] == 1.0
    assert len(state["rounds"]) == 1


@pytest.mark.asyncio
async def test_start_battle_creates_state_and_task(orchestrator, monkeypatch):
    class DummyTask:
        def __init__(self, coro):
            self.coro = coro
            coro.close()

        def done(self):
            return False

    monkeypatch.setattr(orchestrator.asyncio, "create_task", lambda coro: DummyTask(coro))

    req = orchestrator.StartBattleRequest(rounds=1, interval_seconds=0.0, run_id="run123")
    result = await orchestrator.start_battle(req, BackgroundTasks())

    assert result == {"run_id": "run123", "status": "started"}
    assert "run123" in orchestrator.battle_states
    assert "run123" in orchestrator.battle_tasks
    assert isinstance(orchestrator.battle_tasks["run123"], DummyTask)

    with pytest.raises(HTTPException):
        await orchestrator.start_battle(req, BackgroundTasks())


@pytest.mark.asyncio
async def test_stop_battle_sets_stop_requested(orchestrator):
    run_id = "stop123"
    orchestrator.battle_states[run_id] = {
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

    result = await orchestrator.stop_battle(run_id)

    assert result == {"run_id": run_id, "status": "stop_requested"}
    assert orchestrator.battle_states[run_id]["stop_requested"] is True


@pytest.mark.asyncio
async def test_battle_status_and_persistence(orchestrator, tmp_path):
    run_id = "status123"
    orchestrator.battle_states[run_id] = {
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

    orchestrator.battle_tasks[run_id] = DummyTask()
    status = await orchestrator.battle_status(run_id)
    assert status["task_active"] is True

    orchestrator.save_battle_state(run_id)
    listed = await orchestrator.list_battles()
    assert run_id in listed["runs"]

    loaded = await orchestrator.get_battle(run_id)
    assert loaded["run_id"] == run_id
