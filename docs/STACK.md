# Stack base

Versiones seleccionadas el **2026-09-08**. Se priorizan versiones estables y el cumplimiento literal de `product.md`.

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
| PostgreSQL | 18.6 | flujo validado: instalación local Windows en `localhost:5432`; Docker opcional publica `55432 -> 5432` |

## Dependencias deliberadamente no instaladas todavía

Los paquetes pesados de IA/visión/STT (Transformers, PyTorch, Qwen, faster-whisper, Pillow/scikit-image, etc.) se incorporarán cuando su caso de uso lo requiera. Esto reduce tiempo de instalación, consumo de disco y ruido durante los primeros ciclos.

Flutter tampoco se incluye como proyecto base: será una salida generada futura.

## Actualizaciones

No ejecutar upgrades masivos durante un caso de uso. Si una actualización mayor es necesaria:

1. documentarla en `DECISIONS.md`;
2. ejecutar tests antes/después;
3. hacerla en un commit separado.
