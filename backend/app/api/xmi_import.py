from fastapi import APIRouter, HTTPException, Request
from pymongo.errors import PyMongoError
from sqlalchemy.exc import SQLAlchemyError
from starlette.concurrency import run_in_threadpool

from app.api.auth import current_user_dependency
from app.api.projects import database_session
from app.db.dependencies import StorageSession, rollback_sql_session
from app.db.projects import create_project
from app.db.users import UserRecord
from app.domain.uml.models import DomainModel, ProjectDocument
from app.interoperability.xmi.importer import MAX_XMI_BYTES, XmiImportError, import_xmi

router = APIRouter(tags=["xmi"])


class ImportXmiResponse(DomainModel):
    document: ProjectDocument
    warnings: list[str]


def persist_import(data: bytes, user: UserRecord, session: StorageSession) -> ImportXmiResponse:
    try:
        result = import_xmi(data)
    except XmiImportError as error:
        raise HTTPException(422, detail={"code": error.code, "message": str(error)}) from error
    document = ProjectDocument(
        ownerId=user.id,
        metadata={"name": result.name, "importSource": "XMI 2.1"},
        umlModel=result.model,
    )
    try:
        saved = create_project(session, document)
    except (SQLAlchemyError, PyMongoError) as error:
        rollback_sql_session(session)
        raise HTTPException(
            503,
            detail={
                "code": "XMI_PERSISTENCE_UNAVAILABLE",
                "message": "Import storage is unavailable",
            },
        ) from error
    return ImportXmiResponse(document=saved, warnings=result.warnings)


@router.post("/projects/import/xmi", response_model=ImportXmiResponse, status_code=201)
async def import_project_xmi(
    request: Request,
    user: UserRecord = current_user_dependency,
    session: StorageSession = database_session,
) -> ImportXmiResponse:
    media_type = request.headers.get("content-type", "application/octet-stream").split(";")[0]
    if media_type not in {"application/xml", "text/xml", "application/octet-stream"}:
        raise HTTPException(415, detail={"code": "XMI_CONTENT_TYPE", "message": "Send an XML file"})
    data = bytearray()
    async for chunk in request.stream():
        if len(data) + len(chunk) > MAX_XMI_BYTES:
            raise HTTPException(413, detail={"code": "XMI_SIZE_LIMIT", "message": "Maximum 2 MiB"})
        data.extend(chunk)
    return await run_in_threadpool(persist_import, bytes(data), user, session)
