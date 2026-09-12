# CU-00 - Project Foundation / Fundacion del proyecto

**Estado:** DONE

## 1. Objetivo

Establecer un monorepo ejecutable que demuestre Vue -> HTTP -> FastAPI mediante `GET /health`, con PostgreSQL y Alembic preparados sin entidades de dominio.

## 2. Actor(es) y dependencias

- Actor: equipo de desarrollo.
- Dependencias: ninguna.
- Referencia: [`/product.md`](../../../product.md), secciones 4, 5, 20, 34 y 39.

## 3. Alcance realizado

- Monorepo con `frontend/`, `backend/`, `docs/` y `scripts/`.
- Vue 3, TypeScript, Vite, Vuetify 3, Pinia, Vue Flow y d3-dag preparados sin canvas UML.
- FastAPI, Pydantic 2, SQLAlchemy 2, Alembic y PostgreSQL preparados sin modelos de dominio.
- `GET /health`, `GET /health/db`, CORS de desarrollo, ejemplos de variables, tests y scripts PowerShell.

No incluye UML, ProjectDocument, canvas, auth, persistencia de proyectos, WebSockets, IA, XMI, generadores, Flutter, Android ni AWS.

## 4. Configuracion PostgreSQL real

El desarrollo validado finalmente usa PostgreSQL local de Windows:

```text
host: localhost
port: 5432
database: examen_sw1
user: postgres
```

El backend usa `localhost:5432/examen_sw1`. Docker Compose se conserva solo como alternativa reproducible: publica `55432` en el host para evitar colisionar con PostgreSQL local y mantiene `5432` dentro del contenedor. Docker no es requisito para desarrollar.

## 5. Incidentes y decisiones

- La imagen Docker `postgres:18.6-alpine` falló inicialmente porque el volumen heredado se montaba en `/var/lib/postgresql/data`; PostgreSQL 18 requiere el volumen en `/var/lib/postgresql`. `compose.yaml` se corrigió.
- La diferencia de puertos entre PostgreSQL local y Docker podía causar colisión. La decisión final es usar `5432` para desarrollo local validado y `55432 -> 5432` únicamente para Docker opcional.
- `vue-tsc` no era compatible con TypeScript 7; se fijó TypeScript 5.9.3.
- Los tests Vue registran ahora el plugin real de Vuetify en `frontend/src/test/setup.ts`, reutilizable por todas las pruebas Vitest. Esto resuelve los componentes Vuetify sin filtros de consola ni stubs.

## 6. Evidencia verificada

| Prueba/comando | Resultado |
|---|---|
| `GET /health` | 200, `{"status":"ok","service":"backend"}` |
| `GET /health/db` | 200, `{"status":"ok","database":"postgresql"}` |
| `psql -U postgres -h localhost -p 5432 -d examen_sw1` | Base local `examen_sw1` verificada. |
| `alembic check` | `No new upgrade operations detected.` |
| `pytest` | 2 passed. |
| `npm run typecheck` | OK. |
| `npm test` | 2 passed; sin warnings de resolucion de componentes Vuetify. |
| `npm run build` | OK. |
| Integracion Vue -> FastAPI | Verificada manualmente: la UI muestra que el backend esta conectado. |
| `scripts/check.ps1` | `Todos los checks terminaron correctamente.` |

## 7. Estructura final

```text
backend/    FastAPI, SQLAlchemy, Alembic y pruebas
frontend/   Vue, Vuetify, Vitest y pruebas
scripts/    setup, arranque y checks PowerShell
product.md  fuente de verdad unica del producto
compose.yaml alternativa PostgreSQL Docker opcional
```

## 8. Deuda tecnica

`pytest` puede emitir `StarletteDeprecationWarning` y un `DeprecationWarning` de AnyIO originados en FastAPI/Starlette. No proceden de código propio y no bloquean CU-00; se revisarán al justificar una actualización de esas dependencias.

## 9. Criterios de aceptacion

- [x] Monorepo con frontend y backend en raiz.
- [x] Stack de fundacion preparado sin adelantar CU-01.
- [x] `GET /health` responde 200 sin depender de PostgreSQL.
- [x] `GET /health/db` responde 200 contra PostgreSQL local validado.
- [x] Alembic valida que no hay operaciones pendientes.
- [x] Integracion visual Vue -> FastAPI verificada.
- [x] Tests, typecheck, build, compilacion y Ruff aplicables en verde.
- [x] Documentacion, variables ejemplo y alternativas de base sincronizadas.

## 10. Commit y push sugeridos

```powershell
git add .env.example README.md backend/.env.example compose.yaml docs frontend scripts product.md
git add -u
git commit -m "chore(cu-00): close project foundation"
git push -u origin main
```

No se ejecutaron commit ni push.
