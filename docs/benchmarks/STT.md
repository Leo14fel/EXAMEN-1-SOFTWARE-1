# Benchmark STT — Voz → texto/intención

## Se usa en
CU-19 y cambios posteriores de configuración STT.

## Configuración fijada
faster-whisper sobre CTranslate2 para comandos breves.

## Dataset sugerido
Audios cortos con transcripción y, cuando aplique, intención esperada: habla clara, rápida/lenta, nombres técnicos, ruido de habitación/tráfico, micrófono laptop/celular, acento natural, pausas y autocorrecciones.

## Métricas
- WER;
- CER cuando aporte;
- intent accuracy;
- entity/name accuracy;
- latencia p50/p95;
- real-time factor;
- RAM/VRAM pico;
- % audios vacíos/error.

## Variables comparables
Modelo Whisper elegido durante CU, idioma fijo/autodetección, beam size, VAD, compute type y normalización.

## Edge cases manuales
Susurro; 1–2 m de distancia; ruido de calle; palabra inglesa; nombre inventado; “crea Cliente... no, Usuario”; audio que no es comando.
