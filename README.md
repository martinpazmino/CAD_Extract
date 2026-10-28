# Geo_Agent — del Bodengutachten al Baugrundmodell

Herramienta local (Streamlit, sólo `localhost`) para informes geotécnicos alemanes en PDF:

* **Baugrundmodell (v2, página principal):** se suben los PDF → se reconocen los sondeos
  (vector o escaneo con OCR) → **tablas** para revisar y corregir sondeos y capas → los sondeos se
  colocan sobre el **PDF del Lageplan o del Längsschnitt** en el visor (o en fila con distancias
  propias) → *Baugrundmodell erzeugen*: las **Bodenschichten se generan** como modelo 3D (IFC 4.3:
  `IfcGeomodel` + `IfcBorehole`) y **se ajustan solas a cada cambio** → el estado de revisión se
  **eincheckt**. Visor **That Open** con los controles del TwinBimM, también para trasses de más de
  5 km. Export: IFC con estado de revisión, informe de control, JSON.
* **Excel nach Vorlage (v1):** Bohrprofil + Längsschnitt (layout Hamburgo) → `.xlsx` de 4 hojas.

![Lageplan sintético calibrado en el visor: sondeos arrastrados a su símbolo](docs/img/20_lageplan_kalibriert.jpg)

## Arrancar

**Windows:** doble clic en [`start.bat`](start.bat). La primera vez crea `.venv` e instala todo
(unos minutos; el OCR es opcional y no bloquea), después abre `http://localhost:8501`.

**A mano (cualquier sistema):**

```bash
pip install -r requirements.txt
pip install -r requirements-ocr.txt      # opcional: escaneos y texto SHX (OpenCV + onnxruntime)
streamlit run app.py
```

No hace falta Node: el visor compilado está en `apps/web/dist`. Sin PDF propio, la barra lateral
ofrece [ejemplos](data/beispiele/README.md) (Berlín georreferenciado, Talheim sin coordenadas,
demo sintética, trasse sintética de 6 km y un PDF sintético para probar la subida).

Si la instalación se quedó a medias: borrar la carpeta `.venv` y volver a ejecutar `start.bat`.

## Qué hace la v2

1. **Extracción v4** ([docs/17](docs/17_algoritmo_extraccion.md)): clase de página, columnas,
   escala, límites, Bodenart, nivel freático, Schichtenverzeichnis, coordenadas; cada capa con
   confianza y procedencia (página, bbox).
2. **Revisión antes del modelo** ([docs/20](docs/20_lage_pruefung_viewer.md)): tablas editables de
   sondeos (incluir, revisado, GOK, Rechts-/Hochwert, EPSG) y de capas (von/bis, Bodenart, revisado),
   **Lage** sobre el PDF del plano (calibrado con dos puntos) o fila con distancias propias
   (BK1 → BK2 10 m …), **Prüfstand** con *Einchecken*. Todo lo corregido o supuesto queda **marcado**
   (manuell, Plan, Reihe, schematisch, relativ) y el estado del proyecto se guarda solo.
3. **Modelo de capas** ([docs/18](docs/18_modelador_capas.md)): unidades por correlación de las
   secuencias (clase + cota/profundidad, acuñamientos, lentes, sondeos cortos), superficies que
   respetan cada contacto, sólidos cerrados, IFC 4.3 válido. Las unidades se pueden fijar a mano.
4. **Visor That Open** ([apps/web](apps/web/README.md)) dentro de la página, con los controles del
   TwinBimM (barra inferior, ViewCube, engranaje, coordenadas reales) y el editor de Lage; tras
   *Erzeugen* el modelo se recalcula con cada cambio.

Detalle de la app: [docs/19](docs/19_app_v2.md) y [docs/20](docs/20_lage_pruefung_viewer.md). Sin
coordenadas ni plano, los sondeos van en una **fila** (esquemática con la distancia estándar,
avisado en la app, el IFC y el visor; con distancias propias o estaciones del Längsschnitt, marcada
como tal).

## Estructura

```
app.py                      entrada Streamlit (páginas v2 y v1)
start.bat                   arranque en Windows (venv + instalación + navegador)
ui/                         páginas, pipeline sin interfaz, componente del visor
spikes/extraktion_v2/       extracción v4 (referencia de la regresión, docs/17)
services/modeler/           modelador de capas `baugrundmodell` (python -m baugrundmodell …)
apps/web/                   visor That Open (Vite + TypeScript); dist/ compilado en el repo
geo_agent/                  paquete v1 (Excel)
data/beispiele/             ejemplos (datos factuales y sintéticos)
tests/  scripts/            pruebas de la app y prueba de punta a punta (Playwright)
docs/                       notas enlazadas (español): índice en docs/README.md
spikes/                     corpus, regresión, IFC, Supabase
```

Pruebas: `pytest tests`, `cd services/modeler && pytest tests`; visor:
`python scripts/testplan.py planes && cd apps/web && node scripts/check.mjs <modelo.ifc> ../../planes capturas`;
con la app en marcha: `node scripts/check_app.mjs http://localhost:8501 capturas --plan planes`.

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
