# Benchmark LLM — Texto → intención/comando

## Se usa en
CU-18 y cualquier cambio posterior de modelo, prompt, esquema o parámetros.

## Configuración inicial fijada
Qwen3 1.7B Instruct local con Hugging Face Transformers + PyTorch.

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
