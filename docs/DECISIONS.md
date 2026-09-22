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

## ADR-lite 011 - Diagnosticos para validacion UML semantica

**Estado:** aceptada

CU-04 separa la validacion semantica de las invariantes estructurales Pydantic. `validate_uml_model` no muta ni corrige el modelo y devuelve todos los `UmlDiagnostic` detectados, en vez de lanzar una excepcion por un error UML habitual. Los codigos y severidades son enums estables para permitir consumo posterior desde API y UI; `isValid` se calcula a partir de la ausencia de diagnosticos `error`.

Las comparaciones de nombres y tipos son exactas y case-sensitive. Para evitar ruido, cada regla de duplicados diagnostica cada ocurrencia posterior a la primera en orden canónico; el DFS de generalizaciones registra un diagnostico por arista de retorno detectada en orden de elementos. Las reglas de tipos, paquetes, herencia multiple y ownership se difieren.

## ADR-lite 012 - Command Bus con snapshots locales

**Estado:** aceptada

Todas las mutaciones UML futuras deben pasar por `UmlCommand -> UmlCommandBus -> UmlCommandExecutor -> ProjectDocument`; ninguna entrada modifica el documento directamente. Los comandos son modelos Pydantic discriminados por `commandType`, para permitir serializacion y reutilizacion posterior.

Undo/Redo usa snapshots completos inicialmente por simplicidad, correccion y facilidad de pruebas. El historial de undo tiene un limite fijo de 100 estados: al superar el limite se descarta el snapshot mas antiguo para evitar crecimiento indefinido de memoria y conservar los 100 mas recientes. `UmlCommandBus` encapsula su estado mediante copias profundas: ninguna referencia de documento o resultado entregada a un consumidor puede modificar el estado interno fuera de comandos. El executor tambien devuelve un documento independiente de sus entradas y comandos. `revision` es monotona incluso durante undo/redo y `updatedAt` se renueva sin retroceder; identidad, ownership y fecha de creacion se conservan. La validacion semantica no bloquea comandos estructuralmente validos.

## ADR-lite 013 - Canvas Vue conectado al Command Bus por sesiones HTTP temporales

**Estado:** reemplazada por ADR-lite 018

CU-06 mantiene una unica implementacion autoritativa de mutaciones UML en Python. El frontend Vue no replica `UmlCommandBus`, atomicidad, historial ni validaciones estructurales. En su lugar, usa un adaptador HTTP de sesiones efimeras en memoria: Vue envia `UmlCommand` serializados, FastAPI los ejecuta mediante el bus canonico y devuelve `ProjectDocument`, `canUndo` y `canRedo`.

La memoria del proceso no se considera persistencia y se pierde al reiniciar FastAPI. Esta decision fue temporal para CU-06 y se retiro en CU-07 Incremento 3.

## ADR-lite 014 - Vue Flow es proyeccion, no modelo de dominio

**Estado:** aceptada

CU-06 convierte `ProjectDocument` en nodes/edges mediante un mapper puro. Vue Flow no almacena una segunda version del UML ni decide reglas semanticas. Las posiciones fallback de clases sin `DiagramLayout` son deterministas pero transitorias. Hasta Incremento 3 los nodos no son arrastrables para evitar que una posicion visual aparente ser persistida sin pasar por `SetNodeLayoutCommand`.

El grid usa CSS y los controles llaman acciones de viewport de `@vue-flow/core`; no agregan logica de dominio ni nuevas dependencias.

## ADR-lite 015 - Edicion del canvas sin mutacion paralela

**Estado:** aceptada

Vue Flow puede mover visualmente un node durante el drag, pero el cambio real se confirma solo con `SetNodeLayoutCommand` en `node-drag-stop`. Toolbox e inspector construyen comandos publicos y esperan el nuevo `ProjectDocument` del backend. No existe historial, validacion estructural ni cascada de borrado duplicada en TypeScript.

El inspector conserva el `kind` de una relacion al actualizarla porque CU-05 rechaza `ELEMENT_KIND_MISMATCH`. Cambiar association/aggregation/composition/generalization requiere eliminar y volver a crear la relacion. Una clase con relaciones no se ofrece para borrado hasta retirar esas relaciones, coherente con el rechazo atomico del executor.

## ADR-lite 016 - ProjectDocument persistido como columnas tipadas y JSONB separado

**Estado:** aceptada

CU-07 persiste un unico `ProjectDocument` por fila en `projects`. Los metadatos de proyecto, revision, propiedad estructural e identidad/timestamps usan columnas tipadas; `CanonicalUmlModel` y `DiagramLayout` se guardan como `JSONB` separados. Esto conserva la forma JSON-safe Pydantic, evita dos fuentes de verdad y no adelanta tablas relacionales para elementos UML. Las lecturas deben revalidar el payload mediante `ProjectDocument.model_validate(...)`.

## ADR-lite 017 - Lock local y CAS para mutaciones persistentes

**Estado:** aceptada

CU-07 serializa execute, undo y redo por `projectId` con un lock process-local, porque `UmlCommandBus` mantiene estado mutable. PostgreSQL mantiene la autoridad entre procesos mediante `UPDATE ... WHERE id AND revision`. La cache process-local de buses solo conserva historial local y se invalida ante conflicto o error de persistencia; los snapshots no se guardan en PostgreSQL ni sobreviven un reinicio.

## ADR-lite 018 - Editor Vue conectado a proyectos persistentes

**Estado:** aceptada

El frontend usa `/projects` para listar, crear, abrir y mutar. El store Pinia adjunta `baseRevision` en cada comando, Undo y Redo, y reemplaza el documento local con la respuesta autoritativa. Un conflicto de revision recarga el documento y limpia los indicadores de historial. El bridge `/editor/sessions` de CU-06 fue eliminado al completar esta migracion.

## ADR-lite 019 - Admisibilidad de herencia en comandos

**Estado:** aceptada

Los diagnosticos UML permanecen separados de las invariantes estructurales y no bloquean comandos de forma general. Sin embargo, una generalization autoreferenciada o ciclica nunca es un estado admisible del editor. El executor construye el modelo candidato y consulta una funcion pura del dominio que reutiliza las reglas de validacion existentes para detectar exclusivamente `GENERALIZATION_SELF_REFERENCE` y `GENERALIZATION_CYCLE`; ante una de ellas rechaza el comando antes de modificar snapshots, revision o persistencia.

Las autorrelaciones de association, aggregation y composition se mantienen permitidas: describen una relacion entre instancias de un mismo classifier y no implican que una instancia se contenga a si misma. Dependency, Realization, roles de extremo, navegabilidad y asociaciones n-arias siguen fuera del dominio actual.

## ADR-lite 020 - Edges UML derivados y self-loops visuales

**Estado:** aceptada

Vue Flow sigue siendo una proyeccion de `ProjectDocument`. Un edge reutilizable recibe datos derivados por `projectDocumentToFlow()` para renderizar los markers UML existentes, labels de multiplicidad por extremo y una curva lateral para self-loops. Usa el hitbox y eventos nativos de `BaseEdge`, por lo que la seleccion sigue la misma ruta Vue Flow -> `selectedElementId` -> inspector.

Los self-loops se excluyen solamente del grafo de `d3-dag`; no se eliminan ni se persisten datos visuales adicionales. Las relaciones paralelas reciben una desviacion Bezier derivada minima para no quedar completamente superpuestas. No se agregan tipos UML, roles, navegabilidad ni routing avanzado.
