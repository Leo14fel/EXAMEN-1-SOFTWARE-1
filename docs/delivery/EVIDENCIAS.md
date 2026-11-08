# Evidencias para la documentación académica

Fecha de corte: 7 de noviembre de 2026. Este registro no sustituye los tests ni los documentos de CU. No marcar un escenario aprobado por una impresión general de la interfaz.

## Evidencia registrada

| ID | Evidencia | Resultado y alcance | Fuente |
| --- | --- | --- | --- |
| EV-01 | Gate completo de preparación de QA local | 311 backend / 86 frontend, análisis estático y build PASS; ejecución histórica, no repetida en esta edición documental | [TESTING](../TESTING.md) |
| EV-02 | Migración y recuperación CU-25 | 3 usuarios / 15 proyectos / 2 permisos; origen conservado y reinicio real verificado | [CU-25](../puds/use-cases/CU-25-cloud-nosql-persistence.md) |
| EV-03 | HTTP/WebSocket de la prueba temporal | Login de tres roles, vista relacional y frames snapshot/presence/conversation PASS, con MongoMock | [Preparación de QA](../TESTING.md), recibo local ignorado artifacts/manual-qa/readiness.json |
| EV-04 | Comentario humano sobre la pantalla | El usuario indica «estoy viendo que si esta bien»; revisión inicial favorable, escenarios concretos no especificados | Chat del proyecto, 2026-11-07 |

Los archivos de artifacts contienen recibos locales y están excluidos de Git. Para una entrega reproducible, conservar los resultados relevantes en los documentos de CU y adjuntar únicamente evidencias saneadas, sin tokens, contraseñas o cadenas de conexión reales.

## Evidencia manual por completar

Estos IDs organizan comprobaciones de funciones existentes; no son nuevos casos de uso ni un segundo roadmap. Usar el [recorrido manual](../MANUAL-REVIEW.md).

| ID | Escenario | Evidencia que debe recogerse | Estado |
| --- | --- | --- | --- |
| EM-01 | Editar clase/atributo/método y deshacer/rehacer | Acción, resultado visible y comportamiento tras recargar | Pendiente |
| EM-02 | Dos usuarios en el mismo proyecto | Dos sesiones independientes; cambio visible en ambas sin recargar | Pendiente |
| EM-03 | Presencia y conversación compartidas | Participantes y mensaje con autor; recepción en otra sesión | Pendiente |
| EM-04 | Observador sin edición | Consulta correcta y edición restringida; contraste con prueba backend de permisos | Pendiente |
| EM-05 | Modelo relacional | Tablas/claves, aviso al quedar desactualizado y descarga de revisión actual | Pendiente |
| EM-06 | Exportación/importación XMI | Nuevo proyecto, contenido esperado, avisos y original conservado | Pendiente |
| EM-07 | Invitación dirigida, canje y cancelación | Cuenta destinataria, rol asignado y rechazo de token usado/cancelado; ocultar el código en capturas | Pendiente |
| EM-08 | Retomar sesión en infraestructura real | Documento, revisión y contexto recuperados tras reiniciar; no usar el servidor temporal para esta prueba | Pendiente cloud |
| EM-09 | Enterprise Architect | Archivo de origen, versión EA, importación/exportación y comparación del subconjunto soportado | Pendiente EA real |

## Formato para cada resultado manual

Registrar fecha/hora y zona, CU y escenario, versión o commit y modificaciones locales relevantes, entorno (temporal/Atlas), navegador, rol, precondiciones, pasos, resultado esperado, resultado observado, captura o archivo, incidencia y resultado del reintento si hubo corrección. No sustituir un resultado fallido por el reintento: conservar ambos.

Las capturas futuras deben tener títulos que expliquen la acción y el resultado. Aún no se han creado ni adjuntado capturas en este paquete documental. Los benchmarks de IA/STT/VLM se incorporarán solo después de mediciones reales en sus CUs.

## EV-05 — CU-14 incremento 1

2026-11-07: backend generado Java 21/Boot 4.1.2 compilado con Gradle 9.5.1, JAR construido y un test JUnit real de validación Jakarta PASS. Gate principal 336 backend/86 frontend, análisis estático/build PASS; 11 templates incluidos en wheel. [Detalle y reproducción](../puds/use-cases/CU-14-spring-backend-generation.md). Acredita la base de persistencia escalar, no CRUD, relaciones, SQL ejecutado ni descarga desde el editor. No sustituye EV-01; es una ejecución posterior.

## EV-06 — CU-14 incremento 2

2026-11-07 16:01:50 Bolivia: 51 comprobaciones HTTP sobre backend Spring Boot generado con PostgreSQL 17.6 real PASS, incluyendo CRUD, consultas, restricciones, referencias 1:1/1:N/self, readOnly y reinicio JVM. Solo base temporal cu14_UUID, retirada al terminar; no Atlas ni contenido legacy. Corrección de ordenamiento registrada en [CU-14](../puds/use-cases/CU-14-spring-backend-generation.md). Gate final 342 backend/86 frontend, estático/build PASS y 17 templates empaquetados. No acredita descarga/UI, relaciones avanzadas ni artefactos CU-15.

## EV-07 — Preparación CU-18 y cambio de prioridad

2026-11-07: el usuario priorizó el segundo parcial. CU-14 pendiente de reanudación; CU-18 activo. Gate 384 backend/86 frontend y estático/build PASS; 42 pruebas controladas, sin proveedor real. Dataset doce casos y runner preparados: fixtures-only NOT_RUN con cero llamadas, métricas LLM null y hardware/commit/hashes registrados. No acredita IA, voz, contexto grupal con IA ni móvil/push funcionando. [CU-18](../puds/use-cases/CU-18-natural-language.md) y [configuración de clave](../deployment/GEMINI-CU18.md).

## EV-08 — CU-18 integración grupal y formulario

2026-11-07: gate 402 backend/96 frontend (22 archivos), estático/build PASS; 18 pruebas API y diez frontend adicionales. Verifica propuestas compartidas sin mutación, acceso/JWT/revisión, idempotencia/recuperación y dos WebSockets con observador. Tras añadir atribución al contexto, 60 pruebas específicas PASS. Smoke TCP sin clave PASS 16:59:01 Bolivia con storage aislado y cero llamadas al proveedor; proceso temporal retirado, instancia previa del usuario conservada. Benchmark de doce fixtures NOT_RUN, métricas LLM null: no acredita inteligencia, precisión, Gemini operativo ni aceptación visual/Atlas. [Detalle CU-18](../puds/use-cases/CU-18-natural-language.md).

## EV-09 — Revisión del usuario y corte para relevo

El usuario indicó «me parece bien, esta bien logrado ya lo probe» sobre la vista actualizada; impresión humana favorable sin detalle de escenarios. Luego pidió cierre del avance y organización con otra persona, entrega martes 10 de noviembre por la tarde. [Guía de relevo](RELEVO-EQUIPO.md). Esto no acredita Gemini real, benchmark, persistencia remota, voz o push; CU-18 continúa pendiente de validación. No se ejecutó regresión nueva por esta edición documental.
