import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

ADAPTER_ID = os.getenv("ADAPTER_ID", "defender-demo")
ADAPTER_PATH = os.getenv("ADAPTER_PATH", "/data/adapter")

app = FastAPI(title="Tesseract Capsule", version="0.1.0")

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
    if req.name == "generate_attack":
        prompt = req.arguments.get("prompt", "")
        return [{"type": "text", "text": f"[ATTACK-DEMO] {prompt}"}]
    elif req.name == "evaluate_defense":
        return [{"type": "text", "text": "[DEFENSE-DEMO] safe=false,severity=low"}]
    else:
        raise HTTPException(status_code=400, detail=f"Unknown tool {req.name}")
