---
title: "Sondierungen: digitising DPH/CPT curves"
date: 2026-10-23
tags: [geo_agent, extraction, sondierungen, dph, cpt]
aliases: [Sondierungen, Rammsondierung, Drucksondierung]
---

# Sondierungen: digitising DPH/CPT curves

**Conclusion:** the Sondierungen (Rammsondierung DPH/DPL/DPM, Drucksondierung CPT) are discarded
today (`geo_agent/bohrprofil.py:32`, README: "CPT-/Sonden-Spalten bewusst weggelassen"), but in a
vector PDF their curves are **exact polylines**. With the axes calibrated by regression (the same
technique as in the Längsschnitt) they can be digitised without loss.

**Status:** tested for DPH in the synthetic layout B (`soundings` in
[`prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py)): **32 steps**, maximum error
**0.4 blows N10** (rounding of the regression on the centre of the labels). CPT: design.

## 1. What they contain

| Type | Standard | Curve | Value |
|---|---|---|---|
| DPL / DPM / DPH / DPSH | DIN EN ISO 22476-2 | steps every 10 cm | `N10` (blows / 10 cm) |
| CPT / CPTu | DIN EN ISO 22476-1 | continuous | `q_c` [MN/m²], `f_s`, `R_f`, (`u_2`) |
| SPT (in the Bohrprofil) | DIN EN ISO 22476-3 | single numbers | `N30` |

Later use (Lagerungsdichte, consistency, model parameters): standardised correlations, done by the
geotechnical engineer; the app only delivers the data with its provenance.

## 2. Algorithm

1. **Find the diagram**: title with the regex `^(DPH|DPL|DPM|DS|CPT|SRS)\s*\d+…` and the frame
   (tall rectangle without fill) below it.
2. **Value axis**: integers in a row below the title (`0 10 20 30`) → fit `N10 = a·x + b`. Accept
   only if they form an arithmetic progression (≥ 3).
3. **Depth axis**: ruler of integers to the left of the frame (`1 2 3 …`) → `Tiefe = c·y + d`; if
   the diagram shares the axis with the Bohrprofil, reuse its regression
   ([02 §3](02_bohrprofil_generalization.md#3-vertical-scale-by-regression)).
4. **Curve**: the path without fill with ≥ 6 segments inside the frame. DPH: each vertical segment
   is a step `(Tiefe_oben, Tiefe_unten, N10)`. CPT: sample the polyline every 2 cm.
5. **Several curves** (CPT: `q_c` and `R_f`): separate them by colour, line width, dash pattern or
   OCG layer, and assign each one to its axis (a CPT usually has two horizontal scales).
6. **Validate**: monotonic depth, values inside the axis, last depth = the labelled Endtiefe.

## 3. Special cases

- Values beyond the axis are written as text at the edge (`N10 > 50`, `76`) → read the text instead
  of the curve and mark it `censored`.
- Logarithmic axes (some CPTs): fit on `log10(value)`.
- Diagram split over several pages → concatenate by depth.
- Scans: raster only → Fast Line Detector / vectorisation (swissgeol has line detection in raster,
  [08](08_swissgeol_reuse.md)); lower confidence.

## 4. Data model

```sql
create table soundings (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects on delete cascade,
  code text not null,                      -- 'DPH 1', 'CPT 3'
  kind text not null,                      -- 'DPH' | 'DPL' | 'CPT' ...
  collar geometry(PointZ),
  provenance jsonb not null default '[]',
  unique (project_id, code)
);
create table sounding_values (
  sounding_id uuid references soundings on delete cascade,
  depth_top numeric(7,2), depth_bottom numeric(7,2),
  quantity text not null,                  -- 'N10' | 'qc' | 'fs' | 'Rf'
  value real, censored boolean default false
);
```

It fits next to `boreholes` in the schema of the
[architecture §5.2](ARCHITECTURE_BAUGRUNDMODELL.md#52-supabase-schema-draft-migration); in IFC,
`Pset_SolidStratumCapacity.NValue` can take values aggregated per stratum.

Up: [Index](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalization.md) · [09 Validation](09_validation_benchmark.md) · [Architecture](ARCHITECTURE_BAUGRUNDMODELL.md)
