# CU-14 — Generar backend Spring Boot

**Estado: PENDIENTE DE REANUDACIÓN.** Desde 2026-11-07, el usuario prioriza el segundo parcial; CU-18 es el único CU activo. Incrementos 1/2 preservados, incremento 3 pendiente. Inicio: 2026-11-07. Dependencia CU-13 implementada; aceptación visual/cloud de casos anteriores diferida por el usuario.

## Objetivo, actores y referencias

Generar un backend Java 21/Spring Boot 4.x compilable a partir del modelo/metadatos, usando Jinja2. Actor: participante autorizado que solicita generación. Referencias: product.md secciones 21..25, 33..34 y 41. La persistencia PostgreSQL de la salida generada es independiente de MongoDB Atlas de la herramienta CASE.

## Alcance y precondiciones

Reutilizar RelationalModel y su mapper, sin usar el canvas ni deducir negocio de métodos UML. Rechazar explícitamente modelos o restricciones aún no soportados; nunca emitir una aplicación parcial como si estuviera completa. No incluye Postman/Domain Manifest/cliente Flutter (CU-15/16), IA ni despliegue. La instalación de springdoc en el proyecto generado pertenece a su stack; la derivación de artefactos OpenAPI corresponde a CU-15.

## Plan autorizado: máximo tres incrementos

El usuario autorizó continuar con el generador y sus pruebas/documentación en el chat; no se solicita de nuevo aprobación de trabajo rutinario dentro de este alcance.

1. **Base compilable y persistencia escalar:** render determinista en memoria con Jinja2, configuración validada, proyecto Gradle/Java 21, entidades y repositorios, esquema PostgreSQL con constraints/índices, validación de enums, instrucciones de operación y pruebas. Rechazar relaciones y obligaciones de runtime hasta el incremento siguiente. Compilar una salida real.
2. **Capacidades y relaciones:** CRUD/consulta/paginación/orden/filtros/búsqueda/count y navegación según metadatos soportados, DTOs/servicios/errores, relaciones/identidades y estrategia documentada para restricciones. Pruebas de ejecución; rechazar los planes no soportados.
3. **Entrega autorizada y verificación:** descarga desde un proyecto con revisión identificable, acceso y errores, integración necesaria de interfaz, compilación/regresión y documentación reproducible. La orquestación integral de aplicaciones sigue siendo CU-17.

## Incremento 1 — DONE

Render puro generate_spring_sources(RelationalModel, SpringOptions) devuelve rutas relativas POSIX y fuentes ordenadas; no escribe ni ejecuta contenido. Jinja2 con StrictUndefined y templates propios, incluidos en el paquete Python. Revalida modelos/configuración mutables, restringe paquetes y nombres de artefactos, deriva símbolos Java con prefijo/sufijo estable, escapa literales Java/SQL y rechaza NUL/surrogates en valores PostgreSQL. No incorpora credenciales o metadatos CASE en las fuentes.

Genera Gradle/Java 21/Spring Boot 4.1.2, aplicación, entidades JPA con los diez tipos SQL soportados, repositorios, validación Jakarta de required/enums, esquema PostgreSQL con PK/UNIQUE/CHECK/índices y guía de operación con variables externas. Hibernate valida el esquema; no modifica bases al arrancar. El SQL se aplica manualmente a una base nueva, sin DROP ni migraciones implícitas. Enum permite null solo cuando el perfil lo permite. Identidad técnica UUID usa GenerationType.UUID; identidad explícita no recibe un generador inventado.

Este incremento rechaza relaciones/FKs/identidades compuestas, también si requieren validación de runtime: no entrega una estructura parcial. No contiene CRUD, rutas de negocio, auditoría, editor de perfil ni descarga desde la aplicación. No incluye wrapper binario; la guía requiere Gradle 9.5.1 y explica generar el wrapper estándar. No hay autenticación generada ni se confunden los permisos CASE con autorización del dominio generado. No se deduce negocio a partir de operaciones UML.

### Verificaciones reales

| Comprobación | Resultado |
| --- | --- |
| 25 pruebas específicas de renderer/configuración | PASS; determinismo/inmutabilidad/tipos/PK/constraints/enum/escapado/rutas/reservados y rechazos explícitos |
| scripts/check.ps1 | PASS: 336 backend / 86 frontend en 20 archivos, compileall/Ruff/pip check/typecheck/build |
| Gradle 9.5.1, Java Temurin 21.0.12.1+1 | BUILD SUCCESSFUL; compileJava/bootJar/compileTestJava/test/build, 7 tareas ejecutadas |
| JUnit ejecutado sobre entidad generada | 1 test, 0 fallos/errores: validación real Jakarta, enum con comillas/apóstrofo/backslash/nueva línea, null obligatorio y UUID generado |
| Paquete wheel construido e inspeccionado | PASS: las 11 plantillas Jinja están incluidas; JAR contiene Boot/Hibernate/Jackson/PostgreSQL/springdoc |
| SQL aplicado / arranque PostgreSQL / CRUD | No ejecutados todavía; obligatorios al desarrollar capacidades de ejecución del incremento 2 |

Recibo local ignorado: artifacts/cu14/foundation-result.json. Proyecto de prueba aislado: artifacts/cu14/0f34c34c-2800-4d86-8717-b9e06b137937. JUnit: build/test-results/test/TEST-com.example.generated.FoundationContractTest.xml dentro de esa salida. Fecha: 2026-11-07, America/La_Paz. Gate backend: 94 warnings externos (92 MongoMock TTL y 2 previos); advertencia de chunk Vite existente. No benchmark IA aplicable.

### Reproducción

Desde backend ejecutar `.\.venv\Scripts\python.exe -m tests.manual.spring_foundation_probe`; imprime una nueva carpeta aislada. Con Java 21 y Gradle 9.5.1 ejecutar `gradle -p "<carpeta impresa>" --no-daemon --console=plain build`. La primera compilación descarga dependencias oficiales. El probe no accede a bases de datos. Conserva el fixture y su JUnit para inspección; no escribe dentro de proyectos reales.

### Correcciones y límites

Se ajustó el delimitador de una anotación de array Jinja antes de las pruebas. La primera comprobación de wheel con --no-build-isolation falló porque setuptools solo estaba disponible en el entorno de construcción aislado; se repitió con el aislamiento estándar y pasó. No fue necesario cambiar el stack ni instalar Gradle adicional. La demostración local sigue sin botón de generación hasta el incremento 3. No se reinició su servidor ni se modificaron datos reales.

## Incremento 2 — DONE

El renderer ahora genera DTOs de entrada/respuesta, servicios transaccionales, controladores REST y un componente común de consultas sobre Specification/JpaSpecificationExecutor. Las fuentes siguen derivándose de RelationalModel y del perfil explícito; no se interpretan métodos UML como negocio. La salida CASE normal sigue siendo FastAPI/MongoDB; PostgreSQL pertenece exclusivamente a la aplicación generada.

### Contrato generado y metadatos

Por tabla, GET /api/{tabla} lista y GET /count cuenta; GET/PUT/DELETE /item reciben id por query para admitir identificadores de texto con caracteres reservados. POST en la base crea con 201; DELETE devuelve 204, ausencia 404, solicitud inválida 400 y conflicto de constraints 409 sin exponer SQL. PUT reemplaza atributos mutables; los opcionales omitidos pasan a null. Una PK asignada debe coincidir con el id de query. Una PK UUID generada no forma parte del DTO de entrada. create utiliza EntityManager.persist/flush, evitando que una identidad asignada se interprete como merge y sobrescriba datos existentes.

El perfil metadata.generation conserva version=1 y añade classes[UUID].readOnly y attributes[UUID].searchable/sortable, todos false por defecto. El mapper conserva el significado relacional anterior; el renderer recibe el mismo perfil para decidir capacidades. readOnly omite POST/PUT/DELETE. Búsqueda solo sobre texto declarado searchable; ordenar solo por atributos declarados sortable o PK. UUID/PK es el desempate estable. Referencias obsoletas, searchable sobre no-texto y configuración inválida se rechazan. No se infieren capacidades a partir del nombre o de la visibilidad de un atributo.

Lista/count admiten page=0..1000000, size=1..100, sort, direction=asc/desc, filter.COLUMNA=valor tipado (igualdad AND) y q (substring literal OR entre atributos habilitados). Máximo 20 parámetros y 512 caracteres por valor; se rechazan duplicados/desconocidos y valores inválidos/no finitos en filtros numéricos. NUL se rechaza en textos de entrada, identidad, filtro y búsqueda porque PostgreSQL no puede almacenarlo. No hay rutas arbitrarias de propiedades, SQL del cliente ni orden libre no declarado. El README generado contiene tablas de propiedades y contratos reales; no sustituye OpenAPI/Postman/Manifest de CU-15.

### Relaciones y restricciones

FK simple a PK simple, 1:1 y 1:N con scalar reference IDs y navegación en ambos sentidos: /references/{nombreFK}?id=... y /related/{nombreFK}?id=..., esta última paginada/filtrable. Referencia opcional no establecida devuelve 204. No hay escrituras de objetos anidados ni cascadas implícitas. Autorrelaciones soportadas sin dependencias circulares entre servicios. El esquema crea todas las tablas antes de añadir las FK, respetando NOT NULL/UNIQUE/RESTRICT y los tipos originales. Se conserva el rechazo de planes con reglas de runtime no ejecutadas.

**Límites explícitos:** N:M/PK compuesta, JOINED/herencia, composición, cardinalidades con conteos entre objetos y otros planes marcados requiresRuntimeValidation se rechazan antes de devolver fuentes. No se anuncian como implementados. Máximo 200 columnas por tabla y 200 tipos de entidad relacionados por controlador para respetar límites de parámetros Java. Auditoría/custom business logic y política de autorización del dominio generado no están implementadas. La salida se verifica solo en desarrollo controlado; los permisos CASE no se transfieren a su API de negocio.

### Pruebas reales y correcciones

Seis pruebas Python nuevas verifican esquema/navegación, metadatos readOnly/searchable/sortable, DTO sin UUID generado, persist sin merge, rechazo de perfiles/capacidad no válida, límites Java y errores sin detalles SQL. Más las 25 anteriores: 31 específicas PASS. La primera compilación CRUD y un JUnit de validación generado también pasaron; no equivalían a aceptación de ejecución.

La primera prueba PostgreSQL detectó PropertyReferenceException: el guion bajo en símbolos Java era interpretado por Spring Data como separador de propiedad al ordenar. Se corrigió el identificador Java para concatenar un sufijo hash sin guion bajo y se añadió regresión; los nombres SQL no cambiaron. La disponibilidad se consulta por count y el recorrido comprueba explícitamente listado/orden. Un error de longitud Ruff se resolvió formateando el código. Se repitió el recorrido completo, no se ocultó el fallo anterior.

Prueba HTTP/JVM/PostgreSQL final **PASS: 51 comprobaciones**, 2026-11-07 16:01:50 Bolivia: esquema aplicado, alta/lectura/reemplazo/borrado, identidad de texto con caracteres reservados, duplicado sin sobrescritura, UNIQUE/NOT NULL/enums/NUL, filtros/búsqueda literal/orden/paginación/count, FK válida/inexistente y delete RESTRICT, 1:1 única/opcional, 1:N y autorrelación en ambas direcciones, solo lectura y recuperación después de reiniciar la JVM. PostgreSQL 17.6 local; base cu14_UUID creada aparte y eliminada en finally tras detener el servidor propio. No se conectó al contenido de la base legacy ni se modificó Atlas. Recibo ignorado artifacts/cu14/crud-result.json; logs/fuentes preservados en artifacts/cu14/crud-4594213524d947b3ac6e39a3db1e8d60.

Reproducción desde backend: `.\.venv\Scripts\python.exe -m tests.manual.spring_crud_probe`. Requiere Java 21, Gradle 9.5.1 en caché y PostgreSQL local con permiso para crear una base temporal; lee las credenciales existentes sin mostrarlas ni copiarlas a la salida. Solo crea/retira el nombre temporal validado, nunca reutiliza examen_sw1. No utiliza Atlas ni el servidor de QA de la interfaz. Las 17 plantillas están verificadas dentro del wheel.

Gate completo final scripts/check.ps1 **PASS: 342 backend / 86 frontend en 20 archivos**, compileall/Ruff/pip check/typecheck/build PASS. 94 warnings backend externos (92 MongoMock TTL y 2 previos); aviso de tamaño de chunk Vite existente. CU-14 sigue IN PROGRESS hasta el incremento 3 y su evidencia; la descarga/UI aún no existen. No se reinició la demostración local ni se modificaron sus datos temporales.

## Diseño inicial y versiones verificadas

Java 21 ya está instalado. Gradle 9.5.1 está disponible en la caché local. Se comprobaron HTTP 200 de los artefactos oficiales de Spring Boot 4.1.2 y springdoc 3.2.0 en Maven Central. No se cambia el stack aprobado. Dependencia Python Jinja2 3.1.6, con templates propios empaquetados; ningún template ni código ejecutable procede del usuario.

Fuentes primarias: [Spring Boot](https://docs.spring.io/spring-boot/system-requirements.html), [compatibilidad springdoc](https://springdoc.org/#what-is-the-compatibility-matrix-of-springdoc-openapi-with-spring-boot), [Gradle Wrapper](https://docs.gradle.org/current/userguide/gradle_wrapper.html), [Jinja 3.1.6](https://jinja.palletsprojects.com/en/stable/changes/#version-3-1-6). Consulta 2026-11-07. Las versiones resueltas y resultados reales se registran por incremento.

## Pruebas, evidencia y pendientes

Incrementos 1 y 2 verificados según evidencia anterior. Pendiente: entrega por proyecto/revisión y UI del incremento 3. Los límites de relaciones no soportadas quedan explícitos y deben mostrarse como errores, sin generar proyectos incompletos. Se preservan las deudas anteriores Atlas/EA/visual y las aclaraciones RP-01..03. No se modifica product.md ni se ejecutan commits/push automáticos. El CU no está cerrado; no se entregan comandos de commit de cierre todavía.
