---
title: "v1: Excel nach Vorlage"
date: 2026-10-29
tags: [v1, excel, bohrprofil, laengsschnitt]
aliases: [Excel v1, Geo_Template]
---

# v1: Excel nach Vorlage

The `geo_agent` package of the first version: two PDFs of one specific layout (Hamburg) → an Excel
with 4 sheets. It is started with [`start_excel.bat`](../start_excel.bat) or `streamlit run app.py`.
It only works for the layout it was built for (fixed positions,
[docs/01](../docs/01_diagnosis_fixed_layout.md)); for other Gutachten there is the step app of the
[README](../README.md). The sheet and column names below are those of the Excel template.

Input: **`Bohrprofil.pdf`** (DIN 4023, vector CAD) and **`Längsschnitt.pdf`** (Vortriebsplan with the
tunnel). Page *Excel nach Vorlage (v1)*: upload both PDFs → tick the dynamic columns → generate the
Excel. Only for the layout v1 was built for.

## Output — 4 sheets (exactly as in `Geo_Template.xlsx`)

| Sheet | Columns | Rows |
|---|---|---|
| **Geomodul** | Bohr_ID, NHN, Tiefe, Rechtswert, Hochwert | one per Kernbohrung |
| **Geomodul_Bodenschicht** | Bohr_ID, Bodenart, Tiefe(oberkante) | one per consolidated Schicht |
| **Geo_Tunnel** | Bohr_BID, NHN, OK Tunnel bis GOK, OK Tunnel, Achse, Sohle Tunnel, Tunnelmeter, Bodenart auf Tunnel | one per **Abschnitt** (zone of a Bohrung) |
| **Geo_Spec** *(dynamic)* | bodenart, abschnitt_id, Prozent_Bodenart_pro_abschnitt, bohr_id, Tunnelmeter **+ DIN columns** | one per **Abschnitt × Bodenart (≥ 5 %)** |

The DIN columns of sheet 4 (`kornbereich`, `nebenanteil_staerke`, `kalkgehalt`, `konsistenz`) only
appear if the corresponding section exists in the **legend of the Bohrprofil** — and only those the
user ticks. CPT/sounding columns are deliberately left out.

**Cell colours:** 🟩 green = certain · 🟨 yellow = uncertain / not classifiable (check by hand).

## How it works

### Bohrprofil (sheets 1 & 2) — proven

* Only **Kernbohrungen** (header `B nn/jj`); soundings (`DS`) and observation wells (`GWM`) are
  excluded, but they serve as the x limit of the Bodenart text band.
* Per Bohrung: depth column (pairs `(NHN_rel) tiefe`), Bodenart text band, diagram (ignored). Axis
  noise is filtered out.
* **Validation:** ground elevation − Endtiefe must give the last NHN value (e.g. B 18/19:
  −14.51 − 35.00 = −49.51 ✓). Visible per Bohrung in the tool.
* Sheet 2 consolidates consecutive equal Bodenarten and coarsens them for Civil 3D
  (Feinsand/Mittelsand/Grobsand → **Sand**, Glimmerschluff → Glimmerton). The Bodenart vocabulary
  comes from the legend (section BODENARTEN) — not hard-coded. If a Bodenart repeats within **one**
  Bohrung, it is numbered (e.g. `Sand`, `Sand1`, `Sand2`), so that every Schicht has a unique name.

### Längsschnitt (sheets 3 & 4) — the most delicate part, made checkable

* **X → Tunnelmeter** and **Y → NHN** through a linear regression of the axis labels.
* **Tunnel tube:** only the grey fill polygons (RGB ≈ 0.73) are rasterised as a clean mask → per
  Tunnelmeter OK (top) / Sohle (bottom) / Achse (middle). Validated to the centimetre against the
  `TS=…m` labels (Tunnelsohle) in the drawing.
* **Bodenart auf Tunnel:** derived **from the Bohrprofil**, not from the colours of the
  Längsschnitt. The depth of the tunnel axis below the GOK of the associated Bohrung falls into
  exactly one Schicht of sheet 2 → its Bodenart. In sheet 4 the tunnel cross-section (OK–Sohle)
  against the Schichten of the Bohrprofil gives the Bodenart proportions. (The evaluation of the
  colour polygons now only serves as a visual check in the preview image.)
* **abschnitt_id = zone of influence per Bohrung:** the tunnel is split into Abschnitte at the
  located Bohrungen. The boundary between two neighbouring Bohrungen lies at the **middle**
  ((TM_i + TM_{i+1})/2); the first zone starts at the beginning of the tunnel, the last ends at its
  end. That gives **one row per Abschnitt** instead of one per Tunnelmeter. In sheet 3 `NHN` is the
  **GOK of the Bohrung** (from the Bohrprofil, more precise than the terrain scan),
  `OK Tunnel bis GOK` = GOK − OK, and `Tunnelmeter` the station of the Bohrung. In sheet 4 the
  Bodenart composition along the tunnel (proportions in %) is broken down per Abschnitt.
* In the **"Tunnel-Vorschau"** tab a Prüfbild overlays the detected OK line (red), the Sohle (blue),
  the Abschnitt bands and the located Bohrungen on the original drawing — so that intermediate
  results are visible instead of being written blindly.

## Notes on the template

* **Sheet 1** contains `Rechtswert`/`Hochwert` according to the template. These coordinates are not
  in the Bohrprofil PDF and stay empty (marked yellow).
* **Sheet 3** of the template has **no** separate "Sohle" column (unlike the task description).
  `NHN` = GOK of the associated Bohrung, `OK Tunnel bis GOK` = cover (GOK − OK),
  `OK Tunnel`/`Achse` = tunnel geometry at the station of the Bohrung.
* `Bohr_BID` (sheet 3) and `bohr_id` (sheet 4) = the Kernbohrung that defines the Abschnitt (located
  in the Längsschnitt, with an existing Bohrprofil).

## Performance (v1)

The Bohrprofil is evaluated in < 1 s. The Längsschnitt takes ~20 s, because `page.get_drawings()`
works on a page with > 150,000 vector objects; the result is cached per upload, so that ticking and
unticking DIN columns reacts immediately.

Up: [Repository README](../README.md)

Related: [01 Diagnosis of the fixed layout](../docs/01_diagnosis_fixed_layout.md) · [Documentation index](../docs/README.md)
