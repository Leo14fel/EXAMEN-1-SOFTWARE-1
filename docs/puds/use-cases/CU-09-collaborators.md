# CU-09 - Administrar acceso de colaboradores

**Estado: IMPLEMENTED, tres incrementos; prueba visual/cloud pendiente.** Colaboradores anteriores + invitaciones/tokens/vencimiento + interfaz. Reanudación autorizada el 2026-11-07 por petición expresa de completar funciones antiguas. No se afirma DONE ni validación externa no ejecutada.

## Comportamiento actual

Se mantienen owner implícito y memberships EDITOR/VIEWER. Owner puede agregar un usuario registrado directamente, cambiar rol o quitar acceso, y ahora también crear invitaciones por correo/rol con duración de 1 a 168 horas (24 por defecto), listarlas y cancelarlas. Destinatario se registra/inicia sesión con ese correo y canjea el código autenticado; recibe la membership indicada sin modificar revisión/UML/layout. No se envían correos ni mensajes a terceros automáticamente.

Token generado con secrets.token_urlsafe(32), entregado una vez por POST de creación. Persistencia privada _invitations dentro del proyecto conserva solo SHA-256 del secreto, correo, rol y fechas UTC; no se expone en ProjectDocument ni al listar invitaciones. El código incluye proyecto/UUID invitación/secreto y se transmite en body POST, no en URL ni localStorage. Interfaz mantiene el código recién creado en memoria mientras está abierta; puede copiarse o seleccionarse manualmente si clipboard no está disponible. No se recupera desde el listado.

Canje comprueba correo autenticado, hash con compare_digest, vigencia y rol. Concesión de membership y consumo del token ocurren en la misma escritura Mongo condicionada por hash/email/fecha/rol y ausencia de membership. Una cancelación concurrente impide conceder acceso. Dos canjes simultáneos tienen un ganador. Un código antiguo no rebaja/sobrescribe un rol ya existente y nunca crea membership para el owner. Reutilización/secreto incorrecto/correo distinto no concede acceso. Expiración aplica al código sin usar; una membership aceptada continúa hasta que owner cambie rol o revoque. Fechas vencidas se excluyen del listado; no hay job de limpieza ni expiración automática de memberships. El tamaño BSON del proyecto se comprueba al crear y sigue limitado a 16 MiB.

## Contratos definidos aquí

- POST /projects/{id}/invitations: owner, email/role/expiresHours → datos públicos y token (201).
- GET /projects/{id}/invitations: owner, pendientes vigentes sin secreto/hash.
- DELETE /projects/{id}/invitations/{invitationId}: owner, cancela (204).
- POST /project-invitations/accept: usuario autenticado, token → projectId/effectiveRole.

Errores: 404 para recurso/token/correo no visible, 410 vencido, 409 conflicto/consumido/cancelación concurrente/miembro ya existente, 422 datos inválidos. Mongo y la configuración normal NoSQL se mantienen; SQL legacy no agrega invitaciones, devuelve 503 en este flujo y conserva sus contratos anteriores. Se reutilizan el validador de email, ProjectRole y autorización de CU-08/09.

## Incrementos y evidencia

1. Roles/colaboradores: evidencia histórica más abajo.
2. Invitaciones/tokens: gate 282 backend/73 frontend, Ruff/compileall/pip check/typecheck/build PASS. Cinco pruebas backend nuevas cubren restricciones de propietario, email/validación, hash/secreto no listado, registro posterior, canje/replay, expiración, cancelación, carreras y conservación de documento/revisión.
3. Interfaz: gestión en diálogo Colaboradores del propietario; «Canjear invitación» en toolbar autenticada. Si el canje fue aceptado pero falla cargar proyectos, se informa acceso concedido y se vacía el código, sin invitar a repetir un canje ya consumido. Pruebas de componentes y API verifican creación/listado/cancelación, canje/apertura, errores, identidad/token fuera de URL y vigencia/rol. **Gate final: 282 backend/80 frontend en 18 archivos**, Ruff/compileall/pip check/typecheck/build PASS. 94 warnings medidos (92 MongoMock TTL y 2 externos anteriores); chunk Vite >500 kB existente. Sin benchmarks IA aplicables.

Smoke HTTP TCP loopback con MongoMock temporal PASS: invitación antes de registrar destinatario, canje VIEWER, lectura, uso único, revocación owner, cancelación y UML/revisión intactos. Resultado artifacts/cu09/wire-result.json, 2026-11-07 13:27:26 Bolivia; script invitation-wire.py. Servidor y datos de prueba retirados. No se modificaron usuarios/proyectos reales ni Atlas, no se envió correo y no hubo commit/push.

## Aceptación y límites

Prueba visual pendiente: owner crea código para otro correo, copia y comparte personalmente; cuenta destinataria canjea, abre con rol y permite/rechaza edición según permiso; probar otro correo/vencido/cancelado; owner revoca colaborador. Prueba cloud/visual diferida por el usuario al priorizar desarrollo/pruebas locales, sin darla por aprobada. No se reemplaza verificación de email ni autenticación previa del producto. Próximo CU antiguo según dependencias: CU-13, generación relacional; resto de CU-13..17 y primer parcial siguen sin aceptación integral.

Cambios no confirmados conviven con otros CUs: revisar hunks y commits separados, no stage amplio. Preparación revisable (no ejecutada), solo hunks CU-09:

```powershell
git add -- backend/app/api/invitations.py backend/tests/api/test_invitations.py frontend/src/features/editor/invitations-api.ts frontend/src/features/editor/invitations-api.spec.ts frontend/src/features/editor/InvitationManager.vue frontend/src/features/editor/InvitationRedeem.vue frontend/src/features/editor/Invitations.spec.ts docs/puds/use-cases/CU-09-collaborators.md
git add -p -- backend/app/main.py backend/app/db/mongo_projects.py frontend/src/features/editor/EditorWorkspace.vue README.md docs/STATUS.md docs/TESTING.md docs/HANDOFF.md docs/PROJECT-CONTEXT.md docs/README.md docs/puds/use-cases/IMPLEMENTATION-ROADMAP.md docs/requirements/LEGACY-GAPS.md
git diff --cached
git commit -m "feat(cu-09): add expiring single-use project invitations"
git push -u origin feat/xmi-export
```

---

# Evidencia histórica CU-09

**Estado:** IMPLEMENTED - pendiente de prueba manual humana final.

## Implementado

- `project_memberships` relaciona un proyecto y usuario con rol `EDITOR` o `VIEWER`; el propietario se deriva siempre de `projects.owner_id` y no tiene membership propia.
- La migracion `20260922_03` crea el enum, tabla, claves foraneas con `CASCADE` e indice por usuario sin modificar proyectos legacy de CU-08.
- La abstraccion central `ProjectAccess` resuelve lectura, edicion y ownership. Propietarios y editores pueden mutar; viewers solo pueden leer; recursos sin acceso permanecen ocultos con `404`.
- Solo el propietario administra `GET/POST/PATCH/DELETE /projects/{project_id}/collaborators` mediante correo de un usuario registrado.
- `GET /projects` incluye proyectos compartidos y publica `effectiveRole` para cada resumen.
- El editor Vue muestra el rol efectivo, bloquea mutaciones de viewer y permite al propietario listar, agregar, cambiar rol y eliminar colaboradores.

## Evidencia

- Backend: `pytest` 173 passed (2 warnings externos), `ruff check app tests` y `python -m compileall -q app`: OK.
- Frontend: `npm run typecheck`: OK; `npm run test`: 45 passed en 13 archivos; `npm run build`: OK. El warning existente de chunk Vite mayor a 500 kB no bloquea el build.
- Migracion: `alembic upgrade head` aplico `20260922_03`; `alembic check`: `No new upgrade operations detected.`

## Limites

No se implementan invitaciones, tokens, expiracion ni realtime: pertenecen al alcance posterior definido por el roadmap.

## Continuidad documental del segundo parcial (2026-11-06)

Sin cambios de código ni nueva ejecución de las pruebas anteriores. Se mantiene IMPLEMENTED con manual final pendiente. El roadmap ahora registra explícitamente que invitaciones/tokens/expiración del alcance original no se implementaron. El siguiente CU propuesto es CU-25 para adaptar la persistencia antes de CU-10; no se adelanta realtime. Ver SECOND-PARTIAL y STATUS para requisitos y verificaciones de esta preparación.


## Reanudación autorizada 2026-11-07

El usuario pidió completar funciones antiguas; tras CU-21 se retoma solo CU-09. Implementación previa de colaboradores cuenta como incremento 1. Plan: incremento 2 invitaciones con token/cancelación/vencimiento y autorización atómica; incremento 3 interfaz y pruebas integradas. Sin envío automático de correos ni cambios a usuarios/datos reales. Pruebas visuales/cloud previas diferidas por usuario no se declaran aprobadas.

### Incremento 2 - DONE

Owner crea una invitación dirigida a correo, rol EDITOR/VIEWER y plazo de 1 a 168 horas. Token aleatorio secreto entregado solo una vez; persistir hash, no token. Usuario registrado con ese mismo correo lo canjea autenticado. Token de un uso, con vencimiento verificable y cancelable. Reserva privada dentro del proyecto Mongo permite comprobar token/email/vigencia y conceder membership en la misma escritura atómica, sin aumentar revisión UML. No sustituye las membresías existentes ni permite invitar al owner o cambiar roles por un token antiguo.

### Incremento 3 - IMPLEMENTED

Owner administra invitaciones y copia código; destinatario pega código desde el editor tras registrarse/iniciar sesión. No enviar mensajes a terceros. SQL legacy no añade este flujo, modo normal CASE Mongo. Enlaces/correo automatizado no son necesarios para canjear el token y quedan fuera de este incremento.

Inc.2 gate completo PASS: 282 backend/73 frontend, Ruff/compileall/pip check/typecheck/build. Cinco pruebas nuevas cubren hash/uso único, correo/roles/propietario, vencimiento/cancelación/secreto incorrecto, carrera de canje y cancelación atómica, registro posterior al crear invitación. CanonicalUmlModel no contiene _invitations. No aplica benchmark IA.
