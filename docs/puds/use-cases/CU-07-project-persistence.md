# CU-07 - Persistir y recuperar proyectos

**Estado:** DONE

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

- Auth, ownership real, realtime, presencia, IA, XMI, generacion, Flutter y AWS.

## 6. Precondiciones

PostgreSQL, SQLAlchemy y Alembic estan configurados. El bridge temporal de CU-06 fue retirado en el Incremento 3.

## 7. Escenarios / flujo principal

1. El cliente crea un proyecto mediante `POST /projects`.
2. FastAPI genera un `ownerId` estructural temporal y guarda un `ProjectDocument` vacio.
3. El cliente lista proyectos con `GET /projects`.
4. El cliente recupera un documento completo con `GET /projects/{projectId}`.
5. La lectura reconstruye y valida `ProjectDocument` directamente desde PostgreSQL, sin crear `UmlCommandBus`.

## 8. Plan aprobado

CU-07 se ejecuto en tres incrementos, todos terminados y validados.

## 9. Incrementos

### Incremento 1 - Base persistente

**Objetivo:** almacenar y recuperar `ProjectDocument` sin romper el bridge de CU-06.

**Implementado:** tabla `projects`, conversiones validadas, dependencia SQLAlchemy por request, migracion Alembic y API de creacion/listado/lectura.

**Resultado real:** DONE. Validado contra PostgreSQL local y el gate final.

### Incremento 2 - Mutaciones persistentes

**Objetivo:** ejecutar comandos, Undo y Redo con lock por proyecto, CAS por revision e invalidacion de buses ante conflicto o error de persistencia.

**Implementado:** endpoints persistentes de command/undo/redo, lock process-local por proyecto, cache efimera de `UmlCommandBus`, CAS SQL por revision e invalidacion de cache ante conflicto o error de almacenamiento.

**Resultado real:** DONE. Validado contra PostgreSQL local y el gate final.

### Incremento 3 - Migrar editor y retirar bridge temporal

**Objetivo:** migrar el frontend a proyectos persistentes y retirar `/editor/sessions` solo despues de validar la UI.

**Implementado:** cliente HTTP, store Pinia y workspace migrados de sesiones a proyectos; listado/creacion/apertura de proyectos; `baseRevision` centralizada; recuperacion ante conflicto; retiro completo del bridge temporal.

**Resultado real:** DONE. Validado automaticamente, por API contra una instancia limpia y mediante prueba manual humana final de la UI.

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
- El editor Vue lista, crea y abre proyectos persistentes sin Vue Router.
- El store adjunta la revision actual en comandos, Undo y Redo, y reemplaza siempre la proyeccion con la respuesta autoritativa.
- `PROJECT_REVISION_CONFLICT` recarga el documento y reinicia los indicadores de historial; errores UML no provocan recarga.
- Se eliminaron `backend/app/api/editor.py`, sus pruebas y todas las referencias de frontend a sesiones temporales.

## 12. Archivos/componentes principales afectados

- `backend/app/db/projects.py`
- `backend/app/db/dependencies.py`
- `backend/app/api/projects.py`
- `backend/migrations/versions/20260920_01_create_projects.py`
- `backend/tests/db/test_project_persistence.py`
- `backend/tests/api/test_projects.py`
- `backend/tests/api/test_project_mutations.py`
- `frontend/src/features/editor/editor-api.ts`
- `frontend/src/features/editor/editor-store.ts`
- `frontend/src/features/editor/EditorWorkspace.vue`
- Pruebas frontend de API, store y App.

## 13. Pruebas automáticas

| Prueba/comando | Resultado | Evidencia/nota |
|---|---|---|
| `pytest` | 150 passed, 2 warnings | El bridge temporal fue retirado; conserva dominio, persistencia, CAS y Undo/Redo. |
| `python -m compileall app` | OK | Compilacion del backend sin errores. |
| `ruff check .` | OK | Sin hallazgos. |
| `alembic history --verbose` | OK | Revision `20260920_01` es head. |
| `alembic current` antes | `20260920_01 (head)` | PostgreSQL local ya tenia aplicada la revision al iniciar la validacion. |
| `alembic upgrade head` | OK, sin operaciones pendientes | No se aplicaron cambios adicionales. |
| `alembic current` despues | `20260920_01 (head)` | Estado confirmado tras upgrade. |
| `alembic check` | `No new upgrade operations detected.` | Metadata y esquema sincronizados. |
| `npm run typecheck` | OK | TypeScript sin errores. |
| `npm test` | 27 passed | Suite frontend aprobada. |
| `npm run build` | OK | Build frontend aprobado. |
| `scripts/check.ps1` | OK | Gate global aprobado. |

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

Validacion tecnica del Incremento 3 contra PostgreSQL local:

- se creo Proyecto A `5798db34-a970-4fcb-b8a1-a5c67a57725a`;
- cuatro comandos persistieron dos clases, una asociacion y layout de `Customer` en revision 4;
- consulta PostgreSQL confirmo tres elementos y layout `{x: 120, y: 80, width: 220, height: 160}`;
- una instancia FastAPI limpia recupero revision 4, las tres entidades y layout completo;
- Undo tras reinicio respondio `409 UNDO_NOT_AVAILABLE` como corresponde al historial no durable;
- un nuevo comando, Undo y Redo persistieron revisiones 5, 6 y 7 respectivamente.

Prueba manual humana final aprobada el 2026-09-21:

- frontend en `http://localhost:5173` y backend actual en `http://127.0.0.1:8000`;
- OpenAPI confirmo `GET/POST /projects`, `GET /projects/{project_id}`, `POST /projects/{project_id}/commands`, `POST /projects/{project_id}/undo` y `POST /projects/{project_id}/redo`;
- se crearon y abrieron proyectos, clases, atributos y relaciones; tambien se validaron movimiento de nodos/layout, auto-layout e inspector;
- Undo y Redo funcionaron antes y despues de reiniciar FastAPI;
- al reabrir el mismo proyecto tras el reinicio se conservaron clases, atributos, relaciones y layout; una operacion nueva posterior al reinicio y su Undo/Redo funcionaron correctamente;
- el 404 observado en una validacion anterior provenia de una instancia antigua de FastAPI en el puerto 8000, no del codigo actual. La instancia actual registro las cinco rutas esperadas.

## 15. Errores encontrados e iteraciones de corrección

- La columna SQL `metadata` no puede usar ese mismo atributo Python porque es reservado por SQLAlchemy; se usa `project_metadata` sin cambiar el esquema de base de datos.
- Las pruebas fuera de paquetes requieren basenames unicos para pytest; la prueba de persistencia usa `test_project_persistence.py`.

## 16. Benchmarks relacionados

No aplica.

## 17. Documentación actualizada

CU-07, arquitectura, decisiones, estado, handoff, contexto y testing.

## 18. Deuda técnica y riesgos restantes

- No hay base PostgreSQL de test aislada configurada; no se ejecutan pruebas de integracion destructivas contra `examen_sw1`.
- Undo/Redo no sobrevive al reinicio deliberadamente; solo se conserva dentro de la cache process-local de un bus activo.
- No hay deuda bloqueante de CU-07. Undo/Redo sigue siendo efimero por proceso; despues de reiniciar, las operaciones nuevas vuelven a crear historial para esa instancia.

## 19. Criterios de aceptación y evidencia

- [x] Una tabla `projects` conserva el documento sin duplicar UML relacionalmente.
- [x] Las lecturas validan y reconstruyen `ProjectDocument` desde columnas PostgreSQL.
- [x] `POST /projects` genera `ownerId` en backend y crea un documento vacio valido.
- [x] `GET /projects` devuelve resumen ordenado por actualizacion descendente.
- [x] Proyecto inexistente responde `404 PROJECT_NOT_FOUND`.
- [x] Migracion y endpoints integrados contra PostgreSQL local sin operaciones destructivas.
- [x] Command, Undo y Redo persisten el documento resultado del `UmlCommandBus`.
- [x] Lock local y CAS evitan que una mutacion obsoleta sobrescriba PostgreSQL.
- [x] Conflicto o error de persistencia invalida el bus cacheado.
- [x] Tras reinicio se recupera el documento, sin reconstruir historial Undo/Redo.
- [x] Frontend usa proyectos persistentes, revision autoritativa y respuesta del backend.
- [x] Bridge temporal de CU-06 retirado sin referencias residuales de codigo.
- [x] Prueba manual humana final: crear/abrir/editar proyecto desde UI y verificar recuperacion tras reinicio.

## 20. Estado final

DONE. Incremento 1 DONE. Incremento 2 DONE. Incremento 3 DONE. La prueba manual humana final fue aprobada.

## 21. Commit y push

Commits de implementacion: `11afae4`, `163c978` y `1871e2d`. El commit de cierre documental se registra al completar esta actualizacion. No se hizo push.
