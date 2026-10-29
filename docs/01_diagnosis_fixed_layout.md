---
title: "Diagnosis: fixed layout assumptions in geo_agent"
date: 2026-10-23
tags: [geo_agent, extraction, diagnosis, generalization]
aliases: [Fixed assumptions, Layout diagnosis]
---

# Diagnosis: fixed layout assumptions in geo_agent

**Conclusion:** the current extraction (v1) is exact for the drawing it was written for, but it
depends on **fixed positions, colours and formats**. With another office, another scale or simply
the text a few points closer to the column, it fails completely or, worse, **silently** (wrong
values marked green). It also throws away useful data: the Schraffur, the Sondierungen, the
Grundwasser level and the coordinates.

## 1. Measured evidence (synthetic PDFs)

Generator and scripts: [`spikes/extraktion_v2/`](../spikes/extraktion_v2/README.md). Six simplified
DIN 4023 layouts with known ground truth (18 Schichten in A–A5, 12 in B):

| Layout | What changes compared with A | v1: Bohrungen | v1: boundaries | v1: correct Bodenart | v1: correct text |
|---|---|---|---|---|---|
| A | reference (M 1:100, `B n/jj`, pairs `(NHN) Tiefe` on the left) | 3/3 | 18/18 | 18/18 | 18/18 |
| A2 | M 1:50, wider column | 3/3 | 18/18 | 18/18 | 18/18 |
| A3 | the description starts **10 pt closer** to the column | 3/3 | 18/18 | **6/18** | **0/18** |
| A4 | name centred above the column, labels 20 pt further left | **0/3** | 0/18 | 0/18 | 0/18 |
| A5 | like A, but one Schicht with the text *Sand* and the Schraffur of *Kies* (drawing error) | 3/3 | 18/18 | 18/18 | 18/18 — **the contradiction is not detected** |
| B | another office: `BK n`, depths on the right, decimal point, GOK in the header, DPH | **0/2** | 0/12 | 0/12 | 0/12 |

In A3, **7 of the 12 wrong Bodenarten come out marked as certain (green)**. For example,
`Kies, sandig, …` loses its first word (it falls outside the band `x_label+58`), and `sandig`
contains `sand`, so it is classified as *Sand* with certainty. That is the worst failure mode: the
Excel looks correct.

### With real PDFs

In the first three public Gutachten, v1 extracts **0 of 16 Bohrungen** (it does not recognise
`B 1`, `BK1`, `GWM1` without a year, nor those layouts). Moreover, with real texts `soil.classify`
returns as **certain** `Sandstein` → *Sand*, `Tonstein` → *Steine* and `Beton` → *Ton*
([15](15_results_real_pdfs.md)).

## 2. Inventory of fixed assumptions

Failure mode: **T** = total (nothing is extracted, visible) · **S** = silent (wrong value that
looks valid) · **P** = loss of information.

### Bohrprofil (`geo_agent/bohrprofil.py`, `legend.py`, `soil.py`)

| # | Where | Assumption | Failure | Solution |
|---|---|---|---|---|
| 1 | `geo_agent/bohrprofil.py:26-29` | Fixed bands relative to the token `B`: depths `−65…+8`, text `+58…next−25` | T (A4), S (A3) | Column from geometry + scale by regression → [02](02_bohrprofil_generalization.md) |
| 2 | `geo_agent/bohrprofil.py:31-32` | ID = `B` + `nn/jj`; fixed prefixes | T (B: `BK 1`, `KB3`, `B1`) | Generic regex + profile → [02](02_bohrprofil_generalization.md#2-header-name-and-gok) |
| 3 | `geo_agent/bohrprofil.py:33` | GOK = single token `NHN±x,xx m` inside the depth band | P/S | Regex in the header (`Ansatzhöhe`, `GOK`, `m NN`) |
| 4 | `geo_agent/bohrprofil.py:34` | Pairs `(NHN) Tiefe` in that order, NHN without `+` | T (depths on the right, no NHN) | Numeric column validated by correlation → [02](02_bohrprofil_generalization.md#3-vertical-scale-by-regression) |
| 5 | `geo_agent/bohrprofil.py:80-83` | A single row of headers per page (the one with the most IDs) | T (Bohrungen in two rows) | Detection per column, not per row |
| 6 | `geo_agent/bohrprofil.py:151`, `:181` | Grouping rows with `round(y/4)` | S with another font size | Text lines from PyMuPDF (`block_no`, `line_no`) |
| 7 | `geo_agent/bohrprofil.py:13` | Graphic column ignored | P | Schraffur classifier → [04](04_schraffur_din4023.md) |
| 8 | `geo_agent/bohrprofil.py:32` + README | `DS`, `GWM` excluded; "CPT-/Sonden-Spalten bewusst weggelassen" | P | → [05](05_sondierungen.md) |
| 9 | — | Grundwasser level is not extracted | P | → [06](06_grundwasser.md) |
| 10 | `geo_agent/bohrprofil.py:186-190` | If a segment has no certain Bodenart, it is assumed to be the "continuation of the previous Schicht" | S | Treat it as a review issue, not as data |
| 11 | `geo_agent/soil.py:22`, `:51` | Substring rules (`"sand" in word`) → adjectives (`sandig`, `tonig`) count as Bodenart, and so do rocks and man-made materials (`Sandstein` → Sand, `Beton` → Ton, verified with real PDFs); regional vocabulary (Lauenburger Ton, Glimmerton, Klei) | S | Grammar: main noun vs. `-ig` adjective → [02](02_bohrprofil_generalization.md#5-classifying-the-text-noun-not-adjective) |
| 12 | `geo_agent/legend.py:73-75` | The legend is only recognised if it contains DIN sections (`KORNGR…`, `KONSISTENZ`…) | T (no vocabulary) | Look for `ZEICHENERKLÄRUNG`/`LEGENDE`/`BODENARTEN` and Schraffur samples |
| 13 | `geo_agent/legend.py:88-90`, `:102` | Fixed `y` window and column cut `ax+85` | S | Rows = sample (rectangle) + text to its right |

### Längsschnitt (`geo_agent/laengsschnitt.py`)

| # | Where | Assumption | Failure | Solution |
|---|---|---|---|---|
| 14 | `:104-105` | Station `^(\d)\+(\d{3})\.000$` at `y≈1137` | T | Regex with variants + grouping by row → [03](03_laengsschnitt_generalization.md) |
| 15 | `:110`, `:428` | NHN axis at `290<x<360`, format `-?\d+\.\d{2}` | T | Evenly spaced numeric column + correlation |
| 16 | `:28-33`, `:38` | 5 fixed geology colours, tolerance 40 | S/T | Colours read from the legend of the Längsschnitt or from OCG layers |
| 17 | `:35` | Tunnel = grey fill `RGB 0.73` | T | OCG layer, band geometry or one click by the user |
| 18 | `:200`, `:238-239` | Only `doc[0]`; vertical region `160…1130 pt` | T | All pages; region = drawing frame |
| 19 | `:177`, `:180` | Bohrungen at `y<360`, `B` less than 25 pt from the number | T | Mini-column detector reused from [02](02_bohrprofil_generalization.md) |
| 20 | `:242`, `:286` | Terrain GOK = first 6 px "run" of geology colour | S | Terrain polyline (its own layer/style) |
| 21 | `:37`, `:139` | Raster of the whole page at zoom 2 (~20 s) | performance | Vector polygons + cache |
| 22 | `:419` | Global cache `_NHN_FIT` keyed by `id(page)` | S (ids reused across documents) | Pass the regression as a parameter |

### Output (`geo_agent/excel_writer.py`)

| # | Where | Assumption | Failure | Solution |
|---|---|---|---|---|
| 23 | `:145-147` | Rechts-/Hochwert always empty | P | → [07](07_coordinates.md) |

## 3. Reading

- Assumptions 1, 4, 14 and 15 are the same design error: **absolute position instead of a
  statistical relation**. The right technique already exists in the code itself (axis regression
  in the Längsschnitt) and in swissgeol (validating depth columns by correlation) →
  [08](08_swissgeol_reuse.md).
- Assumptions 10 and 11 turn an extraction failure into a "certain" value: the **silent error
  rate** has to be measured as the main KPI → [09](09_validation_benchmark.md).
- The losses (7, 8, 9, 23) are recovered with specific geometric detectors, all tested in the
  spike.

Up: [Index](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalization.md) · [03 Längsschnitt](03_laengsschnitt_generalization.md) · [09 Validation](09_validation_benchmark.md) · [11 Decisions](11_decisions.md)
