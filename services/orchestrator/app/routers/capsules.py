from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import SessionLocal
from app.models import Capsule, Role
from app.schemas import CapsuleCreate, CapsuleOut
import json

router = APIRouter(prefix="/capsules", tags=["capsules"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("", response_model=CapsuleOut)
def create_capsule(payload: CapsuleCreate, db: Session = Depends(get_db)):
    """Register a new capsule (attack/defense)."""
    obj = Capsule(
        name=payload.name,
        version=payload.version,
        role=Role(payload.role),
        image=payload.image,
        entrypoint=payload.entrypoint,
        env=json.dumps(payload.env or {}),
        config=json.dumps(payload.config or {}),
        tags=json.dumps(payload.tags or []),
        enabled=payload.enabled,
        owner=payload.owner,
        description=payload.description,
    )
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


@router.get("", response_model=List[CapsuleOut])
def list_capsules(db: Session = Depends(get_db)):
    """List all registered capsules."""
    items = db.query(Capsule).all()
    return [c for c in items]
