from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from app.api.auth import router as auth_router
from app.api.group_sessions import router as group_sessions_router
from app.api.health import router as health_router
from app.api.invitations import router as invitations_router
from app.api.projects import router as projects_router
from app.api.realtime import router as realtime_router
from app.api.xmi_import import router as xmi_import_router
from app.core.config import settings
from app.db.mongo_projects import ProjectTooLargeError
from app.db.mongo_store import close_mongo_store


@asynccontextmanager
async def lifespan(_: FastAPI):
    try:
        yield
    finally:
        close_mongo_store()


app = FastAPI(title=settings.app_name, version="0.0.0", lifespan=lifespan)


@app.exception_handler(PyMongoError)
async def mongo_storage_error(_: Request, __: PyMongoError) -> JSONResponse:
    return JSONResponse(
        status_code=503,
        content={
            "detail": {
                "code": "PERSISTENCE_UNAVAILABLE",
                "message": "Storage is unavailable",
            }
        },
    )


@app.exception_handler(ProjectTooLargeError)
async def mongo_project_too_large(_: Request, __: ProjectTooLargeError) -> JSONResponse:
    return JSONResponse(
        status_code=413,
        content={
            "detail": {
                "code": "PROJECT_DOCUMENT_TOO_LARGE",
                "message": "Project exceeds storage limit",
            }
        },
    )


app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_router)
app.include_router(auth_router)
app.include_router(projects_router)
app.include_router(realtime_router)
app.include_router(group_sessions_router)
app.include_router(xmi_import_router)
app.include_router(invitations_router)
