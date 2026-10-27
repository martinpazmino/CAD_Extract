---
title: "Spike: extracción v2 sobre PDFs sintéticos"
date: 2026-10-23
tags: [spike, extraccion, benchmark]
aliases: [Spike extracción v2]
---

# Spike: extracción v2 sobre PDFs sintéticos

Prueba de concepto de [02 Bohrprofil independiente del layout](../../docs/02_bohrprofil_generalizacion.md)
y de la recuperación de Schraffur, Grundwasser, Sondierungen y coordenadas. **No es código de
producción**: los umbrales están elegidos para los PDFs sintéticos.

| Archivo | Qué hace |
|---|---|
| [`synth_bohrprofil.py`](synth_bohrprofil.py) | Genera 6 layouts DIN 4023 simplificados (A, A2, A3, A4, A5, B) + JSON con la verdad |
| [`prototyp_v2.py`](prototyp_v2.py) | Extractor v2: columnas, cabecera/GOK, escala por regresión, descripción, Schraffur, agua, DPH, coordenadas |
| [`prototyp_v3.py`](prototyp_v3.py) | Iteración tras los PDFs reales: segmentos, rotación, escala por confirmación de etiquetas, convención techo/base, filtros de tabla y de ejes, adaptador raster, abreviaturas DIN 4023, Schichtenverzeichnis como segunda fuente ([15](../../docs/15_resultados_pdfs_reales.md)); sigue acertando los sintéticos |
| [`prototyp_v4.py`](prototyp_v4.py) | Algoritmo por etapas E0–E9 ([17](../../docs/17_algoritmo_extraccion.md)): clase de página, OCR, cabeceras genéricas, etiquetas como valor final, modo "etiqueta primero", tablas de capas, Schichtenverzeichnis, coordenadas, confianza y JSON canónico; reglas conmutables en `RULES` |
| [`stress_cases.py`](stress_cases.py) | 17 casos de estrés, uno por lección ([16](../../docs/16_lecciones_aprendidas.md)), con verdad |
| [`run_geo_agent_v1.py`](run_geo_agent_v1.py) | Ejecuta el parser actual (`geo_agent`) sobre los layouts |
| [`run_prototyp_v2.py`](run_prototyp_v2.py) | Ejecuta el prototipo v2 y lo compara con la verdad |
| [`score_swissgeol.py`](score_swissgeol.py) | Puntúa las predicciones de swissgeol con la misma métrica |
| [`eval_utils.py`](eval_utils.py) | Métrica común (límites ±2 cm, Bodenart, texto) |

## Ejecutar

```bash
pip install pymupdf numpy openpyxl      # mismas dependencias que geo_agent
python synth_bohrprofil.py /tmp/synth
python run_geo_agent_v1.py /tmp/synth
python run_prototyp_v2.py  /tmp/synth
```

swissgeol (opcional, en un entorno **separado**: fija PyMuPDF 1.26.3 y trae OpenCV/AWS):

```bash
python -m venv sgvenv && sgvenv/bin/pip install git+https://github.com/swisstopo/swissgeol-boreholes-dataextraction
for L in A A2 A3 A4 B; do
  mkdir -p in_$L && cp /tmp/synth/synth_$L.pdf in_$L/
  sgvenv/bin/boreholes-extract-all -i in_$L -o out_$L -p out_$L/predictions.json --skip-draw-predictions
done
python score_swissgeol.py /tmp/synth .
```

## Resultados (2026-10-23)

Tabla completa e interpretación: [09 Validación](../../docs/09_validacion_benchmark.md#1-resultados-actuales-spike-pdfs-sintéticos).

- v1: correcto en A/A2; A3 6/18 Bodenarten (7 erróneas en verde); A4 y B 0 %; no detecta la
  contradicción de A5.
- v2: 102/102 capas, Schraffur 101/102 (la restante es la contradicción de A5, reportada como
  issue), GOK/agua/coordenadas 17/17, DPH error máx. 0,4 N10, escala 1:100/1:50 detectada.
- swissgeol (sin cambios, commit `776ea39`): límites y descripciones 18/18 en A–A3, 12/18 en A4;
  en B datos correctos bajo nombres equivocados; 0 agua, 0 cota, 0 coordenadas; capas falsas desde
  la leyenda.

Up: [Índice de documentación](../../docs/README.md)

Related: [01 Diagnóstico](../../docs/01_diagnostico_layout_fijo.md) · [08 swissgeol](../../docs/08_swissgeol_reutilizacion.md) · [09 Validación](../../docs/09_validacion_benchmark.md)
