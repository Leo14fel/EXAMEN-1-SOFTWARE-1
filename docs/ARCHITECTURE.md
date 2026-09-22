# Arquitectura inicial

## Alcance de esta fundación

```text
Monorepo
├── frontend/  -> herramienta CASE web
├── backend/   -> API de la herramienta CASE
└── docs/      -> especificación y estado
```

No se implementan todavía:

- dominio UML completo;
- colaboración realtime;
- IA/STT;
- importación XMI;
- generadores Spring Boot;
- generador Flutter;
- infraestructura AWS.

## Aplicación principal

```text
Vue 3 + TypeScript
        |
        | HTTP / WebSocket (futuro)
        v
FastAPI + Python
        |
        v
PostgreSQL
```

## Salidas futuras definidas por el producto

```text
CanonicalUmlModel
       |
       +--> Backend generado: Java 21 + Spring Boot
       |
       +--> Mobile generado: Flutter + Dart -> Android
```

La aplicación Flutter generada no debe confundirse con el frontend web Vue del producto principal.

## Base incluida hoy

- `GET /health` en FastAPI, independiente de PostgreSQL.
- `GET /health/db` para verificar FastAPI -> SQLAlchemy -> PostgreSQL.
- configuración central mínima;
- capa de sesión SQLAlchemy preparada;
- Alembic preparado, sin migraciones de dominio;
- Vue/Vuetify/Pinia preparados;
- Vue Flow y d3-dag instalados pero sin inventar el editor UML;
- smoke test frontend;
- smoke test backend;
- PostgreSQL local de Windows validado en `localhost:5432/examen_sw1`.
- Docker Compose como alternativa reproducible opcional en `localhost:55432` hacia `5432` dentro del contenedor.

## Dominio UML base

```text
ProjectDocument
├── id, metadata, ownerId, revision, createdAt, updatedAt
├── umlModel: CanonicalUmlModel
└── diagramLayout: DiagramLayout
```

`CanonicalUmlModel` es la fuente semántica canónica y conserva elementos UML identificados. `DiagramLayout` contiene exclusivamente posiciones y tamaños visuales asociados a esos UUIDs. El layout no es fuente de verdad y no contiene semántica UML.

Los elementos top-level forman una union discriminada por `kind`: `UmlClass`, `UmlAssociation`, `UmlAggregation`, `UmlComposition` y `UmlGeneralization`. Las relaciones conservan semantica (`sourceId`, `targetId` y multiplicidades cuando aplican), pero no son nodos visuales. `DiagramLayout.nodes` solo puede referenciar clases. La identidad UUID es global entre elementos top-level y miembros anidados.

`models.py` conserva contratos Pydantic e invariantes estructurales. `app.domain.uml.validation` contiene el validador semantico puro `validate_uml_model`, que recibe un `CanonicalUmlModel` inmutable y devuelve `UmlValidationResult` con diagnosticos tipados; no corrige el modelo ni lanza excepciones por errores UML normales. Esta capa sera reutilizada por las futuras entradas, persistencia y generacion.

## Mutaciones UML

```text
UmlCommand -> UmlCommandBus -> UmlCommandExecutor -> ProjectDocument
```

Las entradas futuras manual, canvas, texto, voz, imagen, XMI, colaboracion y API deberan construir un `UmlCommand` Pydantic discriminado por `commandType`; no modifican `ProjectDocument` directamente. El executor es puro y construye un documento nuevo independiente de sus entradas, mientras que el bus mantiene snapshots en memoria para undo/redo y aplica revision monotona y `updatedAt` nuevo. El bus entrega copias profundas a consumidores externos para encapsular su estado. El historial de undo conserva como maximo 100 snapshots, descartando el mas antiguo al superar ese limite para acotar memoria. La validacion semantica de CU-04 queda separada: los comandos solo bloquean invariantes estructurales.

## Regla de evolución

No crear arquitectura para una capacidad futura hasta que un caso de uso aprobado la necesite.

## Editor persistente - CU-07

```text
Vue / Pinia (proyeccion cliente)
        |
        | HTTP + UmlCommand JSON + baseRevision
        v
FastAPI /projects
        |
        v
Lock por proyecto + UmlCommandBus canonico
        |
        v
ProjectDocument -> PostgreSQL
```

El frontend lista, crea y abre proyectos persistidos. Pinia y Vue Flow reciben una proyeccion autoritativa; las mutaciones pasan por `/projects/{projectId}/commands`, Undo y Redo incluyen la revision actual. Ante conflicto de revision el frontend recarga el documento y descarta el historial visual. El `ownerId` temporal sigue siendo estructural hasta CU-08.

## Proyeccion Vue Flow - CU-06 Incremento 2

`ProjectDocument` sigue siendo la unica fuente de verdad semantica. `projectDocumentToFlow()` deriva de manera determinista `Node[]` y `Edge[]` para `@vue-flow/core`: clases se convierten en nodes y relaciones top-level en edges. `DiagramLayout` se consume solo para posiciones/dimensiones existentes; una posicion fallback sin layout es exclusivamente visual y no muta el documento.

Incremento 2 mantiene `nodesDraggable=false`, `nodesConnectable=false` y no ofrece borrado. Zoom, pan, seleccion, Background y Controls son interaccion visual local. La persistencia de posicion mediante `SetNodeLayoutCommand` pertenece al Incremento 3.

## Edicion manual del canvas - CU-06 Incremento 3

El canvas permite drag visual, pero solo persiste la posicion al finalizar el movimiento mediante `SetNodeLayoutCommand`. Creacion, actualizacion y borrado de elementos utilizan `addElement`, `updateElement` y `removeElement`; Undo/Redo llaman al historial canonico del backend. El inspector nunca modifica `ProjectDocument` directamente.

`d3-dag` calcula posiciones de auto-layout en frontend. Cada posicion calculada se envia despues como `SetNodeLayoutCommand`, por lo que el documento canonico sigue siendo la fuente de verdad. En CU-06 el auto-layout puede producir varias entradas de historial, una por clase, porque no existe un comando compuesto y no se introduce uno artificialmente en este CU.

## Relaciones visuales - UML Editor Completeness

`projectDocumentToFlow()` deriva las relaciones soportadas como edges UML: association conserva una linea simple; aggregation usa diamante hueco en `sourceId`; composition usa diamante lleno en `sourceId`; y generalization usa triangulo hueco en `targetId`. Las multiplicidades de association, aggregation y composition se derivan como labels independientes junto a cada extremo; generalization no recibe labels de multiplicidad.

Cuando `sourceId == targetId`, el mapper marca un self-loop y el edge Vue Flow reutilizable dibuja una curva Bezier lateral con un hitbox ampliado. El edge sigue usando la seleccion nativa de Vue Flow, por lo que alimenta el mismo inspector y no crea estado semantico paralelo. Association, aggregation y composition pueden usar esta representacion; generalization autorreferenciada permanece bloqueada por el backend.

El auto-layout excluye self-loops solo del grafo de `d3-dag`, porque no aportan jerarquia de nodos. No elimina ni modifica la relacion del `ProjectDocument`; todos los edges siguen renderizandose despues del layout. Dependency, Realization, roles de extremo, navegabilidad y asociaciones n-arias no estan implementados.

## Persistencia de proyectos - CU-07 Incremento 1

`projects` conserva una fila por `ProjectDocument`: identidad, owner estructural, metadata, revision y timestamps son columnas tipadas; `uml_model` y `diagram_layout` son columnas `JSONB` separadas. La persistencia no modela elementos UML en tablas relacionales ni reemplaza el documento como fuente canonica. Cada lectura reconstruye el documento mediante Pydantic antes de entregarlo.

El Incremento 2 agrega mutaciones en `/projects/{projectId}/commands`, `/undo` y `/redo`. Cada una serializa acceso con un lock process-local por proyecto, lee la revision autoritativa de PostgreSQL y aplica CAS al persistir el documento producido por `UmlCommandBus`. La cache de buses solo mantiene historial local: se descarta ante conflicto o fallo de almacenamiento y no se reconstruye tras reinicio.

## Autenticacion y ownership - CU-08

`users` almacena identidad minima y hash Argon2. Bearer JWT se valida antes de `/projects`; listas se filtran por `owner_id` y recursos ajenos devuelven 404. El dominio UML, locks y CAS no cambian. La migracion agrega usuarios e indice sin FK sobre `projects.owner_id`, preservando UUID legacy no verificables.
