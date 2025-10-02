from fastapi import FastAPI
from pydantic import BaseModel
import random

app = FastAPI(title="Toxicity Judge MCP")


class JudgeRequest(BaseModel):
    text: str


class JudgeResponse(BaseModel):
    toxicity_score: float


@app.get("/health")
def health():
    return {"service": "toxicity-judge", "ok": True}


@app.post("/judge", response_model=JudgeResponse)
def judge(req: JudgeRequest):
    """
    Fake toxicity judge: assigns a random toxicity score.
    Later: plug in Perspective API, Detoxify, or a fine-tuned Llama.
    """
    score = round(random.uniform(0.0, 1.0), 3)
    return {"toxicity_score": score}
