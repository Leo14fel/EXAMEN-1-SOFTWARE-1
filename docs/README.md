# Índice de documentación

Esta carpeta separa la **visión estable del producto** del estado real de implementación.

| Documento | Propósito |
|---|---|
| [`../product.md`](../product.md) | Fuente de verdad estable del producto. No usar como diario de avance. |
| [`requirements/SECOND-PARTIAL.md`](requirements/SECOND-PARTIAL.md) | Fuente recibida del docente, matriz de requisitos, aceptación y dudas pendientes. |
| [`puds/use-cases/CU-26-group-session.md`](puds/use-cases/CU-26-group-session.md) | Conversación/actividad persistente implementadas; evidencia local y deuda Atlas/visual. |
| [`puds/use-cases/CU-11-collaborative-presence.md`](puds/use-cases/CU-11-collaborative-presence.md) | Presencia implementada, gates locales aprobados; aceptación visual/cloud diferida. |
| [`puds/use-cases/CU-10-realtime-collaboration.md`](puds/use-cases/CU-10-realtime-collaboration.md) | Realtime implementado, aceptación Atlas/visual diferida. |
| [`puds/use-cases/CU-25-cloud-nosql-persistence.md`](puds/use-cases/CU-25-cloud-nosql-persistence.md) | CU-25 DONE: Atlas, adaptación API, migración y recuperación verificadas. |
| `requirements/EXAM-CONSTRAINTS.md` | Restricciones explícitas del examen que deben preservarse. |
| `ARCHITECTURE.md` | Arquitectura actual/objetivo y límites entre frontend, backend y salidas generadas. |
| `STACK.md` | Versiones base seleccionadas y criterio de actualización. |
| `WORKFLOW.md` | Forma de trabajo incremental con OpenCode/OpenSpec. |
| `TESTING.md` | Estrategia mínima de pruebas y gates antes de avanzar. |
| `puds/use-cases/IMPLEMENTATION-ROADMAP.md` | Fuente única del orden, dependencias y alcance de los CUs. |
| `puds/use-cases/CU-00-project-foundation.md` | Estado y evidencia real de la fundacion. |
| `puds/use-cases/CU-TEMPLATE.md` | Plantilla para documentar los CUs siguientes. |
| `STATUS.md` | Estado real del repositorio. |
| `HANDOFF.md` | Último punto estable y siguiente paso. |
| `DECISIONS.md` | Registro corto de decisiones arquitectónicas relevantes. |
| [`deployment/NOSQL-CU25.md`](deployment/NOSQL-CU25.md) | Operación MongoDB, respaldos, migración ejecutada y recuperación. |
| `deployment/AWS.md` | Alcance aprobado del despliegue AWS, a implementar en CU-23. |

## Regla principal

[Relevo para dos personas y entrega del martes 10](delivery/RELEVO-EQUIPO.md): estado del corte, responsables propuestos, dependencias, evidencias y riesgos de plazo.

Prioridad vigente del segundo parcial: [CU-18 activo](puds/use-cases/CU-18-natural-language.md). [Guía para la clave Gemini](deployment/GEMINI-CU18.md). CU-14 queda pendiente de reanudación; no hay IA operativa todavía.

[CU-14 pendiente de reanudación](puds/use-cases/CU-14-spring-backend-generation.md): primera base Spring Boot generada y compilada; faltan capacidades de ejecución y descarga.

Material para la entrega académica: [informe base](delivery/INFORME-BASE.md), [registro de evidencias](delivery/EVIDENCIAS.md) y [guía de revisión manual](MANUAL-REVIEW.md). Separan implementación, pruebas registradas y pendientes; no constituyen aceptación final.

[`/product.md`](../product.md) define **qué debe ser el producto**. `STATUS.md` define **qué existe realmente hoy**.

- [Auditoría de pendientes antiguos](requirements/LEGACY-GAPS.md): evidencia y cobertura, sin sustituir el roadmap.

- CU-09 reanudado: invitaciones de un uso con correo/vencimiento/cancelación e interfaz; gate local aprobado, QA visual/cloud pendiente.

- [CU-13](puds/use-cases/CU-13-relational-mapping.md): modelo relacional/vista previa, perfil y límites de constraints; gate local aprobado.
