---
title: "Lessons learned (project memory)"
date: 2026-10-26
tags: [lessons, memory, extraction, validation]
aliases: [Lessons learned, Lessons, Memory]
---

# Lessons learned (project memory)

**What this note is for:** everything learned, written as **explicit rules** that any person (or
agent) must respect when touching the extraction. Each rule says what to do, why (evidence) and
which test watches it. If a rule stops being met, a test must turn red.

**Goal of the project (do not lose sight of it):** from a Bodengutachten in PDF, build the
**Baugrundmodell**: validated, traceable Bohrung data → Supabase → IFC 4.3 geometry in That Open
Engine ([Architecture](ARCHITECTURE_BAUGRUNDMODELL.md)). The extraction is not the end: what
matters is that every value reaches the model **with its provenance and its confidence**, and that a
doubtful value stays **marked**, never hidden.

> [!IMPORTANT]
> Rules L1–L18 come from real PDFs ([15](15_results_real_pdfs.md)). The figures after each fix are
> training figures; the blind rounds gave **0/13** and **11/29**. A new rule is only accepted if it
> does not break the regression set (§P5).

## P. Process and measurement

| # | Rule | Why / evidence |
|---|---|---|
| P1 | **Measure blind before fixing.** Freeze the predictions for every new PDF before opening it | v3 got 29/29 in training and **0/13** in the first blind round ([15 §6](15_results_real_pdfs.md#6-blind-test-hausham-and-rednitzhembach)) |
| P2 | **Push the frozen predictions to the repo** (with the `sha256` of the PDF and the code revision) **before** transcribing the ground truth | The git history proves the order; round 3: `5325ead`/`2d4d5e7` → ground truth `acc5cd5` (D29) |
| P3 | Always separate **blind figures** from **training figures** in every report | Avoids fooling ourselves (D24) |
| P4 | The main metric is the **silent error**: a wrong value marked as certain. A false Bohrung is worse than one not found | v1 marked wrong Bodenarten green ([01](01_diagnosis_fixed_layout.md)); swissgeol invented 55 Bohrungen in 9 PDFs |
| P5 | **Every change is measured against the full set** (real PDFs + synthetic) before it is pushed | A rule from round 3 broke B 4 of Rednitzhembach and only the regression set caught it |
| P6 | A new rule must be **general** (describe a feature of the drawing), never an exception for a PDF, an office or a coordinate | The fixed positions of v1 are the root cause of its 0/58 |
| P7 | The ground truth is transcribed **from the image** and checked against a second source (Schichtenverzeichnis, report) when there is one | The Schichtenverzeichnis confirmed 14/14 transcribed Bohrungen |
| P8 | The PDFs are **not** pushed to the repo; only URL, `sha256` and factual data | Internal use of other people's work (D16, D23) |
| P9 | **Perturb the PDFs that already work** (rotate, scale, rasterise) with the same ground truth: it finds failures the originals hide | Rotating Wesel revealed that the Schichtenverzeichnis reader used unrotated coordinates |
| P10 | **Ablation**: switch off each rule and see which case gets worse. A rule whose removal makes nothing worse is not protected by any test | [`ablation.py`](../spikes/korpus/ablation.py): 22 of 28 rules protected ([table](../spikes/korpus/ablation_v4.md)) |
| P11 | **One stress case per lesson**: the real failure becomes a minimal PDF that reproduces it. Writing the case for an unprotected rule often uncovers a new failure | [`stress_cases.py`](../spikes/extraktion_v2/stress_cases.py), 17 cases; s15 uncovered the L14 failure |
| P12 | Also measure **precision to the centimetre** (exact boundaries), not only the 5 cm tolerance | v3 414/515 exact, v4 509/515 after T2 |

## E. Input: what kind of PDF it is

| # | Rule | Evidence |
|---|---|---|
| L1 | Do not assume rectangles or fills: **reduce everything to segments** | Ghostscript/PDF24 left Wachenroth as 965 loose segments |
| L2 | **Normalise the rotation** (`page.rotation_matrix`) of words and paths before any geometry | Talheim (`/Rotate 90`), Marl p. 19, Wesel p. 17 (`/Rotate 270`) |
| L11 | **Scan = same logic**: segments from the image (OpenCV) and text from the OCR layer | Rednitzhembach 4/4 after the raster adapter |
| L17 | **AutoCAD with SHX fonts**: the text of the drawing is lines; there is no text layer even though it is vector. Detect it (many paths, almost no words) and send it through OCR | Wesel p. 17: 1389 paths, 18 loose "words" |
| L18 | **Raster without a text layer** (portal screenshots, archive scans): our own OCR is needed | Berlin: 11 Bohrungen in images; OCR (RapidOCR) reads depths and elevations with confidence 0.6–0.9 |
| E1 | Classify every page **before** extracting: vector+text · vector without text (SHX) · raster+OCR · raster without text | All four classes appeared in 9 Gutachten |
| E2 | A scan can carry **vector noise** (hundreds of paths from the OCR software): with an image > 80 % it is still a scan, and both image **and** vector segments are used | Swiss KB5: 220 paths |
| E3 | **Every module takes its primitives from the same normalised layer** (E1); never `page.get_text()` directly | The SV reader failed on rotated pages because it skipped the rotation |
| L18b | The OCR layer of a scan **loses text** ("2 / I", labels of B 4): complement it with our own OCR where there are no words | A7367, Rednitzhembach |
| E4 | OCR reads the Schraffur of Kies (circles) as `000`: do not count those tokens as text | Case s12 |
| E5 | The page size of a scan (or of a reduced printed PDF) is **not** that of the paper: the `M 1:100` in the title block does not give the scale in PDF points; the labels decide. If the title block contradicts them, the Bohrung comes out **without Schichten** and with a warning | KB5; perturbation at 70 %: false boundaries 57 → 2 |
| E7 | In raster, a column drawn only with **colour fills without an outline** gives no dark lines: edges between colours (gradient) have to be detected, not only a black threshold | Raster perturbation of Hausham (DC-Software) |
| E6 | OCR **loses spaces** (`KeinWasser`, `RKS 1-Betonweg`, `GW2.53m`, `36,25mNHN`): every text pattern must accept optional spaces and must not depend on `\b` between a letter and a digit | Raster perturbation: GW status 3/20 |

## G. Geometry: column and boundaries

| # | Rule | Evidence |
|---|---|---|
| G1 | Column = **pair of stroked verticals**, width 8–80 pt, height ≥ 2.5 × width | Works in 7 different offices |
| G2 | Boundary = **continuous** (not dashed) horizontal that touches **both edges** (±0.6 pt; scan ±1.6 pt) | L6: the Schraffur of Ton and the double line of Schwarzdecke crossed the column |
| G3 | Nested columns (inner strip, GWM pipe): keep the one with the **thickest edges** | Talheim GWM |
| G4 | A column with numbers inside is a **table**, not a Bohrung | L5: table "B 6" of Wachenroth at M 1:12 |
| G5 | Every boundary must be **confirmed 1:1 by a label**; otherwise it is marked (not deleted) | Talheim BK5: 1 extra boundary marked |

## T. Labels, scale and headers

| # | Rule | Evidence |
|---|---|---|
| L3 | The **position** of the label is not reliable (offset, above, below); some offices label the **top** (with 0.00), others the **base**. The scale is chosen by **how many labels** each candidate confirms (direct, by order, text `1:75`) | Talheim 65/65 |
| L8 | Labels with the unit attached (`0.20m`), decimal comma or point | Hausham (DC-Software) |
| L9 | Non-normalised scales exist (log fitted to the sheet, M ≈ 1:35; Triefenstein 1:30): valid if ≥ 80 % of ≥ 3 labels confirm them | Hausham RKS, Triefenstein |
| L14 | A group of values in **arithmetic progression** is an **axis** (elevation ruler, scale of a DPH diagram), not Schicht labels, **if** it has a round step (0.1 · 0.25 · 0.3 · 0.5 · 1 m…) and ≥ 8 values, or more values than the column has boundaries. Schichten of equal thickness (0.4 · 0.8 · 1.2…) are still labels | Marl BS 10 (DPH axis); case s15 (the first version of the rule deleted real labels) |
| L15 | A column of values **in pairs** (Von/Bis of samples) are not Schicht labels | Marl (IDAT/GeoDin) |
| L15b | A column without any confirmed label while the neighbouring ones have them → it is not a log (e.g. GWM construction drawing). If **no** column on the page has labels (OCR lost), the title-block scale is accepted and marked | Marl GWM 10; Rednitzhembach B 4 |
| L4 | In the height representation the header sits far above the column: associate the header with the column **below** it, without a vertical limit | Wachenroth section, Talheim |
| L13 | The header can carry a **suffix**: `RKS 1 - Betonweg 0+050`, `B 1 Bohrung Nr.` | Triefenstein 0/5 because of this |
| T1 | Third-party codes do not follow the `B 1` pattern: `422C-460`, `B 7/16`, `S 2a`, `DS 1/17`. The prefix list must be **configurable** and extended from the legend and the Lageplan of the document itself | Berlin |
| L12 | The same Bohrung appears on its own sheet and in the section: prefer the **titled sheet** with fewer Bohrungen; a confirmation < 50 % does not count | Wachenroth B 2, Rednitzhembach B 4 |
| T2 | A boundary confirmed by a label is delivered with the **printed value** (3.50), not the geometry (3.49) | Exact precision 414 → 509 of 515 |
| T3 | Sheet with **a single header**: it is anchored to the column with the most labels even if the header is far away (forms with a centred header) | KB5 |
| T4 | If the lines do not fit but the labels form a **clean straight line** with a normalised scale: the boundaries are the labels, the lines only confirm | KB5 (raster Schraffur creates extra lines) |
| T5 | A column with ≥ 3 depths **inside** it is the depth column of the form, not the log | KB5 |

## B. Text and Bodenart

| # | Rule | Evidence |
|---|---|---|
| L7 | Classify by the main **noun**, not by substrings: `Sandstein` is rock, `Tonstein` rock, `Beton`/`Schwarzdecke` man-made, `Oberboden` = Mutterboden | v1: Sandstein→Sand, Beton→Ton marked "certain" |
| L16 | If there is no noun, use the DIN 4023 / EN ISO 14688 **abbreviation** at the start (`U, t, s´` → Schluff; `fS` → Sand; `A (S, u´)` → Auffüllung; `Gr`, `Sa`, `Si`, `Cl`) | Triefenstein, Marl |
| B1 | The text can come with **leader lines** (not centred on the Schicht): assign it by the label convention or by the leader line, not only by `y` | Marl BS 10: 5 Schichten without Bodenart |
| B2 | Always keep the **original text** next to the class | Traceability (model §5.1) |
| B3 | Read the description **by norm** with evidence per value (DIN 4023 / ISO 14688-1 / DIN 18196 / practice / colour only): prepare the text (decimal comma ≠ separator, joined words `FeinsandbisMittelsand`, apostrophes and overlines), main = first noun or Kurzzeichen, *Auffüllung*/*Mutterboden*/geological name + soil = material; foreign materials by **word start** (`Toneisenstein` is not iron) | [21 §3](21_app_schritte_normen.md#3-mini-database-of-norms) |
| B4 | What the norm reads differently from the extraction is **marked**, not changed: "Sand/Auffullung" is fill (13 Schichten in Berlin); `Mg` is ambiguous (Geschiebemergel / made ground); the Bodengruppe only if it is written | Berlin, `test_normen.py` |

## W. Water

| # | Rule | Evidence |
|---|---|---|
| W1 | The triangle can sit next to the **neighbouring column**; the end of the **water line** assigns the Bohrung | Talheim |
| L10 | Not water: triangles in an aligned series (elevation ruler), a triangle with an elevation next to it, a triangle at the GOK | Hausham |
| L10b | Water also comes as **text**: `GW 2.53m`, `Wasserstand nach Sondierung 3,00 m`, `Wasseranschnitt 3.8`, "Ruhewasser" | Hausham, Triefenstein, Berlin |
| W2 | "kein Grundwasser", "trocken", "kein Wassereintritt" are **data**, not absences | Wachenroth 6/6, Wesel |
| W3 | Missing: symbols from the legend ("angebohrt" with two strokes) | Talheim BK2 (the only GW lost in training) |
| W4 | Missing: the **water symbol in raster** (▽ ▼ drawn in a scan); today it is only detected as vector or as text. Tried: OpenCV triangular contours find the Schraffur (146 false GW) and not the symbol, even when requiring a water line → rule switched off; next attempt: a template of the symbol taken from the legend | Raster perturbation: Hausham GW 4/4 → 0/4 |

## S. Second sources and cross-checks

| # | Rule | Evidence |
|---|---|---|
| S1 | The **Schichtenverzeichnis** (DIN 4022 form) is the most stable source: depth in column 1, name under `a)`, water in column 3. **Always** read it and compare it 1:1 with the log | Hausham 9/9 and Triefenstein 5/5 "SV ok"; Wesel 24/24 only from there (D30) |
| S2 | Read numbers from tables **per cell** with their words and bbox, never from flattened text | `565 081,64` came out as `"56508164\n,"` ([07](07_coordinates.md)) |
| S3 | The title of a form can be **spaced out** (`S c h i c h t e n v e r z e i c h n i s`) and the text **duplicated** (two layers): normalise before searching | Wesel |
| S4 | Rammsondierungen can come as a **table of values** (N10 every 10 cm) instead of a curve | Triefenstein pp. 32–35 |
| S5 | Coordinates appear in tables, in portal title blocks (`Rechtswert (UTM 33N): 394774,3`) or in the Lageplan; without them there is no real 3D | Berlin (in an image), Halle (GW table 26/26) |
| S6 | The log can be **only a text table** (Tiefe \| Beschreibung) without a graphic column; accept it only if ≥ 60 % of the intervals give a Bodenart (DPH and lab tables do not) | A7367 (Switzerland) |
| S8 | A **scanned** Schichtenverzeichnis is read the same way through OCR if the reader uses the common primitives: OCR glues the marker to the text (`a)Auffullung`), drops umlauts (`Auffullung`) and spaces (`B1` on one page, `B 1` on another): compare **normalised** codes and accept forms without umlauts | Raster perturbation: Triefenstein 0/5 → 5/5, Wesel 0/24 → 24/24 |
| S7 | Label and value in the title block can be **separate blocks** on the same row (`Höhe in m ü.M.:` · `668.99`): join by row before searching | A7367 |

## R. swissgeol: what to copy and what not

| # | Rule | Evidence |
|---|---|---|
| R1 | Copy its **tolerance of formats** in labels (units, OCR, positions) and the exclusion of arithmetic progressions | swissgeol 13/13 in blind round 2 where v3 got 0 |
| R2 | Do not copy its assignment of Bohrungen without geometric validation: it produces **many false ones** and does not read German elevations | 55 false Bohrungen and 6/50 GOK in 9 PDFs |
| R3 | AGPL license (like PyMuPDF): internal use without problems; for third parties, our own primitives layer (D17, D18) | [14](14_licensing.md) |

## M. Model, IFC and That Open

| # | Rule | Evidence |
|---|---|---|
| M1 | IFC 4.3: `IfcBorehole` ⊃ `IfcGeotechnicalStratum`; model in `IfcGeomodel`; georeferencing with `IfcMapConversion` + `IfcProjectedCRS` | Spike validated without schema errors |
| M2 | That Open's `IfcImporter` **discards** the geotechnical classes by default: add `IFCBOREHOLE`, `IFCGEOMODEL`, `IFCGEOTECHNICALSTRATUM` to `importer.classes.elements` | 0 → 16 elements with geometry |
| M3 | Encapsulate the IFC writer: IFC 4.4 replaces `IfcGeotechnicalStratum` with `IfcGeoScienceFeature` | 4.4 draft |
| M4 | Without coordinates, the section model (station, NHN) already adds value; with local coordinates from the Lageplan a relative 3D can be built | [Architecture §7.1](ARCHITECTURE_BAUGRUNDMODELL.md#71-ladder-of-levels-each-one-is-deliverable) |
| M5 | An **empty Pset** is invalid IFC: create the Pset only if there are values | Exporter: 5 schema errors → 0 |
| M6 | PostGIS installed in `extensions`: **qualify** `extensions.geometry`, otherwise the migration only works inside Supabase | [Supabase spike](../spikes/supabase/README.md) |
| M7 | The full chain already works with a real PDF: OCR → canonical JSON → PostGIS → georeferenced IFC 4.3 → That Open (80 strata) | Berlin ([15 §8](15_results_real_pdfs.md)) |
| M8 | **Below the Endteufe is unknown, not absent**: treating it as absence pinches out the deep Einheiten at every short Bohrung | Case `zensiert`, Berlin ([18](18_layer_modeler.md)) |
| M9 | The same Bodenart at another elevation is **another Einheit** (Sand 1 / Sand 2): correlate by class **and** elevation, not only by name | Berlin 422C-461: two levels of Kies |
| M10 | A lens missing inside a continuous Abschnitt: the boundary is **free** inside the Abschnitt; place it at the interpolated middle of the lens, not at a Schicht boundary | Case `linse`, Berlin 422C-460 |
| M11 | Bohrungen as mesh **nodes** + exact interpolator ⇒ the model reproduces every contact (always check it: maximum deviation in the report) | 0.0 m in all cases |
| M12 | IDW only reaches 0 at the Bohrungen themselves: an Einheit seen in one Bohrung spreads thinly under the whole site. Limit the extent (presence indicator) | Lens volume ×6.3 → ×1.9 |
| M13 | Thickness thresholds on the **surfaces**, not only on the mesh: otherwise the volume of the IFC and that of the model differ | The volume test caught it (5 m³) |
| M14 | Reading geology needs **vertical exaggeration** (site 150 m × 20 m); scale `model.object` in y around the base: the Fragments raycast uses `matrixWorld` and keeps working. Transparency with `depthWrite: false` | Viewer screenshots |
| M15 | With relief (Talheim: GOK 749–772 m) correlation by absolute elevation splits one shallow Schicht into several Einheiten: also compare the **depth below GOK** and keep the smaller distance | 15 → 6 Einheiten ([19](19_app_v2.md)) |
| M16 | A model without coordinates is only honest as a **schematic**: say so in the app, in the IFC (`Lage`) and in the viewer (`Lagebezug`) | App v2 |
| M17 | `ifcopenshell.api.unit.assign_unit()` **without arguments sets millimetres**: with coordinates in metres the model comes out 1000× too small in any viewer and the `IfcMapConversion` is wrong. Explicit units and a `calculate_unit_scale == 1` test | The 6 km Trasse measured 6 m ([20 §2](20_lage_pruefung_viewer.md#2-moving-the-geometry-and-models-over-5-km)) |
| M18 | That Open camera: perspective near 1 / far 1000, orthographic 0.1 / 1000 at 200 m from the target: **everything > 1 km disappears**. Recompute near/far on every move from the scene size (orthographic: negative near) | Trasse: far 24.6 km, near 0.02 m up close |
| M19 | An IFC that is already local to the project origin is loaded **without `COORDINATE_TO_ORIGIN`** (web-ifc shifts it by default): that way IFC and scene share coordinates. For IFCs with large global coordinates it must stay on | Pins = IFC to the cm |
| M20 | Calibrating a plan with 2 points: Lageplan = **similarity** (complex numbers, `q = u − i·v` because the rows go down); Längsschnitt = **separate scales** for station and height (the drawing's exaggeration is undone). Show the resulting scale and rotation so that the user spots a bad point | 1:500 / 10.0°; 1:500 / 1:100 |
| M21 | BUI 3.4: `Component.create` decides stateful/stateless by the **arity** of the template (`() =>` returns an element, not `[el, update]`); tooltips with `<bim-tooltip>` inside the button (`tooltip-title` is obsolete); `bim-label` cuts to one line (use `<p>`); `bim-dropdown` needs `.value` (it does not follow the `checked` of its options after the first render) | Errors and warnings at the first start |
| M22 | camera-controls applies `fitToSphere(…, false)` on the next `update()`: call `controls.update(0)` before measuring the scale of the view | The offset next to the panel went off screen |
| M23 | CSS: a child with `display:none` in a grid makes the next one take its column (0 px): set `grid-column`; and `[hidden]` loses against `display:grid/flex` (`[hidden]{display:none!important}`) | 0 px viewer when folding the panel; a loading notice that never went away |
| M24 | The ifcopenshell IFC carries **date and time in the header**: the same model gives another hash after a restart. As the model fingerprint (einchecken, caches) use the **key of its inputs**, not the bytes of the IFC | False *seitdem geändert* after restarting the app |
| M25 | Inside Streamlit the iframe measures **0 px** until `setFrameHeight` arrives: framing at that moment gives an aspect of 0/0 and `fitToSphere` leaves the camera at **NaN** with no way back (black viewer, hidden marks). Frame only with a size (ResizeObserver, pending framing) and repair a non-finite camera | Cold start of the app ([20](20_lage_pruefung_viewer.md)) |
| M26 | BUI: `bim-toolbar-section` sets the `label-hidden` of its buttons from its `vertical` when it mounts (and lit does not set it again if the value does not change): for an icon-only bar, use our own groups (`div`) inside `bim-toolbar` | Bar with labels despite `label-hidden` |
| M27 | A lit app with a persistent foreign component (the viewer): keep it in a fixed element of the template and **do not move it** to another parent (web components unmount and remount); show or hide it with CSS; with `display:none` the framing waits for a size (M25) | Viewer that does not reload between *Lage* and *Modell* |
| M28 | Calibrating with **scale (measured distance or 1:n) + reference point + rotation** is as exact as two control points and easier to check; locking the plan before dragging avoids moving Bohrungen by accident | 1:500 · 10.0° from the UI; D67 |
| M29 | That Open, `RendererMode.MANUAL`: with `turnOffOnManualMode` every `update()` draws **without** postproduction and 50 ms later **with** it. If something requests frames all the time (every mouse move, a 1 s interval) the image alternates forever: flicker. Decide the postproduction yourself (`turnOffOnManualMode = false`, `manualDefaultStyle` = style), right before drawing (`renderer.onBeforeUpdate`, after moving the camera), only on real activity (camera, loading, dragging); never in Lage mode; no redraw just for moving the mouse | Plan that flickered even when transparent; `check.mjs` B, `check_app.mjs` C2 |
| M30 | three.js `GTAOPass` sets `PERSPECTIVE_CAMERA` **only when created**: after switching to orthographic it keeps decoding the depth as perspective and, with the negative `near` of the orthographic camera (M18), gives false shadows or a **black viewer** depending on the GPU. Update the *define* (and `needsUpdate`) on every projection change | User's screenshot: black Lage with a valid HUD |
| M31 | 6–7 digit coordinates in the scene: the **origin** must be close to what is shown. Without Bohrungen with a position, the origin comes from the reference point of the calibrated plan; if the origin changes, the camera (and the saved view) moves by the same amount; if the plan jumps far away when its coordinate is typed, the camera follows it; the vertices of the plan are relative to its corner (Float32) | The first dropped Bohrung moved the origin and everything disappeared; empty preview |
| M32 | A pending "pick a point" blocked **all** dragging without a warning. When locking the plan, when starting to drag from the list or with the plan locked, cancel the pending pick | `check_app.mjs` C2 |
| M33 | EPSG never as a free number: a **list** (DE/AT/CH, codes and names verified with pyproj) and a **plausibility range** per system (digits, zone prefix); an unknown code from the PDF is shown marked, not hidden | "EPSG 52" in the HUD; R 74,848.90 → "fits no system" |
| M34 | Orthographic view with a negative `near`: `Raycaster.setFromCamera` starts the ray **at the camera plane**; what lies between `near` and the camera (e.g. the raised GOK of a Bohrung) is never hit. Move the origin to `near` in all our own rays; and draw the plan at the height of the Bohrungen, not at a fixed elevation | Bohrungen with a GOK could not be dragged, GWM without a GOK could |
| M35 | That Open `setOrthoCamera` derives the orthographic frame from the perspective camera (depth to the target) and `setOrthoPerspCameraAspect` scales it with the previous size of the viewer: without a placed camera or with the viewer still without a size it comes out **negative or huge** (image rotated by 180°, zoom stuck at `minZoom`). Normalise after every change of projection and of size | Calibration with «Drehung 180»; plan invisible when opened directly |

## X. Working environment

| # | Rule | Evidence |
|---|---|---|
| X1 | In Claude's environment, downloading Gutachten from municipal websites is **blocked** (403/000); pypi and GitHub are not. The user uploads the PDFs | Rounds 1–3 |
| X2 | Test heavy dependencies (swissgeol, OCR) in **separate environments** in the scratchpad; swissgeol pins PyMuPDF 1.26.3 | `sgvenv` |
| X3 | `pkill -f pattern` in a command that contains that text anywhere **kills itself** (also with `[p]attern` if the name appears later in the same command): run `pkill` in a separate command | Exit 144 three times |
| X4 | `python -I` does not add the script's folder to `sys.path`: scripts must insert it themselves | `ablation.py` |
| X5 | `show_pdf_page` ignores the `/Rotate` of the source page; compensate when recomposing PDFs | First version of `perturb.py` |
| X6 | Expensive OCR → **cache per page image** (hash) so that regression and ablation are fast | `GEO_OCR_CACHE` |
| X7 | Every process that loads the OCR model takes several GB: 4 ablation processes in parallel **ran out of memory and restarted the container**. Load the model only on a cache miss and use ≤ 2 processes | Restart during the final ablation |
| X8 | The ablation reloads the module for every configuration: **do not edit the module while it runs** (versions would mix); test changes in a copy with another name | Final ablation |
| X9 | **web-ifc 0.0.78**: the browser `web-ifc.wasm` does not match its JS (`StreamMeshes called with 4 arguments, expected 3`); in Node it works. In the viewer, 0.0.77 | `apps/web` |
| X10 | That Open downloads WASM (`autoSetWasm`) and worker (`getWorker`) from unpkg by default: copy them to `public/vendor` (`npm run vendor`) to work offline and with pinned versions | `apps/web` |
| X11 | `vite preview` serves `dist/`: an IFC copied to `public/` after the build is not visible; the check copies the IFC to `dist/` | Screenshots with old volumes |
| X12 | Streamlit reloads modules when files change: rebuilding the viewer with the app running leaves it without its component (`dist/index.html` is missing for a moment). Restart the app after the build | Viewer not loading in the test |
| X13 | A new element above the component (e.g. the extraction's `st.status`) **re-mounts** it: new iframe, state reset. The tests detect the iframe change | `check_app.mjs` |
| X14 | Streamlit serves the component's files with `mimetypes`; on Windows the registry can give `text/plain` for `.js` and block modules/workers: register the types in the app | `ui/viewer.py` (precaution; not seen on Windows yet) |
| X15 | With SwiftShader (Chromium without a GPU) a frame with postproduction takes ~1 s: whatever is updated "every frame" (DOM marks, state) lags behind and same-origin iframes block the page. The tests wait for frames (`requestAnimationFrame` ×2) and read the state at that moment; on-demand rendering eases it | `check.mjs`, `check_app.mjs` |
| X16 | `vite build` **empties `dist/`** (including copied test IFCs); and the server answers a missing file with `index.html`: check the `content-type` before passing it to web-ifc | `OpenModel … reading 'arguments'` |
| X17 | The project autosave makes a repeated test start with the previous state: the app tests press *Alle Korrekturen verwerfen* (⋯ menu) when opening each project | `check_app.mjs` |
| X18 | Playwright: `page.mouse` uses window coordinates; an iframe below the fold has to be brought into view (e.g. a click on one of its elements) before dragging | Dragging without effect in the app |
| X19 | X3 also applies to `pgrep -f pattern \| xargs kill`: the command that contains it matches itself | Exit 144 |
| X20 | Keyboard shortcuts: ignore them only in text fields, **not** with the focus on a button (after pressing *Nächste* the focus stays on it and ↓ stopped working); close menus after an action | `check_app.mjs` A |
| X21 | Playwright: the value of an `<input>` is not part of the text of its row (`hasText` does not find it): find the index by `value` with `evaluate` | *Einheiten* test |
| X22 | A render error that only appears on the user's GPU (black, flicker) is not visible in SwiftShader: measure the **sequence of frames** (wrap `postproduction.update` and `three.render`) instead of looking at screenshots, and reproduce the exact case (here: no Bohrung with coordinates) | Reproduction of the user's screenshot |
| X23 | A Node `console.log` is lost if `timeout` kills the process with its output in a pipe: write to a file (`> log 2>&1`) | Reproduction scripts without output |
| X24 | **Realistic** test data: elevations of hundreds of m NHN, Bohrungen without a GOK, and the app also opened directly by URL. With 38 m NHN and always the same path through the steps, two camera errors passed all tests | `testplan.py` (GOK + 300 m), `check_app.mjs` C2/C3 |
| X25 | **Docker in the cloud session:** the daemon is not running (start `dockerd` in the background) and deb.debian.org is blocked (apt fails): build with `--build-arg OCR=0`, `--network host`, the session proxy's `HTTPS_PROXY` and its CA as a secret (`--secret id=ca,src=…` and `PIP_CERT=/run/secrets/ca` in a test Dockerfile). The CI tests the container's OCR. `check_app.mjs` logs in with `GEO_AGENT_PASSWORT` | Image 1.15 GB, 28/28 `check_app.mjs` against the container ([22](22_deployment.md)) |
| X26 | A `dockerd` started as a background shell stops when that shell's time limit runs out (30 min by default): start it with the longest limit and check `docker info` before building | Build failed with "no such file … docker.sock" halfway through |
| X27 | Generic environment variable names collide with the system: tcsh sets `HOST` to the machine name, which would have put the server on the network. Use app-specific names (`GEO_AGENT_HOST`); `PORT` stays because the platforms set it | Review of `server/__main__.py` |
| X28 | Local health checks with `urllib` must bypass the proxy (`ProxyHandler({})`): a company proxy from `HTTP_PROXY` does not know this machine's 127.0.0.1 | `scripts/online.py` |
| X29 | The repository was renamed twice (CAD_Extract → GeoIM → GroundTwin). `git push` keeps working through GitHub's redirect and prints "This repository moved"; the session's GitHub tools only accept the name in the session scope. When a push mentions a move, check `list_repos` and update links | Push output; Actions run read via the old name |

Up: [Index](README.md)

Related: [15 Real results](15_results_real_pdfs.md) · [11 Decisions](11_decisions.md) · [09 Validation](09_validation_benchmark.md) · [Architecture](ARCHITECTURE_BAUGRUNDMODELL.md) · [18 Layer modeler](18_layer_modeler.md) · [21 Step app and norms](21_app_schritte_normen.md) · [22 Online](22_deployment.md)
