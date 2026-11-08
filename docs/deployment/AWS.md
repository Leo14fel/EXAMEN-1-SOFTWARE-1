# Despliegue AWS

## Estado

Planificado en CU-23; no implementado. Ver roadmap PUDS para dependencias actuales, incluida persistencia NoSQL de CU-25 y capacidades grupales.

## Alcance objetivo

Frontend Vue, backend FastAPI, NoSQL cloud, WebSockets, integración IA cloud, secretos externos, configuración reproducible, procedimiento de operación/recuperación y smoke tests remotos. CU-25 selecciona MongoDB Atlas sobre AWS con PyMongo (prueba cloud aún pendiente); los demás servicios se deciden aquí sin anticipar infraestructura.

Verificar dos clientes remotos autorizados, reconexión y recuperación de sesión/contexto persistente. CU-28 integra y revalida visor móvil y push con evidencia en dispositivo. El backend PostgreSQL generado es una salida independiente, no la base CASE cloud objetivo.

## Límites

No se despliega ni se contrata infraestructura durante la preparación documental. Offline/LAN sigue como objetivo previo pendiente del enunciado del primer parcial; no sustituye el escenario cloud. No versionar secretos ni anunciar smoke tests sin ejecutarlos.
