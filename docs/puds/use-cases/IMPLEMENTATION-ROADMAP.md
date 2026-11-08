# Roadmap PUDS - Casos de uso y ciclos

## Proposito y reglas

Este roadmap deriva `/product.md` en una secuencia de implementacion. PUDS es la unica fuente de verdad para roadmap y documentos de casos de uso; `/product.md` sigue siendo la fuente de verdad de producto y stack.

- Implementar en orden, con un solo CU activo y un maximo de tres incrementos por CU.
- Cada CU cerrado actualiza su `CU-XX-<slug>.md` con evidencia real.
- No crear CUs por componentes tecnicos aislados, salvo CU-00 como fundacion solicitada.
- Cierre: pruebas aplicables verdes, documentacion sincronizada y comandos Git sugeridos.

## Replanificación del segundo parcial

Requisitos incorporados el 2026-11-06 a solicitud del usuario; ver `product.md` sección 41 y `docs/requirements/SECOND-PARTIAL.md`. Este documento sigue siendo la única secuencia de implementación. Los números existentes se conservan para no reescribir la historia de los CUs.

**Último CU cerrado:** CU-25 DONE (3 incrementos): prueba Atlas, adaptación de API, respaldo/migración de datos existentes y recuperación tras reinicio verificados. CU-10 IMPLEMENTED con aceptación Atlas/visual diferida por petición explícita del usuario de avanzar localmente. CU-11 IMPLEMENTED con gate local 248 backend/61 frontend y deuda Atlas/visual diferida; CU-26 IMPLEMENTED con deuda Atlas/visual diferida; la prioridad actual de funciones antiguas se detalla abajo, antes de retomar CU-18; ver documentos CU correspondientes. PostgreSQL original intacto.

**Ajuste autorizado 2026-11-07:** el usuario pidió completar funciones antiguas. CU-21 implementó importación/round-trip en sus incrementos 2/3 (exportación previa era inc.1), con aceptación visual/EA pendiente. CU-09 también IMPLEMENTED con invitaciones/tokens/vencimiento y UI (tres incrementos), gate local 282 backend/80 frontend; CU-13 IMPLEMENTED en tres incrementos con gate 309 backend/86 frontend y TCP local; siguiente CU-14; seguir los pendientes antiguos verificables antes de retomar CU-18, que requiere credencial IA para su benchmark real. No se amplía el alcance de CUs en paralelo.

**Orden prioritario del segundo parcial:** CU-25 → CU-10 → CU-11 → CU-26 → CU-18 → CU-19 → CU-27 → CU-23 → CU-28. Después completar los CUs anteriores que siguen abiertos o pendientes y ejecutar CU-24. Las dependencias de cada CU prevalecen sobre cualquier paralelización; se trabaja uno a la vez.

CU-12 conserva el objetivo offline/LAN previo, con alcance de aceptación pendiente de contrastar con el primer parcial. CU-13..17, CU-20..22 no se eliminan. CU-21 ahora implementa exportación/importación y round-trip para el subconjunto canónico; mantiene aceptación visual y EA real pendientes. No se continúa otro CU en paralelo.

**Regla de cierre:** diferenciar IMPLEMENTED de DONE cuando falten pruebas manuales. Las cifras de pruebas de los CUs son evidencia histórica, no una nueva ejecución.

## Prioridad vigente

> **Prioridad vigente, 2026-11-07:** el usuario revocó la prioridad temporal de funciones del primer parcial y pidió acelerar el segundo. Caso activo CU-18; luego CU-19 → CU-27 → CU-23 → CU-28, respetando dependencias y verificaciones. CU-14 queda pendiente de reanudación en incremento 3, con sus incrementos 1/2 y evidencia preservados; no se elimina alcance anterior. No trabajar ambos en paralelo. IA real/benchmark requiere una clave que el usuario todavía no tiene; preparar las partes verificables sin simular resultados ni declarar cierre cloud.

# CICLO 1 - Nucleo UML y editor

**Incremento usable:** una herramienta local mantiene un documento UML en memoria, modela clases y relaciones, valida, modifica por Command Bus y lo proyecta en un canvas.

## CU-00 - Fundar el proyecto ejecutable
**Estado:** IMPLEMENTED - pendiente de prueba manual humana final.
**Objetivo:** crear el monorepo y demostrar frontend <-> backend.
**Dependencias:** ninguna.

## CU-01 - ProjectDocument y Canonical UML Model
**Estado:** DONE.
**Objetivo:** representar un proyecto separando semantica y layout.
**Dependencias:** CU-00.
**Product:** secciones 3, 6 y 7.
**Incluye:** identidad estable con UUID, metadatos, ownership estructural, revision, timestamps, CanonicalUmlModel, DiagramLayout y serializacion estructural.
**Cierre:** crear, serializar y reconstruir el documento sin contaminar la semantica UML con layout.

## CU-02 - Modelar clases y miembros UML
**Estado:** DONE.
**Objetivo:** crear, editar y eliminar clases y miembros soportados.
**Dependencias:** CU-01.
**Incluye:** Class, Attribute/Property, Operation, Visibility, tipos, Enumeration, Package cuando aplique y metadatos de generacion separados.

## CU-03 - Modelar relaciones UML
**Estado:** DONE.
**Objetivo:** crear y modificar relaciones UML validas.
**Dependencias:** CU-02.
**Incluye:** Association, Aggregation, Composition, Generalization y Multiplicity.

## CU-04 - Validar el modelo UML y navegar diagnosticos
**Estado:** DONE.
**Objetivo:** disponer de un unico motor de validacion y diagnosticos accionables.
**Dependencias:** CU-02, CU-03.
**Incluye:** severity, code, mensaje, path, referencia, bloqueo y navegacion UI cuando exista interfaz.

## CU-05 - Command Bus y Undo/Redo
**Estado:** DONE.
**Objetivo:** canalizar mutaciones por UmlCommand/UmlCommandBus/UmlCommandExecutor y soportar Undo/Redo.
**Dependencias:** CU-02..04.
**Incluye:** estrategia de undo/redo con snapshots completos y un maximo fijo de 100 estados de undo; al superar el limite se descarta el snapshot mas antiguo.
**Cierre:** toda mutacion soportada usa la ruta oficial y conserva consistencia al deshacer/rehacer.

## CU-06 - Editar el diagrama desde el canvas
**Estado:** DONE.
**Objetivo:** proyectar y editar el documento con `@vue-flow/core` sin que el canvas sea fuente de verdad.
**Dependencias:** CU-01..05.
**Incluye:** nodos, relaciones, zoom/pan/seleccion/movimiento, inspector, toolbox, fit, grid y d3-dag; las mutaciones pasan por el Command Bus existente.

# CICLO 2 - Persistencia, acceso y colaboracion

**Incremento usable:** usuarios autorizados guardan, abren y comparten proyectos; los cambios y la presencia se sincronizan, con operacion local/LAN base.

## CU-07 - Persistir y recuperar proyectos
**Estado:** DONE.
**Objetivo histórico implementado:** almacenar ProjectDocument con PostgreSQL y revision optimista. La adaptación NoSQL se realiza en CU-25 sin reescribir la evidencia de CU-07.
**Dependencias:** CU-01, CU-04..06.
**Incluye:** SQLAlchemy, Alembic, migraciones, guardado, lectura y revision.

## CU-08 - Autenticacion, ownership y administracion de proyectos
**Estado:** IMPLEMENTED - pendiente de prueba manual humana final, según su documento de CU.
**Objetivo:** autenticar usuarios y administrar sus propios proyectos.
**Dependencias:** CU-07.
**Incluye:** registro/login, PyJWT, Argon2/pwdlib, listado, creacion, apertura, ownerId y autorizacion.

## CU-09 - Administrar acceso de colaboradores
**Estado:** IMPLEMENTED - pendiente de prueba manual humana final.
**Objetivo:** autorizar colaboradores de un proyecto antes de permitir colaboracion realtime.
**Dependencias:** CU-08.
**Implementado:** memberships EDITOR/VIEWER y administración por owner mediante correo registrado. Invitaciones, tokens y expiración se implementaron en los incrementos 2/3 de la reanudación autorizada por el usuario. Gates locales aprobados; visual/cloud pendiente.

## CU-10 - Editar colaborativamente en tiempo real
**Estado:** IMPLEMENTED; gates automáticos 242 backend/55 frontend y smoke TCP MongoMock PASS. Aceptación Atlas/visual diferida como deuda explícitamente autorizada para continuar CU-11.
**Objetivo:** sincronizar operaciones con servidor autoritativo.
**Dependencias:** CU-05, CU-07..09, CU-25.
**Incluye:** WebSockets, baseRevision, nueva revisión, persistencia NoSQL inmediata, broadcast, rechazo de operaciones obsoletas y recuperación autoritativa. Verificar dos editores, reconexión, revocación de acceso y fallo de persistencia sin anunciar cambios aceptados.

## CU-11 - Mostrar presencia colaborativa
**Estado:** IMPLEMENTED; presencia efímera, selección/edición y cursores. Gate 248 backend/61 frontend y TCP MongoMock PASS; aceptación Atlas/visual diferida por usuario. Ver CU-11-collaborative-presence.md.
**Objetivo:** mostrar presencia efimera sin incrementar revision.
**Dependencias:** CU-10.
**Incluye:** sesion, seleccion, cursor, elemento en edicion, actividad y UI de presencia.

## CU-12 - Operar capacidades esenciales offline y por LAN
**Objetivo previo:** demostrar host y clientes LAN sin Internet para capacidades implementadas. Criterio final pendiente del enunciado del primer parcial; no sustituye operación cloud del segundo parcial.
**Dependencias:** CU-07..11, CU-25.
**Incluye:** configuracion local/LAN, acceso, persistencia y realtime; IA/STT se revalidan cuando existan.

# CICLO 3 - Transformaciones y generacion deterministica

**Incremento usable:** UML valido produce modelo relacional, backend Spring Boot, OpenAPI/Postman/Manifest y aplicacion Flutter Android para capacidades derivables.

## CU-13 - Transformar UML a modelo relacional
**Estado:** IMPLEMENTED; mapper/perfil, relaciones/herencia y API/vista previa. Gate 309 backend/86 frontend y TCP MongoMock PASS; aceptación visual/cloud diferida. Ver CU-13-relational-mapping.md.
**Objetivo:** producir RelationalModel determinista.
**Dependencias:** CU-04.
**Incluye:** tablas, columnas, PK/FK, restricciones, indices y reglas para relaciones, herencia, enums y nulabilidad.

## CU-14 - Generar backend Spring Boot
**Estado:** PENDIENTE DE REANUDACIÓN por prioridad del segundo parcial; incrementos 1/2 DONE: Jinja2, entidades/repositorios, DTOs, servicios y REST CRUD/consultas/navegación para FK simples. Gate 342 backend/86 frontend y 51 comprobaciones PostgreSQL/JVM PASS. Compuestas/N:M/herencia/composición/reglas de runtime no soportadas se rechazan explícitamente. Incremento 3 pendiente: entrega por proyecto/revisión y UI. Ver CU-14-spring-backend-generation.md.
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
**Estado:** IN PROGRESS; contratos/Gemini, solicitudes grupales autorizadas y formulario preparados. Gate 402 backend/96 frontend, estático/build PASS; proveedor controlado y TCP sin clave verificados. El usuario difirió la clave: inferencia/benchmark real y aceptación visual/Atlas pendientes, sin cierre ni paso a CU-19 todavía. Ver CU-18-natural-language.md.
**Objetivo:** texto -> intencion estructurada -> UmlCommand; la IA no manipula canvas.
**Dependencias:** CU-04, CU-05, CU-26.
**Incluye:** selección de proveedor/modelo cloud, integración backend con conversación compartida de CU-26, esquema cerrado, allow-lists, resolver, validación, permisos, revisión y benchmark real. Qwen3 1.7B local queda opcional. La ejecución de modificaciones por texto queda bloqueada por la aclaración RP-02; puede evaluarse intención sin aplicarla. CU-19 habilita el flujo de voz requerido.

## CU-19 - Editar UML mediante voz
**Objetivo:** audio breve -> texto -> reutilizar CU-18.
**Dependencias:** CU-18.
**Incluye:** faster-whisper/CTranslate2, captura, transcripción visible y atribuida en la conversación grupal, comandos breves, aplicación validada por la ruta canónica, broadcast y benchmark STT. No exigir transcripción continua de reuniones ni escucha autónoma.

## CU-20 - Operar la aplicacion generada mediante asistente
**Objetivo:** ejecutar solo capacidades declaradas via AssistantCommand.
**Dependencias:** CU-15..16, CU-18; CU-19 si usa voz.
**Incluye:** CommandValidator, Executor, operaciones allow-listed, planes cortos y seguridad.

## CU-21 - Importar y exportar XMI
**Estado:** IMPLEMENTED para el subconjunto canónico: exportación/importación y round-trip, tres incrementos. Ver documento CU-21; visual/EA real pendientes.
**Objetivo:** interoperar con XMI 2.1 y Enterprise Architect en el subconjunto soportado.
**Dependencias:** CU-04.
**Incluye:** lxml/iterparse, importacion, validacion, modelo, exportacion y round-trip cuando aplique.

## CU-22 - Crear UML desde imagen
**Objetivo:** imagen -> estructura UML -> validacion -> modelo canonico.
**Dependencias:** CU-04, CU-05.
**Incluye:** Pillow/scikit-image, Qwen2.5-VL 3B, salida estructurada y benchmark VLM.

## CU-23 - Desplegar la herramienta CASE en AWS
**Objetivo:** desplegar la herramienta CASE conforme al requisito de producto.
**Dependencias:** CU-25, CU-10, CU-11, CU-27.
**Incluye:** frontend Vue, backend FastAPI, NoSQL cloud, WebSockets y asistente cloud con secretos externos, procedimiento y smoke tests remotos. Los servicios AWS se deciden aquí coordinando la decisión de CU-25. CU-28 revalida el despliegue al integrar push. PostgreSQL generado es independiente.

## CU-24 - Validar integralmente el MVP
**Objetivo:** aceptar el producto mediante evidencia de sus flujos finales.
**Dependencias:** CU-12, CU-17, CU-20..23, CU-25..28. El alcance offline de CU-12 requiere resolver RP-01.
**Incluye:** crear, validar, guardar y reabrir UML; colaborar; generar artefactos; compilar backend generado y Flutter cuando corresponda; OpenAPI/Postman; texto, voz e imagen a UML; XMI; offline final y LAN cuando corresponda; escenarios E2E con Cypress.
**Cierre:** evidencia real del flujo completo del MVP y la matriz SECOND-PARTIAL, sin resultados ficticios. Exige cotejo del primer parcial, dos editores remotos, observador móvil, IA grupal por voz, resumen de avances persistidos, reapertura tras reinicio y push real; además regresión del alcance anterior.

# Ampliación del segundo parcial

## CU-25 - Retomar proyectos sobre persistencia NoSQL cloud
**Estado:** DONE; evidencia de los tres incrementos en `CU-25-cloud-nosql-persistence.md`.
**Objetivo:** conservar proyectos, usuarios y acceso al trasladar la persistencia CASE a NoSQL cloud.
**Dependencias:** CU-07, CU-08, CU-09; preservar la exportación existente de CU-21.
**Incluye:** selección de motor/proveedor/SDK con evidencia, escritura condicional, integridad, respaldo, migración verificable y recuperación. Modelo canónico y layout separados; sin borrar datos ni sustituir autenticación. Contratos de almacenamiento se definen aquí cuando se necesiten.
**Cierre:** crear/guardar/reabrir y mutar con permisos y conflictos conservados; comparar identidades y contenido migrados; recuperar tras reinicio. No quedan usuarios o permisos obligatorios dependiendo exclusivamente de PostgreSQL.

## CU-26 - Participar en una sesión grupal persistente
**Estado:** IMPLEMENTED; conversación/historial/actividad y UI compartidos, gates locales y TCP con recuperación aprobados. Atlas/visual diferidos por usuario. Ver CU-26-group-session.md.
**Objetivo:** compartir conversación, participantes y actividad atribuida del diagrama, sin IA todavía.
**Dependencias:** CU-25, CU-10, CU-11.
**Incluye:** sesión autorizada, mensajes y actividad persistidos, difusión, orden e identidad, historial al reconectar y aislamiento entre proyectos. No duplicar UmlModel dentro de mensajes como otra fuente de verdad.
**Cierre:** dos participantes ven la misma conversación; quien llega tarde recupera historial; reinicio no pierde estado aceptado y permisos impiden accesos ajenos.

## CU-27 - Consultar, revisar y resumir con la IA grupal
**Estado:** PLANNED.
**Objetivo:** disponer de asesor y desarrollador por solicitud, con contexto compartido.
**Dependencias:** CU-26, CU-18, CU-19.
**Incluye:** preguntas teóricas, revisión con explicación, sugerencias, resumen de avances basado en actividad y conversación persistidas, atribución y respuestas visibles para todos. Revisiones no mutan automáticamente. Mutaciones solicitadas usan el pipeline existente y permisos/revisión vigentes; sin chats privados ni agentes autónomos.
**Cierre:** responder quién hizo qué según evidencia disponible, resumir al incorporarse tarde, no inventar actividad, no filtrar proyectos, no actuar sin solicitud y registrar benchmark/edge cases reales.

## CU-28 - Consultar desde móvil y recibir push
**Estado:** PLANNED.
**Objetivo:** observar el diagrama remoto en movimiento, sin edición UML.
**Dependencias:** CU-25, CU-10, CU-11, CU-26, CU-23.
**Incluye:** selección justificada de cliente móvil y proveedor push, acceso autorizado, diagrama realtime, reconexión y notificaciones push de actualizaciones. No confundir con CRUD Flutter generado ni con un toast en una pestaña abierta.
**Cierre:** dispositivo real observa cambios; prueba push con cliente en segundo plano, permisos de notificación y acceso revocado. Registrar versiones, dispositivo y evidencia; tecnología se decide en este CU.

# Dependencias resumidas

```text
CU-00 -> CU-01..06 -> CU-07 -> CU-08 -> CU-09 -> CU-25
CU-25 + CU-05 + CU-07..09 -> CU-10 -> CU-11
CU-25 + CU-10 + CU-11 -> CU-26 -> CU-18 -> CU-19 -> CU-27
CU-25 + CU-10 + CU-11 + CU-27 -> CU-23
CU-25 + CU-10 + CU-11 + CU-26 + CU-23 -> CU-28
CU-07..11 + CU-25 -> CU-12 (alcance de aceptación pendiente RP-01)
CU-04 -> CU-13 -> CU-14 -> CU-15 -> CU-16 -> CU-17
CU-15 + CU-16 + CU-18 (+ CU-19 si voz) -> CU-20
CU-04 -> CU-21 (exportación parcial ya existente), CU-22
CU-12 + CU-17 + CU-20..23 + CU-25..28 -> CU-24
```

# Documento real de cada CU

Al iniciar un CU se crea `docs/puds/use-cases/CU-XX-<slug>.md` desde `CU-TEMPLATE.md`. El roadmap describe intencion; el documento del CU registra lo realmente implementado.
