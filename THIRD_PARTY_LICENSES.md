# Third-party licenses

GroundTwin (Geo_Agent) is published under the **GNU Affero General Public License v3.0 or later**
([`LICENSE`](LICENSE)). It uses the following components, each under its own license. The only
third-party code in the repository is inside the compiled interface (`apps/web/dist`: web libraries
and the web-ifc WASM); everything else is installed with `pip` / `npm`.

| Component | What for | License |
|---|---|---|
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | reading, analysing and rendering the PDFs | **AGPL-3.0** or commercial (Artifex) |
| [IfcOpenShell](https://ifcopenshell.org) | writing the IFC 4.3 | LGPL-3.0-or-later |
| NumPy, SciPy, pandas, Shapely, networkx | computation and geometry | BSD-3-Clause (parts of NumPy also 0BSD/MIT/Zlib/CC0) |
| FastAPI, Pydantic, openpyxl, lark, onnxruntime | server, Excel v1, dependencies | MIT |
| Starlette, Uvicorn | web server | BSD-3-Clause |
| python-multipart, Streamlit | file upload, Excel v1 app | Apache-2.0 |
| Pillow | images | MIT-CMU (HPND) |
| RapidOCR, OpenCV (optional, `requirements-ocr.txt`) | OCR of scans | Apache-2.0 |
| [That Open Engine](https://github.com/ThatOpen) (`@thatopen/components`, `-front`, `fragments`, `ui`, `ui-obc`) | 3D viewer and BIM interface | MIT |
| three.js, camera-controls, iconify-icon | 3D, camera, icons | MIT |
| [web-ifc](https://github.com/ThatOpen/engine_web-ifc) (`dist/vendor/*.wasm`) | reading IFC in the browser | MPL-2.0 |
| lit | interface of the step app | BSD-3-Clause |
| Material Design Icons (`@iconify-json/mdi`) | icons | Apache-2.0 |
| EOS Icons (`@iconify-json/eos-icons`) | icons | MIT |
| [cloudflared](https://github.com/cloudflare/cloudflared) (optional, installed separately for `start_online.bat`) | free tunnel to share the app from your own PC | Apache-2.0 |

## Why the AGPL

PyMuPDF can only be used for free under the AGPL-3.0. Whoever offers GroundTwin to others over a
network must offer them the source code of the version they run (AGPL § 13). The app does this with a
*Quellcode* link on the start page and in the menu; it points to this repository
(`GEO_AGENT_QUELLCODE` changes it for a fork). Details and alternatives (commercial PyMuPDF license,
switching to pypdfium2): [docs/14](docs/14_licensing.md).

## Data

- The examples in `data/beispiele` are factual (coordinates, Schichten) or synthetic data; third-party
  PDFs are **not** in the repository (only URL and `sha256`).
- The norms database (`services/modeler/baugrundmodell/normen.json`) does **not** reproduce texts of
  DIN 4023, DIN EN ISO 14688-1 or DIN 18196: it collects abbreviations and colours with the evidence
  for every value.
