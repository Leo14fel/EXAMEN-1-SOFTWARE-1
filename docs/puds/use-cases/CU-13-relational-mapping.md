# CU-13 - Transformar UML a modelo relacional

**Estado: IMPLEMENTED, tres incrementos; aceptación visual/cloud diferida.** Inicio 2026-11-07. Usuario autorizó continuar agregando casos sin quedar pendiente. Dependencia CU-04; conserva casos previos y deuda visual/cloud explícitamente diferida. Product secciones 6, 7, 21, 33.

## Plan y alcance

Tres incrementos: (1) contratos Pydantic del modelo relacional, perfil mínimo y mapeo de clases/atributos/PK/tipos/constraints; (2) relaciones, cardinalidades, composición, herencia y pruebas; (3) consulta autorizada y vista previa del editor, regresión y evidencia. No incluye archivos SQL/Java/Flutter, Jinja, ejecución de DDL, migración ni cambios de datos. CU-14..17 son pasos posteriores. Sin IA ni benchmark IA.

## Decisiones necesarias ahora

Modelo relacional derivado determinísticamente de CanonicalUmlModel y perfil explícito. Perfil mínimo bajo metadata.generation (version=1): classes por UUID (tableName/primaryKeyAttributeId), attributes por UUID (columnName/required/unique/indexed), enumTypes con listas de valores. No se añade metadata a UmlModel ni se usa layout. Atributos nullable por defecto salvo required/PK/FK; no se deducen requisitos por nombre o por visibilidad. Cada raíz recibe PK UUID técnica id salvo primaryKeyAttributeId explícito. Los valores por defecto de negocio no se inventan. Tipos desconocidos producen diagnóstico, nunca conversión silenciosa a texto. Enum de perfil se representa por texto con allowedValues; no equivale a añadir Enumeration al UML canónico.

Nombres SQL derivados en ASCII snake_case, con prefijo y sufijo estable por UUID, máximo 63 bytes. Overrides explícitos restringidos a identificadores ASCII; colisiones se rechazan. CU-14 deberá citar/escapar identificadores/literales correctamente al emitir código, no se emite SQL aquí. Herencia JOINED de padre único con PK heredada/FK CASCADE; herencia múltiple rechazada. Relaciones 1:1 FK única, 1:N FK en N, N:M tabla de unión con PK compuesta; índices para FKs no cubiertas. Composición FK de parte a todo con CASCADE y multiplicidad de todo <=1; otras relaciones RESTRICT. No se deducen reglas de negocio a partir de métodos UML.

Multiplicidades que necesiten conteos entre filas se conservan como metadatos/requisitos de validación y avisos; PK/FK/UNIQUE/NOT NULL por sí solos no las garantizan. Cero como máximo y composiciones con varios tipos de owner se rechazan en esta primera estrategia. No declarar restricciones de cardinalidad avanzada ya ejecutadas.

## Incremento 1 - DONE

Modelo relacional/perfil mínimo, tipos, PK UUID o atributo explícito, required/unique/indexed/enums de perfil, nombres acotados y determinismo. Gate completo scripts/check.ps1 PASS: 296 backend/80 frontend, Ruff/compileall/pip check/typecheck/build. Un hallazgo de longitud de línea de Ruff corregido y gate repetido. 98 warnings (96 MongoMock TTL y 2 previos); chunk Vite existente. No IA/benchmark aplicable.

## Incremento 2 - DONE

Relaciones 1:1/1:N/N:M y autorrelaciones, FK/índices, composición CASCADE con limitaciones explícitas, herencia JOINED de padre único y referencias de atributos a clases resueltas al tipo de PK. Grafo de almacenamiento validado por Pydantic: nombres, columnas, claves/FK y tipos compatibles. Multiplicidades se conservan sin compartir objetos con el UML original. Gate completo PASS: 306 backend/80 frontend, Ruff/compileall/pip check/typecheck/build. Diez pruebas nuevas, 90 warnings medidos (88 MongoMock TTL y 2 previos), chunk Vite existente.

## Incremento 3 - IMPLEMENTED

GET /projects/{id}/relational-model autoriza lectura con _project_access para owner/editor/viewer, devuelve projectId/sourceRevision/model/diagnostics. Tipos/metadatos/semántica inválidos producen model=null y diagnóstico, no esquema parcial. Consulta no muta proyecto/revisión/historial/permisos. Perfil inválido da diagnóstico GENERATION_PROFILE_INVALID. No se expone ni aplica SQL.

Editor añade «Modelo relacional»: tablas, columnas, tipos, nulabilidad, PK/FK, UNIQUE, índices y enums de perfil; avisos/errores visibles como texto escapado. Puede actualizar vista y descargar JSON derivado. Si el diagrama cambia, se indica revisión desactualizada y se bloquea descargar como si fuera actual. Perfil mínimo se lee de metadata.generation: esta iteración no añade un editor visual del perfil ni modifica sus metadatos. DiagramLayout/ownership no entran en el mapper.

Gate completo scripts/check.ps1 PASS: **309 backend/86 frontend en 20 archivos**, Ruff/compileall/pip check/typecheck/build. 98 warnings medidos: 96 datetime.utcnow internos de MongoMock TTL y 2 externos previos; chunk Vite >500 kB existente. No se introdujeron librerías ni benchmark IA. Tres tests API nuevos de permisos/lectura inmutable, perfil/tipo inválido y PK explícita/vacío; seis tests frontend nuevos de API, tablas/constraints, revisión obsoleta, diagnóstico escapado y fallo de consulta. Veinticuatro tests de mapper (14 inc.1 + 10 inc.2).

Smoke HTTP TCP loopback con MongoMock temporal PASS: tres clases/dos relaciones, PK natural Long heredada por JOINED, composición, lectura sin mutación y mismo modelo después de mover un nodo (solo cambia sourceRevision). Resultado artifacts/cu13/wire-result.json, 2026-11-07 14:48:32 Bolivia; script relational-wire.py, servidor/datos temporales retirados. No es Atlas ni verificación de ejecución DDL PostgreSQL; no se aplicó esquema generado.

## Reglas y límites verificados

Mapeos de tipos: String/Text/string→text; Integer/int→integer; Long/long→bigint; Decimal/BigDecimal→numeric sin precisión inventada; Boolean/boolean/bool→boolean; Date→date; DateTime/Instant→timestamp with time zone; UUID→uuid; Double/Float→double precision. Tipos de clase resuelven referencia FK con el mismo tipo de PK destino. No se fusiona esa referencia con una asociación existente por suponer que representan lo mismo. Visibilidad no define nulabilidad ni seguridad de datos; operaciones UML no se convierten en columnas/lógica y generan aviso.

Nombres normales usan prefijos t/c/r/j/fk/ix y hash estable de UUID, ASCII y <=63 bytes; overrides explícitos ASCII minúscula y se detectan colisiones. RelationalModel valida grafo/nombres/PK no nula/columnas de índice/clave única referenciada/tipos FK coincidentes. Perfil desconocido y referencias de perfil obsoletas se rechazan. Orden canónico de entrada y posiciones no cambian el resultado. PK técnica default UUID, o atributo explícito de UUID/text/integer/bigint; no se deduce PK por nombre. En herencia, raíz genera identidad y hija usa PK no generada/FK al padre; herencia múltiple y override de PK hija se rechazan.

FK de 1:N se almacena en N y su nulabilidad deriva del mínimo del extremo referenciado; 1:1 añade UNIQUE, N:M usa dos FK/PK compuesta y evita índice duplicado cubierto por PK. Autorrelación N:M conserva source_id/target_id diferentes. FKs normales RESTRICT; composición parte→todo CASCADE; JOINED CASCADE hacia hijo. La composición exige un tipo de owner por clase parte y máximo uno en el extremo del todo; no se afirma resolver todos los patrones UML posibles.

Multiplicidades no expresables solo con PK/FK/UNIQUE/NOT NULL quedan en relation.sourceMultiplicity/targetMultiplicity y requiresRuntimeValidation con aviso. También se avisa validar propiedad/ciclos de objetos de composición. El generador posterior debe abordar estas obligaciones o rechazar el plan; este CU no promete que estén ejecutadas. Upper=0 se rechaza en esta estrategia. Se limita a 2000 clases/20 000 atributos/10 000 relaciones; profundidad excesiva de herencia se convierte en diagnóstico controlado. Enums se declaran explícitamente en perfil y producen allowedValues sobre texto; no son soporte de Enumeration canónico aún ausente en CU-02.

## Aceptación pendiente y continuidad

Prueba visual: abrir modelo con clases/relaciones, pulsar Modelo relacional, revisar PK/FK/nulos/avisos, cambiar diagrama con diálogo abierto y actualizar, descargar JSON y confirmar revisión. VIEWER puede consultar; usuario ajeno no. Pruebas automáticas y TCP PASS; visual/cloud diferidas por usuario. No se declara DONE ni aceptación integral. No se modificó product.md, datos reales, configuración de persistencia, SQL/Java/Flutter ni se hizo commit/push. Siguiente CU-14: generador Java 21/Spring Boot/Jinja2, con compilación real y sin inventar negocio; no se implementó anticipadamente aquí.

Fuentes primarias consultadas: [restricciones PostgreSQL](https://www.postgresql.org/docs/18/ddl-constraints.html), [identificadores PostgreSQL](https://www.postgresql.org/docs/current/sql-syntax-lexical.html). No se presentan como ejecución de PostgreSQL ni métricas.

## Git (no ejecutado)

El árbol comparte cambios de CUs anteriores. Stagear solo archivos/hunks CU-13 y revisar; nunca git add . ni mezclar CUs. Para cambios compartidos usar selección/edición de hunks según corresponda:

```powershell
git add -- backend/app/domain/relational backend/app/api/relational.py backend/tests/domain/test_relational_mapping.py backend/tests/api/test_relational_preview.py frontend/src/features/editor/relational-api.ts frontend/src/features/editor/relational-api.spec.ts frontend/src/features/editor/RelationalPreview.vue frontend/src/features/editor/RelationalPreview.spec.ts docs/puds/use-cases/CU-13-relational-mapping.md
git add -p -- backend/app/main.py frontend/src/features/editor/EditorWorkspace.vue README.md docs/STATUS.md docs/PROJECT-CONTEXT.md docs/HANDOFF.md docs/TESTING.md docs/ARCHITECTURE.md docs/README.md docs/requirements/LEGACY-GAPS.md docs/puds/use-cases/IMPLEMENTATION-ROADMAP.md
git diff --cached
git commit -m "feat(cu-13): derive relational model and authenticated preview"
git push -u origin feat/xmi-export
```


## Apoyo a aceptación manual, 2026-11-07

Se preparó un perfil aislado con Cliente/Pedido, propietario/editor/observador y acceso a la vista relacional: [guía](../../MANUAL-REVIEW.md). Gate transversal 311 backend/86 frontend y smoke HTTP/WebSocket PASS, con dos tablas relacionales verificadas. Usa MongoMock temporal; revisión visual y Atlas siguen pendientes. No modifica el mapper ni inicia CU-14.

## Material de documentación y revisión humana inicial

2026-11-07: el usuario informó que el proyecto se ve bien, sin confirmar escenarios de CU-13. Se incorporó una base de informe y registro de evidencias en docs/delivery, enlazados desde docs/README.md; se describen los límites del mapper y de la prueba temporal. No cambia aceptación visual/cloud ni implementación; siguiente CU-14. Verificación documental de UTF-8, enlaces locales y bloques Markdown PASS; no se repitieron pruebas de código porque solo cambió documentación.
