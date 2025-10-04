from fastapi import FastAPI, HTTPException
import httpx
import os

app = FastAPI(title="Tesseract Orchestrator")

CAPSULE_URL = os.getenv("CAPSULE_URL", "http://capsule-demo:9000")

@app.get("/health")
async def health():
    return {
        "service": "orchestrator",
        "ok": True,
        "capsule_url": CAPSULE_URL
    }

@app.get("/mcp/tools")
async def list_tools():
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(f"{CAPSULE_URL}/list_tools")
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

@app.post("/mcp/demo_attack")
async def demo_attack(prompt: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.post(
                f"{CAPSULE_URL}/call_tool",
                json={"name": "generate_attack", "arguments": {"prompt": prompt}}
            )
            return resp.json()
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
