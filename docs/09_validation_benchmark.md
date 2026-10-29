---
title: "Validation and benchmark of the extraction"
date: 2026-10-23
tags: [geo_agent, validation, benchmark, ground-truth, tests]
aliases: [Benchmark, Ground truth, Validation]
---

# Validation and benchmark of the extraction

**Conclusion:** without a test bench, "generalising" cannot be demonstrated. Three things are
needed: a **ground truth format** (adopted from swissgeol, with extensions), a **corpus** (synthetic
for CI + real for calibration) and **metrics** in which the main one is the **silent error rate**:
wrong data that the app marks as certain.

> [!NOTE]
> With **real PDFs** (5 public Gutachten): v1 0/29. In the **blind test**, v3 0/13 and swissgeol
> 13/13 (with 18 false ones). After the fixes, v3 reaches 29/29 Bohrungen and 143/143 boundaries,
> training figures. See [15 Real results](15_results_real_pdfs.md) and the blind protocol (D25).

## 1. Current results (spike, synthetic PDFs)

Reproduce: [`spikes/extraktion_v2/README.md`](../spikes/extraktion_v2/README.md).

| Layout | current v1: boundaries / Bodenart | v2 prototype: boundaries / Bodenart / Schraffur | swissgeol unchanged: boundaries / Bodenart |
|---|---|---|---|
| A reference | 18/18 · 18/18 | 18/18 · 18/18 · 18/18 | 18/18 · 18/18 |
| A2 M 1:50 | 18/18 · 18/18 | 18/18 · 18/18 · 18/18 | 18/18 · 18/18 |
| A3 text closer | 18/18 · **6/18 (7 in green)** | 18/18 · 18/18 · 18/18 | 18/18 · 18/18 |
| A4 centred header | **0/18** | 18/18 · 18/18 · 18/18 | 12/18 · 12/18 |
| A5 contradiction text/Schraffur | 18/18 · 18/18, **no warning** | 18/18 · 18/18 · 17/18 + **1 correct issue** | (does not read the Schraffur) |
| B another office + DPH | **0/12** | 12/12 · 12/12 · 12/12 | 0/12 because of swapped names* |

In addition, v2: GOK 17/17, water 17/17 (±5 cm), coordinates 17/17, DPH 32 steps with a maximum
error of 0.4 N10, scale detected without configuration (1:100 and 1:50), no false Bohrungen or
Schichten, ~1 s per PDF. swissgeol: 0 water, 0 elevations, 0 coordinates and false Schichten from
the legend ([08 §4](08_swissgeol_reuse.md#4-test-swissgeol-unchanged-on-our-pdfs)).

\* depths and texts correct, assigned to the name of the neighbouring DPH diagram.

> [!WARNING]
> The synthetic PDFs were written by the same author as the v2 prototype. They show that the method
> works and that v1 depends on the layout; they do **not** show robustness on real drawings. The
> next mandatory step is the real corpus (§3).

## 2. Ground truth format

Base: swissgeol's `ground_truth.json` (`docs/groundtruth-json.md` in their repo): per PDF, a list of
Bohrungen with `metadata` (coordinates, elevation, name, total depth), `layers` (`depth_interval`,
`material_description`) and `groundwater` (`depth`, `elevation`, `date`). Our own extensions
(optional fields, compatible with their reader):

```jsonc
{
  "Bohrprofil_Projekt_X.pdf": [{
    "borehole_index": 0,
    "metadata": {"original_name": "B 18/19", "reference_elevation": 6.20, "total_depth": 35.0,
                 "coordinates": {"E": 565081.64, "N": 5933169.81},
                 "crs_epsg": 25832, "height_datum": "DHHN2016"},              // + ours
    "layers": [{"depth_interval": {"start": 0.0, "end": 0.3},
                "material_description": "Mutterboden, humos, dunkelbraun",
                "soil_class": "Mutterboden", "hatch_class": "Mutterboden",   // + ours
                "din": {"main_fraction": "Mu"}}],                            // + ours
    "groundwater": [{"depth": 2.55, "elevation": 3.65, "date": "2019-03-08",
                     "kind": "angetroffen"}],                                // + our kind
    "soundings": [{"code": "DPH 1", "quantity": "N10",                      // + ours
                   "values": [[0.0, 0.5, 26], [0.5, 1.0, 19]]}]
  }]
}
```

Advantage: the same file scores Geo_Agent **and** swissgeol (`boreholes-score`).

## 3. Corpus

| Corpus | Content | Use |
|---|---|---|
| Synthetic | Generator `synth_bohrprofil.py`, extendable: page rotation, several rows of Bohrungen, multi-page Bohrungen, 4-line rectangles, `/Pattern` fills, thin Schichten with leader lines, CPT, simulated scan (render + OCR) | CI on every commit |
| Current reference | The PDFs of the current project (not versioned) with their validated Excel | Non-regression from v1 → v2 |
| Real, multi-office | 5–10 **public** Gutachten from different offices/software (GGU-STRATIG, DC-BOHR, WinBohr, AutoCAD) in a private bucket; sources and criteria in [12](12_public_corpus.md) | Calibrate thresholds and weights; measure for real |

The real ground truth is built **semi-automatically**: run v2 → correct in the review UI → export
as ground truth (human review is already part of the workflow, see
[architecture §4.2](ARCHITECTURE_BAUGRUNDMODELL.md#42-data-flow)).

## 4. Metrics

| Metric | Definition | Target |
|---|---|---|
| **Silent error** | wrong Schichten/values with high confidence (green) / total | **≈ 0**; main KPI |
| Boundary recall | boundaries with \|Δ\| ≤ 2 cm / true boundaries | ≥ 0.98 |
| Schicht precision | extracted Schichten that exist in the ground truth / extracted Schichten | ≥ 0.98 (penalises legends read as Bohrungen) |
| Bodenart accuracy | by text, by Schraffur and merged | ≥ 0.95 merged |
| Review coverage | values marked for review / total | report it (low, but not 0 with real data) |
| Metadata | name, GOK (±1 cm), coordinates (±1 cm), water (±5 cm) | ≥ 0.95 |
| Sondierungen | max. error per step / RMSE of the curve | ≤ 1 N10 |

The targets are proposals, to be fixed with the real corpus.

## 5. CI integration

1. `pytest` generates the synthetic corpus in a temporary directory.
2. It runs v1 (while it exists) and v2, compares with the ground truth, and fails if a metric drops
   compared with the last accepted version (thresholds in a versioned YAML).
3. Optional, nightly: swissgeol as an oracle on the same corpus.

Up: [Index](README.md)

Related: [01 Diagnosis](01_diagnosis_fixed_layout.md) · [02 Bohrprofil](02_bohrprofil_generalization.md) · [08 swissgeol](08_swissgeol_reuse.md) · [10 Plan](10_implementation_plan.md)
