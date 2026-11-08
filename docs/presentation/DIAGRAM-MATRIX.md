# Matriz maestra de diagramas

Base: auditoria de `feat/xmi-export` en `c58a5f4`; XMI es worktree no confirmado y realtime es CU-10 no fusionado. P0=indispensable, P1=mejora importante, P2=opcional.

| ID | Capitulo | Tipo UML | Nombre | Proposito | Elementos/relaciones | Fuente en codigo | Prioridad | Estado |
|---|---|---|---|---|---|---|---|---|
| D-01 | Fundamentos | Contexto | Contexto del sistema CASE | Delimitar usuario, sistema y EA objetivo | Visitante, usuario, CASE, PostgreSQL, EA; HTTP/XMI | `App.vue`, `main.py`, exporter* | P0 | Obligatorio |
| D-02 | Requisitos | Casos de uso | Casos de uso implementados | Captura funcional real | Visitante, autenticado, OWNER/EDITOR/VIEWER; CU-A/P/U/C | `api/*.py`, workspace | P0 | Obligatorio |
| D-03 | Analisis | Clases | Modelo canonico UML | Explicar fuente de verdad | ProjectDocument, modelo, elementos, layout; composicion/asociaciones | `domain/uml/models.py` | P0 | Obligatorio |
| D-04 | Analisis | Clases/ER | Modelo logico de datos | Persistencia y acceso | users, projects, memberships; PK/FK/cascade | `db/*.py`, migrations | P0 | Obligatorio |
| D-05 | Analisis | Paquetes | Paquetes de analisis | Separar responsabilidades | identidad, proyectos, UML, persistencia, XMI* | estructura app/frontend | P0 | Obligatorio |
| D-06 | Diseno | Componentes | Arquitectura logica | Mostrar UI/API/dominio/DB | navegador, Vue, FastAPI, dominio, ORM, DB | `frontend/src`, `backend/app` | P0 | Obligatorio |
| D-07 | Diseno | Despliegue | Despliegue local validado | Mostrar nodos/protocolos/puertos reales | browser:5173, API:8000, PG:5432/55432 | README, compose, config | P0 | Obligatorio |
| D-08 | Diseno | Secuencia | Login y restaurar sesion | Seguridad de acceso | usuario, AuthScreen, API, security, users | `auth-store.ts`, `api/auth.py` | P0 | Obligatorio |
| D-09 | Diseno | Secuencia | Ejecutar comando UML | Flujo central de edicion | UI, store, API, access, bus, executor, DB | `editor-store.ts`, `projects.py` | P0 | Obligatorio |
| D-10 | Diseno | Secuencia | Administrar colaborador | Roles y permisos | OWNER, dialogo, API, membership DB | `projects.py`, workspace | P0 | Obligatorio |
| D-11 | Diseno | Comunicacion | Modelar UML | Objetos boundary/control/entity | inspector, store, router, bus, record | mismos D-09 | P1 | Obligatorio |
| D-12 | Diseno | Comunicacion | Login | Numeracion de objetos | AuthScreen, API, security, UserRecord | mismos D-08 | P1 | Obligatorio |
| D-13 | Implementacion | Clases | Command Bus y validacion | Responsabilidades de mutacion | comandos, bus, executor, diagnosticos | `commands.py`, `validation.py` | P1 | Obligatorio |
| D-14 | Implementacion | Secuencia | Undo y redo | Explicar snapshots/revision | UI, router, bus, DB | `command_bus.py`, `projects.py` | P1 | Obligatorio |
| D-15 | Interoperabilidad | Secuencia | Exportar XMI | Delimitar exportacion parcial | lector, toolbar, API, exporter, blob | exporter/API/UI* | P1 | Opcional hasta commit |
| D-16 | Interoperabilidad | Comunicacion | Exportar XMI | Objetos y mensajes XMI | toolbar, router, exporter, document | exporter* | P1 | Opcional hasta commit |
| D-17 | Colaboracion | Secuencia | Realtime de CU-10 | Documentar rama no integrada | WS client, manager, REST commit, sockets | `git show 01eb2cd` | P1 | Opcional/anexo |
| D-18 | Analisis | Casos de uso | Planificacion futura | Separar backlog de producto | CU-11..24 | roadmap | P2 | Opcional |
| D-19 | Diseno | Comunicacion | Crear/abrir proyecto | Complemento de persistencia | workspace, API, DB | `editor-store.ts`, `projects.py` | P2 | Opcional |
| D-20 | Implementacion | Actividad | Auto-layout | Detalle de d3-dag y comandos por nodo | editor, auto-layout, API | `auto-layout.ts` | P2 | Opcional |

Conteo: **P0 10; P1 7; P2 3**. No crear diagramas de presencia, importacion, AWS, generadores o IA como realizados: no tienen respaldo en HEAD.
