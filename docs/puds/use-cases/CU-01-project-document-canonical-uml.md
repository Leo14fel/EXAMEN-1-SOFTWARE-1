# CU-01 - ProjectDocument y Canonical UML Model

**Estado:** DONE

## 1. Objetivo

Implementar el contrato de dominio que representa un proyecto UML, separando su semantica canonica del layout visual.

## 2. Actor(es)

Usuario de modelado. El valor observable actual es poder crear, validar, serializar y reconstruir un documento UML en memoria sin infraestructura.

## 3. Dependencias

CU-00 terminado.

## 4. Referencias a product.md

`/product.md`, secciones 3, 6, 7 y 11.

## 5. Alcance

### Incluye

- `ProjectDocument` con UUID, metadata JSON-safe, `ownerId`, revision, timestamps, `CanonicalUmlModel` y `DiagramLayout`.
- `UmlElementBase` minimo con UUID y `kind` no vacio.
- UUID unicos entre elementos UML.
- Layout de nodos por UUID, con coordenadas libres y dimensiones positivas.
- Validacion de layouts huerfanos, campos inesperados y timestamps.
- Serializacion Pydantic 2 con aliases camelCase y round-trip JSON.

### Fuera de alcance

Clases, atributos, operaciones, relaciones, validacion UML de negocio, Command Bus, canvas, persistencia, SQLAlchemy, REST, autenticacion, colaboracion, XMI, generadores, IA y AWS.

## 6. Precondiciones

Python 3.13, Pydantic 2 y dependencias de CU-00 instaladas. No requiere PostgreSQL, Docker ni red.

## 7. Escenarios / flujo principal

1. Crear `ProjectDocument` con `ownerId` y timestamps UTC.
2. Incluir elementos semanticos en `umlModel` y, opcionalmente, nodos visuales en `diagramLayout`.
3. Validar que cada nodo refiere un elemento existente.
4. Serializar con aliases publicos y reconstruir desde JSON.

## 8. Plan aprobado

Un incremento: contrato Pydantic, validaciones deterministas, pruebas de dominio y documentacion. No se implementan CUs posteriores.

## 9. Incrementos

### Incremento 1

**Objetivo:** entregar el contrato de dominio serializable y validado.

**Cambios realizados:** se crearon `app.domain.uml` y pruebas de `ProjectDocument` sin dependencias de infraestructura.

**Pruebas:** especifica de dominio, suite backend, compileall, Ruff, pip check y regresion frontend.

**Resultado real:** checks automaticos verdes, con warnings externos preexistentes de FastAPI/Starlette en pytest.

## 10. Diseño y decisiones utilizadas

`CanonicalUmlModel` contiene la semantica y `DiagramLayout` solo el estado visual. `ProjectDocument` verifica la relacion entre ambos porque `DiagramLayout` aislado no conoce el modelo canonico.

`owner_id` es UUID estructural sin usuario, auth ni FK. `revision` inicia en 0 y solo reserva la semantica futura de concurrencia optimista. Los timestamps se generan en UTC, deben incluir timezone y cumplen `updatedAt >= createdAt`.

No se agrego version de esquema, persistencia ni contratos HTTP. Todos los modelos usan Pydantic 2 con `extra="forbid"` y aliases publicos.

## 11. Implementación realizada

```text
ProjectDocument
├── id: UUID
├── metadata: dict[str, JsonValue]
├── ownerId: UUID
├── revision: int >= 0
├── createdAt / updatedAt: datetime timezone-aware
├── umlModel: CanonicalUmlModel
└── diagramLayout: DiagramLayout
```

- `CanonicalUmlModel.elements` inicia vacio y exige UUID unicos.
- `UmlElementBase` contiene solamente `id` y `kind`; normaliza espacios externos y rechaza valores vacios.
- `DiagramLayout.nodes` es `dict[UUID, DiagramNodeLayout]`.
- `DiagramNodeLayout` contiene `x`, `y`, `width > 0` y `height > 0`.
- El documento rechaza nodos cuyo UUID no exista en `umlModel.elements`.

## 12. Archivos/componentes principales afectados

- `backend/app/domain/__init__.py`
- `backend/app/domain/uml/__init__.py`
- `backend/app/domain/uml/models.py`
- `backend/tests/domain/test_project_document.py`
- `docs/ARCHITECTURE.md`, `docs/DECISIONS.md`, `docs/STATUS.md`, `docs/HANDOFF.md`, `docs/PROJECT-CONTEXT.md` y roadmap PUDS.

## 13. Pruebas automáticas

| Prueba/comando | Resultado | Evidencia/nota |
|---|---|---|
| `pytest tests/domain/test_project_document.py -v` | OK | 17 passed. |
| `pytest` | OK | 19 passed, 2 warnings externos. |
| `python -m compileall app` | OK | Dominio compilado. |
| `ruff check .` | OK | All checks passed. |
| `pip check` | OK | No broken requirements found. |
| `npm run typecheck` | OK | Sin cambios frontend. |
| `npm test` | OK | 2 passed. |
| `npm run build` | OK | Build Vite correcto. |
| `scripts/check.ps1` | OK | Todos los checks terminaron correctamente. |

## 14. Pruebas manuales

No aplica: CU-01 implementa un contrato de dominio sin UI ni infraestructura externa.

## 15. Errores encontrados e iteraciones de corrección

- Un caso de test pasaba dos veces `width` o `height`, provocando `TypeError` antes de Pydantic; se corrigio el fixture para ejercer la validacion de dimensiones.
- Ruff solicito `datetime.UTC` y orden de imports; se aplicaron sin modificar el comportamiento.

## 16. Benchmarks relacionados

No aplica: CU-01 no introduce LLM, VLM ni STT.

## 17. Documentación actualizada

Este documento, arquitectura, decisiones, estado, handoff, contexto y roadmap PUDS.

## 18. Deuda técnica y riesgos restantes

- Los warnings deprecados de FastAPI/Starlette/AnyIO provienen de dependencias externas y ya estan registrados desde CU-00.
- CU-01 no implementa clases UML concretas; ese alcance corresponde a CU-02.
- `CanonicalUmlModel.elements` utiliza `UmlElementBase` durante CU-01 porque todavia no existen tipos UML concretos. En CU-02, cuando se introduzcan clases y otros elementos concretos, la coleccion debera evolucionar a un contrato polimorfico explicito, preferentemente una union discriminada por `kind`, preservando validacion y round-trip JSON de los campos especificos.

## 19. Criterios de aceptación y evidencia

- [x] Documento con identidad, metadata, owner estructural, revision, timestamps, modelo y layout.
- [x] Semantica UML y layout visual separados.
- [x] UUIDs de elementos unicos y layouts sin referencias huerfanas.
- [x] Contrato publico camelCase, estricto y serializable por round-trip.
- [x] Pruebas sin PostgreSQL, Docker ni red.
- [x] Checks automaticos aplicables verdes.

## 20. Estado final

DONE. El usuario reviso y aprobo CU-01.

## 21. Commit y push

```powershell
git status
git add backend/app/domain backend/tests/domain docs
git commit -m "feat(cu-01): add project document domain"
git push -u origin feat/cu-01-project-document
```

No se ejecutaron commit ni push.
