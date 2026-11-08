# CU-11 - Mostrar presencia colaborativa

**Estado: IMPLEMENTED, aceptación visual/Atlas diferida como deuda autorizada.** Inicio 2026-11-07, America/La_Paz.

## Objetivo y dependencias

Participantes autorizados ven sesiones, selección, cursor, elemento en edición y última actividad, sin modificar ProjectDocument/revisión. Dependencia CU-10 implementado. Su aceptación Atlas/visual se difiere como deuda por petición explícita del usuario de avanzar localmente y hacer todo lo posible; no se elimina ni se aprueba por silencio. Product secciones 5.1 y 18.

## Plan autorizado

Dos incrementos máximos previstos: (1) presencia efímera con permisos sobre la suscripción existente y pruebas backend; (2) avatares/estado/cursor y selección/edición en Vue, pruebas y regresión. Sin chat, actividad persistente para IA, bloqueos de edición, despliegue ni cambios al modelo UML.

## Diseño a implementar

Se reutiliza /projects/{UUID}/sync. Mensajes presence separados de snapshot/patch; cliente informa solo cursor/selección/edición, servidor fija identidad/sesión/rol/hora. Sesión UUID por conexión; dos pestañas son sesiones distintas. Mongo conserva registros efímeros separados con TTL de 15 segundos y consulta filtrada por expiresAt para no depender de la limpieza asíncrona de TTL. Disconnect/revocación elimina solo esa sesión; heartbeat no incrementa revisión UML. El mismo almacenamiento permite visibilidad entre procesos sin un hub en memoria. Sin nueva dependencia. Modo SQL legacy no ofrece presencia distribuida.

Controles se limitan a dos por segundo por conexión; cursor en coordenadas del diagrama con throttle cliente; VIEWER puede observar/seleccionar, no anunciar edición. Selecciones/ediciones de elementos eliminados se limpian. No son locks: dos editores pueden seleccionar/editar el mismo elemento y CAS sigue decidiendo escrituras. No se garantiza historial ni tiempo exacto de expulsión durante corte de red; TTL acota residuos.

## Incremento 1 - DONE

Presencia con TTL/filtrado de vencimiento, identidad de servidor, roles, dos pestañas, aislamiento y cleanup implementados. Gate scripts/check.ps1 PASS: 247 backend (5 nuevas), 55 frontend, Ruff/compileall/pip check/typecheck/build. 79 warnings medidos: 77 de datetime.utcnow en MongoMock/TTL, más 2 previos Starlette/AnyIO; chunk Vite preexistente. Pruebas locales sin Atlas.

## Incremento 2 - IMPLEMENTED

Panel con sesiones/avatares, identidad y rol, selección/edición y hora de actividad; avisos de entrada/salida duran cuatro segundos. Cursores proyectados con pan/zoom y halos de selección, sin persistir Vue Flow como dominio. El inspector emite edición al tener un borrador modificado; no crea un bloqueo. Mensajes presence separados del flujo documental y opt-in negociado al autenticar, preservando clientes CU-10. Cliente agrupa cursor/selección a máximo dos envíos por segundo y reenvía el último estado al reconectar; recibir actualizaciones remotas no inventa actividad local. Cleanup de suscripciones/timers al salir.

Se corrigió cola de posiciones atrasadas ante almacenamiento lento: servidor agrupa controles pendientes, usa la última posición y limita ráfagas; no acumula indefinidamente cada movimiento. Test nuevo de diez posiciones encoladas verifica último cursor sin cambiar documento. Identidad/rol/hora vienen del servidor, no del cliente.

Gate final scripts/check.ps1: 248 backend y 61 frontend, Ruff/compileall/pip check/typecheck/build PASS. Seis pruebas backend nuevas y seis frontend nuevas respecto de CU-10, más ampliación del test existente del inspector para señal de edición. En la ejecución final backend hubo 90 warnings: 88 datetime.utcnow de MongoMock TTL, dos externos existentes; el número de avisos TTL depende de las consultas. Chunk Vite >500 kB preexistente. No aplica benchmark IA.

Smoke por HTTP/WebSocket TCP loopback PASS: dos sesiones, cursor remoto, revisión/documento inalterados y cleanup tras salir. MongoMock temporal, no Atlas; servidor aislado apagado. Resultado artifacts/cu11/wire-result.json, 2026-11-07 12:38:28 Bolivia; script privado ignorado artifacts/cu11/presence-wire.py.

Prueba visual y cloud siguen diferidas por la instrucción expresa del usuario de avanzar sin configurar Atlas. No se presentan como aprobadas. No se cambió la configuración normal Mongo ni datos migrados. Modo SQL legacy no negocia presencia distribuida; la ruta normal CASE es Mongo.


## Evidencia y cierre

Implementado en dos incrementos. Pruebas cubren dos sesiones/pestañas, cursor/selección/edición, VIEWER sin edición, spoofing/NaN/límites, aislamiento, expiración filtrada antes de TTL, revocación, elementos eliminados, cleanup, agrupación de controles y proyección/identidad escapada en UI. No se afirma prueba real multiworker ni benchmark de carga. TTL es eventual: la consulta excluye expiresAt vencido sin esperar a Mongo. Lease de quince segundos mantiene heartbeat sin modificar UML.

Aceptación manual pendiente: dos ventanas/cuentas del mismo proyecto, ver avatar/cursores y halo con zoom/pan; cambiar selección/borrador, cerrar una pestaña, degradar/revocar; comprobar que revisión no cambia solo por presencia. Control visual no disponible según CU-10; deuda diferida, no otra solicitud de configuración al usuario.

No se ejecutó commit/push; cambios compartidos con CUs no confirmados requieren stage de hunks separados, nunca git add .; no mezclar CUs. Siguiente CU-26, manteniendo la deuda explícita y desarrollando/pruebas locales.
