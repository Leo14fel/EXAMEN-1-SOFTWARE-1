# Contexto de continuidad del proyecto

## Uso
Este archivo debe acompañar un ZIP/snapshot actualizado del repositorio cuando se cambie de chat. El estado real se obtiene del código y la documentación del ZIP, no de recuerdos previos.

## Producto
Herramienta CASE colaborativa y offline-first para modelado UML de clases. Mantiene una representación canónica y desde ella genera artefactos/aplicaciones. Incluye edición manual, texto, voz, imagen e interoperabilidad XMI según `product.md`.

## Stack fijado
### Aplicación principal
- Vue 3 + TypeScript + Vite
- Vuetify 3
- `@vue-flow/core`
- d3-dag
- Pinia
- Python 3.13+ + FastAPI
- SQLAlchemy 2.0 + Alembic + PostgreSQL
- WebSockets de FastAPI

### Generación
- Jinja2
- backend generado: Java 21 + Spring Boot 4.x + Gradle + Spring Data JPA/Hibernate + PostgreSQL
- mobile generado: Flutter + Dart para Android
- OpenAPI, Postman y Domain Manifest según `product.md`

### IA / interoperabilidad
- Qwen3 1.7B Instruct local para texto
- Qwen2.5-VL 3B Instruct local para imagen → UML
- Hugging Face Transformers + PyTorch
- faster-whisper sobre CTranslate2
- XMI 2.1 / Enterprise Architect como objetivo de interoperabilidad

## Flutter
Flutter NO reemplaza el frontend web principal. Vue es la herramienta CASE web; Flutter es únicamente la salida móvil generada.

## Flujo acordado por CU
1. Usuario pide plan de CU-X.
2. Asistente explica objetivo, dependencias, alcance, decisiones ya fijadas, pruebas y documentación.
3. Si es grande, se divide en máximo 3 incrementos.
4. Usuario aprueba el plan.
5. Asistente entrega prompt detallado para el agente.
6. Agente modifica código/docs.
7. Usuario corre tests y pruebas manuales.
8. Se corrigen UI, tests, fallos y ajustes; cada iteración actualiza la doc del CU cuando corresponda.
9. Se repite hasta aceptación.
10. Se cierra el documento `CU-XX-<slug>.md` con evidencia real.
11. Asistente entrega comandos de commit/push.
12. Se pasa al siguiente CU.

No generar el prompt de implementación antes de la aprobación del plan.

## Documentación por CU
Cada CU real vive en `docs/puds/use-cases/CU-XX-<slug>.md` e incluye objetivo, actores, dependencias, alcance/fuera de alcance, plan aprobado, incrementos, diseño usado, implementación, archivos afectados, pruebas, resultados, fallos/correcciones, benchmarks, documentación, deuda, aceptación y comandos Git.

La documentación final se reutilizará para el informe académico y debe coincidir al 100% con la implementación.

## Benchmarks
Viven en `docs/benchmarks/`. Nunca inventar accuracy, latencia o uso de recursos. Registrar resultados de ejecuciones reales y preservar comparaciones.

## CU-00
Es una excepción técnica de fundación: monorepo/repo, frontend y backend mínimos, health, integración frontend → backend, `.gitignore`, configuración, tests mínimos y documentación. No adelanta UML.

## Punto pendiente detectado
El `product.md` adjunto usado para crear este contexto no contiene una especificación AWS. Si AWS es requisito del docente, debe añadirse primero a `product.md` como requisito/decisión aprobada antes de derivar un CU de despliegue. No inventar servicios AWS desde este contexto.
