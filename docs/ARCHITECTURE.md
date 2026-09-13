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
- PostgreSQL local de Windows validado en `localhost:5432/examen_sw1`.
- Docker Compose como alternativa reproducible opcional en `localhost:55432` hacia `5432` dentro del contenedor.

## Dominio UML base

```text
ProjectDocument
├── id, metadata, ownerId, revision, createdAt, updatedAt
├── umlModel: CanonicalUmlModel
└── diagramLayout: DiagramLayout
```

`CanonicalUmlModel` es la fuente semántica canónica y conserva elementos UML identificados. `DiagramLayout` contiene exclusivamente posiciones y tamaños visuales asociados a esos UUIDs. El layout no es fuente de verdad y no contiene semántica UML.

Las entradas futuras manual, texto, voz, imagen y XMI deberán producir o modificar el modelo canónico mediante los mecanismos definidos por el roadmap; esos adaptadores no están implementados todavía.

## Regla de evolución

No crear arquitectura para una capacidad futura hasta que un caso de uso aprobado la necesite.
