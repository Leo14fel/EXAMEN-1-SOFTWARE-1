from collections.abc import Generator

from fastapi import HTTPException
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.mongo_store import MongoStore, get_mongo_store

StorageSession = Session | MongoStore


def get_db_session() -> Generator[StorageSession]:
    if settings.persistence_backend == "mongodb":
        try:
            store = get_mongo_store()
        except ValidationError as error:
            raise HTTPException(
                status_code=503, detail="storage configuration unavailable"
            ) from error
        yield store
        return
    from app.db.session import SessionLocal

    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def commit_sql_session(session: StorageSession) -> None:
    """Mongo adapter methods persist atomically; only the legacy SQL path has a UoW."""
    if not isinstance(session, MongoStore):
        session.commit()


def rollback_sql_session(session: StorageSession) -> None:
    if not isinstance(session, MongoStore):
        session.rollback()
