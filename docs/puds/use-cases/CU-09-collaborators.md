# CU-09 - Administrar acceso de colaboradores

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
