---
title: "Resultados con PDFs reales (primera ronda)"
date: 2026-10-25
tags: [corpus, validacion, resultados, extraccion]
aliases: [Resultados reales, Primera ronda corpus]
---

# Resultados con PDFs reales (primera ronda)

**Conclusión:** con los tres primeros Gutachten públicos el parser actual (v1) extrae **0 de 16**
sondeos. El enfoque geométrico funciona con planos reales, pero sólo después de siete cambios
que los PDFs sintéticos no habían revelado. Con esos cambios (prototipo **v3**) se obtienen
**16/16 sondeos, 83/83 límites, 14/14 GOK, 3/4 niveles freáticos** y **0 sondeos falsos**.

> [!WARNING]
> v3 se ajustó mirando estos mismos PDFs (son el conjunto de *entrenamiento*). Las cifras
> demuestran que el método es capaz, no que generalice. La prueba honesta es la siguiente
> ronda con Gutachten **no vistos** ([12](12_corpus_publico.md)).

## 1. Los documentos

| PDF | Oficina / software | Qué contiene | Particularidades |
|---|---|---|---|
| Wachenroth (B-Plan Angerleite, BY) | Geotechnik Prof. Dr. Gründer · PDF24/Ghostscript | 6 Bohrprofile (1 por página, M 1:25) + corte en altura (M 1:75) + leyenda DIN 4023 | Texto del informe **escaneado** (págs. 1–34 sin texto); dibujo en **965 segmentos sueltos sin rellenos**; etiquetas = **base** de capa |
| Talheim (Sickerwassertrasse, BW) | GeoTech Kaiser · Word + CAD | 8 BK + 2 GWM en **páginas giradas 90°**, eje mNN, Höhenmaßstab 1:75 | Etiquetas = **techo** con 0,00, **desplazadas** con líneas de referencia; bordes de columna por tramos; máscaras blancas detrás del texto; GW con línea hasta su columna |
| Halle (B-Plan 152, ST) | Word | Sólo texto del informe, **sin anexos** de Bohrprofile | Tabla de niveles freáticos (26 KRB), tablas de parámetros y Homogenbereiche |

Verdad de referencia transcrita a mano y revisada contra las imágenes:
[`spikes/korpus/groundtruth/`](../spikes/korpus/groundtruth/wachenroth.json) (sólo datos
factuales: códigos, cotas, profundidades, clase de suelo, agua; con URL y `sha256` del PDF).

## 2. Resultados

Tolerancia de límites 5 cm (a M 1:75, 1 pt = 2,6 cm); emparejamiento 1:1.
Reproducir: `python spikes/korpus/eval_real.py <pdfs> [<salida swissgeol>]`.

| | v1 actual | **v3 prototipo** | swissgeol (sin cambios) |
|---|---|---|---|
| **Wachenroth** sondeos / límites | 0/6 · 0/18 | **6/6 · 18/18** | 6/6 · 18/18 |
| Bodenart | — | **18/18** (incl. *Sandstein* = roca) | (no clasifica) |
| GOK | 0/6 | **6/6** | 6/6 |
| Falsos (sondeos / GW) | 0 / 0 | **0 / 0**; duplicados del corte fusionados | **5 / 1** (corte duplicado, informe de laboratorio) |
| **Talheim** sondeos / límites | 0/10 · 0/65 | **10/10 · 65/65** (+1 límite falso, marcado) | 0/10 · 0/65 |
| GOK / GW | 0/8 · 0/4 | **8/8 · 3/4** | 0/8 · 0/4 |
| Falsos sondeos | 0 | **0** | 3 (desde el texto del informe) |
| **Halle** (no tiene perfiles) | 0 falsos | **0 falsos** | **4 falsos** (desde tablas) |
| Tabla de GW de Halle | — | **26/26** (lectura por celda) | — |

## 3. Siete lecciones de los planos reales

| # | Qué pasó | Cambio en v3 | Nota afectada |
|---|---|---|---|
| L1 | El PDF regenerado con Ghostscript/PDF24 no tiene rectángulos ni rellenos: sólo segmentos | **Todo a segmentos**; columna = par de verticales con trazo; límites = horizontales que tocan ambos bordes | [02](02_bohrprofil_generalizacion.md) |
| L2 | Página con `/Rotate 90`: PyMuPDF da coordenadas sin rotar | Normalizar palabras y paths con `page.rotation_matrix` | [02 §8](02_bohrprofil_generalizacion.md#8-casos-aún-no-cubiertos) |
| L3 | Etiquetas desplazadas con líneas de referencia; unas oficinas rotulan el **techo** (con 0,00), otras la **base** | Escala por candidatos (directa, por orden, texto `1 : 75`) y se elige la que **más etiquetas confirma**; la convención decide cómo asignar las descripciones | [02 §3](02_bohrprofil_generalizacion.md#3-escala-vertical-por-regresión) |
| L4 | En la representación en altura la cabecera está muy por encima de la columna | Asociar la cabecera con la columna de debajo sin límite vertical | [03](03_laengsschnitt_generalizacion.md) |
| L5 | Tablas con "B 6" y números crecientes parecían un sondeo (M 1:12) | Escalas normalizadas (±4 %), columna con números dentro = tabla, duplicados → versión con GOK y más etiquetas confirmadas | [09](09_validacion_benchmark.md) |
| L6 | La Schraffur de *Ton* (rayas) y de *Schwarzdecke* (dos líneas) cruzan la columna como si fueran límites | Excluir líneas discontinuas y exigir que el límite toque los bordes; confirmación etiqueta↔límite **1:1**, para que un límite extra quede marcado | [04](04_schraffur_din4023.md) |
| L7 | v1 clasifica `Sandstein` → *Sand*, `Tonstein` → *Steine*, `Beton` → *Ton*, todos "seguros" | Sustantivo principal + lista de roca (`-stein`) y antrópicos (Beton, Schwarzdecke, Anschüttung → Auffüllung), Oberboden = Mutterboden | [01](01_diagnostico_layout_fijo.md), [02 §5](02_bohrprofil_generalizacion.md#5-clasificación-del-texto-sustantivo-no-adjetivo) |

Además, el nivel freático real confirma dos detalles: el triángulo puede estar junto a la
columna **vecina** y lo que asigna el sondeo es el extremo de la **línea de agua**; y
"kein Grundwasser" es un dato que hay que guardar (6/6 en Wachenroth), no una ausencia.

## 4. Lo que todavía falla o no se probó

- **GW "angebohrt" de BK2 (Talheim)**: es otro símbolo (dos trazos + línea). Falta leer los
  símbolos de agua desde la leyenda del documento ([06](06_grundwasser.md)).
- **1 límite falso** (doble línea de *Schwarzdecke* en BK5): queda marcado como no confirmado.
  Mejor solución: reconocer esa Schraffur por la leyenda.
- **Clasificación por Schraffur no evaluada con planos reales**: las muestras de leyenda de
  Wachenroth son cuadrados de líneas sueltas y las de Talheim combinan color y letra; el detector
  de muestras del prototipo sólo acepta rectángulos rellenos ([04](04_schraffur_din4023.md)).
- **Coordenadas**: ninguno de los tres trae una tabla de coordenadas. Los Lagepläne mezclan
  raster y vector ([07](07_coordenadas.md)).
- **Texto escaneado** (Wachenroth, págs. 1–34): requiere OCR para los Homogenbereiche y
  parámetros del informe.
- **Descripciones completas** (Nebenanteile, consistencia): sólo se evaluó la clase principal.
- **Sondierungen**: ninguno de los tres trae curvas DPH vectoriales.

## 5. Próximos pasos

1. Segunda ronda con 5–7 Gutachten **nuevos** (otro software: GGU-STRATIG, DC-BOHR, WinBohr),
   sin tocar v3 antes de medir: esa es la cifra real de generalidad.
2. Muestras de leyenda desde segmentos → Schraffur y símbolos de agua con datos reales.
3. Llevar las lecciones L1–L7 al plan de implementación ([10](10_plan_implementacion.md)).

Up: [Índice](README.md)

Related: [12 Corpus](12_corpus_publico.md) · [09 Validación](09_validacion_benchmark.md) · [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [08 swissgeol](08_swissgeol_reutilizacion.md) · [11 Decisiones](11_decisiones.md)
