# Benchmarks — Política general

## Objetivo
Tomar decisiones de configuración con evidencia reproducible para LLM, VLM y STT. No sustituyen tests funcionales.

## Toda corrida registra
- fecha y commit;
- SO, CPU, RAM, GPU/VRAM;
- versiones de runtime/dependencias;
- modelo/revisión exacta;
- parámetros;
- prompt cuando aplique;
- dataset/fixtures y versión;
- número de casos;
- métricas;
- observaciones/errores.

## Comparar configuraciones
1. Congelar dataset.
2. Ejecutar A.
3. Ejecutar B sobre exactamente los mismos casos.
4. Repetir latencia si hay variabilidad.
5. Separar calidad de consumo de recursos.
6. Documentar trade-offs.
7. Elegir y justificar.
8. Conservar ambas corridas.

## Métricas transversales
- % de acierto;
- % de salida estructurada válida;
- latencia p50/p95;
- tiempo total;
- RAM pico;
- VRAM pico;
- CPU/GPU si se puede medir consistentemente;
- fallos/excepciones.

No inventar umbrales ni resultados. El baseline sirve para proponerlos y luego aprobarlos.
