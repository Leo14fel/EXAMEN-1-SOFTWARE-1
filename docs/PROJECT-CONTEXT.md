# Contexto de continuidad del proyecto

## Uso

Este archivo acompaña snapshots del repositorio. El estado real se obtiene del código y la documentación del snapshot.

## Producto y stack

La herramienta CASE es colaborativa y offline-first para modelado UML de clases. `/product.md` es la fuente de verdad del producto y stack: Vue 3 + TypeScript + Vite + Vuetify en la herramienta web; FastAPI + SQLAlchemy + Alembic + PostgreSQL en su backend; Java 21 + Spring Boot 4.x + Spring Data JPA/Hibernate para backend generado; Flutter/Dart para Android generado.

## Estado actual

CU-00, CU-01, CU-02 y CU-03 estan DONE. CU-03 agrega association, aggregation, composition, generalization y multiplicidades estructuradas a `CanonicalUmlModel`, con validacion y serializacion Pydantic en memoria. Association tiene extremos neutrales; aggregation/composition van de todo a parte y generalization de hija a padre. Los UUID son globalmente unicos y el layout solo contiene nodos de clase.

La base validada es PostgreSQL local de Windows: `localhost:5432/examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Flujo por CU

1. Revisar `/product.md`, el roadmap PUDS y el CU activo.
2. Aprobar el plan del CU antes de implementar.
3. Implementar un CU por vez en hasta tres incrementos verificables.
4. Registrar evidencia real, deuda y documentación al cerrar cada incremento.
5. Entregar comandos Git al cerrar el CU sin ejecutarlos salvo petición explícita.

## Roadmap

`docs/puds/` es la unica fuente de roadmap y CUs. CU-04 es NEXT / NOT_STARTED. La auditoria previa establecio validacion antes del Command Bus y Command Bus antes del canvas mutable. CU-09 administra acceso de colaboradores antes de CU-10 realtime. AWS es requisito de producto y se implementara en CU-23 sin elegir servicios antes de ese CU; CU-24 ejecutara la aceptacion integral del MVP.

## Benchmarks

Los benchmarks de LLM, STT y VLM viven en `docs/benchmarks/`. Registrar únicamente mediciones reales, configuración, hardware, fecha y edge cases manuales.
