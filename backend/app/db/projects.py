from collections.abc import Sequence
from datetime import datetime
from typing import Any
from uuid import UUID

from sqlalchemy import DateTime, Integer, or_, select, update
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PostgreSQLUUID
from sqlalchemy.orm import Mapped, Session, mapped_column

from app.db.base import Base
from app.domain.uml.models import ProjectDocument


class ProjectRecord(Base):
    __tablename__ = "projects"

    id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), primary_key=True)
    owner_id: Mapped[UUID] = mapped_column(PostgreSQLUUID(as_uuid=True), nullable=False, index=True)
    # DeclarativeBase reserves `metadata`, so the Python attribute uses a distinct name.
    project_metadata: Mapped[dict[str, Any]] = mapped_column("metadata", JSONB, nullable=False)
    revision: Mapped[int] = mapped_column(Integer, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    uml_model: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    diagram_layout: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)


def project_record_from_document(document: ProjectDocument) -> ProjectRecord:
    data = document.model_dump(mode="json", by_alias=True)
    return ProjectRecord(
        id=document.id,
        owner_id=document.owner_id,
        project_metadata=data["metadata"],
        revision=document.revision,
        created_at=document.created_at,
        updated_at=document.updated_at,
        uml_model=data["umlModel"],
        diagram_layout=data["diagramLayout"],
    )


def project_document_from_record(record: ProjectRecord) -> ProjectDocument:
    return ProjectDocument.model_validate(
        {
            "id": record.id,
            "ownerId": record.owner_id,
            "metadata": record.project_metadata,
            "revision": record.revision,
            "createdAt": record.created_at,
            "updatedAt": record.updated_at,
            "umlModel": record.uml_model,
            "diagramLayout": record.diagram_layout,
        }
    )


def create_project(session: Session, document: ProjectDocument) -> ProjectDocument:
    record = project_record_from_document(document)
    session.add(record)
    session.commit()
    session.refresh(record)
    return project_document_from_record(record)


def get_project(session: Session, project_id: UUID) -> ProjectDocument | None:
    record = session.get(ProjectRecord, project_id)
    return None if record is None else project_document_from_record(record)


def list_projects(session: Session, owner_id: UUID) -> Sequence[ProjectRecord]:
    from app.db.memberships import ProjectMembershipRecord

    statement = (
        select(ProjectRecord)
        .outerjoin(
            ProjectMembershipRecord,
            ProjectMembershipRecord.project_id == ProjectRecord.id,
        )
        .where(
            or_(
                ProjectRecord.owner_id == owner_id,
                ProjectMembershipRecord.user_id == owner_id,
            )
        )
        .order_by(ProjectRecord.updated_at.desc())
    )
    return session.scalars(statement).all()


def update_project_if_revision(
    session: Session, document: ProjectDocument, base_revision: int
) -> bool:
    data = document.model_dump(mode="json", by_alias=True)
    result = session.execute(
        update(ProjectRecord)
        .where(ProjectRecord.id == document.id, ProjectRecord.revision == base_revision)
        .values(
            project_metadata=data["metadata"],
            revision=document.revision,
            created_at=document.created_at,
            updated_at=document.updated_at,
            uml_model=data["umlModel"],
            diagram_layout=data["diagramLayout"],
        )
    )
    return result.rowcount == 1
