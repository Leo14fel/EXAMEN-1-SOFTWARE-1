# Registro de decisiones

## ADR-lite 001 — Monorepo con dos proyectos base

**Estado:** aceptada

La fundación contiene `frontend/` y `backend/` en la raíz para mantener el repositorio simple y fácil de navegar.

## ADR-lite 002 — Vue permanece como frontend web

**Estado:** aceptada

Flutter no reemplaza Vue. Flutter corresponde únicamente a la salida móvil Android generada definida por el producto.

## ADR-lite 003 — Dependencias de IA diferidas

**Estado:** aceptada

No se instalan modelos/runtime pesados en la fundación. Se agregarán cuando exista un CU que los necesite.

## ADR-lite 004 — PostgreSQL local validado y Docker opcional

**Estado:** aceptada

El flujo de desarrollo validado usa PostgreSQL local de Windows en `localhost:5432/examen_sw1`. Docker Compose se conserva como alternativa reproducible y publica `localhost:55432` hacia el puerto `5432` del contenedor; no es requisito para desarrollar.

## ADR-lite 005 — Fuentes documentales de verdad

**Estado:** aceptada

`/product.md` es la fuente principal de requisitos y stack. `docs/puds/` es la fuente unica de roadmap y casos de uso; no se mantienen roadmaps alternativos.

## ADR-lite 006 — Command Bus antes del canvas mutable

**Estado:** aceptada

El Command Bus y Undo/Redo se implementan antes del canvas para que toda mutacion del editor use desde el inicio `UmlCommand -> UmlCommandBus -> UmlCommandExecutor -> ProjectDocument`.

## ADR-lite 007 — AWS diferido a su CU de despliegue

**Estado:** aceptada

AWS es un requisito de producto. La seleccion de servicios se difiere al CU de despliegue, que debe contemplar Vue, FastAPI, PostgreSQL, secretos externos y smoke tests sin reemplazar las capacidades locales/offline.

## ADR-lite 008 - Contrato de dominio ProjectDocument

**Estado:** aceptada

`ProjectDocument` es el contenedor central del dominio: UUID estable, metadata JSON-safe, `ownerId` estructural sin autenticacion, revision reservada para concurrencia optimista y timestamps timezone-aware. Pydantic 2 define validacion, serializacion con aliases publicos y rechazo de campos desconocidos.

`CanonicalUmlModel` es la unica fuente semantica. `DiagramLayout` se mantiene separado y solo referencia UUIDs de elementos existentes; no contiene semantica UML.

## ADR-lite 009 - Clases y miembros UML tipados

**Estado:** aceptada

CU-02 representa clases, atributos, operaciones y parametros con modelos Pydantic tipados y `kind` estable. La visibilidad usa `UmlVisibility`; tipos y nombres son strings semanticos no vacios. La ausencia de `returnType` se representa con `null`/`None`; los generadores futuros la mapearan al equivalente del lenguaje destino. Los UUID son globalmente unicos en `CanonicalUmlModel`; relaciones y validaciones entre clases se difieren a CUs posteriores.

## ADR-lite 010 - Relaciones UML semanticas top-level

**Estado:** aceptada

CU-03 amplia `CanonicalUmlModel.elements` con una union discriminada Pydantic por `kind` para clases, asociaciones, agregaciones, composiciones y generalizaciones. Las relaciones contienen UUID estable, `sourceId` y `targetId`; association, aggregation y composition requieren multiplicidades estructuradas explicitas (`lower >= 0`, `upper >= lower` o `"*"`). Association mantiene extremos neutrales. En aggregation y composition, `sourceId` es la clase todo/contenedor y `targetId` la parte/contenido; las multiplicidades homonimas corresponden a esos extremos. En generalization, `sourceId` es la clase hija y `targetId` la clase padre, sin multiplicidades.

La integridad de referencias se valida en el modelo canonico: ambos extremos deben identificar clases del mismo modelo, aunque se permiten autorrelaciones. La unicidad UUID es global entre clases, miembros y relaciones. El layout sigue separado y acepta solo UUIDs de clases, nunca relaciones.
