from sqlalchemy import create_engine, Column, Integer, Float, String, JSON, ForeignKey
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_URL = "sqlite:///data.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Candidate(Base):
    __tablename__ = "candidates"
    id = Column(Integer, primary_key=True, index=True)
    rank = Column(Integer)
    alpha = Column(Float)
    status = Column(String, default="pending")
    style_score = Column(Float, nullable=True)
    toxicity_score = Column(Float, nullable=True)
    latency_ms = Column(Float, nullable=True)
    cerebras_job_id = Column(String, nullable=True)

class Capsule(Base):
    __tablename__ = "capsules"
    id = Column(Integer, primary_key=True, index=True)
    candidate_id = Column(Integer, ForeignKey("candidates.id"))
    manifest = Column(JSON)
    docker_image = Column(String)

def init_db():
    Base.metadata.create_all(bind=engine)
