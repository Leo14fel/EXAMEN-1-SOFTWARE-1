# Examen SW1 - Herramienta CASE colaborativa

Monorepo de la herramienta CASE definida en [`product.md`](product.md). El estado documentado está en [`docs/STATUS.md`](docs/STATUS.md). Los requisitos del segundo parcial y las dudas pendientes están en [`docs/requirements/SECOND-PARTIAL.md`](docs/requirements/SECOND-PARTIAL.md).

La persistencia normal es MongoDB Atlas. CU-25 trasladó y verificó 3 usuarios, 15 proyectos y 2 permisos; PostgreSQL original quedó intacto y respaldado. Se conservaron 13 proyectos legacy cuyo ownerId no corresponde a un usuario registrado, sin reasignarlos. Ver la [prueba NoSQL](docs/deployment/NOSQL-CU25.md). Ver el [roadmap único](docs/puds/use-cases/IMPLEMENTATION-ROADMAP.md).

CU-10 incorpora sincronización WebSocket con reconexión y deltas del diagrama. Pruebas locales aprobadas; comprobación Atlas y visual pendientes, sin despliegue nuevo. Detalles en [CU-10](docs/puds/use-cases/CU-10-realtime-collaboration.md).

CU-11 incorpora participantes/cursores/selección/edición efímeros; CU-26 añade conversación grupal y actividad con autor, historial y recuperación. Gates locales aprobados, sin IA ni despliegue nuevo; comprobación Atlas/visual diferida por autorización del usuario. Ver [CU-11](docs/puds/use-cases/CU-11-collaborative-presence.md) y [CU-26](docs/puds/use-cases/CU-26-group-session.md).

CU-21 incorpora **Importar XMI como proyecto nuevo**, validación del subconjunto UML y round-trip semántico con exportación. Conserva el proyecto anterior. Compatibilidad visual/EA real pendiente; detalles en [CU-21](docs/puds/use-cases/CU-21-xmi-interoperability.md).

CU-09 permite crear y cancelar invitaciones con código, correo y vencimiento desde Colaboradores; el destinatario usa **Canjear invitación** tras ingresar con el correo indicado. No se envían correos automáticamente. [Detalles](docs/puds/use-cases/CU-09-collaborators.md).

CU-13 añade **Modelo relacional** al editor: vista previa de tablas, columnas y claves, con diagnóstico de limitaciones y descarga JSON. Es la base de la generación posterior; no ejecuta SQL ni genera todavía la aplicación. [Detalles](docs/puds/use-cases/CU-13-relational-mapping.md).

## Requisitos

- Git.
- Node.js 24 y npm 11.
- Python 3.13 o superior.
- Acceso a MongoDB Atlas y variables Mongo configuradas en `backend/.env`.
- Docker Desktop y Docker Compose solo si se usara la alternativa reproducible.

## Instalacion

Desde la raiz, copie los ejemplos de variables si todavia no existen:

```powershell
Copy-Item .env.example .env
Copy-Item backend\.env.example backend\.env
Copy-Item frontend\.env.example frontend\.env
```

Instale el backend:

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

Instale el frontend en otra terminal:

```powershell
cd frontend
npm install
```

El lockfile `frontend/package-lock.json` debe conservarse. El backend se instala de forma reproducible con las versiones fijadas en `backend/pyproject.toml`.

## Desarrollo actual probado

El backend usa `PERSISTENCE_BACKEND=mongodb`, `MONGODB_URI` y `MONGODB_DATABASE` en `backend/.env` (ignorado por Git). No copie secretos al repositorio. El entorno actual está configurado y fue verificado sobre Atlas. Su usuario temporal dura una semana y el acceso IP autorizado seis horas; requieren renovación para uso duradero.

PostgreSQL local 17.6 se conserva como origen y recuperación legacy; no es necesario para ejecutar el editor en modo Mongo:

```text
host: localhost
port: 5432
database: examen_sw1
user: postgres
```

Para inspeccionar el origen legacy, use:

```powershell
psql -U postgres -h localhost -p 5432 -d examen_sw1
```

## Docker opcional

Docker no es requisito para desarrollar ni para ejecutar los checks. `compose.yaml` conserva la alternativa PostgreSQL legacy y publica el puerto host `55432` para no colisionar con PostgreSQL local; dentro del contenedor PostgreSQL sigue escuchando en `5432`.

```powershell
docker compose up -d db
docker compose ps
```

Para detenerlo:

```powershell
docker compose down
```

## Ejecucion

Inicie el backend desde `backend/`:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

Inicie el frontend desde `frontend/`:

```powershell
npm run dev
```

Tambien estan disponibles los scripts de PowerShell desde la raiz:

```powershell
.\scripts\setup.ps1
.\scripts\dev-backend.ps1
.\scripts\dev-frontend.ps1
.\scripts\check.ps1
```

`setup.ps1` instala las dependencias y crea los archivos `.env` faltantes; no inicia Docker.

## URLs

- Frontend: `http://localhost:5173`
- Backend: `http://localhost:8000`
- Swagger/OpenAPI: `http://localhost:8000/docs`
- Health general: `http://localhost:8000/health`
- Health del almacenamiento seleccionado: `http://localhost:8000/health/db`

`/health` no requiere conexión a la base. `/health/db` devuelve `503` cuando la infraestructura no esta disponible.

## Tests y checks

```powershell
cd frontend
npm run typecheck
npm test
npm run build
```

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
.\.venv\Scripts\python.exe -m compileall app
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pip check
```

Con backend iniciado, valide los endpoints:

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/health/db
```

## Problemas comunes

**Docker Desktop no esta iniciado:** no afecta el flujo local probado. Solo inicie Docker Desktop si desea usar `docker compose up -d db`.

**PostgreSQL 18 no inicia tras actualizar `compose.yaml`:** la configuracion anterior montaba el volumen en `/var/lib/postgresql/data`, incompatible con PostgreSQL 18. Para recrear solo la base local con el nuevo montaje, ejecute `docker compose down -v` y luego `docker compose up -d db`. El primer comando elimina los datos locales del volumen `postgres_data`.

**`/health/db` devuelve 503:** compruebe las variables Mongo locales, disponibilidad de Atlas, vigencia del usuario y acceso IP. Alembic y DATABASE_URL corresponden al origen SQL legacy. No cambie a SQL como recuperación después de nuevas escrituras Mongo sin congelar y reconciliar los cambios; consulte la guía CU-25.

**El frontend muestra "Backend: sin conexion":** inicie FastAPI en el puerto 8000 o ajuste `VITE_API_BASE_URL` en `frontend/.env`.
