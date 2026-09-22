from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, select
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.base import Base


class ProjectRole(StrEnum):
    EDITOR = "EDITOR"
    VIEWER = "VIEWER"


class ProjectMembershipRecord(Base):
    __tablename__ = "project_memberships"

    project_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("projects.id", ondelete="CASCADE"),
        primary_key=True,
    )
    user_id: Mapped[UUID] = mapped_column(
        PostgreSQLUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
        index=True,
    )
    role: Mapped[ProjectRole] = mapped_column(
        Enum(ProjectRole, name="project_membership_role"), nullable=False
    )


def get_membership(
    session: Session, project_id: UUID, user_id: UUID
) -> ProjectMembershipRecord | None:
    return session.get(ProjectMembershipRecord, (project_id, user_id))


def list_memberships(session: Session, project_id: UUID) -> list[ProjectMembershipRecord]:
    return session.scalars(
        select(ProjectMembershipRecord)
        .where(ProjectMembershipRecord.project_id == project_id)
        .order_by(ProjectMembershipRecord.user_id)
    ).all()
