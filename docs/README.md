---
title: "GroundTwin documentation: index"
date: 2026-10-23
updated: 2026-10-29
tags: [index, geo_agent]
aliases: [Index, Map of documents]
---

# GroundTwin documentation: index

Entry point. Goal of the whole set: move from "PDF → Excel for one specific drawing" to a
**layout-independent** extraction that recovers all the data of the Bodengutachten and feeds a
**Baugrundmodell** (Supabase → IFC 4.3 → That Open).

The notes are in English and keep the German technical terms of the Gutachten and of the app
(Bohrung, Schicht, GOK, Lageplan, Längsschnitt…): see the [glossary](glossary.md).

> [!NOTE]
> Summary in one sentence: the current extraction depends on fixed positions and colours; a
> geometric/statistical approach (tested on synthetic PDFs), swissgeol's mature algorithms for the
> textual stratigraphy and a test bench with the silent error as KPI solve it. See
> [11 Decisions](11_decisions.md).

## Overview

- [Architecture and Baugrundmodell](ARCHITECTURE_BAUGRUNDMODELL.md): evaluation, benchmark of tools, Supabase + workers + That Open architecture, IFC 4.3; read it first for the full picture.
- [11 Decisions and conclusions](11_decisions.md): all conclusions in one table, with evidence and status; read it if you only have 5 minutes.

## Extraction: problem and solution

- [01 Diagnosis: fixed layout assumptions](01_diagnosis_fixed_layout.md): inventory with code lines and measured failures; read it to understand why it fails with another office.
- [02 Layout-independent Bohrprofil](02_bohrprofil_generalization.md): columns from geometry, scale by regression, description, merging; the core of the solution.
- [03 Längsschnitt without constants](03_laengsschnitt_generalization.md): axes, tunnel, vector geology; design for the second PDF.

## Data that is lost today

- [04 Schraffur DIN 4023](04_schraffur_din4023.md): the graphic column as a second signal, classified with the legend.
- [05 Sondierungen DPH/CPT](05_sondierungen.md): digitising curves with calibrated axes.
- [06 Grundwasser](06_grundwasser.md): symbol, keywords, colour and water lines.
- [07 Coordinates and georeferencing](07_coordinates.md): tables, Lageplan, alignment; German CRSs; it unlocks 3D.

## Reuse, measurement and plan

- [08 swissgeol: what to reuse](08_swissgeol_reuse.md): module map, test on our PDFs, strategies and license.
- [09 Validation and benchmark](09_validation_benchmark.md): v1 / v2 / swissgeol results, ground truth format, corpus and metrics.
- [10 Implementation plan](10_implementation_plan.md): steps 0–8 with files, criteria and effort.
- [12 Real corpus with public Gutachten](12_public_corpus.md): where to get 5–10 real PDFs, how to evaluate them without ground truth, legal use.
- [13 Collaboration with swisstopo](13_swisstopo_collaboration.md): what they give us and what we give them, first steps, drafts of issues and email.
- [14 Licensing: internal today, third parties tomorrow](14_licensing.md): AGPL, options, pypdfium2 test, primitives layer.
- [15 Results with real PDFs](15_results_real_pdfs.md): v1 / v3 / swissgeol with 9 public Gutachten, blind tests (v3 0/13 and 11/29), eighteen lessons, Schichtenverzeichnis as a second source, OCR as the next step.
- [16 Lessons learned](16_lessons_learned.md): **project memory**, all the explicit rules (process, input, geometry, labels, text, water, second sources, swissgeol, IFC/Supabase, environment).
- [17 Extraction algorithm v4](17_extraction_algorithm.md): specification by stages E0–E9, parameters and their origin, confidence and canonical output.
- [18 Layer modeler and That Open viewer](18_layer_modeler.md): automatic Bodenschichten (Einheiten by correlation, surfaces, closed solids), IFC 4.3 and web viewer; results against synthetic ground truth and with Berlin.
- [19 App v2: from the PDF to the Baugrundmodell](19_app_v2.md): Streamlit with PDF upload, review, automatic model and integrated That Open viewer; start on Windows, marked assumptions.
- [20 Viewer with TwinBimM controls, Lage on the plan and Prüfstand](20_lage_pruefung_viewer.md): TwinBimM controls, camera for models > 5 km, Bohrungen placed on the PDF of the Lageplan/Längsschnitt, own distances in the row, tables before the model, automatic nachführen and einchecken of the review state.
- [21 Step app, norms and new calibration](21_app_schritte_normen.md): the full-screen app (Gutachten → Bohrungen → Lage → Einheiten → Modell, FastAPI + integrated viewer), warnings for unclassified Schichten, mini database DIN 4023 / EN ISO 14688-1 / DIN 18196 with colours, calibration by distance + reference point + lock, column diameter, description and norm on every Schicht of the IFC.
- [22 Online: deployment from GitHub](22_deployment.md): free on your own PC with a Cloudflare tunnel (`start_online.bat`), the app as a container (`Dockerfile`, Render blueprint with disk and password), the free hosts compared, why not Vercel (4.5 MB per request, no disk or background work), environment variables, measured memory, security, AGPL license and CI.
- [German–English glossary](glossary.md): geotechnical and swissgeol terms.

## Supporting code

- [Extraction v2 spike](../spikes/extraktion_v2/README.md): synthetic PDF generator, prototype v2, comparison v1/v2/swissgeol.
- [IFC + That Open spike](../spikes/ifc_thatopen/README.md): geotechnical IFC 4.3 with IfcOpenShell and its import into That Open.
- [Public corpus](../spikes/korpus/README.md): manifest, ground truth, blind test, regression, ablation and perturbations.
- [Supabase spike](../spikes/supabase/README.md): migration tested on PostGIS and loader of the canonical JSON.
- [`baugrundmodell` modeler](../services/modeler/README.md): canonical JSON → Einheiten → solids → IFC 4.3 (`IfcGeomodel`), with tests.
- [Web viewer](../apps/web/README.md): That Open Engine; Einheiten, properties, sections, vertical exaggeration.
- [Examples of the app](../data/beispiele/README.md): Berlin, Talheim, demo and synthetic PDF.

## How to read

```
Architecture ─► 11 Decisions
      │
      ▼
01 Diagnosis ─► 02 Bohrprofil ─► 04 Schraffur
      │               │   └──────► 05 Sondierungen · 06 Grundwasser · 07 Coordinates
      │               ▼
      └──────────► 03 Längsschnitt
08 swissgeol ─► 13 swisstopo collaboration
      │              14 Licensing
      ▼
09 Validation ◄─ 12 Public corpus ─► 15 Real results ─► 16 Lessons · 17 Algorithm
      ▼                                                         │
10 Plan                                                         ▼
                                                 18 Layer modeler + That Open viewer
                                                                ▼
                                                        19 App v2 (Streamlit)
                                                                ▼
                                            20 Lage and Prüfstand ─► 21 Step app
                                                                ▼
                                                  22 Online (own PC, container)
```

Up: [Repository README](../README.md)
