# CU-10 - Editar colaborativamente en tiempo real

**Estado:** IMPLEMENTED - pendiente de prueba manual humana final.

## Implementado

- `GET` no se usa para realtime: `WebSocket /projects/{project_id}/realtime?token=<JWT>` autentica el token antes de aceptar y verifica el acceso persistido al proyecto. Una conexión sin token, con token inválido o sin membresía se cierra con política `1008`.
- `ProjectConnectionManager` centraliza conexiones async por proyecto y usuario. Distribuye `project.updated` con el `ProjectDocument` autoritativo a owners, editors y viewers conectados.
- Los comandos REST, undo y redo continúan siendo la única ruta de mutación. El broadcast se ejecuta exclusivamente después de CAS, `commit` exitoso y la respuesta autoritativa; conflictos y errores de persistencia no emiten eventos.
- Al eliminar una membresía, sus sockets de ese usuario y proyecto se cierran después del commit. Los viewers no obtienen ninguna vía de mutación y solo consumen actualizaciones.
- El store Vue abre una única conexión al abrir o crear un proyecto, cierra la anterior al cambiar de proyecto y al cerrar sesión, expone estado de conexión y reintenta sin duplicar sockets. Solo aplica un evento para el proyecto abierto cuya revisión sea estrictamente mayor; revisiones iguales o anteriores se ignoran.

## Evidencia

- Backend: `pytest` no inició porque el Python global no tiene instalados `fastapi` ni `sqlalchemy`; por ello tampoco se ejecutaron `ruff` ni `compileall` de la cadena dependiente.
- Frontend: `npm run typecheck`, `npm run test` (48 pruebas en 14 archivos) y `npm run build`: OK. El build conserva el warning preexistente de chunks mayores de 500 kB.
- Frontend format: `npm run format:check` falla sobre 38 archivos preexistentes del repositorio. La comprobación limitada a los siete archivos frontend tocados también falla porque la base no sigue la configuración Prettier actual; no se reformateó masivamente este CU.

## Prueba manual pendiente

1. Abrir el mismo proyecto como editor y viewer, ejecutar un comando en el editor y confirmar que el viewer recibe la revisión nueva sin poder mutar.
2. Eliminar el viewer desde el owner y confirmar el cierre inmediato de su WebSocket y que no recibe broadcasts posteriores.

## Límites

- No envía comandos por WebSocket ni implementa presencia, cursores o CRDT; pertenecen a CU-11 o posteriores.
