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

## Base de datos

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
