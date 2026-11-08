"""Run explicitly with python -m tests.manual.qa_server; never a production fallback."""

import os
import secrets
from contextlib import asynccontextmanager
from uuid import UUID

import mongomock
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

QA_PASSWORD = "Prueba1234!"
QA_EMAILS = ("owner@prueba.local", "editor@prueba.local", "viewer@prueba.local")


def create_qa_app() -> FastAPI:
    # Delayed imports let the CLI set an ephemeral JWT key before settings load.
    from app.api import (
        ai,
        auth,
        group_sessions,
        invitations,
        projects,
        realtime,
        relational,
        xmi_import,
    )
    from app.core.config import settings
    from app.core.security import hash_password
    from app.db.dependencies import get_db_session
    from app.db.mongo_store import MongoStore
    from app.domain.uml.models import (
        CanonicalUmlModel,
        DiagramLayout,
        DiagramNodeLayout,
        ProjectDocument,
        UmlAssociation,
        UmlAttribute,
        UmlClass,
        UmlMultiplicity,
    )
    from app.main import app as production_app

    connection = mongomock.MongoClient(tz_aware=True)
    store = MongoStore(connection["manual_qa_temporary"])
    store.ensure_indexes()
    users = [store.create_user(email, hash_password(QA_PASSWORD)) for email in QA_EMAILS]
    name = UmlAttribute(name="nombre", type="String", visibility="private")
    email = UmlAttribute(name="correo", type="String", visibility="private")
    customer = UmlClass(name="Cliente", visibility="public", attributes=[name, email])
    order = UmlClass(
        name="Pedido",
        visibility="public",
        attributes=[
            UmlAttribute(name="total", type="Decimal", visibility="private"),
            UmlAttribute(name="fecha", type="Date", visibility="private"),
        ],
    )
    relation = UmlAssociation(
        sourceId=customer.id,
        targetId=order.id,
        sourceMultiplicity=UmlMultiplicity(lower=1, upper=1),
        targetMultiplicity=UmlMultiplicity(lower=0, upper="*"),
    )
    document = ProjectDocument(
        ownerId=users[0]["_id"],
        metadata={
            "name": "Prueba local - Cliente y Pedido",
            "generation": {
                "attributes": {str(name.id): {"required": True}, str(email.id): {"unique": True}}
            },
        },
        umlModel=CanonicalUmlModel(elements=[customer, order, relation]),
        diagramLayout=DiagramLayout(
            nodes={
                customer.id: DiagramNodeLayout(x=80, y=100, width=280, height=180),
                order.id: DiagramNodeLayout(x=460, y=100, width=280, height=180),
            }
        ),
    )
    store.create_project(document)
    store.add_membership(document.id, UUID(users[1]["_id"]), "EDITOR")
    store.add_membership(document.id, UUID(users[2]["_id"]), "VIEWER")

    @asynccontextmanager
    async def lifespan(_: FastAPI):
        try:
            yield
        finally:
            connection.close()

    app = FastAPI(
        title="Prueba local temporal - no Atlas",
        lifespan=lifespan,
        exception_handlers=production_app.exception_handlers,
    )
    app.state.qa_store = store
    app.state.qa_project_id = document.id
    app.dependency_overrides[get_db_session] = lambda: store
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    for router in (
        auth.router,
        ai.router,
        projects.router,
        realtime.router,
        group_sessions.router,
        invitations.router,
        xmi_import.router,
        relational.router,
    ):
        app.include_router(router)

    @app.get("/health")
    def health() -> dict:
        return {"status": "ok", "service": "manual-qa", "temporary": True}

    @app.get("/health/db")
    def health_db() -> dict:
        return {"status": "ok", "database": "mongomock", "temporary": True, "atlas": False}

    return app


if __name__ == "__main__":
    import uvicorn

    # Process-local only: never modify .env, production settings or real data.
    os.environ["JWT_SECRET_KEY"] = secrets.token_urlsafe(64)
    os.environ["FRONTEND_ORIGIN"] = "http://localhost:5175"
    uvicorn.run(create_qa_app(), host="127.0.0.1", port=8001, log_level="warning")
