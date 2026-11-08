# Preparar la clave de Gemini para CU-18

La integración preparada usa Gemini Developer API desde el backend. Solicitudes grupales y formulario ya tienen código y pruebas controladas, pero faltan llamada/benchmark reales y aceptación visual/cloud. Este procedimiento no implica migrar el backend ni contratar un servicio.

## Clave personal

1. Abrir [Google AI Studio: claves de API](https://aistudio.google.com/api-keys), iniciar sesión personalmente y crear una clave en una cuenta/proyecto propio. Revisar disponibilidad y cuota que muestre la cuenta; no se presupone gratuidad ni facturación habilitada.
2. En PowerShell ejecutar:

```powershell
cd "C:\Users\Lenovo\Documents\cosas variadas\materias\software 1\examen 1 softwaren1\backend"
.\.venv\Scripts\python.exe -m app.ai.configure
```

3. Introducir la clave en el campo oculto y pulsar Enter. No enviarla al chat, incluirla en capturas ni pasarla como argumento del comando. El script guarda únicamente GEMINI_API_KEY en backend/.env, conservando la configuración de MongoDB, SQL y autenticación. Ese archivo está excluido de Git.

El formato se valida localmente; guardar la clave no comprueba que el proveedor la acepte. Una clave rechazada, cuota agotada o modelo no disponible se registrarán como fallo del proveedor durante la prueba, sin exponer su contenido.

El servidor lee la configuración al iniciar: reiniciarlo después de guardar la clave. Si se está usando scripts/dev-qa.ps1, detener/iniciar esa modalidad borra sus datos temporales; guardar antes los diagramas que se quieran conservar. El servidor QA que ya estaba abierto no fue reiniciado automáticamente. La disponibilidad mostrada solo confirma configuración, no la validez de la clave.

El formulario «Evaluar una solicitud con IA» está junto a la conversación: requiere editor, conexión sincronizada y clave configurada. Registra solicitud/resultado para el grupo y no aplica cambios por texto. Ante un fallo de red usar «Consultar resultado»; no es necesario crear otra solicitud ni repetir la llamada al proveedor.

## Pruebas antes de aceptar IA

Sin credenciales se puede ejecutar:

```powershell
.\.venv\Scripts\python.exe -m app.ai.benchmark --fixtures-only
```

Esto valida los 12 fixtures y registra NOT_RUN, cero solicitudes y métricas LLM null. No equivale a inferencia ni a un benchmark de calidad aprobado.

Con la clave ya configurada, el runner sin ese flag realiza 24 solicitudes: los mismos 12 casos con temperaturas 0 y 0.2. Consume la cuota del proveedor. No modifica diagramas ni ejecuta los comandos propuestos. Deben revisarse los resultados reales antes de aceptar CU-18 y de considerar elegido el modelo candidato.

Los recibos se guardan en artifacts/cu18, excluidos de Git. Registran prompt, dataset/hash, commit/estado del árbol, hashes de implementación, hardware cliente cuando disponible y la versión del modelo/tokens que informe el proveedor. El hardware remoto y picos RAM/VRAM no se conocen y no deben inventarse.

Las mutaciones por texto siguen deshabilitadas por la aclaración RP-02. Voz requiere CU-19 y asesoría/resúmenes CU-27; introducir la clave no implementa automáticamente esos casos.
