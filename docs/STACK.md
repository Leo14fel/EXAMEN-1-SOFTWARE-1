# Stack base

Versiones seleccionadas el **2026-09-08**. Se priorizan versiones estables y el cumplimiento literal de `product.md`.

## Objetivo actualizado del segundo parcial

El cuadro de versiones de abajo describe las dependencias existentes, no el destino final de persistencia. FastAPI y Vue se conservan. NoSQL cloud pasa a ser destino CASE: CU-25 selecciona MongoDB Atlas sobre AWS y PyMongo 4.19.0; el driver está instalado y las rutas existentes pueden operar con MongoDB seleccionando PERSISTENCE_BACKEND=mongodb; el modo por defecto es MongoDB tras migración y recuperación verificadas. SQLAlchemy/Alembic/PostgreSQL se conservan para origen/recuperación legacy; PostgreSQL del backend generado permanece. IA de texto cloud se selecciona en CU-18; Qwen3 local queda opcional. Cliente móvil CASE/push se decide en CU-28 y no se confunde con Flutter CRUD generado.

## Frontend web

| Tecnología | Versión base | Nota |
|---|---:|---|
| Vue | 3.5.42 | estable |
| Vite | 8.2.2 | estable |
| Vuetify | 3.13.3 | última línea estable **v3**, porque `product.md` exige Vuetify 3 |
| Pinia | 4.0.3 | estable |
| @vue-flow/core | 1.48.2 | preparada para el canvas futuro |
| d3-dag | 1.2.2 | preparado para auto-layout futuro |
| @mdi/font | 7.4.47 | iconografía definida por el producto |
| TypeScript | 5.9.3 | compatible con Vue TSC |
| Vitest | 4.1.10 | pruebas frontend |
| Vue Test Utils | 2.5.0 | pruebas de componentes |

## Backend

| Tecnología | Versión base | Nota |
|---|---:|---|
| Python | 3.13+ | requisito del producto |
| FastAPI | 0.141.1 | estable |
| SQLAlchemy | 2.0.52 | estable |
| Alembic | 1.19.2 | estable |
| Pydantic | 2.13.5 | estable |
| pydantic-settings | 2.15.0 | carga reproducible de `backend/.env` |
| PyJWT | 2.13.0 | autenticación futura |
| pwdlib | 0.3.1 | hashing futuro |
| PostgreSQL legacy | 17.6 local / 18.6 imagen Compose | origen Windows en `localhost:5432`, respaldo/restauración aislada verificados; Docker opcional `55432 -> 5432` |

PyMongo 4.19.0 es dependencia nueva fijada en backend/pyproject.toml; dnspython 2.9.2 fue la dependencia resuelta en esta ejecución. Ver ADR-lite 023 y docs/deployment/NOSQL-CU25.md.

## Dependencias deliberadamente no instaladas todavía

Los paquetes pesados de IA/visión/STT (Transformers, PyTorch, Qwen, faster-whisper, Pillow/scikit-image, etc.) se incorporarán cuando su caso de uso lo requiera. Esto reduce tiempo de instalación, consumo de disco y ruido durante los primeros ciclos.

Flutter tampoco se incluye como proyecto base: será una salida generada futura.

## Actualizaciones

No ejecutar upgrades masivos durante un caso de uso. Si una actualización mayor es necesaria:

1. documentarla en `DECISIONS.md`;
2. ejecutar tests antes/después;
3. hacerla en un commit separado.

MongoMock 4.3.0 es dependencia de desarrollo añadida en CU-25 para pruebas sin red. Las siete pruebas de API también se ejecutaron contra Atlas real; no se confunde el mock con el servidor.
