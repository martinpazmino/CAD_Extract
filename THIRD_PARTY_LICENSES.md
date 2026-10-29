# Licencias de terceros

GeoIM (Geo_Agent) se publica bajo la **GNU Affero General Public License v3.0 o posterior**
([`LICENSE`](LICENSE)). Usa los componentes siguientes, cada uno con su propia licencia. En el repositorio
sólo va código de terceros dentro de la interfaz compilada (`apps/web/dist`: bibliotecas web y el WASM de
web-ifc); el resto se instala con `pip` / `npm`.

| Componente | Para qué | Licencia |
|---|---|---|
| [PyMuPDF](https://github.com/pymupdf/PyMuPDF) | leer, analizar y renderizar los PDF | **AGPL-3.0** o comercial (Artifex) |
| [IfcOpenShell](https://ifcopenshell.org) | escribir el IFC 4.3 | LGPL-3.0-or-later |
| NumPy, SciPy, pandas, Shapely, networkx | cálculo y geometría | BSD-3-Clause (NumPy además 0BSD/MIT/Zlib/CC0 en partes) |
| FastAPI, Pydantic, openpyxl, lark, onnxruntime | servidor, Excel v1, dependencias | MIT |
| Starlette, Uvicorn | servidor web | BSD-3-Clause |
| python-multipart, Streamlit | subida de archivos, app Excel v1 | Apache-2.0 |
| Pillow | imágenes | MIT-CMU (HPND) |
| RapidOCR, OpenCV (opcional, `requirements-ocr.txt`) | OCR de escaneos | Apache-2.0 |
| [That Open Engine](https://github.com/ThatOpen) (`@thatopen/components`, `-front`, `fragments`, `ui`, `ui-obc`) | visor 3D e interfaz BIM | MIT |
| three.js, camera-controls, iconify-icon | 3D, cámara, iconos | MIT |
| [web-ifc](https://github.com/ThatOpen/engine_web-ifc) (`dist/vendor/*.wasm`) | leer IFC en el navegador | MPL-2.0 |
| lit | interfaz de la app por pasos | BSD-3-Clause |
| Material Design Icons (`@iconify-json/mdi`) | iconos | Apache-2.0 |
| EOS Icons (`@iconify-json/eos-icons`) | iconos | MIT |

## Por qué AGPL

PyMuPDF sólo se puede usar gratis bajo la AGPL-3.0. Quien ofrezca GeoIM a otros por la red debe
ofrecerles el código fuente de la versión que ejecuta (AGPL § 13). La app lo hace con un enlace
*Quellcode* en la página de inicio y en el menú; apunta a este repositorio (`GEO_AGENT_QUELLCODE` lo
cambia para un fork). Detalles y alternativas (licencia comercial de PyMuPDF, cambiar a pypdfium2):
[docs/14](docs/14_licencias_terceros.md).

## Datos

- Los ejemplos de `data/beispiele` son datos factuales (coordenadas, capas) o sintéticos; los PDF de
  terceros **no** están en el repositorio (sólo URL y `sha256`).
- La base de datos de normas (`services/modeler/baugrundmodell/normen.json`) **no** reproduce textos de
  DIN 4023, DIN EN ISO 14688-1 ni DIN 18196: recoge abreviaturas y colores con la evidencia de cada dato.
