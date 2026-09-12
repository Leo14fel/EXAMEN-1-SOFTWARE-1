# Roadmap PUDS - Casos de uso y ciclos

## Proposito y reglas

Este roadmap deriva `/product.md` en una secuencia de implementacion. PUDS es la unica fuente de verdad para roadmap y documentos de casos de uso; `/product.md` sigue siendo la fuente de verdad de producto y stack.

- Implementar en orden, con un solo CU activo y un maximo de tres incrementos por CU.
- Cada CU cerrado actualiza su `CU-XX-<slug>.md` con evidencia real.
- No crear CUs por componentes tecnicos aislados, salvo CU-00 como fundacion solicitada.
- Cierre: pruebas aplicables verdes, documentacion sincronizada y comandos Git sugeridos.

# CICLO 1 - Nucleo UML y editor

**Incremento usable:** una herramienta local mantiene un documento UML en memoria, modela clases y relaciones, valida, modifica por Command Bus y lo proyecta en un canvas.

## CU-00 - Fundar el proyecto ejecutable
**Estado:** DONE.
**Objetivo:** crear el monorepo y demostrar frontend <-> backend.
**Dependencias:** ninguna.

## CU-01 - ProjectDocument y Canonical UML Model
**Objetivo:** representar un proyecto separando semantica y layout.
**Dependencias:** CU-00.
**Product:** secciones 3, 6 y 7.
**Incluye:** identidad estable con UUID, metadatos, ownership estructural, revision, timestamps, CanonicalUmlModel, DiagramLayout y serializacion estructural.
**Cierre:** crear, serializar y reconstruir el documento sin contaminar la semantica UML con layout.

## CU-02 - Modelar clases y miembros UML
**Objetivo:** crear, editar y eliminar clases y miembros soportados.
**Dependencias:** CU-01.
**Incluye:** Class, Attribute/Property, Operation, Visibility, tipos, Enumeration, Package cuando aplique y metadatos de generacion separados.

## CU-03 - Modelar relaciones UML
**Objetivo:** crear y modificar relaciones UML validas.
**Dependencias:** CU-02.
**Incluye:** Association, Aggregation, Composition, Generalization y Multiplicity.

## CU-04 - Validar el modelo UML y navegar diagnosticos
**Objetivo:** disponer de un unico motor de validacion y diagnosticos accionables.
**Dependencias:** CU-02, CU-03.
**Incluye:** severity, code, mensaje, path, referencia, bloqueo y navegacion UI cuando exista interfaz.

## CU-05 - Command Bus y Undo/Redo
**Objetivo:** canalizar mutaciones por UmlCommand/UmlCommandBus/UmlCommandExecutor y soportar Undo/Redo.
**Dependencias:** CU-02..04.
**Incluye:** historial inicial configurable de 100 y estrategia de undo/redo.
**Cierre:** toda mutacion soportada usa la ruta oficial y conserva consistencia al deshacer/rehacer.

## CU-06 - Editar el diagrama desde el canvas
**Objetivo:** proyectar y editar el documento con `@vue-flow/core` sin que el canvas sea fuente de verdad.
**Dependencias:** CU-01..05.
**Incluye:** nodos, relaciones, zoom/pan/seleccion/movimiento, inspector, toolbox, fit, grid y d3-dag; las mutaciones pasan por el Command Bus existente.

# CICLO 2 - Persistencia, acceso y colaboracion

**Incremento usable:** usuarios autorizados guardan, abren y comparten proyectos; los cambios y la presencia se sincronizan, con operacion local/LAN base.

## CU-07 - Persistir y recuperar proyectos
**Objetivo:** almacenar ProjectDocument con PostgreSQL y revision optimista.
**Dependencias:** CU-01, CU-04..06.
**Incluye:** SQLAlchemy, Alembic, migraciones, guardado, lectura y revision.

## CU-08 - Autenticacion, ownership y administracion de proyectos
**Objetivo:** autenticar usuarios y administrar sus propios proyectos.
**Dependencias:** CU-07.
**Incluye:** registro/login, PyJWT, Argon2/pwdlib, listado, creacion, apertura, ownerId y autorizacion.

## CU-09 - Administrar acceso de colaboradores
**Objetivo:** autorizar colaboradores de un proyecto antes de permitir colaboracion realtime.
**Dependencias:** CU-08.
**Incluye:** ProjectMembership, ProjectInvitation, roles, estado y expiracion de invitaciones, token y autorizacion de acceso.

## CU-10 - Editar colaborativamente en tiempo real
**Objetivo:** sincronizar operaciones con servidor autoritativo.
**Dependencias:** CU-05, CU-07..09.
**Incluye:** WebSockets, baseRevision, nueva revision, persistencia inmediata, broadcast, rechazo de operaciones obsoletas y recuperacion autoritativa.

## CU-11 - Mostrar presencia colaborativa
**Objetivo:** mostrar presencia efimera sin incrementar revision.
**Dependencias:** CU-10.
**Incluye:** sesion, seleccion, cursor, elemento en edicion, actividad y UI de presencia.

## CU-12 - Operar capacidades esenciales offline y por LAN
**Objetivo:** demostrar host y clientes LAN sin Internet para capacidades implementadas.
**Dependencias:** CU-07..11.
**Incluye:** configuracion local/LAN, acceso, persistencia y realtime; IA/STT se revalidan cuando existan.

# CICLO 3 - Transformaciones y generacion deterministica

**Incremento usable:** UML valido produce modelo relacional, backend Spring Boot, OpenAPI/Postman/Manifest y aplicacion Flutter Android para capacidades derivables.

## CU-13 - Transformar UML a modelo relacional
**Objetivo:** producir RelationalModel determinista.
**Dependencias:** CU-04.
**Incluye:** tablas, columnas, PK/FK, restricciones, indices y reglas para relaciones, herencia, enums y nulabilidad.

## CU-14 - Generar backend Spring Boot
**Objetivo:** generar un backend Java compilable.
**Dependencias:** CU-13.
**Incluye:** Java 21, Spring Boot 4.x, Gradle, MVC, Spring Data JPA/Hibernate, Validation, Jackson, PostgreSQL, Jinja2 y capacidades declaradas.

## CU-15 - Generar OpenAPI, Postman y Domain Manifest
**Objetivo:** producir artefactos coherentes del dominio generado.
**Dependencias:** CU-14.
**Incluye:** OpenAPI publicado por springdoc-openapi, Postman derivado y Domain Manifest.

## CU-16 - Generar aplicacion movil Flutter para Android
**Objetivo:** generar una app Flutter que consuma el backend generado.
**Dependencias:** CU-14, CU-15.
**Incluye:** Flutter, Dart, Android, CRUD, filtros, paginacion, relaciones, validaciones e inferencia UI.

## CU-17 - Ejecutar y verificar el pipeline de generacion
**Objetivo:** integrar UML valido hasta aplicaciones y artefactos compilables.
**Dependencias:** CU-13..16.
**Incluye:** accion/UI de generacion, validacion previa, orquestacion, verificacion y demo CRUD.

# CICLO 4 - IA, interoperabilidad, despliegue y aceptacion

**Incremento usable:** entradas asistidas e interoperabilidad funcionan dentro del alcance soportado; la herramienta puede desplegarse en AWS y el MVP se acepta integralmente.

## CU-18 - Editar UML mediante lenguaje natural
**Objetivo:** texto -> intencion estructurada -> UmlCommand; la IA no manipula canvas.
**Dependencias:** CU-04, CU-05.
**Incluye:** Qwen3 1.7B local, esquema cerrado, allow-lists, resolver, validacion, Command Bus, UI y benchmark.

## CU-19 - Editar UML mediante voz
**Objetivo:** audio breve -> texto -> reutilizar CU-18.
**Dependencias:** CU-18.
**Incluye:** faster-whisper/CTranslate2, captura, transcripcion, comandos breves, integracion y benchmark STT.

## CU-20 - Operar la aplicacion generada mediante asistente
**Objetivo:** ejecutar solo capacidades declaradas via AssistantCommand.
**Dependencias:** CU-15..16, CU-18; CU-19 si usa voz.
**Incluye:** CommandValidator, Executor, operaciones allow-listed, planes cortos y seguridad.

## CU-21 - Importar y exportar XMI
**Objetivo:** interoperar con XMI 2.1 y Enterprise Architect en el subconjunto soportado.
**Dependencias:** CU-04.
**Incluye:** lxml/iterparse, importacion, validacion, modelo, exportacion y round-trip cuando aplique.

## CU-22 - Crear UML desde imagen
**Objetivo:** imagen -> estructura UML -> validacion -> modelo canonico.
**Dependencias:** CU-04, CU-05.
**Incluye:** Pillow/scikit-image, Qwen2.5-VL 3B, salida estructurada y benchmark VLM.

## CU-23 - Desplegar la herramienta CASE en AWS
**Objetivo:** desplegar la herramienta CASE conforme al requisito de producto.
**Dependencias:** CU-07..12.
**Incluye:** frontend Vue, backend FastAPI, PostgreSQL, configuracion y secretos externos al codigo, procedimiento documentado y smoke tests. La seleccion de servicios AWS se decide en este CU.

## CU-24 - Validar integralmente el MVP
**Objetivo:** aceptar el producto mediante evidencia de sus flujos finales.
**Dependencias:** CU-12, CU-17, CU-20..23.
**Incluye:** crear, validar, guardar y reabrir UML; colaborar; generar artefactos; compilar backend generado y Flutter cuando corresponda; OpenAPI/Postman; texto, voz e imagen a UML; XMI; offline final y LAN cuando corresponda; escenarios E2E con Cypress.
**Cierre:** evidencia real del flujo completo del MVP, sin resultados ficticios.

# Dependencias resumidas

```text
CU-00 -> CU-01 -> CU-02 -> CU-03 -> CU-04 -> CU-05 -> CU-06
                              |                 |
                              +-> CU-13 -> CU-14 -> CU-15 -> CU-16 -> CU-17
CU-06 -> CU-07 -> CU-08 -> CU-09 -> CU-10 -> CU-11 -> CU-12
CU-05 -> CU-18 -> CU-19
CU-15 + CU-18 -> CU-20
CU-04 -> CU-21, CU-22
CU-07..12 -> CU-23
CU-12 + CU-17 + CU-20..23 -> CU-24
```

# Documento real de cada CU

Al iniciar un CU se crea `docs/puds/use-cases/CU-XX-<slug>.md` desde `CU-TEMPLATE.md`. El roadmap describe intencion; el documento del CU registra lo realmente implementado.
