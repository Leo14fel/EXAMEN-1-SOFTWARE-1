# Despliegue AWS

## Estado

**No implementado en la fundación.**

El examen requiere despliegue en AWS. Esta capacidad se trabajará en su propio caso de uso/ciclo para no mezclar infraestructura con la construcción inicial del dominio.

## Alcance mínimo esperado cuando llegue el CU

- frontend web Vue desplegable en AWS;
- backend FastAPI desplegable en AWS;
- PostgreSQL accesible desde el backend desplegado;
- variables/secretos fuera del código;
- procedimiento de despliegue documentado;
- smoke test posterior al despliegue.

## Decisiones pendientes

La selección exacta de servicios (por ejemplo, hosting del frontend, ejecución del backend y PostgreSQL administrado) se decidirá en el CU de despliegue según costo, restricciones académicas y simplicidad.

## Restricción

AWS no debe borrar la capacidad local/offline definida en `product.md`.
