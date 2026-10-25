---
title: "Corpus: Gutachten públicos (manifest y evaluación)"
date: 2026-10-25
tags: [spike, corpus, validacion]
aliases: [Spike corpus]
---

# Corpus: Gutachten públicos (manifest y evaluación)

| Archivo | Qué hace |
|---|---|
| [`manifest.tsv`](manifest.tsv) | 24 candidatos públicos (B-Pläne, UVP-Verbund, NLWKN, Transparenzportal Hamburg) de 9 Länder: nombre, Land, procedimiento, URL, contenido esperado. Revisados: `wachenroth`, `talheim`, `halle`, `hausham`, `rednitzhembach` (marcados `GEPRUEFT`); los marcados `Runde 3 (blind)` son la próxima ronda ciega; el resto, encontrados por búsqueda y sin abrir |
| [`screen_corpus.py`](screen_corpus.py) | `--download` descarga el manifest; `--screen` filtra páginas (vector/escaneo/Bohrprofil), corre v1 y v3 y escribe `report.md` + miniaturas (sin verdad) |
| [`eval_real.py`](eval_real.py) | Compara v1, v3 y (opcional) swissgeol con la verdad de `groundtruth/` |
| [`blind_test.py`](blind_test.py) | Prueba ciega: `freeze` congela predicciones antes de mirar los PDFs nuevos, `score` las puntúa después |
| [`groundtruth/`](groundtruth/wachenroth.json) | Verdad transcrita a mano de Wachenroth, Talheim, Halle, Hausham y Rednitzhembach (datos factuales, URL y `sha256` del PDF) |

```bash
python screen_corpus.py --download ~/gutachten          # requiere acceso de red a los dominios
python screen_corpus.py --screen ~/gutachten ~/gutachten_report
```

Los PDFs **no** se commitean (uso interno, ver [12 Corpus](../../docs/12_corpus_publico.md#4-uso-legal-de-los-pdfs)).
En el entorno de Claude la descarga está bloqueada por la política de red (2026-10-25); los tres
PDFs evaluados se subieron a mano. Resultados: [15 Resultados reales](../../docs/15_resultados_pdfs_reales.md).

```bash
python eval_real.py <carpeta_con_wachenroth.pdf_talheim.pdf_halle.pdf> [<carpeta_salida_swissgeol>]
```

Up: [Índice de documentación](../../docs/README.md)

Related: [12 Corpus público](../../docs/12_corpus_publico.md) · [15 Resultados reales](../../docs/15_resultados_pdfs_reales.md) · [09 Validación](../../docs/09_validacion_benchmark.md)
