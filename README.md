# Geo_Agent — del Bodengutachten al Baugrundmodell

Herramienta local (sólo `localhost`) para informes geotécnicos alemanes en PDF:

* **Baugrundmodell (app por pasos, pantalla completa):** **1 Gutachten** (subir PDF; vector o
  escaneo con OCR) → **2 Bohrungen** (revisar y corregir sondeos y capas; avisos para capas sin
  clasificar; lectura de cada descripción según **DIN 4023 / EN ISO 14688-1 / DIN 18196**; quitar
  sondeos) → **3 Lage** (Lageplan o Längsschnitt en PDF: distancia medida → escala, punto de
  referencia con coordenada, candado; después se arrastran los sondeos; o fila con distancias
  propias) → **4 Einheiten** (cómo se unen las capas) → **5 Modell** (IFC 4.3 `IfcGeomodel` +
  `IfcBorehole` en el visor **That Open** con los controles del TwinBimM, también para trasses de
  más de 5 km; *einchecken* del estado de revisión; export). Cada paso actualiza el siguiente.
* **Excel nach Vorlage (v1):** Bohrprofil + Längsschnitt (layout Hamburgo) → `.xlsx` de 4 hojas.

![Lageplan sintético calibrado en el visor: sondeos arrastrados a su símbolo](docs/img/20_lageplan_kalibriert.jpg)

## Arrancar

**Windows:** doble clic en [`start.bat`](start.bat). La primera vez crea `.venv` e instala todo
(unos minutos; el OCR es opcional y no bloquea); después abre `http://localhost:8500` en el
navegador. Excel v1: [`start_excel.bat`](start_excel.bat) (`http://localhost:8501`).

**A mano (cualquier sistema):**

```bash
pip install -r requirements.txt
pip install -r requirements-ocr.txt      # opcional: escaneos y texto SHX (OpenCV + onnxruntime)
python -m server                          # app por pasos en http://localhost:8500 (--port, --arbeit, --kein-browser)
streamlit run app.py                      # sólo Excel v1
```

No hace falta Node: la página compilada está en `apps/web/dist`. Sin PDF propio, la primera
página ofrece [ejemplos](data/beispiele/README.md) (Berlín georreferenciado, Talheim sin
coordenadas, demo sintética, trasse de 6 km y un PDF sintético para probar la extracción); también
se puede subir una extracción en JSON. Los proyectos se guardan solos y aparecen en *Zuletzt
bearbeitet*.

Si la instalación se quedó a medias: borrar la carpeta `.venv` y volver a ejecutar `start.bat`.

## Qué hace

1. **Extracción v4** ([docs/17](docs/17_algoritmo_extraccion.md)): clase de página, columnas,
   escala, límites, Bodenart, nivel freático, Schichtenverzeichnis, coordenadas; cada capa con
   confianza y procedencia (página, bbox).
2. **Revisión** ([docs/21](docs/21_app_schritte_normen.md)): sondeo a sondeo con la página del PDF y
   la capa marcada; avisos sólo para capas **sin clasificar**; propuesta según norma con un clic;
   *todo revisado*; quitar y restaurar sondeos. Todo lo corregido o supuesto queda **marcado**
   (manuell, Plan, Reihe, schematisch, relativ) y el proyecto se guarda solo.
3. **Normas** ([docs/21 §3](docs/21_app_schritte_normen.md#3-mini-base-de-datos-de-normas)): mini
   base de datos de Kurzzeichen, colores DIN 4023 y grupos DIN 18196 con la evidencia de cada dato;
   la lectura de cada descripción va al IFC (`CPset_Bodenansprache`).
4. **Lage** ([docs/21 §4](docs/21_app_schritte_normen.md#4-lage-calibración-nueva)): escala por
   distancia medida o 1:n, punto de referencia, giro / escala vertical, candado; los sondeos se
   arrastran sólo en x/y (sección: estación; la altura sólo sin GOK del PDF). Diámetro de las
   columnas ajustable.
5. **Modelo de capas** ([docs/18](docs/18_modelador_capas.md)): unidades por correlación de las
   secuencias, superficies que respetan cada contacto, sólidos cerrados, IFC 4.3 válido en metros.
6. **Visor That Open** ([apps/web](apps/web/README.md)) con barra de herramientas compacta, ayuda en
   cada ajuste y el editor de Lage; con cada cambio el modelo se recalcula.

Historia: [docs/19](docs/19_app_v2.md) (app v2 en Streamlit) y [docs/20](docs/20_lage_pruefung_viewer.md)
(controles TwinBimM, cámara > 5 km, Prüfstand).

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
```

Pruebas:

- `pytest tests` (lógica del proyecto y API) y `cd services/modeler && pytest tests` (modelador y normas).
- Visor: `python scripts/testplan.py planes && cd apps/web && node scripts/check.mjs <modelo.ifc> ../../planes capturas`.
- App: `python -m server --port 8511 --kein-browser --arbeit <carpeta vacía>` y
  `node scripts/check_app.mjs http://localhost:8511 planes capturas`.

Documentación: [`docs/README.md`](docs/README.md) (arquitectura, decisiones, lecciones, resultados).

## v1: Excel nach Vorlage (descripción original, en alemán)

Eingabe: **`Bohrprofil.pdf`** (DIN 4023, Vektor-CAD) und **`Längsschnitt.pdf`** (Vortriebsplan mit
Tunnel). Seite *Excel nach Vorlage (v1)*: beide PDFs hochladen → dynamische Spalten ankreuzen →
Excel generieren. Nur für das Layout, für das v1 gebaut wurde.

### Ausgabe — 4 Blätter (exakt nach `Geo_Template.xlsx`)

| Blatt | Spalten | Zeilen |
|---|---|---|
| **Geomodul** | Bohr_ID, NHN, Tiefe, Rechtswert, Hochwert | je Kernbohrung |
| **Geomodul_Bodenschicht** | Bohr_ID, Bodenart, Tiefe(oberkante) | je konsolidierter Schicht |
| **Geo_Tunnel** | Bohr_BID, NHN, OK Tunnel bis GOK, OK Tunnel, Achse, Sohle Tunnel, Tunnelmeter, Bodenart auf Tunnel | je **Abschnitt** (Bohrungs-Zone) |
| **Geo_Spec** *(dynamisch)* | bodenart, abschnitt_id, Prozent_Bodenart_pro_abschnitt, bohr_id, Tunnelmeter **+ DIN-Spalten** | je **Abschnitt × Bodenart (≥ 5 %)** |

Die DIN-Spalten von Blatt 4 (`kornbereich`, `nebenanteil_staerke`, `kalkgehalt`,
`konsistenz`) erscheinen nur, wenn die jeweilige Sektion in der **Bohrprofil-Legende**
vorkommt — und nur die, die der Nutzer ankreuzt. CPT-/Sonden-Spalten werden bewusst
weggelassen.

**Zellfarben:** 🟩 grün = sicher · 🟨 gelb = unsicher / nicht klassifizierbar
(manuell prüfen).

### Wie es funktioniert

#### Bohrprofil (Blatt 1 & 2) — erprobt
* Nur **Kernbohrungen** (Header `B nn/jj`); Sonden (`DS`) und Messstellen (`GWM`)
  werden ausgeschlossen, dienen aber als X-Grenze des Bodenart-Textbands.
* Pro Bohrung: Tiefen-Spalte (Paare `(NHN_rel) tiefe`), Bodenart-Textband,
  Diagramm (ignoriert). Achsen-Rauschen wird gefiltert.
* **Validierung:** Geländehöhe − Endtiefe muss den letzten NHN-Wert ergeben
  (z. B. B 18/19: −14,51 − 35,00 = −49,51 ✓). Im Tool je Bohrung sichtbar.
* Blatt 2 konsolidiert aufeinanderfolgende gleiche Bodenarten und gröbert sie für
  Civil 3D (Feinsand/Mittelsand/Grobsand → **Sand**, Glimmerschluff → Glimmerton).
  Das Bodenart-Vokabular kommt aus der Legende (Sektion BODENARTEN) — nicht hartkodiert.
  Wiederholt sich eine Bodenart innerhalb **einer** Bohrung, wird sie durchnummeriert
  (z. B. `Sand`, `Sand1`, `Sand2`), damit jede Schicht eindeutig benannt ist.

#### Längsschnitt (Blatt 3 & 4) — heikelste Stelle, prüfbar gemacht
* **X → Tunnelmeter** und **Y → NHN** über lineare Regression der Achsen-Labels.
* **Tunnelröhre:** nur die grauen Füllpolygone (RGB ≈ 0,73) werden als saubere
  Maske gerastert → pro Tunnelmeter OK (oben) / Sohle (unten) / Achse (Mitte).
  Validiert gegen die `TS=…m`-Beschriftungen (Tunnelsohle) im Plan auf den Zentimeter.
* **Bodenart auf Tunnel:** wird **aus dem Bohrprofil** abgeleitet, nicht aus den
  Farben des Längsschnitts. Die Tiefe der Tunnelachse unter der GOK der
  zugehörigen Bohrung fällt in genau eine Schicht aus Blatt 2 → deren Bodenart.
  In Blatt 4 ergibt der Tunnelquerschnitt (OK–Sohle) gegen die Bohrprofil-Schichten
  die Bodenart-Anteile. (Die Farbpolygon-Auswertung dient nur noch der Sichtprüfung
  im Vorschaubild.)
* **abschnitt_id = Einflusszone je Bohrung:** Der Tunnel wird an den verorteten
  Bohrungen in Abschnitte geteilt. Die Grenze zwischen zwei benachbarten Bohrungen
  liegt auf der **Mitte** ((TM_i + TM_{i+1})/2); die erste Zone beginnt am Tunnel­anfang,
  die letzte endet am Tunnelende. So gibt es **eine Zeile je Abschnitt** statt je
  Tunnelmeter. In Blatt 3 ist `NHN` die **GOK der Bohrung** (aus dem Bohrprofil,
  genauer als der Terrain-Scan), `OK Tunnel bis GOK` = GOK − OK, und `Tunnelmeter`
  die Station der Bohrung. In Blatt 4 wird je Abschnitt die Bodenart-Zusammensetzung
  entlang des Tunnels (Anteile in %) aufgeschlüsselt.
* Im Reiter **„Tunnel-Vorschau"** überlagert ein Prüfbild die erkannte OK-Linie (rot),
  Sohle (blau), Abschnitts-Bänder und verortete Bohrungen über den Originalplan —
  damit Zwischenergebnisse sichtbar sind statt blind geschrieben.

### Hinweise zur Vorlage

* **Blatt 1** enthält laut Vorlage `Rechtswert`/`Hochwert`. Diese Koordinaten stehen
  nicht im Bohrprofil-PDF und bleiben leer (gelb markiert).
* **Blatt 3** der Vorlage hat **keine** separate „Sohle"-Spalte (anders als die
  Aufgaben-Prosa). `NHN` = GOK der zugehörigen Bohrung, `OK Tunnel bis GOK` =
  Überdeckung (GOK − OK), `OK Tunnel`/`Achse` = Tunnelgeometrie an der Bohr-Station.
* `Bohr_BID` (Blatt 3) und `bohr_id` (Blatt 4) = die Kernbohrung, die den Abschnitt
  definiert (im Längsschnitt verortet, mit vorliegendem Bohrprofil).

### Performance (v1)

Das Bohrprofil wird in < 1 s ausgewertet. Der Längsschnitt dauert ~20 s, weil
`page.get_drawings()` auf einer Seite mit > 150 000 Vektorobjekten arbeitet; das
Ergebnis wird pro Upload gecacht, sodass das An-/Abwählen von DIN-Spalten sofort
reagiert.
