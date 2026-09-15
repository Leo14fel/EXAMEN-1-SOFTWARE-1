# CU-05 - Command Bus y Undo/Redo

**Estado:** DONE

## Objetivo

CU-05 establece la ruta oficial para mutar el documento UML en memoria. Evita que una interfaz o futura entrada modifique `ProjectDocument` directamente, centralizando reglas de ejecucion, historial y versionado.

```text
        Add / Update / Remove / Layout
                     |
                     v
                UmlCommand
                     |
                     v
               CommandBus
              /          \
        History          Executor
                           |
                           v
                   ProjectDocument
```

## Alcance implementado

- `UmlCommand` Pydantic serializable, discriminado por `commandType`.
- `AddUmlElementCommand`, `UpdateUmlElementCommand`, `RemoveUmlElementCommand`, `SetNodeLayoutCommand` y `RemoveNodeLayoutCommand`.
- Executor puro `execute_uml_command(document, command) -> ProjectDocument`.
- `UmlCommandBus` con documento actual, execute, undo, redo, `can_undo` y `can_redo`.
- Snapshots completos que restauran `umlModel`, `diagramLayout` y `metadata`.
- Revision monotona y timestamps actualizados en cada operacion exitosa.

No se implementan canvas, API, persistencia, colaboracion, IA, XMI ni comandos para miembros individuales.

## Arquitectura y comandos

Toda futura mutacion UML de UI, canvas, IA, XMI, colaboracion o API debe construir un comando tipado y recorrer `UmlCommand -> UmlCommandBus -> execute_uml_command -> ProjectDocument`; esas capas no deben mutar `ProjectDocument` directamente. `commands.py` contiene contratos y errores; `executor.py` es puro, sin mutacion in-place, DB, red, historial ni efectos externos; `command_bus.py` mantiene snapshots y versionado. `UmlCommandBus` encapsula su estado: `document`, `execute`, `undo` y `redo` entregan copias profundas, por lo que ninguna referencia entregada a consumidores externos permite modificarlo fuera del flujo de comandos.

Add acepta solo elementos top-level soportados y rechaza UUID repetido. Update exige que exista el elemento, que `element.id` sea igual a `elementId` y que no cambie `kind`. Remove rechaza IDs inexistentes; al quitar una clase elimina su node layout pero no hace cascada de relaciones. Si eso deja una relacion sin extremo, se rechaza todo el comando. Los comandos de layout solo operan sobre clases y retirar un layout inexistente es un error explicito.

## Atomicidad, estructura y semantica

El executor construye el resultado antes de que el bus modifique documento o stacks. Un error conserva documento, revision, undo y redo. `UmlCommandExecutionError` tiene codigos estables: `ELEMENT_NOT_FOUND`, `ELEMENT_ALREADY_EXISTS`, `ELEMENT_ID_MISMATCH`, `ELEMENT_KIND_MISMATCH`, `NODE_LAYOUT_NOT_FOUND`, `NODE_LAYOUT_TARGET_NOT_CLASS`, `INVALID_RESULTING_DOCUMENT`, `UNDO_NOT_AVAILABLE` y `REDO_NOT_AVAILABLE`.

El bus solo bloquea invariantes estructurales Pydantic, como referencias de relaciones faltantes o layout huerfano. No ejecuta ni bloquea por `validate_uml_model`: dos clases llamadas `Cliente` pueden agregarse y CU-04 reporta su diagnostico semantico.

## Historial, Undo y Redo

CU-05 usa snapshots completos por simplicidad, correccion, facilidad de pruebas y el tamano reducido actual de los documentos. El historial de undo tiene un maximo fijo de 100 estados: al agregar el snapshot 101, se descarta el mas antiguo y se conservan los 100 mas recientes. El limite evita crecimiento indefinido de memoria sin incorporar comandos inversos ni configuracion dinamica. Execute guarda el estado anterior en undo, actualiza el documento y limpia redo. Undo mueve el actual a redo y restaura el ultimo snapshot; redo realiza la operacion inversa. Por tanto, `execute A`, `execute B`, `undo B`, `execute C` invalida redo.

La restauracion recupera contenido UML, layout y metadata, pero no retrocede version. Cada cambio exitoso incrementa `revision`: 0 inicial, 1 execute, 2 execute, 3 undo, 4 redo. `id`, `ownerId` y `createdAt` se conservan. `updatedAt` recibe una marca nueva y nunca es anterior a la actual.

## Pruebas y evidencia

`backend/tests/domain/test_uml_command_bus.py` contiene 36 pruebas: altas, reemplazos y bajas de clases/relaciones; layouts; errores tipados; atomicidad; encapsulacion de salidas y comandos; semantica no bloqueante; undo/redo simple y multiple; invalidacion de redo; limite de 100 snapshots; revision/timestamp; y serializacion JSON publica de los cinco subtipos y elementos anidados.

| Comando | Resultado real |
|---|---|
| `pytest tests/domain/test_project_document.py -v` | 17 passed |
| `pytest tests/domain/test_uml_classes_members.py -v` | 25 passed |
| `pytest tests/domain/test_uml_relationships.py -v` | 32 passed |
| `pytest tests/domain/test_uml_validation.py -v` | 20 passed |
| `pytest tests/domain/test_uml_command_bus.py -v` | 36 passed |
| `pytest` | 132 passed, 2 warnings externos |
| `python -m compileall app` | OK |
| `ruff check .` | All checks passed |
| `pip check` | No broken requirements found |
| `npm run typecheck` | OK |
| `npm test` | 2 passed |
| `npm run build` | OK |
| `scripts/check.ps1` | OK, todos los checks terminaron correctamente |

No aplica prueba manual: CU-05 es dominio puro sin UI ni infraestructura externa.

## Limitaciones actuales

- El limite de undo es fijo en 100 snapshots; no hay configuracion dinamica ni comandos inversos.
- No hay UI, atajos, persistencia, concurrencia ni comandos inversos.
- Las capas de guardado/generacion decidiran posteriormente cuando la validacion semantica bloquea.

## Estado final

DONE. CU-05 fue revisado y aprobado. CU-06 permanece NEXT / NOT_STARTED y no se implementa como parte de este cierre.

## Git sugerido

```powershell
git add backend/app/domain/uml backend/tests/domain docs
git commit -m "feat(cu-05): add command bus undo redo"
git push -u origin feat/cu-05-command-bus-undo-redo
```

No se ejecutaron commit ni push.
