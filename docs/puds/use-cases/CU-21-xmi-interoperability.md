# CU-21 - Importar y exportar XMI

**Estado: IMPLEMENTED para el subconjunto canónico, tres incrementos.** Exportación anterior + importador/round-trip + API/editor. Aceptación visual y prueba real con Enterprise Architect pendientes; no se declara DONE ni interoperabilidad completa con EA. Reanudación autorizada por el usuario para completar funciones antiguas, 2026-11-07.

## Gate final de la reanudación

277 backend/73 frontend, Ruff/compileall/pip check/typecheck/build PASS; 90 warnings medidos (88 MongoMock TTL y 2 externos previos), chunk Vite existente. Validación visual/EA permanece pendiente; el usuario pidió completar todo lo posible localmente, sin afirmar comprobaciones externas no ejecutadas. Se finaliza el trabajo de código de este CU antes de retomar CU-09.

## Resultado actual

POST /projects/import/xmi autenticado recibe XML crudo y crea un proyecto nuevo, con nuevo UUID/owner actual/revisión cero, modelo validado y layout vacío. No modifica el proyecto abierto ni importa ownership del archivo. API responde document/warnings; UI selecciona archivo, abre resultado y muestra advertencias. Exportación conserva acceso de lectura owner/editor/viewer.

Importador lxml.iterparse con límite 2 MiB, 50 000 nodos y 64 niveles; sin DTD, resolución de entidades ni acceso de red. XMI 2.1 con namespaces indicados abajo. IDs id_<UUID> propios se recuperan, externos se mapean por UUID5 determinista. Se rechazan duplicados, referencias rotas, multiplicidades inválidas y errores del validador UML (incluidos ciclos/autoherencia y nombres duplicados). Se mantienen UML/layout separados.

Subconjunto: clases, visibilidad, atributos, operaciones, parámetros in/return, tipos primitivos y referencias a clases, asociaciones binarias, agregación/composición, multiplicidades y autorrelaciones, generalizaciones independientes o anidadas. Paquetes se aplanan con aviso; extensiones/diagramas del proveedor no se importan y se advierte. Elementos empaquetados no soportados (por ejemplo Interface/Enumeration), modificadores abstract/static/readOnly/derived activos, tipos de datos estructurados, dirección out/inout y multiplicidad de atributos no representable se rechazan. Metadata/XML adicional genera aviso. No se obtienen recursos externos ni perfiles; referencias de tipo deben estar resueltas dentro del archivo.

Namespaces admitidos: XMI http://schema.omg.org/spec/XMI/2.1 y http://www.omg.org/XMI con versión 2.1; UML http://www.omg.org/spec/UML/20161101 y http://schema.omg.org/spec/UML/2.1. Elementos estructurales no calificados también se reconocen. No se promete importar cualquier dialecto de XMI.

Se corrigió _type_id del exportador: dict.get evaluaba primitive_ids[type_name] aun si el tipo era una clase; ahora resuelve explícitamente clase o primitivo. Round-trip semántico probado con clases y tipos de clase en atributos/parámetros/retorno. No se promete conservar orden XML/paquetes/layout/metadatos ajenos al modelo.

## Incrementos

1. Exportación: evidencia histórica al final.
2. Parser seguro, validador, corrección del exportador y round-trip: gate completo 270 backend/68 frontend PASS. Ajustes de Ruff en fixtures XML y gate repetido. Sin IA/benchmarks aplicables.
3. API/editor y endurecimiento: gate completo 273 backend/72 frontend PASS; posteriormente 275/73 PASS con rechazo de pérdida de propiedades y recuperación de listado. Gate final actual registrado abajo. Importar crea proyecto nuevo, no requiere permiso para editar el proyecto previamente abierto. Rechazo antes de persistir, fallos de almacenamiento 503 redactados, tipo HTTP no permitido 415 y tamaño 413. Parseo/persistencia en threadpool; lectura del body acotada antes del parseo.

## Pruebas y evidencia actual

Tests de adaptador: semántica/IDs/tipos y reexportación, IDs externos/paquetes/herencia anidada, Interface/duplicados/tipos desconocidos/ciclos/nombres duplicados/modificadores, DTD UTF-8/UTF-16, XML inválido/versión/tamaño/profundidad/nodos, extensiones, metadata adicional y multiplicidad de atributo. API: nuevo owner/UUID, proyecto original intacto, round-trip, autenticación/tipo/tamaño/422 y almacenamiento fallido sin proyecto ficticio. Frontend: bytes del archivo, límite antes de transmisión, apertura con avisos, rechazo conservando documento, importación guardada aunque refrescar lista falle. No se confunde este último fallo con una importación fallida que induciría duplicados.

Smoke HTTP TCP loopback con MongoMock temporal PASS: nuevo proyecto del usuario, original intacto, round-trip semántico rico e importación inválida sin escritura. Resultado artifacts/cu21/wire-result.json, 2026-11-07 13:13:51 Bolivia. Script artifacts/cu21/import-wire.py, servidor/datos temporales retirados. No se tocó Atlas ni datos reales. No equivale a prueba visual o EA real.

Prueba manual pendiente: abrir un proyecto, importar .xmi válido y confirmar nuevo proyecto/avisos; abrir el original y comprobar que sigue igual; reexportar y volver a importar; comprobar error con XML inválido; verificar con archivo y herramienta EA reales el subconjunto que se pretenda presentar. Aceptación visual/cloud diferida por el usuario; la prueba EA no está acreditada y no se declara por silencio.

## Continuidad

Se auditó requirements/LEGACY-GAPS.md: invitaciones/tokens/vencimiento de CU-09 y generación CU-13..17 siguen pendientes. No se amplió este CU para implementarlos. Mantener un CU de código a la vez. Rúbrica del primer parcial y RP-01..03 siguen pendientes, sin respuestas inventadas.

No se hizo commit/push. Archivos compartidos con cambios de otros CUs requieren stage de hunks, nunca stage amplio. Comandos de preparación revisables (no ejecutados), seleccionar solo hunks CU-21:

```powershell
git add -- backend/app/api/xmi_import.py backend/app/interoperability/xmi/importer.py backend/app/interoperability/xmi/exporter.py backend/tests/api/test_xmi_import.py backend/tests/interoperability/test_xmi_importer.py docs/puds/use-cases/CU-21-xmi-interoperability.md docs/requirements/LEGACY-GAPS.md
git add -p -- backend/app/main.py frontend/src/features/editor/editor-api.ts frontend/src/features/editor/editor-api.spec.ts frontend/src/features/editor/editor-store.ts frontend/src/features/editor/editor-store.spec.ts frontend/src/features/editor/EditorWorkspace.vue README.md docs/STATUS.md docs/TESTING.md docs/HANDOFF.md docs/PROJECT-CONTEXT.md docs/README.md docs/puds/use-cases/IMPLEMENTATION-ROADMAP.md
git diff --cached
git commit -m "feat(cu-21): import XMI 2.1 with semantic round-trip"
git push -u origin feat/xmi-export
```

Fuentes técnicas consultadas: [lxml iterparse](https://lxml.de/apidoc/lxml.etree.html#lxml.etree.iterparse), [XMI 2.1 OMG](https://www.omg.org/spec/XMI/2.1). No se sustituyeron tecnologías/dependencias.

---

# Evidencia histórica del incremento 1

**Estado:** IMPLEMENTED - exportacion; importacion y round-trip pendientes.

## Objetivo
Exportar el subconjunto UML canonico a XMI 2.1 interoperable, sin usar el canvas como fuente.

## Actor(es)
Owner, editor o viewer con acceso de lectura al proyecto.

## Dependencias
CU-04, CU-07, CU-08 y CU-09.

## Referencias a product.md
Secciones 3, 6, 7, 16 y 34.

## Alcance
Incluye exportacion XMI 2.1 con UML 20161101 de clases, atributos, operaciones, parametros, retornos, tipos primitivos, asociaciones, agregaciones, composiciones, generalizaciones, multiplicidades y autorrelaciones. Excluye importacion, perfiles y round-trip.

## Diseno y decisiones utilizadas
`app/interoperability/xmi/exporter.py` recibe un `ProjectDocument` y lee exclusivamente `uml_model`; `diagram_layout` no se serializa. Los identificadores XMI se derivan de UUIDs con prefijo seguro y los tipos primitivos se identifican de forma estable a partir de su nombre. La ruta protegida reutiliza `_project_access`, por lo que owner, editor y viewer pueden descargar sin conceder permisos de mutacion. El nombre de descarga se reduce a ASCII seguro antes de construir `Content-Disposition`.

## Implementacion realizada
- Se agrego `lxml==6.0.2` y el adaptador aislado de exportacion.
- Se agrego `GET /projects/{project_id}/export/xmi` con respuesta XML adjunta.
- Se agrego el boton `Descargar XMI` en la toolbar, usando `authenticatedFetch` mediante `downloadProjectXmi`.

## Pruebas automaticas
| Prueba/comando | Resultado | Evidencia/nota |
|---|---|---|
| `backend/.venv/Scripts/python.exe -m pytest` | PASS | 179 passed; cubre serializacion XMI y acceso owner/editor/viewer. |
| `backend/.venv/Scripts/python.exe -m ruff check app tests` | PASS | Sin hallazgos. |
| `npm test` | PASS | 46 pruebas Vitest verdes. |
| `npm run build` | PASS | Typecheck y build Vite completados. |

## Deuda tecnica y riesgos restantes
La importacion XMI con `iterparse` y el round-trip pertenecen al resto de CU-21 y no se adelantaron en este incremento.

## Criterios de aceptacion y evidencia
- [x] El XMI contiene namespaces XMI 2.1 y UML 20161101 con IDs deterministas.
- [x] La descarga requiere y respeta acceso de lectura.
- [x] El frontend descarga mediante el cliente autenticado.

## Estado final
Incremento de exportacion cerrado; CU-21 completo permanece abierto hasta implementar importacion y round-trip.

## Git histórico
No ejecutado. Los comandos de stage amplio originales no deben aplicarse ahora porque el árbol contiene cambios de otros CUs.
