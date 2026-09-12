from fastapi import APIRouter, HTTPException
from sqlalchemy import text

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "backend"}


@router.get("/health/db")
def database_health() -> dict[str, str]:
    # Importación diferida: el health general no depende del driver PostgreSQL.
    from app.db.session import engine

    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
    except Exception as exc:
        raise HTTPException(status_code=503, detail="database unavailable") from exc
    return {"status": "ok", "database": "postgresql"}
