# CU-06 - Editar el diagrama desde el canvas

**Estado:** DONE

## 1. Objetivo

Proyectar `ProjectDocument` en el frontend Vue mediante un canvas UML sin convertir la interfaz en fuente de verdad. Toda mutacion debe seguir usando el `UmlCommandBus` canonico implementado en Python.

## 2. Actor(es)

Usuario de modelado UML.

## 3. Dependencias

CU-01 a CU-05 terminados.

## 4. Referencias a product.md

`/product.md`, secciones de arquitectura, editor UML, frontend web y Command Bus.

## 5. Alcance

### Incluye

- Puente HTTP temporal entre Vue y `UmlCommandBus`.
- Sesiones de editor en memoria, sin persistencia.
- Contratos TypeScript espejo de la forma publica de `ProjectDocument` y `UmlCommand`.
- Store Pinia como proyeccion del estado autoritativo recibido del backend.
- Canvas `@vue-flow/core`.
- Clases como nodos UML personalizados.
- Relaciones como edges de lectura.
- Zoom, pan, Background, Controls y seleccion.
- En el Incremento 3: movimiento persistido, creacion, inspector, Undo/Redo UI y auto-layout `d3-dag`.

### Fuera de alcance

- PostgreSQL para proyectos.
- autenticacion y ownership real de usuario.
- WebSocket, realtime y presencia.
- IA, XMI, generadores, Flutter y AWS.

## 6. Precondiciones

CU-05 cerrado. Frontend Vue 3/Vuetify/Pinia disponible. `@vue-flow/core` y `d3-dag` ya formaban parte del stack. Incremento 2 no agrega dependencias: el grid se resuelve con CSS y los controles usan las acciones de viewport de `@vue-flow/core`.

## 7. Escenarios / flujo principal

1. El frontend crea una sesion temporal de editor.
2. FastAPI crea un `ProjectDocument` vacio y un `UmlCommandBus` en memoria.
3. Vue recibe `document`, `canUndo` y `canRedo`.
4. Pinia reemplaza su proyeccion local con la respuesta.
5. El mapper `projectDocumentToFlow()` deriva nodes/edges sin mutar el documento.
6. Vue Flow renderiza clases y relaciones; seleccion, zoom y pan son estado visual.
7. Las mutaciones reales se envian como `UmlCommand` al backend.

## 8. Plan aprobado

CU-06 usa tres incrementos verificables.

## 9. Incrementos

### Incremento 1 - Puente Vue -> Command Bus

**Objetivo:** conectar Vue con el dominio Python sin duplicar Command Bus ni adelantar persistencia.

**Implementado:** API de sesiones en memoria, endpoints command/undo/redo, contratos TypeScript, cliente HTTP y store Pinia.

**Resultado real:** APROBADO.

Evidencia:
- API editor: 5 passed.
- Backend completo: 137 passed, 2 warnings externos.
- Ruff: OK.
- Frontend: 7 passed.
- Frontend typecheck: OK.
- Frontend build: OK.
- `scripts/check.ps1`: OK.

### Incremento 2 - Canvas de lectura

**Objetivo:** proyectar el documento canonico mediante Vue Flow.

**Implementado:** mapper determinista `ProjectDocument -> nodes/edges`, nodo de clase UML, relaciones como edges, workspace del editor, seleccion, zoom/pan, grid CSS y controles locales de viewport.

**Evidencia de I2:** durante este incremento los nodos se mantuvieron `nodesDraggable=false`; el movimiento persistido se habilito y valido en I3.

**Resultado real:** APROBADO. 12 tests frontend, typecheck/build/gate completos y prueba manual con sesion real/canvas vacio.

### Incremento 3 - Edicion del canvas y cierre

**Objetivo:** habilitar modificaciones reales mediante `UmlCommand`.

**Implementado:** movimiento persistido con `SetNodeLayoutCommand`, crear/editar clases y relaciones, Undo/Redo UI, inspector, auto-layout `d3-dag`, validacion manual integral y cierre documental.

**Resultado real:** APROBADO. Typecheck, tests, build, gate completo y prueba manual integral del editor completados.

## 10. Diseno y decisiones utilizadas

El Command Bus permanece unicamente en Python. Vue Flow es una proyeccion visual derivada de `ProjectDocument`.

```text
ProjectDocument
      |
      v
projectDocumentToFlow
   /             \
 nodes           edges
   \             /
       Vue Flow
```

El mapper no tiene efectos secundarios. Si una clase posee `DiagramLayout`, usa sus coordenadas y dimensiones. Si aun no existe layout, genera una posicion determinista solo para visualizacion; no escribe esa posicion en el documento.

Association, aggregation, composition y generalization conservan `sourceId` y `targetId` definidos por el dominio. Incremento 2 distingue las relaciones mediante etiqueta/color; marcadores UML especializados se completan junto con la edicion final si resultan necesarios.

I2 mantuvo el canvas read-only respecto al dominio. I3 habilito drag persistente, creacion, edicion y borrado, siempre mediante `UmlCommand` hacia el backend; Vue Flow nunca modifica `ProjectDocument` directamente.

## 11. Arquitectura

```text
Vue Flow (proyeccion visual)
        ^
        |
ProjectDocument recibido por Pinia
        ^
        |
FastAPI /editor/sessions
        |
UmlCommandBus
```

Pinia y Vue Flow no son fuentes semanticas de verdad.

## 12. Archivos principales

Incremento 1:
- `backend/app/api/editor.py`
- `backend/tests/api/test_editor_sessions.py`
- `frontend/src/features/editor/types.ts`
- `frontend/src/features/editor/editor-api.ts`
- `frontend/src/features/editor/editor-store.ts`

Incremento 2:
- `frontend/src/features/editor/EditorWorkspace.vue`
- `frontend/src/features/editor/canvas/project-to-flow.ts`
- `frontend/src/features/editor/canvas/UmlClassNode.vue`
- `frontend/src/features/editor/canvas/UmlCanvas.vue`
- pruebas de mapper/nodo/App.
- `frontend/src/App.vue`
- `frontend/src/main.ts`
- `frontend/src/plugins/vuetify.ts`
- `frontend/src/styles/main.css`

## 13. Pruebas automaticas

| Prueba/comando | Resultado |
|---|---|
| API editor I1 | 5 passed |
| backend completo I1 | 137 passed, 2 warnings externos |
| Ruff I1 | OK |
| frontend I1 | 7 passed |
| typecheck I1 | OK |
| build I1 | OK |
| gate I1 | OK |
| mapper/node/App I2 | OK |
| frontend completo I2 | 12 passed |
| gate completo I2 | OK |

## 14. Pruebas manuales

En Incremento 2 se valido:
- carga de la pantalla `Editor UML`;
- canvas vacio al iniciar una sesion nueva;
- grid y controles locales de viewport visibles;
- zoom y pan;
- ausencia de errores de consola;
- ausencia de movimiento/creacion/borrado durante la fase read-only.

Las pruebas visuales con clases/relaciones se completaron en Incremento 3 al habilitar la edicion por comandos.

## 15. Errores encontrados e iteraciones

Durante Incremento 1 dos scripts documentales fallaron por coincidencias fragiles/codificacion de PowerShell 5.1. Se corrigio el proceso para usar UTF-8 explicito y busquedas estructurales. El codigo funcional del Incremento 1 no resulto afectado.

Los warnings de componentes Vuetify observados en `App.spec.ts` durante I1 se corrigen en I2 registrando explicitamente `vuetify/components` y `vuetify/directives`.

## 16. Benchmarks relacionados

No aplica.

## 17. Documentacion actualizada

CU-06, arquitectura, decisiones, estado, handoff, contexto, testing y roadmap.

## 18. Deuda tecnica y riesgos restantes

- Las sesiones siguen siendo efimeras hasta CU-07 y se pierden al reiniciar FastAPI.
- El bridge temporal es process-local, soporta un solo worker y esta limitado a 64 sesiones LRU.
- Cada sesion serializa lecturas y mutaciones con un lock; almacenamiento compartido/realtime quedan fuera de CU-06.
- Los contratos TypeScript deben mantenerse sincronizados con la forma publica Python.

## 19. Criterios de aceptacion y evidencia

- [x] Vue puede crear/leer una sesion temporal.
- [x] Los comandos HTTP reutilizan `UmlCommandBus`.
- [x] Pinia no implementa historial paralelo.
- [x] Incremento 1 pasa el gate completo.
- [x] `ProjectDocument` se proyecta correctamente en Vue Flow.
- [x] Canvas read-only pasa typecheck/tests/build.
- [x] Prueba manual del canvas read-only.
- [x] Incremento 3 completa edicion y cierre.

## 20. Estado final

DONE. Los tres incrementos fueron implementados y validados.

## 21. Commit y push

Commit base de CU-06: `f32dc53 feat(cu-06): implement UML canvas editor`. Los ajustes derivados del review del PR #1 se agregan como un commit de correccion en la misma rama antes del merge.
## 22. Evidencia final CU-06

Validacion automatica final:

- Backend: 139 tests passed, 2 warnings externos.
- Ruff: OK.
- pip check: OK.
- Frontend typecheck: OK.
- Frontend: 22 tests passed en 9 archivos.
- Frontend build: OK.
- scripts/check.ps1: OK.

Validacion manual final:

- sesion de editor creada correctamente;
- creacion de clases;
- edicion de nombre, atributos y operaciones;
- creacion de relaciones;
- seleccion e inspector;
- movimiento de nodos con incremento de revision;
- Undo y Redo;
- auto-layout con incremento de revision por cada SetNodeLayoutCommand;
- canvas, zoom y controles funcionando sin errores bloqueantes.

CU-06 queda cerrado y CU-07 pasa a ser el siguiente caso de uso.

## 23. Ajustes por review del PR #1

Antes del merge se revisaron los hallazgos de Copilot:

- el bridge de sesiones permanece intencionalmente en memoria, pero ahora esta acotado a 64 sesiones LRU y documentado como single-worker;
- cada sesion serializa estado/execute/undo/redo mediante un lock propio;
- las requests activas pinnean su sesion y quedan excluidas del eviction; si toda la capacidad esta activa, una nueva sesion responde `503 EDITOR_SESSION_CAPACITY_REACHED`;
- la creacion de relaciones respeta `busy` y el dialogo bloquea reenvios mientras hay una mutacion en vuelo;
- el inspector conserva borradores dirty cuando una revision externa cambia por drag/auto-layout u otro comando;
- la prueba de auto-layout exige jerarquia vertical en una relacion `source -> target`, evitando que un fallback de grilla oculte una falla del layout;
- se corrigieron estados `IN_PROGRESS`/`PENDING`, checklists y referencias documentales obsoletas.

La implementacion `import { dagre } from 'd3-dag'`, `new dagre.graphlib.Graph()` y `dagre.layout(...)` se conserva: corresponde a la API dagre-compatible expuesta por `d3-dag` 1.2.2.
