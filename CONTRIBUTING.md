# Contributing to GroundTwin

Thank you for helping. GroundTwin turns Bodengutachten in PDF into an IFC 4.3 Baugrundmodell. A false
Bohrung is worse than a missing one, which is why the project has strict rules about how things are
measured and tested. The full rules are in [docs/16 Lessons learned](docs/16_lessons_learned.md).

## Set up the environment

```bash
python -m venv .venv && . .venv/bin/activate        # Windows: start.bat does it for you
pip install -r requirements.txt -c constraints.txt  # Python 3.13; with another version, without -c
pip install -r requirements-ocr.txt -c constraints.txt   # optional: OCR
cd apps/web && npm ci                                # only if you change the page or the viewer
```

## Before every pull request

1. **Tests:** `pytest tests` and `cd services/modeler && pytest tests`.
2. **Page or viewer changed** (`apps/web/src`):
   - `cd apps/web && npm run build` and **commit `apps/web/dist`**: the server uses it without Node.
   - Check with `scripts/check_app.mjs` (see the [README](README.md#tests)).
3. **Extraction changed** (`spikes/extraktion_v2/prototyp_v4.py`): regression on real PDFs, stress
   cases and synthetic ones. The figures must not get worse:
   ```bash
   python spikes/korpus/regression.py --module spikes/extraktion_v2/prototyp_v4.py \
     --real <pdfs> --stress <folder> --synth <folder> --baseline spikes/korpus/baseline_v4.json
   ```
   If a rule is touched, `ablation.py` shows which case it protects.
4. **Modeler changed:**
   - exact contacts;
   - closed solids;
   - IFC without errors;
   - unit METRE.
5. **Dependencies changed:** update `constraints.txt` as explained in
   [docs/22 §9](docs/22_deployment.md#9-dependencies-and-versions).

GitHub runs points 1, 2 (build) and the container image on every push
([Prüfungen](.github/workflows/pruefungen.yml)).

## Project rules

- **Blind test with every new PDF:**
  1. Freeze the predictions with `spikes/korpus/blind_test.py freeze`.
  2. Push them to the repository **before** opening the PDF.
  3. Afterwards, transcribe the ground truth in `spikes/korpus/groundtruth/`.

  Blind figures and training figures are always kept apart.
- **General rules** based on features of the drawing, never exceptions for one PDF or one office.
- **What is doubtful is marked** (issue, low confidence, unclassified Schicht), never hidden.
- **No third-party PDFs in the repository:** only URL, `sha256` and factual data
  (`spikes/korpus/manifest.tsv`).
- **Standards:** do not copy texts of DIN standards. The norms database stores abbreviations and
  colours with the evidence for every value. The app proposes and never applies a norm silently.
- **Languages:**
  - documentation in **English**, keeping the German technical terms (Bohrung, Schicht, GOK,
    Lageplan… see the [glossary](docs/glossary.md)), as linked notes (frontmatter, `Up:` and
    `Related:`);
  - code, comments and interface texts in **German**.
- **Decisions and lessons:**
  - a new decision goes to [docs/11](docs/11_decisions.md) (D…);
  - a lesson, with the test that watches it, to [docs/16](docs/16_lessons_learned.md).

## License of contributions

GroundTwin is published under the [AGPL-3.0-or-later](LICENSE). By sending a contribution, you agree
that it is published under the same license. Third-party code or data only with a compatible license,
noted in [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). In particular, do not copy code from
swissgeol: only reimplement its ideas ([docs/14](docs/14_licensing.md)).
