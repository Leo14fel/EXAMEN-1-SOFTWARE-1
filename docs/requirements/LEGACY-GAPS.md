# Pendientes antiguos auditados

Fecha: 2026-11-07. Fuente: product.md, roadmap PUDS, documentos CU y archivos actuales. El usuario pidió completar las funciones antiguas. Esta lista es trazabilidad, no un roadmap alternativo ni la rúbrica del primer parcial (RP-01 sigue sin recibirse).

| Función | Evidencia actual | Tratamiento |
|---|---|---|
| Diagramación manual, atributos/métodos, relaciones, Undo/Redo | CU-01..07 y sus pruebas existentes | Conservar regresión; no reescribir funciones ya existentes |
| Registro/login, ownership, colaboradores EDITOR/VIEWER | CU-08/09 y API actual | Implementados; pruebas humanas anteriores pendientes |
| Invitaciones, token y vencimiento | CU-09 los implementó al reanudarse: token de un uso, correo, 1..168 h y cancelación atómica | Gate local 282 backend/80 frontend; QA visual/cloud pendiente |
| Importar XMI y vuelta exportar/importar | Faltaban en CU-21, exportación ya existía | Implementados ahora para el subconjunto canónico; QA visual/EA real pendiente |
| Tipos de clase en exportación XMI | _type_id evaluaba un default inexistente y podía lanzar KeyError | Corregido y probado con atributos/parámetros/retornos que referencian otra clase |
| Generación relacional/backend/OpenAPI/Postman/Manifest/Flutter | CU-13 implementó mapper/modelo relacional y vista previa; CU-14..17 siguen pendientes | Continuar por CU-14 y dependencias; no hay aún aplicaciones Spring/Flutter generadas |
| Importación desde imagen | CU-22 pendiente | Requiere VLM/benchmark real; no reemplazar por reconocimiento simulado |
| IA texto/voz/asistente generado | CU-18/19/20 pendientes | Proveedor/credencial y benchmarks; texto a mutación sigue bajo RP-02 |
| Enterprise Architect | Objetivo de CU-21 | Falta archivo/evidencia real de EA; los tests XML sintéticos no acreditan interoperabilidad completa |
| Offline/LAN y primer parcial completo | CU-12/24, RP-01 | Conservar alcance y esperar rúbrica para aceptación integral; no confundir pruebas locales con cloud |

Las comprobaciones Atlas/visuales de CU-10/11/26 siguen diferidas por instrucción explícita del usuario. No se considera aprobada la aceptación de producto completo. Se mantiene un CU activo a la vez; los pasos concretos y dependencias siguen en IMPLEMENTATION-ROADMAP.md.
