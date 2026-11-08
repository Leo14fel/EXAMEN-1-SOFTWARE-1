# CU-10 - Editar colaborativamente en tiempo real

**Estado: IMPLEMENTED, verificación Atlas y prueba visual humana pendientes.** Inicio y evidencia: 2026-11-07, America/La_Paz. Dos incrementos de código realizados. El usuario pidió avanzar localmente sin depender de Atlas y luego confirmó "si avanza todo lo posible"; se difiere explícitamente la aceptación Atlas/visual como deuda, sin declararla aprobada. Se permite continuar secuencialmente con CU-11.

## Objetivo, actores y dependencias

Editores y viewers autorizados reciben cambios persistidos del mismo ProjectDocument. Dependencias: CU-05, CU-07..09 y CU-25. Product secciones 4, 6, 11, 17 y 20. Los pendientes manuales anteriores de CU-08/09 siguen abiertos.

## Plan autorizado y alcance

El usuario pidió continuar tras CU-25 y autorizó avanzar dentro del plan. Dos incrementos: (1) transporte WebSocket autenticado, deltas, revisión, recuperación, permisos y pruebas backend; (2) cliente nativo, proyección Pinia, reconexión/estado visible y pruebas integradas. Sin presencia/cursores (CU-11), conversación/actividad (CU-26), IA ni despliegue. Sin nuevas dependencias ni cambios a product.md.

## Diseño y contratos utilizados

HTTP mantiene comandos/Undo/Redo y CAS existentes. WebSocket `/projects/{UUID}/sync` entrega snapshot al conectar/recuperar y deltas entre revisiones persistidas; no acepta mutaciones. Cliente envía primero `{"type":"authenticate","token":"<JWT>"}` dentro de cinco segundos: token nunca en URL. Origen permitido igual a FRONTEND_ORIGIN; clientes no navegador pueden omitir Origin, pero necesitan token. Cada lectura revalida JWT, existencia del usuario y permisos persistidos. Origen rechazado: 4403; JWT inválido/expirado: 4401; proyecto inexistente/no autorizado: 4404; protocolo inválido: 4400; error almacenamiento: 1013 redactado.

Snapshot: type, document, canUndo, canRedo, effectiveRole. Patch: type, projectId, baseRevision, revision, changes, canUndo, canRedo, effectiveRole. Changes son operaciones set/remove con path de segmentos string/int y value para set, sobre JSON canónico. Semántica UML y layout siguen separados; no se usa el canvas como autoridad.

Cada conexión consulta almacenamiento autoritativo cada 500 ms, fuera del event loop; la cadencia real incluye latencia del almacenamiento. Detecta escrituras externas al proceso sin bus exclusivamente local ni infraestructura nueva. Cambios intermedios pueden agruparse en un delta consistente: esto no es historial de actividad ni garantía de entregar cada revisión individual (CU-26). Escala de consultas proporcional a conexiones/documentos: optimización y benchmark de carga no realizados. No se afirma despliegue de gran escala ni prueba real entre workers independientes.

Solo se difunden documentos persistidos; rechazos CAS/fallos no publican contenido del bus no confirmado. Se conservan los locks y CAS existentes. El estado de Undo/Redo sigue efímero y local al proceso; conflicto puede invalidar su historial, como antes. Las actualizaciones de rol no necesitan incrementar revisión UML.

Cliente aplica cambios sobre baseRevision coincidente y publica el documento completo derivado solo tras aplicar todo el delta. Ignora revisiones viejas/duplicadas, recupera snapshot ante huecos, valida rutas y bloquea claves de prototipo. Una respuesta HTTP atrasada no hace retroceder revisión ni reemplaza otro proyecto abierto. Reconexión con backoff de 1 a 10 segundos; watchdog de snapshot/resync de 15 segundos; limpieza al cambiar proyecto/token, salir o desmontar. Revocación limpia la proyección; expiración cierra sesión. Editor bloquea mutaciones mientras reconecta y muestra estado. Los borradores existentes del inspector se mantienen según el comportamiento previo.

Referencia técnica consultada: [WebSockets de FastAPI](https://fastapi.tiangolo.com/advanced/websockets/). Se reutilizan FastAPI y WebSocket nativo del stack aprobado.

## Incremento 1 - DONE

Backend en app/api/realtime.py y router en main.py. Gate scripts/check.ps1 PASS: 241 backend (6 nuevos), 46 frontend, Ruff/compileall/pip check/typecheck/build. Correcciones de tests: un conflicto obsoleto invalida Undo como antes; el fallo debía inyectarse en project_store.update_if_revision; las clases requieren visibility explícita. No se modificó semántica UML para acomodar pruebas.

## Incremento 2 - IMPLEMENTED, aceptación operativa pendiente

editor-sync.ts, integración Pinia y EditorWorkspace; siete escenarios backend totales (incluida carrera de dos editores) y nueve pruebas nuevas frontend. Gate final scripts/check.ps1 PASS: **242 backend y 55 frontend en 14 archivos**; Ruff, compileall, pip check, typecheck y build PASS. Dos warnings externos de Starlette/httpx y AnyIO; warning existente de chunk Vite >500 kB. No se introdujeron LLM/VLM/STT: no aplica benchmark IA.

## Evidencia funcional

- Backend automatizado: dos clientes, revisión/delta, rechazo obsoleto, Undo/reconexión, carrera de dos editores con un ganador, aislamiento, origen, JWT, rol VIEWER, revocación, fallo de persistencia sin publicación y lectura desde escritor externo. MongoMock por defecto; fixture admite prueba Atlas opt-in CU25_LIVE_TESTS=1 sobre colecciones UUID, sin tocar datos migrados.
- Frontend automatizado: deltas atómicos, duplicados/huecos, snapshot y rol, respuesta HTTP atrasada, listas/layout, protección de prototipo, token fuera de URL, resync único, reconexión, cleanup y cierres de seguridad.
- Smoke por HTTP+WebSocket TCP real en 127.0.0.1: dos clientes, cambios persistidos, revisión obsoleta, reconexión, degradación y revocación PASS. Usa MongoMock temporal, no Atlas. Script/resultado locales ignorados en artifacts/cu10/wire-smoke.py y wire-result.json; timestamp 2026-11-07 11:44:19 Bolivia. Servidor temporal apagado al terminar; sin cambios a usuarios/proyectos reales.
- Atlas: ping agotó tiempo (ServerSelectionTimeoutError), credenciales redactadas. La IP anterior duraba seis horas. Usuario autorizó renovación por seis horas; no se logró modificarla porque el navegador/control visual falló al iniciar: "failed to write kernel assets: El sistema no puede encontrar la ruta especificada. (os error 3)". Se pidió al usuario renovar la IP actual y avisar estado Active. No se presenta como evidencia cloud aprobada de CU-10.
- Prueba visual humana: pendiente, misma indisponibilidad del control visual. Procedimiento: dos sesiones/cuentas owner/editor del mismo proyecto, crear/mover/editar y ver el mismo resultado sin recargar; Undo/Redo; desconectar/reconectar; degradar a VIEWER y revocar; comprobar edición bloqueada y acceso retirado. Confirmar que borradores del inspector no se pisan. No se declara esta prueba ejecutada.

## Estado, deuda y siguiente acción

Código y gates automáticos verdes. CU-10 permanece IMPLEMENTED hasta prueba sobre Atlas y aceptación visual. La deuda Atlas/visual se difiere por indicación explícita del usuario; se permite continuar CU-11, sin considerar cumplido el realtime remoto desplegado (CU-23). Datos migrados y respaldos de CU-25 sin cambios. No se reinició el backend normal anterior ni se desplegó esta versión; el smoke usó su servidor aislado.

No se hizo commit/push. CU-25 y CU-10 comparten archivos ya modificados del árbol: separar hunks al preparar commits; no usar git add . ni aplicar ciegamente los comandos globales históricos de CU-25. Se entregarán comandos exactos al cerrar el CU con un árbol revisado, sin mezclar CUs.
