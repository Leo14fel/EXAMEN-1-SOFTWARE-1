# Restricciones del examen

Este documento registra restricciones que deben mantenerse explícitas durante el desarrollo.

## Frontend principal

- La herramienta CASE principal mantiene el frontend web definido en `product.md`: **Vue 3 + TypeScript + Vite**.
- Flutter **no reemplaza** este frontend web.

## Mobile

- La salida móvil Android generada deberá utilizar **Flutter + Dart**.
- No se crea una aplicación Flutter base en esta fundación porque esa salida pertenece a un caso de uso posterior de generación.

## AWS

- La solución deberá poder desplegarse en **AWS**.
- El requisito también está incorporado en `/product.md`; este documento no es una fuente alternativa de producto.
- La selección concreta de servicios AWS se documentará y decidirá cuando llegue el caso de uso de despliegue, evitando introducir infraestructura prematuramente.
- El despliegue cloud no debe borrar el requisito de capacidades esenciales locales/offline indicado en `product.md`.

## Regla para agentes

Antes de implementar un caso de uso, el agente debe revisar:

1. `/product.md`;
2. este documento;
3. el archivo específico del caso de uso;
4. `docs/STATUS.md`.

El agente no debe sustituir tecnologías ya decididas ni adelantar funcionalidades de casos futuros.
