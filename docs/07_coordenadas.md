---
title: "Coordenadas y georreferencia de los sondeos"
date: 2026-10-23
tags: [geo_agent, extraccion, coordenadas, crs, georreferencia]
aliases: [Coordenadas, Rechtswert Hochwert, Georreferencia]
---

# Coordenadas y georreferencia de los sondeos

**Conclusión:** Rechts-/Hochwert no están en el Bohrprofil (`geo_agent/excel_writer.py:145-147`
los deja vacíos), pero casi siempre están en **otro lugar del Gutachten**: una tabla de
Aufschlüsse, el Lageplan o el eje del proyecto. Sin coordenadas no hay modelo 3D real, así que
esta es la extracción que desbloquea el Baugrundmodell.

**Estado:** tabla probada en el prototipo (`coordinate_table` en
[`prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py)): **17/17** sondeos con Ost-/Nordwert
exactos. Lageplan y eje: diseño. swissgeol sin cambios: **0/14** (sólo valida CRS suizos).

## 1. Fuentes, por orden de preferencia

| # | Fuente | Método | Confianza |
|---|---|---|---|
| 1 | Tabla "Lage- und Höhenverzeichnis der Aufschlüsse" (Anlage) | `page.find_tables()` + lectura por celda | alta, y trae la GOK para cruzar con el Bohrprofil |
| 2 | Texto en la cabecera del sondeo (`R = …`, `H = …`, `E/N`, `Ostwert/Nordwert`) | regex cerca de palabras clave | media-alta |
| 3 | Lageplan PDF | símbolos de sondeo + etiqueta; transformación afín con ≥ 3 etiquetas de la cuadrícula; residuos | media |
| 4 | Eje (LandXML de Civil 3D) + estación del Längsschnitt + offset rotulado | `XY = eje(estación) + offset` | media |
| 5 | Entrada manual / CSV en la UI | — | según usuario |

## 2. Trampa verificada en la lectura de tablas

`tab.extract()` de PyMuPDF devolvió `565 081,64` como `"56508164\n,"` (pierde los espacios de
millares y separa la coma). Solución probada: leer cada celda con
`page.get_text("words", clip=celda)` y unir las palabras. Generalizable: **nunca parsear números
desde texto "aplanado"**; siempre desde palabras con su bbox.

## 3. Sistemas de referencia en Alemania

| CRS | EPSG | Rasgo para detectarlo |
|---|---|---|
| ETRS89 / UTM 32N | 25832 | Este 6 dígitos (280 000–920 000) o 8 con prefijo de zona `32…`; Norte 7 dígitos (5,2–6,1 M) |
| ETRS89 / UTM 33N | 25833 | ídem con prefijo `33…` (este de Alemania) |
| DHDN / Gauß-Krüger zonas 2–5 | 31466–31469 | `R` 7 dígitos empezando por la zona (2…5), `H` 7 dígitos |
| Alturas | DHHN2016 y DHHN92 (`NHN`); antiguo DHHN12 (`NN`) | texto `m NHN` / `m NN`; diferencias de pocos cm a dm según la región → registrar el sistema |

Reglas: plausibilidad de rangos, quitar prefijo de zona, detectar ejes intercambiados (swissgeol
hace lo mismo para LV95/LV03: `coordinate_extraction.py`, "Swapping coordinates"). Si sólo hay
Gauß-Krüger, transformar con `pyproj` al CRS del proyecto y guardar el original.

## 4. Validaciones cruzadas

- GOK de la tabla = GOK del Bohrprofil (±2 cm).
- Distancia del sondeo al eje ≈ offset rotulado en el Längsschnitt.
- Estación del sondeo en el Längsschnitt ≈ estación proyectada de su XY sobre el eje.
- Todos los sondeos dentro de la envolvente del Lageplan.

## 5. Qué reutilizar de swissgeol

La estructura de `CoordinateExtractor`: palabras clave (`Koordinaten`, `Koord.`), etiquetas `X/Y`,
búsqueda cerca de la palabra clave y selección de la mejor coincidencia por página. Hay que
reescribir los validadores (`LV95Coordinate`, `LV03Coordinate`) para los CRS alemanes →
[08](08_swissgeol_reutilizacion.md).

## 6. Modelo de datos

`boreholes.collar geometry(PointZ)` con el SRID del proyecto (Z = GOK), más `coord_source` y
`confidence` en `provenance`. En IFC: `IfcMapConversion` + `IfcProjectedCRS` (verificado en el
[spike IFC](../spikes/ifc_thatopen/README.md)).

Up: [Índice](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [03 Längsschnitt](03_laengsschnitt_generalizacion.md) · [08 swissgeol](08_swissgeol_reutilizacion.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md)
