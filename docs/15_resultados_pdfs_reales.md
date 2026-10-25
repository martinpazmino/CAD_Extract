---
title: "Resultados con PDFs reales (ronda 1 y prueba ciega)"
date: 2026-10-25
tags: [corpus, validacion, resultados, extraccion]
aliases: [Resultados reales, Primera ronda corpus]
---

# Resultados con PDFs reales (ronda 1 y prueba ciega)

**Conclusión:**
- **v1 (actual):** 0 de 29 sondeos en cinco Gutachten públicos.
- **Ronda 1** (3 PDFs): v3 funciona después de siete cambios que los sintéticos no revelaban.
- **Prueba ciega** (2 PDFs nuevos, código congelado): **v3 sacó 0 de 13**. swissgeol sacó
  13/13 sondeos, pero ninguna cota y 18 sondeos inventados.

La lección es que la geometría da precisión y control de falsos positivos, mientras que la
tolerancia a formatos de texto desconocidos es el punto fuerte de swissgeol. **La solución es
combinar ambas** (§6). Tras corregir las causas generales, v3 llega a **29/29 sondeos y 143/143
límites**, incluido un PDF escaneado.

> [!WARNING]
> Las cifras **después** de cada corrección son de *entrenamiento*. La única cifra honesta de
> generalidad es la de la prueba ciega (§6.1): **0/13**. La próxima ronda debe volver a medirse
> sin tocar el código ([12](12_corpus_publico.md)).

## 1. Los documentos

| PDF | Oficina / software | Qué contiene | Particularidades |
|---|---|---|---|
| Wachenroth (B-Plan Angerleite, BY) | Geotechnik Prof. Dr. Gründer · PDF24/Ghostscript | 6 Bohrprofile (1 por página, M 1:25) + corte en altura (M 1:75) + leyenda DIN 4023 | Texto del informe **escaneado** (págs. 1–34 sin texto); dibujo en **965 segmentos sueltos sin rellenos**; etiquetas = **base** de capa |
| Talheim (Sickerwassertrasse, BW) | GeoTech Kaiser · Word + CAD | 8 BK + 2 GWM en **páginas giradas 90°**, eje mNN, Höhenmaßstab 1:75 | Etiquetas = **techo** con 0,00, **desplazadas** con líneas de referencia; bordes de columna por tramos; máscaras blancas detrás del texto; GW con línea hasta su columna |
| Halle (B-Plan 152, ST) | Word | Sólo texto del informe, **sin anexos** de Bohrprofile | Tabla de niveles freáticos (26 KRB), tablas de parámetros y Homogenbereiche |

Verdad de referencia transcrita a mano y revisada contra las imágenes:
[`spikes/korpus/groundtruth/`](../spikes/korpus/groundtruth/wachenroth.json) (sólo datos
factuales: códigos, cotas, profundidades, clase de suelo, agua; con URL y `sha256` del PDF).

## 2. Resultados de la ronda 1

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

## 6. Prueba ciega: Hausham y Rednitzhembach

### 6.1 Resultado ciego

Protocolo: predicciones congeladas con el código del commit `d35e3d4` **antes** de mirar los PDFs;
después, transcripción de la verdad y puntuación ([`blind_test.py`](../spikes/korpus/blind_test.py)).

| PDF | Qué es | v1 | **v3 (ciego)** | swissgeol (ciego) |
|---|---|---|---|---|
| Hausham (Frank + Bumiller + Kraft, **DC-Software**) | Vectorial, 3 B + 6 RKS, etiquetas `0.20m`, escala de RKS ajustada a la página | 0/9 | **0/9** | **9/9 · 45/45 límites · 4/4 GW**; GOK 0/9; **15 sondeos falsos** |
| Rednitzhembach (Prof. Dr. Gründer) | **Escaneado** con capa OCR, 4 B, M 1:50 | 0/4 | **0/4** | 4/4 · 6/15 límites; GOK 0/4; 3 falsos |

### 6.2 Por qué falló v3 y qué se cambió después

| # | Causa | Cambio (general, no específico del PDF) |
|---|---|---|
| L8 | Etiquetas con unidad pegada (`0.20m`); "Kein Wasser" | Patrón de etiqueta con unidad opcional; frases de "sin agua" ampliadas |
| L9 | DC-Software ajusta la escala del perfil a la hoja (M ≈ 1:35) | Se acepta una escala no normalizada si ≥ 80 % de ≥ 3 etiquetas la confirman (corrige L5) |
| L10 | Nivel freático como texto `GW 2.53m`; los ▽ de la regla de cotas y el ▼ de la cota de inicio parecían agua | GW también por texto; se descartan series de triángulos alineados, triángulos con una cota al lado y triángulos a profundidad 0 |
| L11 | **Escaneo** sin vectores | **Adaptador raster:** OpenCV detecta líneas horizontales y verticales en la imagen y las convierte en los mismos segmentos que usa la lógica vectorial; la profundidad sale de la escala del cajetín (`M 1:50`) cuando el OCR pierde etiquetas; las líneas duplicadas del escaneo se fusionan |
| L12 | El mismo sondeo en la hoja individual y en un corte | Preferir la hoja titulada `Bohrung B 4` y la hoja con un solo sondeo; una confirmación de etiquetas < 50 % no cuenta |

### 6.3 Acumulado de los cinco PDFs (después de las correcciones = entrenamiento)

| | v1 | v3 | swissgeol |
|---|---|---|---|
| Sondeos | 0/29 | **29/29** | 19/29 |
| Límites | 0/143 | **143/143** (+1 falso, marcado) | 69/143 |
| GOK | 0/27 | **27/27** | 6/27 |
| Nivel freático | 0/8 | **7/8** | 4/8 |
| Bodenart (capas con verdad) | — | **59/61** | (no clasifica) |
| Sondeos / GW falsos | 0 / 0 | **0 / 0** | **30 / 1** |

Los 5 límites de B4 (Rednitzhembach) salen sólo de la geometría y la escala, sin etiquetas
legibles, y quedan **marcados para revisión**. Ése es el comportamiento buscado.

### 6.4 Consecuencia para la arquitectura

1. **Combinar los dos enfoques:** la búsqueda de columnas de profundidad de swissgeol es
   tolerante a formatos (unidades, OCR, posiciones). La parte geométrica nuestra hace la
   validación: columna, escala, límites, cabecera y filtros de tablas y duplicados. Hay que
   portar y ampliar su catálogo de formatos de etiqueta ([08](08_swissgeol_reutilizacion.md)).
2. **Un solo núcleo, dos fuentes de segmentos:** vectorial (`get_drawings`) o raster (OpenCV).
   Los escaneos ya no son un caso aparte ([02](02_bohrprofil_generalizacion.md)).
3. **La prueba ciega forma parte del proceso:** cada ronda nueva se congela antes de mirar.

## 7. Próximos pasos

1. Tercera ronda ciega con Gutachten **nuevos** (GGU-STRATIG, WinBohr, otro escaneado), ahora
   con v3 + catálogo de formatos de swissgeol: medir antes de tocar.
2. Muestras de leyenda desde segmentos → Schraffur y símbolos de agua con datos reales.
3. Llevar las lecciones L1–L7 al plan de implementación ([10](10_plan_implementacion.md)).

Up: [Índice](README.md)

Related: [12 Corpus](12_corpus_publico.md) · [09 Validación](09_validacion_benchmark.md) · [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [08 swissgeol](08_swissgeol_reutilizacion.md) · [11 Decisiones](11_decisiones.md)
