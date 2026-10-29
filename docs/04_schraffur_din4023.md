---
title: "Schraffur DIN 4023: the graphic column as a second signal"
date: 2026-10-23
tags: [geo_agent, extraction, schraffur, din4023, classification]
aliases: [Schraffur, Hatch, Signaturen]
---

# Schraffur DIN 4023: the graphic column as a second signal

**Conclusion:** the graphic column of the Bohrprofil (DIN 4023 patterns: dots = Sand, circles =
Kies, stripes = Ton/Schluff…) is a signal **independent of the text** that is ignored today
(`geo_agent/bohrprofil.py:13`). Read from the vectors and compared with the samples in the **legend
of the same document**, it classifies the Bodenart without prior training and makes it possible to
detect errors in the text.

**Status:** tested in the prototype (`hatch_features`, `legend_swatches`, `classify_hatch` in
[`prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py)): **101/102 Schichten** of the 6
synthetic layouts classified correctly from the Schraffur alone. The remaining one is the A5
Schicht drawn on purpose with the wrong pattern, and the prototype reports it as
`Text 'Sand' != Schraffur 'Kies'` (v1 does not notice). Real drawings need calibration (see §5).

> [!NOTE]
> It has **not** been evaluated with real PDFs yet. In Wachenroth the pattern and the legend
> samples are loose segments (no fills); in Talheim colour, letters (`A`, `Mu`) and symbols are
> combined. The prototype's sample detector only accepts filled rectangles: the samples have to be
> built from segments, like the column in v3 ([15](15_results_real_pdfs.md)).

## 1. Why the legend is the training set

Every DIN 4023 Zeichenerklärung draws a sample of the pattern next to the name of the Bodenart.
Those samples use the same software, the same pattern scale and the same styles as the columns of
the document. That is why a nearest neighbour against the samples works without labelled data: the
document brings its own "ground truth".

Sample detection: a filled rectangle of 15–60 × 8–30 pt with a line of text starting with a
capital letter less than 40 pt to its right (`legend_swatches`).

## 2. Feature vector

Per rectangle (Schicht or sample), going through the **items** of each path (CAD programs usually
export the whole pattern as a single path with hundreds of sub-items):

| Feature | How it is measured |
|---|---|
| `dot` | small Bézier curves (< 1.5 pt) that are **filled** → dots |
| `circle` | Bézier curves without fill, or larger → circles |
| `line_0/45/90/135` | length of segments per orientation (45° bins) |
| `dash` | length of segments with a dash pattern (`dashes ≠ "[] 0"`) |

Only items whose midpoint falls inside the rectangle are counted (patterns are usually clipped),
the frame itself is excluded, and the vector is normalised by area and by L2 norm. Classification
is cosine similarity against the samples; the similarity is stored as the confidence.

## 3. Merging with the text

| Text | Schraffur | Result |
|---|---|---|
| Sand | Sand | Sand, high confidence |
| Sand | Kies | issue "Text ≠ Schraffur", review |
| — (not recognised) | Kies | Kies, medium confidence, marked |
| Sand | — (no pattern) | Sand, medium confidence |

Cases from the spike: in A3, v1 classified `Kies, sandig` as *Sand* with certainty
([01](01_diagnosis_fixed_layout.md)) while the Schraffur says *Kies*; in A5 (text *Sand*, pattern of
*Kies*) the merge raises exactly one issue on the affected Schicht.

## 4. Colours

Many Gutachten colour the Schichten (by Bodenart or by Homogenbereich). The fill colour is stored as
a feature and, if the legend has coloured samples, it is classified just like the pattern. In the
Längsschnitt it is the main route ([03 §4](03_laengsschnitt_generalization.md#4-geology)).

## 5. Risks with real PDFs

- **Fills with a PDF pattern** (`/Pattern`, tiling patterns): the pattern may not show up as
  geometry in `get_drawings()` **[to be verified]**. Fallback: render the Schicht and the sample at
  high resolution and compare the images (normalised correlation / texture descriptors).
- **Blocks / Form XObjects**: patterns inserted as CAD blocks → check that PyMuPDF flattens them
  **[to be verified]**.
- **Different pattern scale** between legend and column: the L2 normalisation makes the vector
  depend on the *proportion* of items, not on their density; if that is not enough, normalise by
  the detected spacing.
- **Mixed patterns** (DIN 4023 combines symbols: `Sand, kiesig` = dots + circles): kNN gives the
  most similar class; for the composition, decompose the vector as a non-negative combination of
  the samples (NNLS) **[idea, not tested]**.
- Legend samples on another page or in another document: they are stored per project in Supabase
  and reused.

## 6. Relation to swissgeol

swissgeol detects the *position* of the graphic columns (`strip_log_detection.py`: raster,
morphology, Hough circles and Fast Line Detector) but **does not classify** the pattern. Its
detector is useful as a fallback to locate columns in scans; the classification is our own
contribution → candidate for an upstream contribution ([08](08_swissgeol_reuse.md)).

Up: [Index](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalization.md) · [03 Längsschnitt](03_laengsschnitt_generalization.md) · [08 swissgeol](08_swissgeol_reuse.md) · [Glossary](glossary.md)
