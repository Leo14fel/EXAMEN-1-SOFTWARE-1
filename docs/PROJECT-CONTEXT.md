# Contexto de continuidad del proyecto

## Uso

Este archivo acompaña snapshots del repositorio. El estado real se obtiene del código y la documentación del snapshot.

## Producto y stack

La herramienta CASE es colaborativa para modelado UML de clases. El segundo parcial requiere operación cloud; offline/LAN conserva un objetivo previo pendiente de cotejar con el primer parcial. `/product.md` es la fuente de verdad del producto y stack: Vue 3 + TypeScript + Vite + Vuetify en la herramienta web; FastAPI con destino NoSQL cloud (CU-25) en su backend; SQLAlchemy/Alembic/PostgreSQL se conservan para origen/recuperación legacy; la persistencia normal ya es MongoDB Atlas; Java 21 + Spring Boot 4.x + Spring Data JPA/Hibernate para backend generado; Flutter/Dart para Android generado.

## Estado actual

CU-00 a CU-09 tienen implementación documentada, con gates manuales pendientes según sus documentos. CU-21 implementa exportación/importación y round-trip para el subconjunto canónico; tres incrementos, visual/EA real pendientes. CU-08 protege `/projects` con JWT, usa `current_user.id` para proyectos nuevos y conserva `ProjectDocument`, CAS y Command Bus sin cambios semanticos. CU-09 agrega memberships `EDITOR`/`VIEWER`: el owner se deriva de `projects.owner_id`, editores mutan, viewers solo leen y el owner administra colaboradores. CU-07 persiste `ProjectDocument`, expone lectura y mutaciones con lock/CAS y conecta el editor Vue a `/projects`.

El bridge HTTP temporal de CU-06 fue retirado en CU-07. Los proyectos y mutaciones usan `/projects`; MongoDB Atlas es la fuente persistente y el cache process-local del bus conserva solo el historial de Undo/Redo de la instancia actual. Tras reiniciar, el documento se recupera desde MongoDB y las operaciones nuevas generan historial para la nueva instancia.

El origen SQL legacy conservado es PostgreSQL local de Windows 17.6: `localhost:5432/examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Flujo por CU

1. Revisar `/product.md`, el roadmap PUDS y el CU activo.
2. Aprobar el plan del CU antes de implementar.
3. Implementar un CU por vez en hasta tres incrementos verificables.
4. Registrar evidencia real, deuda y documentacion al cerrar cada incremento.
5. Entregar comandos Git al cerrar el CU sin ejecutarlos salvo peticion explicita.

## Segundo parcial

El usuario autorizó incorporar los requisitos el 2026-11-06. Leer product.md sección 41 y requirements/SECOND-PARTIAL.md. IA grupal cloud por solicitud, sesión/contexto persistente, NoSQL cloud y visor móvil informativo/push son objetivos, no capacidades ya implementadas. PostgreSQL/Flutter generados se conservan. RP-01..03 siguen abiertos; no inventar respuestas.

## Roadmap

`docs/puds/` es la única fuente de roadmap y CUs. CU-25 DONE: tres incrementos, 3 usuarios/15 proyectos/2 permisos migrados a Atlas y recuperación tras reinicio real PASS. 13 proyectos legacy conservan ownerId sin usuario, sin reasignación. PostgreSQL original intacto y respaldado; modo normal mongodb. CU-10 IMPLEMENTED con transporte y cliente; aceptación Atlas/visual pendiente. Gate 242 backend/55 frontend y smoke TCP MongoMock PASS. Control de navegador no arranca; renovación IP seis horas autorizada, pendiente de confirmar Active. El usuario pidió diferir Atlas/visual y avanzar localmente; CU-11 implementado con gate 248 backend/61 frontend y smoke TCP MongoMock PASS. Presencia TTL separada de UML; CU-26 también implementado: sesión/historial/actividad y UI compartidos, 258 backend/68 frontend y TCP/reinicio de servidor MongoMock PASS. Siguiente CU-18; falta credencial de IA cloud para llamada/benchmark reales. Deuda no equivale a aceptación cloud/visual. Ver STATUS y CU-25 para evidencia y comandos Git no ejecutados. IA sigue pendiente; realtime/presencia/sesión grupal tienen código implementado, sin aceptación cloud/visual ni despliegue. No usar cambios de backend como rollback después de nuevas escrituras Mongo sin congelar/reconciliar datos.

## Editor CU-06

El frontend envia mutaciones como `UmlCommand` al backend y recibe una nueva proyeccion de `ProjectDocument`. El drag se confirma con `SetNodeLayoutCommand`; Undo/Redo pertenecen al backend; el auto-layout usa `d3-dag`. El inspector conserva borradores con cambios sin guardar frente a revisiones externas del documento.

Las relaciones visuales usan un edge custom derivado: association es una linea continua; aggregation/composition muestran diamante hueco/lleno en source; generalization muestra triangulo hueco en target y no multiplicidades. Las otras tres relaciones pueden ser recursivas y se muestran como self-loops curvos seleccionables con labels por extremo. Los self-loops se omiten solo del input de auto-layout, nunca del documento ni del render. La UI previene `source == target` para generalization; la autoridad para ciclos indirectos sigue en backend.

## Benchmarks

Los benchmarks de LLM, STT y VLM viven en `docs/benchmarks/`. Registrar unicamente mediciones reales, configuracion, hardware, fecha y edge cases manuales.

## Prioridad de funciones antiguas (2026-11-07)

Por petición expresa del usuario se completó CU-21 antes de IA. Importación crea nuevo proyecto, valida XML/UML y no cambia el original; round-trip y tipos de clase corregidos. Ver su documento e inventario requirements/LEGACY-GAPS.md. CU-09 también implementó invitaciones/tokens/vencimiento/cancelación y UI en sus incrementos 2/3; gate final 282 backend/80 frontend, estático/build y TCP MongoMock PASS. CU-13 implementado en tres incrementos: modelo relacional/perfil, relaciones/herencia y vista previa, gate 309 backend/86 frontend + TCP local PASS. Siguiente CU-14 según dependencias. QA visual/cloud/EA sigue pendiente. No declarar todas las funciones antiguas completas sin rúbrica RP-01. Un CU a la vez, sin commit/push.

El perfil CU-13 se lee de metadata.generation y no altera UmlModel. La salida es un modelo intermedio PostgreSQL (destino generado), no persistencia CASE ni DDL ejecutado. Cardinalidades avanzadas tienen avisos/requisitos de runtime, sin afirmar garantía ya implementada; CU-14 debe atenderlos o rechazar el plan.

## CU activo CU-14 — 2026-11-07

El usuario autorizó continuar el generador y documentación. Inc.1 DONE: Jinja2 genera base Java 21/Boot 4.1.2, entidades/repositorios escalares/esquema/README. Gradle 9.5.1 y JUnit real PASS, gate 336 backend/86 frontend. Faltan inc.2 capacidades/relaciones y prueba PostgreSQL, inc.3 entrega/UI. Ver documento CU-14; no iniciar CU-15. No se modificó product.md ni datos reales.

CU-14 inc.2 DONE (2026-11-07): backend generado compilado/ejecutado con CRUD/consultas y FK simples, 51 verificaciones PostgreSQL/HTTP/JVM y gate 342/86 PASS. Continúa inc.3 entrega por proyecto/revisión y UI. Respetar límites UnsupportedGeneration y perfil explícito; no dar por completo el generador de relaciones avanzadas ni CU-15.

## Prioridad vigente del usuario — 2026-11-07

Segundo parcial primero. CU-18 es único activo; CU-14 queda pendiente de reanudación, inc.3 no implementado, sin eliminar sus fuentes/evidencia. CU-18 inc.1 preparado con gate 384 backend/86 frontend y estático/build PASS. Falta clave (usuario no tiene), benchmark real y pasos de integración grupal/UI. No confundir pruebas controladas o fixtures-only NOT_RUN con IA cloud funcionando. Continuidad después: CU-19 → CU-27 → CU-23 → CU-28; no saltar dependencias. Guía deployment/GEMINI-CU18.md.

CU-18 inc.2/3 preparados por autorización de continuar sin clave: solicitudes grupales persistidas y formulario, sin mutaciones textuales; 402 backend/96 frontend y estático/build PASS, 60 pruebas posteriores de atribución y smoke TCP sin clave PASS. La IA real y benchmark siguen NOT_RUN. Completar evaluación/aceptación dentro de CU-18; no iniciar CU-19 ni retomar CU-14 en paralelo. No se reinició el QA existente; conservar datos temporales antes de actualizarlo.

## Relevo y plazo — 2026-11-07

El usuario quiere organizar trabajo con otra persona y entregar el martes 10 de noviembre de 2026 por la tarde (hora sin confirmar). Leer delivery/RELEVO-EQUIPO.md para el corte, responsabilidades y dependencias; no es roadmap nuevo. Se conserva un CU activo, CU-18, con clave/prueba real pendientes. No declarar toda la IA operativa ni compartir .env/artifacts de bases. Cambios locales de muchos CUs aún sin commit; copia local de fuentes no equivale a una base Git compartida.
