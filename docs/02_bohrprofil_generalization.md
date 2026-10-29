---
title: "Bohrprofil: layout-independent extraction"
date: 2026-10-23
tags: [geo_agent, extraction, bohrprofil, generalization]
aliases: [Bohrprofil v2, Bohrprofil generalization]
---

# Bohrprofil: layout-independent extraction

**Central idea:** stop looking for the data *at a position* and look for it *by its relation*. The
column is a stack of rectangles, the depths are numbers whose `y` position correlates linearly with
their value, and the description is the block of text aligned to the right of the column. That way
the same code works for any office and any scale.

**Status:** tested in the prototype
[`spikes/extraktion_v2/prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py) on the 6 synthetic
layouts (17 Bohrungen, 102 Schichten): **102/102 Schichten** with correct boundary, Bodenart and
text, also in A3, A4 and B, where v1 fails, and the deliberate contradiction of A5 is reported as an
issue ([01](01_diagnosis_fixed_layout.md)).

**With real PDFs** (Wachenroth, Talheim) seven changes were needed, among them: geometry reduced to
segments, rotation normalisation, scale chosen by label confirmation, table filters and normalised
scales. The result is [`prototyp_v3.py`](../spikes/extraktion_v2/prototyp_v3.py). In the **blind
test** with two new PDFs, v3 scored **0/13**: labels like `0.20m`, a scale fitted to the sheet and a
scan. After fixing that (including a raster adapter that produces the same segments from the image)
it reaches **29/29 Bohrungen and 143/143 boundaries** in the five real PDFs, with no regression on
the synthetic ones. Details and limits in [15 Real results](15_results_real_pdfs.md). The method
described below is still the same; the v3 variants are marked **(v3)**.

## Pipeline

```
words + drawings ─► 1 columns ─► 2 header (ID, GOK) ─► 3 scale y→Tiefe ─► boundaries
                                                               │
              4 description block ◄────────────────────────────┘
                     │
              5 text classification ─┐
              6 Schraffur (→ 04) ────┴► merge + confidence + issues
```

## 1. Columns from geometry

- Candidates: closed filled paths with a rectangular shape (`re` or 4 orthogonal segments), 8–80 pt
  wide. They are grouped by `(x0, x1)` with a tolerance of 0.8 pt and chained if
  `|y1_i − y0_{i+1}| ≤ 0.8 pt`. A chain of ≥ 2 rectangles is a column (`find_columns` in the
  prototype).
- The legend samples do not form chains (there are gaps between them) and diagram frames have no
  fill, so they are excluded automatically.
- **(v3)** More general: reduce everything (lines, rectangles, quads) to **segments**, merge the
  collinear ones, and define the column as a **pair of stroked verticals** (8–80 pt, height
  ≥ 2.5 × width). Boundaries are continuous horizontals that touch **both** edges (±0.6 pt), so the
  Schraffur stays out. Of nested candidates, the one with the thickest edges is kept. This works the
  same with rectangles (synthetic), loose segments (Wachenroth) and edges drawn in pieces with
  white masks (Talheim).
- **Fallbacks** for drawings where the column is not made of rectangles:
  1. horizontal lines crossing the same `x` interval (the Schicht boundaries);
  2. raster: the swissgeol *strip log* detector (`swissgeol_doc_processing/utils/strip_log_detection.py`)
     finds graphic columns in images → [08](08_swissgeol_reuse.md).

## 2. Header: name and GOK

- Name: the lowest line of text above the column (≤ 70 pt) that matches
  `^(B|BK|KB|RKS|BS|GWM)\s*\d+[a-z]?(/\d{2})?$`. The valid prefixes come from the profile.
- The Sondierungen (`DPH`, `DPL`, `DS`, `CPT`, `SRS`) use another regex and another extractor
  → [05](05_sondierungen.md). **Careful:** swissgeol gets the name wrong here: in layout B it
  assigns each Bohrung the title of the neighbouring DPH diagram
  ([08](08_swissgeol_reuse.md#4-test-swissgeol-unchanged-on-our-pdfs)).
- GOK: `(?:NHN|NN)\s*±x,xx\s*m` or `±x,xx\s*m\s*(?:NHN|NN)` in the header area (covers
  `NHN+6,20m`, `Ansatzhöhe: 5.47 m NHN`, `GOK = 5,47 mNN`).

## 3. Vertical scale by regression

1. Candidates: numbers with decimals near the column (−120…+60 pt in `x`), excluding those in
   brackets or with a sign (they are NHN, not depth).
2. Group them by text column (right-aligned edge) and, per group, require ≥ 3 values that are
   **strictly increasing** with a **Pearson correlation > 0.95** between `y` and value (exactly the
   criterion of swissgeol's `AAboveBSidebarValidator`).
3. Fit `Tiefe = a·y + b`. The real scale follows from `a`: `M = a / 0.000352778`
   (1 pt = 0.3528 mm). The prototype recovers **1:100 and 1:50** without configuration; the result
   is checked against the text `M 1:…`.
4. **(v3)** In real drawings the labels can be **offset** (leader lines) and can label the **top**
   (with 0.00) or the **base**. That is why v3 generates scale candidates:
   - direct, with the label on the line;
   - by order, with the k-th label at the k-th boundary;
   - the text `M 1:xx` / `Höhenmaßstab 1 : 75`.

   The candidate with the most **labels confirmed** by some boundary (±3 cm) wins, and only
   **normalised scales** (±4 %) are accepted. The label↔boundary confirmation is 1:1.
5. Further robustness from swissgeol worth porting:
   - iteratively remove the entry that worsens the fit most (`remove_entry_by_correlation_gradient`);
   - discard **rulers/scales** (`0, 1, 2, 3 m…`): arithmetic progressions that contain 0
     (`_arithmetic_progression_entries`);
   - fix OCR decimal-point errors (`fix_ocr_mistakes`), only relevant for scans.

## 4. Boundaries and description

- **The boundaries come from the geometry** (lower edge of each rectangle) and are converted with
  the regression; the closest label (< 6 pt) **confirms** the value (|Δ| ≤ 2 cm). Boundary without
  a label → issue; label without a boundary → issue.
- NHN check: if there are NHN values (in brackets or with a sign) next to the boundary,
  `GOK − Tiefe = NHN` (already in v1, `geo_agent/bohrprofil.py:203`).
- **Description block:** lines of text (not numeric, no date) to the right of the column and before
  the next column; the left edge is the mode of `x0` (left-aligned text). Each line is assigned to
  the Schicht whose interval `[y0, y1)` contains its `y0`. This solves A3 (text closer) and B
  (text further away).
- **Thin Schichten with leader lines** (text offset, with a diagonal pointing to its Schicht):
  swissgeol already solves this with `get_diagonals_near_textlines` + `compute_entries_shift`
  (shifts the label area along the diagonal) and a matching by **dynamic programming**
  (`depth_description_alignment.py`). Not in the prototype; to be ported.

## 5. Classifying the text: noun, not adjective

The silent failure in A3 comes from `soil.classify` searching for substrings: `sandig` → *Sand*.
DIN 4023 / EN ISO 14688 rule: the **main fraction is a noun** (capitalised: *Sand, Kies,
Mittelsand, Geschiebemergel*); the secondary ones are adjectives ending in `-ig` (*sandig, kiesig,
schluffig*). Changes:

- The head word must be a noun (initial capital, does not end in `-ig`/`-haltig`).
- If the first word is not a noun → **issue**, never "continuation of the previous Schicht"
  (`geo_agent/bohrprofil.py:186-190`).
- Regional vocabulary (Lauenburger Ton, Klei…) is loaded from the legend or the profile, not from
  the code.
- Full parsing of Nebenanteile, consistency, etc.: see
  [architecture §6.5](ARCHITECTURE_BAUGRUNDMODELL.md#65-description-parser-din-4023--din-en-iso-14688-1).

## 6. Merging and confidence

Each Schicht gathers independent signals; the confidence is the agreement between them
(`Layer.confidence` in the prototype):

| Signal | Indicative weight |
|---|---|
| Geometric boundary confirmed by a label | 0.4 (0.2 without a label) |
| Bodenart from the text (noun recognised) | +0.3 |
| Bodenart from the Schraffur matches the text ([04](04_schraffur_din4023.md)) | +0.3 |

Green/yellow in the Excel is derived from this value. The weights are calibrated with the real
corpus.

## 7. What remains as configuration (profile)

Only hints, never positions: ID prefixes, depth/NHN regex, language, regional vocabulary, expected
scale. See the format in
[architecture §6.10](ARCHITECTURE_BAUGRUNDMODELL.md#610-layout-profiles).

## 8. Cases not yet covered

- Rotated pages (`/Rotate`) and vertical text → normalise with `page.rotation_matrix` **[to be verified]**.
- Bohrungen that continue on the next page → swissgeol `layer/continuation_detection.py`.
- Scanned PDFs → OCR first (swissgeol uses AWS Textract + `swissgeol-ocr`); lower confidence.
- Several columns per Bohrung (e.g. stratigraphy + Bodenart): choose the one with the Schraffur.

Up: [Index](README.md)

Related: [01 Diagnosis](01_diagnosis_fixed_layout.md) · [04 Schraffur](04_schraffur_din4023.md) · [08 swissgeol](08_swissgeol_reuse.md) · [09 Validation](09_validation_benchmark.md) · [Architecture](ARCHITECTURE_BAUGRUNDMODELL.md)
