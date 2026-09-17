# Contexto de continuidad del proyecto

## Uso

Este archivo acompaña snapshots del repositorio. El estado real se obtiene del código y la documentación del snapshot.

## Producto y stack

La herramienta CASE es colaborativa y offline-first para modelado UML de clases. `/product.md` es la fuente de verdad del producto y stack: Vue 3 + TypeScript + Vite + Vuetify en la herramienta web; FastAPI + SQLAlchemy + Alembic + PostgreSQL en su backend; Java 21 + Spring Boot 4.x + Spring Data JPA/Hibernate para backend generado; Flutter/Dart para Android generado.

## Estado actual

CU-00 a CU-05 estan DONE. CU-05 establece que toda futura mutacion UML de UI, canvas, IA o XMI recorre `UmlCommand -> UmlCommandBus -> execute_uml_command -> ProjectDocument`; ninguna capa futura modifica `ProjectDocument` directamente. El executor es puro y no muta entradas in-place. El bus encapsula estado y sus consumidores reciben copias seguras. Undo/Redo usa snapshots completos, mantiene un maximo de 100 estados de undo y descarta el mas antiguo al superar el limite. La revision es monotona incluso durante undo/redo, `updatedAt` no retrocede y un comando nuevo despues de undo invalida redo. Los errores usan codigos estables; la validacion semantica no bloquea comandos estructuralmente validos y eliminar una clase referenciada se rechaza atomicamente, sin cascada. CU-06 esta IN_PROGRESS - Incremento 1 pendiente de validacion. CU-03 aporta association, aggregation, composition, generalization y multiplicidades estructuradas; los UUID son globalmente unicos y el layout solo contiene nodos de clase.

La base validada es PostgreSQL local de Windows: `localhost:5432/examen_sw1`, usuario `postgres`. Docker Compose es opcional y publica `localhost:55432` hacia `5432` dentro del contenedor.

## Flujo por CU

1. Revisar `/product.md`, el roadmap PUDS y el CU activo.
2. Aprobar el plan del CU antes de implementar.
3. Implementar un CU por vez en hasta tres incrementos verificables.
4. Registrar evidencia real, deuda y documentación al cerrar cada incremento.
5. Entregar comandos Git al cerrar el CU sin ejecutarlos salvo petición explícita.

## Roadmap

`docs/puds/` es la unica fuente de roadmap y CUs. CU-06 esta IN_PROGRESS - Incremento 1 pendiente de validacion. La auditoria previa establecio validacion antes del Command Bus y Command Bus antes del canvas mutable. CU-09 administra acceso de colaboradores antes de CU-10 realtime. AWS es requisito de producto y se implementara en CU-23 sin elegir servicios antes de ese CU; CU-24 ejecutara la aceptacion integral del MVP.

## Benchmarks

Los benchmarks de LLM, STT y VLM viven en `docs/benchmarks/`. Registrar únicamente mediciones reales, configuración, hardware, fecha y edge cases manuales.
## CU-06 - puente temporal del editor

El Incremento 1 conecta el frontend Vue con el UmlCommandBus canonico mediante sesiones HTTP temporales en memoria. Pinia conserva una proyeccion del estado recibido y no modifica ProjectDocument directamente. No existe persistencia de sesiones en CU-06; reiniciar FastAPI elimina el estado y CU-07 incorporara almacenamiento real.

## CU-06 Incremento 2 - proyeccion visual

El canvas usa `@vue-flow/core` como superficie visual, con grid CSS y controles locales de zoom/fit. Las clases se renderizan mediante un nodo UML propio y las relaciones como edges. Esta capa consume `ProjectDocument` y no lo modifica; la edicion persistente entra en el Incremento 3 usando los comandos de CU-05.

## CU-06 Incremento 3 - editor mutable

La UI crea y edita UML exclusivamente mediante comandos HTTP hacia el `UmlCommandBus`. El drag solo se persiste en `node-drag-stop`. El auto-layout usa `d3-dag` para calcular geometria y despues confirma cada layout con `SetNodeLayoutCommand`. Undo/Redo son los del backend, no un historial de Vue Flow.

## CU-06 cerrado / CU-07 siguiente

El editor UML web ya permite crear y editar clases, atributos, operaciones, parametros y relaciones; mover nodos; Undo/Redo; y auto-layout. Toda mutacion sigue pasando por `UmlCommandBus`. CU-07 debe introducir persistencia/recuperacion de proyectos conservando `ProjectDocument` como fuente de verdad. La sesion HTTP temporal de CU-06 no debe considerarse persistencia.
