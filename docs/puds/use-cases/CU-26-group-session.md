# CU-26 - Participar en una sesión grupal persistente

**Estado: IMPLEMENTED; aceptación Atlas/visual diferida como deuda autorizada.** Inicio 2026-11-07. Dependencias CU-25 y CU-10/11 implementados; comprobación Atlas/visual diferida por petición explícita del usuario. Un CU de código activo a la vez.

## Objetivo y plan autorizado

Compartir conversación, participantes conocidos y actividad atribuida, preservados al reconectar/reiniciar. Tres incrementos: (1) sesión y mensajes con permisos/idempotencia/historial; (2) actividad de comandos con registro duradero y difusión; (3) panel Vue y verificación integrada. Sin IA, voz, resúmenes automáticos, notificaciones push ni despliegue. Product 14, 20, 41; no se modifica product.md para progreso.

## Decisiones concretas del CU

Una sesión persistente por proyecto, independiente de la presencia efímera. Colección Mongo sessions, eventos ordenados embebidos con secuencia/version CAS y UUID idempotente; tamaño BSON máximo 16 MiB, rechazo explícito al llenarse. No se promete historial ilimitado ni se introduce particionado anticipado. Semántica/layout no se duplican en mensajes. EDITOR participa por texto; VIEWER consulta, conservando su restricción de lectura. Identidad/hora/rol fijados por servidor, sin conversaciones privadas.

Actividad de operaciones nuevas solamente: no reconstruir autores históricos que no fueron registrados. Una actividad pendiente se almacena en la misma escritura atómica del proyecto y se promueve idempotentemente a sesión; recuperación puede completar la promoción tras un fallo. No se anuncia una operación aceptada que no haya quedado persistida. Se mantiene el documento canónico libre de campos privados.

## Incremento 1 - DONE

Sesión, participantes conocidos, mensajes autorizados, UUID idempotente, orden CAS/paginación y reserva duradera de mensajes en proyecto con permiso atómico. GET recupera reservas tras fallo. Cinco pruebas nuevas: identidad/duplicados, roles/inputs, concurrencia/orden, recuperación tras fallo y tamaño. Gate scripts/check.ps1 PASS: 253 backend/61 frontend, Ruff/compileall/pip check/typecheck/build. Primer gate detectó variable de test sin uso; eliminada y gate completo repetido PASS. 98 warnings medidos (96 MongoMock TTL y 2 previos) y chunk Vite existente.

## Incremento 2 - DONE

Actividad pendiente persistida en CAS del proyecto (autor, acción, revisión e ID de elemento cuando existe); promoción idempotente al ledger y recuperación tras fallo. Operaciones rechazadas no registran éxito. No se inventaron autores anteriores. Mensajes usan reserva atómica separada, con permiso EDITOR comprobado en esa misma escritura; revocación concurrente rechaza el envío. Reservas privadas excluidas de ProjectDocument.

Difusión WebSocket opt-in conversation=true: página inicial reciente e incrementos ordenados, participantes conocidos y reconexión; misma sesión grupal, sin canales privados. Recuperación de pendientes antes de historial. Gate completo PASS: 257 backend/61 frontend, estático/build; luego optimización de página con proyección $slice y test de 55 eventos: 10 pruebas específicas, Ruff/compileall PASS. El gate final del incremento 3 volverá a medir el total completo. Warnings externos existentes y MongoMock TTL, sin benchmark IA.


## Incremento 3 - IMPLEMENTED

Panel Vue de conversación y actividad grupal, autor/hora, texto escapado, revisión de operaciones y selección de elemento si aún existe. Historial paginado de cincuenta eventos, carga de anteriores y difusión incremental. Pinia mezcla por ID/secuencia, rechaza páginas de otro proyecto y respuestas HTTP atrasadas. Sesión conocida y presencia viva se distinguen. VIEWER consulta; EDITOR envía con conexión sincronizada. Borrador e ID se conservan tras un fallo para reintentar sin duplicados; no se interpreta HTML del chat.

IDs de actividad usan prefijo reservado activity:proyecto:revision, diferente de UUID de mensajes: un cliente no puede ocupar el ID de una actividad futura. Actividad solo de operaciones registradas desde este CU; no se atribuyeron cambios históricos sin evidencia. Se conserva RP-02: no hay IA ni ejecución de cambios por texto.

Gate completo previo a separación de IDs: 258 backend/68 frontend, Ruff/compileall/pip check/typecheck/build PASS. Una prueba del panel necesitaba esperar el DOM al terminar el envío; se corrigió la espera y se repitió todo el gate. Ver evidencia final actualizada abajo. No se cambiaron dependencias ni modelos IA.

Smoke real por HTTP+WebSocket TCP loopback PASS: dos clientes reciben mensaje/actividad con autor y secuencia; reinicio completo del servidor Uvicorn, caché de bus vaciada y nuevo adaptador sobre la misma base MongoMock recuperan historial/proyecto. Reintento idempotente y entrada tardía PASS, mensajes no cambian UML/revisión. Resultado artifacts/cu26/wire-result.json, 2026-11-07 12:55:50 Bolivia. No es Atlas ni reinicio del proceso MongoDB; MongoMock se mantuvo entre servidores como almacenamiento de prueba. Servidores y datos temporales retirados al cerrar el script.

## Contratos y coherencia

POST /projects/{id}/session une participante y devuelve página reciente. GET /projects/{id}/session?before=N devuelve anteriores. POST /projects/{id}/session/messages recibe únicamente UUID id y text de 1 a 4000 caracteres no vacíos. Identidad y fecha vienen del servidor. IDs reutilizados con otro autor/contenido dan 409; registro ocupado después de ocho CAS da 409 reintentable; tamaño excesivo da 413; errores de almacenamiento se redactan. SessionPage contiene projectId, events, participantes conocidos, cursor/version y hasEarlier/hasMore.

WebSocket autentica y autoriza antes de negociar conversation=true; envía tipo conversation separado de patch/presence. Cada página tiene hasta cincuenta eventos, nunca otra copia de UML. Secuencia es orden de incorporación al ledger: promoción de un pendiente después de un fallo puede ocurrir más tarde que su createdAt. No se promete orden total de ejecución entre workers ni historial ilimitado.

Reservas _pendingMessage y _pendingActivity son privadas del documento Mongo. La primera exige permiso EDITOR atómico sin incrementar revisión UML. La segunda se guarda en el CAS autoritativo de cada comando/Undo/Redo. Promoción idempotente y eliminación condicionada por ID evitan pérdida ante caída entre ambos pasos; la lectura puede recuperar el pendiente. No se acepta una nueva operación con reserva de actividad anterior sin recuperar. Si el ledger se llena/falla, conservar reserva y datos: no se inventa éxito de historial ni se descarta actividad. Fragmentación/archivo y una política de retención aún no implementados. SQL legacy conserva sus contratos anteriores pero no ofrece sesión grupal; modo normal es Mongo.

## Verificaciones y deuda

Diez pruebas backend nuevas de sesión cubren permisos, validación, UUID idempotente/conflictivo, orden concurrente, páginas de 55 eventos, fallos/reintentos/reservas, tamaño, actividad/Undo/Redo, difusión, entrada tardía y revocación concurrente. Siete pruebas frontend nuevas cubren mezcla/aislamiento, borrador/idempotencia, VIEWER, escape, anteriores, respuesta atrasada y negociación del stream. Los tests usan MongoMock; no confundir con cloud. No se ejecutó benchmark LLM/VLM/STT.

Aceptación visual/Atlas diferida por petición explícita del usuario de avanzar sin configuraciones. Procedimiento pendiente: dos ventanas/cuentas, enviar y ver mensajes/actividad, cargar anteriores, desconectar/reconectar, reiniciar backend real con Atlas, revocar y confirmar aislamiento. No se declara DONE ni despliegue cloud probado. Datos migrados de CU-25 y sus respaldos no se tocaron. Control visual continúa no disponible según CU-10.

Sin commit/push. Cambios compartidos entre CUs requieren hunks revisados y commits separados; no git add . ni comandos amplios históricos de CU-25. Siguiente CU-18: integración de IA cloud y benchmark real; no hay GEMINI_API_KEY, GOOGLE_API_KEY u OPENAI_API_KEY configuradas en backend/.env al comprobar únicamente su presencia (sin mostrar valores). No se creó cuenta/clave ni se ejecutó una llamada facturable.



## Gate final de esta revisión

scripts/check.ps1 PASS: **258 backend, 68 frontend en 16 archivos**, Ruff/compileall/pip check/typecheck/build PASS. Backend: 94 warnings en esta ejecución (92 de datetime.utcnow interno de MongoMock/TTL y 2 externos previos); chunk Vite >500 kB existente. Validación de 12 Markdown/enlaces/UTF-8 y git diff --check PASS. Secretos/artefactos siguen ignorados por Git. No se hizo commit/push ni se cambió la configuración normal. Criterios automatizados y smoke locales aprobados; aceptación visual/cloud sigue diferida como deuda explícita.

Smoke TCP final repetido sobre esta revisión: PASS el 2026-11-07 a las 13:00:32 Bolivia, resultado actual en artifacts/cu26/wire-result.json.
