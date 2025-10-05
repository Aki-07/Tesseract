"""Capsule registry endpoints."""

import json
import uuid
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ...db import get_db
from ...db.models import Capsule, Role
from ..schemas import CapsuleCreate, CapsuleOut

router = APIRouter(prefix="/capsules", tags=["capsules"])


@router.post("", response_model=CapsuleOut)
def create_capsule(capsule: CapsuleCreate, db: Session = Depends(get_db)) -> CapsuleOut:
    try:
        db_capsule = Capsule(
            id=str(uuid.uuid4()),
            name=capsule.name,
            version=capsule.version,
            role=Role(capsule.role),
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
        return CapsuleOut(
            id=db_capsule.id,
            name=db_capsule.name,
            version=db_capsule.version,
            role=db_capsule.role.value if db_capsule.role else None,
            image=db_capsule.image,
            entrypoint=db_capsule.entrypoint,
            env=json.loads(db_capsule.env or "{}"),
            config=json.loads(db_capsule.config or "{}"),
            tags=json.loads(db_capsule.tags or "[]"),
            enabled=db_capsule.enabled,
            owner=db_capsule.owner,
            description=db_capsule.description,
            created_at=db_capsule.created_at,
            updated_at=db_capsule.updated_at,
        )
    except Exception as exc:  # pylint: disable=broad-except
        db.rollback()
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@router.get("", response_model=List[CapsuleOut])
def list_capsules(db: Session = Depends(get_db)) -> List[CapsuleOut]:
    capsules = db.query(Capsule).all()
    results: List[CapsuleOut] = []
    for capsule in capsules:
        results.append(
            CapsuleOut(
                id=capsule.id,
                name=capsule.name,
                version=capsule.version,
                role=capsule.role.value if capsule.role else None,
                image=capsule.image,
                entrypoint=capsule.entrypoint,
                env=json.loads(capsule.env or "{}"),
                config=json.loads(capsule.config or "{}"),
                tags=json.loads(capsule.tags or "[]"),
                enabled=capsule.enabled,
                owner=capsule.owner,
                description=capsule.description,
                created_at=capsule.created_at,
                updated_at=capsule.updated_at,
            )
        )
    return results


@router.get("/{capsule_id}", response_model=CapsuleOut)
def get_capsule(capsule_id: str, db: Session = Depends(get_db)) -> CapsuleOut:
    capsule = db.query(Capsule).filter(Capsule.id == capsule_id).first()
    if not capsule:
        raise HTTPException(status_code=404, detail="Capsule not found")

    return CapsuleOut(
        id=capsule.id,
        name=capsule.name,
        version=capsule.version,
        role=capsule.role.value if capsule.role else None,
        image=capsule.image,
        entrypoint=capsule.entrypoint,
        env=json.loads(capsule.env or "{}"),
        config=json.loads(capsule.config or "{}"),
        tags=json.loads(capsule.tags or "[]"),
        enabled=capsule.enabled,
        owner=capsule.owner,
        description=capsule.description,
        created_at=capsule.created_at,
        updated_at=capsule.updated_at,
    )
