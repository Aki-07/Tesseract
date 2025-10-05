from pydantic import BaseModel
from typing import Optional, Dict, List
from datetime import datetime


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
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
