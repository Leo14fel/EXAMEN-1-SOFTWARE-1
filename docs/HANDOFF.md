# Handoff

## Punto estable

CU-25 DONE en tres incrementos. MongoDB Atlas es la autoridad normal del editor y PERSISTENCE_BACKEND=mongodb el valor por defecto y local. PostgreSQL 17.6 original sigue intacto; SQLAlchemy/Alembic y adaptador SQL se conservan para recuperación y herramientas legacy. No se hizo commit/push. Comandos exactos en CU-25, rama actual feat/xmi-export.

## Datos y evidencia

3 usuarios, 15 proyectos y 2 permisos migrados y comparados íntegros. 13 proyectos legacy ya tenían ownerId sin usuario registrado; se conservaron tal cual y no se reasignaron. Backups sensibles locales: artifacts/cu25/postgres-20261107T020534Z.dump y source-20261107T020534Z.json; ambos ignorados por Git. No imprimir ni subir sus contenidos a chat/docs.

Respaldo restaurado en base SQL temporal y comparado; ensayo Atlas idempotente; importación final; API real para usuarios/permisos y reinicio del backend PASS. Gate final: 235 backend/46 frontend, estático y build PASS. Ver STATUS/CU-25 para límites y warnings existentes.

## CU-10 implementado, aceptación pendiente

Continuar docs/puds/use-cases/CU-10-realtime-collaboration.md. Transporte y cliente implementados; gate 242 backend/55 frontend, estático/build PASS. Smoke TCP de dos clientes en MongoMock PASS, servidor temporal retirado. Atlas agotó tiempo; usuario autorizó renovar IP actual por seis horas. Navegador y control visual no arrancan (kernel assets, os error 3); usuario debe confirmar regla Active. El usuario pidió avanzar sin configurar Atlas y diferir verificación cloud/visual como deuda explícita. CU-11 también IMPLEMENTED: presencia TTL, UI/cursor/selección/edición, gate 248 backend/61 frontend, TCP MongoMock PASS. CU-26 también IMPLEMENTED: sesión/mensajes/actividad duraderos y UI compartidos; gate 258 backend/68 frontend, TCP/reinicio de servidor y nuevo adaptador MongoMock PASS. Consultar su documento para evidencia final. Siguiente CU-18; clave IA cloud ausente, no se ejecutó llamada/benchmark LLM. No declarar aceptación cloud/visual. Código normal anterior no fue reiniciado/desplegado.

CU-25 y CU-10 comparten cambios no confirmados: no aplicar comandos históricos de stage amplio ni mezclar CUs; revisar hunks para commits separados. No se hizo commit/push.

## Próximo paso

Leer product.md → roadmap PUDS → último CU-26 y siguiente CU-18 → PROJECT-CONTEXT y documentación específica. Trabajar solo colaboración realtime; presencia y conversación pertenecen a CUs posteriores. No reabrir migración ni continuar XMI en paralelo. La autorización del usuario de avanzar dentro del plan sigue vigente; no volver a solicitarla para trabajo rutinario ya autorizado.

El backend local se dejó activo en 127.0.0.1:8000. Verificar proceso antes de arrancar otro; su recibo local está en artifacts/cu25/backend-process.json. El frontend se inicia con npm run dev si hace falta.

## Accesos y recuperación

Atlas Free en AWS São Paulo, base examen_sw1_cu25_probe. Usuario cu25_probe temporal de una semana; IP /32 actual autorizada por seis horas. Puede requerir renovación para continuar después de expirar. Secretos únicamente en backend/.env, excluido de Git. Los tests cloud usan prefijos UUID y nunca borran users/projects migrados.

No cambiar simplemente a SQL después de editar en Mongo: congelar y reconciliar avances nuevos primero. No restaurar respaldos sobre el origen sin un plan explícito. La copia SQL y el snapshot permanecen disponibles. RP-01..03 siguen abiertos en SECOND-PARTIAL; no inventar alcance.

## Reanudación de funciones antiguas

Usuario pidió completar pendientes antiguos. CU-21 implementado en sus tres incrementos: exportación previa + parser/round-trip + API/UI de importación como proyecto nuevo. Gate final/evidencia en CU-21; smoke TCP MongoMock PASS sin tocar datos originales. Aceptación visual/EA real pendiente. requirements/LEGACY-GAPS.md registra pendientes reales: CU-09 también implementado con token de un uso/correo/vencimiento/cancelación y UI; gate 282 backend/80 frontend, estático/build y TCP MongoMock PASS. CU-13 también IMPLEMENTED (tres incrementos): mapper/perfil/relaciones/JOINED y API/vista previa; gate 309 backend/86 frontend y TCP MongoMock PASS. Siguiente CU-14; no hay Java/SQL/Flutter generado todavía. Respetar avisos/requisitos de runtime del modelo relacional al generar. No iniciar varios CUs a la vez ni mezclar commits.

## Estado más reciente: revisión manual preparada, 2026-11-07

Prevalece sobre las instrucciones históricas de arranque: el último chequeo encontró 8000/5173 apagados y Atlas sin respuesta. Se dejó activa una prueba aislada en http://localhost:5175 (API 8001), con MongoMock temporal y cuentas ficticias; no sustituye el arranque normal ni modifica .env. Instrucciones y limitaciones en [MANUAL-REVIEW.md](MANUAL-REVIEW.md). Gate 311 backend/86 frontend, estático/build y smoke HTTP/WebSocket PASS. Revisión visual del usuario pendiente; Atlas sigue pendiente. No se implementó CU-14 en esta preparación; sigue como siguiente CU. No se hizo commit/push.

## Documentación de entrega preparada — 2026-11-07

Consultar delivery/INFORME-BASE.md y delivery/EVIDENCIAS.md para redactar la entrega y reunir capturas reales. Comentario humano favorable general registrado; no equivale a ejecutar el recorrido manual completo. Mantener documentación por incremento y completar evidencia real al implementar CU-14, que sigue siendo el siguiente caso. Esta revisión solo modifica Markdown.

## Continuar CU-14 — 2026-11-07

CU-14-spring-backend-generation.md es el caso activo, incremento 1 DONE. Plan de tres incrementos autorizado en el chat. Generator backend/app/generation/spring.py/templates, Jinja2 3.1.6 agregado y empaquetado. Gate 336/86 y Gradle/JUnit reales PASS, recibo artifacts/cu14/foundation-result.json. Siguiente incremento 2: capacidades CRUD/consulta/relaciones con validación y ejecución PostgreSQL aislada; no adelantar CU-15 ni inventar negocio. Incremento 3: entrega autorizada por proyecto/revisión y UI. Foundation rechaza relaciones/composite PK; aún no hay descarga. QA local del usuario no reiniciado; datos temporales siguen aparte. No commit/push ni cambio a product.md.

## Continuar CU-14 incremento 3 — 2026-11-07

Inc.2 DONE: CRUD/DTO/servicios/REST, filtros/orden/paginación/búsqueda/count y navegación FK simples; perfil readOnly/searchable/sortable (false por defecto). Gate 342/86 y 51 checks PostgreSQL 17.6 HTTP/JVM reales PASS. Recibo artifacts/cu14/crud-result.json, base temporal eliminada; servidor QA del usuario no reiniciado. El renderer recibe GenerationProfile como tercer argumento: pasar el mismo perfil validado desde el proyecto al integrar la descarga para no perder capacidades. Genera IDs Java sin guion bajo (Spring Data interpreta guiones bajos como rutas); no cambia nombres SQL. UnsupportedGeneration para N:M/composite/JOINED/composición/conteos; UI debe mostrar error sin ZIP parcial. Queda inc.3: descarga autorizada ligada a revisión y UI/regresión, sin ejecutar Gradle ni código generado en solicitudes del servidor CASE. No adelantar CU-15. No commit/push.

## Vigente: acelerar segundo parcial, CU-18 — 2026-11-07

La última instrucción del usuario prioriza segundo parcial sobre primero; prevalece sobre el siguiente CU-14 histórico. CU-14 queda pendiente de reanudación con inc.1/2 verdes e inc.3 pendiente. Único activo CU-18: leer su documento tras producto/roadmap y continuar sus incrementos 2/3, sin saltar a CU-19. Contratos/contexto/resolver/adaptador Gemini y dataset/runner listos; 42 tests específicos, gate 384/86, estático/build PASS. No endpoint/UI de IA todavía. Usuario confirmó que no tiene clave; guía deployment/GEMINI-CU18.md y python -m app.ai.configure para entrada privada. Ninguna clave se escribió ni se pidió por chat. Benchmark solo fixtures-only, NOT_RUN, doce casos/cero solicitudes/métricas null, hardware y hashes. No declarar modelo elegido por calidad ni CU-18 cerrado. Revalidar permisos/revisión al integrar persistencia grupal; nunca aplicar cambios por texto (RP-02). No modificar CU-14 en paralelo ni product.md para progreso; sin commit/push.

## Vigente: CU-18 preparado hasta formulario — 2026-11-07

El usuario pidió avanzar mientras hace la clave después. Se implementaron las partes verificables de inc.2/3: app/api/ai.py, db/ai_requests.py y UI AiRequestPanel junto al grupo. GET status, POST requests (ID/revisión/texto), GET resultado; siempre proposalOnly, no apply. Revalidación JWT/cuenta/permiso/revisión tras proveedor. Reserva _aiRequest lease 30 s y marcador permanente _aiSeen bloquean inferencias duplicadas, inclusive carrera de finalización antes de CAS; ambos se excluyen de ProjectDocument. Recuperación en ledger normal/WS, sin reintentos automáticos de proveedor y sin segunda fuente UML.

Gate 402/96, estático/build PASS; después 60 específicos de atribución y smoke TCP sin clave PASS. Ver CU-18 para fallos/correcciones y límites. ConfigSecretStr y guía deployment/GEMINI-CU18.md; no clave nueva guardada. Proveedor real/benchmark NOT_RUN; no cerrar CU ni avanzar a CU-19. El servidor QA antiguo no fue reiniciado: código nuevo requiere reinicio y los fixtures se pierden; preservar/exportar lo importante antes. El smoke aislado se retiró. No commit/push/product.md ni datos reales alterados. Siguiente acción: prueba real/benchmark y aceptación cuando haya clave; corregir dentro del incremento 3, no abrir un cuarto incremento.

## Última preparación manual, 2026-11-07

Vista nueva activa localhost:5176 / API 8002 con factory QA actualizada y proveedor forzado sin clave por env del proceso. Instancia anterior intacta, no reutilizar su script stop-qa.ps1. Recibo artifacts/cu18/preview-processes.json, helper seguro artifacts/cu18/stop-preview.ps1, config frontend/.vite/qa-cu18.config.ts (todos ignorados). Login fake owner@prueba.local / Prueba1234!; archivos y datos temporales sin Atlas. Readiness HTTP PASS a las 19:30:52 Bolivia. Control visual sigue fallando al inicializar kernel; no se afirma revisión humana/screenshot. Si el usuario crea la clave, esta vista permanece sin proveedor por diseño: iniciar una instancia configurada para prueba real, preservando/exportando antes los temporales que interesen. CU-18 sin cerrar; no cambiar a CU-19/CU-14. Sin commits/push.

## Corte para relevo de dos personas — 2026-11-07

El usuario pidió cerrar este avance para organizarse con otra persona y fijó entrega martes 10 de noviembre de 2026 por la tarde, hora exacta pendiente. Punto de entrada: delivery/RELEVO-EQUIPO.md. CU-18 conserva IN PROGRESS: implementación preparada/pruebas controladas verdes, clave y benchmark/inferencia reales pendientes. Usuario revisó favorablemente la vista 5176, sin confirmar todas las pruebas funcionales. No cerrar CU-18 como DONE ni saltar a CU-19 antes de resolver dependencia.

La base para compartir tiene cambios locales/untracked de varios CUs; clonar la rama feat/xmi-export no trae este trabajo todavía. Se prepara copia de fuentes local saneada en artifacts/delivery/corte-2026-11-07-fuentes.zip con manifiesto de hashes, excluyendo secretos, datos reales y dependencias; no se envía/publica. Antes de trabajo en ramas: organizar commits separados por CU/hunks, sin git add . ni commit/push automáticos. Dos personas dentro del CU activo: A backend/proveedor; B frontend/QA/evidencia, acuerdos de archivos compartidos. El plan incluye puntos de control y riesgo de plazo, sin quitar requisitos anteriores ni prometer tiempos no medidos.
