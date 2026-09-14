# CU-04 - Validacion UML

**Estado:** READY_FOR_USER_VALIDATION

## 1. Objetivo

Detectar problemas semanticos de UML en un `CanonicalUmlModel` y devolver diagnosticos accionables, sin modificar el modelo ni depender de infraestructura.

## 2. Actor(es)

Usuario de modelado. Las futuras capas de guardado, importacion, colaboracion y generacion reutilizaran el mismo resultado de validacion.

## 3. Dependencias

CU-00, CU-01, CU-02 y CU-03 terminados.

## 4. Referencias a product.md

`/product.md`, secciones 3, 7, 9, 10 y 11.

## 5. Alcance

### Incluye

- Validador puro `validate_uml_model(model)` y resultado Pydantic serializable.
- Diagnosticos con codigo, severity, mensaje, `elementId` y campo opcional.
- Duplicados de clases, atributos, parametros, firmas de operaciones y generalizaciones.
- Generalizaciones a si misma y ciclos de herencia.
- Acumulacion determinista de multiples errores sin mutar el modelo.

### Fuera de alcance

- Tipos inexistentes o de lenguajes destino, visibilidad contextual, nombres reservados y paquetes.
- Herencia multiple, ciclos de composicion, ownership avanzado, asociaciones duplicadas y navegabilidad.
- Command Bus, Undo/Redo, canvas, API, persistencia, XMI, generacion e IA.

## 6. Diferencia entre validaciones

Pydantic en `models.py` protege estructura: UUID globales, `kind`, referencias de relaciones a clases, multiplicidades y layout. `validation.py` evalua reglas semanticas sobre modelos ya estructuralmente validos; no lanza excepciones por un error UML normal, no corrige automaticamente y devuelve todos los problemas detectados.

## 7. Arquitectura y contratos

```text
CanonicalUmlModel
       |
       v
validate_uml_model
       |
       v
UmlValidationResult(diagnostics, isValid)
```

`UmlDiagnosticSeverity` contiene `error` y `warning`. `UmlDiagnosticCode` centraliza los codigos. `UmlDiagnostic` usa aliases camelCase para `elementId`; `UmlValidationResult.isValid` es calculado: es verdadero cuando no hay diagnosticos `error`.

| Codigo | Regla | Severidad |
|---|---|---|
| `DUPLICATE_CLASS_NAME` | Nombre repetido de clase | error |
| `DUPLICATE_ATTRIBUTE_NAME` | Atributo repetido en una clase | error |
| `DUPLICATE_PARAMETER_NAME` | Parametro repetido en una operacion | error |
| `DUPLICATE_OPERATION_SIGNATURE` | Firma de operacion repetida | error |
| `GENERALIZATION_SELF_REFERENCE` | Clase heredando de si misma | error |
| `GENERALIZATION_CYCLE` | Ciclo de herencia | error |
| `DUPLICATE_GENERALIZATION` | Herencia duplicada | error |

## 8. Reglas implementadas

- Los nombres de clases, atributos y parametros se comparan de forma exacta y case-sensitive. `Cliente` y `cliente` son distintos. Cada ocurrencia posterior a la primera recibe un diagnostico, respetando el orden de elementos del modelo.
- Un atributo solo compite con atributos de su propia clase; un parametro solo con parametros de su propia operacion.
- Una firma de operacion es nombre mas secuencia ordenada de tipos de parametros. Los nombres de parametros y el tipo de retorno no forman parte de la firma, por lo que `buscar(id: UUID)` y `buscar(codigo: UUID)` son duplicadas.
- Una generalizacion duplicada comparte la pareja `(sourceId, targetId)`. La convencion permanece: source es hija y target es padre.
- Una generalizacion `A -> A` recibe `GENERALIZATION_SELF_REFERENCE`.

Para ciclos, un DFS determinista recorre las generalizaciones en el orden del modelo y marca nodos como no visitado, en curso o terminado. Una arista hacia un nodo en curso produce un `GENERALIZATION_CYCLE`; esta politica genera un diagnostico por arista de retorno y evita repetir el mismo ciclo por cada nodo.

## 9. Incrementos

### Incremento 1

**Objetivo:** entregar el motor semantico reusable con contratos, pruebas y documentacion.

**Cambios realizados:** se crearon contratos de diagnostico y resultado, el validador puro y la suite de reglas semanticas. No se modificaron los contratos UML existentes.

**Pruebas:** pruebas especificas del validador, regresiones CU-01 a CU-03, suite backend, compileall, Ruff, pip check, checks frontend y gate PowerShell.

**Resultado real:** todos los checks finales verdes; pytest conserva dos warnings externos de FastAPI/Starlette/AnyIO.

## 10. Archivos/componentes principales afectados

- `backend/app/domain/uml/validation.py`
- `backend/app/domain/uml/__init__.py`
- `backend/tests/domain/test_uml_validation.py`
- Documentacion de arquitectura, decisiones, estado, continuidad, testing y roadmap.

## 11. Pruebas automaticas

| Prueba/comando | Resultado | Evidencia/nota |
|---|---|---|
| `pytest tests/domain/test_uml_validation.py -v` | OK | 20 passed. |
| `pytest tests/domain/test_project_document.py -v` | OK | 17 passed. |
| `pytest tests/domain/test_uml_classes_members.py -v` | OK | 25 passed. |
| `pytest tests/domain/test_uml_relationships.py -v` | OK | 32 passed. |
| `pytest` | OK | 96 passed, 2 warnings externos. |
| `python -m compileall app` | OK | Dominio compilado. |
| `ruff check .` | OK | All checks passed. |
| `pip check` | OK | No broken requirements found. |
| `npm run typecheck` | OK | Sin cambios frontend. |
| `npm test` | OK | 2 passed. |
| `npm run build` | OK | Build Vite correcto. |
| `scripts/check.ps1` | OK | Todos los checks terminaron correctamente. |

## 12. Pruebas manuales

No aplica: CU-04 es dominio puro sin interfaz ni infraestructura externa.

## 13. Benchmarks relacionados

No aplica: CU-04 no introduce LLM, VLM ni STT.

## 14. Deuda tecnica y riesgos restantes

- Las reglas semanticas deliberadamente excluidas se evaluaran solo en su CU aprobado.
- Las futuras capas deben consumir diagnosticos por codigo y severity, no por comparar mensajes.

## 15. Criterios de aceptacion y evidencia

- [x] Capa semantica separada de Pydantic y sin efectos secundarios.
- [x] Diagnosticos, severidades y codigos estables serializables.
- [x] Duplicados, firmas y generalizaciones validadas de forma determinista.
- [x] Multiples errores acumulados y modelo sin mutacion.
- [x] Regresiones completas documentadas.

## 16. Estado final

READY_FOR_USER_VALIDATION. No se marca DONE hasta aprobacion del usuario.

## 17. Commit y push

```powershell
git status
git add backend/app/domain/uml backend/tests/domain docs
git commit -m "feat(cu-04): add UML semantic validation"
git push -u origin feat/cu-04-uml-validation
```

No se ejecutaron commit ni push.
