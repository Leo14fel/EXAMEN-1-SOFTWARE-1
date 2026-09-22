from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, String, select
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.base import Base


class UserRecord(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True, default=uuid4)
    email: Mapped[str] = mapped_column(String(320), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(512), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


def get_user_by_email(session: Session, email: str) -> UserRecord | None:
    return session.scalar(select(UserRecord).where(UserRecord.email == email))


def get_user_by_id(session: Session, user_id: UUID) -> UserRecord | None:
    return session.get(UserRecord, user_id)


def create_user(session: Session, email: str, password_hash: str) -> UserRecord:
    now = datetime.now(UTC)
    user = UserRecord(email=email, password_hash=password_hash, created_at=now, updated_at=now)
    session.add(user)
    session.commit()
    session.refresh(user)
    return user
