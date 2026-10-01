# Especificaciones preparatorias para Enterprise Architect 15

Fuente y convencion: nombres logicos estables; `RG-Core` reutiliza el sistema, `RG-Identity` identidad, `RG-UML` dominio, `RG-Data` datos, `RG-XMI` interoperabilidad. `*` = worktree no confirmado; `**` = rama CU-10 no fusionada. Estas especificaciones no son XMI.

## D-01 - Contexto del sistema
**Tipo:** UML System Context. **Nombre:** Contexto CASE UML.

**Elements:** `visitor` Actor Visitante RG-Core; `user` Actor Usuario autenticado RG-Core; `case` Component Sistema CASE RG-Core; `browser` Component Navegador/Vue RG-Core; `api` Component FastAPI RG-Core; `db` Node PostgreSQL RG-Data; `ea` Actor/System Enterprise Architect RG-XMI.

**Relationships:** visitor->case association registrar/login; user->case association gestionar proyectos/UML; browser->api dependency HTTP JSON; api->db dependency SQL; case->ea dependency exportar XMI*. 

**Layout suggestion:** actores izquierda, CASE centro, browser/API dentro o a derecha, DB abajo derecha, EA derecha; routing orthogonal, sin cruzar API-DB.

## D-02 - Casos de uso implementados
**Tipo:** Use Case. **Nombre:** Casos de uso reales en HEAD.

**Elements:** `visitor` Actor Visitante RG-Core; `authenticatedUser` Actor Usuario autenticado RG-Identity; `owner` Actor OWNER RG-Identity; `editor` Actor EDITOR RG-Identity; `viewer` Actor VIEWER RG-Identity; UC `register`, `login`, `accessProjects`, `createOpen`, `modelClasses`, `modelRelations`, `undoRedo`, `autoLayout`, `manageCollaborators` RG-Core.

**Relationships:** owner/editor/viewer generalization->authenticatedUser; visitor->register/login; authenticatedUser->accessProjects/createOpen; owner/editor->modelClasses/modelRelations/undoRedo/autoLayout; owner->manageCollaborators; viewer->accessProjects. `modelClasses` and `modelRelations` include `validateUml` (shown as internal UC only if needed). 

**Layout suggestion:** actors left (visitor top; user specializations below), use cases within system boundary center; owner-only collaborator UC right; no Backend actor.

## D-03 - Modelo canonico UML
**Tipo:** Class. **Nombre:** Modelo canonico ProjectDocument.

**Elements:** `ProjectDocument` Class RG-UML; `CanonicalUmlModel` Class RG-UML; `DiagramLayout` Class RG-UML; `DiagramNodeLayout` Class RG-UML; `UmlClass`, `UmlAttribute`, `UmlOperation`, `UmlParameter`, `UmlMultiplicity`, `UmlAssociation`, `UmlAggregation`, `UmlComposition`, `UmlGeneralization` Classes RG-UML; `UmlElement` abstract/interface RG-UML.

**Relationships:** ProjectDocument *--1 CanonicalUmlModel; ProjectDocument *--1 DiagramLayout; CanonicalUmlModel *--0..* UmlElement; UmlClass generalization->UmlElement; each relation class generalization->UmlElement; UmlClass *--0..* UmlAttribute and UmlOperation; UmlOperation *--0..* UmlParameter; DiagramLayout *--0..* DiagramNodeLayout; Association/Aggregation/Composition *--2 UmlMultiplicity; relation source/target dependency->UmlClass (label UUID reference, multiplicity 1 each).

**Layout suggestion:** root top; semantic and layout under it; class/member hierarchy left, relationship hierarchy right, multiplicity below relationship; composition vertical.

## D-04 - Modelo logico de datos
**Tipo:** Class/ER. **Nombre:** PostgreSQL de proyectos y accesos.

**Elements:** `users` Entity RG-Data label `id UUID PK; email UNIQUE; password_hash; timestamps`; `projects` Entity RG-Data label `id UUID PK; owner_id INDEX; metadata/uml_model/diagram_layout JSONB; revision; timestamps`; `project_memberships` Entity RG-Data label `project_id,user_id PK/FK; role; timestamps`.

**Relationships:** projects 1--0..* project_memberships composition/cascade via project_id; users 1--0..* project_memberships composition/cascade via user_id; projects.owner_id -> users.id dependency labeled `sin FK`. 

**Layout suggestion:** projects center, users left, memberships bottom center; FK associations solid, owner dependency dashed to avoid claiming FK.

## D-05 - Paquetes de analisis
**Tipo:** Package. **Nombre:** Paquetes conceptuales reales.

**Elements:** `IdentityAccess`, `ProjectsCollaboration`, `UmlModelEditing`, `Persistence`, `XmiInteroperability*`, `RealtimeCU10**` Packages.

**Relationships:** ProjectsCollaboration->IdentityAccess; ProjectsCollaboration->UmlModelEditing; ProjectsCollaboration->Persistence; UmlModelEditing->Persistence; XmiInteroperability->ProjectsCollaboration/UmlModelEditing; RealtimeCU10->ProjectsCollaboration/Persistence.

**Layout suggestion:** identidad arriba izquierda, UML arriba derecha, proyectos centro, persistencia abajo, XMI derecha, realtime como paquete discontinuo/anexo.

## D-06 - Arquitectura logica
**Tipo:** Component. **Nombre:** Componentes de la aplicacion CASE.

**Elements:** `VueApp` Component RG-Core; `AuthFeature`, `EditorFeature`, `CanvasProjection`, `ApiClient` Components RG-Core; `FastApi` Component RG-Core; `AuthApi`, `ProjectsApi`, `UmlDomain`, `SqlAlchemyRepositories` Components RG-Core; `PostgreSQL` Database RG-Data.

**Relationships:** VueApp *-- features; features->ApiClient; ApiClient->FastApi HTTP/JSON; FastApi *-- AuthApi/ProjectsApi; ProjectsApi->UmlDomain; AuthApi/ProjectsApi->SqlAlchemyRepositories; repositories->PostgreSQL SQL. 

**Layout suggestion:** frontend left, API center, domain below API, persistence right; ports labeled HTTP 8000 and SQL.

## D-07 - Despliegue local validado
**Tipo:** Deployment. **Nombre:** Despliegue local de desarrollo validado.

**Elements:** `UserDevice` Node; `Browser` Artifact; `ViteDevServer` Node `:5173`; `FastAPIUvicorn` Node `:8000`; `PostgreSQLLocal` Database `:5432`; `PostgreSQLDockerOptional` Database `host:55432/container:5432`.

**Relationships:** Browser->ViteDevServer HTTP; Browser->FastAPIUvicorn HTTP/JSON Bearer; FastAPIUvicorn->PostgreSQLLocal psycopg/SQL; FastAPIUvicorn->PostgreSQLDockerOptional alternate SQL path. 

**Layout suggestion:** device/browser left, Vite/API middle, local DB right; Docker DB below with `alternative` note. Do not include AWS/WS as deployed.

## D-08 - Secuencia login
**Tipo:** Sequence. **Nombre:** Registro, login y restauracion de sesion.

**Elements:** lifelines `User`, `AuthScreen`, `AuthStore`, `AuthApi`, `AuthRouter`, `Security`, `UserRecord`, `PostgreSQL` RG-Identity.

**Relationships/messages:** 1 User->AuthScreen submit; 2 AuthScreen->AuthStore login/register; 3 Store->AuthApi POST; 4 AuthApi->AuthRouter request; 5 router->UserRecord lookup/create; 6 router->Security verify/hash and create JWT; 7 return token/user; 8 Store->localStorage save; restore path: Store->AuthApi GET `/auth/me` with Bearer; alt invalid -> clear session/401.

**Layout suggestion:** left-to-right UI, client state, API, security/data; use `alt register/login`, `alt invalid credentials/token` fragments.

## D-09 - Secuencia comando UML
**Tipo:** Sequence. **Nombre:** Ejecutar comando UML persistente.

**Elements:** `User`, `InspectorOrCanvas`, `EditorStore`, `ProjectsRouter`, `CurrentUser`, `ProjectAccess`, `ProjectLock`, `UmlCommandBus`, `UmlCommandExecutor`, `ProjectRepository`, `PostgreSQL` RG-UML.

**Relationships/messages:** 1 user edit; 2 UI->store command; 3 store->router POST commands(baseRevision, command); 4 router->CurrentUser authenticate; 5 router->ProjectAccess authorize editor; 6 router->lock acquire; 7 bus->executor execute deep copy; 8 executor->validation/Pydantic invariants; 9 router->repository CAS update; 10 repository->DB commit; 11 return document/canUndo/canRedo; 12 store replaces projection. Alt 403/404/409/422/503.

**Layout suggestion:** UI left, API/auth middle, domain then DB right; place lock around bus/repository messages; avoid an imaginary realtime lifeline.

## D-10 - Secuencia colaboradores
**Tipo:** Sequence. **Nombre:** Administrar colaborador directo.

**Elements:** `Owner`, `CollaboratorDialog`, `EditorApi`, `ProjectsRouter`, `CurrentUser`, `ProjectAccess`, `UserRepository`, `MembershipRepository`, `PostgreSQL` RG-Identity.

**Relationships/messages:** 1 owner add/change/remove; 2 dialog->API POST/PATCH/DELETE; 3 router authenticate; 4 access require owner; 5 lookup registered email/user; 6 create/update/delete membership; 7 DB commit; 8 return collaborator/204. Alt 403,404,409 duplicate.

**Layout suggestion:** owner/UI left, router/access center, repositories/DB right; `alt` for create/update/delete.

## D-11 - Comunicacion modelar UML
**Tipo:** Communication. **Nombre:** Objetos de edicion UML.

**Elements:** `inspector:InspectorPanel` Boundary RG-UML; `store:EditorStore` Control; `router:ProjectsRouter` Control; `bus:UmlCommandBus` Control; `executor:UmlCommandExecutor` Control; `project:ProjectRecord` Entity; `db:PostgreSQL` Entity.

**Relationships/messages:** inspector->store `1: execute(command)`; store->router `2: POST commands`; router->bus `3: execute`; bus->executor `3.1: execute`; router->project `4: compare_and_swap`; project->db `4.1: commit`; router->store `5: EditorState`; store->inspector `6: render authoritative document`.

**Layout suggestion:** boundary left, controls central chain, entities right; connectors only adjacent objects; number labels visible.

## D-12 - Comunicacion login
**Tipo:** Communication. **Nombre:** Objetos de autenticacion.

**Elements:** `screen:AuthScreen` Boundary; `store:AuthStore` Control; `api:AuthApi` Boundary; `router:AuthRouter` Control; `security:Security` Control; `user:UserRecord` Entity; `db:PostgreSQL` Entity RG-Identity.

**Relationships/messages:** `1 submit`, `2 login/register`, `3 POST`, `4 lookup/create`, `5 verify/hash`, `6 issue JWT`, `7 session response`, `8 localStorage save`. 

**Layout suggestion:** screen/store/API left-to-center, router/security center, data right; response numbering returns over same links.

## D-13 - Command Bus y validacion
**Tipo:** Class. **Nombre:** Estructura de comandos y validacion.

**Elements:** `UmlCommand` abstract/interface; `AddElementCommand`, `UpdateElementCommand`, `RemoveElementCommand`, `SetNodeLayoutCommand`, `RemoveNodeLayoutCommand`; `UmlCommandBus`; `UmlCommandExecutor`; `UmlValidationResult`; `UmlDiagnostic`; `ProjectDocument` RG-UML.

**Relationships:** concrete commands generalization->UmlCommand; Bus dependency->UmlCommandExecutor/ProjectDocument/UmlCommand; Executor dependency->ProjectDocument; ValidationResult *--0..* Diagnostic; Bus aggregation->undoSnapshots/redoSnapshots `ProjectDocument[0..100]`. 

**Layout suggestion:** command hierarchy left, bus center, executor right, document bottom right, validation bottom left. Note validator reports diagnostics and is not universal command blocker.

## D-14 - Secuencia Undo/Redo
**Tipo:** Sequence. **Nombre:** Deshacer y rehacer persistente.

**Elements:** `User`, `EditorStore`, `ProjectsRouter`, `ProjectLock`, `UmlCommandBus`, `ProjectRepository`, `PostgreSQL` RG-UML.

**Relationships/messages:** 1 click undo/redo; 2 POST route with baseRevision; 3 authorize/acquire lock; 4 bus restore snapshot/move stacks/increment revision; 5 repository CAS; 6 commit; 7 response state; 8 store replace. Alt empty history/conflict/persistence error.

**Layout suggestion:** same placement D-09; annotate snapshots `process-local`, capacity 100.

## D-15 - Secuencia exportar XMI
**Tipo:** Sequence. **Nombre:** Exportar XMI 2.1 (worktree).

**Elements:** `Reader`, `EditorWorkspace`, `EditorApi`, `ProjectsRouter`, `ProjectAccess`, `ProjectRepository`, `XmiExporter`, `ProjectDocument`, `BrowserDownload` RG-XMI.

**Relationships/messages:** 1 click download; 2 GET export/xmi Bearer; 3 authenticate/read access; 4 load document; 5 exporter serializes umlModel with lxml; 6 XML attachment response; 7 Blob/object URL/anchor download. Alt 401/404.

**Layout suggestion:** reader/UI left, router/access center, repository/exporter right, download far right; note `diagramLayout excluded` and status `uncommitted`.

## D-16 - Comunicacion exportar XMI
**Tipo:** Communication. **Nombre:** Objetos de exportacion XMI.

**Elements:** `toolbar:EditorWorkspace` Boundary; `api:EditorApi` Boundary; `router:ProjectsRouter` Control; `access:ProjectAccess` Control; `exporter:XmiExporter` Control; `document:ProjectDocument` Entity; `download:BrowserDownload` Boundary RG-XMI.

**Relationships/messages:** toolbar->api `1 downloadProjectXmi`; api->router `2 GET`; router->access `3 authorize read`; router->document `4 load`; router->exporter `5 export_project_document`; router->api `6 XML/filename`; api->download `7 Blob URL/click`.

**Layout suggestion:** strict left-to-right chain; exporter below document; label XMI 2.1 namespaces only, no EA geometry.

## D-17 - Secuencia realtime CU-10
**Tipo:** Sequence. **Nombre:** Sincronizacion realtime de rama CU-10.

**Elements:** `EditorA`, `RestApi`, `ProjectsRouter`, `PostgreSQL`, `ConnectionManager`, `EditorBRealtimeService` RG-Core.

**Relationships/messages:** 1 EditorB->router WS connect token; 2 authorize then manager connect; 3 EditorA->router REST command; 4 CAS/commit DB; 5 router->manager broadcast `project.updated` full document; 6 manager->EditorB apply only newer revision. Revocation: membership delete -> commit -> close user sockets 1008.

**Layout suggestion:** EditorA left, REST/API center, DB below, manager right, EditorB far right; dashed frame `branch only / not HEAD`; call out no inbound WS command/presence.
