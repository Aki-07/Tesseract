from fastapi import FastAPI
import os, requests

app = FastAPI(title="Tessera Orchestrator")

INFER_URL = os.getenv("INFER_URL", "http://localhost:8082")

@app.get("/health")
def health():
    ok = False
    try:
        r = requests.get(f"{INFER_URL}/health", timeout=2)
        ok = (r.status_code == 200)
    except Exception as e:
        print("inference unreachable:", e)
    return {"service": "orchestrator", "inference_ok": ok}
