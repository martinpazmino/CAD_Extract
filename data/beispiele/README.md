---
title: "Ejemplos para la app v2"
date: 2026-10-27
tags: [ejemplos, app, datos]
aliases: [Beispiele]
---

# Ejemplos para la app v2

La app ([`app.py`](../../app.py), página *Baugrundmodell*) los ofrece en la barra lateral para
recorrer el flujo completo sin un PDF propio. Sólo datos factuales o generados por nosotros: los
PDF de terceros **no** están en el repo (fuente y `sha256` abajo).

| Archivo | Qué es | Lo que enseña |
|---|---|---|
| [`berlin_v67b.json`](berlin_v67b.json) | Extracción v4 (JSON canónico) del geotechnischer Bericht B-Plan V-67b-VE, Berlín: Anlage 3 en raster, leída con OCR | Modelo **georreferenciado** (EPSG:25833) con 5 sondeos; 2 sondeos de archivo sin coordenadas quedan fuera y marcados |
| [`talheim.json`](talheim.json) | Extracción v4 del informe de la Sickerwasserleitung Talheim (perfiles vectoriales) | PDF **sin coordenadas**: sondeos en fila (distancias propias o arrastrados en el Längsschnitt), marcado en el IFC y en el visor |
| [`demo_synthetisch.json`](demo_synthetisch.json) | Caso sintético `demo` de [`baugrundmodell.synthetisch`](../../services/modeler/baugrundmodell/synthetisch.py) | 12 sondeos, lente de Kies, Torf que se acuña, sondeos cortos |
| [`trasse_synthetisch.json`](trasse_synthetisch.json) | Caso sintético `trasse` del mismo módulo | **Trasse de 6 km**, 51 sondeos cada 120 m: cámara, delimitación y rendimiento para modelos > 5 km ([20](../../docs/20_lage_pruefung_viewer.md)) |
| [`synthetisch_bohrprofil.pdf`](synthetisch_bohrprofil.pdf) | PDF generado por [`synth_bohrprofil.py`](../../spikes/extraktion_v2/synth_bohrprofil.py) (layout A) | **Subida de PDF** de punta a punta: extracción → modelo en coordenadas locales del Lageplan |

Fuentes de los PDF reales (no incluidos):

- Berlín: <https://www.berlin.de/sen/stadtentwicklung/_assets/planung/bebauungsplanverfahren/bebauungsplanverfahren-der-senatsverwaltung-fuer-stadtentwicklung-bauen-und-wohnen/v-67b-ve/geotechnischer_bericht_b_plan_v67bve.pdf>, `sha256` 659713ac…27c4
- Talheim: <https://uvp-verbund.de/documents-ige-ng/igc_bw/9b935c78-6f28-4f37-9f29-2ce860316ece/230405_Geotech%20Kaiser_7867_Bericht%20Sickerwasserleitung%20Talheim.pdf>, `sha256` 50a3af26…db03

Las cifras de estos dos son de **entrenamiento** (los PDFs se usaron para ajustar el extractor,
[15](../../docs/15_resultados_pdfs_reales.md)); no miden la generalidad.

Up: [Índice de documentación](../../docs/README.md)

Related: [19 App v2](../../docs/19_app_v2.md) · [18 Modelador de capas](../../docs/18_modelador_capas.md) · [Corpus](../../spikes/korpus/README.md)
