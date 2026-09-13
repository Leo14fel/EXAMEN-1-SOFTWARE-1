# Estado real

Fecha de actualizacion: 2026-09-12

## Completado

- [x] CU-00 terminado: monorepo, frontend y backend minimos.
- [x] `GET /health` y `GET /health/db` validados en 200.
- [x] PostgreSQL local Windows validado: `localhost:5432/examen_sw1`.
- [x] Alembic, tests frontend/backend, typecheck, build y Ruff en verde.
- [x] Integracion visual Vue -> FastAPI verificada.
- [x] Docker Compose documentado como alternativa opcional (`55432` en host -> `5432` en contenedor).
- [x] Auditoría previa a CU-01: producto, roadmap PUDS, arquitectura, decisiones y gate base alineados.

## No implementado todavía

- [x] CU-01 terminado: ProjectDocument, CanonicalUmlModel y DiagramLayout en memoria.
- [ ] Clases y miembros UML concretos (CU-02).
- [ ] Persistencia de proyectos.
- [ ] Auth/ownership.
- [ ] Canvas UML funcional.
- [ ] Realtime/presencia.
- [ ] Generación Spring Boot.
- [ ] Generación Flutter.
- [ ] IA/STT/XMI.
- [ ] Despliegue AWS.

## Próximo paso

CU-00: DONE. CU-01: DONE. CU-02: NEXT / NOT_STARTED.
