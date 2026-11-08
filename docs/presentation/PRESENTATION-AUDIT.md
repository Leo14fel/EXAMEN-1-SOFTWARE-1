# Auditoria tecnica para presentacion

**Fecha de auditoria:** 2026-09-28. **Regla de lectura:** el codigo y Git prevalecen; la documentacion se usa solo como evidencia secundaria. **Alcance:** estado del worktree al iniciar la auditoria, sin modificar comportamiento.

## Estado del repositorio

| Dato | Resultado |
|---|---|
| Rama auditada | `feat/xmi-export` |
| HEAD | `c58a5f41710b8cc43db6c757fe8d7461f734e8e8`, igual a `main` y `origin/main` |
| `origin/main` | `c58a5f4`, merge de CU-09 |
| Merge-base HEAD/main | `c58a5f4` |
| Estado | Cambios sin confirmar: XMI en backend/frontend y sus pruebas/CU; no forman parte de HEAD ni de `main`. |
| Ramas relevantes | `feat/cu-10-realtime-collaboration`=`01eb2cd`, un commit por delante de main; `feat/uml-editor-completeness`, CU-01..CU-09 son ancestros/ramas ya integradas. |
| Commits recientes | `c58a5f4` merge CU-09; `f4a590b` colaboradores; `3cf1416` JWT/ownership; `d6e8112` rendering UML. |

**Presentable sin reservas como HEAD/main:** CU-01 a CU-09: modelo UML, editor, persistencia, autenticacion y colaboradores. **No presentable como integrado:** CU-10 realtime (solo rama no fusionada) y CU-21 exportacion XMI (solo worktree no confirmado). La diferencia `origin/main..HEAD` es vacia; las funcionalidades XMI no aparecen en Git porque son untracked/modificadas.

Evidencia: `git status --short --branch`, `git branch -avv`, `git log --oneline -15`, `git merge-base HEAD origin/main`; `backend/app/api/projects.py`; `backend/app/interoperability/xmi/exporter.py` (no confirmado).

## 1. Vision real del producto

Producto sin nombre comercial: paquete `examen-sw1`; herramienta CASE web para crear y editar diagramas de clases UML con documento canonico persistible. El objetivo tecnico realizado es una aplicacion Vue/FastAPI/PostgreSQL con edicion mediante comandos, no el generador completo descrito en `product.md`.

| Capacidad | Estado real | Evidencia |
|---|---|---|
| Proyecto canonico separado de layout | IMPLEMENTADA | `backend/app/domain/uml/models.py`, `frontend/src/features/editor/types.ts` |
| Clases, miembros y cuatro relaciones | IMPLEMENTADA | `models.py`, `executor.py`, canvas Vue Flow |
| Validacion diagnostica, Command Bus, Undo/Redo | IMPLEMENTADA | `validation.py`, `command_bus.py` |
| Canvas, inspector, drag y auto-layout | IMPLEMENTADA | `frontend/src/features/editor/`, `canvas/`, `auto-layout.ts` |
| PostgreSQL, CAS, JWT y ownership | IMPLEMENTADA | `backend/app/db/`, `api/auth.py`, `api/projects.py` |
| Colaboradores directos EDITOR/VIEWER | IMPLEMENTADA | `db/memberships.py`, `projects.py` |
| Exportar XMI | PARCIAL, no confirmado | `backend/app/interoperability/xmi/exporter.py`, cambios de worktree |
| Realtime | PARCIAL, solo rama `feat/cu-10-realtime-collaboration` | `git show 01eb2cd:backend/app/realtime/projects.py` |
| Presencia, invitaciones, importacion XMI, IA/STT, generadores, AWS, offline/LAN demostrado | PLANIFICADA / inexistente en HEAD | roadmap CU-11..24; ausencia de modulos correspondientes |
| README/arquitectura de fundacion | OBSOLETA | `README.md`, `docs/ARCHITECTURE.md` frente a codigo CU-01..09 |

## 2. Stack tecnologico real

| Area | Tecnologia/version usada | Fuente |
|---|---|---|
| Frontend | Vue 3.5.42, TypeScript 5.9.3, Vite 8.2.2, Node >=24 | `frontend/package.json` |
| UI/estado | Vuetify 3.13.3, Pinia 4.0.3, MDI 7.4.47 | `frontend/package.json`, `src/plugins/vuetify.ts` |
| Canvas/layout | `@vue-flow/core` 1.48.2, `d3-dag` 1.2.2 | `frontend/package.json`, `auto-layout.ts` |
| Tests frontend | Vitest 4.1.10, Vue Test Utils 2.5.0, jsdom 30.0.1 | `frontend/package.json` |
| Backend | Python >=3.13, FastAPI 0.141.1, Uvicorn 0.52.4 | `backend/pyproject.toml` |
| Datos | Pydantic 2.13.5, SQLAlchemy 2.0.52, Alembic 1.19.2, psycopg 3.3.5; PostgreSQL por URL | `backend/pyproject.toml`, `core/config.py` |
| Seguridad | PyJWT 2.13.0; `pwdlib[argon2]` 0.3.1 | `backend/pyproject.toml`, `core/security.py` |
| XML | lxml 6.0.2 solo en cambio no confirmado | `backend/pyproject.toml`, `interoperability/xmi/exporter.py` |
| Tests backend | pytest 9.1.1, pytest-asyncio 1.4.0, HTTPX 0.28.1, Ruff 0.16.6 | `backend/pyproject.toml` |

No hay WebSocket, AWS, Java/Spring, Flutter, Jinja2, Transformers, PyTorch ni CTranslate2 en HEAD. WebSocket aparece exclusivamente en CU-10 no fusionado.

## 3. Estructura general del sistema

| Modulo | Responsabilidad | Dependencias/archivos principales |
|---|---|---|
| Frontend app | Gate de sesion y workspace | `frontend/src/App.vue`, `main.ts`, Pinia/Vuetify |
| Auth frontend | Login/registro/JWT local | `features/auth/*`, `services/api.ts` |
| Editor frontend | Proyeccion y controles | `features/editor/EditorWorkspace.vue`, `editor-store.ts`, `editor-api.ts` |
| Canvas | Render de documento a Vue Flow | `features/editor/canvas/*`, `project-to-flow.ts` |
| API FastAPI | HTTP, dependencias, respuestas | `backend/app/main.py`, `api/{health,auth,projects}.py` |
| Dominio UML | Tipos, comandos, invariantes y snapshots | `domain/uml/{models,commands,executor,validation,command_bus}.py` |
| Persistencia | ORM, conversion ProjectDocument, CAS | `db/{projects,users,memberships,session}.py` |
| Interoperabilidad | Exporta XMI del modelo semantico | `interoperability/xmi/exporter.py`, no confirmado |

Arquitectura real: navegador --HTTP JSON/Bearer--> FastAPI --SQLAlchemy/psycopg--> PostgreSQL. El frontend nunca persiste directamente ni es fuente semantica; Vue Flow es una proyeccion. Realtime no integra esta arquitectura en HEAD.

## 4. Modelo canonico UML

Todos son Pydantic `DomainModel` (`extra="forbid"`, aliases), en `backend/app/domain/uml/models.py`.

| Tipo | Atributos/tipos | Relaciones/responsabilidad |
|---|---|---|
| `ProjectDocument` | `id: UUID`, `metadata: dict`, `ownerId: UUID`, `revision: int>=0`, `createdAt/updatedAt: datetime`, `umlModel`, `diagramLayout` | Raiz; layout solo referencia clases existentes. |
| `CanonicalUmlModel` | `elements: list[UmlElement]` discriminada por `kind` | Contenedor semantico; UUID unico global entre elementos y miembros. |
| `UmlClass` | UUID, `kind=class`, nombre, `visibility`, `attributes[]`, `operations[]` | Composicion 0..* con atributos y operaciones. |
| `UmlAttribute` | UUID, nombre, tipo texto, visibilidad | Parte de una clase, 0..*. |
| `UmlOperation` | UUID, nombre, visibilidad, `parameters[]`, `returnType?` | Parte de clase; compone parametros 0..*. |
| `UmlParameter` | UUID, nombre, tipo texto | Parte de operacion. |
| `UmlMultiplicity` | `lower:int>=0`, `upper:int|"*"`, upper>=lower | Valor en ambos extremos de asociacion/agregacion/composicion. |
| `UmlAssociation` | UUID, `sourceId`, `targetId`, ambas multiplicidades | Relacion 1 a 2 entre clases; extremos neutrales. |
| `UmlAggregation` | mismos campos | `sourceId` todo -> `targetId` parte; diamante hueco fuente. |
| `UmlComposition` | mismos campos | `sourceId` todo -> `targetId` parte; diamante lleno fuente. |
| `UmlGeneralization` | UUID, `sourceId`, `targetId` | hija -> padre; sin multiplicidad. |
| `DiagramLayout` | `nodes: dict[UUID, DiagramNodeLayout]` | Separado de semantica. |
| `DiagramNodeLayout` | `x,y: float`, `width,height: float>0` | Posicion/tamano de una clase. |

`metadata` es JSON libre del proyecto; no hay tipo de metadata de generacion ni semantica interpretada. Soporta exactamente Association, Aggregation, Composition y Generalization. No soporta Enumeration, Package, Dependency, Realization, asociaciones n-arias, nombres de rol, navegabilidad, restricciones, perfiles/estereotipos tipados ni UMLDI.

## 5. Command Bus y edicion

`UmlCommand` es union discriminada: `addElement`, `updateElement`, `removeElement`, `setNodeLayout`, `removeNodeLayout` (`commands.py`). `UmlCommandExecutor.execute` hace copia profunda, aplica y devuelve nuevo documento; `UmlCommandBus` mantiene snapshots undo/redo (maximo 100), aumenta revision y `updatedAt` monotono (`executor.py`, `command_bus.py`).

Flujo exacto: Usuario -> `EditorWorkspace`/dialogo/inspector -> `editor-store.execute()` -> `POST /projects/{id}/commands` con `baseRevision` -> `get_current_user` Bearer y `_project_access` -> lock process-local -> documento/bus -> executor -> validacion estructural Pydantic y regla de herencia -> CAS SQL `WHERE id AND revision` -> commit -> `{document,canUndo,canRedo}` -> store reemplaza proyeccion. Undo/redo usan rutas propias, mismo acceso/lock/CAS/bus. No hay broadcast en HEAD.

## 6. Reglas UML y validacion

| Regla | Archivo/funcion | Comportamiento/error |
|---|---|---|
| UUID global | `models.py: CanonicalUmlModel` | Rechazo Pydantic de IDs duplicados en top-level/miembros. |
| Layout valido | `ProjectDocument` validator | Nodo layout a clase inexistente: validacion Pydantic. |
| Nombre/tipo | modelos de miembros | No vacio; `upper` multiplicidad >= `lower`; `*` permitido. |
| Duplicados semanticos | `validation.py: validate_uml_model` | Diagnosticos `DUPLICATE_CLASS_NAME`, atributo/parametro/operacion; no bloquean en general. |
| Extremos | modelos relaciones | IDs deben ser clases existentes por modelo/ejecutor. |
| Autoherencia/ciclo | `executor.py` | Bloquea con `GENERALIZATION_SELF_REFERENCE`/`GENERALIZATION_CYCLE`. |
| Generalizacion duplicada | `validation.py` | Diagnostico; no bloqueo generico. |
| Eliminar clase relacionada | `executor.py` | Solo quita layout; modelo restante invalido y operacion atomica se rechaza. |
| Revision | `api/projects.py` | `409 PROJECT_REVISION_CONFLICT`; no se persiste cambio. |

`validate_uml_model` devuelve `UmlValidationResult` de errores (`code`, `severity`, `message`, `elementId`, `field`), sin warnings ni `path` logico. No hay endpoint de validacion separado.

## 7. Persistencia y base de datos

Migraciones: `20260920_01_create_projects.py`, `20260921_02_create_users.py`, `20260922_03_create_project_memberships.py`.

| Tabla | Columnas/llaves/indices | Relaciones |
|---|---|---|
| `users` | `id UUID PK`, `email VARCHAR UNIQUE`, `password_hash`, `created_at`, `updated_at` | Referenciada por memberships. |
| `projects` | `id UUID PK`, `owner_id UUID INDEX` sin FK, `metadata JSONB`, `uml_model JSONB`, `diagram_layout JSONB`, `revision`, timestamps TZ | Una fila contiene el documento; UML no se normaliza. |
| `project_memberships` | `project_id,user_id` PK compuesta/FK, `role ENUM(EDITOR,VIEWER)`, timestamps, indice usuario | ambos FK con `ON DELETE CASCADE`. |

Relacionalmente se guarda identidad/acceso; semantica UML y layout son JSONB separados. `owner_id` identifica al propietario y representa implicita y efectivamente OWNER: no hay fila membership OWNER. EDITOR/VIEWER son filas de membership.

## 8. Autenticacion y autorizacion

Registro/login normalizan email y exigen password 8..128; hash `PasswordHash.recommended()` (Argon2 de pwdlib). JWT HS256 contiene `sub`, `iat`, `exp`, con expiracion por defecto 480 minutos; se envía `Authorization: Bearer` (`api/auth.py`, `core/security.py`, `core/config.py`). `/auth/me` resuelve usuario actual. Token ausente, invalido, expirado o usuario inexistente: `401 AUTH_INVALID_TOKEN` y `WWW-Authenticate: Bearer`. Recurso sin acceso: `404 PROJECT_NOT_FOUND`; miembro sin privilegio administrativo: `403 PROJECT_ACCESS_FORBIDDEN`.

| Actor/rol | Leer | Crear | Editar/Undo/Redo | Exportar XMI* | Colaboradores | Realtime* |
|---|---|---|---|---|---|---|
| Visitante | No | No | No | No | No | No |
| Autenticado/OWNER | Propios | Si | Si | Si | Si | No HEAD |
| EDITOR | Compartidos | Si | Si | Si | No | No HEAD |
| VIEWER | Compartidos | Si | No | Si | No | No HEAD |

\*XMI es worktree no confirmado; realtime es CU-10 no integrado. Todo autenticado puede crear su propio proyecto; OWNER es una especializacion contextual del autenticado.

## 9. Colaboradores

El OWNER agrega directamente un usuario ya registrado por email con `POST /projects/{id}/collaborators`; selecciona `EDITOR`/`VIEWER`, cambia con PATCH y elimina con DELETE. No existen invitaciones, email saliente, tokens, expiracion ni estados. Solo OWNER lista/administra; `effectiveRole` aparece en `GET /projects`. Evidencia: `api/projects.py`, `db/memberships.py`, `CU-09-collaborators.md`.

Contradiccion: roadmap CU-09 dice incluir `ProjectInvitation`, token, estado y expiracion (`IMPLEMENTATION-ROADMAP.md:76-80`); codigo y CU-09 dicen explicitamente que no existen.

## 10. Realtime

**HEAD:** no hay endpoint, `ConnectionManager`, cliente, eventos ni presencia. **Solo rama `feat/cu-10-realtime-collaboration` commit `01eb2cd`:** `WS /projects/{id}/realtime?token=JWT`; autentica antes de aceptar, agrupa sockets por proyecto/usuario, transmite `{"type":"project.updated","document":ProjectDocument completo}` tras commit/CAS REST, y cierra sockets revocados con 1008. Frontend reconecta 1..5 s, aplica solo revisiones mayores y no reintenta 1008. Recibe VIEWER; no permite comandos por WS. No hay presencia, cursor, seleccion, CRDT ni manager distribuido/multiproceso. El manager es process-local.

Contradiccion con producto: `product.md:631` prohíbe documento completo por edición; CU-10 de rama lo envía completo. Evidencia: `git show 01eb2cd:backend/app/realtime/projects.py`, `...:frontend/src/features/editor/realtime-service.ts`.

## 11. Exportacion XMI

**Exportacion: SI, solo worktree no confirmado. Importacion: NO. UMLDI: NO. Geometria EA: NO. `xmi:Extension` EA: NO.**

`GET /projects/{id}/export/xmi` reutiliza lectura OWNER/EDITOR/VIEWER y entrega adjunto XML. `export_project_document` usa lxml, ignora `diagramLayout`, usa `xmi:XMI`, `xmi:version="2.1"`, XMI `http://schema.omg.org/spec/XMI/2.1` y UML `http://www.omg.org/spec/UML/20161101`. Genera `uml:Model`, primitive types (ordenados, ID SHA-256 estable), clases, atributos, operaciones, parametros y retorno sintetico; asociaciones con dos extremos y multiplicidad; agregacion/composicion como Association con `aggregation=shared/composite` en extremo destino; generalizacion. IDs UUID -> `id_<hex>`. Nombre de archivo ASCII sanitizado. Repetir con igual entrada es determinista salvo que el orden de `elements` sea parte de entrada.

No valida antes de exportar, no usa `iterparse`, no hay importador/round-trip ni prueba contra Enterprise Architect. Evidencia: `backend/app/interoperability/xmi/exporter.py`, `api/projects.py`, `tests/interoperability/test_xmi_exporter.py`, `tests/api/test_project_xmi_export.py`, `CU-21-xmi-interoperability.md`.

## 12. Catalogo de endpoints reales

| Grupo | Metodo/ruta | Auth/acceso | Input -> output/responsabilidad | Archivo |
|---|---|---|---|---|
| HEALTH | GET `/health` | Publico | -> estado servicio | `api/health.py` |
| HEALTH | GET `/health/db` | Publico | -> DB o 503 | `api/health.py` |
| AUTH | POST `/auth/register` | Publico | email/password -> token+usuario | `api/auth.py` |
| AUTH | POST `/auth/login` | Publico | email/password -> token+usuario | `api/auth.py` |
| AUTH | GET `/auth/me` | Bearer | -> usuario | `api/auth.py` |
| PROJECTS | POST `/projects` | Bearer | metadata? -> ProjectDocument | `api/projects.py` |
| PROJECTS | GET `/projects` | Bearer | -> ProjectSummary[] propios/compartidos | `api/projects.py` |
| PROJECTS | GET `/projects/{id}` | lector | -> ProjectDocument | `api/projects.py` |
| COMMANDS | POST `/{id}/commands` | owner/editor | baseRevision+UmlCommand -> editor state | `api/projects.py` |
| UNDO/REDO | POST `/{id}/undo`, `/redo` | owner/editor | baseRevision -> editor state | `api/projects.py` |
| COLLABORATORS | GET/POST `/ {id}/collaborators` | owner | -> lista / collaborator | `api/projects.py` |
| COLLABORATORS | PATCH/DELETE `/{id}/collaborators/{userId}` | owner | role -> collaborator / 204 | `api/projects.py` |
| XMI* | GET `/{id}/export/xmi` | lector | -> XML attachment | `api/projects.py` |
| REALTIME** | WS `/{id}/realtime?token=` | lector | -> `project.updated` | rama CU-10 |

Rutas sin espacio inicial: todas bajo `/projects`. *No confirmado. **No HEAD.

## 13. Frontend

| Componente | Responsabilidad/dependencias | Archivo |
|---|---|---|
| Auth | formulario login/registro | `features/auth/AuthScreen.vue`, `auth-store.ts`, `auth-api.ts` |
| Seleccion | lista/crea/abre proyectos | `EditorWorkspace.vue`, `editor-store.ts` |
| Workspace/toolbars | comandos, roles, undo/redo, auto-layout | `EditorWorkspace.vue` |
| Canvas | Vue Flow, nodos/edges, pan/zoom/drag | `canvas/UmlCanvas.vue`, `UmlClassNode.vue`, `UmlRelationshipEdge.vue` |
| Inspector/dialogos | borrradores y relaciones | `InspectorPanel.vue`, `RelationshipDialog.vue` |
| Colaboradores | alta/rol/baja OWNER | `EditorWorkspace.vue`, `editor-api.ts` |
| API/store | fetch Bearer, estado autoritativo | `services/api.ts`, `editor-api.ts`, `editor-store.ts` |
| XMI* | descarga Blob/anchor | `editor-api.ts`, `EditorWorkspace.vue` |

No router, presencia ni realtime en HEAD. `localStorage` conserva JWT. Canvas no conecta handles; relaciones solo dialogo.

## 14. Matriz de actores

| Actor | Definicion/capacidades |
|---|---|
| Visitante | Sin JWT: registro, login, health. |
| Usuario autenticado | Base de OWNER/EDITOR/VIEWER; crea proyectos propios. |
| OWNER | Usuario con `projects.owner_id`; administra miembros y edita/lee. |
| EDITOR | Membership; lee y muta modelo. |
| VIEWER | Membership; solo lee y exporta XMI si cambio no confirmado se integra. |
| Backend | Sistema que autentica, autoriza, ejecuta, persiste y responde. |
| Enterprise Architect | Sistema externo objetivo de XMI; no existe integracion ejecutada/verificada. |

OWNER, EDITOR y VIEWER especializan Usuario autenticado en contexto de proyecto. No asociar Backend como actor de casos internos; EA solo se asocia a exportar como receptor externo.

## 15. Casos de uso reales

| ID | CU | Actor | Precondicion -> resultado | Punto tecnico | Estado |
|---|---|---|---|---|---|
| CU-A01 | Registrar usuario | Visitante | credenciales validas -> JWT | `/auth/register` | IMPLEMENTADO |
| CU-A02 | Iniciar sesion | Visitante | usuario/password -> JWT | `/auth/login` | IMPLEMENTADO |
| CU-P01 | Acceder/listar proyectos | Autenticado | JWT -> lista autorizada | `GET /projects` | IMPLEMENTADO |
| CU-P02 | Crear/abrir proyecto | Autenticado | JWT -> documento owner/lector | `/projects` | IMPLEMENTADO |
| CU-U01 | Modelar clases/miembros | OWNER/EDITOR | proyecto editable -> revision persistida | commands/editor | IMPLEMENTADO |
| CU-U02 | Modelar relaciones | OWNER/EDITOR | clases existentes -> revision | commands/dialogo | IMPLEMENTADO |
| CU-U03 | Validar UML | OWNER/EDITOR | modelo -> diagnosticos; no CU HTTP separado | `validate_uml_model` | IMPLEMENTADO, interno |
| CU-U04 | Deshacer/Rehacer | OWNER/EDITOR | historial instancia -> revision | `/undo`,`/redo` | IMPLEMENTADO |
| CU-U05 | Auto-organizar | OWNER/EDITOR | clases -> layouts persistidos | `auto-layout.ts` | IMPLEMENTADO |
| CU-C01 | Administrar colaboradores | OWNER | usuario registrado -> membership | collaborators API | IMPLEMENTADO |
| CU-X01 | Exportar XMI | lector | proyecto accesible -> archivo | export endpoint | PARCIAL/no confirmado |
| CU-R01 | Colaborar realtime | lector | socket -> actualizaciones | WS CU-10 | PARCIAL/no HEAD |
| CU-PL | Presencia/importar/generar/IA/AWS | segun roadmap | no implementado | CU-11..24 | PLANIFICADO |

`Modelar clases` y `Modelar relaciones` pueden incluir `Validar UML`; Undo/Redo son especializaciones de editar. No hay extension justificable para invitaciones/presencia porque no existen.

## 16. Paquetes de analisis

| Paquete | CUs/responsabilidad | Dependencias/componentes reales |
|---|---|---|
| Identidad y acceso | A01,A02,P01 | auth API/store, users, security |
| Proyectos y acceso compartido | P01,P02,C01 | projects API, memberships, PostgreSQL |
| Modelo y edicion UML | U01..U05 | domain/uml, editor, canvas |
| Persistencia | soporte | SQLAlchemy/Alembic/JSONB/CAS |
| Interoperabilidad XMI | X01 | exporter/API/UI no confirmado |
| Colaboracion realtime | R01 | solo rama CU-10; no paquete desplegado HEAD |

Dependencias: UI -> API -> identidad/acceso + modelo -> persistencia; XMI depende de proyectos/modelo; realtime depende de proyectos/persistencia.

## 17. Secuencias importantes

| Flujo | Lifelines y mensajes ordenados | Errores |
|---|---|---|
| A Registro/login | Usuario->AuthScreen->auth-api->FastAPI auth->users/security->JWT->store/localStorage | 401 credenciales, 422 entrada |
| B Crear proyecto | Usuario->workspace/store->POST projects->JWT->ProjectRecord/DB->ProjectDocument->store | 401 token, 503 DB |
| C Abrir proyecto | Usuario->store->GET project->acceso->DB->document->canvas projection | 401/404 |
| D Comando | Usuario->UI->store->POST commands->auth/acceso->lock/bus/executor->CAS DB->state->store | 403,404,409,422 |
| E Undo/Redo | Usuario->store->POST undo/redo->mismo acceso/lock/bus snapshot->CAS DB->state | 409, historial vacio |
| F Colaborador | OWNER->dialogo->POST/PATCH/DELETE->auth/owner check->membership DB->respuesta | 403,404,409 duplicado |
| G Realtime* | Navegador->WS token->manager->REST commit->broadcast ProjectDocument->store | 1008; solo rama CU-10 |
| H XMI* | Lector->toolbar->GET export->acceso->exporter->XML attachment->Blob download | 401/404; no confirmado |

## 18. Comunicacion

| Flujo | Boundary / control / entity | Mensajes |
|---|---|---|
| Login | `AuthScreen` / auth API+security / `UserRecord` | 1 submit, 2 verify, 3 JWT, 4 persist session |
| Crear proyecto | `EditorWorkspace` / projects router / `ProjectRecord` | 1 create, 2 authorize, 3 insert, 4 document |
| Modelar UML | inspector/canvas / store-router-bus-executor / ProjectRecord | 1 command, 2 authorize, 3 execute, 4 CAS, 5 state |
| Realtime* | realtime service / connection manager / ProjectRecord | 1 connect, 2 REST commit, 3 broadcast; rama CU-10 |
| XMI* | toolbar / router-exporter / ProjectDocument JSONB | 1 request, 2 access, 3 serialize, 4 download |

## 19. Componentes y despliegue

**Despliegue actual validado/documentado:** navegador a `http://localhost:5173` (Vite) por HTTP a FastAPI `:8000`; FastAPI a PostgreSQL local `localhost:5432/examen_sw1`. Docker Compose opcional expone PostgreSQL host `55432` -> contenedor `5432`. Variables: backend `DATABASE_URL`, `JWT_SECRET_KEY`, `FRONTEND_ORIGIN`, `JWT_EXPIRE_MINUTES`; frontend `VITE_API_BASE_URL`. CORS permite el origen configurado.

**Planificado/no verificado:** WebSocket de CU-10, LAN/offline integral, AWS. No afirmar que AWS esta desplegado. Evidencia: `README.md`, `compose.yaml`, `.env.example`, `docs/deployment/AWS.md`.

## 20. Pruebas

Worktree auditado: backend 14 archivos de test, incluidos XMI no confirmados; ejecucion reportada/verificada: **179 passed**, Ruff OK con `JWT_SECRET_KEY` temporal. Sin esa variable, collection falla por configuracion requerida. Cubre health, dominio, persistencia, auth, mutaciones, colaboradores y XMI. Frontend: 13 specs; **46/46 en 13 archivos**, typecheck/build OK; cubre auth, API/store, projection, layout, inspector/dialogo/nodos/edges. Build advierte chunks >500 kB. No Cypress/E2E, coverage ni prueba manual actual de CU-08/09/XMI independiente.

`compileall`, `pip check`, Alembic y `scripts/check.ps1`: documentados como checks; para este corte, resultado integral actual **NO VERIFICADO** por auditoria. Las cifras CU-10 (48/14) son de otra rama; no mezclar.

## 21. Deuda y limitaciones

| Clase | Limitacion demostrable |
|---|---|
| LIMITACION FUNCIONAL | Subconjunto UML sin Package/Enumeration/Dependency/Realization/roles/navegabilidad; no import XMI/UMLDI/EA extension; sin presencia. |
| DEUDA TECNICA | Undo/redo y locks/bus process-local; `ConnectionManager` CU-10 process-local; `owner_id` sin FK; UI auto-layout genera una revision por nodo. |
| RIESGO | JWT en localStorage; errores DB no generales en colaboradores; XMI no comprobado con EA; endpoint realtime manda documento completo; test suite requiere secreto de entorno. |
| TRABAJO FUTURO | CU-10 merge/pruebas manuales; CU-11..24; import/round-trip; despliegue y E2E. |

## 22. Documentacion desactualizada

| Documento | Afirmacion | Realidad | Correccion recomendada |
|---|---|---|---|
| `README.md:1-3` | Solo CU-00/health | HEAD CU-01..09 | Describir editor, DB, JWT y collaborators. |
| `docs/STATUS.md:24,29,33-38` | Auth pendiente; CU-09 siguiente | Ambos existen en HEAD | Actualizar al corte CU-09. |
| `docs/HANDOFF.md:5,9,51-55` | CU-09 siguiente, no XMI | CU-09 HEAD; XMI worktree | Actualizar CU-09 y separar XMI no confirmado. |
| `docs/ARCHITECTURE.md:12-20,47-58` | Solo fundacion/no UML editor | Su propio texto y codigo CU-01..09 lo contradicen | Consolidar arquitectura actual. |
| Roadmap CU-09 | invitations/tokens/expiry incluidos | Solo memberships directas | Reducir alcance o marcar pendiente. |
| `product.md` | Offline, presencia, importacion, generadores, IA, AWS | Planificados/no HEAD | Mantener como vision, no como estado. |

## 25. Estructura academica recomendada

1. Perfil/fundamentos: problema CASE y alcance real; diagrama de contexto.
2. ERS/captura: actores, matriz de permisos y CUs implementados vs planificados.
3. Analisis: paquetes, modelo canonico UML, reglas y modelo de datos.
4. Diseno: componentes, despliegue, secuencias/comunicaciones de login, comando y colaborador; XMI separado como incremento no confirmado.
5. Implementacion: Vue/FastAPI/PostgreSQL, Command Bus, persistencia y seguridad.
6. Pruebas: evidencia por rama/worktree, limitaciones y pruebas manuales pendientes.
7. Riesgos/seguridad, resultados, conclusiones y anexos: contratos API, migraciones y matriz EA.

## 26. Afirmaciones para la defensa

**Puedo afirmar (HEAD/main):**
- Existe una herramienta web Vue/FastAPI/PostgreSQL para diagramas de clases UML.
- ProjectDocument separa modelo semantico y layout.
- Se soportan clases, atributos, operaciones, parametros y cuatro tipos de relacion.
- Las mutaciones pasan por Command Bus, con CAS y Undo/Redo por proceso.
- Hay JWT/Argon2, ownership y memberships EDITOR/VIEWER.

**Solo con reserva explicita:** XMI 2.1 exportable existe en worktree sin commit; realtime existe en rama CU-10 no fusionada.

**No debo afirmar:**
- Importacion XMI, compatibilidad verificada con Enterprise Architect, UMLDI o geometria EA.
- Presencia, cursores remotos, CRDT o realtime integrado en main.
- Invitaciones/tokens/expiracion de colaboradores.
- AWS desplegado, offline/LAN integral demostrado, IA/STT, generacion Spring/Flutter/OpenAPI/Postman/Domain Manifest.
