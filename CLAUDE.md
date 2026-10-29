# GroundTwin (Geo_Agent) — project memory

## Goal
From a Bodengutachten in PDF build the **Baugrundmodell**: validated, traceable Bohrungen →
Supabase → IFC 4.3 geometry in That Open Engine. Architecture: `docs/ARCHITECTURE_BAUGRUNDMODELL.md`.
The old app (`app.py`, `geo_agent/`, Streamlit) is v1: fixed positions, 0/58 Bohrungen on other offices' PDFs.
Repository `github.com/martinpazmino/GroundTwin` (formerly CAD_Extract and GeoIM; GitHub redirects the old names),
license **AGPL-3.0-or-later** (D79).

## Read before touching the extraction
- `docs/16_lessons_learned.md`: explicit rules (process P1–P12, input E, geometry G, labels L/T, text B, water W,
  second sources S, swissgeol R, model M, environment X). Respect them.
- `docs/17_extraction_algorithm.md`: specification of the algorithm (stages, parameters, confidence).
- `docs/15_results_real_pdfs.md`: blind and training results.
- `docs/11_decisions.md`: decisions D1–D83.
- `docs/18_layer_modeler.md`: layer model (N3) and That Open viewer.
- `docs/19_app_v2.md`: Streamlit app v2 (history; superseded by 21).
- `docs/20_lage_pruefung_viewer.md`: viewer with TwinBimM controls, models > 5 km, Lage on the plan, Prüfstand.
- `docs/21_app_schritte_normen.md`: step app (FastAPI + viewer), norms for the description, new calibration.
- `docs/22_deployment.md`: free online from your own PC (Cloudflare tunnel), container (Render), free hosts compared,
  why not Vercel, variables, memory, CI.

## Working rules
- **Blind test**: with a new PDF, freeze the predictions (`spikes/korpus/blind_test.py freeze`)
  and **push them to the repo before opening the PDF**; then transcribe the ground truth in `spikes/korpus/groundtruth/`.
- Always keep blind figures apart from training figures.
- Every change to the extraction passes the regression on real PDFs, stress cases and synthetic ones:
  `python spikes/korpus/regression.py --module spikes/extraktion_v2/prototyp_v4.py --real <pdfs> --stress <ordner>
  --synth <ordner> --baseline spikes/korpus/baseline_v4.json` (stress cases: `stress_cases.py`; OCR with
  `GEO_OCR_CACHE=<dir>`). In addition: `ablation.py` (which rule protects which case) and `perturb.py`
  (rotate/scale/raster).
- General rules (features of the drawing), never exceptions per PDF or office.
- A doubtful value is **marked** (issue / low confidence), never hidden. A false Bohrung is worse than a missing one.
- Third-party PDFs are **not** pushed to the repo: only URL, `sha256` and factual data.
- **Documentation in English**, keeping the German technical terms of the Gutachten and the app (Bohrung, Schicht,
  GOK, Lageplan, Längsschnitt, Einheit… see `docs/glossary.md`); linked notes (Up/Related, frontmatter); doc file
  names in English (D82). **Code, comments and UI texts in German.**

## App, model and viewer
- Step app (docs/21): `python -m server` (Windows: `start.bat`, port 8500) = FastAPI (`server/`) + page
  `apps/web/dist` (lit + viewer). Streamlit (`app.py`, `start_excel.bat`) only for Excel v1.
- Project rules in `ui/projekt.py` (`aendern(op)`): warnings = **unklassifiziert** Schichten (not confidence), all
  reviewed, remove/restore, Ø of the columns, calibration (scale by distance or 1:n + reference point + rotation /
  vertical scale + lock), dragging only with the lock (plan x/y; section: height only without a GOK from the PDF),
  points on the locked plan (place, assign to a Bohrung, delete).
  Extraction/model in `ui/pipeline.py`; the extraction is used from `spikes/extraktion_v2/prototyp_v4.py` without
  touching it.
- Norms (DIN 4023 / EN ISO 14688-1 / DIN 18196): `services/modeler/baugrundmodell/normen.json` + `normen.py`, with
  evidence per value; read them, never apply them silently (proposal with a click). IFC: `CPset_Bodenansprache` per
  Schicht.
- `services/modeler` (package `baugrundmodell`): `python -m baugrundmodell model.ifc a.json [...] --bericht report.json`;
  tests `cd services/modeler && python -m pytest tests`. Every change: exact contacts, closed solids, IFC without
  errors, **unit METRE** (M17).
- `apps/web` (step app `src/app`, viewer `src/viewer`: TwinBimM controls, Lage editor): after changing anything
  `npm run build` and **commit `apps/web/dist`** (the server uses it without Node); web-ifc 0.0.77 (X9). Test:
  `python scripts/testplan.py <plans>` and in `apps/web` `node scripts/check.mjs <model.ifc> <plans> <screenshots>` (19).
- End to end: `python -m server --port <p> --kein-browser --arbeit <empty>` and `node scripts/check_app.mjs
  http://localhost:<p> <plans> <screenshots>` (28 checks; with a password: `GEO_AGENT_PASSWORT=…`). `pkill`/`pgrep -f`
  in a separate command (X3, X19).
- Online (docs/22, D80): `Dockerfile` (python:3.13-slim, OCR off with `--build-arg OCR=0`, data in `/data`, user
  1000) and the `render.yaml` blueprint. Variables: `PORT`, `GEO_AGENT_HOST`, `GEO_AGENT_PASSWORT` (HTTP Basic except
  `/gesund`), `GEO_AGENT_BENUTZER`, `GEO_AGENT_MAX_MB`, `GEO_AGENT_ARBEIT`, `GEO_AGENT_QUELLCODE`. The *Quellcode* link
  (AGPL § 13) stays. Dependencies: `requirements-server.txt` + exact versions in `constraints.txt` (D81; renewed with
  `pip freeze`); CI `.github/workflows/pruefungen.yml`. Third parties: `THIRD_PARTY_LICENSES.md`; rules:
  `CONTRIBUTING.md`.
- Free online (D83): `start_online.bat` / `scripts/online.py` start the server **always with a password** and a
  Cloudflare Quick Tunnel (`cloudflared`, `CLOUDFLARED` for the path); it refuses a server already running on the
  port. Test `tests/test_online.py` with a simulated cloudflared.

## Environment (cloud sessions)
- Municipal websites blocked by the network policy; pypi and GitHub reachable. The user uploads the PDFs.
- Heavy dependencies in venvs in the scratchpad: `venv` (pymupdf, opencv, rapidocr), `sgvenv` (swissgeol).
- Docker (X25, X26): start `dockerd` in the background with the longest time limit; apt blocked → `--build-arg OCR=0`,
  `--network host`, the session's proxy and CA as a secret. vercel.com, render.com, gnu.org and flaviocopes.com
  blocked (Vercel docs: Vercel MCP or search).
- The GitHub tools of the session only accept the repository name in the session scope (X29).
- Working branch given by the session; do not open a PR unless asked.
