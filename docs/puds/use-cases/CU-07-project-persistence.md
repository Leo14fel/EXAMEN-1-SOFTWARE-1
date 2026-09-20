# CU-07 - Persistir y recuperar proyectos

**Estado:** IN_PROGRESS

## 1. Objetivo

Persistir y recuperar `ProjectDocument` con PostgreSQL sin duplicar el modelo UML ni convertir la persistencia en una fuente de verdad distinta del documento canonico.

## 2. Actor(es)

Usuario de modelado UML.

## 3. Dependencias

CU-01, CU-04, CU-05 y CU-06 terminados.

## 4. Referencias a product.md

Secciones 3, 6, 10, 11, 20 y 34.

## 5. Alcance

### Incluye

- Persistencia PostgreSQL de `ProjectDocument`.
- Creacion, listado y lectura de proyectos persistidos.
- Primera migracion Alembic de dominio.

### Fuera de alcance

- Mutaciones persistentes, revision optimista, locks por proyecto y cache de buses.
- Undo/Redo persistente.
- Auth, ownership real, realtime, presencia, IA, XMI, generacion, Flutter y AWS.

## 6. Precondiciones

CU-06 mantiene `/editor/sessions` como bridge temporal process-local. PostgreSQL, SQLAlchemy y Alembic ya estan configurados.

## 7. Escenarios / flujo principal

1. El cliente crea un proyecto mediante `POST /projects`.
2. FastAPI genera un `ownerId` estructural temporal y guarda un `ProjectDocument` vacio.
3. El cliente lista proyectos con `GET /projects`.
4. El cliente recupera un documento completo con `GET /projects/{projectId}`.
5. La lectura reconstruye y valida `ProjectDocument` directamente desde PostgreSQL, sin crear `UmlCommandBus`.

## 8. Plan aprobado

CU-07 se ejecuta en tres incrementos. Este documento registra los Incrementos 1 y 2.

## 9. Incrementos

### Incremento 1 - Base persistente

**Objetivo:** almacenar y recuperar `ProjectDocument` sin romper el bridge de CU-06.

**Implementado:** tabla `projects`, conversiones validadas, dependencia SQLAlchemy por request, migracion Alembic y API de creacion/listado/lectura.

**Resultado real:** VALIDADO contra PostgreSQL local. CU-07 permanece IN_PROGRESS.

### Incremento 2 - Mutaciones persistentes

**Objetivo:** ejecutar comandos, Undo y Redo con lock por proyecto, CAS por revision e invalidacion de buses ante conflicto o error de persistencia.

**Implementado:** endpoints persistentes de command/undo/redo, lock process-local por proyecto, cache efimera de `UmlCommandBus`, CAS SQL por revision e invalidacion de cache ante conflicto o error de almacenamiento.

**Resultado real:** VALIDADO contra PostgreSQL local.

### Incremento 3 - Migrar editor y retirar bridge temporal

**Objetivo:** migrar el frontend a proyectos persistentes y retirar `/editor/sessions` solo despues de validar la UI.

**Estado:** NEXT.

## 10. Diseño y decisiones utilizadas

La tabla unica `projects` contiene `id`, `owner_id`, `metadata`, `revision`, `created_at`, `updated_at`, `uml_model` y `diagram_layout`. Los UUID usan `UUID`, los timestamps `TIMESTAMPTZ` y los contenidos estructurados `JSONB`.

`JSONB` conserva la representacion JSON-safe ya definida por Pydantic y evita duplicar clases, atributos, operaciones, parametros, relaciones y layout en tablas relacionales. `uml_model` y `diagram_layout` se almacenan en columnas separadas para mantener la separacion entre semantica UML y presentacion visual.

Toda lectura reconstruye el payload mediante `ProjectDocument.model_validate(...)`; nunca retorna JSON de base de datos como sustituto del dominio. `ownerId` no llega desde el request: FastAPI genera un UUID temporal hasta CU-08.

Las mutaciones adquieren un lock por `projectId`, recargan el documento persistido y comparan `baseRevision` antes de usar un `UmlCommandBus`. La cache process-local de buses conserva solamente snapshots de Undo/Redo durante la vida del proceso; no es fuente de verdad ni se persiste. El documento producido por el bus se actualiza mediante `UPDATE projects WHERE id = :id AND revision = :base_revision`. Si el CAS falla, o si una operacion de base de datos/commit falla despues de mutar el bus, se hace rollback y se descarta el bus cacheado. La siguiente request reconstruye desde PostgreSQL.

## 11. Implementación realizada

- `ProjectRecord` mapea la tabla `projects`. El atributo Python para la columna SQL `metadata` es `project_metadata`, porque `DeclarativeBase.metadata` esta reservado.
- `project_record_from_document` y `project_document_from_record` convierten entre ORM y dominio.
- `get_db_session` crea y cierra una sesion SQLAlchemy por request.
- Se implementaron `POST /projects`, `GET /projects` y `GET /projects/{projectId}`.
- El listado devuelve resumen ordenado por `updatedAt` descendente.
- `backend/migrations/env.py` importa el modelo ORM antes de evaluar `Base.metadata`.
- Se implementaron `POST /projects/{projectId}/commands`, `/undo` y `/redo`.
- Las mutaciones usan lock por proyecto, CAS por revision y cache efimera de buses.

## 12. Archivos/componentes principales afectados

- `backend/app/db/projects.py`
- `backend/app/db/dependencies.py`
- `backend/app/api/projects.py`
- `backend/migrations/versions/20260920_01_create_projects.py`
- `backend/tests/db/test_project_persistence.py`
- `backend/tests/api/test_projects.py`
- `backend/tests/api/test_project_mutations.py`

## 13. Pruebas automáticas

| Prueba/comando | Resultado | Evidencia/nota |
|---|---|---|
| `pytest` | 156 passed, 2 warnings externos | Incluye CAS, locks, cache, Undo/Redo y regresion de `/editor/sessions`. |
| `ruff check .` | OK | Sin hallazgos. |
| `alembic history --verbose` | OK | Revision `20260920_01` es head. |
| `alembic current` antes | `20260920_01 (head)` | PostgreSQL local ya tenia aplicada la revision al iniciar la validacion. |
| `alembic upgrade head` | OK, sin operaciones pendientes | No se aplicaron cambios adicionales. |
| `alembic current` despues | `20260920_01 (head)` | Estado confirmado tras upgrade. |
| `alembic check` | `No new upgrade operations detected.` | Metadata y esquema sincronizados. |
| `scripts/check.ps1` | OK | Backend 156 passed, frontend 22 passed, typecheck y build verdes. |

Las pruebas de persistencia son unitarias y no destruyen ni modifican `examen_sw1`. El repositorio no tiene configurada una base PostgreSQL de test aislada; la integracion real se valido manualmente contra la base local sin operaciones destructivas.

## 14. Pruebas manuales

Validacion real contra PostgreSQL local el 2026-09-20:

- auditoria de migracion: `upgrade()` solo crea `projects` con las ocho columnas aprobadas; no elimina, trunca ni modifica objetos existentes;
- esquema observado: `alembic_version` y `projects`; `projects` tiene PK `id`, UUID para `id` y `owner_id`, JSONB para `metadata`, `uml_model` y `diagram_layout`, INTEGER para `revision` y timestamps con timezone;
- antes de HTTP, `projects` no tenia filas;
- `GET /health` respondio `200 {"status":"ok","service":"backend"}` y `GET /health/db` respondio `200 {"status":"ok","database":"postgresql"}`;
- `POST /projects` creo `00e140fa-5deb-4f5c-958a-093e0ee215bf` con owner temporal `9d42b5fa-fec0-409f-85e5-0f966903718c`, revision 0, metadata `Proyecto persistente CU-07`, modelo y layout vacios;
- `GET /projects` devolvio el resumen creado en orden descendente de actualizacion;
- `GET /projects/{id}` devolvio el `ProjectDocument` completo y validado;
- consulta directa PostgreSQL confirmo la fila, owner, revision, metadata, JSONB vacios y timestamps;
- una instancia FastAPI limpia del mismo backend recupero el documento identico desde PostgreSQL y fue detenida despues de la prueba; el listener existente en 8000 no tenia un PID atribuible de forma segura para reiniciarlo sin riesgo de afectar un proceso externo;
- `POST /editor/sessions` respondio 200 con una sesion temporal valida, sin afectar el proyecto persistido.

Validacion real del Incremento 2 contra PostgreSQL local:

- se creo `b51a2c2b-0976-4cf0-98da-935d1a3d64ac`;
- command con `baseRevision: 0` agrego `Customer`, devolvio revision 1 y `canUndo: true`; PostgreSQL confirmo el JSONB y la revision;
- Undo con revision 1 devolvio revision 2 sin elementos y `canRedo: true`;
- Redo con revision 2 devolvio revision 3 y restauro `Customer`;
- despues de reiniciar una instancia limpia de FastAPI, GET recupero el documento de revision 3, pero Undo con la misma revision respondio `409 UNDO_NOT_AVAILABLE`, confirmando historial no durable;
- un nuevo comando creo `Order` en revision 4 con `canUndo: true`; Undo en revision 4 persistio revision 5 y conservo solo `Customer`;
- un comando con `baseRevision: 4` respondio `409 PROJECT_REVISION_CONFLICT`; PostgreSQL conservo revision 5 y el contenido autoritativo.

## 15. Errores encontrados e iteraciones de corrección

- La columna SQL `metadata` no puede usar ese mismo atributo Python porque es reservado por SQLAlchemy; se usa `project_metadata` sin cambiar el esquema de base de datos.
- Las pruebas fuera de paquetes requieren basenames unicos para pytest; la prueba de persistencia usa `test_project_persistence.py`.

## 16. Benchmarks relacionados

No aplica.

## 17. Documentación actualizada

CU-07, arquitectura, decisiones, estado, handoff, contexto y testing.

## 18. Deuda técnica y riesgos restantes

- No hay base PostgreSQL de test aislada configurada; no se ejecutan pruebas de integracion destructivas contra `examen_sw1`.
- `/editor/sessions` permanece intencionalmente hasta el Incremento 3.
- Undo/Redo no sobrevive al reinicio deliberadamente; solo se conserva dentro de la cache process-local de un bus activo.
- El frontend aun usa `sessionId` y no consume las rutas persistentes hasta el Incremento 3.

## 19. Criterios de aceptación y evidencia

- [x] Una tabla `projects` conserva el documento sin duplicar UML relacionalmente.
- [x] Las lecturas validan y reconstruyen `ProjectDocument` desde columnas PostgreSQL.
- [x] `POST /projects` genera `ownerId` en backend y crea un documento vacio valido.
- [x] `GET /projects` devuelve resumen ordenado por actualizacion descendente.
- [x] Proyecto inexistente responde `404 PROJECT_NOT_FOUND`.
- [x] `/editor/sessions` conserva su suite existente verde.
- [x] Migracion y endpoints integrados contra PostgreSQL local sin operaciones destructivas.
- [x] Command, Undo y Redo persisten el documento resultado del `UmlCommandBus`.
- [x] Lock local y CAS evitan que una mutacion obsoleta sobrescriba PostgreSQL.
- [x] Conflicto o error de persistencia invalida el bus cacheado.
- [x] Tras reinicio se recupera el documento, sin reconstruir historial Undo/Redo.

## 20. Estado final

IN_PROGRESS. Incrementos 1 y 2 implementados y validados contra PostgreSQL local. Incremento 3 es el siguiente paso.

## 21. Commit y push

No se ejecutaron commit ni push.
