# Registro de decisiones

## ADR-lite 001 — Monorepo con dos proyectos base

**Estado:** aceptada

La fundación contiene `frontend/` y `backend/` en la raíz para mantener el repositorio simple y fácil de navegar.

## ADR-lite 002 — Vue permanece como frontend web

**Estado:** aceptada

Flutter no reemplaza Vue. Flutter corresponde únicamente a la salida móvil Android generada definida por el producto.

## ADR-lite 003 — Dependencias de IA diferidas

**Estado:** aceptada

No se instalan modelos/runtime pesados en la fundación. Se agregarán cuando exista un CU que los necesite.

## ADR-lite 004 — PostgreSQL mediante Docker en desarrollo

**Estado:** aceptada

Se usa Docker Compose para reducir diferencias de instalación local y facilitar pruebas reproducibles.
