from uuid import UUID

from fastapi import APIRouter
from pydantic import Field, ValidationError

from app.api.auth import current_user_dependency
from app.api.projects import _project_access, database_session
from app.db.dependencies import StorageSession
from app.db.users import UserRecord
from app.domain.relational.mapper import map_relational
from app.domain.relational.models import GenerationProfile, MappingDiagnostic, MappingResult

router = APIRouter(tags=["relational"])


class RelationalPreviewResponse(MappingResult):
    project_id: UUID = Field(alias="projectId")
    source_revision: int = Field(alias="sourceRevision")


@router.get("/projects/{project_id}/relational-model", response_model=RelationalPreviewResponse)
def preview_relational_model(
    project_id: UUID,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> RelationalPreviewResponse:
    document = _project_access(session, project_id, user).document
    try:
        profile = GenerationProfile.model_validate(document.metadata.get("generation", {}))
    except ValidationError:
        result = MappingResult(
            model=None,
            diagnostics=[
                MappingDiagnostic(
                    severity="error",
                    code="GENERATION_PROFILE_INVALID",
                    message="Los metadatos de generación no tienen un formato válido.",
                )
            ],
        )
    else:
        result = map_relational(document.uml_model, profile)
    return RelationalPreviewResponse(
        projectId=project_id, sourceRevision=document.revision, **result.model_dump()
    )
