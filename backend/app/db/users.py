from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, select
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.base import Base
from app.db.mongo_store import MongoStore


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def get_user_by_email(session: Session | MongoStore, email: str) -> UserRecord | None:
    if isinstance(session, MongoStore):
        return _mongo_user(session.get_user_by_email(email))
    return session.scalar(select(UserRecord).where(UserRecord.email == email))


def get_user_by_id(session: Session | MongoStore, user_id: UUID) -> UserRecord | None:
    if isinstance(session, MongoStore):
        return _mongo_user(session.get_user_by_id(user_id))
    return session.get(UserRecord, user_id)


def create_user(session: Session | MongoStore, email: str, password_hash: str) -> UserRecord:
    if isinstance(session, MongoStore):
        return _mongo_user(session.create_user(email, password_hash))
    now = datetime.now(UTC)
    user = UserRecord(email=email, password_hash=password_hash, created_at=now, updated_at=now)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def _mongo_user(data: dict | None) -> UserRecord | None:
    if data is None:
        return None
    return UserRecord(
        id=UUID(data["_id"]),
        email=data["email"],
        password_hash=data["password_hash"],
        created_at=datetime.fromisoformat(data["created_at"]),
        updated_at=datetime.fromisoformat(data["updated_at"]),
    )
