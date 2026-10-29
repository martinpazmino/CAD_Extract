# GroundTwin — from the Bodengutachten to the Baugrundmodell

[![Prüfungen](https://github.com/martinpazmino/GroundTwin/actions/workflows/pruefungen.yml/badge.svg)](https://github.com/martinpazmino/GroundTwin/actions/workflows/pruefungen.yml)
[![License: AGPL-3.0-or-later](https://img.shields.io/badge/license-AGPL--3.0--or--later-blue.svg)](LICENSE)

GroundTwin reads German geotechnical reports in PDF (Bodengutachten) and builds an **IFC 4.3
Baugrundmodell** from them: validated Bohrungen traceable back to the PDF page, Schichten
interpreted according to the standards, and closed solids in the **That Open** viewer. It used to be
called Geo_Agent / CAD_Extract and then GeoIM.

The German technical terms (Bohrung = borehole, Schicht = layer, GOK = ground level, Lageplan =
site plan, Längsschnitt = longitudinal section…) are kept as they appear in the Gutachten and in the
app: see the [glossary](docs/glossary.md).

* **Baugrundmodell (step app, full screen):**
  1. **Gutachten**: upload the PDF (vector, or scanned with OCR).
  2. **Bohrungen**: review and correct Bohrungen and Schichten. There are warnings for unclassified
     Schichten, and every description is read according to **DIN 4023 / EN ISO 14688-1 /
     DIN 18196**. Bohrungen can be removed.
  3. **Lage**: calibrate a Lageplan or a Längsschnitt PDF (measured distance → scale, reference point
     with a coordinate, lock) and place the Bohrungen on it by dragging or with points. A row with
     your own distances also works.
  4. **Einheiten**: decide how the Schichten are joined into model Einheiten.
  5. **Modell**: IFC 4.3 `IfcGeomodel` + `IfcBorehole` in the viewer with the TwinBimM controls, also
     for Trassen longer than 5 km. Includes *einchecken* of the review state and export.

  Each step updates the next one.
* **Excel nach Vorlage (v1):** Bohrprofil + Längsschnitt (Hamburg layout) → `.xlsx` with 4 sheets
  ([description](geo_agent/README.md)).

![Synthetic Lageplan calibrated in the viewer: Bohrungen dragged onto their symbols](docs/img/20_lageplan_kalibriert.jpg)

## Run it on your own computer

**Windows:** double click on [`start.bat`](start.bat).
- The first time it creates `.venv` and installs everything. It takes a few minutes; OCR is optional
  and does not block.
- Then it opens `http://localhost:8500` in the browser.
- Excel v1: [`start_excel.bat`](start_excel.bat) (`http://localhost:8501`).
- If the installation stopped halfway: delete `.venv` and run `start.bat` again.

**By hand (any system, Python 3.10 or later):**

```bash
pip install -r requirements.txt
pip install -r requirements-ocr.txt       # optional: scans and SHX text (OpenCV + onnxruntime)
python -m server                          # step app at http://localhost:8500 (--port, --arbeit, --kein-browser)
streamlit run app.py                      # Excel v1 only
```

With Python 3.13, adding `-c constraints.txt` to each `pip install` installs exactly the tested
versions, the same as the container and the CI.

**With Docker:**

```bash
docker build -t groundtwin .              # without OCR: --build-arg OCR=0
docker run -p 8500:8500 -v groundtwin-daten:/data groundtwin
```

No Node needed: the compiled page is in `apps/web/dist`.

To try it without your own PDF, the first page offers [examples](data/beispiele/README.md):
- Berlin, georeferenced.
- Talheim without coordinates.
- A synthetic demo.
- A 6 km Trasse.
- A synthetic PDF to test the extraction.

An extraction can also be uploaded as JSON. Projects are saved automatically and appear under
*Zuletzt bearbeitet*.

## Online

**Free: your own PC + Cloudflare Tunnel.** Install `cloudflared` once
(`winget install --id Cloudflare.cloudflared`) and double click on
[`start_online.bat`](start_online.bat) (after the first `start.bat`). The window shows a public
`https://….trycloudflare.com` address and a password to share. The Gutachten stay on your PC; the
address lives while the PC and the window are running, and changes on every start. On other systems:
`python scripts/online.py`. On a company PC, ask IT before opening a tunnel.

**Permanent service: a container.** The whole app (FastAPI server + page) goes into **one
container** built from this repository ([`Dockerfile`](Dockerfile)). The blueprint
[`render.yaml`](render.yaml) is ready for [Render](https://render.com):
1. On Render, *New → Blueprint*, choose this repository.
2. Enter a password in `GEO_AGENT_PASSWORT`.

From then on, every push to `main` redeploys. The data goes to a disk at `/data` and the server is in
Frankfurt (paid plan, about $8/month with the disk).

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/martinpazmino/GroundTwin)

**Vercel?** Only for static pages, not for this app:
- Its functions accept at most 4.5 MB per request, and a Gutachten weighs more.
- They have no disk to store the projects.
- They run no background work for the extraction.

[docs/22](docs/22_deployment.md) has the details, with sources: the free option step by step, the
free hosts compared (Render Free, Hugging Face, Koyeb, Oracle…), other platforms, memory, security
and how to update the versions.

> [!IMPORTANT]
> Without `GEO_AGENT_PASSWORT`, anyone with the URL can see and change the Gutachten. With it, the
> browser asks for a user (any, or `GEO_AGENT_BENUTZER`) and the password. `/gesund` answers without
> a password, for the platform's health check. `start_online.bat` always sets a password.

## What it does

1. **Extraction v4** ([docs/17](docs/17_extraction_algorithm.md)): page class, columns, scale,
   boundaries, Bodenart, Grundwasser, Schichtenverzeichnis and coordinates. Every Schicht carries its
   confidence and its provenance (page, bbox).
2. **Review** ([docs/21](docs/21_app_schritte_normen.md)): Bohrung by Bohrung, with the PDF page and
   the Schicht marked.
   - Warnings only for **unclassified** Schichten.
   - A proposal by norm with one click.
   - *Everything reviewed*; remove and restore Bohrungen.

   Everything corrected or assumed stays **marked** (manuell, Plan, Reihe, schematisch, relativ) and
   the project is saved automatically.
3. **Norms** ([docs/21 §3](docs/21_app_schritte_normen.md#3-mini-database-of-norms)): a mini database
   of Kurzzeichen, DIN 4023 colours and DIN 18196 groups, with the evidence for every value. The
   reading of each description goes into the IFC (`CPset_Bodenansprache`).
4. **Lage** ([docs/21 §4](docs/21_app_schritte_normen.md#4-lage-new-calibration)):
   - Calibration: scale by measured distance or 1:n, reference point, rotation / vertical scale and
     lock.
   - The Bohrungen are placed with points or dragged in x/y only. In the section the station moves;
     the height only if the PDF has no GOK.
   - The diameter of the columns is adjustable.
5. **Layer model** ([docs/18](docs/18_layer_modeler.md)): Einheiten by correlating the sequences,
   surfaces that honour every contact, closed solids and a valid IFC 4.3 in metres.
6. **That Open viewer** ([apps/web](apps/web/README.md)): compact toolbar, help on every setting and
   the Lage editor. With every change, the model is recomputed.

History:
- [docs/19](docs/19_app_v2.md): app v2 in Streamlit.
- [docs/20](docs/20_lage_pruefung_viewer.md): TwinBimM controls, camera > 5 km, Prüfstand.

## Structure

```
server/                     Baugrundmodell app: FastAPI + projects, background extraction (python -m server)
ui/                         project state (projekt.py), pipeline without UI, Excel v1 page
app.py                      Streamlit: Excel v1 only
start.bat  start_excel.bat  start on Windows; start_online.bat: free online via Cloudflare Tunnel
spikes/extraktion_v2/       extraction v4 (reference of the regression, docs/17)
services/modeler/           `baugrundmodell` modeler and norms database (python -m baugrundmodell …)
apps/web/                   step app and That Open viewer (Vite + TypeScript + lit); dist/ compiled in the repo
geo_agent/                  v1 package (Excel)
data/beispiele/             examples (factual and synthetic data)
tests/  scripts/            tests of the app and the API; end-to-end test (Playwright); synthetic plans; online.py
docs/                       linked notes (English, German technical terms): index in docs/README.md
spikes/                     corpus, regression, IFC, Supabase
Dockerfile  docker/         container (docs/22); render.yaml: Render blueprint
.github/workflows/          tests on every push (Prüfungen)
requirements*.txt           dependencies; constraints.txt pins the tested versions
```

## Tests

- `pytest tests` (project logic, API, online script) and `cd services/modeler && pytest tests`
  (modeler and norms).
- Viewer: `python scripts/testplan.py plans && cd apps/web && node scripts/check.mjs <model.ifc> ../../plans screenshots`.
- App: start `python -m server --port 8511 --kein-browser --arbeit <empty folder>` and then
  `node scripts/check_app.mjs http://localhost:8511 plans screenshots`.
- Extraction: regression on real PDFs, stress cases and synthetic ones ([CONTRIBUTING](CONTRIBUTING.md)).

GitHub runs these tests on every push ([`pruefungen.yml`](.github/workflows/pruefungen.yml)):
- Python.
- Build of the page.
- Container with password and OCR.

The end-to-end test is started by hand (*Run workflow*).

## Documentation and contributing

- [`docs/README.md`](docs/README.md): architecture, decisions, lessons and results.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): project rules (blind test, regression, no third-party PDFs in
  the repository, documentation in English and code in German).

## License

**[GNU Affero General Public License v3.0 or later](LICENSE)** (AGPL-3.0-or-later).

Whoever offers GroundTwin to others over a network must give them the source code of the version
they run. The app does this with the *Quellcode* link. The reason for the AGPL is PyMuPDF, which is
only free under that license ([docs/14](docs/14_licensing.md)). Third-party components and their
licenses: [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

The app extracts and proposes; the geotechnical interpretation and its signature belong to the
geotechnical engineer. It comes without any warranty (AGPL §§ 15–16).
