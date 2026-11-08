# Estrategia de testing

La base incluye pruebas mínimas para verificar que ambos proyectos arrancan correctamente.

## Backend

Comando:

```bash
pytest
```

Smoke test inicial:

- `GET /health` responde HTTP 200.
- el body identifica el servicio y estado.

No requiere PostgreSQL para este smoke test, por lo que permite distinguir fallos de aplicación de fallos de infraestructura.

### Validacion UML semantica

`tests/domain/test_uml_validation.py` prueba el validador puro contra modelos validos, duplicados de nombres, firmas de operaciones, ciclos y duplicados de generalizacion. Tambien verifica acumulacion ordenada de diagnosticos, no mutacion y serializacion Pydantic con aliases publicos. Estas pruebas no requieren PostgreSQL, red ni frontend.

### Command Bus y Undo/Redo

`tests/domain/test_uml_command_bus.py` verifica ejecucion de comandos de elementos y layout, errores con codigos estables, atomicidad ante resultados estructuralmente invalidos, ausencia de mutacion del documento previo, snapshots, undo/redo, invalidacion de redo al crear una rama, revision monotona, `updatedAt` monotono y serializacion JSON discriminada de comandos. Las pruebas confirman que diagnosticos semanticos no bloquean mutaciones estructuralmente validas.

## Frontend

Comandos:

```bash
npm run typecheck
npm run test
npm run build
```

Smoke test inicial:

- la aplicación monta;
- muestra el estado de fundación.

## Gate base sin infraestructura externa

`scripts/check.ps1` ejecuta pytest, compileall, Ruff y pip check en backend; typecheck, Vitest y build en frontend. Falla ante cualquier comando nativo con código de salida distinto de cero.

## Checks de integración con PostgreSQL

Configuracion de desarrollo validada: PostgreSQL local de Windows en `localhost:5432`, base `examen_sw1`, usuario `postgres`. Para comprobarla:

```bash
curl http://localhost:8000/health/db
```

Docker es opcional. Si se usa `docker compose up -d db`, el puerto host es `55432` y el servicio mantiene `5432` dentro del contenedor.

Tambien se valida el estado de migraciones con:

```bash
alembic check
```

El resultado esperado es HTTP 200 con `{"status":"ok","database":"postgresql"}`. Si PostgreSQL no esta disponible, el endpoint devuelve HTTP 503 sin afectar `/health`.

## E2E

El producto define Cypress, pero los escenarios E2E reales deben añadirse cuando existan flujos funcionales que probar. No se inventan flujos del dominio en la fundación.

## Regla

Cada CU debe añadir o actualizar pruebas que correspondan a sus criterios de aceptación.

### CU-08 - autenticacion y ownership

Las pruebas cubren registro normalizado, email duplicado, hash Argon2, login correcto/incorrecto, JWT invalido/expirado, `/auth/me`, proteccion Bearer y aislamiento de proyectos entre dos usuarios para listado, lectura, comandos, Undo y Redo. Frontend cubre formulario login/registro, bootstrap, token persistido, header Authorization, logout y limpieza tras 401.

Evidencia final CU-08: backend `pytest` 171 passed (2 warnings externos), `compileall`, Ruff y `pip check`: OK; frontend typecheck, 45 pruebas y build: OK; `scripts/check.ps1`: OK; `alembic upgrade head` aplicado y `alembic check`: sin operaciones nuevas.

### CU-09 - colaboradores

Las pruebas backend verifican que un editor puede leer y ejecutar la ruta de mutacion, un viewer queda bloqueado con `PROJECT_ACCESS_FORBIDDEN`, y solo el owner lista y cambia colaboradores. La regresion CU-08 conserva el ocultamiento `404` para usuarios sin membership. Frontend conserva sus pruebas de API/store y valida los tipos que incluyen `effectiveRole`.

Evidencia final CU-09: backend `pytest` 173 passed (2 warnings externos), Ruff y compileall: OK; frontend typecheck, 45 pruebas y build: OK; `alembic upgrade head` aplico `20260922_03` y `alembic check` no detecta operaciones nuevas.

### CU-06 - Puente temporal del editor

El Incremento 1 agrega pruebas backend para crear/consultar sesiones en memoria, ejecutar un `UmlCommand` real y reutilizar Undo/Redo de CU-05. Tambien comprueba errores HTTP estables para sesion inexistente y comandos rechazados. En frontend, Vitest cubre el cliente HTTP y el store Pinia para confirmar que envia comandos al backend y reemplaza su proyeccion con la respuesta, sin aplicar mutaciones UML locales.

No requiere PostgreSQL. Los resultados reales se registran en `CU-06-uml-canvas.md` despues de ejecutar el gate.

### CU-06 - Incremento 2 canvas de lectura

Se agregan pruebas deterministas para `ProjectDocument -> Node[]/Edge[]`, incluyendo uso de `DiagramLayout`, fallback visual, multiplicidades y direccion de generalizacion. El nodo UML se prueba como componente independiente. La prueba de `App` usa transporte mockeado para verificar que el workspace inicia una sesion y muestra el canvas vacio sin depender del backend real.

El gate debe confirmar ademas que desaparecen los warnings previos de componentes Vuetify no resueltos.

### CU-06 - Incremento 3 editor mutable

Se agregan pruebas puras para creacion de elementos/multiplicidades y auto-layout `d3-dag`, se actualiza el mapper para nodos arrastrables y marcadores UML, y `App.spec.ts` verifica que `Nueva clase` termina enviando `addElement` mediante el cliente del editor.

La validacion manual final debe crear al menos dos clases, editar atributos/operaciones, crear una relacion, mover una clase, ejecutar Undo/Redo, auto-organizar y confirmar que revision/estado cambian sin errores de consola.

### Evidencia final CU-06

- backend: 139 passed, 2 warnings externos;
- frontend: 22 passed en 9 archivos;
- typecheck: OK;
- build: OK;
- Ruff: OK;
- pip check: OK;
- `scripts/check.ps1`: OK;
- prueba manual: crear/editar clases, atributos y operaciones, relacion, drag con revision, Undo/Redo y auto-layout.

El warning de chunks Vite mayores a 500 kB se registra como optimizacion futura y no bloquea CU-06.

### Review PR #1 de CU-06

Cobertura agregada antes del merge:

- eviction LRU del bridge temporal de sesiones, excluyendo sesiones con requests activas;
- serializacion de accesos concurrentes sobre una misma sesion;
- preservacion de borradores dirty del inspector frente a revisiones externas;
- resincronizacion del inspector cuando el borrador esta limpio;
- asercion de layout jerarquico para una relacion dirigida, de modo que el fallback no pueda pasar la prueba principal de `d3-dag`.

### CU-07 - Incremento 1 persistencia base

Las pruebas unitarias de persistencia verifican el round-trip `ProjectDocument -> ProjectRecord -> ProjectDocument` con metadata, miembros, relacion, layout, UUIDs, revision y timestamps. Las pruebas API cubren creacion con owner temporal generado en backend, listado resumido, lectura validada y `PROJECT_NOT_FOUND`. No existe una base PostgreSQL de test aislada configurada, por lo que estas pruebas no ejecutan operaciones destructivas contra `examen_sw1`; `alembic upgrade head`, `alembic check` y el flujo HTTP real contra PostgreSQL son gates manuales de integracion.

### CU-07 - Incremento 2 mutaciones persistentes

Las pruebas API usan un repositorio transaccional en memoria para verificar execute, layout, relacion, Undo/Redo, revision y timestamps, comandos invalidos, proyecto inexistente, conflicto de revision, CAS sin fila actualizada, serializacion de dos requests mediante lock por proyecto, invalidacion de cache por conflicto/fallo de commit e historial vacio tras limpiar cache. La validacion manual PostgreSQL confirma command, Undo, Redo, reconstruccion de documento tras reinicio y Undo limitado a operaciones de la nueva instancia.

### CU-07 - Incremento 3 editor persistente

Las pruebas frontend cubren listado, creacion, apertura y cambio de proyectos, envio centralizado de `baseRevision`, respuesta autoritativa, Undo/Redo y recuperacion ante `PROJECT_REVISION_CONFLICT` sin confundir errores UML. Las pruebas existentes de canvas, relaciones, auto-layout e inspector dirty se mantienen. Al retirar `/editor/sessions`, se eliminan solamente sus pruebas exclusivas; la suite backend conserva dominio, persistencia, CAS y Undo/Redo.

### Evidencia final CU-07

- backend: `pytest` 150 passed, 2 warnings; `python -m compileall app`, `ruff check .` y `pip check`: OK;
- frontend: `npm run typecheck`: OK; `npm test`: 27 passed; `npm run build`: OK;
- global: `scripts/check.ps1`: OK;
- PostgreSQL: `python -m alembic check` informa `No new upgrade operations detected.` y `GET /health/db`: 200 OK;
- prueba manual humana final aprobada: crear y abrir proyecto, clases, atributos, relacion, movimiento/layout, auto-layout, inspector, Undo/Redo y recuperacion de clases, atributos, relaciones y layout despues de reiniciar FastAPI. Una nueva operacion posterior al reinicio y su Undo/Redo tambien fueron aprobados.

### UML Editor Completeness - relaciones visuales

Las pruebas de frontend verifican los cuatro tipos de relacion, los markers UML, multiplicidades por extremo, self-loops seleccionables con curva lateral, ausencia de multiplicidades en generalization y la exclusion del origen como destino de una generalization tanto en dialogo como en inspector. Tambien cubren el auto-layout que ignora self-loops sin quitarlos del documento, y la preservacion de borradores dirty del inspector.

Las pruebas de backend de integridad de relaciones cubren creacion, actualizacion, eliminacion, Undo/Redo, persistencia y reapertura de las cuatro relaciones, incluidas autorrelaciones permitidas, junto con el rechazo autoritativo de `GENERALIZATION_SELF_REFERENCE` y `GENERALIZATION_CYCLE`.

### CU-25 - Incremento 1, parte local (2026-11-06)

Los tests nuevos usan BSON real y dobles PyMongo para comprobar round-trip de semántica/layout/metadatos/UUID/fechas con microsegundos, identidad inconsistente, exceso de 16 MiB, inserción duplicada sin reemplazo, ausencia de upsert, transición de revisión, contrato CAS, fallos de almacenamiento, timeouts, URI protegida y limpieza exclusiva del UUID de prueba. No se presentan como pruebas de concurrencia/atomicidad de un servidor Mongo real.


- `scripts/check.ps1` fuera del aislamiento: **PASS**.
- Backend: **207 passed**, 2 warnings externos deprecados de Starlette/httpx/AnyIO; **28 pruebas nuevas** CU-25.
- Backend `compileall app`, `ruff check .` y `pip check`: **PASS**.
- Frontend: typecheck **PASS**, **46 tests passed / 13 archivos**, build **PASS**. Warning de chunk >500 kB preexistente, sin ampliación de frontend en este CU.
- Prueba CLI sin configuración cloud: **NOT RUN / exit 2**, comprobado; no es evidencia de servidor Mongo.
- Manual cloud, concurrencia real y reinicio completo: **pendientes**, no aprobados ni sustituidos por mocks.
- Entorno: Windows 11 (10.0.26300), Python 3.13.5, PyMongo 4.19.0. Sin benchmark IA aplicable.

El intento inicial dentro del aislamiento de Windows se bloqueó al crear el socket interno de asyncio usado por TestClient. Se interrumpió y se ejecutó el gate fuera del aislamiento, donde terminó correctamente. No se cambió código de aplicación para esquivar esa limitación. Se corrigieron los fixtures nuevos (visibilidad y dimensiones requeridas) y formato Ruff antes del gate final.

Incremento 1 permanece abierto hasta la prueba cloud de docs/deployment/NOSQL-CU25.md. No avanzar a incrementos 2/3 con esa verificación obligatoria pendiente. No se modificaron rutas SQL, datos ni frontend.

## Continuación: prueba de concurrencia preparada (2026-11-06)

Dentro del incremento 1 de CU-25 se amplió la CLI: fixture UML no vacío con dos clases, atributo, asociación, multiplicidades, layout y metadata; dos clientes independientes compiten por la misma revisión mediante ThreadPoolExecutor/Barrier. Debe aceptarse exactamente un candidato; la recuperación con cliente nuevo compara el documento ganador completo. El resultado real cloud sigue NOT RUN; el informe solo emitirá concurrentRevisionRejected=PASS tras comprobarlo en servidor.

Se agregaron cuatro pruebas locales: round-trip del fixture, rechazo de cero/dos ganadores y uso de dos clientes con recuperación del candidato aceptado. Los dobles de cliente no demuestran concurrencia de MongoDB real.

Verificación ejecutada tras estos cambios: **211 pruebas backend PASS**, dos warnings externos existentes; **32 pruebas locales CU-25** en total. Ruff, compileall app y pip check: **PASS**. Frontend no modificado; su gate anterior de 46 pruebas/typecheck/build sigue siendo evidencia histórica y no se reejecutó en esta continuación. Sin benchmark IA aplicable, sin migración, sin commit/push. Incremento y CU siguen abiertos por prueba cloud pendiente; no se inició otro CU.

## Atlas preparado y configuración local protegida (2026-11-06)

Se verificó el panel Atlas tras el registro personal del usuario. Se creó el cluster `cu25-pruebas`, opción Free ($0/h mostrado), proveedor AWS, región São Paulo/sa-east-1. El panel lo mostró ACTIVE y versión 8.0.37; backups y autoscaling OFF. No se cargaron datasets de ejemplo ni se contrataron tiers pagos.

Se preparó un usuario limitado `cu25_probe`: readWrite únicamente sobre `examen_sw1_cu25_probe`, acceso restringido a ese cluster, temporal por una semana. El usuario introdujo personalmente la contraseña y confirmó Add User; se verificó su presencia y roles en la lista. El agente no conoce ni registró la contraseña.

Regla de red preparada, sin confirmar: solo la IP pública actual del equipo durante seis horas. Se solicitó aprobación puntual por tratarse de acceso cloud. No se autorizó 0.0.0.0/0 ni se creó API key. Prueba cloud aún NOT RUN hasta regla aplicada y credencial configurada localmente.

Nuevo `app.db.mongo_configure`: pide contraseña oculta en terminal interactiva, codifica caracteres reservados, escribe conexión en backend/.env mediante reemplazo atómico y preserva el resto de ajustes. Rechaza entrada no interactiva para evitar eco de contraseña, hostname ajeno a Atlas y escritura incompleta. No se ejecutó con credenciales reales.

Se añadieron seis pruebas. Regresión ejecutada: **217 backend PASS**, dos warnings externos existentes; Ruff, compileall y pip check PASS. Frontend sin cambios, sin nueva ejecución de su gate. Incremento 1 y CU-25 siguen abiertos; sin migración ni inicio de otros CUs, sin commit/push.

## Incremento 1 cerrado; inicio del incremento 2 (2026-11-06)

Atlas mostró la regla /32 actual Active con expiración de seis horas, según autorización puntual del usuario. Se obtuvo el hostname del cluster desde Connect/PyMongo. El usuario configuró la contraseña personalmente en la terminal; backend/.env está excluido de Git.

Primer intento cloud: FAIL, código Atlas 8000, autenticación rechazada. Se diagnosticó solo tipo/código y banderas seguras, sin exponer URI ni contraseña. El configurador ganó --verify: comprueba autenticación antes de reemplazar .env y permite hasta tres correcciones ocultas. Nueve pruebas del configurador; regresión **220 backend PASS**, dos warnings externos; Ruff, compileall y pip check PASS.

Después de corregir la credencial, prueba real ejecutada: **PASS** a las 2026-11-07T01:36:21.743247Z (2026-11-06 21:36:21, America/La_Paz), revisión final 2. roundTrip, compareAndSwap, staleRevisionRejected, concurrentRevisionRejected y freshClientRecovery PASS. UUID temporal f72cdaaf-7ff8-467a-b697-57361cbaa4fd; limpieza de ese UUID completada antes de emitir PASS. Servidor Atlas 8.0.37 según panel; Python 3.13.5/PyMongo 4.19.0. Base examen_sw1_cu25_probe. HEAD c3bbdc34af1b87e3c2e832af8c619122bdc33a18 con cambios sin commit; la prueba corresponde al árbol de trabajo, no a ese commit limpio.

Incremento 1 cerrado con evidencia local y cloud. Se inicia incremento 2 autorizado: adaptación de usuarios/proyectos/memberships y API; no se inicia otro CU ni se modifica SQL existente por anticipado. El cambio definitivo y migración siguen para incremento 3.

## Incremento 2 cerrado (2026-11-06)

MongoStore integrado mediante selección PERSISTENCE_BACKEND sin cambios en rutas/payloads frontend. Usuarios e índice único de correo normalizado; proyectos canónicos y memberships privadas en una sola envoltura. CAS comprueba permiso EDITOR/owner y revisión en la misma escritura; memberships no contaminan UML/layout. Adaptadores SQL preservados y modo por defecto todavía PostgreSQL. Cliente Mongo reutilizado/cerrado con ciclo de vida FastAPI, health del almacenamiento seleccionado, errores PyMongo redactados 503 y exceso BSON 413 con invalidación de bus.

Pruebas nuevas: siete escenarios API ejecutados sin red con MongoMock y también contra Atlas real con CU25_LIVE_TESTS=1. Cubren registro/login, unicidad normalizada, owner/editor/viewer/outsider, listado compartido, comandos/conflictos, Undo/Redo, XMI, revocación/downgrade, rechazo atómico tras revocación, fallo de almacenamiento y selección de backend. Colecciones temporales cu25_<UUID>_users/projects creadas y eliminadas en examen_sw1_cu25_probe; no se tocaron colecciones ni datos de PostgreSQL.

Gate final scripts/check.ps1 PASS: **227 backend**, 2 warnings externos; compileall, Ruff y pip check PASS; **46 frontend / 13 archivos**, typecheck y build PASS, warning preexistente de chunk >500 kB. Atlas: **7 escenarios API PASS**; son integración automatizada sobre servidor real, no prueba humana de interfaz. Se corrigió el orden del test Undo/Redo: provocar conflicto antes de Undo invalida su caché según comportamiento anterior; no se cambió esa semántica. Se limitaron cambios de formato a archivos afectados.

Incrementos 1/2 cerrados; incremento 3 pendiente de corte/recuperación y decisión del usuario sobre trasladar datos SQL existentes o iniciar datos nuevos conservando SQL intacto. La pregunta de conservación sigue pendiente. No se inicia otro CU ni se presume aprobado subir datos personales reales. Sin commit/push.


## CU-25 incremento 3: cierre medido (2026-11-06)

Gate scripts/check.ps1 PASS: 235 backend y 46 frontend (13 archivos), Ruff, compileall, pip check, typecheck y build PASS. Persisten dos warnings externos de Starlette/httpx y AnyIO, y warning Vite de chunk >500 kB. Ocho pruebas nuevas de migración cubren integridad/checksum, respaldo exclusivo, identidad/hashes/permisos/legacy owners, idempotencia, conflictos previos a escritura y recuperación tras inserción parcial.

Prueba operativa real: pg_dump 17.6 restaurado en base temporal y comparado; ensayo Atlas e idempotencia; corte de 3 usuarios/15 proyectos/2 permisos; source-check antes/después; autenticación/autorización HTTP, reinicio completo, recuperación, comandos nuevos/Undo/Redo. Registros y originales comparados, datos temporales limpiados. Resultado artifacts/cu25/cutover-result.json (privado). Trece ownerIds legacy sin cuenta fueron preservados, no reparados. Undo previo sigue efímero. No se ejecutó una nueva prueba humana del frontend ni benchmark IA. Ver CU-25 y deployment/NOSQL-CU25.md para límites y recuperación.


## CU-10: evidencia 2026-11-07

Incremento backend: 241 backend/46 frontend y gate completo PASS. Incremento cliente/carrera concurrente: scripts/check.ps1 PASS, **242 backend/55 frontend (14 archivos)**, Ruff/compileall/pip check/typecheck/build. Warnings externos y chunk Vite preexistentes. Siete pruebas backend y nueve frontend nuevas; escenarios y límites en CU-10.

Smoke aislado HTTP+WebSocket TCP con dos clientes: deltas persistidos, revisión obsoleta, reconexión, downgrade y revocación PASS a las 11:44:19 Bolivia. MongoMock temporal, no Atlas; servidor apagado. Script/resultado ignorados en artifacts/cu10. Ping Atlas falló por timeout; control visual no inicia (os error 3); renovación IP autorizada, confirmación Active y aceptación visual pendientes. No se marca DONE ni se avanza a CU-11.


## CU-11: evidencia 2026-11-07

Inc.1: gate 247 backend/55 frontend PASS. Inc.2 final: scripts/check.ps1, **248 backend/61 frontend (15 archivos)**, Ruff/compileall/pip check/typecheck/build PASS. Warnings finales: 88 de datetime.utcnow interno de MongoMock al consultar TTL y dos externos previos; chunk Vite existente. Seis pruebas backend, seis frontend nuevas y señal de edición añadida al test de inspector. Casos detallados en CU-11.

Smoke aislado HTTP+WebSocket TCP: dos sesiones, cursor remoto, documento/revisión inalterados y cleanup PASS; MongoMock, no Atlas. Resultado artifacts/cu11/wire-result.json a las 12:38:28 Bolivia. Datos/servidor temporales retirados. Aceptación visual/Atlas diferida como deuda por petición explícita del usuario; no se afirma validación cloud ni multiworker. No se modificaron datos reales.


## CU-26: evidencia 2026-11-07

Inc.1 gate 253 backend/61 frontend PASS, tras corregir variable de test sin uso. Inc.2 gate 257 backend/61 frontend PASS, luego 10 pruebas específicas + Ruff/compileall para proyección/paginación de 55 eventos. Inc.3 gate 258 backend/68 frontend, estático/build PASS; prueba de reintento se corrigió para esperar el DOM. Ver documento CU-26 para gate final tras reservar IDs de actividad.

Smoke HTTP+WebSocket TCP: dos clientes, mensaje compartido y actividad atribuida, reinicio Uvicorn/caché vaciada/nuevo adaptador, historial recuperado, reintento idempotente y entrada tardía PASS a las 12:55:50 Bolivia. MongoMock se mantuvo como almacenamiento entre servidores; no equivale a proceso MongoDB reiniciado ni Atlas. Resultado artifacts/cu26/wire-result.json; servidores/datos temporales retirados. Sin prueba visual/cloud ni benchmark IA; deuda diferida por usuario, no aceptación aprobada.


Gate final CU-26 tras separación de IDs: **258 backend/68 frontend (16 archivos)**, Ruff/compileall/pip check/typecheck/build PASS. Backend 94 warnings medidos: 92 MongoMock TTL y 2 externos previos; chunk Vite existente. Markdown (12 archivos/enlaces/UTF-8) y git diff --check PASS. Aceptación cloud/visual diferida, no aprobada.

Smoke CU-26 repetido tras los IDs reservados: PASS 2026-11-07 13:00:32 Bolivia; recibo local actualizado, mismos límites MongoMock.


## Reanudación de funciones antiguas 2026-11-07

CU-21: inc.2 gate 270 backend/68 frontend; inc.3 final **277 backend/73 frontend**, Ruff/compileall/pip check/typecheck/build PASS. 90 warnings (88 MongoMock TTL y 2 externos previos); chunk Vite existente. Smoke HTTP TCP loopback con MongoMock, proyecto nuevo/owner, original intacto, round-trip semántico y error sin escritura PASS a las 13:13:51 Bolivia, artifacts/cu21/wire-result.json. Aceptación visual/EA real pendiente; XML sintético no la acredita. No IA/benchmark aplicable.

CU-09: inc.2 gate 282 backend/73 frontend; inc.3 final **282 backend/80 frontend en 18 archivos**, Ruff/compileall/pip check/typecheck/build PASS. 94 warnings (92 MongoMock TTL y 2 externos previos), chunk existente. Cinco pruebas backend y siete frontend nuevas para código/correo/roles/vigencia/cancelación, canje atómico/carreras y UI/errores. Smoke HTTP TCP con MongoMock PASS a las 13:27:26 Bolivia, artifacts/cu09/wire-result.json: registro posterior, acceso VIEWER, replay, revocación y cancelación sin cambiar UML/revisión. Servidores/datos de prueba retirados; sin modificaciones a usuarios/datos reales ni mensajes externos. QA visual/cloud diferida, no aprobada. Git no ejecutado.

Cierre documental de reanudación: 11 Markdown/enlaces/UTF-8 y git diff --check PASS tras retirar una línea vacía final. Secretos y recibos de pruebas siguen ignorados por Git.


## CU-13: modelo relacional, 2026-11-07

Inc.1 gate 296 backend/80 frontend PASS tras corregir una línea larga de Ruff y repetir gate. Inc.2 306 backend/80 frontend PASS. Inc.3 final scripts/check.ps1 **309 backend/86 frontend en 20 archivos**, Ruff/compileall/pip check/typecheck/build PASS. 98 warnings (96 de datetime.utcnow interno de MongoMock TTL + 2 externos previos), chunk Vite >500 kB existente. 24 tests mapper, 3 API y 6 frontend nuevos: tipos/PK/perfiles/enums, nombres/determinismo/immutabilidad, relaciones/autorrelaciones/nulabilidad/UNIQUE/índices, composición y obligaciones de runtime, JOINED/herencia múltiple, permisos, diagnósticos, revisión obsoleta y errores.

Smoke HTTP TCP loopback con MongoMock PASS 2026-11-07 14:48:32 Bolivia: 3 clases/2 relaciones, PK Long heredada JOINED, composición, vista sin escritura y mismo modelo tras mover nodo (sourceRevision cambia). artifacts/cu13/wire-result.json; servidor/datos temporales retirados. No PostgreSQL DDL ejecutado, Atlas ni UI manual. QA visual/cloud diferida por usuario, no aprobada. No benchmark IA, cambios de tecnología ni commit/push.

## Preparación de revisión manual, 2026-11-07

Perfil explícito de prueba: backend/tests/manual/qa_server.py y frontend/vite.qa.config.ts; scripts/dev-qa.ps1 y stop-qa.ps1. Tres cuentas ficticias y MongoMock aislado, sin fallback de producción ni cambios de .env. Guía: [revisión manual](MANUAL-REVIEW.md). Gate final: 311 backend/86 frontend (20 archivos), Ruff/compileall/pip check/typecheck/build PASS; 94 warnings externos (92 MongoMock TTL y 2 previos), aviso de tamaño Vite existente. Primera ejecución falló por inspeccionar route.path en un _IncludedRouter; se corrigió el test para inspeccionar OpenAPI y se repitió el gate completo. Analizador PowerShell de ambos scripts y git diff --check PASS.

Smoke HTTP/WebSocket real PASS 2026-11-07 15:04:15 Bolivia: banner, destino API aislado, tres logins/roles, dos tablas relacionales y frames snapshot/presence/conversation con Origin correcto. Recibo ignorado artifacts/manual-qa/readiness.json. No es prueba visual ni Atlas. Los servidores temporales quedaron activos en localhost:5175/8001 para revisión del usuario. El script de detención fue analizado, sin prueba de detención en vivo aún.

## CU-14 incremento 1 — 2026-11-07

25 pruebas nuevas del renderer, gate completo 336 backend/86 frontend (20 archivos), Ruff/compileall/pip check/typecheck/build PASS. 94 warnings backend externos y advertencia Vite previos. Proyecto generado con Java Temurin 21.0.12.1+1-LTS / Gradle 9.5.1 / Boot 4.1.2 / springdoc 3.2.0: build/JAR y 1 JUnit de validación Jakarta PASS. Wheel aislado e inclusión de 11 templates PASS; intento previo sin aislamiento carecía de setuptools y fue corregido usando el aislamiento estándar. Recibo ignorado artifacts/cu14/foundation-result.json; reproducción en CU-14. No se ejecutó SQL ni CRUD todavía, no se modificaron datos reales ni el servidor de QA visual.

## CU-14 incremento 2 — 2026-11-07

Gate final 342 backend/86 frontend (20 archivos), Ruff/compileall/pip check/typecheck/build PASS; 94 warnings externos y aviso Vite previos. Seis tests nuevos de CRUD/contratos/metadatos y límites, más 25 del renderer. Compilación real Gradle/Java PASS y 51 comprobaciones HTTP contra PostgreSQL 17.6 PASS a las 16:01:50 Bolivia, incluyendo reinicio JVM/recuperación. Base temporal propia creada y eliminada, legacy/Atlas intactos. Primera ejecución detectó PropertyReferenceException en ordenamiento por guion bajo; se corrigió el símbolo Java, añadió regresión y repitió todo. Recibo artifacts/cu14/crud-result.json. Wheel con 17 templates verificado. Reproducción y límites en CU-14; no aceptación visual de una descarga/UI aún inexistente.

## CU-18 incremento 1 — 2026-11-07

Gate final scripts/check.ps1 384 backend/86 frontend (20 archivos), Ruff/compileall/pip check/typecheck/build PASS. 42 tests nuevos de contratos/resolver sin escritura/contexto, transporte Gemini controlado/redirects/errores/JSON inválido y duplicado, guardado privado y métricas A/B. 90 warnings externos (88 MongoMock TTL y 2 previos), aviso Vite existente. Dataset doce casos; runner fixtures-only ejecutado con hardware cliente, commit/dirty/hashes y estado NOT_RUN, cero llamadas y métricas LLM null. No equivale a inferencia; clave/benchmark real pendientes. Sin nuevos endpoints/UI, Atlas o datos reales modificados. Ver CU-18 y deployment/GEMINI-CU18.md.

## CU-18 integración grupal y formulario — 2026-11-07

Gate final scripts/check.ps1 402 backend/96 frontend (22 archivos), Ruff/compileall/pip check/typecheck/build PASS. 18 pruebas API nuevas: permisos/revisión/contexto compartido, JWT/acceso/cambios en vuelo, idempotencia y carrera de finalización antes de reserva, promoción recuperable, lease/BSON, duplicado inmutable, dos WebSockets editor/observador y reconexión. Nueve pruebas panel/API y una de historial UI nuevas (diez frontend). Inicialmente falló cobertura del harness (nuevas rutas ausentes); se incluyeron. UI detectó clonación de array reactivo de participantes; corregida con objetos planos. Correcciones y gate intermedio en CU-18.

Tras añadir atribución de eventos AI al contexto: 60 pruebas específicas, Ruff/compileall PASS; fixture-only de doce casos NOT_RUN, cero llamadas/métricas LLM null. Smoke TCP HTTP/WS con instancia QA nueva aislada PASS a las 16:59:01 Bolivia: status sin clave/401/503/403, snapshot/conversación y documento intacto; artifacts/cu18/http-readiness.json. Sin proveedor real ni Atlas, sin aceptación visual humana. El proceso QA previo y sus datos temporales permanecen; no se actualizó ese backend en vivo.

## Vista manual independiente CU-18 — 2026-11-07

Readiness HTTP de frontend5176/API8002 PASS 19:30:52 Bolivia: banner temporal, módulo de formulario servido, VITE_API_BASE_URL correcto, CORS para 5176, login ficticio y status configured=false. Cero llamadas a IA; storage MongoMock independiente. Instancia previa no reiniciada. Config, recibos y helper propios ignorados; parser PowerShell del helper PASS, no se detuvo para permitir revisión. Runtime visual falló al iniciar; aceptación UI continúa pendiente. No cambios de implementación ni nueva ejecución de las cifras históricas 402/96.
