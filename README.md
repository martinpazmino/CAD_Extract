# GeoIM — del Bodengutachten al Baugrundmodell

[![Prüfungen](https://github.com/martinpazmino/GeoIM/actions/workflows/pruefungen.yml/badge.svg)](https://github.com/martinpazmino/GeoIM/actions/workflows/pruefungen.yml)
[![Licencia: AGPL-3.0-or-later](https://img.shields.io/badge/licencia-AGPL--3.0--or--later-blue.svg)](LICENSE)

Lee informes geotécnicos alemanes en PDF (Bodengutachten) y construye con ellos un **Baugrundmodell
IFC 4.3**: sondeos validados y trazables hasta la página del PDF, capas interpretadas según norma y
sólidos cerrados en el visor **That Open**. Antes se llamaba Geo_Agent / CAD_Extract.

* **Baugrundmodell (app por pasos, pantalla completa):**
  1. **Gutachten**: subir el PDF (vectorial o escaneado con OCR).
  2. **Bohrungen**: revisar y corregir sondeos y capas. Hay avisos para las capas sin clasificar y
     cada descripción se lee según **DIN 4023 / EN ISO 14688-1 / DIN 18196**. Los sondeos se pueden
     quitar.
  3. **Lage**: calibrar un Lageplan o un Längsschnitt en PDF (distancia medida → escala, punto de
     referencia con coordenada, candado) y poner los sondeos encima arrastrándolos o con puntos.
     También vale una fila con distancias propias.
  4. **Einheiten**: decidir cómo se unen las capas.
  5. **Modell**: IFC 4.3 `IfcGeomodel` + `IfcBorehole` en el visor con los controles del TwinBimM,
     también para trasses de más de 5 km. Incluye *einchecken* del estado de revisión y export.

  Cada paso actualiza el siguiente.
* **Excel nach Vorlage (v1):** Bohrprofil + Längsschnitt (layout Hamburgo) → `.xlsx` de 4 hojas
  ([descripción](geo_agent/README.md)).

![Lageplan sintético calibrado en el visor: sondeos arrastrados a su símbolo](docs/img/20_lageplan_kalibriert.jpg)

## Arrancar en el propio ordenador

**Windows:** doble clic en [`start.bat`](start.bat).
- La primera vez crea `.venv` e instala todo. Tarda unos minutos; el OCR es opcional y no bloquea.
- Después abre `http://localhost:8500` en el navegador.
- Excel v1: [`start_excel.bat`](start_excel.bat) (`http://localhost:8501`).
- Si la instalación se quedó a medias: borrar `.venv` y volver a ejecutar `start.bat`.

**A mano (cualquier sistema, Python 3.10 o posterior):**

```bash
pip install -r requirements.txt
pip install -r requirements-ocr.txt       # opcional: escaneos y texto SHX (OpenCV + onnxruntime)
python -m server                          # app por pasos en http://localhost:8500 (--port, --arbeit, --kein-browser)
streamlit run app.py                      # sólo Excel v1
```

Con Python 3.13, `-c constraints.txt` detrás de cada `pip install` instala exactamente las versiones
probadas, las mismas del contenedor y de la CI.

**Con Docker:**

```bash
docker build -t geoim .                   # sin OCR: --build-arg OCR=0
docker run -p 8500:8500 -v geoim-daten:/data geoim
```

No hace falta Node: la página compilada está en `apps/web/dist`.

Para probar sin un PDF propio, la primera página ofrece [ejemplos](data/beispiele/README.md):
- Berlín georreferenciado.
- Talheim sin coordenadas.
- Una demo sintética.
- Una trasse de 6 km.
- Un PDF sintético para probar la extracción.

También se puede subir una extracción en JSON. Los proyectos se guardan solos y aparecen en
*Zuletzt bearbeitet*.

## En línea

La app completa (servidor FastAPI + página) va en **un contenedor** construido desde este mismo
repositorio ([`Dockerfile`](Dockerfile)). Para [Render](https://render.com) ya está el blueprint
[`render.yaml`](render.yaml). Pasos:
1. En Render, *New → Blueprint*, elegir este repositorio.
2. Escribir una contraseña en `GEO_AGENT_PASSWORT`.

Desde ahí, cada push a `main` vuelve a desplegar. Los datos van a un disco en `/data` y el servidor
está en Fráncfort.

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy?repo=https://github.com/martinpazmino/GeoIM)

**¿Vercel?** Sólo sirve para páginas estáticas, no para esta app:
- Sus funciones aceptan como máximo 4,5 MB por petición, y un Gutachten pesa más.
- No tienen disco para guardar los proyectos.
- No tienen procesos en segundo plano para la extracción.

En [docs/22](docs/22_despliegue.md) están los detalles, con fuentes. También: otras plataformas
(Railway, servidor propio), memoria, seguridad y cómo actualizar las versiones.

> [!IMPORTANT]
> Sin `GEO_AGENT_PASSWORT`, cualquiera que tenga la URL ve y cambia los Gutachten. Con él, el
> navegador pide usuario (cualquiera, o `GEO_AGENT_BENUTZER`) y contraseña. `/gesund` responde sin
> contraseña, para el control de la plataforma.

## Qué hace

1. **Extracción v4** ([docs/17](docs/17_algoritmo_extraccion.md)): clase de página, columnas,
   escala, límites, Bodenart, nivel freático, Schichtenverzeichnis y coordenadas. Cada capa lleva
   su confianza y su procedencia (página, bbox).
2. **Revisión** ([docs/21](docs/21_app_schritte_normen.md)): sondeo a sondeo, con la página del PDF y
   la capa marcada.
   - Avisos sólo para las capas **sin clasificar**.
   - Propuesta según norma con un clic.
   - *Todo revisado*; quitar y restaurar sondeos.

   Todo lo corregido o supuesto queda **marcado** (manuell, Plan, Reihe, schematisch, relativ) y el
   proyecto se guarda solo.
3. **Normas** ([docs/21 §3](docs/21_app_schritte_normen.md#3-mini-base-de-datos-de-normas)): una mini
   base de datos de Kurzzeichen, colores DIN 4023 y grupos DIN 18196, con la evidencia de cada dato.
   La lectura de cada descripción va al IFC (`CPset_Bodenansprache`).
4. **Lage** ([docs/21 §4](docs/21_app_schritte_normen.md#4-lage-calibración-nueva)):
   - Calibración: escala por distancia medida o 1:n, punto de referencia, giro / escala vertical y
     candado.
   - Los sondeos se ponen con puntos o se arrastran sólo en x/y. En la sección se mueve la estación;
     la altura sólo si el PDF no trae GOK.
   - El diámetro de las columnas es ajustable.
5. **Modelo de capas** ([docs/18](docs/18_modelador_capas.md)): unidades por correlación de las
   secuencias, superficies que respetan cada contacto, sólidos cerrados e IFC 4.3 válido en metros.
6. **Visor That Open** ([apps/web](apps/web/README.md)): barra de herramientas compacta, ayuda en
   cada ajuste y el editor de Lage. Con cada cambio, el modelo se recalcula.

Historia:
- [docs/19](docs/19_app_v2.md): app v2 en Streamlit.
- [docs/20](docs/20_lage_pruefung_viewer.md): controles TwinBimM, cámara > 5 km, Prüfstand.

## Estructura

```
server/                     app del Baugrundmodell: FastAPI + proyectos, extracción en segundo plano (python -m server)
ui/                         estado del proyecto (projekt.py), pipeline sin interfaz, página Excel v1
app.py                      Streamlit: sólo Excel v1
start.bat  start_excel.bat  arranque en Windows
spikes/extraktion_v2/       extracción v4 (referencia de la regresión, docs/17)
services/modeler/           modelador `baugrundmodell` y base de datos de normas (python -m baugrundmodell …)
apps/web/                   app por pasos y visor That Open (Vite + TypeScript + lit); dist/ compilado en el repo
geo_agent/                  paquete v1 (Excel)
data/beispiele/             ejemplos (datos factuales y sintéticos)
tests/  scripts/            pruebas de la app y de la API; prueba de punta a punta (Playwright); planes sintéticos
docs/                       notas enlazadas (español): índice en docs/README.md
spikes/                     corpus, regresión, IFC, Supabase
Dockerfile  docker/         contenedor (docs/22); render.yaml: blueprint de Render
.github/workflows/          pruebas en cada push (Prüfungen)
requirements*.txt           dependencias; constraints.txt fija las versiones probadas
```

## Pruebas

- `pytest tests` (lógica del proyecto y API) y `cd services/modeler && pytest tests` (modelador y normas).
- Visor: `python scripts/testplan.py planes && cd apps/web && node scripts/check.mjs <modelo.ifc> ../../planes capturas`.
- App: arrancar `python -m server --port 8511 --kein-browser --arbeit <carpeta vacía>` y después
  `node scripts/check_app.mjs http://localhost:8511 planes capturas`.
- Extracción: regresión sobre PDFs reales, casos de estrés y sintéticos ([CONTRIBUTING](CONTRIBUTING.md)).

GitHub ejecuta estas pruebas en cada push ([`pruefungen.yml`](.github/workflows/pruefungen.yml)):
- Python.
- Compilación de la página.
- Contenedor con contraseña y OCR.

La prueba de punta a punta se lanza a mano (*Run workflow*).

## Documentación y colaboración

- [`docs/README.md`](docs/README.md): arquitectura, decisiones, lecciones y resultados.
- [`CONTRIBUTING.md`](CONTRIBUTING.md): reglas del proyecto (prueba ciega, regresión, nada de PDFs
  de terceros en el repositorio, documentación en español y código en alemán).

## Licencia

**[GNU Affero General Public License v3.0 o posterior](LICENSE)** (AGPL-3.0-or-later).

Quien ofrezca GeoIM a otros por la red debe darles el código fuente de la versión que ejecuta. La
app lo hace con el enlace *Quellcode*. El motivo de la AGPL es PyMuPDF, que sólo es gratis bajo esa
licencia ([docs/14](docs/14_licencias_terceros.md)). Componentes de terceros y sus licencias:
[THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md).

La app extrae y propone; la interpretación geotécnica y su firma son del geotécnico. Se ofrece sin
garantía (AGPL §§ 15–16).
