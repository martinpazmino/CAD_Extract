---
title: "Collaboration with swisstopo: what they give us and what we give them"
date: 2026-10-25
tags: [swissgeol, collaboration, open-source]
aliases: [swisstopo collaboration, swisstopo]
---

# Collaboration with swisstopo: what they give us and what we give them

**Conclusion:** collaboration makes sense for both sides because the projects complement each
other. swisstopo has a mature textual/statistical core, an evaluation infrastructure and experience
with very heterogeneous documents. We bring what they lack for **vector CAD PDFs**, **reading the
drawing** and **German conventions**. The project explicitly invites other organisations to
contribute and to talk about partnerships (README of their repo). Start with little risk: two issues
with synthetic reproducers and an introduction email.

## 1. What swisstopo can contribute

| Contribution | What it does for us | How to ask for it |
|---|---|---|
| Proven algorithms (AAboveB columns, matching, diagonals, continuation) | The core of [02](02_bohrprofil_generalization.md) without reinventing it | Already public; port the ideas ([08](08_swissgeol_reuse.md)) |
| **Experience** with thousands of logs of unknown layouts | Avoid errors they already solved (OCR, multi-page, tables) | Technical conversation / review of our design |
| **Evaluation**: `ground_truth.json` format, metrics, `--benchmark` | Measure the same way they do; compare results | Public; confirm that our extensions are acceptable |
| **Swiss corpus with ground truth** (if they can share part of it) | Test generality with documents from another country | Ask; their data is in a private S3 |
| **OCR** route (`swissgeol-ocr`, AWS Textract) and BERT description models (HuggingFace `swissgeol/*`) | Scanned Gutachten; classification of German descriptions | Public; ask about applicability to the DIN vocabulary |
| Shared roadmap | Know what they will build (date, drilling method…) so as not to duplicate it | Conversation |

## 2. What we can contribute

| Contribution | Value for them | Effort | Already tested |
|---|---|---|---|
| **Bug reports with a synthetic reproducer** (§4) | They fix real failures: name of the neighbouring diagram assigned to the Bohrung, legend treated as a Bohrung | Low | Yes ([08 §4](08_swissgeol_reuse.md#4-test-swissgeol-unchanged-on-our-pdfs)) |
| **Generator of synthetic PDFs** with ground truth | Regression tests without copyright problems | Low | Yes ([spike](../spikes/extraktion_v2/README.md)) |
| **Lines from vectors** (`get_drawings()` → their `Line`) instead of FLD on raster | Accuracy and speed on digitally born PDFs | Low-medium | Design ([08 §6](08_swissgeol_reuse.md#6-proposed-adapter-vector-lines-for-their-pipeline)) |
| **Schraffur classification with the legend** | Their strip log detector locates but does not classify | Medium | Yes, synthetic ([04](04_schraffur_din4023.md)) |
| **German conventions**: elevation keys `NHN/NN`, UTM/Gauß-Krüger CRS, DIN 4023 water symbol | Opens the project to German logs | Medium | Water and coordinates, synthetic ([06](06_grundwasser.md), [07](07_coordinates.md)) |
| **Digitising Sondierungen** (DPH/CPT) | New data for their database | Medium | DPH, synthetic ([05](05_sondierungen.md)) |
| **IFC 4.3** export of Bohrungen | Bridge to BIM / swissgeol 3D | Medium | Yes ([IFC spike](../spikes/ifc_thatopen/README.md)) |

## 3. How to collaborate and intellectual property

- Their repo has no CLA and no `CONTRIBUTING` (checked at commit `776ea39`): contributions go in under
  **AGPL-3.0-only**. The copyright of what we write remains ours, so we can also use *our* code
  under another license **[confirm with them and with a lawyer]**. What we cannot do is take *their*
  code into a closed product ([14](14_licensing.md)).
- Contribute **small, isolated** pieces (vector adapter, CRS validators, symbol detector). Our own
  core (merge, Längsschnitt, model, IFC) stays in Geo_Agent.
- Respect their roadmap: they accept contributions "compatible with their mandate". Ask before large
  PRs.

## 4. First steps

The team sends these; Claude does not publish anything in other people's repos.

1. **Issue 1: name of the Bohrung** (draft below) with `synth_B.pdf` attached.
2. **Issue 2: the legend produces false Schichten or Bohrungen** with `synth_A.pdf` / `synth_A4.pdf`.
3. **Introduction email** to the project contact (from `publiccode.yml`: Stijn Vermeeren,
   `stijn.vermeeren@swisstopo.ch`).
4. If they reply: a small PR with the vector line adapter and a proposal for a module of German
   conventions.

### Draft issue 1

```text
Title: Borehole name assigned from neighbouring diagram title (e.g. "DPH 1") instead of the borehole header

Hi, we are evaluating the pipeline on German DIN 4023 borehole profiles (digitally born PDFs).
On a synthetic profile with two boreholes ("BK 1", "BK 2"), each followed by a dynamic probing
diagram titled "DPH 1" / "DPH 2", the layers and depths are extracted correctly, but the
borehole metadata name becomes "DPH 1" / "DPH 2" instead of "BK 1" / "BK 2".

Steps: boreholes-extract-all -i <dir with synth_B.pdf> -o out -p out/predictions.json
Version: commit 776ea39 (2026-10-23), default config.
Attached: synth_B.pdf (synthetic, no copyright restrictions) and its ground truth JSON.
Expected: name taken from the header above the depth sidebar / strip log.
```

### Draft issue 2

```text
Title: Legend page ("Zeichenerklärung") parsed as a borehole / continuation of the last borehole

On synthetic DIN 4023 profiles whose second page only contains the legend (soil-type swatches
with names), the legend entries become layers: either appended to the last borehole of page 1
as a continuation (9 instead of 6 layers) or as an extra borehole without depths.
Attached: synth_A.pdf, synth_A4.pdf + ground truth. Commit 776ea39, default config.
Possible signal: legend swatches are isolated small rectangles with a name to their right,
not a contiguous strip log; the page also contains a "Zeichenerklärung/Legende" heading.
```

### Draft email

```text
Subject: German DIN 4023 profiles – possible collaboration on swissgeol-boreholes-dataextraction

Dear Mr Vermeeren,

we are building an internal tool that extracts borehole data from German geotechnical reports
(digitally born CAD PDFs, DIN 4023) and turns it into a 3D ground model (IFC 4.3). We evaluated
your pipeline on synthetic German profiles: the depth-sidebar and description matching worked
very well across layouts; German specifics (NHN elevations, UTM/Gauss-Krüger coordinates,
DIN groundwater symbol) and the two issues we just opened are where it struggled.

We would like to contribute small, isolated pieces where useful to you, for example:
- a line source from PDF vector drawings (exact lines without rasterisation),
- German elevation/coordinate conventions,
- a synthetic DIN 4023 profile generator with ground truth for regression tests,
- (if of interest) classification of strip-log hatch patterns using the document legend.

Would you be open to a short call to check fit with your roadmap? We would also be interested
to know whether a small Swiss test subset with ground truth could be shared for benchmarking.

Kind regards,
<Name>, <Organisation>
```

Up: [Index](README.md)

Related: [08 swissgeol](08_swissgeol_reuse.md) · [14 Licensing](14_licensing.md) · [12 Corpus](12_public_corpus.md) · [11 Decisions](11_decisions.md)
