# Estado real

Actualizado: 2026-11-07, America/La_Paz.

## Último CU cerrado

**CU-25 DONE, tres incrementos.** Herramienta CASE usando MongoDB Atlas por defecto. Migración real verificada: **3 usuarios, 15 proyectos y 2 permisos**, con hashes, IDs, ownership, revisión, timestamps, UML y layout preservados. PostgreSQL original quedó intacto y respaldado. CU-10/CU-11 IMPLEMENTED; aceptación Atlas/visual diferida por instrucción explícita del usuario de avanzar localmente. CU-26 también implementado. Por la nueva prioridad del usuario se reanudaron CU-21 y CU-09, implementados localmente; CU-13 también implementado localmente, siguiente CU-14. IA CU-18 sigue pendiente de credencial/benchmark.

## CU-10 actual

WebSocket autenticado, deltas canónicos, revisión, recuperación, control de acceso/revocación y cliente nativo integrado. Gate completo: **242 backend / 55 frontend**, estático y build PASS. Smoke HTTP+WebSocket TCP con dos clientes y MongoMock PASS; no equivale a Atlas. Ping Atlas agotó tiempo; renovación IP autorizada por usuario, pendiente de confirmar Active porque el control de navegador falló al iniciar. Aceptación visual pendiente. Ver CU-10-realtime-collaboration.md. Sin commit/push. El usuario pidió continuar localmente y diferir Atlas/visual; deuda explícita, no aceptación aprobada.

## CU-11 actual

Presencia efímera con TTL de quince segundos, identidad y permisos de servidor, dos pestañas, cursor/selección/edición, última actividad y avisos de entrada/salida. Documento/revisión UML intactos. Gate local 248 backend/61 frontend, estático/build y smoke TCP MongoMock PASS. Seis pruebas backend/seis frontend nuevas, con avisos externos de MongoMock TTL y chunk Vite preexistente. Prueba cloud/visual diferida como deuda explícita; siguiente CU-26. Sin despliegue ni commit/push.

## CU-26 actual

Conversación grupal, participantes conocidos, historial y actividad atribuida persistidos en colección sessions, independientes de UML/presencia. UUID idempotente, orden CAS, páginas de 50, roles y reservas duraderas para recuperar mensajes/actividad tras fallos. Panel Vue y stream compartido integrados, sin IA. Gate 258 backend/68 frontend y smoke TCP con reinicio del servidor/nuevo adaptador MongoMock PASS; evidencia final en CU-26. Aceptación Atlas/visual diferida por usuario. Sin cambios a datos reales, despliegue, commit o push. Siguiente CU-18: proveedor IA y benchmark; no hay clave cloud configurada.

## Implementación existente

CU-01..07 DONE según sus documentos; CU-00/08/09 con implementación y manual humano final pendiente según sus documentos originales. CU-08 JWT/Argon2/ownership; CU-09 EDITOR/VIEWER. Invitaciones/tokens/expiración implementados al reanudar CU-09, con interfaz y aceptación visual/cloud pendiente. CU-21 ahora implementa exportación/importación y round-trip para el subconjunto canónico; visual/EA real pendientes.

CU-25 añade MongoStore, selección de backend (mongodb por defecto), auth/proyectos/memberships NoSQL, CAS con autorización atómica, health y errores seguros. CLI de configuración protegida, prueba cloud, snapshot/migración sin sobrescrituras y verificación de origen. PostgreSQL sigue disponible explícitamente para respaldo/recuperación, no como autoridad normal del editor.

## Funciones antiguas: CU-21

Importación XMI como proyecto nuevo, parser seguro/validación, advertencias, round-trip semántico y corrección del exportador con tipos de clase implementados. API/UI y smoke HTTP TCP con MongoMock aprobados; gate final en CU-21. No se acredita aún prueba visual/EA real. Gate XMI final 277 backend/73 frontend PASS. CU-09 también implementó invitaciones por correo con token de un uso, vencimiento/cancelación y UI; gate final **282 backend/80 frontend**, estático/build y smoke TCP MongoMock PASS. Inventario en requirements/LEGACY-GAPS.md: generación CU-13..17 sigue pendiente, entre otros; no se declara paridad del primer parcial sin rúbrica. Sin modificaciones a datos reales ni commit/push.

## CU-13 actual

Conversión determinista UML/perfil→modelo relacional, tablas/columnas/PK/FK/UNIQUE/índices, enums de perfil, relaciones y JOINED de padre único. Tipos/metadatos/semántica inválidos no producen plan parcial; límites de cardinalidad avanzada quedan explícitos. Vista previa autenticada en editor y descarga JSON, sin aplicar esquema ni alterar revisión. Gate final **309 backend/86 frontend**, estático/build y smoke HTTP TCP MongoMock PASS (PK heredada, composición, independencia de layout). QA visual/cloud diferida, sin cambios de datos reales ni commit/push. Siguiente CU-14: generación Spring Boot, no implementada todavía.

## Datos conservados y límites

**13 de los 15 proyectos son legacy con ownerId sin usuario registrado**, situación ya existente. Se conservaron sin asignar propietarios ni crear cuentas ficticias; mantienen visibilidad/permisos anteriores. Cualquier reasignación requiere indicación explícita.

Atlas Free cu25-pruebas en AWS São Paulo, servidor 8.0.37 observado. Base actual examen_sw1_cu25_probe. Credencial limitada temporal por una semana e IP /32 autorizada por seis horas. Deben renovarse para operación duradera; no se abrió acceso global ni se contrataron tiers pagos. Secretos y respaldos excluidos de Git.

## Evidencia histórica del cierre CU-25

- Gate scripts/check.ps1 PASS: **235 backend**, 2 warnings externos, Ruff/compileall/pip check PASS; **46 frontend / 13 archivos**, typecheck/build PASS, warning existente de chunk >500 kB.
- Almacenamiento Atlas: round-trip, CAS, revisión obsoleta, concurrencia y cliente nuevo PASS; siete escenarios API Atlas PASS.
- pg_dump local PostgreSQL 17.6, archivo verificado y restaurado en una base temporal; comparación íntegra PASS. La base temporal fue retirada.
- Ensayo: 18 documentos insertados, segunda ejecución 0; importación final 18, comparación de usuarios/proyectos/permisos PASS. source-check final confirma SQL original idéntico.
- API real: auth/listados/lectura/denegación para todos los usuarios y proyectos; reinicio de backend, recuperación y nuevas operaciones Undo/Redo PASS. Datos temporales limpiados. Undo previo sigue efímero como antes.
- Resultado: artifacts/cu25/cutover-result.json, 2026-11-06 22:15:29 hora de Bolivia. Respaldo y snapshot en artifacts/cu25; archivos locales con datos sensibles, no compartir/versionar.

Backend del proyecto se dejó ejecutándose en 127.0.0.1:8000 tras el reinicio de prueba. Su información de proceso está en artifacts/cu25/backend-process.json; volver a comprobar si se reinició el equipo. No se ejecutó prueba humana nueva del frontend ni benchmark IA. No se hizo commit/push; comandos exactos en CU-25.

## Pendiente de producto

Validar la deuda Atlas/visual de CU-10/11/26 y continuar IA/voz, asesor/resúmenes, despliegue y visor móvil/push, además de los CUs previos abiertos. RP-01: enunciado primer parcial; RP-02: modificación IA por texto o solo voz; RP-03: NoSQL en aplicaciones generadas. No se inventan respuestas ni se declara aceptación integral del segundo parcial.

## Revisión manual disponible — 2026-11-07

Prueba local aislada preparada en http://localhost:5175, API 8001, datos ficticios temporales; [instrucciones](MANUAL-REVIEW.md). Gate 311 backend/86 frontend, estático/build y protocolo HTTP/WebSocket PASS. Aceptación visual y Atlas pendientes. No cambia el estado de los CUs; siguiente CU-14.

## Base para documentación académica — 2026-11-07

El usuario comunicó revisión visual inicial favorable, sin detallar escenarios; no se cierran gates manuales. Se prepararon delivery/INFORME-BASE.md y delivery/EVIDENCIAS.md con arquitectura actual, cobertura, resultados históricos y aceptación pendiente. No se modificó funcionalidad ni se inició CU-14.

## CU-14 en curso — incremento 1, 2026-11-07

Base del generador Jinja2 disponible: Java 21/Spring Boot, entidades/repositorios escalares, esquema PostgreSQL y README sin secretos. Salida compilada realmente, JUnit PASS; gate 336 backend/86 frontend, estático/build PASS. CU-14 no cerrado: faltan CRUD/relaciones y descarga/UI. No hay cambios visibles de este incremento en localhost:5175 ni cambio de persistencia CASE.

## CU-14 incremento 2 completado — 2026-11-07

Backend generado con CRUD, consultas tipadas/acotadas y navegación FK simple 1:1/1:N/self; readOnly/searchable/sortable explícitos. Gate 342 backend/86 frontend, estático/build y 51 comprobaciones HTTP/PostgreSQL/JVM PASS, base temporal retirada sin tocar datos originales. N:M/PK compuesta/herencia/composición/reglas de runtime se rechazan, no se omiten. Siguiente paso dentro del mismo CU: incremento 3, descarga por proyecto/revisión y UI. La pantalla de QA no cambió en esta iteración.

## Prioridad vigente: segundo parcial, CU-18 activo — 2026-11-07

El usuario priorizó explícitamente el segundo parcial. CU-14 pendiente de reanudación en incremento 3; código/evidencia anterior preservados. CU-18 inc.1 preparado: intención cerrada, resolver/validación sobre copia, contexto acotado y Gemini REST sin ejecución, dataset/runner y configurador privado. Gate 384 backend/86 frontend y estático/build PASS. El usuario no tiene clave; benchmark/inferencia real NOT_RUN, sin métricas estimadas. Aún no hay IA en la UI ni solicitudes grupales integradas. Sigue CU-18; después CU-19 → CU-27 → CU-23 → CU-28 según dependencias; no trabajar CU-14 en paralelo.

## CU-18 integración grupal/UI preparada — 2026-11-07

Único CU activo. Código listo para solicitudes grupales, registro/recuperación, permisos/JWT/revisión y formulario de evaluación sin aplicar cambios. Gate 402 backend/96 frontend, estático/build PASS; 60 pruebas específicas posteriores de atribución y smoke HTTP/WS sin clave PASS. No IA simulada activable en aplicación. Clave diferida por el usuario: benchmark/inferencia reales NOT_RUN; visual/Atlas pendientes. Sin reinicio del QA previo para preservar datos temporales. Completar validación de CU-18 antes de CU-19; CU-14 sigue pendiente de reanudación.

## Revisión actualizada sin clave disponible — 2026-11-07

Nueva vista aislada http://localhost:5176 (API 8002) activa para revisar el formulario pendiente de configuración; datos ficticios separados y proveedor deshabilitado. Prueba anterior 5175/8001 no alterada. Login/CORS/routing/status HTTP PASS; visual pendiente porque el runtime de control no inicia. Guía MANUAL-REVIEW.md; no llamada LLM ni cambios en código de producto. CU-18 sigue activo con clave/benchmark reales pendientes.

## Corte de trabajo para relevo — 2026-11-07

Entrega indicada: martes 10 de noviembre por la tarde, hora exacta pendiente. Guía delivery/RELEVO-EQUIPO.md para dos personas, con responsabilidades dentro de un CU, dependencias y control de plazo. El usuario probó la vista 5176 y expresó conformidad; IA real/benchmark/cloud y pruebas manuales específicas continúan pendientes. No es cierre integral del proyecto ni CU-18 DONE. Sin cambios de código ni nueva ejecución del gate histórico 402/96 al preparar este corte. Copia local de fuentes saneada prevista en artifacts/delivery, sin publicación/commit/push.
