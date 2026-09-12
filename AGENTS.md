# AGENTS.md

## Propósito
Reglas generalizables para cualquier agente que trabaje en el proyecto. Las decisiones del producto viven en `product.md`; las decisiones del CU activo viven en su documento.

## Orden de lectura obligatorio
1. `product.md` — fuente de verdad de producto y stack.
2. `docs/puds/use-cases/IMPLEMENTATION-ROADMAP.md` — orden y dependencias.
3. `docs/puds/use-cases/CU-XX-<nombre>.md` — CU activo, si existe.
4. `docs/PROJECT-CONTEXT.md` — flujo de trabajo y continuidad.
5. Documentación técnica específica relacionada.

Si hay contradicción, no inventar una solución ni ampliar alcance: reportarla.

## Implementación
- Trabajar un solo CU a la vez.
- Cada CU puede tener de 1 a 3 incrementos como máximo.
- No adelantar trabajo de CUs futuros.
- Mantener exactamente las tecnologías decididas en `product.md`.
- No sustituir librerías, frameworks o modelos por preferencias del agente.
- No fijar contratos/rutas/payloads antes de que el CU los necesite si `product.md` los dejó abiertos.
- Reutilizar la arquitectura existente antes de introducir capas/patrones/dependencias nuevas.
- El canvas nunca es fuente de verdad; proyecta el modelo canónico.
- Mantener semántica UML y `DiagramLayout` separados.
- La lógica generada debe derivarse del modelo/metadatos; no inventar lógica de negocio.

## Calidad
Cada incremento debe cerrar con:
1. pruebas específicas;
2. regresión relevante;
3. lint/typecheck/análisis estático aplicable;
4. build/compilación del componente afectado;
5. prueba manual documentada cuando sea necesaria.

No avanzar con verificaciones obligatorias en rojo salvo deuda explícitamente aprobada y documentada.

## Documentación
En cada iteración:
- actualizar el documento del CU activo;
- registrar lo realmente implementado;
- registrar pruebas y evidencia;
- registrar problemas/correcciones y deuda;
- actualizar documentación transversal solo si realmente cambió.

`product.md` es estable. Solo se modifica ante un requisito o decisión de producto aprobada; nunca para registrar progreso.

## Benchmarks
Si el CU introduce o modifica LLM, VLM o STT:
- ejecutar/actualizar el benchmark correspondiente;
- registrar hardware, versiones, modelo, parámetros, prompt, dataset, fecha y commit;
- comparar configuraciones sobre el mismo conjunto de casos;
- nunca escribir métricas estimadas como si fueran medidas;
- documentar edge cases manuales.

## Git
- Cambios pequeños y trazables.
- No mezclar CUs en un mismo commit.
- Una corrección posterior de un CU anterior usa un commit nuevo que mencione ese CU.
- No hacer commit/push automáticamente salvo petición explícita.
- Al cerrar cada CU entregar comandos exactos de `git add`, `git commit` y `git push`.
