# Índice de documentación

Esta carpeta separa la **visión estable del producto** del estado real de implementación.

| Documento | Propósito |
|---|---|
| [`../product.md`](../product.md) | Fuente de verdad estable del producto. No usar como diario de avance. |
| `requirements/EXAM-CONSTRAINTS.md` | Restricciones explícitas del examen que deben preservarse. |
| `ARCHITECTURE.md` | Arquitectura inicial y límites entre frontend, backend y salidas generadas. |
| `STACK.md` | Versiones base seleccionadas y criterio de actualización. |
| `WORKFLOW.md` | Forma de trabajo incremental con OpenCode/OpenSpec. |
| `TESTING.md` | Estrategia mínima de pruebas y gates antes de avanzar. |
| `CYCLES.md` | Plantilla para los 4 ciclos. Se completa al derivar casos de uso. |
| `puds/use-cases/IMPLEMENTATION-ROADMAP.md` | Orden, dependencias y alcance de los CUs. |
| `puds/use-cases/CU-00-project-foundation.md` | Estado y evidencia real de la fundacion. |
| `puds/use-cases/CU-TEMPLATE.md` | Plantilla para documentar los CUs siguientes. |
| `STATUS.md` | Estado real del repositorio. |
| `HANDOFF.md` | Último punto estable y siguiente paso. |
| `DECISIONS.md` | Registro corto de decisiones arquitectónicas relevantes. |
| `deployment/AWS.md` | Alcance del despliegue AWS para cuando corresponda implementarlo. |

## Regla principal

[`/product.md`](../product.md) define **qué debe ser el producto**. `STATUS.md` define **qué existe realmente hoy**.
