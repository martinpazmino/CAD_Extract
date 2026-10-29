---
title: "Glossary (German – English)"
date: 2026-10-23
updated: 2026-10-29
tags: [glossary, terminology]
aliases: [Glossary, Terminology]
---

# Glossary (German – English)

The documentation is in English, but it keeps the German technical terms used by the Gutachten and by
the app's interface. This table explains them.

| Term | Meaning |
|---|---|
| **Abschnitt** | Run of consecutive Schichten of the same class in one Bohrung (input of the modeler) |
| **Aufschluss** | Exploration point of the subsurface (Bohrung, trial pit, penetration test) |
| **Auffüllung** | Fill, made ground |
| **Bodengutachten / Baugrundgutachten / Gutachten** | Geotechnical report |
| **Gutachter** | Author of the Gutachten (geotechnical office or engineer) |
| **Baugrundmodell** | Ground model (3D interpretation of Schichten and parameters) |
| **Bohrprofil / Schichtenverzeichnis** | Borehole log drawing / layer log (DIN 4023 drawing / description per Schicht, DIN 4022 form) |
| **Bohrung, Bohrungen (B, BK, KB, RKS)** | Borehole(s) (Kernbohrung = with core recovery; RKS = Rammkernsondierung) |
| **Bodenart** | Soil type (Sand, Kies, Schluff, Ton, …) |
| **Bodengruppe** | Soil group according to DIN 18196 (GE … HZ) |
| **DIN 4023** | German standard for the graphic representation of Bohrungen (revised 2023) |
| **DIN EN ISO 14688-1** | Identification and classification of soils (description) |
| **DPH / DPL / DPM** | Dynamic probing (Rammsondierung) heavy / light / medium; value `N10` = blows per 10 cm |
| **CPT / Drucksondierung** | Cone penetration test; `q_c` cone resistance, `f_s` sleeve friction. In the current drawings the `DS` soundings are excluded (`geo_agent/bohrprofil.py:32`); whether `DS` means Drucksondierung is **[to be confirmed]** |
| **Einheit, Einheiten (Modelleinheit)** | Unit(s) of the ground model: a Bodenart at one place in the sequence ("Sand 1", "Kies 1") |
| **einchecken / Prüfstand** | Record the review state with a fingerprint of the model / the review dashboard |
| **Endteufe / Endtiefe** | Final depth of a Bohrung |
| **GOK (Geländeoberkante)** | Ground level at the Bohrung |
| **GWM (Grundwassermessstelle)** | Groundwater observation well (piezometer) |
| **Grundwasser (GW)** | Groundwater; *angetroffen* = encountered while drilling, *Ruhewasserspiegel* = stabilised level |
| **HGW / MGW / Bemessungswasserstand** | Highest / mean / design Grundwasser level |
| **Homogenbereich** | Ground unit with homogeneous properties (DIN 18300 ff.) |
| **Kornbereich, Nebenanteil, Konsistenz, Kalkgehalt** | Grain range (f/m/g), secondary fraction (schwach/stark), consistency (weich…fest), lime content (k+, k++) |
| **Kurzzeichen** | DIN 4023 abbreviation (S, G, U, T, mS, fs' …) |
| **Lage** | Position of a Bohrung (coordinates or station); the app step that places the Bohrungen |
| **Lageplan** | Site plan |
| **Längsschnitt** | Longitudinal section (here: geological, with the tunnel) |
| **Legende / Zeichenerklärung** | Legend of the drawing |
| **Mutterboden / Oberboden** | Topsoil |
| **nachführen** | Keep the model updated automatically after every change |
| **NHN / NN** | Normalhöhennull (DHHN92/2016) / Normalnull (DHHN12): height datums |
| **OCG (Optional Content Group)** | Layer of a PDF; keeps the layers of the CAD drawing |
| **OK / Achse / Sohle (Tunnel)** | Crown / axis / invert of the tunnel |
| **Rechtswert / Hochwert** | Easting / northing (Gauß-Krüger; in UTM: Ostwert / Nordwert) |
| **Reihe** | Row of Bohrungen without coordinates, with stations or distances (schematic Lage) |
| **Schicht, Schichten** | Layer(s) of a Bohrung |
| **Schraffur / Signatur** | Graphic pattern of the Bodenart in the column (dots, circles, stripes) |
| **Station / Tunnelmeter (TM)** | Chainage along the alignment |
| **Trasse** | Route / alignment of a linear project (road, tunnel, pipeline) |
| **Überhöhung** | Vertical exaggeration of the drawing |
| **Unterlage** | Plan PDF (Lageplan or Längsschnitt) placed under the Bohrungen in the viewer |
| **Sidebar (swissgeol)** | Depth column; *AAboveB* = stacked values, *AToB* = intervals `a–b` |
| **Strip log (swissgeol)** | Graphic column of the Bohrung |
| **Ground truth** | Verified reference data to measure the extraction |

Up: [Index](README.md)

Related: [04 Schraffur](04_schraffur_din4023.md) · [05 Sondierungen](05_sondierungen.md) · [06 Grundwasser](06_grundwasser.md) · [08 swissgeol](08_swissgeol_reuse.md)
