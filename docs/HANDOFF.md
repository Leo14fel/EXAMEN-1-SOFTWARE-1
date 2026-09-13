# Handoff

## Último punto estable

CU-00, CU-01 y CU-02 cerrados. El stack instalado es Vue 3 + TypeScript + Vite + Vuetify y Python + FastAPI + SQLAlchemy + Alembic. La evidencia de CU-02 vive en `puds/use-cases/CU-02-uml-classes-members.md`.

## Próximo paso exacto

CU-03 es NEXT / NOT_STARTED; preparar y aprobar su plan sin iniciar su implementacion todavia.

## Motivo de la reorganizacion

PUDS es la unica fuente de roadmap. El orden ahora garantiza validacion antes del Command Bus y Command Bus antes del canvas mutable. CU-09 administra membresías e invitaciones antes de CU-10 realtime; AWS queda en CU-23 y la aceptacion integral del MVP en CU-24.

## Dominio actual

`ProjectDocument` contiene UUID, metadata JSON-safe, ownerId estructural, revision, timestamps UTC, `CanonicalUmlModel` y `DiagramLayout`. El modelo canonico mantiene clases, atributos, operaciones y parametros; el layout solo posiciones y dimensiones por UUID. No hay relaciones, persistencia, API ni Command Bus.

## PostgreSQL actual

Desarrollo validado: PostgreSQL local de Windows en `localhost:5432`, base `examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Arranque y checks

```powershell
.\scripts\setup.ps1
.\scripts\dev-backend.ps1
.\scripts\dev-frontend.ps1
.\scripts\check.ps1
```

El gate base sin infraestructura externa ejecuta `backend: pytest`, `python -m compileall app`, `ruff check .`, `pip check`; y `frontend: npm run typecheck`, `npm test`, `npm run build`. `alembic check` y `/health/db` son checks de integración con PostgreSQL separados.

## No hacer todavía

- no implementar Flutter;
- no implementar AWS;
- no instalar modelos de IA;
- no crear el generador Spring Boot;
- no diseñar contratos HTTP definitivos sin el CU correspondiente;
- no empezar varios CU en paralelo.
