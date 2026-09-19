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

- backend: 138 passed, 2 warnings externos;
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

- eviction LRU del bridge temporal de sesiones;
- preservacion de borradores dirty del inspector frente a revisiones externas;
- resincronizacion del inspector cuando el borrador esta limpio;
- asercion de layout jerarquico para una relacion dirigida, de modo que el fallback no pueda pasar la prueba principal de `d3-dag`.
