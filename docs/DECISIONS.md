# Registro de decisiones

Las decisiones 004, 007, 016 y 017 describen la implementación SQL anterior: ADR-lite 022 reemplaza su destino de producto, sin afirmar que el código ya fue migrado. Las invariantes de dominio, revisión y permisos se conservan.

## ADR-lite 001 — Monorepo con dos proyectos base

**Estado:** aceptada

La fundación contiene `frontend/` y `backend/` en la raíz para mantener el repositorio simple y fácil de navegar.

## ADR-lite 002 — Vue permanece como frontend web

**Estado:** aceptada

Flutter no reemplaza Vue. Flutter permanece decidido para la salida móvil Android generada. ADR-lite 022 incorpora además un visor móvil CASE cuya tecnología no está elegida.

## ADR-lite 003 — Dependencias de IA diferidas

**Estado:** aceptada

No se instalan modelos/runtime pesados en la fundación. Se agregarán cuando exista un CU que los necesite.

## ADR-lite 004 — PostgreSQL local validado y Docker opcional

**Estado:** aceptada

El flujo de desarrollo validado usa PostgreSQL local de Windows en `localhost:5432/examen_sw1`. Docker Compose se conserva como alternativa reproducible y publica `localhost:55432` hacia el puerto `5432` del contenedor; no es requisito para desarrollar.

## ADR-lite 005 — Fuentes documentales de verdad

**Estado:** aceptada

`/product.md` es la fuente principal de requisitos y stack. `docs/puds/` es la fuente unica de roadmap y casos de uso; no se mantienen roadmaps alternativos.

## ADR-lite 006 — Command Bus antes del canvas mutable

**Estado:** aceptada

El Command Bus y Undo/Redo se implementan antes del canvas para que toda mutacion del editor use desde el inicio `UmlCommand -> UmlCommandBus -> UmlCommandExecutor -> ProjectDocument`.

## ADR-lite 007 — AWS diferido a su CU de despliegue

**Estado:** aceptada

AWS es un requisito de producto. La seleccion de servicios se difiere al CU de despliegue, que debe contemplar Vue, FastAPI, PostgreSQL, secretos externos y smoke tests sin reemplazar las capacidades locales/offline.

## ADR-lite 008 - Contrato de dominio ProjectDocument

**Estado:** aceptada

`ProjectDocument` es el contenedor central del dominio: UUID estable, metadata JSON-safe, `ownerId` estructural sin autenticacion, revision reservada para concurrencia optimista y timestamps timezone-aware. Pydantic 2 define validacion, serializacion con aliases publicos y rechazo de campos desconocidos.

`CanonicalUmlModel` es la unica fuente semantica. `DiagramLayout` se mantiene separado y solo referencia UUIDs de elementos existentes; no contiene semantica UML.

## ADR-lite 009 - Clases y miembros UML tipados

**Estado:** aceptada

CU-02 representa clases, atributos, operaciones y parametros con modelos Pydantic tipados y `kind` estable. La visibilidad usa `UmlVisibility`; tipos y nombres son strings semanticos no vacios. La ausencia de `returnType` se representa con `null`/`None`; los generadores futuros la mapearan al equivalente del lenguaje destino. Los UUID son globalmente unicos en `CanonicalUmlModel`; relaciones y validaciones entre clases se difieren a CUs posteriores.

## ADR-lite 010 - Relaciones UML semanticas top-level

**Estado:** aceptada

CU-03 amplia `CanonicalUmlModel.elements` con una union discriminada Pydantic por `kind` para clases, asociaciones, agregaciones, composiciones y generalizaciones. Las relaciones contienen UUID estable, `sourceId` y `targetId`; association, aggregation y composition requieren multiplicidades estructuradas explicitas (`lower >= 0`, `upper >= lower` o `"*"`). Association mantiene extremos neutrales. En aggregation y composition, `sourceId` es la clase todo/contenedor y `targetId` la parte/contenido; las multiplicidades homonimas corresponden a esos extremos. En generalization, `sourceId` es la clase hija y `targetId` la clase padre, sin multiplicidades.

La integridad de referencias se valida en el modelo canonico: ambos extremos deben identificar clases del mismo modelo, aunque se permiten autorrelaciones. La unicidad UUID es global entre clases, miembros y relaciones. El layout sigue separado y acepta solo UUIDs de clases, nunca relaciones.

## ADR-lite 011 - Diagnosticos para validacion UML semantica

**Estado:** aceptada

CU-04 separa la validacion semantica de las invariantes estructurales Pydantic. `validate_uml_model` no muta ni corrige el modelo y devuelve todos los `UmlDiagnostic` detectados, en vez de lanzar una excepcion por un error UML habitual. Los codigos y severidades son enums estables para permitir consumo posterior desde API y UI; `isValid` se calcula a partir de la ausencia de diagnosticos `error`.

Las comparaciones de nombres y tipos son exactas y case-sensitive. Para evitar ruido, cada regla de duplicados diagnostica cada ocurrencia posterior a la primera en orden canónico; el DFS de generalizaciones registra un diagnostico por arista de retorno detectada en orden de elementos. Las reglas de tipos, paquetes, herencia multiple y ownership se difieren.

## ADR-lite 012 - Command Bus con snapshots locales

**Estado:** aceptada

Todas las mutaciones UML futuras deben pasar por `UmlCommand -> UmlCommandBus -> UmlCommandExecutor -> ProjectDocument`; ninguna entrada modifica el documento directamente. Los comandos son modelos Pydantic discriminados por `commandType`, para permitir serializacion y reutilizacion posterior.

Undo/Redo usa snapshots completos inicialmente por simplicidad, correccion y facilidad de pruebas. El historial de undo tiene un limite fijo de 100 estados: al superar el limite se descarta el snapshot mas antiguo para evitar crecimiento indefinido de memoria y conservar los 100 mas recientes. `UmlCommandBus` encapsula su estado mediante copias profundas: ninguna referencia de documento o resultado entregada a un consumidor puede modificar el estado interno fuera de comandos. El executor tambien devuelve un documento independiente de sus entradas y comandos. `revision` es monotona incluso durante undo/redo y `updatedAt` se renueva sin retroceder; identidad, ownership y fecha de creacion se conservan. La validacion semantica no bloquea comandos estructuralmente validos.

## ADR-lite 013 - Canvas Vue conectado al Command Bus por sesiones HTTP temporales

**Estado:** reemplazada por ADR-lite 018

CU-06 mantiene una unica implementacion autoritativa de mutaciones UML en Python. El frontend Vue no replica `UmlCommandBus`, atomicidad, historial ni validaciones estructurales. En su lugar, usa un adaptador HTTP de sesiones efimeras en memoria: Vue envia `UmlCommand` serializados, FastAPI los ejecuta mediante el bus canonico y devuelve `ProjectDocument`, `canUndo` y `canRedo`.

La memoria del proceso no se considera persistencia y se pierde al reiniciar FastAPI. Esta decision fue temporal para CU-06 y se retiro en CU-07 Incremento 3.

## ADR-lite 014 - Vue Flow es proyeccion, no modelo de dominio

**Estado:** aceptada

CU-06 convierte `ProjectDocument` en nodes/edges mediante un mapper puro. Vue Flow no almacena una segunda version del UML ni decide reglas semanticas. Las posiciones fallback de clases sin `DiagramLayout` son deterministas pero transitorias. Hasta Incremento 3 los nodos no son arrastrables para evitar que una posicion visual aparente ser persistida sin pasar por `SetNodeLayoutCommand`.

El grid usa CSS y los controles llaman acciones de viewport de `@vue-flow/core`; no agregan logica de dominio ni nuevas dependencias.

## ADR-lite 015 - Edicion del canvas sin mutacion paralela

**Estado:** aceptada

Vue Flow puede mover visualmente un node durante el drag, pero el cambio real se confirma solo con `SetNodeLayoutCommand` en `node-drag-stop`. Toolbox e inspector construyen comandos publicos y esperan el nuevo `ProjectDocument` del backend. No existe historial, validacion estructural ni cascada de borrado duplicada en TypeScript.

El inspector conserva el `kind` de una relacion al actualizarla porque CU-05 rechaza `ELEMENT_KIND_MISMATCH`. Cambiar association/aggregation/composition/generalization requiere eliminar y volver a crear la relacion. Una clase con relaciones no se ofrece para borrado hasta retirar esas relaciones, coherente con el rechazo atomico del executor.

## ADR-lite 016 - ProjectDocument persistido como columnas tipadas y JSONB separado

**Estado:** aceptada

CU-07 persiste un unico `ProjectDocument` por fila en `projects`. Los metadatos de proyecto, revision, propiedad estructural e identidad/timestamps usan columnas tipadas; `CanonicalUmlModel` y `DiagramLayout` se guardan como `JSONB` separados. Esto conserva la forma JSON-safe Pydantic, evita dos fuentes de verdad y no adelanta tablas relacionales para elementos UML. Las lecturas deben revalidar el payload mediante `ProjectDocument.model_validate(...)`.

## ADR-lite 017 - Lock local y CAS para mutaciones persistentes

**Estado:** aceptada

CU-07 serializa execute, undo y redo por `projectId` con un lock process-local, porque `UmlCommandBus` mantiene estado mutable. PostgreSQL mantiene la autoridad entre procesos mediante `UPDATE ... WHERE id AND revision`. La cache process-local de buses solo conserva historial local y se invalida ante conflicto o error de persistencia; los snapshots no se guardan en PostgreSQL ni sobreviven un reinicio.

## ADR-lite 018 - Editor Vue conectado a proyectos persistentes

**Estado:** aceptada

El frontend usa `/projects` para listar, crear, abrir y mutar. El store Pinia adjunta `baseRevision` en cada comando, Undo y Redo, y reemplaza el documento local con la respuesta autoritativa. Un conflicto de revision recarga el documento y limpia los indicadores de historial. El bridge `/editor/sessions` de CU-06 fue eliminado al completar esta migracion.

## ADR-lite 019 - Admisibilidad de herencia en comandos

**Estado:** aceptada

Los diagnosticos UML permanecen separados de las invariantes estructurales y no bloquean comandos de forma general. Sin embargo, una generalization autoreferenciada o ciclica nunca es un estado admisible del editor. El executor construye el modelo candidato y consulta una funcion pura del dominio que reutiliza las reglas de validacion existentes para detectar exclusivamente `GENERALIZATION_SELF_REFERENCE` y `GENERALIZATION_CYCLE`; ante una de ellas rechaza el comando antes de modificar snapshots, revision o persistencia.

Las autorrelaciones de association, aggregation y composition se mantienen permitidas: describen una relacion entre instancias de un mismo classifier y no implican que una instancia se contenga a si misma. Dependency, Realization, roles de extremo, navegabilidad y asociaciones n-arias siguen fuera del dominio actual.

## ADR-lite 020 - Edges UML derivados y self-loops visuales

**Estado:** aceptada

Vue Flow sigue siendo una proyeccion de `ProjectDocument`. Un edge reutilizable recibe datos derivados por `projectDocumentToFlow()` para renderizar los markers UML existentes, labels de multiplicidad por extremo y una curva lateral para self-loops. Usa el hitbox y eventos nativos de `BaseEdge`, por lo que la seleccion sigue la misma ruta Vue Flow -> `selectedElementId` -> inspector.

Los self-loops se excluyen solamente del grafo de `d3-dag`; no se eliminan ni se persisten datos visuales adicionales. Las relaciones paralelas reciben una desviacion Bezier derivada minima para no quedar completamente superpuestas. No se agregan tipos UML, roles, navegabilidad ni routing avanzado.

## ADR-lite 021 - JWT local y ownership sin FK legacy

**Estado:** aceptada

CU-08 usa PyJWT Bearer configurable y `pwdlib`/Argon2. El MVP mantiene JWT en `localStorage`, centraliza el header y limpia 401. Los nuevos proyectos usan `current_user.id`; no se fuerza FK para UUID temporales de CU-07. La migracion es aditiva y CU-09 agregara colaboradores.

## ADR-lite 022 - Base del segundo parcial

**Estado:** requisitos aceptados por el usuario el 2026-11-06; implementación pendiente.

Se incorpora product.md sección 41 y trazabilidad SECOND-PARTIAL. El destino de persistencia CASE cambia de PostgreSQL a NoSQL cloud. Motor/proveedor/SDK y migración se deciden en CU-25 preservando usuarios, propiedad, memberships, documento/revisión y recuperación. PostgreSQL/SQLAlchemy actuales continúan hasta reemplazo probado; JSONB no acredita NoSQL.

Se mantienen Vue/FastAPI y arquitectura canónica. IA cloud grupal con contexto lógico compartido por sesión y acciones solo por solicitud; local opcional. Sesión/conversación/actividad persistidas y visor móvil informativo con push se añaden al alcance. Proveedores/modelos y tecnología móvil quedan para sus CUs.

No se elimina generación Spring Boot/PostgreSQL ni CRUD Flutter; no cubren por sí mismos el visor móvil. Offline/LAN conserva objetivo anterior pendiente RP-01. Mutaciones textuales y NoSQL para aplicaciones generadas requieren aclaraciones RP-02/RP-03. No se borra ni migra ningún dato con esta decisión documental.

## ADR-lite 023 - CU-25: MongoDB Atlas sobre AWS y PyMongo

**Estado:** seleccionada el 2026-11-06; prueba y migración completadas después en CU-25. Los párrafos siguientes registran el contexto inicial; ADR-lite 025 registra el corte.

Se elige MongoDB Atlas sobre AWS y PyMongo 4.19.0. Se conserva un documento por ProjectDocument, semántica y layout separados, UUID como string y fechas ISO UTC para conservar microsegundos. La mutación compara _id, revisión, ownerId y createdAt, actualiza campos mutables sin upsert y exige escrituras reconocidas. Se configura primary/majority y timeouts acotados para la prueba.

Comparación y razonamiento: MongoDB ofrece atomicidad de una escritura sobre un documento y permite incluir la revisión esperada en el filtro. Esto encaja con el documento canónico existente. DynamoDB también admite escrituras condicionales, pero su máximo de 400 KB por ítem exigiría limitar o dividir antes el documento UML. MongoDB admite 16 MiB BSON; se rechaza exceso antes de escribir y se registra ese límite, sin prometer tamaño ilimitado. Se evita introducir sharding/chunking en este CU.

Atlas puede hospedar clusters en AWS. No se ha creado ni contratado cluster y no se fija costo: cuenta, región, tier, respaldo y permisos deben verificarse antes de probar cloud. La prueba usa una base explícita *_cu25_probe, credencial externa y solo un UUID generado; nunca elimina colecciones ni bases. No hay credenciales Mongo configuradas en el entorno inspeccionado. El código actual sigue en PostgreSQL.

Antes de producción se deben completar usuarios, índice único de email normalizado, memberships únicas por proyecto/usuario, consultas autorizadas y su coherencia al revocar permisos, CAS entre procesos, respaldo/importación y recuperación. No se conectará únicamente proyectos Mongo a auth SQL como si eso completara NoSQL CASE.

Fuentes oficiales consultadas el 2026-11-06:

- [Atomicidad MongoDB y filtro con valor esperado](https://www.mongodb.com/docs/v8.0/core/write-operations-atomicity/).
- [Límite BSON MongoDB](https://www.mongodb.com/docs/manual/reference/limits/).
- [Atlas sobre AWS](https://www.mongodb.com/docs/atlas/reference/amazon-aws/).
- [Escrituras condicionales DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/read-write-operations.html).
- [Máximo de ítem DynamoDB](https://docs.aws.amazon.com/amazondynamodb/latest/developerguide/Constraints.html).
- [Driver oficial y versión seleccionada](https://pypi.org/project/pymongo/4.19.0/).

Las ventajas de ajuste arquitectónico son una decisión de diseño, no un benchmark de rendimiento ni garantía de exactitud antes de una corrida real.

## ADR-lite 024 - CU-25: adaptar persistencia sin cambiar contratos HTTP

**Estado:** implementada en incremento 2; ver CU-25 para gate y evidencia.

PERSISTENCE_BACKEND elige postgresql o mongodb; durante el incremento 2 el valor por defecto seguía siendo SQL. ADR-lite 025 registra el cambio a MongoDB. get_db_session entrega Session SQL o MongoStore, y las funciones existentes de usuarios/proyectos/memberships despachan al adaptador. Se conservan DTOs y rutas; los records ORM se usan como forma de compatibilidad en los límites, sin sesiones SQL para escrituras Mongo. No se replica el dominio ni el Command Bus en frontend.

Mongo conserva usuarios con índice único de email normalizado y hashes Argon2. Un documento canónico por proyecto más un mapa privado _memberships en la envoltura de almacenamiento; este mapa no se entrega como UML/DiagramLayout ni aparece en respuestas ProjectDocument. El mapa garantiza una membership por UUID sin transacción entre documentos. La actualización de comandos/Undo/Redo compara revisión, identidad y permiso actual de owner/editor en una sola escritura Mongo. Si un editor pierde acceso después de la lectura inicial, la condición impide guardar.

Las operaciones Mongo persisten de forma atómica y reconocida; commit_sql_session/rollback_sql_session solo aplican al camino SQL. Se invalidan buses locales ante conflictos/fallos, se conserva Undo/Redo efímero y la semántica de exportación XMI. PyMongoError se devuelve como 503 sin detalles/credenciales; exceso BSON como 413. La conexión se reutiliza por proceso y se cierra al terminar la aplicación. Health refleja el backend seleccionado.

No se retiraron SQLAlchemy/Alembic ni se cambiaron datos SQL. Se retienen para reversión y origen de datos hasta resolver el corte. En ese incremento aún estaba pendiente confirmar la conservación; el usuario la confirmó antes del incremento 3 (ADR-lite 025). MongoMock 4.3.0 es dependencia solo de desarrollo para pruebas sin red; la evidencia Atlas se ejecuta aparte sobre colecciones UUID en la base de pruebas y las elimina al terminar.


## ADR-lite 025 - CU-25: corte verificado y conservación de datos

**Estado:** implementada y verificada el 2026-11-06, por autorización del usuario de conservar y trasladar los datos existentes.

MongoDB pasa a ser el valor por defecto. Snapshot SQL repetible de solo lectura y pg_dump 17.6 conservados en artifacts/cu25, excluidos de Git. Archivo SQL restaurado en una base temporal y comparado íntegramente; base temporal retirada. Importación sin sobrescritura, validación previa de conflictos e idempotencia ensayadas en colecciones aisladas. Se trasladaron 3 usuarios, 15 proyectos y 2 permisos, preservando hashes, IDs, revisiones, timestamps, UML y layout. Trece proyectos ya tenían ownerId sin cuenta: se preservan sin atribución ficticia.

Verificación con proceso nuevo, API real y reinicio completo PASS; originales SQL sin cambios y datos temporales limpiados. Undo anterior sigue efímero; comandos nuevos/Undo/Redo funcionan tras reinicio. Regresión: 235 backend y 46 frontend, estático/build PASS. Evidencia detallada en CU-25.

SQL se conserva para respaldo/recuperación; cambiar el selector después de nuevas escrituras Mongo exige congelar y reconciliar los cambios. Usuario Atlas limitado una semana e IP /32 seis horas son temporales y requieren renovación para operación duradera. No se habilitó acceso global ni un tier pago. La recuperación comprobada no sustituye una política de backups cloud de producción.


## ADR-lite 026 - CU-10: deltas de estado persistido por WebSocket

**Estado:** implementada, aceptación cloud/visual pendiente (2026-11-07).

Se reutilizan HTTP/Command Bus/CAS para mutaciones y se añade suscripción WebSocket FastAPI/navegador. Snapshot inicial/recuperación, deltas estructurales canónicos sobre revisión esperada y flags/rol. Los contratos HTTP existentes mantienen su respuesta de estado; la difusión a participantes no envía un ProjectDocument completo en cada cambio. El token viaja en primer mensaje, nunca URL; se valida Origin y se revalidan usuario/permisos/token en cada lectura.

Se consulta persistencia por conexión cada 500 ms más latencia, en threadpool. Frente a difusión exclusivamente en memoria, detecta cambios externos al worker y no anuncia un estado no confirmado; frente a broker/change streams, evita introducir infraestructura o requisitos de cluster en este CU. La decisión admite agrupación de revisiones y coste de lectura por conexión/documento; no sirve como registro de actividad ni acredita alta escala. No se midió benchmark de carga. Optimización requiere evidencia y se mantiene separada de presencia y conversación de CUs futuros.

Cliente publica una proyección solo al aplicar todo el delta, recupera snapshot ante huecos y elimina suscripciones al cambiar de proyecto/sesión. Las revisiones HTTP atrasadas no reemplazan estados nuevos. Gate local 242 backend/55 frontend y TCP MongoMock PASS; Atlas y prueba visual aún pendientes. No se ha probado despliegue multiworker ni se alteró persistencia efímera de Undo/Redo.
