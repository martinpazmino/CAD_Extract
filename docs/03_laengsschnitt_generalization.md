---
title: "Längsschnitt: axes, tunnel and geology without constants"
date: 2026-10-23
tags: [geo_agent, extraction, laengsschnitt, tunnel, generalization]
aliases: [Längsschnitt v2, Längsschnitt generalization]
---

# Längsschnitt: axes, tunnel and geology without constants

**Conclusion:** the current method (axis regressions, tunnel mask, validation with `TS=`) is
correct; what has to be generalised is **how** the labels, the tunnel and the geology are found. It
is also worth moving from raster to **vector polygons**: they are more exact, faster, and produce
the model's `IfcGeoslice` directly.

**Status:** design. Not yet tested with PDFs (the spike covers the Bohrprofil); the assumptions it
replaces are listed in [01 §2](01_diagnosis_fixed_layout.md#längsschnitt-geo_agentlaengsschnittpy).

## 1. X axis: stations

- Regex with variants: `0+100`, `0+100.000`, `km 1+250,000`, `1+250` (km with 1–2 digits).
- The station labels form a **row**: group candidates by `y` (tolerance ~3 pt), keep the row with
  the most elements whose value grows with `x`; several rows → the longest one.
- Fit `TM = a·x + b` with residuals; residual > 0.5 m → label misread or from another row.

## 2. Y axis: NHN

- Candidates: numbers `±dd.dd` / `±dd,dd` aligned in a **column** (same right edge) with constant
  spacing and a correlation |r| > 0.99 with `y`. There can be two axes (left and right): both must
  give the same line.
- The ratio between the scales `a_y / a_x` is the **Überhöhung** (vertical exaggeration); if the
  drawing labels it (`Überhöhung 1:10`), it is validated.

## 3. Tunnel

Order of preference:
1. **OCG layer** of the CAD drawing (`get_drawings()` returns `layer` per path — [verified](ARCHITECTURE_BAUGRUNDMODELL.md#62-primitives-once-per-document-cached)).
2. **Geometry**: polygons that are long in `x`, whose vertical thickness is almost constant and
   matches `Ø / scale_y`; the diameter comes from the text (`Ø`, `D=`, `Da=`).
3. **One click by the user** in the UI: the profile stores the chosen layer/colour/style.

Validation (already in v1): detected Sohle = `TS=…m` labels.

## 4. Geology

- **Colours from the legend of the Längsschnitt itself**: each sample (filled rectangle) with its
  name to the right gives the colour → Bodenart map. It replaces `DEFAULT_COLOR_MAP`
  (`geo_agent/laengsschnitt.py:28-33`). Same pattern as the Schraffur samples
  ([04](04_schraffur_din4023.md)).
- **Vector polygons** instead of the raster of the whole page: each path with a geology fill →
  `shapely.Polygon` in `(station, NHN)` coordinates via the regressions. Result: the interpreted
  geological section (= `IfcGeoslice`) and its **interfaces** between Bohrungen, which feed the 3D
  model ([architecture §6.6](ARCHITECTURE_BAUGRUNDMODELL.md#66-längsschnitt-v2), §7.2).
- The composition in the tunnel is computed by intersecting the tunnel polygon with the geological
  polygons per station, instead of sampling pixels.

## 5. Bohrungen in the section

Längsschnitte draw mini-columns of the Bohrungen. The **same column detector** as for the
Bohrprofil ([02 §1](02_bohrprofil_generalization.md#1-columns-from-geometry)) finds them; the X-axis
regression gives their station. Cross-checks: GOK and boundaries must match the Bohrprofil with the
same ID.

## 6. Terrain and water

- Terrain GOK: the terrain polyline (its own layer/style) instead of the first pixel of geology
  colour (`geo_agent/laengsschnitt.py:242`).
- Water lines (HGW, MGW, Bemessungswasserstand, usually blue and dashed) → polylines in
  `(station, NHN)` → [06](06_grundwasser.md).

## 7. Other fixes

- Go through all pages, not only `doc[0]`; the useful region is the drawing frame, not `160…1130 pt`.
- Remove the global cache `_NHN_FIT` (`geo_agent/laengsschnitt.py:419`): pass the regression to the
  generator of the Prüfbild.
- Cache the primitives (> 150,000 paths) once per document.

Up: [Index](README.md)

Related: [01 Diagnosis](01_diagnosis_fixed_layout.md) · [02 Bohrprofil](02_bohrprofil_generalization.md) · [04 Schraffur](04_schraffur_din4023.md) · [06 Grundwasser](06_grundwasser.md) · [Architecture](ARCHITECTURE_BAUGRUNDMODELL.md)
