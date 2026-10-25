---
title: "Bohrprofil: extracción independiente del layout"
date: 2026-10-23
tags: [geo_agent, extraccion, bohrprofil, generalizacion]
aliases: [Bohrprofil v2, Generalización Bohrprofil]
---

# Bohrprofil: extracción independiente del layout

**Idea central:** dejar de buscar los datos *en una posición* y buscarlos *por su relación*:
la columna es un apilamiento de rectángulos, las profundidades son números cuya posición `y`
correlaciona linealmente con su valor, y la descripción es el bloque de texto alineado a la
derecha de la columna. Así el mismo código sirve para cualquier oficina y escala.

**Estado:** probado en el prototipo
[`spikes/extraktion_v2/prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py) sobre los 6
layouts sintéticos (17 sondeos, 102 capas): **102/102 capas** con límite, Bodenart y texto
correctos, también en A3, A4 y B, donde v1 falla, y la contradicción deliberada de A5 se reporta
como issue ([01](01_diagnostico_layout_fijo.md)).

**Con PDFs reales** (Wachenroth, Talheim) hicieron falta siete cambios: geometría reducida a
segmentos, normalización de la rotación, escala elegida por confirmación de etiquetas, filtros de
tablas y escalas normalizadas, entre otros. El resultado es
[`prototyp_v3.py`](../spikes/extraktion_v2/prototyp_v3.py). En la **prueba ciega** con dos PDFs
nuevos v3 sacó **0/13**: etiquetas `0.20m`, escala ajustada a la hoja y un escaneo. Tras corregirlo
(incluido un adaptador raster que da los mismos segmentos desde la imagen) llega a **29/29 sondeos
y 143/143 límites** en los cinco PDFs reales, sin regresión en los sintéticos. Detalle y límites en
[15 Resultados reales](15_resultados_pdfs_reales.md). El método descrito abajo sigue siendo el
mismo; las variantes de v3 se indican con **(v3)**.

## Pipeline

```
words + drawings ─► 1 columnas ─► 2 cabecera (ID, GOK) ─► 3 escala y→Tiefe ─► límites
                                                               │
              4 bloque de descripción ◄──────────────────────────┘
                     │
              5 clasificación texto ─┐
              6 Schraffur (→ 04) ────┴► fusión + confianza + issues
```

## 1. Columnas por geometría

- Candidatos: paths cerrados con relleno, forma rectangular (`re` o 4 segmentos ortogonales),
  ancho 8–80 pt. Se agrupan por `(x0, x1)` con tolerancia 0,8 pt y se encadenan si
  `|y1_i − y0_{i+1}| ≤ 0,8 pt`. Una cadena de ≥ 2 rectángulos es una columna.
  (`find_columns` en el prototipo.)
- Las muestras de la leyenda no forman cadenas (hay huecos entre ellas) y los marcos de
  diagramas no tienen relleno: se excluyen solos.
- **(v3)** Más general: reducir todo (líneas, rectángulos, quads) a **segmentos**, unir los
  colineales, y definir la columna como **par de verticales con trazo** (8–80 pt, alto ≥ 2,5 ×
  ancho). Los límites son horizontales continuas que tocan **ambos** bordes (±0,6 pt), así que
  la Schraffur queda fuera. De los candidatos anidados se queda el de bordes más gruesos. Funciona
  igual con rectángulos (sintéticos), segmentos sueltos (Wachenroth) y bordes por tramos con
  máscaras blancas (Talheim).
- **Fallbacks** para planos donde la columna no está hecha de rectángulos:
  1. líneas horizontales que cruzan un mismo intervalo `x` (los límites de capa);
  2. raster: el detector de *strip logs* de swissgeol (`swissgeol_doc_processing/utils/strip_log_detection.py`)
     localiza columnas gráficas en imágenes → [08](08_swissgeol_reutilizacion.md).

## 2. Cabecera: nombre y GOK

- Nombre: la línea de texto más baja por encima de la columna (≤ 70 pt) que cumpla
  `^(B|BK|KB|RKS|BS|GWM)\s*\d+[a-z]?(/\d{2})?$`. Los prefijos válidos vienen del perfil.
- Las Sondierungen (`DPH`, `DPL`, `DS`, `CPT`, `SRS`) usan otra regex y otro extractor
  → [05](05_sondierungen.md). **Ojo:** swissgeol confunde aquí el nombre: en el layout B asigna a
  cada Bohrung el título del diagrama DPH vecino ([08](08_swissgeol_reutilizacion.md#4-prueba-swissgeol-sin-cambios-sobre-nuestros-pdfs)).
- GOK: `(?:NHN|NN)\s*±x,xx\s*m` o `±x,xx\s*m\s*(?:NHN|NN)` en la zona de cabecera
  (cubre `NHN+6,20m`, `Ansatzhöhe: 5.47 m NHN`, `GOK = 5,47 mNN`).

## 3. Escala vertical por regresión

1. Candidatos: números con decimales cerca de la columna (−120…+60 pt en `x`), excluyendo los
   que van entre paréntesis o con signo (son NHN, no profundidad).
2. Agrupar por columna de texto (borde derecho alineado) y, por grupo, exigir ≥ 3 valores,
   **estrictamente crecientes** y con **correlación de Pearson > 0,95** entre `y` y valor
   (exactamente el criterio de `AAboveBSidebarValidator` de swissgeol).
3. Ajuste `Tiefe = a·y + b`. De `a` sale la escala real: `M = a / 0,000352778` (1 pt = 0,3528 mm).
   El prototipo recupera **1:100 y 1:50** sin configuración; se contrasta con el texto `M 1:…`.
4. **(v3)** Con planos reales las etiquetas pueden estar **desplazadas** (líneas de referencia) y
   rotular el **techo** (con 0,00) o la **base**. Por eso v3 genera candidatos de escala:
   - directa, con la etiqueta sobre la línea;
   - por orden, con la k-ésima etiqueta en el k-ésimo límite;
   - el texto `M 1:xx` / `Höhenmaßstab 1 : 75`.

   Se elige el candidato con más **etiquetas confirmadas** por algún límite (±3 cm) y sólo se
   aceptan **escalas normalizadas** (±4 %). La confirmación etiqueta↔límite es 1:1.
5. Robustez adicional de swissgeol que conviene portar:
   - quitar iterativamente la entrada que más empeora el ajuste (`remove_entry_by_correlation_gradient`);
   - descartar **reglas/escalas** (`0, 1, 2, 3 m…`): progresiones aritméticas que contienen 0
     (`_arithmetic_progression_entries`);
   - corregir errores OCR de punto decimal (`fix_ocr_mistakes`), sólo relevante con escaneos.

## 4. Límites y descripción

- **Los límites salen de la geometría** (borde inferior de cada rectángulo) y se convierten con
  la regresión; la etiqueta más cercana (< 6 pt) **confirma** el valor (|Δ| ≤ 2 cm). Límite sin
  etiqueta → issue; etiqueta sin límite → issue.
- Comprobación NHN: si hay valores NHN (paréntesis o con signo) junto al límite,
  `GOK − Tiefe = NHN` (ya existe en v1, `geo_agent/bohrprofil.py:203`).
- **Bloque de descripción:** líneas de texto (no numéricas, sin fecha) a la derecha de la
  columna y antes de la columna siguiente; el borde izquierdo es la moda de `x0` (texto alineado
  a la izquierda). Cada línea se asigna a la capa cuyo intervalo `[y0, y1)` contiene su `y0`.
  Esto resuelve A3 (texto más cerca) y B (texto más lejos).
- **Capas delgadas con líneas de referencia** (texto desplazado con una diagonal hacia su capa):
  swissgeol ya lo resuelve con `get_diagonals_near_textlines` + `compute_entries_shift`
  (desplaza la zona de la etiqueta según la diagonal) y un emparejamiento por **programación
  dinámica** (`depth_description_alignment.py`). No está en el prototipo; portar.

## 5. Clasificación del texto: sustantivo, no adjetivo

El fallo silencioso de A3 viene de `soil.classify` buscando subcadenas: `sandig` → *Sand*.
Regla DIN 4023 / EN ISO 14688: la **fracción principal es un sustantivo** (mayúscula:
*Sand, Kies, Mittelsand, Geschiebemergel*); las secundarias son adjetivos en `-ig`
(*sandig, kiesig, schluffig*). Cambios:

- La palabra cabeza debe ser sustantivo (mayúscula inicial, no termina en `-ig`/`-haltig`).
- Si la primera palabra no es sustantivo → **issue**, nunca "continuación de la capa anterior"
  (`geo_agent/bohrprofil.py:186-190`).
- El vocabulario regional (Lauenburger Ton, Klei…) se carga de la leyenda o del perfil, no del
  código.
- Parseo completo de Nebenanteile, consistencia, etc.: ver
  [arquitectura §6.5](ARQUITECTURA_BAUGRUNDMODELL.md#65-parser-de-descripciones-din-4023--din-en-iso-14688-1).

## 6. Fusión y confianza

Cada capa reúne señales independientes; la confianza es el acuerdo entre ellas
(`Layer.confidence` en el prototipo):

| Señal | Peso orientativo |
|---|---|
| Límite geométrico confirmado por etiqueta | 0,4 (0,2 sin etiqueta) |
| Bodenart por texto (sustantivo reconocido) | +0,3 |
| Bodenart por Schraffur coincide con texto ([04](04_schraffur_din4023.md)) | +0,3 |

Verde/amarillo en el Excel se deriva de este valor. Los pesos se calibran con el corpus real.

## 7. Qué queda como configuración (perfil)

Sólo pistas, nunca posiciones: prefijos de ID, regex de profundidad/NHN, idioma, vocabulario
regional, escala esperada. Ver formato en
[arquitectura §6.10](ARQUITECTURA_BAUGRUNDMODELL.md#610-perfiles-de-layout).

## 8. Casos aún no cubiertos

- Páginas rotadas (`/Rotate`) y texto vertical → normalizar con `page.rotation_matrix` **[a verificar]**.
- Sondeos que continúan en la página siguiente → swissgeol `layer/continuation_detection.py`.
- PDFs escaneados → OCR previo (swissgeol usa AWS Textract + `swissgeol-ocr`); confianza menor.
- Varias columnas por sondeo (p. ej. Stratigraphie + Bodenart): elegir la que tiene Schraffur.

Up: [Índice](README.md)

Related: [01 Diagnóstico](01_diagnostico_layout_fijo.md) · [04 Schraffur](04_schraffur_din4023.md) · [08 swissgeol](08_swissgeol_reutilizacion.md) · [09 Validación](09_validacion_benchmark.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md)
