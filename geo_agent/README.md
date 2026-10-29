---
title: "v1: Excel nach Vorlage"
date: 2026-10-29
tags: [v1, excel, bohrprofil, laengsschnitt]
aliases: [Excel v1, Geo_Template]
---

# v1: Excel nach Vorlage

Paquete `geo_agent` de la primera versión: dos PDF de un layout concreto (Hamburgo) → Excel de 4 hojas.
Se arranca con [`start_excel.bat`](../start_excel.bat) o `streamlit run app.py`. Sólo sirve para el layout para el
que se construyó (posiciones fijas, [docs/01](../docs/01_diagnostico_layout_fijo.md)); para otros Gutachten está la
app por pasos del [README](../README.md). Descripción original, en alemán:

Eingabe: **`Bohrprofil.pdf`** (DIN 4023, Vektor-CAD) und **`Längsschnitt.pdf`** (Vortriebsplan mit
Tunnel). Seite *Excel nach Vorlage (v1)*: beide PDFs hochladen → dynamische Spalten ankreuzen →
Excel generieren. Nur für das Layout, für das v1 gebaut wurde.

## Ausgabe — 4 Blätter (exakt nach `Geo_Template.xlsx`)

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

## Wie es funktioniert

### Bohrprofil (Blatt 1 & 2) — erprobt
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

### Längsschnitt (Blatt 3 & 4) — heikelste Stelle, prüfbar gemacht
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

## Hinweise zur Vorlage

* **Blatt 1** enthält laut Vorlage `Rechtswert`/`Hochwert`. Diese Koordinaten stehen
  nicht im Bohrprofil-PDF und bleiben leer (gelb markiert).
* **Blatt 3** der Vorlage hat **keine** separate „Sohle"-Spalte (anders als die
  Aufgaben-Prosa). `NHN` = GOK der zugehörigen Bohrung, `OK Tunnel bis GOK` =
  Überdeckung (GOK − OK), `OK Tunnel`/`Achse` = Tunnelgeometrie an der Bohr-Station.
* `Bohr_BID` (Blatt 3) und `bohr_id` (Blatt 4) = die Kernbohrung, die den Abschnitt
  definiert (im Längsschnitt verortet, mit vorliegendem Bohrprofil).

## Performance (v1)

Das Bohrprofil wird in < 1 s ausgewertet. Der Längsschnitt dauert ~20 s, weil
`page.get_drawings()` auf einer Seite mit > 150 000 Vektorobjekten arbeitet; das
Ergebnis wird pro Upload gecacht, sodass das An-/Abwählen von DIN-Spalten sofort
reagiert.

Up: [README del repositorio](../README.md)

Related: [01 Diagnóstico del layout fijo](../docs/01_diagnostico_layout_fijo.md) · [Índice de la documentación](../docs/README.md)
