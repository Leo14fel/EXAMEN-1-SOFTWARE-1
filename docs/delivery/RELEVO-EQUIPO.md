# Relevo para trabajar entre dos personas

Fecha de corte: 7 de noviembre de 2026, America/La_Paz. Entrega indicada por el usuario: **martes 10 de noviembre por la tarde**; hora exacta sin confirmar. Este es un corte de trabajo, no una declaración de proyecto terminado ni un roadmap alternativo.

## Punto de partida

Leer en orden product.md, el [roadmap](../puds/use-cases/IMPLEMENTATION-ROADMAP.md), [CU-18](../puds/use-cases/CU-18-natural-language.md), PROJECT-CONTEXT y documentación específica. Prioridad vigente: segundo parcial. Se trabaja un CU a la vez; ambas personas colaboran en ese CU, con archivos/responsabilidades separados.

| Área | Estado al entregar este relevo |
| --- | --- |
| Editor, acceso y permisos | Implementados; preservar funciones anteriores |
| NoSQL CASE | Migración a Atlas verificada antes; acceso actual y funciones grupales posteriores requieren revalidación cloud |
| Colaboración, presencia y sesión grupal | Implementadas y probadas localmente; aceptación remota pendiente |
| CU-18 | Contratos, proveedor candidato Gemini, solicitudes grupales autorizadas y formulario preparados; sin inferencia real ni benchmark aprobado |
| Voz / asesoría y resúmenes / despliegue / móvil con push | CU-19 / CU-27 / CU-23 / CU-28 pendientes, respetando dependencias |
| Generación de aplicaciones anterior | CU-14 incrementos 1/2 preservados; incremento 3 y CU-15..17 pendientes de reanudación |
| XMI / imagen / offline y aceptación integral | XMI soportado pendiente de EA real; CU-22 pendiente; CU-12 y CU-24 requieren revisión del primer parcial |

Último gate de código registrado: **402 backend / 96 frontend (22 archivos)**, análisis estático/tipos/build PASS. Después: 60 pruebas específicas de atribución, Ruff y compileall PASS. Son ejecuciones históricas del 7 de noviembre, no una nueva ejecución al redactar este documento. Fuentes: [TESTING](../TESTING.md), [evidencias](EVIDENCIAS.md).

El usuario probó la vista nueva y expresó conformidad. Se registra como revisión humana favorable de la demostración sin clave; no confirma inferencia, permisos remotos, push, benchmark ni todos los escenarios manuales.

## Lo que impide cerrar CU-18 ahora

1. No hay clave de Gemini configurada. Crear/guardar una personalmente según la [guía](../deployment/GEMINI-CU18.md); no compartirla en chat ni versionarla.
2. Ejecutar comparación real sobre los doce casos congelados, revisar respuestas y registrar métricas reales. Corregir dentro del incremento 3 si el modelo/schema falla; no crear un cuarto incremento.
3. Revalidar integración en Atlas y verificar visualmente el flujo con dos participantes. La aceptación local no prueba acceso remoto ni recuperación cloud.
4. Resolver RP-02 antes de habilitar aplicación por texto. Actualmente solo se evalúan propuestas; no hay botón/ruta de aplicación textual. Voz se implementa en CU-19.

La dependencia de clave/benchmark no se resuelve etiquetando el CU como DONE. Tampoco es necesario rehacer lo preparado.

## Reparto propuesto dentro del CU activo

| Persona | Responsabilidad | Zona principal |
| --- | --- | --- |
| A | Configuración privada, proveedor/benchmark, contratos, contexto y persistencia/autorización | backend/app/ai, backend/app/api/ai.py, backend/app/db/ai_requests.py y sus tests |
| B | Formulario/historial, pruebas manuales entre roles, capturas saneadas y documentación de evidencia | frontend/src/features/editor/AiRequestPanel*, ai-api*, GroupSessionPanel* y docs/delivery |
| Ambas | Revisar contratos antes de cambiarlos, probar juntas editor/observador, integrar y ejecutar gates | Archivos compartidos, documento del CU y scripts/check.ps1 |

Un responsable por archivo compartido: acordar quién modifica main.py, config.py, editor-store.ts, EditorWorkspace.vue y el documento del CU antes de editar. Si una tarea necesita otro CU, anotarla como pendiente, sin adelantar su implementación en paralelo. No contratar IA, cambiar tecnologías o inventar comportamiento para ahorrar tiempo.

## Puntos de control hasta el martes

Las siguientes ventanas son objetivos de coordinación, no duraciones medidas ni una garantía de terminar el alcance completo.

| Ventana | Punto de control | Si falta evidencia |
| --- | --- | --- |
| Sábado 7 | Entregar este relevo/copia de fuentes, repartir archivos y reunir clave/accesos/rúbrica/dispositivo | Registrar responsables y bloqueo concreto |
| Domingo 8 por la mañana | Intentar cerrar CU-18 con proveedor/benchmark y grupo reales | Corregir el CU; no simular ni saltar su dependencia |
| Domingo 8, siguiente ventana disponible | CU-19: voz, transcripción y comandos validados, con benchmark STT | Mantener resultado como pendiente si no hay medición/ejecución real |
| Lunes 9 | Si dependencias están verificadas, CU-27 y después CU-23 | Revisar inmediatamente el riesgo de plazo si aún falta IA/voz |
| Martes 10, antes de entregar | CU-28 cuando exista despliegue válido; demostración remota, push real y revisión integral | No afirmar cumplimiento móvil/push sin dispositivo y evidencia |

El calendario tiene poco margen, especialmente para despliegue/push. La generación anterior y demás pendientes siguen obligatorios hasta cotejar la rúbrica; no se eliminan para aparentar entrega completa. Si las dependencias se retrasan, acordar con el docente una decisión explícita sobre alcance o plazo. No se fija aquí una fecha de cierre inventada para cada caso ni se promete terminar todo el martes.

## Pruebas y demostración disponibles

Vista actualizada de solo preparación de IA: http://localhost:5176, API 8002, fixtures MongoMock separados y proveedor deshabilitado expresamente en ese proceso. Cuenta owner@prueba.local, contraseña ficticia Prueba1234!. Editor/viewer usan las cuentas de la [guía manual](../MANUAL-REVIEW.md). La prueba anterior 5175/8001 no fue reiniciada.

Ambas son temporales, locales a esta computadora y no accesibles desde el celular por esos enlaces. Los cambios se pierden al cerrar sus respectivos backends. Preservar/exportar diagramas temporales importantes antes de reiniciar. La instancia 5176 seguirá sin proveedor aunque se agregue una clave al archivo: iniciar una instancia configurada para la prueba real.

Verificaciones para el equipo:

```powershell
.\scripts\check.ps1
cd backend
.\.venv\Scripts\python.exe -m app.ai.benchmark --fixtures-only
```

El segundo comando debe indicar NOT_RUN, no calidad LLM aprobada. Con clave, ejecutar el runner sin ese flag solo cuando se decida efectuar las 24 llamadas de comparación y consumir la cuota correspondiente. No usar resultados controlados de tests como respuestas reales de una demo.

## Git y copia de fuentes

Rama observada: feat/xmi-export. HEAD observado: c3bbdc34af1b87e3c2e832af8c619122bdc33a18. En el corte inicial existían cambios locales de varios CUs sin commit. Después, el usuario autorizó registrarlos y subirlos: el contenido se organizó en commits separados por CU y soporte/documentación. Para obtener el avance versionado, usar la rama feat/xmi-export una vez sincronizada con origin; revisar git log y el estado remoto, sin copiar .env o artifacts.

La publicación fue autorizada expresamente por el usuario después del corte inicial. Se preparó una base compartida con commits separados por CU y selección de contenido en archivos compartidos, conservando el resultado final verificado. La sincronización remota se confirma al terminar el envío. No ejecutar git add . ni usar un único commit para todos los CUs. Los comandos históricos de cierre deben revisarse contra el estado actual; no copiarlos de forma ciega.

Se preparará una copia local de fuentes para conservar el estado actual sin secretos, dependencias instaladas, datos de bases, artifacts ni .git. Sirve de respaldo/revisión, no sustituye los commits ni una instalación probada en la computadora del compañero. La copia no se publica ni se envía a nadie automáticamente. Configurar credenciales por separado; nunca copiar backend/.env ni respaldos reales al paquete de trabajo.

## Qué entregar como evidencia final

Informe actualizado con funciones reales y límites, matriz del docente, casos de uso, arquitectura, procedimiento de ejecución y registros de pruebas. Añadir capturas reales de roles, colaboración remota, IA grupal por solicitud, voz, resumen de avances, reapertura persistente y push en dispositivo cuando existan. Incluir errores/correcciones y revisión/fecha del código; ocultar claves, tokens y códigos de invitación.

Pendientes RP-01/rúbrica, RP-02/texto-voz y RP-03/NoSQL generado permanecen en la [matriz de requisitos](../requirements/SECOND-PARTIAL.md). No resolverlos por suposición ni convertir la conformidad general del usuario con la pantalla en aprobación integral.

## Obtener la base compartida

Después de confirmar el envío a GitHub, en una computadora nueva:

```powershell
git clone --branch feat/xmi-export https://github.com/Leo14fel/EXAMEN-1-SOFTWARE-1.git
cd EXAMEN-1-SOFTWARE-1
```

Si ya existe una copia, conservar primero cualquier cambio local, luego consultar origin y actualizar mediante fast-forward. Cada persona puede crear su rama desde esa base, por ejemplo codex/cu18-backend y codex/cu18-frontend-qa. Mantener un responsable por archivo compartido y un único CU activo. Las credenciales, respaldos reales y dependencias instaladas permanecen fuera del repositorio; seguir README.md y las guías de entorno.

Pruebas de la versión final antes de publicar: 402 backend/96 frontend, estático/tipos/build PASS (7 de noviembre). La organización de commits no declara IA real ni benchmark aprobados, ni cierre de CU-18.
