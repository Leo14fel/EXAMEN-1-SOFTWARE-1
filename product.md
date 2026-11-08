# Documento de producto — Variante 2

> Herramienta CASE colaborativa en la nube, para modelado UML de clases, generación automática de aplicaciones y operación mediante interfaz, lenguaje natural y voz.

## 1. Estado inicial y uso de este documento

Este documento define requisitos y decisiones de producto. El estado real vive en `docs/STATUS.md` y los documentos de CU.

La sección 41 incorpora los requisitos del segundo parcial aportados por el usuario. La herramienta CASE evoluciona a NoSQL en la nube; PostgreSQL se conserva para las aplicaciones generadas. No se elimina ninguna capacidad anterior sin contrastar el enunciado del primer parcial.

No contiene:
- estados de avance;
- casos de uso cerrados;
- referencias a iteraciones anteriores;
- decisiones heredadas de otro proyecto;
- rutas concretas de API;
- cuerpos concretos de solicitudes o respuestas;
- nombres de una aplicación;
- ejemplos de contratos que obliguen a copiar una API existente.

La IA de desarrollo deberá tomar este documento y:

1. derivar los casos de uso;
2. agruparlos en ciclos;
3. proponer criterios de aceptación;
4. implementar un caso de uso por vez;
5. mantener un documento de estado real independiente;
6. preservar este archivo como visión estable de producto.

---

## 2. Visión

La aplicación será una herramienta CASE colaborativa para diseñar diagramas de clases UML, mantener un modelo canónico versionado y transformar ese modelo en una aplicación funcional.

La solución deberá producir:

- backend ejecutable;
- persistencia relacional;
- API REST;
- especificación OpenAPI;
- colección Postman derivada de OpenAPI;
- frontend;
- salida Android;
- Domain Manifest;
- asistente de texto;
- asistente de voz.

El objetivo previo de capacidades esenciales sin Internet se conserva con el tratamiento y la aclaración del primer parcial establecidos en la sección 19; no sustituye los requisitos cloud del segundo parcial.

---

## 3. Principio arquitectónico

Todas las entradas convergerán a una única representación:

```text
Edición manual ────────────┐
Imagen ────────────────────┤
Voz + STT + IA ────────────┼──► CanonicalUmlModel
XMI / herramienta externa ─┘
```

Las salidas partirán de la misma fuente:

```text
CanonicalUmlModel
       │
       ├──► Canvas
       ├──► XMI
       ├──► RelationalModel
       ├──► Backend generado
       ├──► OpenAPI
       ├──► Postman
       ├──► Frontend generado
       └──► Domain Manifest
```

El canvas nunca será la fuente de verdad.

---

## 4. Stack decidido de la aplicación principal

### Frontend web

- Vue 3 + TypeScript + Vite
- Vuetify 3
- @vue-flow/core
- d3-dag
- Pinia
- WebSocket nativo del navegador

### Backend

- Python 3.13+
- FastAPI
- MongoDB Atlas sobre AWS + PyMongo 4.19.0 para persistencia NoSQL cloud
- WebSockets de FastAPI
- PyJWT + pwdlib con Argon2
- Pydantic 2

### XML / interoperabilidad / generación

- XMI 2.1
- Enterprise Architect como herramienta objetivo de interoperabilidad
- lxml con iterparse
- Jinja2
- springdoc-openapi para el OpenAPI del backend Spring Boot generado

### IA, visión y voz

- runtime local: Hugging Face Transformers + PyTorch
- texto: proveedor cloud por decidir en CU-18; Qwen3 1.7B local opcional
- visión: Qwen2.5-VL 3B Instruct local para imagen → UML
- STT: faster-whisper sobre CTranslate2
- preprocesamiento de imagen: Pillow + scikit-image

### Criterio de la variante

Esta variante prioriza productividad y tipado de datos con Pydantic. La integración de IA se mantiene en Python y debe admitir un proveedor cloud; la inferencia local es opcional.

---

## 5. Aplicación principal

La aplicación principal será web.

Debe incluir:

- landing pública;
- registro e inicio de sesión;
- listado de proyectos;
- creación y apertura de proyectos;
- workspace de diagramación;
- inspector;
- validación;
- Undo/Redo;
- colaboración;
- presencia;
- asistente;
- generación;
- importación/exportación.

La UI deberá ser responsive.

La aplicación principal será una aplicación web implementada con Vue 3 + TypeScript.

Flutter no reemplaza el frontend web principal.

La tecnología Flutter permanece decidida para la salida móvil Android generada por la herramienta. Deben distinguirse estos dos conceptos de generación del visor CASE descrito en 5.0:

frontend web principal de la herramienta CASE: Vue 3 + TypeScript;
aplicación móvil generada: Flutter + Dart para Android.

La aplicación móvil consumirá la API REST generada a partir del modelo y deberá conservar las capacidades CRUD, relaciones, búsqueda, filtros y asistente que correspondan al modelo generado.
---

## 5.0. Visor móvil colaborativo

Además de la aplicación CRUD generada, existirá un cliente móvil de la herramienta CASE para consultar el diagrama en tiempo real y recibir notificaciones push. Será de solo lectura respecto del UML y respetará los permisos del proyecto. Su tecnología y servicio push se decidirán en CU-28; no se presume que generar un CRUD Flutter cubre este requisito.

## 5.1. Identidad visual e interfaz obligatoria

La interfaz deberá sentirse como un **dashboard moderno y visual**, con mayor uso de color, superficies elevadas y composición mediante cards.

### Tema

- modo oscuro por defecto;
- fondo azul petróleo/gris oscuro;
- superficies ligeramente más claras;
- acentos turquesa y violeta;
- gradientes sutiles únicamente en áreas de énfasis;
- cards con contraste claro respecto del fondo;
- bordes redondeados notorios;
- sombras moderadas;
- densidad media.

### Tipografía e iconografía

- tipografía principal: Manrope;
- iconografía: Material Design Icons;
- encabezados con mayor peso visual;
- labels y metadata en tamaños pequeños.

### Distribución principal

```text
┌────────┬─────────────────────────────────────────────────────┐
│ Rail   │ Top controls / project context / collaborators     │
│        ├─────────────────────────────────────────────────────┤
│        │                                                     │
│        │      Canvas dentro de superficie elevada            │
│        │                                                     │
│        ├──────────────────────┬──────────────────────────────┤
│        │ Context cards        │ Assistant / diagnostics      │
└────────┴──────────────────────┴──────────────────────────────┘
```

### Navegación

Se utilizará un navigation rail estrecho con iconos y labels cortos.

Las secciones principales serán:

- proyectos;
- editor;
- generación;
- importación/exportación;
- historial;
- configuración.

La navegación no debe parecer una sidebar empresarial tradicional.

### Workspace UML

El canvas estará contenido dentro de una gran card central con padding visible respecto al resto de la interfaz.

Las clases UML utilizarán:

- encabezados coloreados por tipo o estereotipo;
- cuerpo oscuro;
- divisores de baja intensidad;
- selección con glow o halo discreto;
- badges para metadatos;
- relaciones con contraste alto.

El canvas usará grid de puntos.

### Toolbox

La toolbox será flotante y horizontal o vertical según el espacio.

Debe utilizar botones redondeados con:

- icono;
- tooltip;
- estado activo;
- agrupación visual por tipo de herramienta.

### Inspector

El inspector no será un panel permanente rígido.

Se mostrará mediante:

- cards contextuales;
- drawer cuando se requiera edición extensa;
- formularios divididos por secciones plegables.

### Asistente IA

El asistente ocupará una card dedicada dentro del workspace.

El diseño será más visual:

- mensajes en burbujas;
- transcripción de voz visible;
- intención detectada como chip/card;
- pasos del plan en timeline;
- botón principal para aplicar.

### Colaboración

La presencia utilizará:

- avatares apilados;
- pequeños indicadores de color;
- activity feed compacto;
- cursores remotos;
- mensaje temporal cuando alguien entra o sale.

### Errores y validación

Los diagnósticos aparecerán en una card inferior:

- filtros por severidad;
- chips;
- contador por categoría;
- click para enfocar el elemento;
- toast para errores generales.

### Responsive

En tablet y móvil:

- navigation rail → bottom navigation;
- cards se apilan verticalmente;
- inspector → fullscreen dialog;
- toolbox → floating action menu;
- asistente → panel deslizable inferior.

### Landing y autenticación

La landing debe parecer una aplicación SaaS moderna:

- hero oscuro;
- gradientes discretos;
- tarjetas de capacidades;
- secciones alternadas;
- CTA destacado.

Autenticación mediante card oscura centrada con ilustración abstracta o patrón geométrico suave.

## 6. Modelo de proyecto

Cada proyecto se representará mediante:

```text
ProjectDocument
├── UmlModel
└── DiagramLayout
```

`UmlModel` contendrá semántica.

`DiagramLayout` contendrá posiciones y otros datos visuales.

El documento tendrá:

- UUID;
- metadatos;
- propietario;
- revisión;
- timestamps;
- contenido UML;
- layout.

Se utilizará revisión optimista.

---

## 7. Dominio UML

Se tomará UML 2.5.1 como referencia concreta.

El modelo deberá soportar al menos:

- Class;
- Attribute/Property;
- Operation cuando corresponda;
- Visibility;
- tipos de datos;
- Association;
- Aggregation;
- Composition;
- Generalization;
- Multiplicity;
- Enumeration;
- Package cuando sea necesario;
- metadatos de generación.

Se distinguirán claramente los elementos UML puros de los metadatos propios del generador.

---

## 8. Canvas UML

El canvas se implementará con **@vue-flow/core**.

Auto-layout inicial: **d3-dag**.

Debe soportar:

- nodos de clase custom;
- atributos visibles;
- relaciones con estilos UML;
- labels de multiplicidad;
- zoom;
- pan;
- selección;
- movimiento;
- creación de relaciones;
- edición por inspector;
- ajuste a contenido.

El canvas proyectará `ProjectDocument`.

Los datos internos de la librería gráfica no se persistirán como dominio.

---

## 9. Diagramación manual

El usuario podrá:

- crear clases;
- editar clases;
- eliminar clases;
- crear atributos;
- modificar atributos;
- eliminar atributos;
- crear relaciones;
- configurar multiplicidades;
- crear herencia;
- mover elementos;
- usar Undo/Redo.

Todas las mutaciones se representarán mediante `UmlCommand`.

Ejemplos de familias de comando, sin fijar contratos de transporte:

```text
CreateClass
DeleteClass
RenameClass
AddAttribute
RemoveAttribute
UpdateAttribute
CreateAssociation
UpdateMultiplicity
MoveNode
```

No se define aquí ningún body, payload ni ruta de API.

---

## 10. Validación UML

Existirá un único motor de validación reutilizado por:

- guardado;
- importación;
- colaboración;
- asistente;
- generación.

Los diagnósticos tendrán:

- severity;
- code;
- mensaje;
- path lógico;
- referencia al elemento cuando corresponda.

La UI deberá navegar desde el diagnóstico hasta el elemento.

Los errores bloquearán persistencia/generación cuando corresponda.

Las advertencias no bloquearán por defecto.

---

## 11. Command Bus y Undo/Redo

Toda mutación local pasará por:

```text
adaptador
   ↓
UmlCommand
   ↓
UmlCommandBus
   ↓
UmlCommandExecutor
   ↓
ProjectDocument
```

El historial local tendrá un máximo inicial configurable de 100 operaciones.

Undo/Redo podrá utilizar snapshots internos o comandos compensatorios.

La colaboración deberá reutilizar el mismo contrato conceptual de comando.

---

## 12. Creación desde imagen

Flujo:

```text
Imagen
  ↓
Pillow + scikit-image
  ↓
Qwen2.5-VL 3B Instruct local para imagen → UML
  ↓
Representación estructurada
  ↓
Validador UML
  ↓
CanonicalUmlModel
```

Se intentará reconocer:

- clases;
- atributos;
- relaciones;
- multiplicidades;
- herencia.

La salida del modelo multimodal nunca se aplicará sin validación.

---

## 13. Creación y edición por voz

Flujo:

```text
Micrófono
  ↓
faster-whisper sobre CTranslate2
  ↓
Texto
  ↓
Proveedor IA cloud (alternativa local opcional)
  ↓
Intención estructurada
  ↓
Resolver
  ↓
UmlCommand
  ↓
Validador
  ↓
Command Bus
```

La IA no manipulará el canvas.

El conjunto de operaciones será cerrado.

---

## 14. IA compartida y ejecución local opcional

La herramienta deberá funcionar con un proveedor de IA de texto en la nube. Proveedor, modelo, SDK y costos se decidirán en CU-18 y se registrarán con evidencia real. No se exige contratar varios proveedores.

Qwen3 1.7B Instruct con Hugging Face Transformers + PyTorch queda como alternativa local opcional. Qwen2.5-VL 3B local se conserva para imagen → UML. No se sustituyen modelos por preferencias del agente.

El backend intermedia todas las solicitudes: las credenciales no se entregan al cliente. La conversación y el contexto son compartidos por sesión autorizada; no hay chats privados con la IA. Contexto compartido no significa mantener una instancia física exclusiva de un modelo cloud.

La IA explica, revisa, propone y resume avances a petición de participantes autorizados. No inicia trabajo autónomamente. Las mutaciones pasan por comandos cerrados, revisión y permisos vigentes, validación y persistencia autoritativa antes del broadcast. No manipula el canvas ni inventa lógica de negocio.

La ambigüedad entre órdenes por texto y la exigencia de pedir modificaciones por voz se mantiene explícita en la sección 41. No se habilitarán mutaciones textuales nuevas antes de resolverla.

---

## 15. Speech-to-Text

Tecnología fija:

**faster-whisper sobre CTranslate2**

El objetivo será interpretar comandos breves.

No se exige para el segundo parcial:

- reuniones largas;
- diarización;
- transcripción profesional;
- ruido extremo.

El backend ejecutará STT por defecto; no se envía audio directamente a credenciales de proveedor desde el cliente.

---

## 16. Enterprise Architect y XMI

Interoperabilidad objetivo:

- Sparx Systems Enterprise Architect;
- XMI 2.1;
- subconjunto UML soportado por el producto.

Importación:

```text
XMI
 ↓
Parser/adaptador
 ↓
Modelo intermedio
 ↓
Validador
 ↓
CanonicalUmlModel
```

Exportación:

```text
CanonicalUmlModel
 ↓
Adaptador XMI
 ↓
XMI 2.1
```

Implementación XML:

**lxml con iterparse**

No se intentará soportar todo XMI desde el primer ciclo.

---

## 17. Colaboración realtime

Servidor:

**WebSockets de FastAPI**

Cliente:

**WebSocket nativo del navegador**

Modelo:

- servidor autoritativo;
- una operación por intención;
- `baseRevision`;
- nueva revisión después de operación aceptada;
- persistencia inmediata;
- broadcast a participantes;
- rechazo de operaciones obsoletas;
- recuperación del documento autoritativo ante divergencia.

No se enviará el documento completo en cada edición.

No se utilizará un CRDT completo en el MVP.

---

## 18. Presencia

La presencia será efímera y separada de `ProjectDocument`.

Se podrá transmitir:

- sesión conectada;
- selección;
- cursor remoto;
- elemento en edición;
- última actividad.

La presencia no incrementará revisión.

---

## 19. Operación cloud, offline y LAN

El escenario obligatorio del segundo parcial es multiusuario remoto con persistencia NoSQL en la nube, sesiones retomables y contexto grupal persistente. Un servidor local con clientes LAN no sustituye este escenario.

La operación offline/LAN se conserva como objetivo previo, pendiente de cotejar con el enunciado del primer parcial. No se elimina ni se promete equivalencia cloud/offline antes de esa revisión. No se implementan colas offline, resolución adicional de conflictos ni una segunda fuente persistente por anticipado.

IA local opcional no implica por sí misma que toda la aplicación pueda operar sin Internet.

---

## 19.1 Despliegue AWS

Se conserva AWS como destino decidido del despliegue. Los servicios concretos se seleccionarán en CU-23, coordinando la persistencia NoSQL elegida en CU-25, sin fijarlos anticipadamente.

El despliegue contempla frontend Vue, backend FastAPI, almacenamiento NoSQL cloud, integración de IA, WebSockets, configuración y secretos externos, procedimiento reproducible y smoke tests. CU-28 incorpora y verifica push sobre el cliente móvil elegido. Los CUs dependientes revalidan el despliegue al incorporar sus capacidades.

---

## 20. Persistencia, autenticación y ownership

Persistencia objetivo de la herramienta CASE: **MongoDB Atlas sobre AWS + PyMongo 4.19.0**. La estrategia de migración se desarrolla en CU-25; región, tier y cuenta se configuran allí con acceso autorizado. JSONB sobre PostgreSQL no satisface este requisito.

Se deben conservar usuarios, credenciales protegidas, propiedad, permisos, UUIDs, revisiones, timestamps, UML y layout separados. La migración requiere respaldo, validación de integridad y plan de recuperación; no se borra la base existente por defecto.

Las sesiones guardan participantes, conversación grupal y actividad atribuida suficiente para retomar trabajo y resumir avances. Reconectar recupera documento, revisión y contexto persistidos. El historial de conversación/actividad no es equivalente a los snapshots efímeros de Undo/Redo.

Se mantiene revisión optimista y escritura condicional atómica; el diseño concreto depende del motor elegido. No debe anunciarse como aceptado un cambio que no se haya persistido.

Se mantienen PyJWT + pwdlib/Argon2 y autorización por proyecto. El propietario administra acceso; EDITOR puede mutar; VIEWER solo lee. Conversación y resúmenes no deben filtrar información de otros proyectos. Los contratos concretos de sesiones e invitaciones se definen solo en el CU que los necesite.

SQLAlchemy, Alembic y PostgreSQL corresponden al adaptador existente durante la transición; no son el destino de persistencia CASE. PostgreSQL sí sigue decidido para el backend generado de la sección 22.

---

## 21. UML → modelo relacional

La transformación será determinista:

```text
CanonicalUmlModel
       ↓
RelationalMapper
       ↓
RelationalModel
```

El modelo relacional contendrá:

- tables;
- columns;
- primary keys;
- foreign keys;
- unique constraints;
- indexes;
- relations.

Se documentarán reglas para:

- clase → tabla;
- atributo → columna;
- identificador → PK;
- 1:1;
- 1:N;
- N:M;
- composición;
- herencia;
- enums;
- nulabilidad;
- restricciones.

La IA no decidirá estas reglas en runtime.

---

## 22. Backend generado

Stack obligatorio:

**Java 21 LTS + Spring Boot 4.x + Spring Data JPA + Hibernate + PostgreSQL**

El generador deberá producir una estructura equivalente a:

```text
generated-backend/
├── domain/
├── persistence/
├── application/
├── api/
├── validation/
├── errors/
└── config/
```

La estructura exacta deberá seguir convenciones razonables de Spring Boot.

El código se generará mediante:

**Jinja2**

Se prohíbe la concatenación manual extensa de código fuente.

---

### Backend generado obligatorio

Independientemente del stack utilizado por la aplicación principal, **todo backend generado por la herramienta deberá utilizar obligatoriamente**:

- Java 21 LTS;
- Spring Boot 4.x;
- Gradle;
- Spring Web MVC;
- Spring Data JPA;
- Hibernate;
- Jakarta Validation;
- Jackson;
- springdoc-openapi;
- PostgreSQL.

El stack de la aplicación principal y el stack generado son conceptos independientes.

La IA de implementación no deberá sustituir Spring Boot por el framework utilizado internamente por la herramienta principal.

## 23. Capacidades generadas

Por entidad, cuando corresponda:

- create;
- read;
- update;
- delete;
- list;
- pagination;
- sorting;
- filtering;
- search;
- count;
- navegación de relaciones.

La API deberá permitir resolver operaciones de lenguaje natural a partir de metadatos, no de endpoints programados frase por frase.

Este documento no fija rutas ni cuerpos.

---

## 24. Auditoría

Los metadatos de generación podrán activar:

- createdAt;
- updatedAt.

Esto permitirá resolver de forma determinista expresiones como:

- últimos;
- recientes;
- modificados recientemente.

La implementación de auditoría del backend generado se adaptará a **Spring Data JPA + Hibernate**. SQLAlchemy 2.0 + Alembic corresponden al adaptador CASE anterior a su migración NoSQL, no al backend generado.

---

## 25. OpenAPI y colección Postman obligatoria

La especificación del backend generado se publicará mediante:

**springdoc-openapi sobre el backend Spring Boot generado**

Flujo:

```text
UML
       ↓
Backend Spring Boot generado
       ↓
springdoc-openapi
       ↓
OpenAPI
       ↓
Postman Collection
       ↓
Cliente tipado del frontend cuando corresponda
```

OpenAPI será la fuente para documentación y artefactos derivados. La colección de pruebas generada deberá ser obligatoriamente una **Postman Collection**.

No se documentan rutas concretas en `product.md`.

---

## 26. Frontend generado

La aplicación principal de la herramienta CASE continuará utilizando Vue 3 + TypeScript.

La salida móvil generada por la herramienta utilizará obligatoriamente:

Flutter + Dart

Plataforma objetivo inicial:

Android

La aplicación móvil generada consumirá la API REST producida por el backend Spring Boot generado.

Flujo:

CanonicalUmlModel
       │
       ├──► Backend generado
       │       └── Java 21 + Spring Boot
       │
       └──► Aplicación móvil generada
               └── Flutter + Dart
                       │
                       └── Android

La aplicación Flutter generada incluirá, cuando corresponda:

listados;
detalle;
formularios;
creación;
edición;
eliminación;
búsqueda;
filtros;
paginación;
relaciones;
validaciones;
asistente;
captura de voz.

La aplicación Flutter no contendrá lógica de negocio inventada por el generador.

Su estructura y comportamiento deberán derivarse de:

CanonicalUmlModel;
RelationalModel cuando corresponda;
OpenAPI;
Domain Manifest;
metadatos de generación.

La comunicación con el backend generado deberá realizarse mediante API REST.

La generación deberá producir un proyecto Flutter válido y compilable para Android.

Una estructura orientativa podrá ser:

generated-mobile/
├── lib/
│   ├── models/
│   ├── services/
│   ├── repositories/
│   ├── screens/
│   ├── widgets/
│   ├── forms/
│   ├── assistant/
│   └── main.dart
├── android/
├── test/
└── pubspec.yaml

La estructura exacta podrá evolucionar durante la implementación siempre que preserve separación de responsabilidades, mantenibilidad y compilación correcta.

## 27. Inferencia de UI CRUD

Reglas mínimas:

| Tipo | UI |
|---|---|
| String | input |
| Integer/Long | number |
| Decimal | number |
| Boolean | checkbox/switch |
| Date | date picker |
| DateTime | datetime picker |
| Enum | select |
| N:1 | select/autocomplete |
| 1:N | tabla/listado relacionado |
| Text | textarea |

El generador debe priorizar consistencia y funcionalidad sobre diseño específico de negocio.

---

## 28. Domain Manifest

Se generará un `Domain Manifest` derivado del modelo y/o OpenAPI.

Contendrá:

- entidades;
- atributos;
- tipos;
- relaciones;
- aliases;
- propiedades buscables;
- propiedades ordenables;
- operaciones permitidas;
- validaciones;
- capacidades CRUD;
- mapeo lógico necesario para que el ejecutor resuelva la operación solicitada.

No se incluye aquí un ejemplo JSON para evitar fijar un contrato de otra aplicación.

---

## 29. Asistente en la aplicación generada

Flujo:

```text
Texto o audio
  ↓
STT si corresponde
  ↓
Hugging Face Transformers + PyTorch + Domain Manifest
  ↓
AssistantCommand
  ↓
CommandValidator
  ↓
Executor
  ↓
Backend generado
  ↓
Resultado
```

El asistente solo podrá operar capacidades declaradas.

---

## 30. Lenguaje intermedio cerrado

Operaciones iniciales:

```text
LIST
GET
SEARCH
CREATE
UPDATE
DELETE
COUNT
```

El esquema concreto será definido por la IA de implementación para esta variante, pero deberá mantenerse:

- pequeño;
- estable;
- tipado;
- validable;
- independiente de frases;
- independiente de URLs.

No se incluye ningún body de ejemplo.

---

## 31. Operaciones compuestas

El asistente podrá construir planes cortos.

Ejemplo conceptual:

```text
1. Buscar una entidad relacionada.
2. Validar que existe exactamente el resultado esperado.
3. Crear o modificar otra entidad utilizando la referencia anterior.
4. Mostrar el resultado.
```

Cada paso deberá validarse antes de ejecutarse.

---

## 32. Seguridad del asistente

Principios obligatorios:

1. salida estructurada;
2. esquema cerrado;
3. allow-list de operaciones;
4. allow-list de entidades;
5. allow-list de campos;
6. tipos validados;
7. relaciones validadas;
8. confirmación opcional de acciones destructivas;
9. sin SQL generado por IA;
10. sin ejecución de código generado por IA;
11. sin URLs arbitrarias generadas por IA.

---

## 33. Metadatos de generación

Se soportará un perfil propio con conceptos como:

```text
entity
auditable
readOnly
searchable
crud
required
unique
sortable
defaultSort
```

Estos metadatos controlarán:

- persistencia;
- frontend;
- búsquedas;
- auditoría;
- validación;
- asistente.

Deberá documentarse qué parte pertenece a UML y qué parte es perfil propio.

---

## 34. Testing

### Backend

- pytest + pytest-asyncio + HTTPX

### Frontend

- Vitest + Vue Test Utils

### Mobile generado

- flutter analyze;
- flutter test;
- validación de compilación Android.

### End-to-end

- Cypress

### Generadores

Se verificará:

- archivos;
- sintaxis;
- compilación;
- relaciones;
- OpenAPI;
- Postman;
- Domain Manifest;
- frontend;
- backend;
- comandos del asistente.

---

## 35. Flujo de demostración objetivo

1. crear varias clases relacionadas;
2. validar;
3. guardar;
4. abrir desde otro cliente;
5. editar colaborativamente;
6. observar presencia;
7. transformar UML a modelo relacional;
8. generar backend;
9. generar OpenAPI y Postman;
10. generar Domain Manifest;
11. generar frontend;
12. generar salida Android;
13. compilar todo;
14. ejecutar CRUD;
15. ejecutar una operación textual;
16. ejecutar una operación equivalente por voz;
17. importar/exportar XMI;
18. verificar el objetivo offline/LAN según sección 19 y la aclaración del primer parcial;
19. demostrar sesión IA grupal, recuperación de avances y visor móvil con push según sección 41.

No se utiliza un dominio de ejemplo fijo para no contaminar el diseño de los proyectos de los estudiantes.

---

## 36. MVP

El MVP deberá demostrar:

1. clases, atributos y relaciones;
2. modelo canónico;
3. layout separado;
4. validación;
5. Command Bus;
6. Undo/Redo;
7. persistencia;
8. autenticación/ownership;
9. colaboración realtime;
10. presencia;
11. UML → relacional;
12. backend Spring Boot generado;
13. CRUD;
14. filtros/paginación/ordenamiento;
15. OpenAPI;
16. Postman;
17. Domain Manifest;
18. generación de aplicación Flutter a partir del modelo;
19. aplicación Flutter compilable y ejecutable en Android;
20. texto → AssistantCommand;
21. voz → STT → AssistantCommand;
22. ejecución validada;
23. XMI;
24. objetivo offline/LAN según sección 19, pendiente de cotejo del primer parcial;
25. todos los requisitos grupales/cloud/móviles de la sección 41.

Imagen → UML podrá incorporarse una vez estable el pipeline determinista.

---

## 37. Orden de implementación recomendado

```text
1. CanonicalUmlModel
2. ProjectDocument + DiagramLayout
3. Validación
4. UmlCommand + Command Bus
5. Canvas con @vue-flow/core
6. Persistencia NoSQL cloud con revisión optimista (CU-25)
7. Undo/Redo
8. Auth + ownership
9. Realtime con WebSockets de FastAPI
10. Presencia
11. UML → RelationalModel
12. Generador de backend Spring Boot
13. Backend generado compilable
14. OpenAPI
15. Postman
16. Domain Manifest
17. Generador de aplicación móvil Flutter
18. CRUD genérico Flutter
19. AssistantCommand
20. Texto → intención usando proveedor cloud (local opcional); aplicación textual pendiente de aclaración
21. Ejecutor
22. STT con faster-whisper sobre CTranslate2
23. Voz → comando
24. Compilación y ejecución Android mediante Flutter
25. XMI 2.1
26. Imagen → UML con Qwen2.5-VL 3B Instruct 
```

La IA, la visión y la generación no deben preceder a la estabilización del modelo canónico, la validación y la ruta única de mutación.

---

## 38. Trabajo por ciclos

La IA deberá producir los casos de uso y luego ciclos.

Cada ciclo tendrá:

- objetivo;
- casos de uso pequeños;
- criterios de aceptación;
- pruebas;
- build verde;
- documentación de arquitectura;
- estado real separado;
- deuda técnica explícita.

No se deben copiar identificadores de casos de uso de otro proyecto.

---

## 39. Stack consolidado

```text
- Frontend web: Vue 3 + TypeScript + Vite
- Vuetify 3
- @vue-flow/core
- d3-dag
- Pinia
- Python 3.13+
- FastAPI
- MongoDB Atlas sobre AWS + PyMongo 4.19.0 para persistencia NoSQL cloud
- WebSockets de FastAPI

Interoperabilidad
- UML 2.5.1
- XMI 2.1
- Enterprise Architect
- lxml con iterparse

Generación
- Jinja2
- springdoc-openapi para el OpenAPI del backend Spring Boot generado
- OpenAPI
- Postman
- Domain Manifest

IA / STT
- Hugging Face Transformers + PyTorch
- IA de texto cloud por decidir en CU-18; Qwen3 1.7B local opcional
- Qwen2.5-VL 3B Instruct local para imagen → UML
- faster-whisper sobre CTranslate2

Aplicación generada
- Backend: Java 21 + Spring Boot 4.x + Spring Data JPA + Hibernate + PostgreSQL
- Mobile: Flutter + Dart
- Plataforma mobile inicial: Android
```

---

## 40. Definición resumida

La aplicación será una herramienta CASE colaborativa en la nube, con el objetivo previo offline/LAN tratado en la sección 19, que permite diseñar modelos UML de clases mediante edición manual, voz, imagen o XMI, mantener una fuente de verdad canónica y generar aplicaciones funcionales.

La aplicación principal utiliza Vue 3 + TypeScript + Vite como frontend web y FastAPI como backend.

A partir del modelo UML, la herramienta generará obligatoriamente:

- backend Java 21 + Spring Boot;
- API REST;
- OpenAPI;
- Postman Collection;
- Domain Manifest;
- aplicación móvil Flutter + Dart para Android.

Flutter se utilizará para la salida mobile y no reemplazará el frontend web principal en Vue.


---

## 41. Requisitos del segundo parcial y criterios de aceptación

La transcripción aportada por el usuario es la referencia recibida del docente; no reemplaza el enunciado original del primer parcial. Las dudas se registran en `docs/requirements/SECOND-PARTIAL.md` y no se resuelven inventando alcance.

1. Conservar todas las capacidades exigidas en el primer parcial. Su cobertura se verificará contra el enunciado original, todavía pendiente de aportar; no se declara cumplida por tener código o documentación.
2. Varios usuarios autorizados editan el mismo diagrama en tiempo real desde ubicaciones distintas. Todos observan el mismo documento autoritativo; conflictos y reconexión no sobrescriben cambios silenciosamente.
3. Una conversación de IA grupal por sesión: solicitudes, respuestas e ideas solicitadas visibles para sus participantes, sin canales privados con la IA. Las ideas expresadas como texto no se convierten automáticamente en cambios UML.
4. Contexto compartido con identidad del autor y actividad atribuida. Si alguien llega tarde, puede solicitar un resumen basado en lo persistido de esa sesión y su diagrama.
5. La IA actúa solo por solicitud: puede explicar conceptos, revisar elementos, justificar problemas, sugerir ideas y ejecutar modificaciones autorizadas. No diseña ni corrige automáticamente.
6. Las modificaciones por IA reutilizan UmlCommand, autorización, validación, control de revisión, persistencia y broadcast. Una revisión obsoleta o permisos insuficientes impiden aplicar el cambio.
7. Voz como entrada requerida; transcripción visible e integración con la conversación grupal. Permitir modificaciones mediante texto queda pendiente de aclarar: el docente también indicó que la IA no diseñará sin petición por voz.
8. Persistencia NoSQL en la nube para el estado de la herramienta, sesiones, contexto y actividad. Pausar, reiniciar el backend y retomar debe preservar el trabajo registrado. Undo/Redo persistente no se presupone exigido: se conserva su comportamiento existente hasta que un CU lo amplíe.
9. IA cloud funcional como mínimo; IA local opcional y valorable. Se registran benchmarks reales al introducir o modificar LLM/VLM/STT.
10. Visor móvil informativo de la herramienta CASE: diagrama actualizado en tiempo real, sin edición UML, con notificaciones push de actualizaciones. Se verificarán permisos, reconexión y recepción push en dispositivo; responsive por sí solo no prueba push.
11. Mantener Vue y FastAPI. La mención de Spring Boot en la transcripción es permisiva, no una obligación de migrar el backend principal. El backend Spring Boot y el CRUD Flutter generados siguen siendo salidas independientes que no se eliminan por esta ampliación.
12. La aceptación requiere demostración con dos editores y un observador móvil, interacción grupal, edición por voz, resumen al incorporarse tarde, reapertura tras reinicio, rechazo de acceso no autorizado y push real. Los estados esperados no se registran como pruebas ejecutadas.

La matriz de requisitos y el roadmap determinan cobertura y orden. MongoDB Atlas sobre AWS y PyMongo quedan seleccionados para persistencia CASE. No se fijan todavía proveedor IA/push, rutas, payloads ni una infraestructura de inferencia dedicada. El roadmap es la secuencia operativa; la sección 37 es orientación conceptual y no autoriza adelantar CUs.
