import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager

DB_PATH = "data/capsule_registry.db"
DB_URL = os.getenv("DB_URL", f"sqlite:///{DB_PATH}")
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
    echo=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_session():
    """Provides database session in a context manager."""

    @contextmanager
    def _session_scope():
        session = SessionLocal()
        try:
            yield session
            session.commit()
        except:
            session.rollback()
            raise
        finally:
            session.close()

    return _session_scope()


def init_db():
    """Creates tables if not exist."""
    from .models import Capsule

    Base.metadata.create_all(bind=engine)
    print("✅ Capsule table created (if not already)")
