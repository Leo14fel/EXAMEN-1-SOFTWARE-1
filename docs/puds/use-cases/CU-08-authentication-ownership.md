# CU-08 - Autenticacion, ownership y administracion de proyectos

**Estado:** IMPLEMENTED - pendiente de prueba manual humana final.

## Implementado

- `users`: UUID, email unico normalizado, `password_hash`, timestamps.
- `POST /auth/register`, `POST /auth/login` y `GET /auth/me` con Argon2 (`pwdlib`) y JWT Bearer (`PyJWT`).
- Todos los endpoints de `/projects` requieren usuario autenticado; listan solo propios y recursos ajenos devuelven `404 PROJECT_NOT_FOUND`.
- Los proyectos nuevos usan `current_user.id`; CAS no puede cambiar `owner_id`.
- Vue incorpora login/registro, bootstrap por `/auth/me`, logout local, JWT en `localStorage`, header centralizado y limpieza de sesión/editor al recibir 401.

## Migracion legacy

`20260921_02_create_users.py` crea `users` e `ix_projects_owner_id` sin modificar proyectos existentes. No hay FK de `projects.owner_id` a `users.id`: los UUID temporales de CU-07 no son usuarios verificables. Los proyectos legacy se preservan pero no son accesibles por usuarios nuevos hasta una migracion administrativa posterior. No se crean usuarios ficticios ni se reasignan propietarios.

## Limites

No hay refresh token, blacklist, recuperacion de password, invitaciones, memberships ni roles de colaboradores. `localStorage` es una decision MVP; una version endurecida debe usar cookies `HttpOnly` o equivalente. CU-09 es el siguiente paso.

## Evidencia

Las pruebas cubren auth, JWT invalido/expirado, endpoint protegido, ownership para lista/lectura/comando/undo/redo, CAS y regresion UML. Los resultados exactos se registran en `docs/TESTING.md`.
