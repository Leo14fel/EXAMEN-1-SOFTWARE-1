from enum import StrEnum
from uuid import UUID

from sqlalchemy import Enum, ForeignKey, select
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.base import Base
from app.db.mongo_store import MongoStore


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
    session: Session | MongoStore, project_id: UUID, user_id: UUID
) -> ProjectMembershipRecord | None:
    if isinstance(session, MongoStore):
        role = session.get_membership(project_id, user_id)
        return (
            None
            if role is None
            else ProjectMembershipRecord(
                project_id=project_id, user_id=user_id, role=ProjectRole(role)
            )
        )
    return session.get(ProjectMembershipRecord, (project_id, user_id))


def list_memberships(
    session: Session | MongoStore, project_id: UUID
) -> list[ProjectMembershipRecord]:
    if isinstance(session, MongoStore):
        return [
            ProjectMembershipRecord(
                project_id=project_id, user_id=UUID(user_id), role=ProjectRole(role)
            )
            for user_id, role in sorted(session.list_memberships(project_id).items())
        ]
    return session.scalars(
        select(ProjectMembershipRecord)
        .where(ProjectMembershipRecord.project_id == project_id)
        .order_by(ProjectMembershipRecord.user_id)
    ).all()


def create_membership(session: Session | MongoStore, membership: ProjectMembershipRecord) -> None:
    if isinstance(session, MongoStore):
        session.add_membership(membership.project_id, membership.user_id, membership.role.value)
        return
    session.add(membership)
    session.commit()
    session.refresh(membership)


def update_membership(session: Session | MongoStore, membership: ProjectMembershipRecord) -> bool:
    if isinstance(session, MongoStore):
        return session.update_membership(
            membership.project_id, membership.user_id, membership.role.value
        )
    session.commit()
    session.refresh(membership)
    return True


def delete_membership(session: Session | MongoStore, membership: ProjectMembershipRecord) -> bool:
    if isinstance(session, MongoStore):
        return session.delete_membership(membership.project_id, membership.user_id)
    session.delete(membership)
    session.commit()
    return True
