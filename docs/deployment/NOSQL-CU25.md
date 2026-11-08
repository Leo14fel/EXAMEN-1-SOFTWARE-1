# CU-25: operación MongoDB y recuperación

## Estado verificado

CU-25 DONE. FastAPI usa MongoDB Atlas por defecto, sin cambiar contratos HTTP ni frontend. PyMongo 4.19.0, Atlas Free sobre AWS São Paulo, servidor 8.0.37 observado. Se trasladaron 3 usuarios, 15 proyectos y 2 permisos; PostgreSQL 17.6 original quedó intacto. Trece proyectos ya tenían ownerId sin usuario registrado: se conservaron sin reasignarlos.

El entorno local tiene PERSISTENCE_BACKEND=mongodb y configuración Mongo en backend/.env, ignorado por Git. No compartir ese archivo. SQLAlchemy/Alembic y DATABASE_URL quedan para el origen/recuperación legacy, no son necesarios para ejecutar el editor Mongo.

## Acceso y ejecución

Base configurada: examen_sw1_cu25_probe; cluster cu25-pruebas. Usuario cu25_probe con readWrite solo en esa base/cluster, temporal por una semana. La IP actual /32 se autorizó por seis horas. Renovar estos accesos para operación duradera; no habilitar acceso global. La expiración del acceso no borra los datos. No se contrató un tier pago ni backups cloud.

Desde backend, con entorno virtual instalado:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --port 8000
curl.exe http://localhost:8000/health/db
```

La configuración interactiva inicial puede realizarse con `python -m app.db.mongo_configure --verify`, desde backend, introduciendo personalmente la contraseña oculta. Conserva configuración SQL/JWT; no pasar contraseñas en argumentos ni chat. Su base de configuración de prueba debe terminar en _cu25_probe. No ejecutarlo para sobrescribir una configuración vigente sin necesidad.

El backend se dejó iniciado en 127.0.0.1:8000 tras la prueba. Verificar si sigue activo antes de iniciar otro. Información de proceso y logs locales en artifacts/cu25; no detener procesos ajenos.

## Respaldo e importación realizados

Archivos privados e ignorados por Git:

- artifacts/cu25/postgres-20261107T020534Z.dump: pg_dump custom, 9590 bytes; pg_restore --list y restauración en base temporal con comparación íntegra PASS.
- artifacts/cu25/source-20261107T020534Z.json: snapshot con checksum, hashes de contraseñas y datos personales; conservar restringido, no publicar.
- artifacts/cu25/cutover-result.json: resultado final PASS del 2026-11-06 22:15:29 (Bolivia).

El origen se leyó en transacción REPEATABLE READ, READ ONLY. Se comprobó que no había cambiado antes/después del corte. Ensayo en colecciones UUID: 18 documentos insertados y segunda ejecución 0. Importación final: 18 documentos (permisos embebidos). Las colecciones de ensayo se retiraron; users/projects contienen los datos reales.

La CLI permite verificar sin modificar, desde backend:

```powershell
.\.venv\Scripts\python.exe -m app.db.mongo_migration inspect --backup ..\artifacts\cu25\source-20261107T020534Z.json
.\.venv\Scripts\python.exe -m app.db.mongo_migration verify --backup ..\artifacts\cu25\source-20261107T020534Z.json
.\.venv\Scripts\python.exe -m app.db.mongo_migration source-check --backup ..\artifacts\cu25\source-20261107T020534Z.json
```

verify compara contra el estado al corte: después de editar legítimamente un proyecto puede detectar diferencias esperadas. source-check comprueba solamente el origen SQL. export escribe un snapshot nuevo con nombre único dentro de artifacts/cu25; inspect/verify/source-check no importan. import valida todos los conflictos antes de insertar, omite registros idénticos y no sobrescribe los distintos. Puede reintentarse tras inserción parcial. No equivale a sincronización continua ni debe ejecutarse ciegamente después de nuevas ediciones.

## Recuperación comprobada y límites

Se verificaron autenticación/listados/lecturas/denegaciones para los tres usuarios y los quince proyectos. Se creó un proyecto de prueba, se reinició el backend completo y se recuperó su documento exacto desde Atlas. Comandos nuevos, Undo y Redo PASS; el historial anterior al reinicio sigue efímero como antes. Se borró solo ese proyecto temporal y se compararon nuevamente todos los registros migrados. SQL original permaneció idéntico.

Si ocurre una falla, conservar origen, destino y respaldos. Tras nuevas escrituras Mongo, congelar y reconciliar esos cambios antes de volver a SQL: cambiar solamente el selector perdería avances. Restaurar el archivo SQL primero en una base aislada y comprobar su contenido, como se hizo en esta prueba; no sobrescribir la base original. No se implementó exportación inversa Mongo→SQL ni backup cloud automático en CU-25.

## Verificación técnica

Gate scripts/check.ps1: 235 backend, 46 frontend, Ruff/compileall/pip check/typecheck/build PASS. Dos advertencias externas y advertencia existente del tamaño de chunk Vite. Detalles en documento del CU.

Las pruebas de almacenamiento locales usan MongoMock, que no demuestra disponibilidad cloud. Siete escenarios API se ejecutaron también sobre Atlas con CU25_LIVE_TESTS=1: usan colecciones únicas cu25_<UUID>_ y limpian exclusivamente esas colecciones. No borrar users/projects para repetirlas. La prueba mongo_probe crea/retira solo su UUID; verifica documento no vacío, CAS, revisión obsoleta, dos clientes concurrentes y recuperación con cliente nuevo.

compose.mongo-probe.yaml ofrece MongoDB local opcional en 127.0.0.1:27025, separado del Compose SQL. Se validó su configuración; no se afirma ejecución real de Docker. La evidencia real de servidor corresponde a Atlas.

UUIDs como strings y fechas ISO conservan microsegundos; semántica/layout siguen separados. _memberships es privado del almacenamiento. CAS comprueba revisión, identidad y permiso actual en la misma escritura reconocida. BSON mayor de 16 MiB se rechaza con 413 y fallos de almacenamiento se redactan en 503. La persistencia de conversación/actividad y la colaboración realtime corresponden a los siguientes CUs, no se declaran implementadas aquí.
