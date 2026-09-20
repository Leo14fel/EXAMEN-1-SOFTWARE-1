# Contexto de continuidad del proyecto

## Uso

Este archivo acompaña snapshots del repositorio. El estado real se obtiene del código y la documentación del snapshot.

## Producto y stack

La herramienta CASE es colaborativa y offline-first para modelado UML de clases. `/product.md` es la fuente de verdad del producto y stack: Vue 3 + TypeScript + Vite + Vuetify en la herramienta web; FastAPI + SQLAlchemy + Alembic + PostgreSQL en su backend; Java 21 + Spring Boot 4.x + Spring Data JPA/Hibernate para backend generado; Flutter/Dart para Android generado.

## Estado actual

CU-00 a CU-06 estan DONE. CU-07 esta IN_PROGRESS: su Incremento 1 persiste `ProjectDocument` en la tabla `projects` y expone creacion/listado/lectura, sin retirar el bridge temporal. CU-05 establecio `UmlCommand -> UmlCommandBus -> execute_uml_command -> ProjectDocument` como unica ruta de mutacion. CU-06 agrego el canvas UML editable, inspector, relaciones, drag persistido, Undo/Redo y auto-layout sin convertir Vue Flow ni Pinia en fuente de verdad.

El bridge HTTP de CU-06 sigue siendo temporal y process-local: maximo 64 sesiones LRU, un lock por sesion y soporte de un solo worker FastAPI. Reiniciar el backend elimina el estado. CU-07 es NEXT / NOT_STARTED y debe introducir persistencia/recuperacion real conservando `ProjectDocument` como fuente canonica.

La base validada es PostgreSQL local de Windows: `localhost:5432/examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Flujo por CU

1. Revisar `/product.md`, el roadmap PUDS y el CU activo.
2. Aprobar el plan del CU antes de implementar.
3. Implementar un CU por vez en hasta tres incrementos verificables.
4. Registrar evidencia real, deuda y documentacion al cerrar cada incremento.
5. Entregar comandos Git al cerrar el CU sin ejecutarlos salvo peticion explicita.

## Roadmap

`docs/puds/` es la unica fuente de roadmap y CUs. CU-06 esta DONE y CU-07 es el siguiente caso de uso: persistir y recuperar proyectos. CU-08 incorpora auth/ownership. CU-09 administra acceso de colaboradores antes de CU-10 realtime. AWS se implementara en CU-23 y CU-24 ejecutara la aceptacion integral del MVP.

## Editor CU-06

El frontend envia mutaciones como `UmlCommand` al backend y recibe una nueva proyeccion de `ProjectDocument`. El drag se confirma con `SetNodeLayoutCommand`; Undo/Redo pertenecen al backend; el auto-layout usa `d3-dag`. El inspector conserva borradores con cambios sin guardar frente a revisiones externas del documento.

## Benchmarks

Los benchmarks de LLM, STT y VLM viven en `docs/benchmarks/`. Registrar unicamente mediciones reales, configuracion, hardware, fecha y edge cases manuales.
