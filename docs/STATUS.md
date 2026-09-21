# Estado real

Fecha de actualizacion: 2026-09-18

## Completado

- [x] CU-00 terminado: monorepo, frontend y backend minimos.
- [x] `GET /health` y `GET /health/db` validados en 200.
- [x] PostgreSQL local Windows validado: `localhost:5432/examen_sw1`.
- [x] Alembic, tests frontend/backend, typecheck, build y Ruff en verde.
- [x] Integracion visual Vue -> FastAPI verificada.
- [x] Docker Compose documentado como alternativa opcional (`55432` en host -> `5432` en contenedor).
- [x] Auditoria previa a CU-01: producto, roadmap PUDS, arquitectura, decisiones y gate base alineados.

## CUs completados

- [x] CU-01 terminado: ProjectDocument, CanonicalUmlModel y DiagramLayout en memoria.
- [x] CU-02 terminado: clases, atributos, operaciones y parametros UML.
- [x] CU-03 terminado: relaciones UML, multiplicidades y convenciones semanticas de direccion.
- [x] CU-04 terminado: diagnosticos de validacion semantica UML.
- [x] CU-05 terminado: Command Bus encapsulado, snapshots y Undo/Redo.
- [x] CU-06 terminado: canvas UML editable, inspector, relaciones, drag persistido, Undo/Redo y auto-layout.

## CU activo

- [ ] CU-07 IN_PROGRESS: los tres incrementos estan implementados; falta prueba manual humana final del editor persistente.

## No implementado todavia

- [ ] Auth/ownership.
- [ ] Realtime/presencia.
- [ ] Generacion Spring Boot.
- [ ] Generacion Flutter.
- [ ] IA/STT/XMI.
- [ ] Despliegue AWS.

## Proximo paso

CU-00: DONE. CU-01: DONE. CU-02: DONE. CU-03: DONE. CU-04: DONE. CU-05: DONE. CU-06: DONE. CU-07: IN_PROGRESS.
