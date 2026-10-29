---
title: "18 Layer modeler (N3) and That Open viewer"
date: 2026-10-27
tags: [model, layer-cake, ifc, thatopen, baugrundmodell]
aliases: [Modeler, Layer-cake, That Open viewer]
---

# 18 Layer modeler (N3) and That Open viewer

First stretch of the Baugrundmodell that **generates the Bodenschichten automatically**: from the
extracted Bohrungen (canonical JSON, [17](17_extraction_algorithm.md)) to model Einheiten, surfaces,
**closed solids** per Einheit, IFC 4.3 (`IfcGeomodel` + `IfcBorehole`) and a web viewer on That Open
Engine. It implements steps 1–6 of the layer-cake algorithm in the
[architecture §7.2](ARCHITECTURE_BAUGRUNDMODELL.md#72-layer-cake-algorithm-n3).

```
PDF ─prototyp_v4─► canonical JSON ─python -m baugrundmodell─► model.ifc + report.json ─► apps/web (That Open)
                                        ▲
                                        └─ einheiten.json (optional: the geotechnical engineer confirms or corrects the Einheiten)
```

| Code | What |
|---|---|
| [`services/modeler/`](../services/modeler/README.md) | `baugrundmodell` package (Python): Einheiten, surfaces, solids, IFC; 31 tests with synthetic ground truth |
| [`apps/web/`](../apps/web/README.md) | Viewer (Vite + TypeScript + `@thatopen/components` 3.6): Einheiten, properties, sections, vertical exaggeration |

![Demo model, W–E section with 5× exaggeration: local Kies lens and Torf that pinches out](img/18_demo_schnitt.jpg)

## 1. Automatic model Einheiten

**Preparation per Bohrung.** Left out of the model, with the reason in the report and in the IFC
(`Nicht_im_Modell`): no coordinates, a different CRS from the majority, no collar elevation (GOK), no
Schichten, duplicated or at the same position as another one. Gaps between Schichten →
`unklassifiziert`; overlaps → the top is trimmed. A Schicht without a class between two of the same
class is assigned to that class **and noted** (project rule: mark, do not hide). Consecutive
Schichten of the same class are merged into an *Abschnitt*.

**Correlation (sequence alignment).** An Einheit is a Bodenart at one place in the sequence
("Sand 1", "Kies 1", "Sand 2"). Each Bohrung is aligned against the common sequence with dynamic
programming:

| Operation | Meaning | Cost |
|---|---|---|
| M | the Abschnitt belongs to the Einheit (same class) | gap × 1/m + distance between centres × 0.1/m, the smaller of NHN elevation and depth below GOK ([19 §4](19_app_v2.md#4-correlation-with-strong-relief)) |
| S | the Einheit is **missing** in the Bohrung (it pinches out, thickness 0) | 2.0 |
| E | the same Abschnitt also covers the next Einheit of its class (an intermediate lens is missing) | 0.5 + elevation cost |
| C | another Abschnitt in the same Einheit (the engineer's Einheiten with several classes) | 0.2 + elevation cost |
| N | the Abschnitt does not fit → new Einheit | 3.0 |
| T | the Einheit lies **below the Endteufe**: unknown, not "missing" | 0; 3.0 + gap if the Einheit lies entirely above the end |

The reference elevation of each Einheit is the IDW mean of the other Bohrungen (*leave-one-out*).
The sequence grows progressively (it starts with the Bohrung with the most Abschnitte, then always
the closest one) and at the end all Bohrungen are realigned against the complete sequence until no
new Einheiten appear. Names: the class, numbered if it repeats.

**Confirmation by the geotechnical engineer.** The report contains `vorlage_einheiten` in the format
of `--einheiten`; Einheiten can be renamed, classes merged (`{"name": "Sande und Kiese",
"bodenarten": ["Sand", "Kies"]}`) or reordered, and the run repeated. A class that fits no given
Einheit creates a new Einheit **with a warning**.

## 2. Contacts per Bohrung

Base of each Einheit in each Bohrung, of four types:

| Type | When | Use |
|---|---|---|
| exact | boundary between two Abschnitte | data |
| free | the Einheit ends inside an Abschnitt that covers several Einheiten (missing lens) | set at the interpolated middle of the Einheit that pinches out, inside the Abschnitt (margin 0.1 m), ordered |
| censored | the Bohrung ends in the Einheit | base ≤ Endteufe − 0.5 m; if the surface violates it, that point is added (iterative) |
| unknown | Einheit below the Endteufe | no data; the stratigraphic trimming keeps it below |

Real example (Berlin, 422C-460, a single Sand from 0 to 7.7 m above Kies): Sand 1 (free base),
Kies 1 **missing** (it pinches out at 31.15 m NHN, the middle of the lens of 422C-461), Sand 2 (exact
base 28.55), Kies 2, Sand 3 (censored).

## 3. Surfaces and solids

1. **Domain**: convex hull of the Bohrungen + buffer (½ of the median distance to the neighbour,
   5–25 m); it works with one Bohrung (circle) and with Bohrungen in a line (corridor).
2. **A TIN mesh common** to all surfaces; the Bohrungen are **nodes** of the mesh.
3. **Exact interpolation**: IDW (p = 2, by default) or a thin-plate spline with a linear trend
   (`--methode tps`; with < 3 points or collinear ones it falls back to IDW). Exact at the data ⇒ the
   model reproduces every contact (measured deviation: **0.0 m** in all cases).
4. **Stratigraphic trimming** from top to bottom `z_base_i = min(z_base_i, z_top_i)`, never below the
   base of the model (= deepest Endteufe); remainders < 5 mm → 0.
5. **Extent of Einheiten that are not in every Bohrung**: IDW is only exactly 0 at the Bohrungen
   without the Einheit, so a lens seen in one Bohrung stayed thin under the whole site. Indicator
   present = 1 / missing = 0 (unknown does not count), interpolated; where it is < 0.5 the Einheit
   collapses to its middle (the upper one to its top, the lower one to its base). At the Bohrungen
   nothing changes.
6. **Closed solid** per Einheit: top TIN + base TIN + walls at the edge. Where the Einheit pinches
   out, top and base share a vertex and flat triangles are removed; a closure check (each edge used
   equally often in both directions) and a volume check (mesh = Σ area × mean thickness).

## 4. IFC 4.3

- `IfcGeomodel` ⊃ one `IfcGeotechnicalStratum` (SOLID, `IfcTriangulatedFaceSet` with `Closed`;
  formerly `IfcPolygonalFaceSet`, one entity per face: with Trassen of 80,000 faces the IFC tripled)
  per Einheit, `Description = "Modelleinheit k/n"`; `CPset_Modelleinheit`: Einheit, order, classes,
  colour, volume, max./mean thickness, maximum distance to a Bohrung (uncertainty), Bohrungen with
  the Einheit present / absent / unknown, closed, warnings.
- `CPset_Baugrundmodell` on the `IfcGeomodel`: method, mesh, buffer, base, Bohrungen inside and
  outside the model (with the reason), sources, version.
- `IfcBorehole` ⊃ strata of the Bohrung (prisms, `Description = "Bohrsaeule"`) with the usual
  provenance (`CPset_Schichtenverzeichnis`, `CPset_Herkunft`). The spike's N1 exporter now uses the
  same writer.
- Georeferencing `IfcMapConversion` + EPSG from the JSON, origin = rounded centroid (or the fixed
  project origin passed by the app). **Explicit length unit METRE** (formerly mm by ifcopenshell's
  default: the model came out 1000× too small, [M17](16_lessons_learned.md#m-model-ifc-and-that-open)).
  Schema validation: **0 errors** (demo, Berlin, all test cases).

## 5. Viewer (`apps/web`)

> [!NOTE]
> Since [20](20_lage_pruefung_viewer.md) the viewer has the controls of the TwinBimM (BUI,
> ViewCube, postproduction, Highlighter/Hider, coordinates), a camera for models over 5 km and the
> Lage editor on the PDF of the plan. What follows describes the first version.

Loading by `?ifc=`, file picker or drag and drop; it adds `IFCBOREHOLE`, `IFCGEOMODEL`,
`IFCGEOSLICE`, `IFCGEOTECHNICALSTRATUM` to the importer
([M2](16_lessons_learned.md#m-model-ifc-and-that-open)). List of Einheiten (colour, volume,
visibility), click → properties with provenance, labels with the code of each Bohrung, Bohrungen
on/off, translucent Einheiten, vertical exaggeration 1–10×, W–E / N–S sections and double click for a
plane. The web-ifc WASM and the Fragments worker are served **locally** (`npm run vendor`): no unpkg.
`scripts/check.mjs` tests it without a screen (Chromium/Playwright): loading, Einheiten, labels,
selection by list and by click with exaggeration, section, screenshots.

![Berlin V-67b-VE: 5 georeferenced Bohrungen, translucent Einheiten, 5× exaggeration](img/18_berlin_durchscheinend.jpg)

## 6. Results

**Tests** (`pytest services/modeler/tests`, 36 green since [20](20_lage_pruefung_viewer.md); they
include the 6 km Trasse and the METRE unit): invariants in 6 cases × 2 methods (exact contacts,
thickness ≥ 0, closed solids, consistent volume), inclined planes reproduced exactly with TPS
(< 1 mm), pinch-out, lens, censoring, perturbed data, engineer merging classes, unexpected class,
input order irrelevant, 1 and 2 Bohrungen, IFC validity.

**Against the synthetic ground truth** (inside the hull; volume model / truth):

| Case | Method | RMS of bases (m) | Einheiten that are not in every Bohrung |
|---|---|---|---|
| geneigt (planes) | IDW / TPS | ≤ 0.19 / 0.00 | — (volumes 1.00) |
| auskeilen (Torf wedge) | IDW / TPS | ≤ 0.27 / ≤ 0.20 | Torf 0.68 / 0.85 (without rule 5: 0.89 / 0.97) |
| linse (lens in 1 Bohrung) | IDW / TPS | ≤ 0.75 / ≤ 0.76 | Kies 1.91 / 2.26 (**without rule 5: 6.31 / 8.00**) |
| demo (12 Bohrungen) | IDW / TPS | ≤ 0.63 / ≤ 0.72 | Kies 0.70 / 0.83 · Torf 0.93 / 1.04 |

Rule 5 trades a qualitative error (a lens from one Bohrung under the whole site) for a moderate
underestimation of the wedges; the large RMS errors are at the inner boundaries of the lens, which the
Bohrungen do not determine.

**Berlin** (real data, *training* extraction, [15](15_results_real_pdfs.md)): 5 of 7 Bohrungen with
coordinates (S2a and B 1/17 out: no coordinates, marked in the IFC and in the viewer). Automatic
Einheiten: Sand 1 (60,836 m³, in 5), **Kies 1** (lens only in 422C-461, missing in 4, 2,999 m³),
Sand 2 (5), Kies 2 (2 present, 3 unknown below the short Bohrungen), Sand 3 (base = base of the
model). Mesh 2.9 m, buffer 16 m, 1,705 nodes, 3 censoring points, closed solids, IFC 3.0 MB.

> [!NOTE]
> With the current v4 extraction (example in [`data/beispiele`](../data/beispiele/README.md)), the
> Schichten of 2.1–2.6 m in 422C-5526/5527 that used to have no class are read as Auffüllung (OCR
> without umlauts, rule B of docs/16) and the Berlin model has **6 Einheiten** (Auffüllung between
> Kies 1 and Sand 2). The figures above are those of the previous extraction.

There is no 3D ground truth of the subsurface: the model is as good as the extraction and the density
of Bohrungen. What is guaranteed and tested is that it honours every data point, that it does not
invent Einheiten beyond what was observed, and that everything assumed (censoring, extent, Einheiten
left out) is noted.

## 7. Parameters

| Parameter | Value | Origin |
|---|---|---|
| `K_FEHLT`, `K_NEU`, `K_SPALT`, `K_WEITER` | 2.0 · 3.0 · 0.5 · 0.2 | A new Einheit must cost more than pinching out; an intermediate lens, less than two absences |
| `K_ABSTAND`, `K_MITTE` | 1.0/m · 0.1/m | The overlap of elevations decides; the centre breaks ties (Berlin: Kies of 460 ↔ lower Kies of 461) |
| `K_UEBER_ENDE` | 3.0 + gap | An Einheit entirely above the end of the Bohrung cannot be "unknown" |
| `ZENSUR_MARGE` | 0.5 m | The Einheit in which the Bohrung ends continues at least a little |
| `FREI_RAND` | 0.1 m | Free boundary not glued to the top/base of the Abschnitt |
| `MIN_MAECHTIGKEIT` | 5 mm | Depths in cm |
| `PRAESENZ_SCHWELLE` | 0.5 | The Einheit ends halfway to the Bohrungen without it |
| Buffer, mesh | ½ median dist. (5–100 m, by hand up to 5 km); √area / 40 (0.5–10 m), always ≤ 30,000 nodes | Size of the site; Trassen > 5 km ([20 §2](20_lage_pruefung_viewer.md#2-moving-the-geometry-and-models-over-5-km)) |
| Base | Deepest Endteufe | Do not model below what was explored |

## 8. Limits and next steps

1. **Correlation only by class and elevation**: two different sands (e.g. Talsand and
   Schmelzwassersand) with the same class are merged → today the engineer corrects it with
   `--einheiten`; later, finer classes from the description (Nebenanteile, colour, genesis) and the
   legend.
2. Layer-cake: no faults, folds or repeated bodies; N4 (GemPy) for that.
3. Uncertainty only as the maximum distance to a Bohrung; next: kriging with variance per vertex and
   colour in the viewer.
4. **Coordinates are still the bottleneck** (Berlin 5/7; the rest of the corpus 0):
   [07](07_coordinates.md) and N2 Geoslice from the Längsschnitt
   ([architecture §7.1](ARCHITECTURE_BAUGRUNDMODELL.md#71-ladder-of-levels-each-one-is-deliverable)).
5. Grundwasser surface as a model surface; Kennwerte per Einheit (`Pset_SolidStratumCapacity`).
6. Viewer: section caps (ClipStyler from `components-front`), click on the provenance → page of the
   PDF (pdf.js + bbox), editing Einheiten in the browser → `einheiten.json`.
7. Supabase: store each model run (`model_units`, parameters, report) next to the data it comes from.

Up: [Index](README.md)

Related: [20 Lage and Prüfstand](20_lage_pruefung_viewer.md) · [Architecture §7](ARCHITECTURE_BAUGRUNDMODELL.md#7-baugrundmodell-generating-the-geometry) · [17 Extraction algorithm](17_extraction_algorithm.md) · [16 Lessons](16_lessons_learned.md) · [11 Decisions](11_decisions.md) · [07 Coordinates](07_coordinates.md)
