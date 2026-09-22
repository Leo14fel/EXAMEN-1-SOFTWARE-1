# CU-03 - Relaciones UML

**Estado:** DONE

## 1. Objetivo

Representar relaciones UML semanticas entre clases dentro de `CanonicalUmlModel`, sin introducir canvas, comandos ni reglas UML avanzadas.

## 2. Actor(es)

Usuario de modelado. Puede construir y serializar en memoria clases relacionadas con multiplicidades estructuradas.

## 3. Dependencias

CU-00, CU-01 y CU-02 terminados.

## 4. Referencias a product.md

`/product.md`, secciones 3, 6, 7, 8, 9 y 11.

## 5. Alcance

### Incluye

- `UmlAssociation`, `UmlAggregation`, `UmlComposition` y `UmlGeneralization` top-level.
- `UmlMultiplicity` estructurada con `lower: int >= 0` y `upper: int | "*"`.
- Union discriminada Pydantic por `kind` para todos los elementos top-level.
- Referencias `sourceId` y `targetId` exclusivamente a clases del mismo modelo.
- UUID globalmente unicos entre clases, miembros anidados y relaciones.
- Layout restringido a clases y round-trip JSON de todos los tipos concretos.

### Fuera de alcance

- Ciclos de herencia, herencia multiple, duplicados semanticos y reglas avanzadas de composicion.
- Diagnosticos UML, Command Bus, canvas, edges, routing, persistencia, API, frontend, XMI, generacion e IA.

## 6. Precondiciones

Python 3.13, Pydantic 2 y CU-02 instalados. No requiere PostgreSQL, Docker ni red.

## 7. Escenarios / flujo principal

1. Crear clases y relaciones con UUID estables.
2. Declarar multiplicidades explicitas para association, aggregation y composition.
3. Validar que los extremos referencian clases existentes; una autorrelacion es valida.
4. Serializar `ProjectDocument` con aliases camelCase y reconstruir los tipos concretos.

## 8. Plan aprobado

Un incremento: evolucionar el contrato Pydantic, agregar pruebas de dominio y sincronizar documentacion. No se implementa CU-04 ni trabajo posterior.

## 9. Incrementos

### Incremento 1

**Objetivo:** entregar relaciones UML top-level serializables y estructuralmente validadas.

**Cambios realizados:** se agregaron las relaciones, multiplicidad, union discriminada, validacion de referencias e IDs globales; se restringio el layout a clases.

**Pruebas:** suites CU-01/CU-02/CU-03, regresion backend, compileall, Ruff, pip check, regresion frontend y gate PowerShell.

**Resultado real:** todos los checks finales verdes; pytest conserva dos warnings externos de FastAPI/Starlette/AnyIO.

## 10. Diseño y decisiones utilizadas

`CanonicalUmlModel.elements` es `list[CanonicalUmlElement]`, donde `CanonicalUmlElement` es una union discriminada por `kind` de `UmlClass`, `UmlAssociation`, `UmlAggregation`, `UmlComposition` y `UmlGeneralization`. No usa `Any`, diccionarios genericos ni serializacion polimorfica de escape.

Las relaciones comparten `id`, `sourceId` y `targetId` mediante una base minima. En association, source y target son extremos neutrales. En aggregation y composition, `sourceId` es la clase todo/contenedor y `targetId` es la clase parte/contenido; por ejemplo, `Pedido -> LineaPedido` usa `sourceId = Pedido` y `targetId = LineaPedido`. Association, aggregation y composition requieren `sourceMultiplicity` y `targetMultiplicity` sin defaults ocultos: cada multiplicidad corresponde a su extremo homonimo. Generalization no tiene multiplicidades: `sourceId` es la clase hija y `targetId` la clase padre.

`CanonicalUmlModel` recorre clases, atributos, operaciones, parametros y relaciones para mantener UUID globalmente unicos. Tambien verifica que ambos extremos de cada relacion sean UUIDs de `UmlClass`; no se permiten referencias inexistentes ni a relaciones. Las autorrelaciones son validas.

`DiagramLayout` permanece visual: `ProjectDocument` admite nodos solo para UUIDs de clases, nunca para relaciones. No se introducen edges ni datos de routing.

## 11. Implementación realizada

```text
CanonicalUmlElement (kind discriminado)
├── UmlClass                 kind = "class"
├── UmlAssociation           kind = "association"
├── UmlAggregation           kind = "aggregation"
├── UmlComposition           kind = "composition"
└── UmlGeneralization        kind = "generalization"

UmlMultiplicity
├── lower: int >= 0
└── upper: int | "*"
```

Para `upper` numerico se exige `upper >= 0` y `upper >= lower`. `lower` y `upper` numerico usan `StrictInt`, por lo que booleanos tambien se rechazan. Los campos rechazan extras. `model_dump_json(by_alias=True)` seguido de `ProjectDocument.model_validate_json(...)` conserva relaciones, multiplicidades, clases, miembros y layout de clases como tipos concretos.

## 12. Archivos/componentes principales afectados

- `backend/app/domain/uml/models.py`
- `backend/app/domain/uml/__init__.py`
- `backend/tests/domain/test_uml_relationships.py`
- `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/STATUS.md`, `docs/HANDOFF.md`, `docs/PROJECT-CONTEXT.md` y roadmap PUDS.

## 13. Pruebas automáticas

| Prueba/comando | Resultado | Evidencia/nota |
|---|---|---|
| `pytest tests/domain/test_uml_relationships.py -v` | OK | 32 passed. |
| `pytest tests/domain/test_project_document.py -v` | OK | 17 passed. |
| `pytest tests/domain/test_uml_classes_members.py -v` | OK | 25 passed. |
| `pytest` | OK | 76 passed, 2 warnings externos. |
| `python -m compileall app` | OK | Dominio compilado. |
| `ruff check .` | OK | All checks passed. |
| `pip check` | OK | No broken requirements found. |
| `npm run typecheck` | OK | Sin cambios frontend. |
| `npm test` | OK | 2 passed. |
| `npm run build` | OK | Build Vite correcto. |
| `scripts/check.ps1` | OK | Todos los checks terminaron correctamente. |

## 14. Pruebas manuales

No aplica: CU-03 implementa contrato de dominio sin UI ni infraestructura externa.

## 15. Errores encontrados e iteraciones de corrección

Sin incidencias al ejecutar la suite especifica inicial.

## 16. Benchmarks relacionados

No aplica: CU-03 no introduce LLM, VLM ni STT.

## 17. Documentación actualizada

Este documento, arquitectura, decisiones, estado, handoff, contexto y roadmap PUDS.

## 18. Deuda técnica y riesgos restantes

- CU-04 debe introducir diagnosticos y reglas UML de negocio sin alterar la estructura de relaciones salvo necesidad aprobada.
- No existen edges, estilos ni geometria de relaciones hasta el CU de canvas.

## 19. Criterios de aceptación y evidencia

- [x] Cuatro tipos de relacion con `kind` estable.
- [x] Multiplicidades estructuradas explicitas y validadas.
- [x] Referencias limitadas a clases existentes; autorrelaciones permitidas.
- [x] UUID globales y layout exclusivo de clases.
- [x] Round-trip JSON conserva los tipos polimorficos.
- [x] Todos los checks finales registrados.

## 20. Estado final

DONE. El usuario reviso y aprobo CU-03.

## 21. Commit y push

```powershell
git status
git add backend/app/domain/uml backend/tests/domain docs
git commit -m "feat(cu-03): model UML relationships"
git push -u origin feat/cu-03-uml-relationships
```

No se ejecutaron commit ni push.

## 22. Evolucion posterior - UML Editor Completeness Incremento 1

El dominio soportado permanece limitado a `UmlAssociation`, `UmlAggregation`, `UmlComposition` y `UmlGeneralization`. `Dependency` y `Realization` no forman parte de este alcance.

Association, aggregation y composition permiten autorrelaciones de classifier. Generalization no permite `sourceId == targetId` ni ciclos directos o indirectos. Estas dos invariantes se verifican en dominio al construir el resultado candidato de un comando, antes de que `UmlCommandBus` agregue un snapshot o que CU-07 lo persista.

La validacion diagnostica sigue separada de la admisibilidad de comandos: solo `GENERALIZATION_SELF_REFERENCE` y `GENERALIZATION_CYCLE` bloquean esta ruta. Las demas reglas semanticas no cambian de comportamiento. Cambiar el tipo de una relacion continua requiriendo eliminarla y crear una nueva.

## 23. Evolucion posterior - UML Editor Completeness Incremento 2

La proyeccion Vue Flow representa association, aggregation, composition y generalization con sus markers UML. Association, aggregation y composition muestran multiplicidades independientes junto a source y target; generalization no muestra multiplicidades. Las tres relaciones que permiten autorrelacion usan un edge custom visible y seleccionable cuando ambos extremos pertenecen a la misma clase.

El auto-layout ignora self-loops al construir el grafo de `d3-dag`, pero conserva las relaciones canónicas y las vuelve a renderizar. Dependency, Realization, roles/end names, navegabilidad y asociaciones n-arias permanecen fuera de alcance.

### Evidencia final del Incremento 2

Validacion automatica ejecutada el 2026-09-21:

- backend: `pytest` 167 passed, 2 warnings externos conocidos; `python -m compileall app`, `ruff check .` y `pip check`: OK;
- frontend: `npm run typecheck`: OK; `npm test`: 40 passed en 11 archivos; `npm run build`: OK;
- integracion PostgreSQL: `python -m alembic check`: `No new upgrade operations detected.`;
- gate global: `scripts/check.ps1`: OK;
- integridad de diff: `git diff --check`: OK.

No se agrega migracion: la proyeccion visual y el routing de self-loops se derivan exclusivamente de `ProjectDocument` y `DiagramLayout` existentes.
