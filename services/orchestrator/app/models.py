import uuid, json, enum
from sqlalchemy import Column, String, Boolean, DateTime, Enum, Text
from sqlalchemy.sql import func
from app.db import Base


class Role(str, enum.Enum):
    attack = "attack"
    defense = "defense"


class Capsule(Base):
    __tablename__ = "capsules"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String, nullable=False)
    version = Column(String, nullable=False, default="v1")
    role = Column(Enum(Role), nullable=False)

    image = Column(String, nullable=False)  # docker image (for spawning)
    entrypoint = Column(String, nullable=True)  # optional command
    env = Column(Text, nullable=True)  # store as JSON string
    config = Column(Text, nullable=True)

    tags = Column(Text, nullable=True)  # ["fast","guard","policy"]
    enabled = Column(Boolean, default=True)
    owner = Column(String, nullable=True)
    description = Column(String, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(
        DateTime(timezone=True), onupdate=func.now(), server_default=func.now()
    )

    def json_safe(self):
        """Helper to deserialize stored JSON fields."""
        import json

        return {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "role": self.role.value,
            "image": self.image,
            "entrypoint": self.entrypoint,
            "env": json.loads(self.env) if self.env else {},
            "config": json.loads(self.config) if self.config else {},
            "tags": json.loads(self.tags) if self.tags else [],
            "enabled": self.enabled,
            "owner": self.owner,
            "description": self.description,
            "created_at": str(self.created_at),
            "updated_at": str(self.updated_at),
        }
