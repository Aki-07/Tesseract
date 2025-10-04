import os, time
from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel
from prometheus_client import Counter, Histogram, CONTENT_TYPE_LATEST, generate_latest

ADAPTER_ID = os.getenv("ADAPTER_ID", "defender-demo")
ADAPTER_PATH = os.getenv("ADAPTER_PATH", "/data/adapter")

app = FastAPI(title="Tesseract Capsule", version="0.1.0")

# Metrics
TOOL_CALLS = Counter(
    "capsule_tool_calls_total",
    "Total tool calls handled by capsule",
    labelnames=["tool", "status"],
)
TOOL_LATENCY = Histogram(
    "capsule_tool_latency_seconds",
    "Tool call latency (seconds)",
    labelnames=["tool"],
)

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


class AttackRequest(BaseModel):
    prompt: str

class ToolCall(BaseModel):
    name: str
    arguments: dict

@app.get("/health")
async def health():
    return {"capsule": ADAPTER_ID, "ok": True}

@app.get("/list_tools")
async def list_tools():
    return {
        "tools": [
            {"name": "generate_attack", "description": "Generate a demo attack string"},
            {"name": "evaluate_defense", "description": "Evaluate a demo defense (stub)"}
        ]
    }

@app.post("/call_tool")
async def call_tool(req: ToolCall):
    t0 = time.perf_counter()
    tool = req.name
    status = "ok"
    try:
        if req.name == "generate_attack":
            prompt = req.arguments.get("prompt", "")
            result = [{"type": "text", "text": f"[ATTACK-DEMO] {prompt}"}]
        elif req.name == "evaluate_defense":
            result = [{"type": "text", "text": "[DEFENSE-DEMO] safe=false,severity=low"}]
        else:
            status = "error"
            raise HTTPException(status_code=400, detail=f"Unknown tool {req.name}")
        return result
    finally:
        TOOL_CALLS.labels(tool, status).inc()
        TOOL_LATENCY.labels(tool).observe(time.perf_counter() - t0)
