# Examen SW1 - Project Foundation

Monorepo de la herramienta CASE definida en [`product.md`](product.md). CU-00 contiene solo la fundacion tecnica: una aplicacion Vue que consulta el health de una API FastAPI.

## Requisitos

- Git.
- Node.js 24 y npm 11.
- Python 3.13 o superior.
- PostgreSQL local de Windows para el desarrollo probado.
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

El desarrollo validado usa PostgreSQL local de Windows:

```text
host: localhost
port: 5432
database: examen_sw1
user: postgres
```

`backend/.env` no se versiona. Creelo desde `backend/.env.example`, que contiene la URL local sin secretos reales. Verifique que la base exista con:

```powershell
psql -U postgres -h localhost -p 5432 -d examen_sw1
```

## Docker opcional

Docker no es requisito para desarrollar ni para ejecutar los checks. `compose.yaml` es una alternativa reproducible y publica el puerto host `55432` para no colisionar con PostgreSQL local; dentro del contenedor PostgreSQL sigue escuchando en `5432`.

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
- Health PostgreSQL: `http://localhost:8000/health/db`

`/health` no requiere PostgreSQL. `/health/db` devuelve `503` cuando la infraestructura no esta disponible.

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
.\.venv\Scripts\python.exe -m alembic check
```

Con backend iniciado, valide los endpoints:

```powershell
curl.exe http://localhost:8000/health
curl.exe http://localhost:8000/health/db
```

## Problemas comunes

**Docker Desktop no esta iniciado:** no afecta el flujo local probado. Solo inicie Docker Desktop si desea usar `docker compose up -d db`.

**PostgreSQL 18 no inicia tras actualizar `compose.yaml`:** la configuracion anterior montaba el volumen en `/var/lib/postgresql/data`, incompatible con PostgreSQL 18. Para recrear solo la base local con el nuevo montaje, ejecute `docker compose down -v` y luego `docker compose up -d db`. El primer comando elimina los datos locales del volumen `postgres_data`.

**`/health/db` devuelve 503:** confirme que PostgreSQL local este activo y que `DATABASE_URL` en `backend/.env` use `localhost:5432/examen_sw1`. Si usa Docker, use `localhost:55432/examen_sw1` y confirme `docker compose ps`.

**El frontend muestra "Backend: sin conexion":** inicie FastAPI en el puerto 8000 o ajuste `VITE_API_BASE_URL` en `frontend/.env`.
