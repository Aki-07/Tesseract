import importlib
import sys

import pytest
from fastapi import HTTPException
from prometheus_client import REGISTRY


def _sample_value(metric, sample_name, labels):
    for collected in metric.collect():
        for sample in collected.samples:
            if sample.name == sample_name and sample.labels == labels:
                return sample.value
    return 0.0


@pytest.fixture
def capsule(monkeypatch):
    monkeypatch.setenv("ADAPTER_ID", "unit-test-adapter")
    monkeypatch.setenv("ADAPTER_PATH", "/tmp/adapter")

    module_name = "services.capsule.mcp_server"
    existing = sys.modules.get(module_name)
    if existing is not None:
        collectors = {
            collector
            for name, collector in REGISTRY._names_to_collectors.items()
            if name.startswith("capsule_tool_")
        }
        for collector in collectors:
            REGISTRY.unregister(collector)
    sys.modules.pop(module_name, None)
    module = importlib.import_module(module_name)
    yield module


@pytest.mark.asyncio
async def test_metrics_endpoint_returns_payload(capsule):
    response = await capsule.metrics()
    assert response.media_type == capsule.CONTENT_TYPE_LATEST
    assert response.body.startswith(b"# HELP")


@pytest.mark.asyncio
async def test_health_returns_current_adapter(capsule):
    body = await capsule.health()
    assert body == {"capsule": "unit-test-adapter", "ok": True}


@pytest.mark.asyncio
async def test_list_tools_describes_available_tools(capsule):
    body = await capsule.list_tools()
    tool_names = {tool["name"] for tool in body["tools"]}
    assert {"generate_attack", "evaluate_defense"} <= tool_names


@pytest.mark.asyncio
async def test_call_tool_generate_attack_increments_metrics(capsule):
    labels_calls = {"tool": "generate_attack", "status": "ok"}
    labels_latency = {"tool": "generate_attack"}

    before_calls = _sample_value(
        capsule.TOOL_CALLS, "capsule_tool_calls_total", labels_calls
    )
    before_latency = _sample_value(
        capsule.TOOL_LATENCY, "capsule_tool_latency_seconds_count", labels_latency
    )

    result = await capsule.call_tool(
        capsule.ToolCall(name="generate_attack", arguments={"prompt": "hi"})
    )

    assert result[0]["text"].startswith("[ATTACK-DEMO]")

    after_calls = _sample_value(
        capsule.TOOL_CALLS, "capsule_tool_calls_total", labels_calls
    )
    after_latency = _sample_value(
        capsule.TOOL_LATENCY, "capsule_tool_latency_seconds_count", labels_latency
    )

    assert after_calls == pytest.approx(before_calls + 1)
    assert after_latency == pytest.approx(before_latency + 1)


@pytest.mark.asyncio
async def test_call_tool_unknown_records_error(capsule):
    labels_calls = {"tool": "unknown", "status": "error"}

    before_calls = _sample_value(
        capsule.TOOL_CALLS, "capsule_tool_calls_total", labels_calls
    )

    with pytest.raises(HTTPException):
        await capsule.call_tool(capsule.ToolCall(name="unknown", arguments={}))

    after_calls = _sample_value(
        capsule.TOOL_CALLS, "capsule_tool_calls_total", labels_calls
    )
    assert after_calls == pytest.approx(before_calls + 1)
