---
title: "Grundwasser: símbolos, texto y líneas de agua"
date: 2026-10-23
tags: [geo_agent, extraccion, grundwasser]
aliases: [Grundwasser, Nivel freático]
---

# Grundwasser: símbolos, texto y líneas de agua

**Conclusión:** el nivel freático no se extrae hoy. Aparece de tres formas — símbolo en el
Bohrprofil, texto con palabras clave y líneas de agua en el Längsschnitt — y las tres se pueden
leer de forma determinista. Conviene combinar la detección geométrica propia (símbolo DIN) con
las listas de palabras clave y la detección por color de swissgeol.

**Estado:** símbolo probado en el prototipo (`groundwater` en
[`prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py)): **17/17** sondeos sintéticos con
profundidad a ±5 cm y fecha. swissgeol sin cambios encontró **0/14** en los 5 layouts en que se
probó (su detector busca el símbolo suizo de dos líneas; [08](08_swissgeol_reutilizacion.md#4-prueba-swissgeol-sin-cambios-sobre-nuestros-pdfs)).

**Con PDFs reales** ([15](15_resultados_pdfs_reales.md)): Talheim **3/4**. El triángulo puede
estar junto a la columna vecina y lo que decide el sondeo es el extremo de la **línea de agua**.
El símbolo de "angebohrt" (dos trazos + línea) aún no se lee. Wachenroth: "kein Grundwasser"
detectado en **6/6** y guardado como dato. swissgeol: 1 nivel freático falso.

En **Hausham** (DC-Software) el agua va como texto `GW 2.53m` (4/4 tras añadir la lectura por
texto). Hubo que descartar como "no agua" tres cosas: la serie de ▽ de la **regla de cotas**, los
triángulos con una **cota** al lado (`741.00m`) y el ▼ de la **cota de inicio** (profundidad 0).

## 1. Formas de aparición

| Forma | Dónde | Cómo se lee |
|---|---|---|
| Símbolo DIN 4023 (triángulo, relleno o no, a veces con rayas debajo) | junto a la columna | path cerrado de 3 segmentos, 3–16 pt, vértice hacia abajo; la punta es el nivel |
| Texto `GW 3,20 m u. GOK`, `Ruhewasserspiegel …`, fecha | junto al símbolo o en la descripción | palabras clave + número + fecha |
| Texto en color minoritario (azul) con fecha | junto a la columna | heurística de swissgeol `groundwater_color_detection.py` |
| Líneas HGW / MGW / Bemessungswasserstand | Längsschnitt | polilíneas azules/discontinuas → `(estación, NHN)` ([03 §6](03_laengsschnitt_generalizacion.md#6-terreno-y-agua)) |

La diferencia entre "angetroffen" y "Ruhewasserstand / nach Bohrende" se toma de la **leyenda del
documento** (relleno, número de rayas), no del código.

## 2. Algoritmo (símbolo)

1. Paths cerrados con exactamente 3 segmentos y tamaño de símbolo, a < 30 pt de la columna.
2. Exactamente un vértice abajo → `y_nivel = y` de la punta → profundidad con la regresión de la
   columna ([02 §3](02_bohrprofil_generalizacion.md#3-escala-vertical-por-regresión)).
3. Texto a < 14 pt: fecha `dd.mm.yy(yy)` y, si hay, profundidad rotulada → debe coincidir
   (±5 cm) con la geométrica; si no, issue.
4. `NHN = GOK − Tiefe` como comprobación.

## 3. Palabras clave (alemán)

Base: la lista `groundwater_keys.de` de swissgeol (`Grundwasserspiegel`, `GW`, `GWSP`, `Wsp`,
`GW-Spiegel`, `Grundwasser`, …) y sus falsos positivos (`Grundwasserfassung`, `GW/`). Añadir para
Alemania: `GW angetroffen`, `Ruhewasserspiegel`, `Wasserstand nach Bohrende`, `GW-Stand`,
`HGW`, `MGW`, `Bemessungswasserstand`, `Schichtenwasser`; unidades `m u. GOK`, `m NHN`, `m NN`,
`mNN` (swissgeol trae unidades suizas como `m ü. M.`).

## 4. Modelo de datos e IFC

Tabla `groundwater_obs` de la [arquitectura §5.2](ARQUITECTURA_BAUGRUNDMODELL.md#52-esquema-supabase-borrador-de-migración)
con `kind` ∈ {angetroffen, ruhe, nach_bohrende, bemessung, hgw, mgw}, `depth`, `nhn`, `observed_on`,
procedencia. En IFC: `Pset_BoreholeCommon.GroundwaterDepth`; las líneas del Längsschnitt como
estrato `WATER` o superficie en el modelo.

Up: [Índice](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [03 Längsschnitt](03_laengsschnitt_generalizacion.md) · [08 swissgeol](08_swissgeol_reutilizacion.md)
