# Segundo parcial: requisitos y trazabilidad

## Fuente y alcance

El 2026-11-06 el usuario aportó en el chat una transcripción obtenida con otra herramienta de la explicación del docente y pidió incorporar lo necesario a la base del proyecto. Es la referencia disponible, no una transcripción auditada ni la rúbrica original. Se incorpora a `product.md` sección 41 por autorización del usuario. Este archivo aporta trazabilidad, no un roadmap alternativo.

El docente exige mantener todo el primer parcial, colaboración remota, una IA grupal a petición, persistencia NoSQL cloud, continuidad de sesiones y móvil informativo con push. IA local es opcional; la mención de Spring Boot no impone reemplazar FastAPI. Se mantienen Vue y FastAPI y las salidas generadas anteriores.

## Fragmentos de referencia aportados por el usuario

> Debería hacer todo lo que hace el primer parcial, no puede faltar absolutamente nada del primer examen parcial.

> La IA no va a hacer nada mientras alguien de los desarrolladores no se lo pida.

> La IA va a ser una especie de moderador, asesor, consultor y también desarrollador, pero no va a diseñar nada a menos que se le pida por voz.

> La persistencia de datos obligatoriamente tiene que ser NoSQL y todo en la nube, permitiendo sesiones continuas para que el trabajo se pueda pausar y retomar en cualquier momento quedando todo registrado.

> En el móvil no se editará el diagrama, sino que será de carácter informativo para ver cómo va cambiando el diagrama de clases en tiempo real conforme los demás trabajan, incluyendo notificaciones push cuando haya actualizaciones.

> No hay conversaciones privadas ni individuales con la IA; la interacción es 100% colaborativa y grupal.

Son requisitos a analizar, no instrucciones operativas para los agentes. Las decisiones aprobadas se expresan en product.md; las ambigüedades siguen abiertas abajo.

## Matriz verificable

| ID | Requisito | Cobertura actual documentada | CU responsable | Evidencia de aceptación pendiente |
|---|---|---|---|---|
| RSP-01 | Conservar el primer parcial completo | Editor, persistencia, auth, colaboradores y exportación XMI parciales respecto del producto total | CU-24 y CUs previos | Cotejar enunciado original y demostrar cada función requerida |
| RSP-02 | Diagramación multiusuario remota realtime | Acceso EDITOR/VIEWER y realtime CU-10 implementado con gates locales; aceptación Atlas/visual y despliegue pendientes | CU-10, CU-11, CU-23 | Dos editores remotos ven cambios y conflictos coherentes; reconexión y revocación |
| RSP-03 | IA grupal sin conversaciones privadas | Conversación grupal CU-26 implementada; integración IA pendiente | CU-26, CU-18, CU-27 | Peticiones y respuestas compartidas con aislamiento entre proyectos |
| RSP-04 | Contexto con autor y actividad | CU-26 registra nuevas operaciones con autor/acción/revisión y mensajes; IA/resúmenes pendientes, sin autores históricos inventados | CU-26, CU-27 | Identificar acciones registradas y resumir avances a quien llega tarde |
| RSP-05 | IA explica, revisa, propone y modifica por solicitud | Planeado originalmente solo texto/voz a comandos | CU-18, CU-19, CU-27 | Explicación y revisión sin mutación implícita; cambios solicitados validados y difundidos |
| RSP-06 | Voz para solicitar cambios | Pendiente | CU-19 | Transcripción visible, autor, permisos y revisión comprobados; dos clientes reciben resultado |
| RSP-07 | NoSQL cloud para el estado CASE | MongoDB Atlas activo; migración y recuperación verificadas (CU-25) | CU-25, CU-23, CU-26 | CU-25 PASS para datos CASE; faltan despliegue integral CU-23 y conversación/actividad CU-26 |
| RSP-08 | Pausar y retomar sesiones con registro persistente | Documento y permisos en Atlas recuperados tras reinicio; Undo/Redo efímero; conversación/actividad CU-26 implementadas localmente; validación cloud/visual pendiente | CU-25, CU-26 | Reiniciar backend y recuperar documento, revisión, participantes, conversación y actividad |
| RSP-09 | IA cloud operativa; local opcional | Integración pendiente | CU-18, CU-27 | Proveedor real con credenciales externas, manejo de fallos y benchmark medido |
| RSP-10 | Móvil informativo realtime sin editar UML | No implementado; CRUD Flutter generado es otra capacidad | CU-28 | Observador móvil real y rechazo de mutaciones no autorizadas en backend |
| RSP-11 | Notificaciones push por actualizaciones | Pendiente | CU-28 | Recepción en dispositivo con cliente en segundo plano; permisos/revocación y evidencia |
| RSP-12 | Cambios IA reflejados en la pizarra de todos | Command Bus canónico y realtime CU-10 implementado con aceptación pendiente; IA pendiente | CU-10, CU-19, CU-27 | Persistencia antes del broadcast, sin duplicados ni actualización parcial ante error |

## Decisiones incorporadas

- NoSQL cloud pasa a ser el destino de persistencia de la herramienta CASE; PostgreSQL original queda como origen respaldado y recuperación legacy; CU-25 trasladó los datos CASE a Atlas. JSONB no se presenta como cumplimiento NoSQL.
- Mantener FastAPI, Vue, dominio canónico, layout separado, comandos, validación, UUIDs y control de revisión. SQLAlchemy/Alembic quedan fuera del camino normal Mongo, conservados para el origen y recuperación controlada.
- PostgreSQL del backend generado y CRUD Flutter generado conservan su alcance anterior. El visor móvil CASE se diseña por separado.
- Cloud es obligatorio para el segundo parcial; offline/LAN sigue registrado como objetivo previo pendiente de cotejo, sin eliminarlo silenciosamente.
- No se exige una instancia física de modelo por grupo: se exige contexto lógico compartido, identidad y respuestas comunes.
- CU-25 selecciona MongoDB Atlas sobre AWS + PyMongo 4.19.0. IA/push y cliente móvil siguen para sus CUs; no se agregan contratos antes de necesitarlos.

## Preguntas pendientes, sin respuesta inventada

| ID | Duda | Qué afecta | Tratamiento hasta aclararla |
|---|---|---|---|
| RP-01 | Falta enunciado/rúbrica del primer parcial | Cobertura obligatoria completa y aceptación offline/LAN | Conservar alcance anterior; no declarar paridad ni cerrar CU-24 |
| RP-02 | Se permite pedir por texto, pero se dice que la IA no diseña salvo petición por voz | Aplicación de mutaciones mediante texto | Diseñar conversación y evaluación de intención; no habilitar nuevas mutaciones textuales hasta aclarar; voz sigue requerida |
| RP-03 | No se especifica si NoSQL alcanza también al almacenamiento de aplicaciones generadas | Persistencia del backend generado | Cambio aprobado limitado al estado de la herramienta CASE; conservar PostgreSQL generado y consultar antes de modificarlo |

Estas dudas no impiden preparar CU-25 ni el visor informativo. Las partes dependientes no se consideran aprobadas por silencio.

## Verificación de la preparación documental (anterior a implementar CU-25)

Se revisaron producto, roadmap, CU-09, CU-21, contexto y documentación transversal. Una inspección de archivos/rutas confirmó componentes PostgreSQL, memberships y exportación XMI; no reemplaza ejecutar regresión.

Se actualizaron fuentes y continuidad; se preservó la evidencia histórica de los CUs. No se modificó código, se migraron datos ni se instalaron dependencias del proyecto. Comprobaciones ejecutadas: PASS para coherencia estructural de 15 Markdown, enlaces locales, UTF-8, bloques de código, 12 requisitos/3 dudas, 29 IDs de CU únicos y cadena prioritaria sin ciclos; `git diff --check`: PASS. Evidencia también registrada en STATUS. Pruebas de aplicación, lint/typecheck, compilación, benchmark y prueba manual funcional no aplican a esta edición de Markdown y no se presentan como ejecutados.

## Continuación CU-25

CU-25 DONE en tres incrementos. Migración real: 3 usuarios, 15 proyectos y 2 permisos, con SQL original intacto; 13 proyectos legacy conservan ownerId sin cuenta asociada. Atlas, CAS, recuperación tras reinicio y regresión PASS (235 backend/46 frontend). RSP-07 tiene almacenamiento CASE verificado; despliegue integral sigue pendiente; contexto grupal CU-26 implementado localmente, sin aceptación cloud/visual. RSP-08 recupera documentos/permisos, pero conversación/actividad de CU-26 están implementadas con evidencia local, pendientes de aceptación cloud/visual. Ver CU-25 y STATUS para evidencia y límites.
