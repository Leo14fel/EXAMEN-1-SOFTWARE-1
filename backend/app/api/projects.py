from datetime import datetime
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import Field, JsonValue
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.dependencies import get_db_session
from app.db.projects import ProjectRecord, create_project, get_project, list_projects
from app.domain.uml.models import DomainModel, ProjectDocument

router = APIRouter(prefix="/projects", tags=["projects"])
database_session = Depends(get_db_session)


class CreateProjectRequest(DomainModel):
    metadata: dict[str, JsonValue] = Field(default_factory=dict)


class ProjectSummary(DomainModel):
    id: UUID
    owner_id: UUID = Field(alias="ownerId")
    metadata: dict[str, JsonValue]
    revision: int
    created_at: datetime = Field(alias="createdAt")
    updated_at: datetime = Field(alias="updatedAt")


def _not_found() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail={"code": "PROJECT_NOT_FOUND", "message": "Project was not found"},
    )


def _summary(record: ProjectRecord) -> ProjectSummary:
    return ProjectSummary(
        id=record.id,
        ownerId=record.owner_id,
        metadata=record.project_metadata,
        revision=record.revision,
        createdAt=record.created_at,
        updatedAt=record.updated_at,
    )


@router.post("", response_model=ProjectDocument, status_code=status.HTTP_201_CREATED)
def create_persisted_project(
    request: CreateProjectRequest,
    session: Session = database_session,
) -> ProjectDocument:
    document = ProjectDocument(ownerId=uuid4(), metadata=request.metadata)
    try:
        return create_project(session, document)
    except SQLAlchemyError as error:
        session.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail={
                "code": "PROJECT_PERSISTENCE_UNAVAILABLE",
                "message": "Project storage is unavailable",
            },
        ) from error


@router.get("", response_model=list[ProjectSummary])
def list_persisted_projects(session: Session = database_session) -> list[ProjectSummary]:
    return [_summary(record) for record in list_projects(session)]


@router.get("/{project_id}", response_model=ProjectDocument)
def get_persisted_project(
    project_id: UUID, session: Session = database_session
) -> ProjectDocument:
    document = get_project(session, project_id)
    if document is None:
        raise _not_found()
    return document
