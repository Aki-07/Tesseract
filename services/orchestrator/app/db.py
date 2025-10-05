from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from app.models import Capsule
import os

DB_URL = os.getenv("DB_URL", "sqlite:///./capsule_registry.db")

engine = create_engine(
    DB_URL,
    connect_args={"check_same_thread": False} if DB_URL.startswith("sqlite") else {},
    echo=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


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
    from app.models import Capsule

    Base.metadata.create_all(bind=engine)
