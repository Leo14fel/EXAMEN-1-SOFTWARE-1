# CU-02 - Clases y miembros UML

**Estado:** DONE

## 1. Objetivo

Representar clases UML y sus miembros dentro de `CanonicalUmlModel`, sin relaciones entre clases.

## 2. Actor(es)

Usuario de modelado. Puede construir y serializar en memoria una clase con atributos y operaciones.

## 3. Dependencias

CU-01 terminado.

## 4. Referencias a product.md

`/product.md`, secciones 3, 6, 7, 9 y 11.

## 5. Alcance

### Incluye

- `UmlClass`, `UmlAttribute`, `UmlOperation` y `UmlParameter`.
- Visibilidad UML estricta: `public`, `private`, `protected` y `package`.
- Nombres y tipos semanticos no vacios con trim de espacios externos.
- `returnType` de operacion; la ausencia de retorno se representa explicitamente como `null`/`None`.
- UUID globalmente unicos entre clases y todos sus miembros anidados.
- Serializacion JSON, aliases publicos y round-trip de clases, atributos, operaciones, parametros y layout.

### Fuera de alcance

Relaciones, multiplicidades, herencia, interfaces, enumeraciones, validacion UML de negocio, Command Bus, canvas, persistencia, API, autenticacion, colaboracion, XMI, generadores, IA y AWS.

## 6. Precondiciones

Python 3.13, Pydantic 2 y CU-01 instalados. Las pruebas no requieren PostgreSQL, Docker ni red.

## 7. Escenarios / flujo principal

1. Crear una clase con nombre, visibilidad, atributos y operaciones opcionales.
2. Validar miembros, tipos, IDs y layout de la clase.
3. Serializar el `ProjectDocument` con aliases camelCase.
4. Reconstruirlo desde JSON sin perder semantica ni layout.

## 8. Plan aprobado

Un incremento: evolucionar el contrato Pydantic, cubrirlo con pruebas de dominio y sincronizar documentacion. No se implementa CU-03.

## 9. Incrementos

### Incremento 1

**Objetivo:** entregar clases y miembros UML serializables y estructuralmente validados.

**Cambios realizados:** `CanonicalUmlModel.elements` evoluciono a `list[UmlClass]`; se agregaron miembros, visibilidad, IDs globales y pruebas especificas.

**Pruebas:** suites CU-01/CU-02, regresion backend, compileall, Ruff, pip check, regresion frontend y gate PowerShell.

**Resultado real:** checks verdes; pytest conserva dos warnings externos de FastAPI/Starlette/AnyIO.

## 10. Diseño y decisiones utilizadas

`UmlClass.kind`, `UmlAttribute.kind` y `UmlOperation.kind` son `Literal` estables. La clase conserva listas tipadas separadas para atributos y operaciones, evitando diccionarios genericos o `Any`. El discriminante `kind` queda listo para que CU-03 amplie los elementos top-level mediante una union discriminada real cuando exista otro tipo concreto.

`UmlVisibility` es un `StrEnum` con valores semanticos, no simbolos de UI. Los tipos son strings semanticos normalizados, sin mapeos a lenguajes ni base de datos. La ausencia de retorno se representa con `null`/`None`; los generadores futuros son responsables de mapearla al equivalente del lenguaje de destino.

La identidad se valida en `CanonicalUmlModel`, que recorre clases, atributos, operaciones y parametros para prohibir duplicados globales. `DiagramLayout` conserva exclusivamente geometria y solo admite UUIDs de clases existentes.

## 11. Implementación realizada

```text
UmlClass
├── id: UUID
├── kind: "class"
├── name: str
├── visibility: UmlVisibility
├── attributes: list[UmlAttribute]
└── operations: list[UmlOperation]

UmlAttribute: id, kind "attribute", name, visibility, type
UmlOperation: id, kind "operation", name, visibility, parameters, returnType
UmlParameter: id, name, type
```

Todos los modelos rechazan campos inesperados. Los campos semanticos de nombre y tipo aplican trim y rechazan vacios. Las clases se serializan completas desde `CanonicalUmlModel` y sobreviven el round-trip de `ProjectDocument`.

## 12. Archivos/componentes principales afectados

- `backend/app/domain/uml/models.py`
- `backend/app/domain/uml/__init__.py`
- `backend/tests/domain/test_project_document.py`
- `backend/tests/domain/test_uml_classes_members.py`
- Documentacion transversal y roadmap PUDS.

## 13. Pruebas automáticas

| Prueba/comando | Resultado | Evidencia/nota |
|---|---|---|
| `pytest tests/domain/test_project_document.py -v` | OK | 17 passed. |
| `pytest tests/domain/test_uml_classes_members.py -v` | OK | 24 passed. |
| `pytest` | OK | 43 passed, 2 warnings externos. |
| `python -m compileall app` | OK | Dominio compilado. |
| `ruff check .` | OK | All checks passed. |
| `pip check` | OK | No broken requirements found. |
| `npm run typecheck` | OK | Sin cambios frontend. |
| `npm test` | OK | 2 passed. |
| `npm run build` | OK | Build Vite correcto. |
| `scripts/check.ps1` | OK | Todos los checks terminaron correctamente. |

## 14. Pruebas manuales

No aplica: CU-02 implementa contrato de dominio sin UI ni infraestructura externa.

## 15. Errores encontrados e iteraciones de corrección

- Ruff detecto orden de imports y lineas largas en la nueva suite; se corrigieron sin cambiar comportamiento.

## 16. Benchmarks relacionados

No aplica: CU-02 no introduce LLM, VLM ni STT.

## 17. Documentación actualizada

Este documento, arquitectura, decisiones, estado, handoff, contexto y roadmap PUDS.

## 18. Deuda técnica y riesgos restantes

- Los warnings deprecados FastAPI/Starlette/AnyIO son externos y ya estan documentados desde CU-00.
- CU-02 no implementa relaciones ni validaciones de nombres globales; corresponden a CU-03/CU-04.
- Cuando existan relaciones top-level, `CanonicalUmlModel.elements` evolucionara a una union discriminada por `kind`. `DiagramLayout.nodes` debera seguir restringido a elementos UML visualizables como nodos y no aceptar relaciones como nodos por accidente.

## 19. Criterios de aceptación y evidencia

- [x] Clases, atributos, operaciones y parametros con UUID y contrato estricto.
- [x] Visibilidad y tipos semanticos validados.
- [x] IDs unicos globalmente en el modelo canonico.
- [x] Layout de clases separado y sin referencias huerfanas.
- [x] Round-trip JSON conserva miembros y geometria.
- [x] Tests sin infraestructura externa y checks aplicables verdes.

## 20. Estado final

DONE. El usuario reviso y aprobo CU-02.

## 21. Commit y push

```powershell
git status
git add backend/app/domain/uml backend/tests/domain docs
git commit -m "feat(cu-02): model UML classes and members"
git push -u origin feat/cu-02-uml-classes-members
```

No se ejecutaron commit ni push.
