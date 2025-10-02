from fastapi import FastAPI
from pydantic import BaseModel
import random, requests
from db import SessionLocal, init_db, Candidate

app = FastAPI(title="Tessera Orchestrator")
init_db()


class ExperimentReq(BaseModel):
    num_candidates: int = 3


@app.get("/health")
def health():
    return {"service": "orchestrator", "ok": True}


@app.post("/start_experiment")
def start_experiment(req: ExperimentReq):
    """Seeds fake candidates, evaluates via style-judge + toxicity-judge, stores in DB."""
    session = SessionLocal()
    candidates = []

    for _ in range(req.num_candidates):
        rank = random.choice([4, 8, 16])
        alpha = round(random.uniform(0.1, 1.0), 2)

        # seed candidate
        candidate = Candidate(
            rank=rank,
            alpha=alpha,
            status="submitted",
            cerebras_job_id=f"job-{random.randint(1000, 9999)}",
        )
        session.add(candidate)
        session.commit()
        session.refresh(candidate)

        # generate fake output text (later = real inference)
        sample_text = f"Sample output from candidate {candidate.id}"

        # --- call style-judge MCP ---
        try:
            r = requests.post(
                "http://style-judge:8091/judge",
                json={"text": sample_text},
                timeout=5,
            )
            style_score = r.json().get("style_score")
        except Exception:
            style_score = None

        # --- call toxicity-judge MCP ---
        try:
            r = requests.post(
                "http://toxicity-judge:8092/judge",
                json={"text": sample_text},
                timeout=5,
            )
            toxicity_score = r.json().get("toxicity_score")
        except Exception:
            toxicity_score = None

        # update DB
        candidate.style_score = style_score
        candidate.toxicity_score = toxicity_score
        session.commit()

        candidates.append(
            {
                "id": candidate.id,
                "rank": rank,
                "alpha": alpha,
                "status": candidate.status,
                "style_score": style_score,
                "toxicity_score": toxicity_score,
                "job_id": candidate.cerebras_job_id,
            }
        )

    session.close()
    return {"candidates": candidates}


@app.get("/get_candidates")
def get_candidates():
    """Return all candidates and their metrics."""
    session = SessionLocal()
    rows = session.query(Candidate).all()
    result = []
    for c in rows:
        result.append(
            {
                "id": c.id,
                "rank": c.rank,
                "alpha": c.alpha,
                "status": c.status,
                "style_score": c.style_score,
                "toxicity_score": c.toxicity_score,
                "latency_ms": c.latency_ms,
                "job_id": c.cerebras_job_id,
            }
        )
    session.close()
    return {"candidates": result}
