---
title: "Licensing: internal use today, third parties tomorrow"
date: 2026-10-25
tags: [licensing, agpl, pymupdf, saas, decisions]
aliases: [Licensing, AGPL, Use by third parties]
---

# Licensing: internal use today, third parties tomorrow

> [!NOTE]
> **Update 2026-10-29:** option A was chosen. The repository is published under
> **AGPL-3.0-or-later** ([`LICENSE`](../LICENSE), [third parties](../THIRD_PARTY_LICENSES.md), D79)
> and the app links its source code (*Quellcode*) to comply with § 13 when it is online
> ([22](22_deployment.md)). B and C remain open should closed code ever be needed.

**Conclusion:** for **internal** use, the AGPL license of PyMuPDF (and of swissgeol) poses no
practical problems. To offer Geo_Agent **to third parties**, one has to choose between publishing
the code under the AGPL, buying the commercial PyMuPDF license or changing the PDF library. The
decision can wait if two cheap rules are followed from now on:
1. **all of PyMuPDF behind our own primitives layer**;
2. **do not copy code from swissgeol**, only reimplement its ideas.

With that, changing the library stays within one module, and it is feasible: see the test in §3.

> [!IMPORTANT]
> This is not legal advice. Before offering the service to third parties, review the AGPL-3.0 and
> Artifex's conditions with a lawyer.

## 1. What the AGPL requires and when

| Scenario | Practical obligation (AGPL-3.0) |
|---|---|
| Internal use (employees, `localhost`, company network) | None towards the outside. The only "users" are internal. |
| Handing the software to a client (installation) | Also hand over the source code of the whole application under the AGPL |
| **SaaS for third parties** (web) | § 13: offer remote users the source code of the version they run |

PyMuPDF is distributed under the AGPL or under a **commercial license from Artifex** (price on
request). swissgeol is **AGPL-3.0-only** without an alternative license ([08](08_swissgeol_reuse.md)).

## 2. Options for third parties

| Option | Cost | Consequence |
|---|---|---|
| A. Publish Geo_Agent as AGPL | €0 in licenses | The code is public; the business is in the service, the support and the data (which are not code) |
| B. Commercial PyMuPDF license | According to Artifex | Closed code possible, **except** whatever was copied from swissgeol (it would remain AGPL) |
| C. Switch to a permissive library (pypdfium2) | Adaptation work (primitives layer) | No PyMuPDF license restriction |

Recommendation: decide when there is a concrete business case. Until then, keep B and C open with
the two rules of the conclusion.

## 3. Test: can PyMuPDF be replaced?

Same synthetic PDF (layout B), the vector primitives that extraction v2 needs:

| Library | License | Paths | Segments / curves | Fill, stroke, dashes | OCG layers | Time |
|---|---|---|---|---|---|---|
| PyMuPDF 2.0 | AGPL / commercial | 30 | 1,866 items (1,704 curves) | yes | yes, with name (`layer`) | 0.35 s |
| **pypdfium2 5.14** | **BSD-3 / Apache-2.0** | **30** (same objects) | 5,839 segments (5,112 Bézier) | yes (`GetFillColor`, `GetDashCount`) | `OC` mark present; layer name **[to be verified]** | 0.08 s |
| pdfplumber 0.11 / pdfminer.six | MIT | (flattened) | 77 lines, 444 curves | dashes yes; rectangles not recognised in this PDF | no | 0.16 s |

Reading: **pypdfium2** keeps the same object model (one path = one object with segments and style)
and is the natural candidate for option C. pdfplumber changes the model and, being pure Python, is
probably slow with the > 150,000 paths of the Längsschnitt **[to be verified]**. Missing in
pypdfium2: grouping characters into words (PyMuPDF does it for us), `find_tables` and resolving the
names of OCG layers.

## 4. Primitives layer (do it now)

```
geo_agent/primitives/
  model.py            Word(text, bbox, font, size, color) · Path(segments, fill, stroke, dashes, layer, bbox)
  pymupdf_backend.py  the only pymupdf import in the whole extractor
  pdfium_backend.py   (when needed) same interface with pypdfium2
```

The extractors (`bohrprofil/`, `laengsschnitt/`, `hatch.py`…) only see `Word` and `Path`. It also
serves to cache the primitives in Storage
([architecture §6.2](ARCHITECTURE_BAUGRUNDMODELL.md#62-primitives-once-per-document-cached)) and for
tests without a PDF.

## 5. Other dependencies

| Component | License | Problem for a closed SaaS? |
|---|---|---|
| IfcOpenShell | LGPL-3.0 | No (obligations only when distributing a modified library) |
| That Open (`@thatopen/*`) | MIT | No |
| web-ifc | MPL-2.0 | No (copyleft only per modified file) |
| three.js, numpy, shapely, openpyxl | MIT / BSD | No |
| Streamlit | Apache-2.0 | No |
| Supabase (self-hosted) | Apache-2.0 | No |
| GemPy (if used) | **[to be verified]** | Review before integrating it |

## 6. Other requirements once third parties come

- **GDPR:** data processing agreement (AVV/DPA) with clients and with the providers (Supabase,
  hosting, LLM); EU region; deletion of documents.
- **Confidentiality:** separation per client with RLS, already planned in the
  [schema](ARCHITECTURE_BAUGRUNDMODELL.md#52-supabase-schema-draft-migration); encryption and
  private buckets.
- **LLM:** a contract without training on the data and with minimal retention, or switchable off per
  client.
- **Liability:** the app extracts and proposes; the interpretation and the signature belong to the
  geotechnical engineer (DGGT Empf. Nr. 4). State it in the terms of use and in the UI ("not
  approved" status).
- **DIN standards:** do not reproduce texts of standards; the patterns are taken from the legend of
  each document.

Up: [Index](README.md)

Related: [08 swissgeol](08_swissgeol_reuse.md) · [11 Decisions](11_decisions.md) · [12 Corpus](12_public_corpus.md) · [Architecture](ARCHITECTURE_BAUGRUNDMODELL.md) · [22 Online](22_deployment.md)
