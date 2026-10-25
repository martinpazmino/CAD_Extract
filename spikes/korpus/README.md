---
title: "Corpus: Gutachten públicos (manifest y evaluación)"
date: 2026-10-25
tags: [spike, corpus, validacion]
aliases: [Spike corpus]
---

# Corpus: Gutachten públicos (manifest y evaluación)

| Archivo | Qué hace |
|---|---|
| [`manifest.tsv`](manifest.tsv) | 16 candidatos públicos (B-Pläne, UVP-Verbund, Transparenzportal Hamburg) de 8 Länder: nombre, Land, procedimiento, URL, contenido esperado. **Sin verificar**: encontrados por búsqueda, no abiertos todavía |
| [`screen_corpus.py`](screen_corpus.py) | `--download` descarga el manifest; `--screen` filtra páginas (vector/escaneo/Bohrprofil), corre v1 y v2 y escribe `report.md` + miniaturas |

```bash
python screen_corpus.py --download ~/gutachten          # requiere acceso de red a los dominios
python screen_corpus.py --screen ~/gutachten ~/gutachten_report
```

Los PDFs **no** se commitean (uso interno, ver [12 Corpus](../../docs/12_corpus_publico.md#4-uso-legal-de-los-pdfs)).
Probado sólo con los PDFs sintéticos de [`extraktion_v2`](../extraktion_v2/README.md); en el entorno
de Claude la descarga está bloqueada por la política de red (2026-10-25).

Up: [Índice de documentación](../../docs/README.md)

Related: [12 Corpus público](../../docs/12_corpus_publico.md) · [09 Validación](../../docs/09_validacion_benchmark.md)
