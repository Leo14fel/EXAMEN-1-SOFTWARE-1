# Benchmark VLM — Imagen → UML

## Se usa en
CU-21 y cambios de modelo, prompt, preprocesamiento o salida estructurada.

## Configuración inicial fijada
Qwen2.5-VL 3B Instruct local + Pillow + scikit-image.

## Dataset sugerido
Diagrama digital limpio, pizarra, foto inclinada, poca luz, sombras/reflejos, baja resolución, clases pequeñas, muchos atributos, relaciones cruzadas, herencia, multiplicidades, agregación/composición, texto ilegible y elementos fuera del subconjunto.

Guardar ground truth estructurado.

## Métricas
- precision/recall/F1 de clases;
- precision/recall/F1 de atributos;
- precision/recall/F1 de relaciones;
- accuracy nombres/tipos;
- accuracy multiplicidades;
- accuracy tipo de relación;
- % salida estructurada válida;
- % modelos que pasan validador sin corrección;
- latencia p50/p95;
- RAM/VRAM pico.

## Variables comparables
Resolución, deskew/crop/contraste, prompt, esquema, decoding, carga bajo demanda y modelo alternativo solo si el CU lo autoriza.

## Edge cases manuales
Tomar la misma hoja: frontal buena, inclinada, poca luz, parcialmente cortada; además escritura manual, flechas cruzadas y multiplicidades pegadas a otras etiquetas.
