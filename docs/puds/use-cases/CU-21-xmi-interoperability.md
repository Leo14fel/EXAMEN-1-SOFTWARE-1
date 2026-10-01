# CU-21 - Importar y exportar XMI

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

## Commit y push
No ejecutados por solicitud. Al cerrar: `git add backend frontend docs && git commit -m "feat(cu-21): export XMI 2.1" && git push -u origin feat/xmi-export`.
