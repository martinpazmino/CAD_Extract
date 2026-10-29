---
title: "Grundwasser: symbols, text and water lines"
date: 2026-10-23
tags: [geo_agent, extraction, grundwasser]
aliases: [Grundwasser, Grundwasserstand]
---

# Grundwasser: symbols, text and water lines

**Conclusion:** the Grundwasser level is not extracted today. It appears in three forms — a symbol
in the Bohrprofil, text with keywords, and water lines in the Längsschnitt — and all three can be
read deterministically. It is worth combining our own geometric detection (DIN symbol) with
swissgeol's keyword lists and colour detection.

**Status:** symbol tested in the prototype (`groundwater` in
[`prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py)): **17/17** synthetic Bohrungen with
depth within ±5 cm and date. swissgeol unchanged found **0/14** in the 5 layouts it was tested on
(its detector looks for the Swiss two-line symbol;
[08](08_swissgeol_reuse.md#4-test-swissgeol-unchanged-on-our-pdfs)).

**With real PDFs** ([15](15_results_real_pdfs.md)): Talheim **3/4**. The triangle can sit next to
the neighbouring column, and what decides the Bohrung is the end of the **water line**. The
"angebohrt" symbol (two strokes + line) is not read yet. Wachenroth: "kein Grundwasser" detected in
**6/6** and stored as data. swissgeol: 1 false Grundwasser level.

In **Hausham** (DC-Software) the water is written as text `GW 2.53m` (4/4 after adding reading from
text). Three things had to be ruled out as "not water": the series of ▽ on the **elevation ruler**,
the triangles with an **elevation** next to them (`741.00m`) and the ▼ of the **starting
elevation** (depth 0).

## 1. Forms in which it appears

| Form | Where | How it is read |
|---|---|---|
| DIN 4023 symbol (triangle, filled or not, sometimes with lines below) | next to the column | closed path of 3 segments, 3–16 pt, vertex pointing down; the tip is the level |
| Text `GW 3,20 m u. GOK`, `Ruhewasserspiegel …`, date | next to the symbol or in the description | keywords + number + date |
| Text in a minority colour (blue) with a date | next to the column | swissgeol heuristic `groundwater_color_detection.py` |
| HGW / MGW / Bemessungswasserstand lines | Längsschnitt | blue/dashed polylines → `(station, NHN)` ([03 §6](03_laengsschnitt_generalization.md#6-terrain-and-water)) |

The difference between "angetroffen" and "Ruhewasserstand / nach Bohrende" is taken from the
**legend of the document** (fill, number of lines), not from the code.

## 2. Algorithm (symbol)

1. Closed paths with exactly 3 segments and symbol size, less than 30 pt from the column.
2. Exactly one vertex at the bottom → `y_level = y` of the tip → depth with the column's
   regression ([02 §3](02_bohrprofil_generalization.md#3-vertical-scale-by-regression)).
3. Text within 14 pt: date `dd.mm.yy(yy)` and, if present, a labelled depth → it must match the
   geometric one (±5 cm); otherwise, issue.
4. `NHN = GOK − Tiefe` as a check.

## 3. Keywords (German)

Base: swissgeol's `groundwater_keys.de` list (`Grundwasserspiegel`, `GW`, `GWSP`, `Wsp`,
`GW-Spiegel`, `Grundwasser`, …) and its false positives (`Grundwasserfassung`, `GW/`). To add for
Germany: `GW angetroffen`, `Ruhewasserspiegel`, `Wasserstand nach Bohrende`, `GW-Stand`, `HGW`,
`MGW`, `Bemessungswasserstand`, `Schichtenwasser`; units `m u. GOK`, `m NHN`, `m NN`, `mNN`
(swissgeol comes with Swiss units such as `m ü. M.`).

## 4. Data model and IFC

Table `groundwater_obs` in the [architecture §5.2](ARCHITECTURE_BAUGRUNDMODELL.md#52-supabase-schema-draft-migration)
with `kind` ∈ {angetroffen, ruhe, nach_bohrende, bemessung, hgw, mgw}, `depth`, `nhn`,
`observed_on`, provenance. In IFC: `Pset_BoreholeCommon.GroundwaterDepth`; the lines of the
Längsschnitt as a `WATER` stratum or a surface in the model.

Up: [Index](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalization.md) · [03 Längsschnitt](03_laengsschnitt_generalization.md) · [08 swissgeol](08_swissgeol_reuse.md)
