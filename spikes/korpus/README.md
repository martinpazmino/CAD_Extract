---
title: "Corpus: public Gutachten (manifest and evaluation)"
date: 2026-10-25
tags: [spike, corpus, validation]
aliases: [Corpus spike]
---

# Corpus: public Gutachten (manifest and evaluation)

| File | What it does |
|---|---|
| [`manifest.tsv`](manifest.tsv) | 24 public candidates (B-Pläne, UVP-Verbund, NLWKN, Transparenzportal Hamburg) from 9 Länder: name, Land, procedure, URL, expected content. Reviewed (marked `GEPRUEFT`): the 9 with ground truth in `groundtruth/`; those marked `Runde 4 (blind)` are the next blind round (their download was blocked in round 3); the rest were found by searching and are unopened |
| [`screen_corpus.py`](screen_corpus.py) | `--download` downloads the manifest; `--screen` filters pages (vector/scan/Bohrprofil), runs v1 and v3 and writes `report.md` + thumbnails (without ground truth) |
| [`eval_real.py`](eval_real.py) | Compares v1, v3 and (optionally) swissgeol with the ground truth in `groundtruth/` |
| [`blind_test.py`](blind_test.py) | Blind test: `freeze` freezes the predictions before looking at new PDFs, `score` scores them afterwards |
| [`frozen/runde3/`](frozen/runde3/marl_251.json) | Frozen predictions of round 3 (v3, v1 and swissgeol depths, with the `sha256` of the PDF), pushed before the ground truth |
| [`frozen/runde4_swiss/`](frozen/runde4_swiss/A7367.json), [`frozen/runde4_swiss_v4/`](frozen/runde4_swiss_v4/A7367.json) | Blind round 4 (swissgeol examples, Switzerland): v3 and v4 frozen before opening them |
| [`regression.py`](regression.py) | Regression: real PDFs + stress cases + synthetic ones against a baseline (`baseline_v3.json`, `baseline_v4.json`); exits with an error if anything gets worse |
| [`ablation.py`](ablation.py) | Switches off each rule in `RULES` and lists the cases that get worse |
| [`perturb.py`](perturb.py) | Variants of the real PDFs (rotated 90°, reduced to 70 %, raster without text) with the same ground truth |
| [`groundtruth/`](groundtruth/wachenroth.json) | Ground truth of 9 German Gutachten (Wachenroth, Talheim, Halle, Hausham, Rednitzhembach, Triefenstein, Marl, Wesel, Berlin) and 4 Swiss examples from swissgeol (factual data, URL and `sha256` of the PDF) |

```bash
python screen_corpus.py --download ~/gutachten          # needs network access to the domains
python screen_corpus.py --screen ~/gutachten ~/gutachten_report
```

The PDFs are **not** committed (internal use, see
[12 Corpus](../../docs/12_public_corpus.md#4-legal-use-of-the-pdfs)). In Claude's environment the
download is blocked by the network policy (2026-10-25); the three PDFs evaluated were uploaded by
hand. Results: [15 Real results](../../docs/15_results_real_pdfs.md).

```bash
python eval_real.py <folder_with_wachenroth.pdf_talheim.pdf_halle.pdf> [<swissgeol_output_folder>]
```

The ablation table [`ablation_v4.md`](ablation_v4.md) is written by `ablation.py` and keeps its
generated (German) wording.

Up: [Documentation index](../../docs/README.md)

Related: [12 Public corpus](../../docs/12_public_corpus.md) · [15 Real results](../../docs/15_results_real_pdfs.md) · [09 Validation](../../docs/09_validation_benchmark.md)
