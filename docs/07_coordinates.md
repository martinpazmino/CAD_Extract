---
title: "Coordinates and georeferencing of the Bohrungen"
date: 2026-10-23
tags: [geo_agent, extraction, coordinates, crs, georeferencing]
aliases: [Coordinates, Rechtswert Hochwert, Georeferencing]
---

# Coordinates and georeferencing of the Bohrungen

**Conclusion:** Rechts-/Hochwert are not in the Bohrprofil (`geo_agent/excel_writer.py:145-147`
leaves them empty), but they are almost always **somewhere else in the Gutachten**: a table of
Aufschlüsse, the Lageplan or the project alignment. Without coordinates there is no real 3D model,
so this is the extraction that unlocks the Baugrundmodell.

**Status:** table tested in the prototype (`coordinate_table` in
[`prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py)): **17/17** Bohrungen with exact
Ost-/Nordwert. Lageplan and alignment: design. swissgeol unchanged: **0/14** (it only validates
Swiss CRSs). **With a real PDF** (Halle): the table of Grundwasser levels is read **26/26** with the
same cell-based method. None of the three real Gutachten contains a coordinate table
([15](15_results_real_pdfs.md)).

## 1. Sources, in order of preference

| # | Source | Method | Confidence |
|---|---|---|---|
| 1 | Table "Lage- und Höhenverzeichnis der Aufschlüsse" (Anlage) | `page.find_tables()` + reading per cell | high, and it brings the GOK to cross-check with the Bohrprofil |
| 2 | Text in the header of the Bohrung (`R = …`, `H = …`, `E/N`, `Ostwert/Nordwert`) | regex near keywords | medium-high |
| 3 | Lageplan PDF | Bohrung symbols + label; affine transformation with ≥ 3 grid labels; residuals | medium |
| 4 | Alignment (LandXML from Civil 3D) + station from the Längsschnitt + labelled offset | `XY = alignment(station) + offset` | medium |
| 5 | Manual input / CSV in the UI | — | depends on the user |

## 2. Verified trap when reading tables

PyMuPDF's `tab.extract()` returned `565 081,64` as `"56508164\n,"` (it loses the thousands spaces
and separates the comma). Tested solution: read each cell with `page.get_text("words", clip=cell)`
and join the words. Generalisable: **never parse numbers from "flattened" text**; always from words
with their bbox.

## 3. Reference systems in Germany

| CRS | EPSG | How to recognise it |
|---|---|---|
| ETRS89 / UTM 32N | 25832 | Easting 6 digits (280,000–920,000) or 8 with the zone prefix `32…`; northing 7 digits (5.2–6.1 M) |
| ETRS89 / UTM 33N | 25833 | same with the prefix `33…` (eastern Germany) |
| DHDN / Gauß-Krüger zones 2–5 | 31466–31469 | `R` 7 digits starting with the zone (2…5), `H` 7 digits |
| Heights | DHHN2016 and DHHN92 (`NHN`); old DHHN12 (`NN`) | text `m NHN` / `m NN`; differences of a few cm to dm depending on the region → record the system |

Rules: plausibility of ranges, strip the zone prefix, detect swapped axes (swissgeol does the same
for LV95/LV03: `coordinate_extraction.py`, "Swapping coordinates"). If there is only Gauß-Krüger,
transform with `pyproj` to the project CRS and keep the original.

## 4. Cross-checks

- GOK in the table = GOK in the Bohrprofil (±2 cm).
- Distance of the Bohrung from the alignment ≈ offset labelled in the Längsschnitt.
- Station of the Bohrung in the Längsschnitt ≈ projected station of its XY on the alignment.
- All Bohrungen inside the envelope of the Lageplan.

## 5. What to reuse from swissgeol

The structure of `CoordinateExtractor`: keywords (`Koordinaten`, `Koord.`), `X/Y` labels, a search
near the keyword and choosing the best match per page. The validators (`LV95Coordinate`,
`LV03Coordinate`) have to be rewritten for the German CRSs → [08](08_swissgeol_reuse.md).

## 6. Data model

`boreholes.collar geometry(PointZ)` with the project SRID (Z = GOK), plus `coord_source` and
`confidence` in `provenance`. In IFC: `IfcMapConversion` + `IfcProjectedCRS` (verified in the
[IFC spike](../spikes/ifc_thatopen/README.md)).

Up: [Index](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalization.md) · [03 Längsschnitt](03_laengsschnitt_generalization.md) · [08 swissgeol](08_swissgeol_reuse.md) · [Architecture](ARCHITECTURE_BAUGRUNDMODELL.md)
