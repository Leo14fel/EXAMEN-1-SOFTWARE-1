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
