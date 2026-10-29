---
title: "Spike: extraction v2 on synthetic PDFs"
date: 2026-10-23
tags: [spike, extraction, benchmark]
aliases: [Extraction v2 spike]
---

# Spike: extraction v2 on synthetic PDFs

Proof of concept of [02 Layout-independent Bohrprofil](../../docs/02_bohrprofil_generalization.md)
and of recovering Schraffur, Grundwasser, Sondierungen and coordinates. **It is not production
code**: the thresholds are chosen for the synthetic PDFs.

| File | What it does |
|---|---|
| [`synth_bohrprofil.py`](synth_bohrprofil.py) | Generates 6 simplified DIN 4023 layouts (A, A2, A3, A4, A5, B) + JSON with the ground truth |
| [`prototyp_v2.py`](prototyp_v2.py) | Extractor v2: columns, header/GOK, scale by regression, description, Schraffur, water, DPH, coordinates |
| [`prototyp_v3.py`](prototyp_v3.py) | Iteration after the real PDFs: segments, rotation, scale by label confirmation, top/base convention, table and axis filters, raster adapter, DIN 4023 abbreviations, Schichtenverzeichnis as a second source ([15](../../docs/15_results_real_pdfs.md)); still gets the synthetic ones right |
| [`prototyp_v4.py`](prototyp_v4.py) | Algorithm by stages E0–E9 ([17](../../docs/17_extraction_algorithm.md)): page class, OCR, generic headers, labels as the final value, "label first" mode, Schicht tables, Schichtenverzeichnis, coordinates, confidence and canonical JSON; switchable rules in `RULES` |
| [`stress_cases.py`](stress_cases.py) | 17 stress cases, one per lesson ([16](../../docs/16_lessons_learned.md)), with ground truth |
| [`run_geo_agent_v1.py`](run_geo_agent_v1.py) | Runs the current parser (`geo_agent`) on the layouts |
| [`run_prototyp_v2.py`](run_prototyp_v2.py) | Runs prototype v2 and compares it with the ground truth |
| [`score_swissgeol.py`](score_swissgeol.py) | Scores swissgeol's predictions with the same metric |
| [`eval_utils.py`](eval_utils.py) | Common metric (boundaries ±2 cm, Bodenart, text) |

## Run

```bash
pip install pymupdf numpy openpyxl      # same dependencies as geo_agent
python synth_bohrprofil.py /tmp/synth
python run_geo_agent_v1.py /tmp/synth
python run_prototyp_v2.py  /tmp/synth
```

swissgeol (optional, in a **separate** environment: it pins PyMuPDF 1.26.3 and brings OpenCV/AWS):

```bash
python -m venv sgvenv && sgvenv/bin/pip install git+https://github.com/swisstopo/swissgeol-boreholes-dataextraction
for L in A A2 A3 A4 B; do
  mkdir -p in_$L && cp /tmp/synth/synth_$L.pdf in_$L/
  sgvenv/bin/boreholes-extract-all -i in_$L -o out_$L -p out_$L/predictions.json --skip-draw-predictions
done
python score_swissgeol.py /tmp/synth .
```

## Results (2026-10-23)

Full table and interpretation: [09 Validation](../../docs/09_validation_benchmark.md#1-current-results-spike-synthetic-pdfs).

- v1: correct on A/A2; A3 6/18 Bodenarten (7 wrong ones in green); A4 and B 0 %; it does not detect
  the contradiction of A5.
- v2: 102/102 Schichten, Schraffur 101/102 (the remaining one is the contradiction of A5, reported as
  an issue), GOK/water/coordinates 17/17, DPH max. error 0.4 N10, scale 1:100/1:50 detected.
- swissgeol (unchanged, commit `776ea39`): boundaries and descriptions 18/18 on A–A3, 12/18 on A4; on
  B correct data under wrong names; 0 water, 0 elevations, 0 coordinates; false Schichten from the
  legend.

Up: [Documentation index](../../docs/README.md)

Related: [01 Diagnosis](../../docs/01_diagnosis_fixed_layout.md) · [08 swissgeol](../../docs/08_swissgeol_reuse.md) · [09 Validation](../../docs/09_validation_benchmark.md)
