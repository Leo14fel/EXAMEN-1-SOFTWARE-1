# Handoff

## Ultimo punto estable

CU-00 a CU-06 estan cerrados. El stack instalado es Vue 3 + TypeScript + Vite + Vuetify y Python + FastAPI + SQLAlchemy + Alembic. La evidencia de CU-06 vive en `docs/puds/use-cases/CU-06-uml-canvas.md`.

## Proximo paso exacto

CU-07 esta IN_PROGRESS. Los Incrementos 1 y 2 agregan `projects`, migracion Alembic, API de lectura y mutaciones persistentes con lock por proyecto, CAS por revision e invalidacion de buses. El Incremento 3 debe migrar el frontend y retirar el bridge temporal.

## Restriccion temporal del editor CU-06

El frontend no ejecuta ni replica el Command Bus. `frontend/src/features/editor/` contiene contratos TypeScript, cliente HTTP, store Pinia y la proyeccion Vue Flow.

FastAPI mantiene un `UmlCommandBus` temporal por `sessionId` bajo `/editor/sessions`. Este bridge es process-local, esta acotado a 64 sesiones con eviction LRU, serializa lecturas y mutaciones con un lock por sesion y se soporta solamente con un worker de FastAPI. Reiniciar el backend elimina las sesiones. CU-07 reemplazara esta limitacion con persistencia/recuperacion real.

## Dominio actual

`ProjectDocument` contiene UUID, metadata JSON-safe, ownerId estructural, revision, timestamps UTC, `CanonicalUmlModel` y `DiagramLayout`. El modelo canonico mantiene clases y relaciones; association usa extremos neutrales, aggregation/composition van de todo a parte y generalization de hija a padre. Las multiplicidades son estructuradas, los UUID son globalmente unicos y el layout solo conserva posiciones y dimensiones de clases.

Toda mutacion UML recorre `UmlCommand -> UmlCommandBus -> execute_uml_command -> ProjectDocument`; UI, canvas, IA y XMI no modifican el documento directamente. Undo/Redo usa snapshots completos, conserva hasta 100 estados y mantiene revision/`updatedAt` monotonos.

## Editor UML cerrado en CU-06

El editor permite crear/editar/eliminar clases, atributos, operaciones, parametros y relaciones; mover nodos; Undo/Redo; auto-layout `d3-dag`; seleccion e inspector. Los borradores del inspector no se reemplazan por revisiones externas mientras existan cambios sin guardar.

## PostgreSQL actual

Desarrollo validado: PostgreSQL local de Windows en `localhost:5432`, base `examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Arranque y checks

```powershell
.\scripts\setup.ps1
.\scripts\dev-backend.ps1
.\scripts\dev-frontend.ps1
.\scripts\check.ps1
```

El gate base sin infraestructura externa ejecuta `backend: pytest`, `python -m compileall app`, `ruff check .`, `pip check`; y `frontend: npm run typecheck`, `npm test`, `npm run build`. `alembic check` y `/health/db` son checks de integracion con PostgreSQL separados.

## Evidencia CU-06 tras review del PR

- backend: 139 tests passed, 2 warnings externos;
- frontend: 22 tests passed en 9 archivos;
- typecheck/build/gate: OK;
- prueba manual de canvas, drag, Undo/Redo, auto-layout y preservacion de borradores: OK.

## No hacer todavia

- no implementar persistencia fuera de CU-07;
- no implementar auth antes de CU-08;
- no implementar realtime/presencia antes de sus CUs;
- no implementar Flutter, AWS, IA, XMI o generadores antes del CU correspondiente;
- no empezar varios CU en paralelo.
