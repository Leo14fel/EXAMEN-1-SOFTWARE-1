# Handoff

## Último punto estable

CU-00 a CU-05 estan cerrados. El stack instalado es Vue 3 + TypeScript + Vite + Vuetify y Python + FastAPI + SQLAlchemy + Alembic. La evidencia de CU-05 vive en `puds/use-cases/CU-05-command-bus-undo-redo.md`.

## Próximo paso exacto

CU-06 esta IN_PROGRESS. El Incremento 1 conecta Vue con el UmlCommandBus mediante sesiones HTTP temporales en memoria; validar este puente antes de implementar la proyeccion Vue Flow del Incremento 2.

## Motivo de la reorganizacion

PUDS es la unica fuente de roadmap. El orden ahora garantiza validacion antes del Command Bus y Command Bus antes del canvas mutable. CU-09 administra membresías e invitaciones antes de CU-10 realtime; AWS queda en CU-23 y la aceptacion integral del MVP en CU-24.

## Dominio actual

`ProjectDocument` contiene UUID, metadata JSON-safe, ownerId estructural, revision, timestamps UTC, `CanonicalUmlModel` y `DiagramLayout`. El modelo canonico mantiene una union discriminada de clases y relaciones; association usa extremos neutrales, aggregation/composition van de todo a parte y generalization de hija a padre. Las multiplicidades son estructuradas, los UUID son globalmente unicos y el layout solo conserva posiciones y dimensiones de clases. `validate_uml_model` agrega diagnosticos semanticos sin mutar el modelo.

Toda futura mutacion debe recorrer `UmlCommand -> UmlCommandBus -> execute_uml_command -> ProjectDocument`; UI, canvas, IA y XMI no pueden modificar el documento directamente. El executor es puro y sin mutacion in-place. El bus encapsula su estado y entrega copias seguras a consumidores externos. Undo/Redo usa snapshots completos, conserva hasta 100 estados de undo y descarta el mas antiguo al superar el limite. La revision es monotona incluso en undo/redo, `updatedAt` no retrocede y un comando nuevo despues de undo invalida redo. Los errores usan codigos estables; diagnosticos semanticos de CU-04 no bloquean comandos estructuralmente validos. Eliminar una clase referenciada no hace cascada: se rechaza el comando de forma atomica.

## PostgreSQL actual

Desarrollo validado: PostgreSQL local de Windows en `localhost:5432`, base `examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Arranque y checks

```powershell
.\scripts\setup.ps1
.\scripts\dev-backend.ps1
.\scripts\dev-frontend.ps1
.\scripts\check.ps1
```

El gate base sin infraestructura externa ejecuta `backend: pytest`, `python -m compileall app`, `ruff check .`, `pip check`; y `frontend: npm run typecheck`, `npm test`, `npm run build`. `alembic check` y `/health/db` son checks de integración con PostgreSQL separados.

## No hacer todavía

- no implementar Flutter;
- no implementar AWS;
- no instalar modelos de IA;
- no crear el generador Spring Boot;
- no diseñar contratos HTTP definitivos sin el CU correspondiente;
- no empezar varios CU en paralelo.
## CU-06 en curso

El frontend no ejecuta ni replica el Command Bus. rontend/src/features/editor/ contiene contratos TypeScript, cliente HTTP y store Pinia de proyeccion. FastAPI mantiene temporalmente un UmlCommandBus por sessionId bajo /editor/sessions. Las sesiones desaparecen al reiniciar el backend y no requieren PostgreSQL; CU-07 incorporara persistencia. No iniciar el canvas visual hasta validar el Incremento 1.

## CU-06 Incremento 2 preparado

El Incremento 1 fue validado con 137 pruebas backend, 7 frontend y gate completo verde. El Incremento 2 reemplaza la pantalla de fundacion por `EditorWorkspace` y agrega una proyeccion read-only `ProjectDocument -> Vue Flow`. No iniciar Incremento 3 hasta validar typecheck, Vitest, build, gate y prueba manual del canvas.

## CU-06 Incremento 3 preparado

Incrementos 1 y 2 estan aprobados. El ultimo incremento agrega toolbox, inspector, atributos/operaciones/parametros, relaciones, drag persistido por Command Bus, Undo/Redo y auto-layout con `d3-dag`. No cerrar CU-06 hasta pasar typecheck, tests, build, gate completo y la prueba manual integral del editor.

## CU-06 cerrado

CU-06 quedo DONE tras validar bridge de sesiones, canvas Vue Flow, editor mutable, inspector, relaciones, drag persistido por `SetNodeLayoutCommand`, Undo/Redo y auto-layout con `d3-dag`. La suite final pasa con 137 tests backend y 20 frontend, ademas de typecheck/build/gate completo.

Siguiente trabajo: CU-07 persistir y recuperar proyectos. La sesion de CU-06 sigue siendo efimera en memoria y se pierde al reiniciar FastAPI; CU-07 debe reemplazar esa limitacion sin duplicar `ProjectDocument` ni el Command Bus.
