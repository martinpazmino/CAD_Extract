---
title: "Spike: IFC 4.3 geotécnico en That Open"
date: 2026-10-23
tags: [spike, ifc, thatopen]
aliases: [Spike IFC]
---

# Spike: IFC 4.3 geotécnico en That Open

Comprueba que un Baugrundmodell exportado con IfcOpenShell (`IfcBorehole`, `IfcGeomodel`,
`IfcGeotechnicalStratum`, georreferenciado EPSG:25832) se puede cargar en That Open Engine.

| Archivo | Qué hace |
|---|---|
| [`baugrund_ifc_spike.py`](baugrund_ifc_spike.py) | Genera el IFC4X3 (3 sondeos, modelo layer-cake con IDW) |
| [`thatopen_import_spike.mjs`](thatopen_import_spike.mjs) | Lo importa con `web-ifc` y con el `IfcImporter` de `@thatopen/fragments` |
| [`export_ifc.py`](export_ifc.py) | **Datos reales:** JSON canónico de la extracción → IFC4X3 (`IfcBorehole` + estratos con procedencia y confianza; georreferenciado si hay CRS). Usa el escritor de [`services/modeler`](../../services/modeler/README.md); el modelo de capas (N3) lo genera `python -m baugrundmodell` |
| [`package.json`](package.json) | Versiones fijadas (fragments 3.6.0, web-ifc 0.0.78) |

```bash
pip install ifcopenshell numpy && python baugrund_ifc_spike.py baugrund_spike.ifc
npm install && npm run spike
```

**Con datos reales (2026-10-26):** Berlín V-67b-VE (raster + OCR) → 7 sondeos, 80 estratos, 5 en
EPSG:25833 → 0 errores de esquema → That Open: 80 elementos con geometría. Un Pset vacío es IFC
inválido: el exportador sólo crea `Pset_BoreholeCommon` si hay nivel freático.

**Resultado (sintético):** el IFC valida sin errores de esquema; `web-ifc` genera mallas para los 16 estratos;
el `IfcImporter` **los descarta por defecto** y los importa al añadir las clases geotécnicas a
`importer.classes.elements`. Detalle: [arquitectura §8.2](../../docs/ARQUITECTURA_BAUGRUNDMODELL.md#82-resultados-del-spike-verificado).

Up: [Índice de documentación](../../docs/README.md)

Related: [Arquitectura](../../docs/ARQUITECTURA_BAUGRUNDMODELL.md) · [11 Decisiones](../../docs/11_decisiones.md) · [07 Coordenadas](../../docs/07_coordenadas.md)
