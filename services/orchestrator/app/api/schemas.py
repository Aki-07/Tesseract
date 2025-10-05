from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel


class CapsuleBase(BaseModel):
    name: str
    version: str = "v1"
    role: str
    image: str
    entrypoint: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    config: Optional[Dict] = None
    tags: Optional[List[str]] = None
    enabled: bool = True
    owner: Optional[str] = None
    description: Optional[str] = None


class CapsuleCreate(CapsuleBase):
    pass


class CapsuleOut(CapsuleBase):
    id: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class StartBattleRequest(BaseModel):
    run_id: Optional[str] = None
    attacker_tool: str = "generate_attack"
    defender_tool: str = "evaluate_defense"
    rounds: int = 20
    interval_seconds: float = 1.0
    attacker_url: Optional[str] = None
    defender_url: Optional[str] = None
    attacker_model: Optional[str] = None
    defender_model: Optional[str] = None
