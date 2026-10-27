---
title: "Modelador de capas (baugrundmodell)"
date: 2026-10-27
tags: [modelo, layer-cake, ifc]
aliases: [baugrundmodell]
---

# Modelador de capas (`baugrundmodell`)

JSON canónico de la extracción → unidades automáticas → superficies → sólidos cerrados →
IFC 4.3 (`IfcGeomodel` + `IfcBorehole`) para That Open. Diseño, parámetros y resultados:
[18 Modelador de capas](../../docs/18_modelador_capas.md).

```bash
pip install -r requirements.txt
cd services/modeler
python -m baugrundmodell modelo.ifc extraccion1.json [extraccion2.json ...] --bericht informe.json
#   --methode idw|tps   --raster 2.0   --puffer 15   --basis 10.0 (m NHN)   --ohne-bohrsaeulen
#   --einheiten einheiten.json   (unidades del geotécnico; plantilla en informe.json → vorlage_einheiten)
python -m pytest tests                                     # 31 pruebas con verdad sintética
python -m baugrundmodell.synthetisch demo demo.json        # casos: geneigt auskeilen linse zensiert stoerungen demo
```

| Módulo | Qué hace |
|---|---|
| [`einheiten.py`](baugrundmodell/einheiten.py) | Preparación de sondeos (exclusiones con motivo), correlación de Schichtfolgen por programación dinámica, contactos exacto / libre / censurado / desconocido |
| [`flaechen.py`](baugrundmodell/flaechen.py) | Dominio (envolvente + buffer), malla TIN con los sondeos como nodos, IDW/TPS exactos, lentes, censura, recorte, extensión de unidades parciales |
| [`koerper.py`](baugrundmodell/koerper.py) | Sólido cerrado por unidad, comprobación de cierre y volumen |
| [`ifc4x3.py`](baugrundmodell/ifc4x3.py) | Escritor IFC 4.3 (N1 columnas y N3 modelo), colores, Psets |
| [`modell.py`](baugrundmodell/modell.py) | Orquestación, informe JSON |
| [`synthetisch.py`](baugrundmodell/synthetisch.py) | Casos con verdad conocida (pruebas y demo del visor) |

Ver el resultado: [visor `apps/web`](../../apps/web/README.md) o la app (`streamlit run app.py`, [19](../../docs/19_app_v2.md)).

Up: [Índice de documentación](../../docs/README.md)

Related: [18 Modelador de capas](../../docs/18_modelador_capas.md) · [Arquitectura §7](../../docs/ARQUITECTURA_BAUGRUNDMODELL.md#7-baugrundmodell-generación-de-geometrías) · [Spike IFC](../../spikes/ifc_thatopen/README.md)
