---
title: "Ablation v4"
date: 2026-10-26
tags: [spike, ablation]
---

# Ablation v4 (Regeln einzeln abgeschaltet)

Stand `a5edb89`, 13 echte PDFs + 13 Stressfaelle + 6 synthetische Layouts. Erzeugt mit `ablation.py`.

| Regel abgeschaltet | verschlechterte Faelle | Details |
|---|---|---|
| `rotation` | 4 | marl_251: Bodenart 18/23→12/23; talheim: Bohrungen 10/10→0/10, Grenzen 65/65→0/65, Grenzen exakt 65/65→0/65, Bodenart 8/8→-, GOK 8/8→0/8, GW 3/4→0/4; wesel_anlage12: Grenzen 24/24→0/24, Grenzen exakt 24/24→0/24, Bodenart 24/24→0/24; s02_gedreht: Bohrungen 1/1→0/1, Grenzen 5/5→0/5, Grenzen exakt 5/5→0/5, Bodenart 5/5→-, GOK 1/1→0/1, GW 1/1→0/1 |
| `dashed_exclusion` | 0 | — (kein Testfall belegt die Regel) |
| `table_filter` | 0 | — (kein Testfall belegt die Regel) |
| `nonstandard_scale` | 2 | hausham: GOK 9/9→3/9; s04_einheit_gwtext: Bohrungen 2/2→0/2, Grenzen 9/9→0/9, Grenzen exakt 9/9→0/9, Bodenart 9/9→-, GOK 2/2→0/2, GW 1/1→0/1, GW-Status 1/1→0/1 |
| `head_suffix` | 2 | triefenstein_bp41: falsche Bohrungen 0→1; s03_titel_zusatz: Bohrungen 1/1→0/1, Grenzen 5/5→0/5, Grenzen exakt 5/5→0/5, Bodenart 5/5→-, GW 1/1→0/1 |
| `generic_heads` | 4 | A7367: Bohrungen 1/1→0/1, Grenzen 11/11→0/11, Grenzen exakt 11/11→0/11, Bodenart 11/11→-, GOK 1/1→0/1, XY 1/1→0/1, GW-Status 1/1→0/1; berlin_v67b: Bohrungen 7/11→1/11, Grenzen 55/55→0/55, Grenzen exakt 55/55→0/55, GOK 6/11→0/11, GW 2/2→0/2, XY 5/5→0/5; example_borehole_profile: Bohrungen 1/1→0/1, Grenzen 15/15→0/15, Grenzen exakt 15/15→0/15, XY 1/1→0/1; s13_fremdcode: Bohrungen 1/1→0/1, Grenzen 4/4→0/4, Grenzen exakt 4/4→0/4, Bodenart 3/4→-, GOK 1/1→0/1, GW 1/1→0/1, XY 1/1→0/1 |
| `axis_filter` | 1 | marl_251: Grenzen 97/97→91/97, Grenzen exakt 97/97→91/97, Bodenart 18/23→12/23, falsche Grenzen 0→7 |
| `paired_filter` | 1 | marl_251: Bodenart 18/23→6/23 |
| `labelless_column` | 2 | marl_251: falsche Bohrungen 0→1; s06_proben_gwm: falsche Bohrungen 0→1 |
| `top_convention` | 0 | — (kein Testfall belegt die Regel) |
| `abbreviations` | 4 | marl_251: Bodenart 18/23→0/23; triefenstein_bp41: Bodenart 18/24→1/24; s03_titel_zusatz: Bodenart 5/5→1/5; s08_kuerzel: Bodenart 6/6→1/6 |
| `gw_symbol_filter` | 2 | hausham: GW-Status 5/5→0/5, falsches GW 0→54; s04_einheit_gwtext: GW 1/1→0/1, GW-Status 1/1→0/1, falsches GW 0→13 |
| `gw_text` | 1 | s04_einheit_gwtext: GW 1/1→0/1 |
| `gw_description` | 2 | berlin_v67b: GW 2/2→0/2; s13_fremdcode: GW 1/1→0/1 |
| `dup_preference` | 1 | marl_251: Bodenart 18/23→0/23, falsche Grenzen 0→4, falsches GW 0→7 |
| `sv_source` | 2 | wesel_anlage12: Bohrungen 1/1→0/1, Grenzen 24/24→0/24, Grenzen exakt 24/24→0/24, Bodenart 24/24→-, GW-Status 1/1→0/1; s11_shx_sv: Bohrungen 1/1→0/1, Grenzen 7/7→0/7, Grenzen exakt 7/7→0/7, Bodenart 7/7→-, GW-Status 1/1→0/1 |
| `ocr` | 2 | berlin_v67b: Bohrungen 7/11→0/11, Grenzen 55/55→0/55, Grenzen exakt 55/55→0/55, GOK 6/11→0/11, GW 2/2→0/2, XY 5/5→0/5; s12_raster: Bohrungen 1/1→0/1, Grenzen 5/5→0/5, Grenzen exakt 5/5→0/5, Bodenart 5/5→-, GOK 1/1→0/1 |
| `coords_text` | 4 | A7367: XY 1/1→0/1; berlin_v67b: XY 5/5→0/5; example_borehole_profile: XY 1/1→0/1; s13_fremdcode: XY 1/1→0/1 |
| `hatch_continuity` | 2 | talheim: falsche Grenzen 0→1; s09_schraffur: falsche Grenzen 0→2 |
| `label_snap` | 8 | berlin_v67b: Grenzen exakt 55/55→37/55; marl_251: Grenzen exakt 97/97→95/97; rednitzhembach: Grenzen exakt 13/15→6/15; talheim: Grenzen exakt 65/65→45/65; synth_A: Grenzen exakt 18/18→17/18; synth_A3: Grenzen exakt 18/18→17/18; synth_A4: Grenzen exakt 18/18→17/18; synth_A5: Grenzen exakt 18/18→17/18 |
| `scan_with_vectors` | 1 | example_borehole_profile: Grenzen 15/15→0/15, Grenzen exakt 15/15→0/15, falsche Grenzen 0→1 |
| `single_sheet_anchor` | 0 | — (kein Testfall belegt die Regel) |
| `depth_table` | 1 | A7367: Bohrungen 1/1→0/1, Grenzen 11/11→0/11, Grenzen exakt 11/11→0/11, Bodenart 11/11→-, GOK 1/1→0/1, XY 1/1→0/1, GW-Status 1/1→0/1 |
| `ocr_supplement` | 2 | A7367: Bohrungen 1/1→0/1, Grenzen 11/11→0/11, Grenzen exakt 11/11→0/11, Bodenart 11/11→-, GOK 1/1→0/1, XY 1/1→0/1, GW-Status 1/1→0/1; rednitzhembach: Grenzen exakt 13/15→8/15 |
| `label_first` | 1 | example_borehole_profile: Grenzen 15/15→0/15, Grenzen exakt 15/15→0/15 |
| `ocr_decimal_fix` | 1 | example_borehole_profile: Grenzen 15/15→14/15, Grenzen exakt 15/15→14/15 |
| `scale_contradiction` | 0 | — (kein Testfall belegt die Regel) |
| `raster_gw_symbol` | 0 | — (kein Testfall belegt die Regel) |

Up: [Corpus](README.md)
