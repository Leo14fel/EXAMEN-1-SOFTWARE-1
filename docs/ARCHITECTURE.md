# Arquitectura inicial

## Alcance de esta fundación

```text
Monorepo
├── frontend/  -> herramienta CASE web
├── backend/   -> API de la herramienta CASE
└── docs/      -> especificación y estado
```

No se implementan todavía:

- dominio UML completo;
- colaboración realtime;
- IA/STT;
- importación XMI;
- generadores Spring Boot;
- generador Flutter;
- infraestructura AWS.

## Aplicación principal

```text
Vue 3 + TypeScript
        |
        | HTTP / WebSocket (futuro)
        v
FastAPI + Python
        |
        v
PostgreSQL
```

## Salidas futuras definidas por el producto

```text
CanonicalUmlModel
       |
       +--> Backend generado: Java 21 + Spring Boot
       |
       +--> Mobile generado: Flutter + Dart -> Android
```

La aplicación Flutter generada no debe confundirse con el frontend web Vue del producto principal.

## Base incluida hoy

- `GET /health` en FastAPI, independiente de PostgreSQL.
- `GET /health/db` para verificar FastAPI -> SQLAlchemy -> PostgreSQL.
- configuración central mínima;
- capa de sesión SQLAlchemy preparada;
- Alembic preparado, sin migraciones de dominio;
- Vue/Vuetify/Pinia preparados;
- Vue Flow y d3-dag instalados pero sin inventar el editor UML;
- smoke test frontend;
- smoke test backend;
- PostgreSQL local mediante Docker Compose y variables de entorno.

## Regla de evolución

No crear arquitectura para una capacidad futura hasta que un caso de uso aprobado la necesite.
