from fastapi import FastAPI

app = FastAPI(title="Tessera")


@app.get("/health")
def health_endpoint():
    return {"service": "inference", "ok": True}
