# Revisar el proyecto en esta computadora

Esta modalidad usa los módulos de la aplicación con datos ficticios en memoria. No conecta con Atlas ni modifica los usuarios o diagramas reales. La franja amarilla identifica la prueba. Los datos se borran al reiniciar el servidor de prueba; actualizar el navegador no los borra.

## Iniciar

En PowerShell, desde la carpeta del proyecto:

```powershell
cd "C:\Users\Lenovo\Documents\cosas variadas\materias\software 1\examen 1 softwaren1"
.\scripts\dev-qa.ps1
```

Abrir http://localhost:5175. Si ya está abierto, no ejecutar nuevamente el inicio. El script avisa si los puertos están ocupados y no detiene otros procesos. Usa las dependencias ya instaladas en esta computadora.

## Cuentas ficticias

Todas usan la contraseña `Prueba1234!`.

| Cuenta | Permiso |
| --- | --- |
| owner@prueba.local | Propietario |
| editor@prueba.local | Editor |
| viewer@prueba.local | Observador |

## Recorrido de unos diez minutos

1. Ingresar como propietario y abrir **Prueba local - Cliente y Pedido**. Anotar el identificador del proyecto para distinguirlo de copias importadas.
2. Mover una clase, agregar un atributo o método y probar deshacer/rehacer. Actualizar el navegador y comprobar el resultado.
3. Abrir **Modelo relacional**: revisar tablas, claves y avisos. Modificar el diagrama y actualizar esa vista; descargar el JSON si se desea.
4. Abrir una ventana privada del navegador e ingresar como editor. Abrir el mismo proyecto original. Hacer un cambio y enviar un mensaje al grupo: ambos usuarios deben verlos sin recargar. Comprobar también la presencia de los participantes. Usar una ventana privada u otro navegador para mantener cuentas distintas; dos pestañas normales comparten la sesión.
5. Cerrar sesión en la ventana privada e ingresar como observador. Debe ver los cambios y el historial compartido, con edición restringida.
6. Como propietario, exportar XMI e importarlo como proyecto nuevo. Comprobar las clases y relaciones y que el original siga existiendo. La importación conserva el UML soportado; no traslada permisos, conversación, perfil de generación ni distribución visual. Revisar los avisos mostrados.

Anotar qué paso falla, qué cuenta se usó y qué apareció en pantalla. La prueba visual queda pendiente hasta realizar este recorrido. IA, voz, aplicación móvil y generación de aplicaciones aún no forman parte de esta demostración.

## Detener

```powershell
.\scripts\stop-qa.ps1
```

El script comprueba la identidad de los procesos registrados antes de detenerlos. Reiniciar esta modalidad crea nuevamente los datos ficticios. Esto no acredita persistencia en Atlas ni después de reiniciar un servidor real.

La dirección localhost funciona en esta computadora, no desde el celular.

## Revisión posterior del formulario IA

### Vista actualizada independiente — 2026-11-07

Se dejó activa una instancia nueva en http://localhost:5176, API 8002. Conserva la anterior 5175/8001 sin reiniciarla. Tiene sus propios fixtures temporales: entrar como owner@prueba.local con Prueba1234!, abrir «Prueba local - Cliente y Pedido» y revisar el formulario de evaluación junto a la conversación. El puerto nuevo tiene una sesión de navegador separada.

Esta vista se inicia expresamente sin clave de proveedor, aunque se agregue después al archivo .env; permite revisar el estado pendiente y envío deshabilitado sin consumir cuota. No es Atlas ni una demostración de inferencia. Los datos se pierden cuando se detiene su backend. Para la prueba real se debe iniciar una instancia configurada según GEMINI-CU18.md.

Verificación HTTP: login, CORS, frontend apuntando a 8002 y status configured=false PASS; no se inspeccionó visualmente por fallo del runtime de control de navegador. Recibo local artifacts/cu18/preview-readiness.json. Para detener solo esta nueva vista, desde la raíz del proyecto ejecutar `.\artifacts\cu18\stop-preview.ps1`; valida PID/fecha/comando propios. No usar stop-qa.ps1 para detenerla, porque ese comando corresponde a la prueba anterior.

El código nuevo añade «Evaluar una solicitud con IA» junto al grupo. El backend de prueba que ya estaba abierto no se reinició: antes de actualizarlo exportar los diagramas temporales que se quieran conservar; reiniciar QA recrea los fixtures. En una instancia actualizada sin clave, comprobar aviso de configuración y envío deshabilitado, sin respuestas ficticias.

Después de configurar la clave y verificar proveedor/benchmark, probar editor/observador, visibilidad común de petición/respuesta, revisión obsoleta y «Consultar resultado» tras red incierta. La propuesta no debe modificar UML ni ofrecer aplicar por texto. Esta revisión humana sigue pendiente. Preparación privada de clave: [guía](deployment/GEMINI-CU18.md).
