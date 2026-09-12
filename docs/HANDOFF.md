# Handoff

## Último punto estable

CU-00 cerrado. El stack instalado es Vue 3 + TypeScript + Vite + Vuetify y Python + FastAPI + SQLAlchemy + Alembic. La evidencia vive en `puds/use-cases/CU-00-project-foundation.md`.

## Próximo paso exacto

Preparar y aprobar el plan de CU-01; no implementar CU-01 hasta esa aprobacion.

## PostgreSQL actual

Desarrollo validado: PostgreSQL local de Windows en `localhost:5432`, base `examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Arranque y checks

```powershell
.\scripts\setup.ps1
.\scripts\dev-backend.ps1
.\scripts\dev-frontend.ps1
.\scripts\check.ps1
```

Checks individuales: `backend: pytest`, `python -m compileall app`, `ruff check .`, `pip check`, `alembic check`; `frontend: npm run typecheck`, `npm test`, `npm run build`.

## No hacer todavía

- no implementar Flutter;
- no implementar AWS;
- no instalar modelos de IA;
- no crear el generador Spring Boot;
- no diseñar contratos HTTP definitivos sin el CU correspondiente;
- no empezar varios CU en paralelo.
