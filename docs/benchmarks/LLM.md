# Benchmark LLM — Texto → intención/comando

## Se usa en
CU-18 y cualquier cambio posterior de modelo, prompt, esquema o parámetros.

## Configuración vigente según producto
Proveedor cloud preparado en CU-18: Gemini REST, modelo candidato gemini-3.5-flash-lite. La selección por calidad/coste requiere evaluación real; no se declara medida. Qwen3 1.7B local con Transformers/PyTorch queda opcional según product.md, que prevalece sobre el baseline local histórico de este documento.

Dataset congelado inicial: cu18-cases.json (12 casos). Runner: desde backend, `.\.venv\Scripts\python.exe -m app.ai.benchmark --fixtures-only` valida fixtures y genera un recibo NOT_RUN con métricas LLM null. Sin ese flag y con GEMINI_API_KEY configurada evalúa temperaturas 0 y 0.2 sobre los mismos casos. No son dos modelos ni una medición ya ejecutada. No escribe ni aplica comandos al proyecto.

El usuario aún no tiene clave: inferencia/benchmark cloud pendientes; no inventar métricas ni aceptar CU-18 por respuestas controladas en tests. Evidencia y límites en el documento de CU.

## Dataset sugerido
Casos etiquetados: crear/renombrar/eliminar clase; agregar/quitar/modificar atributo; asociaciones; multiplicidad; referencias ambiguas; comandos incompletos; fuera de allow-list; intento de SQL/código/URL; destructivos; español informal; mezcla español/inglés; mensajes irrelevantes.

Cada fixture debe contener entrada, estado previo si aplica y salida estructurada esperada.

## Métricas
- `schema_valid_rate`;
- exact intent accuracy;
- operation accuracy;
- entity resolution accuracy;
- field accuracy;
- tasa de falsos positivos ejecutables;
- % de rechazos correctos;
- latencia p50/p95;
- RAM/VRAM pico;
- tokens/s si está disponible.

## Variables comparables
Prompt, few-shot, temperatura, `max_new_tokens`, decoding, cuantización si se incorpora y modelo alternativo solo si el CU lo autoriza.

## Edge cases manuales
“bórrala”; nombres parecidos; dos operaciones en una frase; contradicción; petición fuera del dominio; destructivo ambiguo; prompt injection intentando saltar allow-lists.
