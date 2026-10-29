---
title: "swissgeol: what it does, what we tested and how to reuse it"
date: 2026-10-23
tags: [swissgeol, reuse, extraction, licensing]
aliases: [swissgeol, swissgeol-boreholes-dataextraction]
---

# swissgeol: what it does, what we tested and how to reuse it

**Conclusion:** `swissgeol-boreholes-dataextraction` (swisstopo) solves the **textual and
statistical** part of the stratigraphy very well — depth columns, description blocks, matching —
and it is robust to the layout: unchanged, it got 18/18 Schichten right in our layouts A, A2 and A3.
It does not cover what is **specific to Germany and to CAD drawings** (Schraffur, DIN water symbol,
German CRSs, Längsschnitt, tunnel), and its name assignment fails next to neighbouring diagrams.
Recommendation: **port its algorithms and its evaluation format**, use it as a **second opinion** in
the benchmark and **propose contributions** upstream; do not fork it or depend on its core.

## 1. Fact sheet

| | |
|---|---|
| Repo | <https://github.com/swisstopo/swissgeol-boreholes-dataextraction> (reviewed commit `776ea39`, 2026-10-23) |
| License | **AGPL-3.0-only** (because of PyMuPDF; they say they would change it if that dependency goes) |
| Version | v1.1.0 (2026-05-04), beta |
| Stack | Python 3.11–3.13, PyMuPDF **1.26.3** (pinned), OpenCV contrib, scikit-learn/-image, FastAPI, AWS (Textract, Bedrock), MLflow |
| Packages | `swissgeol_doc_processing` (geometry, text, tables, strip logs) and `extraction` (pipeline), installable from GitHub |
| CLI | `boreholes-extract-all`, `boreholes-extract-metadata`, `boreholes-score`, `boreholes-classify-descriptions` |
| Input | PDFs with text (scans with prior OCR: AWS Textract + `swissgeol-ocr`) |
| Output | `predictions.json` (Bohrungen → metadata, Schichten with depths and bbox, water) |
| Classification | BERT per property (lithology, USCS, colour, components…) published on HuggingFace `swissgeol/*`; alternative with Claude via AWS Bedrock |

## 2. Module map and relevance for us

| Module | What it does | Relevance | How to use it |
|---|---|---|---|
| `extraction/features/stratigraphy/sidebar/*` | Types of depth column: **AAboveB** (`0.30` / `2.70` stacked = our case), AToB (`0.30–2.70`), LayerIdentifier (`a)`, `1)`), Protocol, Spülprobe | **High** | Port AAboveB + its validator |
| `…/sidebar/utils/a_above_b_sidebar_validator.py` | ≥ 3 entries, strictly increasing, **Pearson > 0.95**, "noise" limit | **High** | Criterion adopted in [02 §3](02_bohrprofil_generalization.md#3-vertical-scale-by-regression) |
| `…/sidebar/extractor/a_above_b_sidebar_extractor.py` | Groups numbers into columns, **excludes rulers** (arithmetic progressions with 0), fixes OCR | **High** | Port |
| `extraction/features/extract.py` (`BoreholeExtractor`) | Description candidates per column, geometric scoring (`score_match`), greedy matching without overlaps, leader diagonals | **High** | Port the ideas: scoring + diagonals |
| `…/stratigraphy/depth_description_alignment.py` | Matching lines ↔ intervals by **dynamic programming** | Medium-high | Port for thin Schichten |
| `…/layer/continuation_detection.py` | Bohrung that continues on the next page | Medium | Port |
| `extraction/features/groundwater/*` | Keywords, Swiss symbol (two lines), text in a minority colour | Medium | Reuse the lists and the colour heuristic; our own DIN symbol ([06](06_grundwasser.md)) |
| `extraction/features/metadata/*` | Name, elevation, coordinates near keywords | Medium | Structure yes; our own German CRS validators ([07](07_coordinates.md)) |
| `swissgeol_doc_processing/geometry/line_detection.py` | Lines by **Fast Line Detector on raster** | Low for vector CAD | For scans; in CAD use `get_drawings()` |
| `swissgeol_doc_processing/utils/strip_log_detection.py` | Finds graphic columns in raster (morphology, Hough, FLD) | Medium (fallback) | Locate columns in scans; it does not classify patterns ([04](04_schraffur_din4023.md)) |
| `swissgeol_doc_processing/config/matching_params.yml` | Description, water and coordinate words, weights | Medium | Start from their `de` lists and extend them |
| `extraction/evaluation/*`, `docs/groundtruth-json.md` | Ground truth per PDF, metrics per Schicht/interval/description/metadata/water, multi-dataset benchmark | **High** | Adopt the format ([09](09_validation_benchmark.md)) |
| `classification/*` | Description classifiers (Swiss BERT, Bedrock) | Low-medium | Swiss systems (USCS, EN main); design reference for our DIN parser |
| `app/*` + `Dockerfile` | FastAPI API (`extract_data`, `extract_stratigraphy`, …) | Medium | Run as an "oracle" service in the benchmark |

## 3. Basic differences

| | swissgeol | Geo_Agent |
|---|---|---|
| Documents | Heterogeneous Swiss logs, many **scanned** | German **vector CAD** drawings, DIN 4023 + tunnel Längsschnitt |
| Lines | Raster + FLD | Exact vectors (`get_drawings`) |
| Main signal | Text | Text **+ geometry** (Schraffur, symbols, curves) |
| CRS / heights | LV95, LV03, `m ü. M.` | UTM 32/33, Gauß-Krüger, `m NHN` |
| Classification | USCS, EN, Swiss lithology | DIN 4023 / EN ISO 14688, vocabulary from the legend |
| Scope | Bohrungen | Bohrungen + Sondierungen + section + tunnel + 3D model |

## 4. Test: swissgeol unchanged on our PDFs

Installed in an isolated environment and run with `boreholes-extract-all` on 5 of the synthetic
layouts (A–A4 and B; A5 only differs in the Schraffur, which swissgeol does not read) from
[`spikes/extraktion_v2`](../spikes/extraktion_v2/README.md); evaluated with the same metric as v1
and v2 (`score_swissgeol.py`):

| Layout | Bohrungen | Boundaries | Bodenart (text) | Water | Elevation | Coordinates |
|---|---|---|---|---|---|---|
| A | 3/3 | 18/18 | 18/18 | 0/3 | 0/3 | 0/3 |
| A2 | 3/3 | 18/18 | 18/18 | 0/3 | 0/3 | 0/3 |
| A3 | 3/3 | 18/18 | 18/18 | 0/3 | 0/3 | 0/3 |
| A4 | 3/3 | 12/18 | 12/18 | 0/3 | 0/3 | 0/3 |
| B | 0/2 correct* | 0/12* | 0/12* | 0/2 | 0/2 | 0/2 |

\* In B the Schichten and depths of both Bohrungen come out **correct**, but each Bohrung gets the
name of the neighbouring diagram (`DPH 1`, `DPH 2`) instead of `BK 1`/`BK 2`, and the only record
called `BK 2` is a false Bohrung built from the legend (3 Schichten without depth). With a metric by
name this counts as a failure, and in production it would be one too (data on the wrong Bohrung).

In addition, in **all** layouts the legend page produces false Schichten: in A/A2/A3 the third
Bohrung is "continued" on page 2 (9 Schichten instead of 6), and in A4/B an extra Bohrung appears
with only legend entries. Our metric (recall by depth) does not penalise those extra Schichten; a
precision metric would.

Readings:
- Its detection of depth columns and description blocks **is layout-independent**: it confirms that
  the statistical approach of [02](02_bohrprofil_generalization.md) is the right one.
- What fails is everything that depends on national conventions or on understanding the drawing:
  water symbol, `NHN`, CRS, the name ↔ column association when there are diagrams, and telling a
  legend from a Bohrung.
- Our prototype v2 also gets Schraffur, water, GOK, coordinates and DPH right on the same PDFs
  ([09](09_validation_benchmark.md)).

### With real PDFs

Details in [15](15_results_real_pdfs.md):
- **Wachenroth**: 6/6 Bohrungen, 18/18 boundaries and 6/6 elevations on the individual pages, but
  **5 false Bohrungen** (the repeated height section and a lab report) and 1 false Grundwasser
  level.
- **Talheim** (rotated pages, drawn by elevation): 0/10.
- **Halle** (no logs): **4 false Bohrungen** taken from tables.

This confirms the reading above: its core finds depths and descriptions well, but it lacks knowing
what is a Bohrung and what is not.

**Blind test** (Hausham with DC-Software and scanned Rednitzhembach,
[15 §6](15_results_real_pdfs.md#6-blind-test-hausham-and-rednitzhembach)):
- swissgeol got **13/13 Bohrungen** and 4/4 Grundwasser levels, and our v3 **0/13**: its label
  reading tolerates formats ours did not know (`0.20m`, OCR).
- But it got 0/13 elevations and invented 18 Bohrungen (the text pages of the Schichtenverzeichnis
  looked like logs).

This strengthens strategy A: **port its catalogue of label formats and its tolerance to OCR**, and
keep our geometric validation (D26).

## 5. Reuse strategies

| Strategy | Pros | Cons | Recommended use |
|---|---|---|---|
| **A. Port algorithms** (reimplement the ideas in `geo_agent`) | Full control, no coupling to a beta API, no AGPL carried along if a commercial PyMuPDF license is bought one day | Reimplementation work | **Core**: AAboveB + validator, ruler exclusion, candidate scoring, diagonals, DP, continuation |
| **B. Direct dependency** (`pip install` of their wheel, call `AAboveBSidebarExtractor` etc.) | Fast | Unstable internal API, pins PyMuPDF 1.26.3 (we use 2.x), drags in OpenCV/scikit/AWS | Only in evaluation scripts |
| **C. Oracle service** (their Docker API) | Independent second opinion; detects our regressions | Another service to operate | **Benchmark** and low-confidence cases |
| **D. Contribute upstream** | Shared improvements; swisstopo invites collaboration | Coordination, their roadmap decides | Vector line adapter, German CRSs, DIN symbol, Schraffur classifier |
| E. Fork | — | Maintaining a fork of a living project | **No** |

### License (important decision)

- swissgeol is **AGPL-3.0-only**. Copying its code makes that part of Geo_Agent AGPL.
- Geo_Agent uses PyMuPDF (also AGPL or commercial): today, for **internal** use, nothing changes.
- If it is offered as a service to third parties, or the commercial PyMuPDF license is bought to
  close the code, the code copied from swissgeol **would still be AGPL**. Therefore: **port ideas
  (A)**, cite the source in comments and, if anything is copied literally, isolate it in a module
  marked as AGPL.

## 6. Proposed adapter: vector lines for their pipeline

Their `Line(start: Point, end: Point)` (`swissgeol_doc_processing/geometry/geometry_dataclasses.py`)
is fed today from the raster (`detect_lines_fld`). For vector CAD it is enough to convert the `l`
segments of `page.get_drawings()` to `Line` and pass them as a `LineDetectionResult`: exact lines,
no rendering. It is the smallest and most useful upstream contribution for both sides.

## 7. Concrete plan

1. Port AAboveB + validator + ruler exclusion to `geo_agent/bohrprofil/scale.py` (with a test).
2. Port the scoring of description candidates and the diagonals → thin Schichten.
3. Adopt their `ground_truth.json` format (+ extensions) and their metrics → [09](09_validation_benchmark.md).
4. Run swissgeol as an oracle in the benchmark (Docker or isolated venv).
5. Reuse the keyword lists (`matching_params.yml`, `de`) for water, coordinates and elevation.
6. Contact swisstopo: vector adapter, German CRSs, DIN water symbol, Schraffur. What each side gains
   and drafts of issues/email: [13 Collaboration](13_swisstopo_collaboration.md).

Up: [Index](README.md)

Related: [13 Collaboration](13_swisstopo_collaboration.md) · [14 Licensing](14_licensing.md) · [02 Bohrprofil](02_bohrprofil_generalization.md) · [04 Schraffur](04_schraffur_din4023.md) · [06 Grundwasser](06_grundwasser.md) · [07 Coordinates](07_coordinates.md) · [09 Validation](09_validation_benchmark.md) · [11 Decisions](11_decisions.md)
