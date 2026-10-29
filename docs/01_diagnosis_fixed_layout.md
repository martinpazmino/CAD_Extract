---
title: "Diagnóstico: supuestos de layout fijos en geo_agent"
date: 2026-10-23
tags: [geo_agent, extraccion, diagnostico, generalizacion]
aliases: [Supuestos fijos, Diagnóstico layout]
---

# Diagnóstico: supuestos de layout fijos en geo_agent

**Conclusión:** la extracción actual (v1) es exacta con el plano para el que se escribió, pero
depende de **posiciones, colores y formatos fijos**. Con otra oficina, otra escala o
simplemente el texto unos puntos más cerca de la columna, falla de forma total o, peor,
**silenciosa** (valores incorrectos marcados en verde). Además descarta datos útiles: la
Schraffur, las Sondierungen, el nivel freático y las coordenadas.

## 1. Evidencia medida (PDFs sintéticos)

Generador y scripts: [`spikes/extraktion_v2/`](../spikes/extraktion_v2/README.md). Seis
layouts DIN 4023 simplificados con verdad conocida (18 capas en A–A5, 12 en B):

| Layout | Qué cambia respecto a A | v1: sondeos | v1: límites | v1: Bodenart correcta | v1: texto correcto |
|---|---|---|---|---|---|
| A | referencia (M 1:100, `B n/jj`, pares `(NHN) Tiefe` a la izquierda) | 3/3 | 18/18 | 18/18 | 18/18 |
| A2 | M 1:50, columna más ancha | 3/3 | 18/18 | 18/18 | 18/18 |
| A3 | la descripción empieza **10 pt más cerca** de la columna | 3/3 | 18/18 | **6/18** | **0/18** |
| A4 | nombre centrado sobre la columna, etiquetas 20 pt más a la izquierda | **0/3** | 0/18 | 0/18 | 0/18 |
| A5 | como A, pero una capa con texto *Sand* y Schraffur de *Kies* (error de dibujo) | 3/3 | 18/18 | 18/18 | 18/18 — **la contradicción no se detecta** |
| B | otra oficina: `BK n`, profundidades a la derecha, punto decimal, GOK en cabecera, DPH | **0/2** | 0/12 | 0/12 | 0/12 |

En A3, de las 12 Bodenarten incorrectas **7 salen marcadas como seguras (verde)**: por
ejemplo `Kies, sandig, …` pierde la primera palabra (queda fuera de la banda `x_label+58`),
`sandig` contiene `sand` y se clasifica como *Sand* con certeza. Ese es el peor modo de fallo:
el Excel parece correcto.

### Con PDFs reales

En los tres primeros Gutachten públicos v1 extrae **0 de 16 sondeos** (no reconoce `B 1`,
`BK1`, `GWM1` sin año, ni esos layouts). Además, con textos reales `soil.classify` da como
**seguros** `Sandstein` → *Sand*, `Tonstein` → *Steine* y `Beton` → *Ton*
([15](15_resultados_pdfs_reales.md)).

## 2. Inventario de supuestos fijos

Modo de fallo: **T** = total (no se extrae nada, visible) · **S** = silencioso (dato erróneo
con aspecto válido) · **P** = pérdida de información.

### Bohrprofil (`geo_agent/bohrprofil.py`, `legend.py`, `soil.py`)

| # | Dónde | Supuesto | Fallo | Solución |
|---|---|---|---|---|
| 1 | `geo_agent/bohrprofil.py:26-29` | Bandas fijas relativas al token `B`: profundidades `−65…+8`, texto `+58…siguiente−25` | T (A4), S (A3) | Columna por geometría + escala por regresión → [02](02_bohrprofil_generalizacion.md) |
| 2 | `geo_agent/bohrprofil.py:31-32` | ID = `B` + `nn/jj`; prefijos fijos | T (B: `BK 1`, `KB3`, `B1`) | Regex genérica + perfil → [02](02_bohrprofil_generalizacion.md#2-cabecera-nombre-y-gok) |
| 3 | `geo_agent/bohrprofil.py:33` | GOK = token único `NHN±x,xx m` dentro de la banda de profundidades | P/S | Regex en la cabecera (`Ansatzhöhe`, `GOK`, `m NN`) |
| 4 | `geo_agent/bohrprofil.py:34` | Pares `(NHN) Tiefe` en ese orden, NHN sin `+` | T (profundidades a la derecha, sin NHN) | Columna numérica validada por correlación → [02](02_bohrprofil_generalizacion.md#3-escala-vertical-por-regresión) |
| 5 | `geo_agent/bohrprofil.py:80-83` | Una sola fila de cabeceras por página (la que tiene más IDs) | T (sondeos en dos filas) | Detección por columna, no por fila |
| 6 | `geo_agent/bohrprofil.py:151`, `:181` | Agrupar filas con `round(y/4)` | S con otro tamaño de fuente | Líneas de texto de PyMuPDF (`block_no`, `line_no`) |
| 7 | `geo_agent/bohrprofil.py:13` | Columna gráfica ignorada | P | Clasificador de Schraffur → [04](04_schraffur_din4023.md) |
| 8 | `geo_agent/bohrprofil.py:32` + README | `DS`, `GWM` excluidos; "CPT-/Sonden-Spalten bewusst weggelassen" | P | → [05](05_sondierungen.md) |
| 9 | — | Nivel freático no se extrae | P | → [06](06_grundwasser.md) |
| 10 | `geo_agent/bohrprofil.py:186-190` | Si un segmento no tiene Bodenart segura, se asume "continuación de la capa anterior" | S | Tratar como issue de revisión, no como dato |
| 11 | `geo_agent/soil.py:22`, `:51` | Reglas por subcadena (`"sand" in palabra`) → adjetivos (`sandig`, `tonig`) cuentan como Bodenart, y rocas/antrópicos también (`Sandstein` → Sand, `Beton` → Ton, verificado con PDFs reales); vocabulario regional (Lauenburger Ton, Glimmerton, Klei) | S | Gramática: sustantivo principal vs. adjetivo `-ig` → [02](02_bohrprofil_generalizacion.md#5-clasificación-del-texto-sustantivo-no-adjetivo) |
| 12 | `geo_agent/legend.py:73-75` | La leyenda sólo se reconoce si contiene secciones DIN (`KORNGR…`, `KONSISTENZ`…) | T (sin vocabulario) | Buscar `ZEICHENERKLÄRUNG`/`LEGENDE`/`BODENARTEN` y muestras de Schraffur |
| 13 | `geo_agent/legend.py:88-90`, `:102` | Ventana `y` y corte de columna `ax+85` fijos | S | Filas = muestra (rectángulo) + texto a su derecha |

### Längsschnitt (`geo_agent/laengsschnitt.py`)

| # | Dónde | Supuesto | Fallo | Solución |
|---|---|---|---|---|
| 14 | `:104-105` | Estación `^(\d)\+(\d{3})\.000$` en `y≈1137` | T | Regex con variantes + agrupación por fila → [03](03_laengsschnitt_generalizacion.md) |
| 15 | `:110`, `:428` | Eje NHN en `290<x<360`, formato `-?\d+\.\d{2}` | T | Columna numérica equiespaciada + correlación |
| 16 | `:28-33`, `:38` | 5 colores de geología fijos, tolerancia 40 | S/T | Colores leídos de la leyenda del Längsschnitt o capas OCG |
| 17 | `:35` | Túnel = relleno gris `RGB 0.73` | T | Capa OCG, geometría de banda o un clic del usuario |
| 18 | `:200`, `:238-239` | Sólo `doc[0]`; región vertical `160…1130 pt` | T | Todas las páginas; región = marco del dibujo |
| 19 | `:177`, `:180` | Sondeos en `y<360`, `B` a < 25 pt del número | T | Detector de mini-columnas reutilizado de [02](02_bohrprofil_generalizacion.md) |
| 20 | `:242`, `:286` | GOK del terreno = primer "run" de 6 px de color geológico | S | Polilínea del terreno (capa/estilo propio) |
| 21 | `:37`, `:139` | Raster de toda la página a zoom 2 (~20 s) | rendimiento | Polígonos vectoriales + caché |
| 22 | `:419` | Caché global `_NHN_FIT` por `id(page)` | S (ids reutilizados entre documentos) | Pasar la regresión como parámetro |

### Salida (`geo_agent/excel_writer.py`)

| # | Dónde | Supuesto | Fallo | Solución |
|---|---|---|---|---|
| 23 | `:145-147` | Rechts-/Hochwert siempre vacíos | P | → [07](07_coordenadas.md) |

## 3. Lectura

- Los supuestos 1, 4, 14 y 15 son el mismo error de diseño: **posición absoluta en lugar de
  relación estadística**. La técnica correcta ya existe en el propio código (regresión de ejes en
  el Längsschnitt) y en swissgeol (validación de columnas de profundidad por correlación) →
  [08](08_swissgeol_reutilizacion.md).
- Los supuestos 10 y 11 convierten un fallo de extracción en un dato "seguro": hay que medir la
  **tasa de error silencioso** como KPI principal → [09](09_validacion_benchmark.md).
- Las pérdidas (7, 8, 9, 23) se recuperan con detectores geométricos específicos, todos
  probados en el spike.

Up: [Índice](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [03 Längsschnitt](03_laengsschnitt_generalizacion.md) · [09 Validación](09_validacion_benchmark.md) · [11 Decisiones](11_decisiones.md)
