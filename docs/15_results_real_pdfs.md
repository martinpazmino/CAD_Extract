---
title: "Results with real PDFs (round 1, three blind rounds and test bench)"
date: 2026-10-25
tags: [corpus, validation, results, extraction]
aliases: [Real results, First corpus round]
---

# Results with real PDFs (round 1, three blind rounds and test bench)

**Conclusion:**
- **v1 (current):** 0 of 58 Bohrungen in nine public Gutachten.
- **Round 1** (3 PDFs): v3 works after seven changes that the synthetic PDFs did not reveal.
- **Blind test 2** (2 new PDFs, code frozen): **v3 got 0 of 13**. swissgeol got 13/13 Bohrungen,
  but no elevation and 18 invented Bohrungen.
- **Blind test 4** (4 Swiss examples from swissgeol, another domain): v3 and v4 **0 of 3**, no false
  ones (§8.2).
- **v4 + test bench** (training, §8): 87/92 Bohrungen, 541/541 boundaries (538 exact to the cm),
  0 false data; robust to rotation, conservative on raster; full chain PDF → PostGIS → IFC → That
  Open.
- **Blind test 3** (4 new PDFs, predictions frozen in the repo): **v3 got 11 of 29**, with elevation
  12/23 and 1 false Bohrung. swissgeol got 12 of 29 (one without Schichten), no elevations and 25
  false Bohrungen (§7). The 18 missing Bohrungen are in a raster without text (11) or in a title
  with a suffix (5) or an AutoCAD drawing with text converted into lines (1), plus one wrong
  instance.

The lesson is that the geometry gives precision and control of false positives, while tolerance to
unknown text formats is swissgeol's strong point. **The solution is to combine both** (§6). After
fixing the general causes, v3 reaches **29/29 Bohrungen and 143/143 boundaries**, including a
scanned PDF.

> [!WARNING]
> The figures **after** each fix are *training* figures. The only honest figures of generality are
> those of the blind tests: **0/13** (§6.1), **11/29** (§7.1) and **0/3** (§8.2, Switzerland). The
> next round with new German Gutachten must be measured with v4 frozen ([12](12_public_corpus.md)).

## 1. The documents

| PDF | Office / software | What it contains | Particularities |
|---|---|---|---|
| Wachenroth (B-Plan Angerleite, BY) | Geotechnik Prof. Dr. Gründer · PDF24/Ghostscript | 6 Bohrprofile (1 per page, M 1:25) + height section (M 1:75) + DIN 4023 legend | Report text **scanned** (pp. 1–34 without text); drawing made of **965 loose segments without fills**; labels = **base** of the Schicht |
| Talheim (Sickerwassertrasse, BW) | GeoTech Kaiser · Word + CAD | 8 BK + 2 GWM on **pages rotated 90°**, mNN axis, Höhenmaßstab 1:75 | Labels = **top** with 0.00, **offset** with leader lines; column edges drawn in pieces; white masks behind the text; GW with a line to its column |
| Halle (B-Plan 152, ST) | Word | Only the report text, **without the Bohrprofil annexes** | Table of Grundwasser levels (26 KRB), parameter tables and Homogenbereiche |

Reference ground truth transcribed by hand and checked against the images:
[`spikes/korpus/groundtruth/`](../spikes/korpus/groundtruth/wachenroth.json) (factual data only:
codes, elevations, depths, soil class, water; with the URL and `sha256` of the PDF).

## 2. Results of round 1

Boundary tolerance 5 cm (at M 1:75, 1 pt = 2.6 cm); 1:1 matching.
Reproduce: `python spikes/korpus/eval_real.py <pdfs> [<swissgeol output>]`.

| | current v1 | **v3 prototype** | swissgeol (unchanged) |
|---|---|---|---|
| **Wachenroth** Bohrungen / boundaries | 0/6 · 0/18 | **6/6 · 18/18** | 6/6 · 18/18 |
| Bodenart | — | **18/18** (incl. *Sandstein* = rock) | (does not classify) |
| GOK | 0/6 | **6/6** | 6/6 |
| False (Bohrungen / GW) | 0 / 0 | **0 / 0**; duplicates from the section merged | **5 / 1** (duplicated section, lab report) |
| **Talheim** Bohrungen / boundaries | 0/10 · 0/65 | **10/10 · 65/65** (+1 false boundary, marked) | 0/10 · 0/65 |
| GOK / GW | 0/8 · 0/4 | **8/8 · 3/4** | 0/8 · 0/4 |
| False Bohrungen | 0 | **0** | 3 (from the report text) |
| **Halle** (has no logs) | 0 false | **0 false** | **4 false** (from tables) |
| Halle GW table | — | **26/26** (reading per cell) | — |

## 3. Seven lessons from the real drawings

| # | What happened | Change in v3 | Note affected |
|---|---|---|---|
| L1 | The PDF regenerated with Ghostscript/PDF24 has no rectangles or fills: only segments | **Everything to segments**; column = pair of stroked verticals; boundaries = horizontals touching both edges | [02](02_bohrprofil_generalization.md) |
| L2 | Page with `/Rotate 90`: PyMuPDF gives unrotated coordinates | Normalise words and paths with `page.rotation_matrix` | [02 §8](02_bohrprofil_generalization.md#8-cases-not-yet-covered) |
| L3 | Labels offset with leader lines; some offices label the **top** (with 0.00), others the **base** | Scale from candidates (direct, by order, text `1 : 75`) and the one that **confirms the most labels** wins; the convention decides how the descriptions are assigned | [02 §3](02_bohrprofil_generalization.md#3-vertical-scale-by-regression) |
| L4 | In the height representation the header is far above the column | Associate the header with the column below without a vertical limit | [03](03_laengsschnitt_generalization.md) |
| L5 | Tables with "B 6" and increasing numbers looked like a Bohrung (M 1:12) | Normalised scales (±4 %), column with numbers inside = table, duplicates → the version with GOK and more confirmed labels | [09](09_validation_benchmark.md) |
| L6 | The Schraffur of *Ton* (stripes) and of *Schwarzdecke* (two lines) crosses the column as if it were boundaries | Exclude dashed lines and require the boundary to touch the edges; label↔boundary confirmation **1:1**, so that an extra boundary stays marked | [04](04_schraffur_din4023.md) |
| L7 | v1 classifies `Sandstein` → *Sand*, `Tonstein` → *Steine*, `Beton` → *Ton*, all "certain" | Main noun + list of rocks (`-stein`) and man-made materials (Beton, Schwarzdecke, Anschüttung → Auffüllung), Oberboden = Mutterboden | [01](01_diagnosis_fixed_layout.md), [02 §5](02_bohrprofil_generalization.md#5-classifying-the-text-noun-not-adjective) |

In addition, the real Grundwasser confirms two details: the triangle can sit next to the
**neighbouring** column and what assigns the Bohrung is the end of the **water line**; and
"kein Grundwasser" is data to be stored (6/6 in Wachenroth), not an absence.

## 4. What still fails or was not tested

- **GW "angebohrt" of BK2 (Talheim)**: it is another symbol (two strokes + line). Reading the water
  symbols from the legend of the document is still missing ([06](06_grundwasser.md)).
- **1 false boundary** (double line of *Schwarzdecke* in BK5): it stays marked as unconfirmed. Better
  solution: recognise that Schraffur through the legend.
- **Classification by Schraffur not evaluated on real drawings**: the legend samples in Wachenroth
  are squares of loose lines and those in Talheim combine colour and letters; the prototype's sample
  detector only accepts filled rectangles ([04](04_schraffur_din4023.md)).
- **Coordinates**: none of the three has a coordinate table. The Lagepläne mix raster and vector
  ([07](07_coordinates.md)).
- **Scanned text** (Wachenroth, pp. 1–34): needs OCR for the Homogenbereiche and the parameters of the
  report.
- **Full descriptions** (Nebenanteile, consistency): only the main class was evaluated.
- **Sondierungen**: none of the three has vector DPH curves.

## 6. Blind test: Hausham and Rednitzhembach

### 6.1 Blind result

Protocol: predictions frozen with the code of commit `d35e3d4` **before** looking at the PDFs; then,
transcription of the ground truth and scoring ([`blind_test.py`](../spikes/korpus/blind_test.py)).

| PDF | What it is | v1 | **v3 (blind)** | swissgeol (blind) |
|---|---|---|---|---|
| Hausham (Frank + Bumiller + Kraft, **DC-Software**) | Vector, 3 B + 6 RKS, labels `0.20m`, RKS scale fitted to the page | 0/9 | **0/9** | **9/9 · 45/45 boundaries · 4/4 GW**; GOK 0/9; **15 false Bohrungen** |
| Rednitzhembach (Prof. Dr. Gründer) | **Scanned** with an OCR layer, 4 B, M 1:50 | 0/4 | **0/4** | 4/4 · 6/15 boundaries; GOK 0/4; 3 false |

### 6.2 Why v3 failed and what was changed afterwards

| # | Cause | Change (general, not specific to the PDF) |
|---|---|---|
| L8 | Labels with the unit attached (`0.20m`); "Kein Wasser" | Label pattern with an optional unit; more "no water" phrases |
| L9 | DC-Software fits the scale of the log to the sheet (M ≈ 1:35) | A non-normalised scale is accepted if ≥ 80 % of ≥ 3 labels confirm it (corrects L5) |
| L10 | Grundwasser as text `GW 2.53m`; the ▽ of the elevation ruler and the ▼ of the starting elevation looked like water | GW also from text; series of aligned triangles, triangles with an elevation next to them and triangles at depth 0 are discarded |
| L11 | **Scan** without vectors | **Raster adapter:** OpenCV detects horizontal and vertical lines in the image and turns them into the same segments the vector logic uses; the depth comes from the scale in the title block (`M 1:50`) when OCR loses labels; the scan's duplicate lines are merged |
| L12 | The same Bohrung on its own sheet and in a section | Prefer the sheet titled `Bohrung B 4` and the sheet with a single Bohrung; a label confirmation < 50 % does not count |

### 6.3 Total over the five PDFs (after the fixes = training)

| | v1 | v3 | swissgeol |
|---|---|---|---|
| Bohrungen | 0/29 | **29/29** | 19/29 |
| Boundaries | 0/143 | **143/143** (+1 false, marked) | 69/143 |
| GOK | 0/27 | **27/27** | 6/27 |
| Grundwasser | 0/8 | **7/8** | 4/8 |
| Bodenart (Schichten with ground truth) | — | **59/61** | (does not classify) |
| False Bohrungen / GW | 0 / 0 | **0 / 0** | **30 / 1** |

The 5 boundaries of B4 (Rednitzhembach) come from geometry and scale only, without readable labels,
and stay **marked for review**. That is the intended behaviour.

### 6.4 Consequence for the architecture

1. **Combine the two approaches:** swissgeol's search for depth columns is tolerant to formats
   (units, OCR, positions). Our geometric part does the validation: column, scale, boundaries,
   header and the filters for tables and duplicates. Their catalogue of label formats has to be
   ported and extended ([08](08_swissgeol_reuse.md)).
2. **One core, two sources of segments:** vector (`get_drawings`) or raster (OpenCV). Scans are no
   longer a special case ([02](02_bohrprofil_generalization.md)).
3. **The blind test is part of the process:** every new round is frozen before looking.

## 7. Blind test 3: Triefenstein, Marl, Wesel and Berlin

### 7.1 Blind result

Strengthened protocol: the predictions of v3 (commit `36e3554`) and of swissgeol were frozen and
**pushed to the repo before the PDFs were opened** (commits `5325ead` and `2d4d5e7`,
[`spikes/korpus/frozen/runde3/`](../spikes/korpus/frozen/runde3/marl_251.json), with the `sha256` of
the PDF); the ground truth came afterwards (`acc5cd5`). That way the order is proven by the git
history.

| PDF | Office / software | What it is | **v3 (blind)** | swissgeol (blind) |
|---|---|---|---|---|
| Triefenstein B-Plan 41 (BY) | Geotechnik Badel | Vector, 5 RKS on single sheets at M 1:30 and 1:25, titles `RKS 1 - Betonweg 0+050`, descriptions only as DIN 4023 abbreviations; DPH as a **table of values** | **0/5** | 0/5 · **15 false Bohrungen** |
| Marl B-Plan 251 (NRW) | Dr. Spang · **IDAT/GeoDin** | Vector, 12 BS at M 1:50 with a column of samples Von/Bis next to the labels, Längsschnitt with DPH, GWM construction on the sheet of BS 10 | **12/12** (BS 10 taken from the section) · 91/97 boundaries · **GOK 12/12** · 1 false Bohrung | 11/12 · 87/97 · GOK 0/12 · 6 false |
| Wesel Anlage 12 (NRW) | Asmus + Prabucki · **AutoCAD** | 1 Bohrung of 38 m, log at M 1:200 with **SHX text converted into lines** (no text layer); DIN 4022 Schichtenverzeichnis as text; core photos | **0/1** | 1/1 · 0/24 boundaries · 3 false |
| Berlin V-67b-VE | GuD Consult | Voruntersuchung without its own Bohrungen: 11 third-party Bohrungen (Geoportal Berlin and archive) as **raster images without text**, with CPT and UTM 33N coordinates in the image | **0/11** | 0/11 · 1 false |
| **Total** | | | **11/29 correct** (+1 wrong instance) · 91/200 boundaries · GOK 12/23 · GW 0/4 · 1 false | 12/29 (1 without Schichten) · 87/200 · GOK 0/23 · GW 0/4 · **25 false** |

v3 was precise where it read (Marl: 87/87 boundaries in the 11 correct Bohrungen and all elevations),
but it fell over completely on format details a human does not even notice. swissgeol again found
depths where v3 did not, at the price of many false ones and no elevation.

### 7.2 Why it failed and what was changed afterwards

| # | Cause | Change (general) | Effect (training) |
|---|---|---|---|
| L13 | Title with a suffix: `RKS 1 - Betonweg 0+050` (name and station) | The header accepts `<code> - <text>` | Triefenstein 0/5 → **5/5 · 24/24 · GW 2/2** |
| L14 | The depth scale of the DPH diagram in the section (1.00 … 10.00) passed for labels of BS 10 | Groups of labels in **arithmetic progression** (≥ 5 values, same step) = axis or ruler, not boundaries. swissgeol already did this and we had not ported it ([08](08_swissgeol_reuse.md)) | Marl BS 10 correct, 97/97 |
| L15 | IDAT puts a column of samples with Von/Bis pairs (`0,20 / 0,60`) next to the labels; the GWM construction drawing looked like a second Bohrung | Group with duplicate values = column of samples. A column without confirmed labels, when the neighbouring ones do have them, is not a log. Without any label on the page (OCR lost) the scale of the title block is kept | 0 false Bohrungen. The first version of this rule broke B 4 of Rednitzhembach and the training set caught it |
| L16 | Description only in abbreviations (`U, t, s´`, `fS, ms´`, `A (S, u´)`) | Main fraction from the DIN 4023 / EN ISO 14688 abbreviation | Bodenart Triefenstein 18/24, Marl 18/23 |
| L17 | AutoCAD with SHX fonts: the labels are lines and the log cannot be read without OCR | **Schichtenverzeichnis** (DIN 4022 form, the same in all offices) as a second source: depth in column 1, name under `a)` and water in column 3. Compared 1:1 with the log | Wesel **1/1 · 24/24**; check "SV ok" on 14/14 Bohrungen of Hausham and Triefenstein |
| L18 | Third-party Bohrungen as **raster without a text layer** (Geoportal screenshots, archive scans); codes `422C-460`; CPT | No change: an **OCR** step (ocrmypdf/Tesseract) is needed before the pipeline; the raster adapter (L11) already covers the lines | Berlin stays at 0/11 |

### 7.3 Total over the nine PDFs (after the fixes = training)

| | v1 | v3 | swissgeol (unchanged) |
|---|---|---|---|
| Bohrungen | 0/58 | **47/58** (the remaining 11 are the Berlin raster) | 31/58 |
| Boundaries | 0/343 | **288/343** (+1 false, marked) | 156/343 |
| GOK | 0/50 | **39/50** | 6/50 |
| Grundwasser | 0/12 | **9/12** | 4/12 |
| Bodenart (Schichten with ground truth) | — | **119/132** | (does not classify) |
| False Bohrungen | 0 | **0** | **55** |

The synthetic ones do not change (102/102). Reproduce: `python spikes/korpus/eval_real.py <pdfs>`.

### 7.4 What we learned

1. **The bottleneck is no longer the geometry but the input:** of the 18 lost Bohrungen, 12 had no
   readable text (raster or SHX). OCR becomes a component, not an extra.
2. **The Schichtenverzeichnis is the most stable source:** it is a standardised form, it comes as
   text even when the drawing is an image, and it serves to verify every log
   ([02](02_bohrprofil_generalization.md)).
3. **Small rules, big effects:** a suffix in the title knocked out a whole Gutachten (0/5). Header
   detection must be tolerant and the geometric validation strict (D26).
4. **The training set as a regression test** caught a rule that broke Rednitzhembach. Every change is
   measured against the nine PDFs and the synthetic ones.

## 8. Test bench, algorithm v4 and full chain (2026-10-26)

Everything in this section is **training** except §8.2 (round 4, blind). Algorithm:
[17](17_extraction_algorithm.md); rules: [16](16_lessons_learned.md).

### 8.1 The test bench

| Layer | What it is | Tool |
|---|---|---|
| Real | 13 PDFs with ground truth: 9 German Gutachten + 4 Swiss examples from swissgeol | [`regression.py`](../spikes/korpus/regression.py) |
| Stress | 17 minimal PDFs, **one per lesson** (title with suffix, rotated page, DPH axis, column of samples, abbreviations, SHX + SV, raster, third-party code, contradictory scale, distant header…) | [`stress_cases.py`](../spikes/extraktion_v2/stress_cases.py) |
| Synthetic | 6 layouts with Schraffur, water, DPH and coordinates | `synth_bohrprofil.py` |
| Perturbation | the 13 real ones rotated 90°, reduced to 70 % and rasterised at 150 dpi without text, with the same ground truth | [`perturb.py`](../spikes/korpus/perturb.py) |
| Ablation | each rule switched off separately | [`ablation.py`](../spikes/korpus/ablation.py) |

New metric: **exact boundaries** (to the centimetre, as printed) in addition to the 5 cm tolerance.

### 8.2 Blind round 4: Swiss examples from swissgeol

Predictions frozen and pushed before the PDFs were opened (v3 `6162150`, v4 `68f0b54`). Different
domain (Switzerland, scans with an OCR layer, French), ground truth with codes `RB 2/I`, `SST KB5`,
`MGR01`.

| | v3 (blind) | v4 (blind) | v4 afterwards (training) |
|---|---|---|---|
| Bohrungen | 0/3 | 0/3 | 2/3 (the French one stays at 0) |
| Boundaries | 0/26 | 0/26 | 26/26 exact |
| False | 0 | 0 | 0 |

Causes and changes: header `Sondierbohrung : SST KB 5` (T1), code split by the OCR (`RB` + `2 / I`),
OCR layer that loses text (L18b), scan with vector noise (E2), depth column of the form (T5), stacked
labels with a scale in points that is not the paper's (E5, T4) and a log only as a **text table**
(S6). The French document (negative depths at the start of each description) stays out.

### 8.3 v3 versus v4 on the same set (13 real + 13 stress + 6 synthetic)

| | v3 | **v4** |
|---|---|---|
| Bohrungen | 76/92 | **87/92** |
| Boundaries (±5 cm) | 451/541 | **541/541** |
| Exact boundaries (to the cm) | 414/541 | **538/541** |
| Bodenart | 282/295 | 300/315 |
| GOK | 65/81 | **74/81** |
| Grundwasser | 30/35 | **33/35** |
| Coordinates | 17/25 | **25/25** |
| False Bohrungen / boundaries / water | 0 / 3 / 0 | **0 / 0 / 0** |

With the current 17 stress cases (§8.5), v4 is at 91/96 Bohrungen and 554/562 boundaries (551 exact);
the 8 missing are those of s14, which are **deliberately** not emitted because scale and labels
contradict each other. Still not a single false value.

What is missing: 4 archive Bohrungen from Berlin (low-quality scans) and the French one; Bodenart
with oblique leader lines (Marl); "trocken" only in the text of the report (Triefenstein).

### 8.4 Perturbations (same ground truth, 13 real PDFs)

| Variant | Bohrungen | Boundaries | Exact | False (Bohrungen / boundaries / water) | Coordinates |
|---|---|---|---|---|---|
| Original | 56/61 | 369/369 | 366/369 | 0 / 0 / 0 | 7/7 |
| Rotated 90° | 56/61 | 369/369 | 366/369 | 0 / 0 / 0 | 7/7 |
| Reduced to 70 % | 54/61 | 300/369 | 293/369 | 1 / 2 / 0 | 6/7 |
| Raster 150 dpi without text | 46/61 | 203/369 | 196/369 | **0 / 0 / 0** | 4/7 |

- **Rotation:** robust. The first version uncovered a real failure (the SV reader ignored the
  rotation) and one in the tool itself (`show_pdf_page` ignores `/Rotate`, X5).
- **Scale:** it was the biggest weakness (57 false boundaries). The text `1:75` in the title block no
  longer counts if the PDF is reduced: now, if it contradicts the labels, the Bohrung comes out
  without Schichten and with a warning (E5). Talheim reduced still has no Schichten: its labels are
  offset with leader lines.
- **Raster:** conservative, without a single false value. The Schichtenverzeichnis is now also read
  by OCR (S8): Triefenstein 0/5 → 5/5 and Wesel 0/24 → 24/24 in the rasterised version. It still
  loses small text (Marl at 150 dpi), the ▽ symbol in the image (W4, attempt discarded) and columns
  made only of colour fills (E7).

### 8.5 Ablation: which rule protects which case

Each of the 28 rules in `RULES` was switched off separately on the full set
([table](../spikes/korpus/ablation_v4.md)). **22 rules are protected by at least one case**: switching
them off makes something measurable worse. The ones with the most effect:

| Rule switched off | What breaks |
|---|---|
| `rotation` (L2) | Talheim 10/10 → 0/10, Wesel 24/24 → 0, rotated case |
| `generic_heads` (T1) | Berlin 7/11 → 1/11, both Swiss ones, third-party code case |
| `ocr` (L18) | Berlin 7/11 → 0/11, raster case |
| `label_snap` (T2) | exact boundaries: Berlin 55 → 37, Talheim 65 → 45, Rednitzhembach 13 → 6 |
| `abbreviations` (L16) | Bodenart Marl 18 → 0, Triefenstein 18 → 1 |
| `gw_symbol_filter` (L10) | 54 false water levels in Hausham |
| `axis_filter` (L14) | 7 false boundaries in Marl |
| `sv_source` (S1) | Wesel 1/1 → 0/1, SHX case |

Six were left without a case protecting them. For four, new cases were written that now fail if the
rule is switched off: s14 (`scale_contradiction`), s15 (`top_convention`), s16
(`single_sheet_anchor`) and s17 (`dashed_exclusion`). Case s15 also uncovered a real failure: the axis
rule (L14) deleted the labels of Schichten of equal thickness; it was refined. Still without a case:
`table_filter` (its failures are covered by other rules) and `raster_gw_symbol` (switched off).

### 8.6 Regression as a safety net

During the night the battery caught **five** of our own errors before they were pushed: the
Schraffur rule that deleted real thin Schichten (Wachenroth, Rednitzhembach), `Bohrung` without a
suffix no longer being recognised (Berlin 7 → 2), the "label first" mode that slipped an elevation
in as a depth (Marl), the raster triangles that invented 146 water levels, and the scale rule that
deleted a Bohrung in Berlin. None reached the final result (P5).

### 8.7 Full chain with real data (the goal)

PDF → `prototyp_v4` → canonical JSON (provenance and confidence per Schicht) →
[PostGIS with the Supabase schema](../spikes/supabase/README.md) (56 Bohrungen, 383 Schichten from 10
Gutachten; Berlin in EPSG:25833 with correct distances; Swiss LV03 transformed to LV95) →
[IFC 4.3](../spikes/ifc_thatopen/README.md) (0 schema errors) → That Open (69 strata with geometry,
7 Bohrungen from Berlin). The Schichten with confidence < 0.6 (9 of 383) stay marked for review.

## 9. Next steps

1. **Fifth blind round with new German Gutachten** (the 4 blocked in round 3: Wolfsburg/GGU, NLWKN,
   Böblingen, Königslutter), with v4 frozen and pushed before looking. It is the only figure that
   will tell whether v4 generalises.
2. Raster: Schichtenverzeichnis by OCR, edges of colour fills (E7), water symbol by template from
   the legend (W4).
3. DPH from **tables** (Triefenstein: N10 every 10 cm as text) and CPT (Berlin) in the data model
   ([05](05_sondierungen.md)).
4. Legend samples from segments → Schraffur and water symbols with real data.
5. Bring lessons L1–L18 into the implementation plan ([10](10_implementation_plan.md)).

Up: [Index](README.md)

Related: [12 Corpus](12_public_corpus.md) · [09 Validation](09_validation_benchmark.md) · [02 Bohrprofil](02_bohrprofil_generalization.md) · [08 swissgeol](08_swissgeol_reuse.md) · [11 Decisions](11_decisions.md)
