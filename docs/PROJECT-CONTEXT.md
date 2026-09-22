# Contexto de continuidad del proyecto

## Uso

Este archivo acompaña snapshots del repositorio. El estado real se obtiene del código y la documentación del snapshot.

## Producto y stack

La herramienta CASE es colaborativa y offline-first para modelado UML de clases. `/product.md` es la fuente de verdad del producto y stack: Vue 3 + TypeScript + Vite + Vuetify en la herramienta web; FastAPI + SQLAlchemy + Alembic + PostgreSQL en su backend; Java 21 + Spring Boot 4.x + Spring Data JPA/Hibernate para backend generado; Flutter/Dart para Android generado.

## Estado actual

CU-00 a CU-09 estan implementados. CU-08 protege `/projects` con JWT, usa `current_user.id` para proyectos nuevos y conserva `ProjectDocument`, CAS y Command Bus sin cambios semanticos. CU-09 agrega memberships `EDITOR`/`VIEWER`: el owner se deriva de `projects.owner_id`, editores mutan, viewers solo leen y el owner administra colaboradores. CU-07 persiste `ProjectDocument`, expone lectura y mutaciones con lock/CAS y conecta el editor Vue a `/projects`.

El bridge HTTP temporal de CU-06 fue retirado en CU-07. Los proyectos y mutaciones usan `/projects`; PostgreSQL es la fuente persistente y el cache process-local del bus conserva solo el historial de Undo/Redo de la instancia actual. Tras reiniciar, el documento se recupera desde PostgreSQL y las operaciones nuevas generan historial para la nueva instancia.

La base validada es PostgreSQL local de Windows: `localhost:5432/examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Flujo por CU

1. Revisar `/product.md`, el roadmap PUDS y el CU activo.
2. Aprobar el plan del CU antes de implementar.
3. Implementar un CU por vez en hasta tres incrementos verificables.
4. Registrar evidencia real, deuda y documentacion al cerrar cada incremento.
5. Entregar comandos Git al cerrar el CU sin ejecutarlos salvo peticion explicita.

## Roadmap

`docs/puds/` es la unica fuente de roadmap y CUs. CU-09 administra acceso de colaboradores antes de CU-10 realtime. AWS se implementara en CU-23 y CU-24 ejecutara la aceptacion integral del MVP.

## Editor CU-06

El frontend envia mutaciones como `UmlCommand` al backend y recibe una nueva proyeccion de `ProjectDocument`. El drag se confirma con `SetNodeLayoutCommand`; Undo/Redo pertenecen al backend; el auto-layout usa `d3-dag`. El inspector conserva borradores con cambios sin guardar frente a revisiones externas del documento.

Las relaciones visuales usan un edge custom derivado: association es una linea continua; aggregation/composition muestran diamante hueco/lleno en source; generalization muestra triangulo hueco en target y no multiplicidades. Las otras tres relaciones pueden ser recursivas y se muestran como self-loops curvos seleccionables con labels por extremo. Los self-loops se omiten solo del input de auto-layout, nunca del documento ni del render. La UI previene `source == target` para generalization; la autoridad para ciclos indirectos sigue en backend.

## Benchmarks

Los benchmarks de LLM, STT y VLM viven en `docs/benchmarks/`. Registrar unicamente mediciones reales, configuracion, hardware, fecha y edge cases manuales.
