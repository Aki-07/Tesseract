from fastapi import APIRouter, HTTPException,Depends
from sqlalchemy.orm import Session
from ..db import get_db
from ..models import Capsule
from pydantic import BaseModel
from typing import List, Optional
import json
import uuid

router = APIRouter(prefix="/capsules", tags=["capsules"])


# Schema for POST 
class CapsuleCreate(BaseModel):
    name: str
    version: str
    role: str
    image: str
    entrypoint: Optional[str] = None
    env: Optional[dict] = None
    config: Optional[dict] = None
    tags: Optional[list[str]] = None
    enabled: bool = True
    owner: Optional[str] = None
    description: Optional[str] = None


# Schema for GET
class CapsuleOut(BaseModel):
    id: str
    name: str
    version: str
    role: str
    image: str
    entrypoint: Optional[str]
    env: Optional[dict]
    config: Optional[dict]
    tags: Optional[list[str]]
    enabled: bool
    owner: Optional[str]
    description: Optional[str]

    class Config:
        from_attributes = True


# Endpoints 
@router.post("", response_model=CapsuleOut)
def create_capsule(capsule: CapsuleCreate, db: Session = Depends(get_db)):
    """Insert capsule into registry and return a Pydantic-safe object."""
    try:
        db_capsule = Capsule(
            id=str(uuid.uuid4()),
            name=capsule.name,
            version=capsule.version,
            role=capsule.role,
            image=capsule.image,
            entrypoint=capsule.entrypoint,
            env=json.dumps(capsule.env or {}),
            config=json.dumps(capsule.config or {}),
            tags=json.dumps(capsule.tags or []),
            enabled=capsule.enabled,
            owner=capsule.owner,
            description=capsule.description,
        )
        db.add(db_capsule)
        db.commit()
        db.refresh(db_capsule)

        # Return a Pydantic object with deserialized fields (avoid validation error)
        return CapsuleOut(
            id=db_capsule.id,
            name=db_capsule.name,
            version=db_capsule.version,
            role=db_capsule.role,
            image=db_capsule.image,
            entrypoint=db_capsule.entrypoint,
            env=json.loads(db_capsule.env or "{}"),
            config=json.loads(db_capsule.config or "{}"),
            tags=json.loads(db_capsule.tags or "[]"),
            enabled=db_capsule.enabled,
            owner=db_capsule.owner,
            description=db_capsule.description,
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))



@router.get("", response_model=List[CapsuleOut])
def list_capsules(db: Session = Depends(get_db)):
    """List all capsules."""
    capsules = db.query(Capsule).all()
    # convert JSON fields
    results = []
    for c in capsules:
        results.append(CapsuleOut(
            id=c.id,
            name=c.name,
            version=c.version,
            role=c.role,
            image=c.image,
            entrypoint=c.entrypoint,
            env=json.loads(c.env or "{}"),
            config=json.loads(c.config or "{}"),
            tags=json.loads(c.tags or "[]"),
            enabled=c.enabled,
            owner=c.owner,
            description=c.description,
        ))
    return results


@router.get("/{capsule_id}", response_model=CapsuleOut)
def get_capsule(capsule_id: str, db: Session = Depends(get_db)):
    """Fetch a capsule by ID and return a Pydantic-safe object."""
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")

    return CapsuleOut(
        id=capsule.id,
        name=capsule.name,
        version=capsule.version,
        role=capsule.role,
        image=capsule.image,
        entrypoint=capsule.entrypoint,
        env=json.loads(capsule.env or "{}"),
        config=json.loads(capsule.config or "{}"),
        tags=json.loads(capsule.tags or "[]"),
        enabled=capsule.enabled,
        owner=capsule.owner,
        description=capsule.description,
    )
