---
title: "Implementation plan: extraction v2"
date: 2026-10-23
tags: [geo_agent, plan, roadmap, extraction]
aliases: [Extraction v2 plan, Extraction roadmap]
---

# Implementation plan: extraction v2

**Goal:** replace the fixed assumptions of v1 with the geometric/statistical extraction, recover the
lost data and make it measurable, without breaking the current Excel. This plan details phases F0–F2
of the [architecture §11](ARCHITECTURE_BAUGRUNDMODELL.md#11-roadmap) for the extraction part.
Indicative estimates for one person.

| Step | Content | Files | Acceptance criterion | Effort |
|---|---|---|---|---|
| 0 | **Test bench**: move the synthetic generator and the metrics from `spikes/extraktion_v2` to `tests/`; add the silent error KPI; non-regression test of the Excel with the reference PDFs | `tests/synth/`, `tests/test_extraction.py` | CI green with v1 on A/A2; v1 failures on A3/A4/B documented | 2–3 days |
| 1 | **Canonical model with provenance** (Pydantic) + adapter v1 → model → Excel; **primitives layer** (the only PyMuPDF import, [14 §4](14_licensing.md#4-primitives-layer-do-it-now)) | `geo_agent/model.py`, `geo_agent/primitives/`, `exporters/excel_writer.py` | Excel identical to the current one; `import pymupdf` only in `primitives/` | 3–4 days |
| 2 | **Bohrprofil v2 core** following `prototyp_v3.py`: segments → columns, normalised rotation, generic header/GOK, scale from candidates with label confirmation (incl. swissgeol's AAboveB), geometric boundaries, top/base convention, table/scale filters ([15](15_results_real_pdfs.md)) | `geo_agent/bohrprofil/{columns,header,scale,text_assign}.py` | A–A5 and B at 100 % in CI; Wachenroth/Talheim as in [15](15_results_real_pdfs.md); reference Excel without regression | 1–1.5 weeks |
| 3 | **Classification**: noun vs. adjective, remove the silent "continuation", Schraffur + merge + confidence | `geo_agent/soil.py`, `geo_agent/bohrprofil/hatch.py`, `validate/` | Silent error = 0 on the corpus; A5 raises its issue | 3–4 days |
| 4 | **Grundwasser and Sondierungen** | `bohrprofil/symbols.py`, `bohrprofil/soundings.py` | Water ±5 cm; DPH ≤ 1 N10; new sheets/tables in the output | 4–5 days |
| 5 | **Coordinates**: tables (reading per cell), header, German CRSs; Lageplan later | `lageplan/coord_tables.py`, `lageplan/georef.py` | Rechts-/Hochwert filled in and verified against GOK | 3–4 days (+1 week Lageplan) |
| 6 | **Längsschnitt v2**: generic axes, colours from the legend, OCG, vector polygons, mini-columns | `geo_agent/laengsschnitt/{axes,tunnel,geoslice}.py` | Same result as v1 on the reference drawing + a second, different drawing | 1–1.5 weeks |
| 7 | **swissgeol**: oracle in the benchmark, keyword lists, upstream contact ([13](13_swisstopo_collaboration.md)) | `tests/oracle_swissgeol.py` | Automatic comparison report | 2 days |
| 8 | **Real corpus**: 5–10 public Gutachten ([12](12_public_corpus.md), `spikes/korpus/`), semi-automatic ground truth, calibrate thresholds and weights | `spikes/korpus/manifest.tsv` → `tests/corpus/`, private bucket, `tests/thresholds.yml` | Real metrics published in [09](09_validation_benchmark.md) | ongoing; can start now (only depends on the network) |

## Order and dependencies

```
0 ─► 1 ─► 2 ─► 3 ─► 4
          │         └─► 5
          └─────────────► 6
0 ─► 7 (in parallel)          8: gather and filter the corpus now; calibrate when 2 is ready
```

## Migration rules

- v1 stays available behind a flag until v2 matches or beats all metrics on the reference corpus.
- Every new detector comes with its synthetic case and its metric.
- Every new constant goes into the YAML profile or `tests/thresholds.yml`, never hard-coded.
- Code ported from swissgeol: reimplemented and cited (license,
  [08 §5](08_swissgeol_reuse.md#5-reuse-strategies)).

Up: [Index](README.md)

Related: [09 Validation](09_validation_benchmark.md) · [11 Decisions](11_decisions.md) · [Architecture](ARCHITECTURE_BAUGRUNDMODELL.md) · [02 Bohrprofil](02_bohrprofil_generalization.md) · [03 Längsschnitt](03_laengsschnitt_generalization.md)
