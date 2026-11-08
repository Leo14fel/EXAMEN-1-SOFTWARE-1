# Arquitectura: estado actual y objetivo

## Estructura existente

Monorepo con frontend Vue 3/TypeScript/Vuetify/Pinia y Vue Flow, backend Python/FastAPI y docs. Pydantic define el dominio y los contratos actuales.

```text
Vue / Pinia / Vue Flow (proyección)
             | HTTP autenticado + UmlCommand + baseRevision
             v
FastAPI / autorización por proyecto
             v
UmlCommandBus -> executor -> ProjectDocument
             v
MongoStore / MongoDB Atlas (persistencia actual)
```

CU-08 añade JWT/Argon2 y ownership; CU-09 memberships EDITOR/VIEWER y administración por owner. La exportación XMI reutiliza autorización de lectura y el modelo canónico. CU-10 implementa colaboración WebSocket con cliente nativo y deltas canónicos; aceptación Atlas/visual pendiente. IA todavía no implementada.

## Invariantes que se conservan

ProjectDocument mantiene UUID, metadata, ownerId, revisión, timestamps UTC, CanonicalUmlModel y DiagramLayout. El modelo semántico no contiene layout; Vue Flow lo proyecta y no decide reglas de dominio.

Clases, atributos, operaciones/parámetros y relaciones mantienen UUIDs globalmente únicos. Association tiene extremos neutrales; aggregation/composition van de todo a parte; generalization de hija a padre. Multiplicidades se mantienen en el dominio. Autoherencia y ciclos de herencia se rechazan; association/aggregation/composition pueden ser autorrelaciones.

Cada mutación pasa por comandos tipados y executor, sin lógica duplicada en frontend. Drag se confirma por SetNodeLayoutCommand; auto-layout usa d3-dag y comandos de layout. El inspector conserva borradores locales sin sobrescribirlos con respuestas externas. La validación semántica está separada de invariantes estructurales y restricciones específicas de comandos.

Undo/Redo mantiene hasta 100 snapshots efímeros. La revisión es monótona; identidad, ownership y creación se conservan. El lock process-local protege el bus local y el CAS Mongo conserva atomicidad y concurrencia entre procesos. Un lock en memoria por sí solo no es garantía distribuida.

## Objetivo integral del segundo parcial (implementado parcialmente)

```text
Editores web autorizados + observador móvil
                    | HTTP / WebSocket
                    v
FastAPI: acceso, sesión grupal, actividad, comandos
       |                     |                |
       v                     v                v
NoSQL cloud          IA cloud por pedido    Push
estado/contexto      respuesta grupal       móvil
```

CU-25 implementó y verificó almacenamiento Atlas, migración y recuperación sin perder usuarios, acceso o documentos. CU-10/11 incorporan sincronización y presencia; CU-26 persistencia de conversación/actividad; CU-18/19/27 IA/voz y consultas; CU-23 despliegue; CU-28 visor/push. El roadmap PUDS es la fuente única de orden y dependencias.

La conversación y actividad están separadas del modelo UML; referencia a proyecto/revisión no crea otra fuente semántica. La presencia efímera no equivale al historial persistido. La IA usa contexto compartido por sesión, no conversaciones privadas ni una instancia física exclusiva obligatoria. Mutaciones solo por solicitud autorizada, con revisión vigente, validación, persistencia y posterior broadcast.

## Salidas generadas independientes

CanonicalUmlModel → RelationalModel → backend Java 21/Spring Boot/PostgreSQL; OpenAPI/Postman/Manifest y CRUD Flutter/Dart Android. No confundir esa salida con el visor móvil informativo de la herramienta CASE, cuya tecnología todavía no está elegida.

## Límites

NoSQL ya usa MongoDB Atlas; IA cloud, cliente móvil y push se seleccionan cuando sus CUs lo necesitan. No se fijan nuevos contratos aquí. Offline/LAN conserva objetivo anterior con alcance de aceptación pendiente de contrastar con primer parcial. No se elimina código SQL hasta disponer de un reemplazo probado y recuperación verificada.

## Adaptación implementada en CU-25

La dependencia get_db_session selecciona SQL Session o MongoStore según PERSISTENCE_BACKEND (por defecto mongodb tras el corte verificado). Las funciones de almacenamiento conservan sus contratos y DTOs; MongoStore no abre sesiones SQL. Usuarios Mongo tienen email único normalizado y hash Argon2. La envoltura del documento Mongo guarda _memberships; la conversión canónica la excluye de UML/layout y de las respuestas.

El CAS Mongo comprueba actor owner/editor y revisión en la misma operación, además de identidad/creación inmutables. Modificar memberships no cambia la revisión UML. Las operaciones Mongo se confirman de forma atómica, mientras commit/rollback solo se aplican a SQL. No se duplica Command Bus ni se persiste su caché Undo/Redo. Los fallos invalidan el bus y se devuelven sin detalles de conexión. El cliente Mongo se reutiliza por proceso y cierra en lifespan.

Siete escenarios API sobre Atlas y regresión completa PASS; migración de 3 usuarios/15 proyectos/2 permisos y recuperación tras reinicio real PASS. SQL original se conserva intacto y respaldado, con 13 propietarios legacy sin cuenta asociada preservados. El adaptador SQL queda para origen/recuperación controlada, fuera del camino normal CASE. El resto de capacidades futuras de este documento sigue sin implementarse.


## CU-10: suscripción a estado persistido

HTTP conserva comandos/CAS; /projects/{UUID}/sync autentica con JWT en primer mensaje y verifica Origin. Snapshot inicial/recuperación y deltas de JSON canónico sobre baseRevision. Cada conexión consulta la autoridad cada 500 ms (más latencia), fuera del event loop, revalidando JWT/usuario/permisos; detecta escrituras de otros procesos sin broker. No difunde el bus no confirmado ni cambia UML por mensajes WebSocket. Revisiones intermedias pueden agruparse, no es historial de actividad. Consulta por conexión implica coste proporcional; carga/optimización no medidas. Undo/Redo sigue efímero por proceso.

Pinia aplica deltas atómicos, rechaza huecos y recupera snapshot, evita respuestas HTTP atrasadas y limpia suscripción al cambiar proyecto/sesión. Reconexión acotada, estado visible y edición bloqueada mientras no sincroniza. Pruebas locales y TCP MongoMock PASS; Atlas/visual pendientes, sin afirmar despliegue remoto.


## CU-11: presencia efímera

Negociación opt-in presence=true al autenticar WebSocket; mensajes presence separados de snapshot/patch. Colección Mongo presence (mismo prefijo aislado en tests), TTL expiresAt=0 y filtro por vigencia. UUID de conexión e identidad/rol/hora fijados por servidor. Lease quince segundos; desconexión/revocación elimina solo la sesión, TTL cubre fallos abruptos. Consulta de permisos excluye peers revocados aun antes del cleanup. Heartbeat no modifica ProjectDocument/revisión. No es un historial persistente ni bloqueo de edición.

Cliente agrupa controles a 2 Hz, servidor agrupa posiciones pendientes; controles de identidad falsos se rechazan. Avatares/rol/última actividad, estado de borrador, selección, cursor con pan/zoom y avisos temporales. SQL legacy no ofrece presencia distribuida. Cloud/visual diferidos; pruebas locales y TCP MongoMock aprobados.


## CU-26: ledger grupal y reservas recuperables

Una sesión por proyecto en Mongo sessions. Participantes conocidos y eventos message/activity separados de presencia y UML. Ledger embebido con versión CAS/secuencia, páginas de 50 y límite BSON 16 MiB; no se promete historial ilimitado. Reservas privadas _pendingMessage (permiso atómico) y _pendingActivity (misma escritura CAS del proyecto) se promueven idempotentemente y se limpian por ID. Tras fallo, la lectura recupera; no se reconstruyen autores históricos. Promoción tardía puede ordenar el evento después de su fecha original. IDs de actividad usan prefijo reservado separado de UUID de mensajes.

REST autorizado e intercambio conversation opt-in por WebSocket; texto escapado, identidad/hora de servidor, VIEWER consulta y EDITOR envía. Pinia mezcla páginas por ID/secuencia, retiene borrador/ID tras fallo y no modifica documento/revisión con mensajes. Nuevo cliente/reinicio recupera desde almacenamiento, sin historial de chat en el bus. Local/TCP MongoMock verificados; Atlas/visual diferidos por usuario; no hay IA integrada todavía.


## Funciones antiguas reanudadas

CU-21 importador XMI con iterparse acotado, sin DTD/red/entidades; valida el subconjunto canónico y crea proyecto nuevo autenticado. Round-trip semántico sin layout, avisos explícitos para contenido no representado. No se presume interoperabilidad EA real sin su evidencia.

CU-09 añade _invitations privado al documento Mongo (excluido de ProjectDocument), solo hash de secreto aleatorio, correo/rol/fechas. Canje y concesión de membership son una escritura atómica condicionada por vigencia/hash/email/rol; consumo/cancelación no cambia revisión UML. Se conserva API de membresías previa. Código solo en respuesta de creación/memoria de UI y body POST al canjear; sin email automático/localStorage. Invitaciones SQL legacy no añadidas; vía normal NoSQL. Gates locales y TCP MongoMock aprobados, QA visual/cloud pendiente.


## CU-13: proyección relacional

CanonicalUmlModel + GenerationProfile opcional de metadata.generation → RelationalMapper → RelationalModel validado. Sin layout/ownership ni segunda autoridad UML. Perfiles propios required/unique/indexed/PK/nombres/enums separados del modelo semántico. PK técnica UUID o atributo explícito, tipos en allow-list, FKs con tipos coincidentes, 1:1/1:N/N:M, composición acotada y JOINED de padre único. Nombres ASCII deterministas de <=63 bytes, colisiones/metadata inválida bloquean plan. Enums de perfil sobre texto no añaden Enumeration a UML.

GET /projects/{id}/relational-model aplica acceso de lectura y devuelve revisión fuente, modelo o diagnósticos sin mutar. Editor marca vista obsoleta y permite descargar JSON. Cardinalidades avanzadas se conservan como requisitos de runtime/avisos, no restricciones ejecutadas. No DDL/Java/Flutter en este CU; CU-14 deberá resolver/rechazar obligaciones antes de generar. Gates locales y TCP MongoMock PASS; QA visual/cloud diferida.

## CU-14: primera base de código generado

app/generation/spring.py recibe RelationalModel revalidado y SpringOptions restringidas. Devuelve fuentes en memoria con templates propios Jinja2/StrictUndefined, sin ejecución, escritura ni lectura de secretos; paquetes/identificadores/literales validados o escapados. Entidades JPA/repositorios/esquema PostgreSQL y configuración externa, con Hibernate validate y sin DDL automático. Rechaza relaciones/identidad compuesta hasta el incremento 2. Gradle/Java compilan el fixture aislado en artifacts, no durante solicitudes de la aplicación. API/UI de descarga aún pendientes.

### CU-14 incremento 2: capacidades generadas

El renderer añade DTOs/servicios transaccionales/controladores y consultas allow-listed mediante JPA Specification. PK técnica omitida en entrada; PK asignada immutable, persist crea sin merge. FK simples son IDs escalares con navegación bidireccional; SQL añade FK tras crear todas las tablas. ReadOnly/searchable/sortable se leen del perfil (false por defecto); solo PK ordenable por defecto. Sin código de negocio inferido. ORM/SQL/constraints probados en PostgreSQL temporal real; planes compuestos/herencia/composición/conteos se rechazan. Sin ejecución de código en generación de fuentes ni nueva API de descarga todavía.

## CU-18: preparación de interpretación cerrada

app/ai contiene contratos Pydantic, contexto acotado, resolver que valida comandos existentes sobre copia y transporte REST Gemini fijo. No se importa en rutas de producción todavía: no hay ejecución, consultas privadas ni cambios autónomos. La futura capa autorizada debe recuperar solo el proyecto/historial permitido y revalidar actor/revisión al persistir. Gemini usa clave backend en header, sin redirect/tools/retries; dataset y runner de evaluación separados. Proveedor/modelo candidato sin inferencia real ni métricas porque falta clave; Qwen local sigue opcional.

### CU-18: solicitudes grupales y persistencia de evaluación

Router AI integra el proveedor únicamente por petición de editor, sobre proyecto/revisión autorizados. Configuración SecretStr no llega al cliente. Events aiRequest/aiResult en sessions: actor humano/IA reservado, solicitud/revisión/estado/intent limitado, nunca copia UML ni comandos persistidos. Reserva privada _aiRequest y marcador _aiSeen en projects coordinan una llamada por ID y un trabajo simultáneo por proyecto; marcador y ledger cuentan para límites BSON. Promoción recuperable y lease interrumpida no vuelven a invocar el proveedor. JWT/cuenta/acceso/revisión se revalidan antes de publicar una propuesta vigente.

AiRequestPanel muestra disponibilidad sin simular conexión, envía revisión/ID, consulta resultado tras incertidumbre y mezcla eventos con el grupo; respuestas tardías de otro proyecto se descartan. CanApply siempre false, sin ruta ni botón de aplicación por texto. Código probado con proveedor controlado/MongoMock, sin llamada real o aceptación cloud todavía.
