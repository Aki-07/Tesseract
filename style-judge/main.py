from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI(title="Style Judge MCP")

class JudgeRequest(BaseModel):
    text: str

class JudgeResponse(BaseModel):
    style_score: float

@app.get("/health")
def health():
    return {"service": "style-judge", "ok": True}

@app.post("/judge", response_model=JudgeResponse)
def judge(req: JudgeRequest):
    """
    Fake style judge: assigns a random score 0-1.
    Later: replace with embeddings similarity to a reference style vector.
    """
    score = round(random.uniform(0.0, 1.0), 3)
    return {"style_score": score}
