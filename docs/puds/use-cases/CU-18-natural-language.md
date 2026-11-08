# CU-18 — Interpretar solicitudes UML con IA cloud

**Estado: IN PROGRESS.** Estado vigente: integración grupal y formulario preparados y verificados con proveedor controlado; llamada/benchmark reales y aceptación visual/Atlas pendientes por clave diferida. Caso activo desde 2026-11-07 por repriorización explícita del usuario hacia el segundo parcial. CU-14 queda pendiente de reanudación en su incremento 3, sin borrar código ni evidencia.

## Objetivo y dependencias

Lenguaje natural → intención cerrada → resolución determinista → comandos UML validados. Depende de CU-04/05/26 implementados, con deuda visual/Atlas previamente diferida. Product secciones 13/14/32/41. La IA no modifica el canvas ni el documento directamente.

## Plan autorizado: tres incrementos como máximo

1. Contratos cerrados, contexto compartido acotado, resolver y adaptador Gemini REST; dataset y runner de benchmark reproducible. Pruebas negativas y regresión. No exponer todavía una ruta que prometa IA operativa.
2. Solicitudes autorizadas por proyecto/revisión, persistencia grupal y reintentos, errores/concurrencia y evaluación real con proveedor. No conversaciones privadas.
3. Interfaz de evaluación grupal y evidencia de contexto compartido. Benchmark comparativo real, manejo de fallos y cierre documentado.

**Autorización posterior:** el usuario pidió continuar con lo posible mientras configura la clave después. Se implementan las partes verificables de los incrementos 2/3 y se mantiene diferido el ensayo real, sin cerrar CU-18 ni iniciar CU-19.

RP-02 sigue abierto: una evaluación por texto puede producir una propuesta, pero no se aplica una mutación textual. CU-19 integra voz con ejecución autorizada después. Consultas/revisión/resumen de IA pertenecen a CU-27, no se adelantan aquí. El componente puro solo ensaya comandos sobre una copia para validar la propuesta.

## Proveedor y requisitos pendientes

Se prepara Gemini Developer API como integración cloud, sin SDK adicional, usando REST estándar de Python. Modelo candidato gemini-3.5-flash-lite, compatible con la documentación oficial consultada el 2026-11-07; aún no medido ni seleccionado por comparación de calidad. No se contratan servicios ni se habilita facturación. La clave permanece exclusivamente en configuración backend privada.

El usuario confirmó que no tiene una clave. No hay llamadas reales ni resultados de calidad/latencia del LLM; faltan la clave y la evaluación antes del cierre. Probar el contrato con respuestas controladas no acredita inferencia. Qwen3 local sigue opcional, no se instala para eludir esta dependencia.

Fuentes primarias: [generación REST](https://ai.google.dev/api/generate-content), [modelo candidato](https://ai.google.dev/gemini-api/docs/models/gemini-3.5-flash-lite), [salida estructurada](https://ai.google.dev/gemini-api/docs/structured-output). No se presupone gratuidad o cuota disponible; se comprobará en la cuenta al configurar el acceso.

## Incremento 1 — Implementado; inferencia/benchmark real pendientes

Contratos cerrados Pydantic para crear/renombrar/eliminar clase, agregar atributo/método sin parámetros, asociación simple con multiplicidades explícitas y clarify/unsupported. Atributos restringidos a tipos declarados; campos extra, código/URLs/SQL y multiplicidades booleanas rechazados. Referencias por nombre deben resolver de forma única, sin adivinar. El servidor construye los comandos existentes y ejecuta solo una copia del documento para validar. Se revalida el modelo de respuesta antes de construir comandos; nunca se persiste desde este componente.

Contexto: solo UML, proyecto/revisión, solicitante y hasta veinte eventos grupales atribuidos; excluye layout, metadata, memberships y campos privados. Máximo 64 000 bytes: falla explícitamente en lugar de omitir el diagrama. El llamador autorizado deberá recuperar los eventos del mismo proyecto en el incremento 2; esta función pura no sustituye autorización.

Adaptador Gemini REST con host fijo, clave en header, TLS estándar, timeout veinte segundos, respuesta máxima 32 000 bytes, salida JSON Schema y 1200 tokens máximos. No sigue redirects, no configura herramientas ni ejecuta resultados; sin reintentos automáticos. Rechaza JSON inválido/duplicado, schema inválido, respuestas múltiples/truncadas y tool calls; errores públicos sin headers, claves o cuerpo remoto. Modelo candidato, no medido ni validado en cuenta real. Configurador getpass y guía: [GEMINI-CU18](../../deployment/GEMINI-CU18.md).

42 pruebas específicas (intentos/resolver/contexto, transporte controlado, guardado de clave y cálculo de métricas). Las respuestas controladas solo prueban el contrato y no se presentan como inteligencia o precisión real. El cálculo diferencia schema válido de propuesta resoluble y divide los falsos positivos entre los casos negativos; A/B usa el mismo dataset congelado.

Dataset de doce casos, comparación prevista temperatura 0/0.2. Se ejecutó únicamente fixtures-only: NOT_RUN, cero solicitudes, métricas LLM null. Se registra commit/dirty, hashes de implementación/dataset, prompt, versiones y hardware cliente; hardware remoto/picos RAM/VRAM no medidos. La primera consulta CIM tuvo acceso insuficiente; la lectura autorizada posterior registró hardware real. Recibo más reciente en artifacts/cu18; no se envió contenido de proyectos reales a proveedores. LLM.md tenía un baseline local histórico; se actualizó para alinearlo con el producto cloud aprobado, sin modificar product.md.

El usuario confirmó que no tiene clave. No se cierra el CU ni se inicia CU-19 antes de resolver su dependencia y la evaluación real. Pendientes del mismo CU: autorización por proyecto/revisión, persistencia grupal/idempotencia, interfaz y benchmark real; no se añade botón ni endpoint de IA aún. CU-14 queda pendiente de reanudación, no es un segundo CU activo. Sin cambios a datos reales, al servidor QA o a product.md; sin commit/push.

### Gate final del incremento 1

2026-11-07: scripts/check.ps1 PASS, **384 backend / 86 frontend en 20 archivos**, Ruff/compileall/pip check/typecheck/build PASS. 90 warnings externos (88 MongoMock TTL y 2 previos) y aviso Vite existente. Las 42 pruebas específicas son funcionales/controladas, no un benchmark LLM. El runner fixtures-only quedó NOT_RUN con doce casos, cero llamadas y métricas null; hardware cliente y hashes verificados. Inferencia y benchmark siguen pendientes de clave, por lo que se conserva IN PROGRESS y no se declara aceptación ni se salta a CU-19.

## Incremento 2 — Integración grupal implementada; proveedor real pendiente

Tres rutas autorizadas por proyecto: GET /projects/{id}/ai/status, POST /projects/{id}/ai/requests y GET /projects/{id}/ai/requests/{requestId}. Un editor/propietario solicita evaluación con UUID, baseRevision y texto de hasta 2000 caracteres. VIEWER solo consulta. Se comprueban permisos y revisión antes de reservar/enviar; tras la llamada se revalidan JWT, existencia del usuario, permisos y revisión. Un resultado obsoleto se registra como stale sin intención vigente; acceso revocado/expirado no devuelve la respuesta al solicitante. No hay canal privado ni ruta para aplicar propuestas textuales.

Contexto obtenido únicamente del documento y ledger del proyecto autorizado. GEMINI_API_KEY se lee como SecretStr backend; status devuelve disponibilidad de configuración y modo proposalOnly, no secretos ni una garantía de conexión. Sin clave, POST responde AI_NOT_CONFIGURED/503 y no llama al proveedor. No hay modo de IA simulada activable por el usuario: las respuestas controladas pertenecen exclusivamente a tests.

Persistencia reutiliza projects/sessions, sin colección adicional. Una reserva privada _aiRequest por proyecto y lease de treinta segundos permite registrar eventos aiRequest/aiResult con identidad del servidor, solicitud/revisión y estado. IDs ai:request:UUID / ai:result:UUID no colisionan con UUIDs de mensajes o activity. _aiSeen conserva un marcador atómico permanente por ID para impedir una segunda inferencia incluso si otra petición termina entre lectura y reserva. Ambos campos privados se excluyen de ProjectDocument/XMI y cuentan para el límite BSON de 16 MiB. No se promete historial ilimitado.

La recuperación normal del grupo promueve los eventos reservados de forma idempotente; tras interrupción/lease vencida registra AI_REQUEST_INTERRUPTED y no repite una llamada de estado incierto. Se devuelve 202 mientras sigue pendiente; reusar el ID con otro actor/texto/revisión da 409. Una única solicitud simultánea por proyecto; errores/cuota y propuestas rechazadas también quedan compartidos, sin exponer cuerpo remoto ni SQL. El primer resultado no puede reemplazarse por otro intent con el mismo ID. No es una promesa de exactly-once del proveedor: un fallo de red puede dejar incierto si consumió cuota; por eso no se reintenta automáticamente.

Los eventos se difunden mediante el WebSocket de conversación existente; la evaluación no altera UML, layout, revisión o Undo/Redo. Las pruebas incluyen permisos, contexto aislado, JWT/permisos/revisión cambiados en vuelo, concurrencia/reintentos, lease interrumpida, fallo de promoción posterior al guardado, guardia BSON, metadatos inmutables, dos WebSockets (editor/observador) y reconexión. Son pruebas con MongoMock/proveedor controlado; falta Atlas/proveedor reales.

Gate intermedio 398 backend/87 frontend, estático/build PASS, antes de la prueba adicional de marcador duradero y las verificaciones finales. La regresión relevante posterior de solicitudes/conversación/realtime/almacenamiento/QA pasó 41 casos. La primera regresión detectó que el harness QA no incluía las nuevas rutas: se corrigió para reutilizar el router real. Ruff detectó imports y cierres de variables de test, corregidos. La carrera de finalización entre lectura/reserva se corrigió con _aiSeen y prueba específica.

## Incremento 3 — Interfaz preparada; aceptación y benchmark pendientes

AiRequestPanel en el workspace junto a la conversación grupal. Consulta disponibilidad; sin clave muestra configuración pendiente y deshabilita envío. No presenta fixture alguno como respuesta de IA. Envía ID y revisión actual, integra eventos en el mismo historial que ven todos, muestra una descripción concreta de la propuesta y no ofrece aplicar. VIEWER consulta historial sin evaluar. Si el diagrama cambia después de la evaluación, se avisa que requiere nueva revisión.

Una respuesta de red incierta conserva el ID y bloquea otro envío; «Consultar resultado» usa GET y no vuelve a llamar a IA. Un 404 confirmado de solicitud no registrada permite reenviar explícitamente manteniendo el texto. Al desmontar/cambiar de proyecto descarta respuestas tardías y no contamina otra sesión. El historial y resultados se muestran escapados como texto. La primera prueba de UI detectó structuredClone de un array reactivo de participantes; se corrigió pasando objetos planos, conservando su información actual.

El servidor QA anterior no se reinició para preservar sus datos temporales; su proceso existente necesita actualizarse para servir estas rutas. Ese reinicio recrea los fixtures. No se declara inspección visual humana ni despliegue del código nuevo. La guía de clave explica reinicio/configuración y aceptación posterior.

Gate final scripts/check.ps1 **PASS: 402 backend / 96 frontend en 22 archivos**, Ruff/compileall/pip check/typecheck/build PASS; 94 warnings backend (92 MongoMock TTL y 2 externos previos), aviso Vite existente. Tras completar la atribución de eventos AI en el contexto (requestId/requestedBy/baseRevision/status/canApply), se repitieron 60 pruebas específicas, Ruff y compileall PASS; dataset fixtures-only NOT_RUN otra vez, sin inferencia. Smoke TCP HTTP/WebSocket PASS 2026-11-07 16:59:01 Bolivia con factory QA nueva aislada: configuración ausente, 401 anónimo, 503 sin clave, 403 observador, snapshot/conversación y documento intacto. Servidor/datos del smoke retirados; recibo ignorado artifacts/cu18/http-readiness.json. El servidor QA previo del usuario no se reinició. Benchmark LLM y llamada cloud siguen NOT_RUN por clave diferida; no se cambia prompt/modelo para aparentar una medición. No se inicia voz, IA asesora/resúmenes ni móvil en paralelo. Sin cambios de producto ni commit/push.

### Vista para revisión sin clave — 2026-11-07

Se verificó que la clave sigue ausente y se creó una segunda instancia QA independiente: frontend localhost:5176, API localhost:8002, fixtures/secret JWT propios y clave de proveedor vacía por entorno del proceso. No se reinició ni reemplazó la instancia 5175/8001. Config temporal ignorada frontend/.vite/qa-cu18.config.ts; recibo/procesos y script de detención propios en artifacts/cu18. Login/CORS/routing frontend/status sin clave PASS 19:30:52 Bolivia, artifacts/cu18/preview-readiness.json. La vista solo permite revisar preparación sin inferencia. El control visual falló al iniciar por kernel assets/os error 3; no se declara screenshot ni aceptación visual. No se repitieron gates de código porque no se modificó implementación; se verificó protocolo real y sintaxis del script local de detención, sin detener la vista antes de la revisión del usuario.

### Corte para relevo — 2026-11-07

Usuario probó la vista 5176 y expresó conformidad; se registra revisión humana favorable de esa demostración, sin inferir pruebas de IA real/cloud/voz ni todos los escenarios funcionales. El usuario pidió cerrar el avance para trabajar con otra persona, con entrega martes 10 por la tarde. El corte y reparto viven en delivery/RELEVO-EQUIPO.md: no cierran este CU ni crean un incremento adicional. No cambia código ni se repiten gates ya verdes por editar documentación. Prueba real/benchmark siguen pendientes de clave.
