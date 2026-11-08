# CU-25 - Retomar proyectos sobre persistencia NoSQL cloud

**Estado: DONE.** Tres incrementos cerrados. Autorización del usuario: avanzar dentro del plan y conservar/trasladar los datos existentes. Cierre: 2026-11-06, America/La_Paz.

## Objetivo y alcance

Trasladar el estado CASE de PostgreSQL a MongoDB Atlas sobre AWS preservando usuarios, hashes de contraseña, ownership, permisos, UUIDs, revisiones, timestamps, UML y layout. Mantener FastAPI/Vue, validación y Command Bus. Sin conversación/IA/realtime/push ni generadores en este CU.

Referencias: product.md secciones 4, 6, 17, 19.1, 20 y 41; SECOND-PARTIAL RSP-07/08. Dependencias CU-07/08/09; se conserva exportación de CU-21. Las pruebas manuales humanas anteriores pendientes de CU-00/08/09 no se declaran cerradas por este trabajo.

## Incrementos (máximo tres)

### 1. Elegir y probar persistencia - DONE

Se seleccionó MongoDB Atlas/AWS + PyMongo 4.19.0 (ADR-lite 023). Cluster Free cu25-pruebas, AWS São Paulo, servidor 8.0.37 observado. Adaptador canónico, BSON lossless, CAS y configuración de prueba externa. La prueba cloud pasó roundTrip, compareAndSwap, staleRevisionRejected, concurrentRevisionRejected y freshClientRecovery a las 21:36:21 del 2026-11-06 en Bolivia. Dos conexiones compiten por la misma revisión y solo una gana. El documento de prueba se limpió.

La cuenta y contraseña fueron creadas personalmente por el usuario. cu25_probe tiene readWrite solo en examen_sw1_cu25_probe y ese cluster, temporal por una semana. Regla /32 actual autorizada por seis horas, verificada Active. No hubo acceso global, API key, tier pago ni secretos en Git/chat.

### 2. Adaptar usuarios/proyectos/permisos y API - DONE

MongoStore se integra en las funciones existentes de almacenamiento. La envoltura Mongo añade _memberships sin contaminar CanonicalUmlModel/DiagramLayout ni respuestas HTTP. Índice único de correo normalizado, hashes Argon2 y roles existentes. CAS comprueba permiso owner/editor junto a revisión; una revocación concurrente impide escribir. Cliente reutilizado por proceso, cierre en lifespan y health del backend seleccionado. Errores de almacenamiento redactados (503); límite BSON 16 MiB (413).

Siete escenarios API pasaron con MongoMock y también sobre Atlas real, con colecciones UUID temporales limpiadas: registro/login, unicidad, ownership/colaboradores, viewer/outsider, comandos, conflicto, Undo/Redo, XMI, revocación, fallos y selección de backend. Se mantuvieron rutas/payloads frontend y el camino SQL para respaldo/recuperación controlada. Gate: 227 backend/46 frontend, estático y build PASS.

### 3. Respaldar, migrar y demostrar recuperación - DONE

El usuario confirmó que necesita conservar datos. Inventario real: **3 usuarios, 15 proyectos, 2 memberships**. **13 proyectos tienen ownerId legado sin usuario registrado**; situación previa preservada sin reasignaciones ni cuentas ficticias. Permisos y visibilidad mantienen el comportamiento original.

- PostgreSQL real observado: 17.6. pg_dump 17 produjo artifacts/cu25/postgres-20261107T020534Z.dump (9.590 bytes). pg_restore pudo listar y restaurar el archivo en una base temporal; su contenido fue idéntico al snapshot lógico. Solo se retiró esa base temporal.
- Snapshot lógico de solo lectura, repeatable-read: artifacts/cu25/source-20261107T020534Z.json, con SHA-256, validación de UUIDs/referencias/unicidad y UML/layout. Incluye hashes y datos personales: archivo local excluido de Git, no compartirlo en chat.
- Ensayo Atlas en colecciones cu25_<UUID>_: 18 documentos insertados, segunda importación 0 insertados, comparación completa desde proceso nuevo PASS. Los permisos están embebidos en proyectos y no suman documentos aparte.
- Importación final a users/projects: 18 insertados; comparación completa PASS. source-check antes/después confirmó PostgreSQL sin cambios. No se sobrescriben documentos diferentes ni se fusionan identidades por correo. Un fallo parcial puede retomarse con el mismo snapshot; el destino queda fuera de servicio hasta verificarlo.
- PERSISTENCE_BACKEND=mongodb es ahora el valor por defecto y la configuración local. PostgreSQL sigue intacto, accesible solo por herramientas legacy/recuperación cuando se selecciona explícitamente. Sin dos backends de aplicación escribiendo a la vez: no había servicio en 8000 antes de iniciar el backend de este trabajo.
- Backend real iniciado en loopback: health/db mongodb; se verificaron auth/me, listados y lectura/denegación para los 3 usuarios sobre los 15 proyectos, comparando documentos completos y los 2 permisos.
- Reinicio real del proceso backend: proyecto temporal recuperado íntegro. Undo previo al reinicio no disponible según semántica efímera existente; nuevas operaciones, Undo y Redo funcionan. Se limpiaron proyecto temporal y colecciones de ensayo. Ver artifacts/cu25/cutover-result.json (PASS, 22:15:29 del 2026-11-06 en Bolivia).

## Pruebas y evidencia final

| Verificación | Resultado real |
|---|---|
| scripts/check.ps1 | PASS |
| Backend pytest | **235 passed**, 2 warnings externos deprecados |
| Backend Ruff / compileall / pip check | PASS |
| Frontend Vitest | **46 passed / 13 archivos** |
| Frontend typecheck / build | PASS; warning de chunk >500 kB preexistente |
| Prueba de almacenamiento Atlas y concurrencia | PASS |
| API sobre Atlas (7 escenarios) | PASS |
| Respaldo, restauración SQL temporal y comparación | PASS |
| Ensayo e importación idempotente / comparación completa | PASS |
| API real tras corte y reinicio de proceso | PASS |
| PostgreSQL source-check final | PASS: origen idéntico |
| git diff --check / exclusión de .env y artifacts | PASS |

Entorno: Windows 11, Python 3.13.5, PyMongo 4.19.0; PostgreSQL local 17.6, Atlas 8.0.37. HEAD c3bbdc34af1b87e3c2e832af8c619122bdc33a18 con árbol modificado: las pruebas corresponden al árbol sin commit, no a ese commit limpio. No se modificó LLM/VLM/STT, sin benchmark aplicable. La verificación manual de almacenamiento/API usó comandos reales; no se presenta como prueba humana del frontend.

## Problemas corregidos

Bloqueo de socketpair/asyncio en aislamiento Windows: gate HTTP ejecutado fuera de él. Primer password Atlas rechazado (8000): configurador con --verify y reintentos ocultos, corrección personal del usuario; jamás se imprimió la credencial. Fixtures nuevos completados con visibilidad/dimensiones requeridas. Test Undo/Redo reordenado para respetar invalidación del historial ante conflicto. Reinicio comprobó identidad/parentesco del proceso y hora UTC por ticks; no se detuvieron otros procesos. No se mezclaron cambios de formato de dominio/XMI.

## Límites, recuperación y continuidad

Los 13 proyectos legacy conservan su ownerId y su accesibilidad anterior; recuperarlos para un usuario específico necesita una decisión explícita, no forma parte de esta migración. No hay conversación persistente todavía (CU-26), ni realtime (CU-10), ni Undo/Redo persistente. Los accesos Atlas son temporales y se deben renovar/configurar para operación duradera en el CU de despliegue; la expiración de credenciales no elimina datos.

Antes de volver a SQL: congelar escrituras Mongo y comparar/reconciliar cambios posteriores al corte. Cambiar solamente la variable a SQL después de editar en Mongo perdería visibilidad de avances nuevos. El respaldo SQL fue restaurado y comparado en aislamiento; no se restauró sobre la base original. Ver deployment/NOSQL-CU25.md.

## Criterios de aceptación

- [x] NoSQL cloud seleccionado y probado, secretos externos.
- [x] Datos CASE operan en MongoDB sin depender de PostgreSQL para las rutas normales.
- [x] Usuarios/hashes, ownership, memberships, IDs, revisiones, timestamps, UML y layout preservados.
- [x] CAS y permisos atómicos, sin pérdida silenciosa ni éxito ante fallo de almacenamiento.
- [x] Respaldo/restauración aislada, importación repetible y reinicio real verificados.
- [x] API/editor/XMI conservan contratos; roles y regresión comprobados.
- [x] Pruebas, estático, build, evidencia manual aplicable y documentación actualizados.

## Git (no ejecutado)

Un solo CU implementado en estos cambios; documentación de requisitos y continuidad acompaña el cambio. Desde la raíz, para el árbol revisado al cerrar CU-25. **Nota posterior CU-10:** estos comandos amplios son históricos; no ejecutarlos con cambios de CU-10 presentes, porque mezclarían CUs. Preparar commits separados revisando hunks de archivos compartidos.

```powershell
git add -- README.md product.md compose.mongo-probe.yaml backend/.env.example backend/pyproject.toml backend/app backend/tests docs
git commit -m "feat(cu-25): migrate CASE persistence to MongoDB Atlas"
git push -u origin feat/xmi-export
```

No agregar backend/.env ni artifacts: contienen secretos o respaldo de datos personales y están excluidos de Git. No se hizo commit ni push automáticamente. Siguiente CU: CU-10 según PUDS.
