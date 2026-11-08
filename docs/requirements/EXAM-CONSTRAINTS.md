# Restricciones del examen

`product.md` es la fuente de verdad. El segundo parcial se registra y traza en [SECOND-PARTIAL.md](SECOND-PARTIAL.md); el roadmap único vive en PUDS.

## Segundo parcial

- Conservar las exigencias del primer parcial; enunciado/rúbrica aún pendientes de aportar.
- Colaboración multiusuario remota y en tiempo real.
- IA grupal por solicitud, con contexto compartido, actividad atribuida, explicación, revisión, propuestas y resúmenes; sin conversaciones privadas.
- Entrada por voz y cambios autorizados difundidos a todos. La autorización de mutaciones por texto requiere aclaración RP-02.
- NoSQL en la nube y sesiones persistentes retomables. PostgreSQL/JSONB actual no prueba cumplimiento.
- IA cloud funcional; ejecución local opcional y valorable.
- Visor móvil de solo lectura UML con actualización realtime y notificaciones push verificadas.

## Decisiones conservadas

Vue 3/TypeScript/Vite y FastAPI no se reemplazan. Spring Boot sigue decidido para backend generado; la mención del docente sobre backend principal es permisiva. Flutter/Dart sigue siendo salida Android generada, diferente del visor CASE.

AWS sigue siendo destino de despliegue. Motor/proveedor/SDK NoSQL se eligen en CU-25; servicios de despliegue en CU-23; proveedor IA en CU-18 y cliente móvil/push en CU-28. No adelantar infraestructura ni contratos.

Offline/LAN conserva objetivo previo, pendiente de contrastar con primer parcial; no sustituye cloud obligatorio. PostgreSQL generado se conserva salvo aclaración explícita RP-03.

## Regla para agentes

Orden de lectura obligatorio: product.md → roadmap PUDS → CU activo si existe → PROJECT-CONTEXT → documentación específica (incluido SECOND-PARTIAL). Un CU a la vez, hasta tres incrementos, evidencia real y documentación actualizada. No declarar implementadas capacidades planeadas.
