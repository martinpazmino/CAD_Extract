---
title: "Real corpus: public Gutachten to test the extraction"
date: 2026-10-25
tags: [corpus, validation, gutachten, data]
aliases: [Public corpus, Test Gutachten]
---

# Real corpus: public Gutachten to test the extraction

**Conclusion:** there is no need to wait for our own Gutachten. In Germany many complete
Baugrundgutachten, with DIN 4023 Bohrprofile, Rammsondierungen and a Lageplan, are published in the
public participation for **Bebauungspläne**, in **Planfeststellungen** (UVP-Verbund) and on
**transparency** portals (e.g. Hamburg). There are 16 candidates from 8 Länder in
[`spikes/korpus/manifest.tsv`](../spikes/korpus/manifest.tsv) and a script that downloads, filters
and evaluates them.

**Status (2026-10-25):** the automatic download is blocked by the network of Claude's environment
(403 on `www.dresden.de`, `daten.transparenz.hamburg.de`, `www.ditzingen.de`, …). The team uploaded
**5 PDFs** by hand: 3 for training (Wachenroth, Talheim, Halle) and 2 for the **blind test**
(Hausham, Rednitzhembach). The ground truth is transcribed in
[`spikes/korpus/groundtruth/`](../spikes/korpus/groundtruth/talheim.json) and the results are in
[15](15_results_real_pdfs.md). For the next blind round: GGU-STRATIG, WinBohr, another scanned one
and one with a coordinate table.

## 1. How to unblock it (pick one)

1. **Allow the domains** in the environment settings (Network access → Allowed domains): the hosts
   in the `url` column of the manifest. Then: `python screen_corpus.py --download <dir>`.
2. **Download by hand** (browser) the PDFs of interest, put them in a folder outside the repo and
   run `python screen_corpus.py --screen <dir> <output>`.
3. Upload them to the Claude session so that it evaluates them (they are not committed).

## 2. What to look for (5–10 well chosen > 50 at random)

| Criterion | Why |
|---|---|
| Different **software** (`Producer`/`Creator`: GGU-STRATIG, DC-BOHR, WinBohr, AutoCAD…) | It is what changes the layout most |
| Different **offices** and **Länder** | Local conventions (IDs, `NHN`/`NN`, CRS) |
| With **Rammsondierung DPH** and, if available, **CPT** | [05](05_sondierungen.md) |
| With a **Lageplan** and/or a coordinate table | [07](07_coordinates.md) |
| At least 1–2 with a **Längsschnitt / Baugrundschnitt** (ideally a tunnel, e.g. `offenstetten`) | [03](03_laengsschnitt_generalization.md) |
| At least 1 **scanned** | Measure the OCR route and check that the filter detects it |

The script already reports `producer/creator`, vector vs. scanned pages, candidate Bohrprofil pages
and the labelled scale (`M 1:…`).

## 3. Evaluation without ground truth (first pass)

Without ground truth only **self-consistency** can be measured (`screen_corpus.py`):

| Indicator | Sign of a problem |
|---|---|
| Bohrungen detected by v1 / v2 vs. Bohrungen labelled on the cover/Lageplan | Bohrungen missing or extra |
| Scale from the regression (v2) vs. `M 1:…` in the text | column or labels found wrongly |
| % boundaries confirmed by a label | geometry and text disagree |
| % text = Schraffur | the Schraffur classifier or the text parser fails |
| NHN arithmetic (v1) | depths misread |
| Issues per Schicht | where to look first |

Plus a thumbnail of each Bohrprofil page for visual review. With that, the 5–10 documents are
chosen and the **semi-automatic ground truth** is created (v2 → human correction →
`ground_truth.json`, [09 §2](09_validation_benchmark.md#2-ground-truth-format)).

## 4. Legal use of the PDFs

> [!IMPORTANT]
> This is not legal advice. The Gutachten are protected works of the offices that sign them, even
> when they are published.

- **Internal use for testing.** § 44b UrhG (*Text und Data Mining* on lawfully accessible works)
  seems to apply here. If the rights holder has opted out of TDM in a machine-readable way, the
  document is not used. Copies are deleted when they are no longer needed.
- **No redistribution:** the PDFs do not go into the repo (`data/*.pdf` is already in
  `.gitignore`). The repo only keeps the manifest (URL + note) and, once they exist, the `sha256`
  and the annotated ground truth.
- **Personal data:** the Gutachten name engineers, owners or addresses. Do not publish excerpts
  outside the team.
- For use with **third parties** the test corpus does not change, but the software license does
  ([14](14_licensing.md)).

## 5. Other sources to explore

- Borehole databases of the geological surveys of the Länder (e.g. NIBIS/LBEG, geoportals of
  Hamburg or Berlin). They are usually **scans** of Schichtenverzeichnisse: useful for the OCR
  route, not for the vector one.
- Shareable synthetic examples: the generator
  [`synth_bohrprofil.py`](../spikes/extraktion_v2/synth_bohrprofil.py) has no restrictions and
  can reproduce errors for third parties, e.g. swisstopo ([13](13_swisstopo_collaboration.md)).

Up: [Index](README.md)

Related: [09 Validation](09_validation_benchmark.md) · [10 Plan](10_implementation_plan.md) · [14 Licensing](14_licensing.md) · [13 swisstopo](13_swisstopo_collaboration.md)
