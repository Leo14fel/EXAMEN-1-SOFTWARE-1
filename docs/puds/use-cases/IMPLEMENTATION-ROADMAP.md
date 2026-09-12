# Roadmap PUDS — Casos de uso y ciclos

## 1. Propósito
Transforma `product.md` en una receta lineal de implementación. Los CUs guían requisitos, diseño, implementación, pruebas y documentación. `product.md` sigue siendo la fuente de verdad.

## 2. Reglas
- Implementar en orden.
- Un CU activo a la vez.
- Máximo 3 incrementos por CU.
- Cada incremento termina verificable.
- No crear CUs separados solo por componentes técnicos; estos viven dentro del comportamiento que los necesita.
- CU-00 es la excepción técnica de fundación solicitada.
- Cada CU cerrado genera/actualiza `CU-XX-<slug>.md`.
- Cierre = pruebas verdes + documentación sincronizada + comandos Git.

# CICLO 1 — Fundación y editor UML local

**Incremento usable:** herramienta web local ejecutable capaz de mantener un documento UML en memoria, modelar clases/relaciones, editar el canvas, validar y usar Undo/Redo.

## CU-00 — Fundar el proyecto ejecutable
**Objetivo:** crear la base del monorepo y demostrar frontend ↔ backend.
**Actor:** equipo de desarrollo (fundación técnica).
**Dependencias:** ninguna.
**Product:** §§4, 34, 37–39.
**Incluye:** repo Git/GitHub; `frontend/` Vue+TS+Vite+Vuetify; `backend/` Python 3.13+ + FastAPI; preparación PostgreSQL/Alembic sin dominio; `.env.example`; `.gitignore`; health; llamada frontend→health; tests/smoke; docs reproducibles.
**No incluye:** UML, auth, realtime, IA, generación, Flutter.
**Incrementos:** 2 — (1) estructura/arranque; (2) health/integración/tests/docs.
**Cierre:** frontend y backend arrancan y frontend confirma health.

## CU-01 — Crear un documento de proyecto UML canónico
**Objetivo:** representar un proyecto separando semántica y layout.
**Actor:** usuario de modelado.
**Dependencias:** CU-00.
**Product:** §§3, 6, 7.
**Incluye:** ProjectDocument, UmlModel, DiagramLayout, UUID, metadatos, revisión, timestamps y serialización estructural.
**Incrementos:** 2.
**Cierre:** crear/serializar/reconstruir documento sin contaminar UML con layout.

## CU-02 — Modelar clases y miembros UML
**Objetivo:** crear/editar/eliminar clases y miembros soportados.
**Actor:** usuario de modelado.
**Dependencias:** CU-01.
**Product:** §§7, 9.
**Incluye:** Class, Attribute/Property, Operation, Visibility, tipos, Enumeration, Package cuando aplique y metadatos de generación separados.
**Incrementos:** 2.
**Cierre:** modelo modificable y testeado sin depender del canvas.

## CU-03 — Modelar relaciones UML
**Objetivo:** crear/modificar relaciones válidas.
**Actor:** usuario de modelado.
**Dependencias:** CU-02.
**Product:** §§7, 9.
**Incluye:** Association, Aggregation, Composition, Generalization, Multiplicity.
**Incrementos:** 2.
**Cierre:** relaciones sobreviven serialización/reconstrucción.

## CU-04 — Editar el diagrama desde el canvas
**Objetivo:** proyectar/editar el documento con `@vue-flow/core` sin volver el canvas fuente de verdad.
**Actor:** usuario de modelado.
**Dependencias:** CU-01..03.
**Product:** §§5, 5.1, 8, 9.
**Incluye:** nodos custom, relaciones, zoom/pan/selección/movimiento, creación de relaciones, inspector, toolbox, fit, grid y d3-dag.
**Incrementos:** 3.
**Cierre:** edición UI termina en documento canónico.

## CU-05 — Validar el modelo UML y navegar diagnósticos
**Objetivo:** único motor de validación + diagnósticos accionables.
**Actor:** usuario de modelado.
**Dependencias:** CU-02..04.
**Product:** §10 y §5.1.
**Incluye:** severity/code/mensaje/path/referencia, bloqueo y navegación UI.
**Incrementos:** 2.
**Cierre:** errores reproducibles y foco desde diagnóstico al elemento.

## CU-06 — Deshacer y rehacer modificaciones UML
**Objetivo:** canalizar mutaciones por Command Bus y soportar Undo/Redo.
**Actor:** usuario de modelado.
**Dependencias:** CU-02..05.
**Product:** §§9, 11.
**Incluye:** UmlCommand, bus, executor, historial inicial configurable de 100 y estrategia Undo/Redo.
**Incrementos:** 2.
**Cierre:** comandos soportados deshacen/rehacen manteniendo consistencia.

# CICLO 2 — Persistencia, acceso y colaboración

**Incremento usable:** usuario autenticado puede guardar/listar/abrir proyectos propios y colaborar con otro cliente con presencia, además de operar el host local/LAN base.

## CU-07 — Persistir y recuperar proyectos
**Objetivo:** almacenar ProjectDocument con PostgreSQL y revisión optimista.
**Actor:** usuario de modelado.
**Dependencias:** CU-01, CU-05, CU-06.
**Product:** §§6, 10, 20.
**Incluye:** SQLAlchemy, Alembic, PostgreSQL, migraciones, guardado/lectura/revisión.
**Incrementos:** 2.
**Cierre:** reabrir conserva modelo/layout.

## CU-08 — Acceder y administrar proyectos propios
**Objetivo:** autenticación, ownership y navegación de proyectos.
**Actor:** visitante/usuario autenticado.
**Dependencias:** CU-07.
**Product:** §§5, 20.
**Incluye:** landing, registro/login, PyJWT, Argon2/pwdlib, listado/creación/apertura, ownerId y autorización.
**Incrementos:** 3.
**Cierre:** usuario solo accede a proyectos autorizados.

## CU-09 — Editar colaborativamente en tiempo real
**Objetivo:** sincronizar operaciones con servidor autoritativo.
**Actor:** participantes del proyecto.
**Dependencias:** CU-06..08.
**Product:** §17.
**Incluye:** WebSockets, baseRevision, nueva revisión, persistencia inmediata, broadcast, obsoletos y recuperación autoritativa.
**Incrementos:** 3.
**Cierre:** dos clientes convergen al documento autoritativo.

## CU-10 — Mostrar presencia colaborativa
**Objetivo:** presencia efímera sin incrementar revisión.
**Actor:** participantes.
**Dependencias:** CU-09.
**Product:** §§5.1, 18.
**Incluye:** sesión, selección, cursor, elemento en edición, actividad y UI de presencia.
**Incrementos:** 2.
**Cierre:** presencia visible sin mutar el documento.

## CU-11 — Operar capacidades esenciales offline y por LAN
**Objetivo:** demostrar host + clientes LAN sin Internet para lo ya implementado.
**Actor:** anfitrión/clientes LAN.
**Dependencias:** CU-07..10.
**Product:** §19 y requisito offline general.
**Incluye:** configuración local/LAN, acceso, persistencia y realtime. IA/STT se revalida cuando exista.
**Incrementos:** 2.
**Cierre:** dos clientes usan capacidades implementadas por LAN sin Internet.

# CICLO 3 — Pipeline determinista y generación

**Incremento usable:** UML válido → modelo relacional → backend Spring Boot + OpenAPI/Postman/Manifest + app Flutter Android operativa para capacidades derivables.

## CU-12 — Transformar UML a modelo relacional
**Objetivo:** producir RelationalModel determinista.
**Actor:** usuario que genera.
**Dependencias:** CU-05.
**Product:** §21.
**Incluye:** tablas/columnas/PK/FK/unique/indexes/relations y reglas 1:1, 1:N, N:M, composición, herencia, enums, nulabilidad/restricciones.
**Incrementos:** 3.
**Cierre:** mismo UML → mismo modelo relacional con tests.

## CU-13 — Generar backend Spring Boot
**Objetivo:** generar backend Java compilable.
**Actor:** usuario que genera.
**Dependencias:** CU-12.
**Product:** §§22, 23, 33.
**Incluye:** Java21, Spring Boot4.x, Gradle, MVC, JPA/Hibernate, Validation, Jackson, PostgreSQL, Jinja2 y CRUD/capacidades declaradas.
**Incrementos:** 3.
**Cierre:** backend generado compila y ejecuta capacidades soportadas.

## CU-14 — Generar OpenAPI, Postman y Domain Manifest
**Objetivo:** producir artefactos coherentes del dominio generado.
**Actor:** usuario/desarrollador consumidor.
**Dependencias:** CU-13.
**Product:** §§25, 28, 33.
**Incluye:** OpenAPI según product vigente, Postman derivado, Domain Manifest.
**Incrementos:** 2.
**Cierre:** artefactos consistentes y validables.

## CU-15 — Generar aplicación móvil Flutter para Android
**Objetivo:** generar app Flutter que consuma backend generado.
**Actor:** usuario que genera/usuario final.
**Dependencias:** CU-13, CU-14.
**Product:** §§26, 27, 34, 36.
**Incluye:** Flutter+Dart, Android, modelos/services/repositories/screens/widgets/forms, CRUD, filtros, paginación, relaciones, validaciones e inferencia UI.
**Incrementos:** 3.
**Cierre:** analyze/tests/build Android acordado verdes y app opera contra backend.

## CU-16 — Ejecutar y verificar el flujo de generación
**Objetivo:** integrar UML válido hasta aplicación/artefactos compilables.
**Actor:** usuario CASE.
**Dependencias:** CU-12..15.
**Product:** §§23, 34–36.
**Incluye:** acción/UI de generación, validación previa, orquestación, verificación y demo CRUD.
**Incrementos:** 2.
**Cierre:** modelo de prueba recorre pipeline completo.

# CICLO 4 — Asistentes, voz, XMI e imagen

**Incremento usable:** instrucciones por texto/voz, asistente generado, XMI e imagen→UML dentro del alcance soportado, con benchmarks reales.

## CU-17 — Editar UML mediante lenguaje natural
**Objetivo:** texto → intención estructurada → UmlCommand; IA nunca manipula canvas.
**Actor:** usuario de modelado.
**Dependencias:** CU-05, CU-06.
**Product:** §§13, 14, 30, 32.
**Incluye:** Qwen3 1.7B local, esquema cerrado, allow-lists, resolver, validación, bus y UI asistente.
**Incrementos:** 3: baseline benchmark/esquema; modelo/prompt; resolver/UI/benchmark final.
**Cierre:** benchmark documentado + comandos válidos por ruta única.

## CU-18 — Editar UML mediante voz
**Objetivo:** audio breve → texto → reutilizar CU-17.
**Actor:** usuario de modelado.
**Dependencias:** CU-17.
**Product:** §§13, 15.
**Incluye:** faster-whisper/CTranslate2, captura, transcripción, comandos breves, integración y benchmark STT.
**Incrementos:** 2.
**Cierre:** audios documentados producen comandos equivalentes dentro del alcance aceptado.

## CU-19 — Operar la aplicación generada mediante asistente
**Objetivo:** ejecutar solo capacidades declaradas vía AssistantCommand.
**Actor:** usuario de app generada.
**Dependencias:** CU-14, CU-15, CU-17; CU-18 si usa voz.
**Product:** §§28–32.
**Incluye:** CommandValidator, Executor, LIST/GET/SEARCH/CREATE/UPDATE/DELETE/COUNT, planes cortos y seguridad.
**Incrementos:** 3.
**Cierre:** solo entidades/campos/operaciones allow-listed se ejecutan.

## CU-20 — Importar y exportar XMI
**Objetivo:** interoperar con XMI 2.1/Enterprise Architect en el subconjunto soportado.
**Actor:** usuario de modelado.
**Dependencias:** CU-05.
**Product:** §16.
**Incluye:** lxml/iterparse, importación→validación→modelo, exportación y round-trip donde aplique.
**Incrementos:** 2.
**Cierre:** subconjunto documentado importa/exporta reproduciblemente.

## CU-21 — Crear UML desde imagen
**Objetivo:** imagen → estructura UML → validación → modelo canónico.
**Actor:** usuario de modelado.
**Dependencias:** CU-05, CU-06.
**Product:** §§12, 14, 34, 36.
**Incluye:** Pillow/scikit-image, Qwen2.5-VL 3B, clases/atributos/relaciones/multiplicidades/herencia según capacidad, salida estructurada y benchmark VLM.
**Incrementos:** 3: dataset/baseline; VLM→estructura; validación/aplicación/edge cases/benchmark final.
**Cierre:** benchmark y pruebas manuales documentan capacidad y límites reales.

# Dependencias resumidas
```text
CU-00
  ↓
CU-01 → CU-02 → CU-03 → CU-04 → CU-05 → CU-06
                                   │
                                   ↓
CU-07 → CU-08 → CU-09 → CU-10 → CU-11
   │
   └────────────→ CU-12 → CU-13 → CU-14 → CU-15 → CU-16
                         │
                         ├────────→ CU-19
CU-05 → CU-06 → CU-17 → CU-18 ────┘
   │
   ├────────────→ CU-20
   └────────────→ CU-21
```

# Documento real de cada CU
Al iniciar un CU crear `docs/puds/use-cases/CU-XX-<slug>.md` desde `CU-TEMPLATE.md`. El roadmap describe intención; el documento del CU registra lo realmente implementado.

# Cierre de ciclo
- todos los CUs `DONE`;
- tests/lint/typecheck/build verdes;
- incremento usable demostrable;
- documentación sincronizada;
- deuda conocida explícita;
- ninguna decisión relevante vive solo en el chat.

# Punto pendiente: AWS
El `product.md` usado para derivar este roadmap no contiene una especificación AWS. No se crea un CU AWS ni se eligen servicios cloud aquí. Si AWS es requisito del docente, primero actualizar `product.md`; después se añadirá el CU de despliegue de forma controlada.
