# Documento de producto — Variante 2

> Herramienta CASE colaborativa, offline-first, para modelado UML de clases, generación automática de aplicaciones y operación mediante interfaz, lenguaje natural y voz.

## 1. Estado inicial y uso de este documento

Este documento describe un proyecto que **todavía no ha comenzado a implementarse**.

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

El sistema deberá poder funcionar sin Internet para sus capacidades esenciales.

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
- SQLAlchemy 2.0 + Alembic
- WebSockets de FastAPI
- PostgreSQL
- PyJWT + pwdlib con Argon2
- Pydantic 2

### XML / interoperabilidad / generación

- XMI 2.1
- Enterprise Architect como herramienta objetivo de interoperabilidad
- lxml con iterparse
- Jinja2
- springdoc-openapi para el OpenAPI del backend Spring Boot generado

### IA, visión y voz

- runtime: Hugging Face Transformers + PyTorch
- texto: Qwen3 1.7B Instruct en ejecución local
- visión: Qwen2.5-VL 3B Instruct local para imagen → UML
- STT: faster-whisper sobre CTranslate2
- preprocesamiento de imagen: Pillow + scikit-image

### Criterio de la variante

Esta variante prioriza productividad y tipado de datos con Pydantic. La parte de IA se mantiene en Python sin un servidor de inferencia separado obligatorio.

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

La tecnología Flutter se utilizará exclusivamente para la salida móvil Android generada por la herramienta. Por lo tanto existirán dos conceptos independientes:

frontend web principal de la herramienta CASE: Vue 3 + TypeScript;
aplicación móvil generada: Flutter + Dart para Android.

La aplicación móvil consumirá la API REST generada a partir del modelo y deberá conservar las capacidades CRUD, relaciones, búsqueda, filtros y asistente que correspondan al modelo generado.
---

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
Hugging Face Transformers + PyTorch
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

## 14. IA local

Runtime fijo:

**Hugging Face Transformers + PyTorch**

Modelo de texto:

**Qwen3 1.7B Instruct en ejecución local**

Modelo multimodal:

**Qwen2.5-VL 3B Instruct local para imagen → UML**

El modelo de texto deberá priorizar:

- baja latencia;
- extracción de intención;
- salida estructurada;
- ejecución local.

El multimodal podrá cargarse bajo demanda.

Los modelos deberán descargarse antes de trabajar offline.

---

## 15. Speech-to-Text

Tecnología fija:

**faster-whisper sobre CTranslate2**

El objetivo será interpretar comandos breves.

No se optimizará inicialmente para:

- reuniones largas;
- diarización;
- transcripción profesional;
- ruido extremo.

La estación anfitriona ejecutará STT por defecto.

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

## 19. Offline y LAN

Escenario principal:

```text
Equipo anfitrión
├── FastAPI
├── PostgreSQL
├── Hugging Face Transformers + PyTorch
├── faster-whisper sobre CTranslate2
└── realtime
      │
      │ LAN / hotspot
      ▼
otros clientes
```

No se requerirá Internet para usar el editor, colaborar en LAN, ejecutar IA/STT o operar la aplicación generada una vez instalados modelos y dependencias.

---

## 19.1 Despliegue AWS

El producto tendrá un despliegue en AWS. El servicio o combinación exacta de servicios AWS se decidirá en el caso de uso de despliegue correspondiente, sin fijar infraestructura antes de ese momento.

El despliegue deberá contemplar:

- frontend Vue;
- backend FastAPI de la herramienta CASE;
- PostgreSQL;
- configuración y secretos externos al código;
- smoke tests del despliegue.

El despliegue cloud no reemplaza las capacidades esenciales locales/offline del producto.

---

## 20. Persistencia, autenticación y ownership

Persistencia principal:

**SQLAlchemy 2.0 + Alembic + PostgreSQL**

Autenticación:

**PyJWT + pwdlib con Argon2**

Cada proyecto tendrá `ownerId`.

Las consultas de proyecto se filtrarán por autorización.

La futura colaboración mediante invitaciones utilizará conceptualmente:

- ProjectMembership;
- ProjectInvitation;
- roles;
- expiración;
- token de invitación de un solo uso o uso controlado.

No se fijan rutas HTTP en este documento.

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

La implementación de auditoría del backend generado se adaptará a **Spring Data JPA + Hibernate**. SQLAlchemy 2.0 + Alembic pertenecen al backend FastAPI de la herramienta CASE.

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
18. repetir sin Internet.

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
24. funcionamiento offline.

Imagen → UML podrá incorporarse una vez estable el pipeline determinista.

---

## 37. Orden de implementación recomendado

```text
1. CanonicalUmlModel
2. ProjectDocument + DiagramLayout
3. Validación
4. UmlCommand + Command Bus
5. Canvas con @vue-flow/core
6. Persistencia con SQLAlchemy 2.0 + Alembic
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
20. Texto → comando usando Hugging Face Transformers + PyTorch
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
- SQLAlchemy 2.0 + Alembic
- WebSockets de FastAPI
- PostgreSQL

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
- Qwen3 1.7B Instruct en ejecución local
- Qwen2.5-VL 3B Instruct local para imagen → UML
- faster-whisper sobre CTranslate2

Aplicación generada
- Backend: Java 21 + Spring Boot 4.x + Spring Data JPA + Hibernate + PostgreSQL
- Mobile: Flutter + Dart
- Plataforma mobile inicial: Android
```

---

## 40. Definición resumida

La aplicación será una herramienta CASE colaborativa y offline-first que permite diseñar modelos UML de clases mediante edición manual, voz, imagen o XMI, mantener una fuente de verdad canónica y generar aplicaciones funcionales.

La aplicación principal utiliza Vue 3 + TypeScript + Vite como frontend web y FastAPI como backend.

A partir del modelo UML, la herramienta generará obligatoriamente:

- backend Java 21 + Spring Boot;
- API REST;
- OpenAPI;
- Postman Collection;
- Domain Manifest;
- aplicación móvil Flutter + Dart para Android.

Flutter se utilizará para la salida mobile y no reemplazará el frontend web principal en Vue.
