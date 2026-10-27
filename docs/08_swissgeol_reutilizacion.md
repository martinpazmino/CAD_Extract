---
title: "swissgeol: qué hace, qué probamos y cómo reutilizarlo"
date: 2026-10-23
tags: [swissgeol, reutilizacion, extraccion, licencias]
aliases: [swissgeol, swissgeol-boreholes-dataextraction]
---

# swissgeol: qué hace, qué probamos y cómo reutilizarlo

**Conclusión:** `swissgeol-boreholes-dataextraction` (swisstopo) resuelve muy bien la parte
**textual y estadística** de la estratigrafía —columnas de profundidad, bloques de descripción,
emparejamiento— y es robusto al layout: sin cambios acertó 18/18 capas en nuestros layouts
A, A2 y A3. No cubre lo **específico de Alemania y de planos CAD** (Schraffur, símbolo DIN de
agua, CRS alemanes, Längsschnitt, túnel) y su asignación de nombres falla con diagramas
vecinos. Recomendación: **portar sus algoritmos y su formato de evaluación**, usarlo como
**segunda opinión** en el benchmark y **proponer contribuciones** upstream; no hacer fork ni
dependencia del núcleo.

## 1. Ficha

| | |
|---|---|
| Repo | <https://github.com/swisstopo/swissgeol-boreholes-dataextraction> (commit revisado `776ea39`, 2026-10-23) |
| Licencia | **AGPL-3.0-only** (por PyMuPDF; dicen que cambiarían si quitan esa dependencia) |
| Versión | v1.1.0 (2026-05-04), estado beta |
| Stack | Python 3.11–3.13, PyMuPDF **1.26.3** (fijado), OpenCV contrib, scikit-learn/-image, FastAPI, AWS (Textract, Bedrock), MLflow |
| Paquetes | `swissgeol_doc_processing` (geometría, texto, tablas, strip logs) y `extraction` (pipeline), instalables desde GitHub |
| CLI | `boreholes-extract-all`, `boreholes-extract-metadata`, `boreholes-score`, `boreholes-classify-descriptions` |
| Entrada | PDFs con texto (escaneos con OCR previo: AWS Textract + `swissgeol-ocr`) |
| Salida | `predictions.json` (sondeos → metadatos, capas con profundidades y bbox, agua) |
| Clasificación | BERT por propiedad (litología, USCS, color, componentes…) publicados en HuggingFace `swissgeol/*`; alternativa con Claude vía AWS Bedrock |

## 2. Mapa de módulos y relevancia para nosotros

| Módulo | Qué hace | Relevancia | Cómo usarlo |
|---|---|---|---|
| `extraction/features/stratigraphy/sidebar/*` | Tipos de columna de profundidad: **AAboveB** (`0.30` / `2.70` apilados = nuestro caso), AToB (`0.30–2.70`), LayerIdentifier (`a)`, `1)`), Protocol, Spülprobe | **Alta** | Portar AAboveB + su validador |
| `…/sidebar/utils/a_above_b_sidebar_validator.py` | ≥ 3 entradas, estrictamente crecientes, **Pearson > 0,95**, límite de "ruido" | **Alta** | Criterio adoptado en [02 §3](02_bohrprofil_generalizacion.md#3-escala-vertical-por-regresión) |
| `…/sidebar/extractor/a_above_b_sidebar_extractor.py` | Agrupa números en columnas, **excluye reglas** (progresiones aritméticas con 0), corrige OCR | **Alta** | Portar |
| `extraction/features/extract.py` (`BoreholeExtractor`) | Candidatos de descripción por columna, puntuación geométrica (`score_match`), emparejamiento voraz sin solapes, diagonales de referencia | **Alta** | Portar ideas: puntuación + diagonales |
| `…/stratigraphy/depth_description_alignment.py` | Emparejamiento líneas ↔ intervalos por **programación dinámica** | Media-alta | Portar para capas delgadas |
| `…/layer/continuation_detection.py` | Sondeo que sigue en la página siguiente | Media | Portar |
| `extraction/features/groundwater/*` | Palabras clave, símbolo suizo (dos líneas), texto en color minoritario | Media | Reusar listas y heurística de color; símbolo DIN propio ([06](06_grundwasser.md)) |
| `extraction/features/metadata/*` | Nombre, cota, coordenadas cerca de palabras clave | Media | Estructura sí; validadores CRS alemanes propios ([07](07_coordenadas.md)) |
| `swissgeol_doc_processing/geometry/line_detection.py` | Líneas por **Fast Line Detector sobre raster** | Baja para CAD vectorial | Para escaneos; en CAD usar `get_drawings()` |
| `swissgeol_doc_processing/utils/strip_log_detection.py` | Localiza columnas gráficas en raster (morfología, Hough, FLD) | Media (fallback) | Localizar columnas en escaneos; no clasifica patrones ([04](04_schraffur_din4023.md)) |
| `swissgeol_doc_processing/config/matching_params.yml` | Palabras de descripción, de agua, de coordenadas, pesos | Media | Partir de sus listas `de` y ampliar |
| `extraction/evaluation/*`, `docs/groundtruth-json.md` | Ground truth por PDF, métricas por capa/intervalo/descripción/metadatos/agua, benchmark multi-dataset | **Alta** | Adoptar el formato ([09](09_validacion_benchmark.md)) |
| `classification/*` | Clasificadores de descripciones (BERT suizo, Bedrock) | Baja-media | Sistemas suizos (USCS, EN main); referencia de diseño para nuestro parser DIN |
| `app/*` + `Dockerfile` | API FastAPI (`extract_data`, `extract_stratigraphy`, …) | Media | Correr como servicio "oráculo" en el benchmark |

## 3. Diferencias de base

| | swissgeol | Geo_Agent |
|---|---|---|
| Documentos | Perfiles suizos heterogéneos, muchos **escaneados** | Planos **CAD vectoriales** alemanes DIN 4023 + Längsschnitt de túnel |
| Líneas | Raster + FLD | Vectores exactos (`get_drawings`) |
| Señal principal | Texto | Texto **+ geometría** (Schraffur, símbolos, curvas) |
| CRS / alturas | LV95, LV03, `m ü. M.` | UTM 32/33, Gauß-Krüger, `m NHN` |
| Clasificación | USCS, EN, litología suiza | DIN 4023 / EN ISO 14688, vocabulario de la leyenda |
| Alcance | Sondeos | Sondeos + Sondierungen + sección + túnel + modelo 3D |

## 4. Prueba: swissgeol sin cambios sobre nuestros PDFs

Instalado en un entorno aislado y ejecutado con `boreholes-extract-all` sobre 5 de los layouts
sintéticos (A–A4 y B; A5 sólo difiere en la Schraffur, que swissgeol no lee) de [`spikes/extraktion_v2`](../spikes/extraktion_v2/README.md); evaluado con la misma
métrica que v1 y v2 (`score_swissgeol.py`):

| Layout | Sondeos | Límites | Bodenart (texto) | Agua | Cota | Coordenadas |
|---|---|---|---|---|---|---|
| A | 3/3 | 18/18 | 18/18 | 0/3 | 0/3 | 0/3 |
| A2 | 3/3 | 18/18 | 18/18 | 0/3 | 0/3 | 0/3 |
| A3 | 3/3 | 18/18 | 18/18 | 0/3 | 0/3 | 0/3 |
| A4 | 3/3 | 12/18 | 12/18 | 0/3 | 0/3 | 0/3 |
| B | 0/2 correctos* | 0/12* | 0/12* | 0/2 | 0/2 | 0/2 |

\* En B las capas y profundidades de ambos sondeos salen **correctas**, pero cada sondeo recibe
el nombre del diagrama vecino (`DPH 1`, `DPH 2`) en vez de `BK 1`/`BK 2`, y el único registro
llamado `BK 2` es un sondeo falso construido con la leyenda (3 capas sin profundidad). Con métrica
por nombre cuenta como fallo, y en producción también lo sería (datos en el sondeo equivocado).

Además, en **todos** los layouts la página de leyenda produce capas falsas: en A/A2/A3 se
"continúa" el tercer sondeo en la página 2 (9 capas en vez de 6) y en A4/B aparece un sondeo
extra sólo con entradas de la leyenda. Nuestra métrica (recall por profundidad) no penaliza esas
capas sobrantes; una métrica de precisión sí lo haría.

Lecturas:
- Su detección de columna de profundidad y de bloques de descripción **es independiente del
  layout**: confirma que el enfoque estadístico de [02](02_bohrprofil_generalizacion.md) es el
  correcto.
- Lo que falla es todo lo que depende de convenciones nacionales o de entender el dibujo:
  símbolo de agua, `NHN`, CRS, asociación nombre ↔ columna cuando hay diagramas, y distinguir
  una leyenda de un sondeo.
- Nuestro prototipo v2 acierta además Schraffur, agua, GOK, coordenadas y DPH en los mismos PDFs
  ([09](09_validacion_benchmark.md)).

### Con PDFs reales

Detalle en [15](15_resultados_pdfs_reales.md):
- **Wachenroth**: 6/6 sondeos, 18/18 límites y 6/6 cotas en las páginas individuales, pero
  **5 sondeos falsos** (el corte en altura repetido y un informe de laboratorio) y 1 nivel
  freático falso.
- **Talheim** (páginas giradas, representación en altura): 0/10.
- **Halle** (sin perfiles): **4 sondeos falsos** sacados de tablas.

Confirma la lectura de arriba: su núcleo encuentra bien profundidades y descripciones, pero
falta saber qué es un sondeo y qué no.

**Prueba ciega** (Hausham con DC-Software y Rednitzhembach escaneado,
[15 §6](15_resultados_pdfs_reales.md#6-prueba-ciega-hausham-y-rednitzhembach)):
- swissgeol sacó **13/13 sondeos** y 4/4 niveles freáticos, y nuestro v3 **0/13**: su lectura de
  etiquetas tolera formatos que no conocía (`0.20m`, OCR).
- Pero dio 0/13 cotas e inventó 18 sondeos (las páginas de texto del registro de capas parecían
  perfiles).

Esto refuerza la estrategia A: **portar su catálogo de formatos de etiqueta y su tolerancia al
OCR**, y mantener nuestra validación geométrica (D26).

## 5. Estrategias de reutilización

| Estrategia | Pros | Contras | Uso recomendado |
|---|---|---|---|
| **A. Portar algoritmos** (reimplementar ideas en `geo_agent`) | Control total, sin acoplamiento a una API beta, sin arrastrar AGPL si algún día se compra licencia comercial de PyMuPDF | Trabajo de reimplementación | **Núcleo**: AAboveB + validador, exclusión de reglas, puntuación de candidatos, diagonales, DP, continuación |
| **B. Dependencia directa** (`pip install` de su wheel, llamar `AAboveBSidebarExtractor` etc.) | Rápido | API interna inestable, fija PyMuPDF 1.26.3 (nosotros 2.x), arrastra OpenCV/scikit/AWS | Sólo en scripts de evaluación |
| **C. Servicio oráculo** (su API Docker) | Segunda opinión independiente; detecta regresiones nuestras | Otro servicio que operar | **Benchmark** y casos de baja confianza |
| **D. Contribuir upstream** | Mejoras compartidas; swisstopo invita a colaborar | Coordinación, su roadmap manda | Adaptador de líneas vectoriales, CRS alemanes, símbolo DIN, clasificador de Schraffur |
| E. Fork | — | Mantener un fork de un proyecto vivo | **No** |

### Licencia (decisión importante)

- swissgeol es **AGPL-3.0-only**. Copiar su código hace que esa parte de Geo_Agent sea AGPL.
- Geo_Agent usa PyMuPDF (también AGPL o comercial): hoy, para uso **interno**, no cambia nada.
- Si se ofrece como servicio a terceros o se compra la licencia comercial de PyMuPDF para cerrar el
  código, el código copiado de swissgeol **seguiría siendo AGPL**. Por eso: **portar ideas
  (A)**, citar la fuente en comentarios y, si se copia algo literal, aislarlo en un módulo marcado
  como AGPL.

## 6. Adaptador propuesto: líneas vectoriales para su pipeline

Su `Line(start: Point, end: Point)` (`swissgeol_doc_processing/geometry/geometry_dataclasses.py`)
se alimenta hoy desde el raster (`detect_lines_fld`). Para CAD vectorial basta convertir los
segmentos `l` de `page.get_drawings()` a `Line` y pasarlos como `LineDetectionResult`: líneas
exactas, sin renderizar. Es la contribución upstream más pequeña y útil para ambos.

## 7. Plan concreto

1. Portar AAboveB + validador + exclusión de reglas a `geo_agent/bohrprofil/scale.py` (con test).
2. Portar puntuación de candidatos de descripción y diagonales → capas delgadas.
3. Adoptar su formato `ground_truth.json` (+ extensiones) y sus métricas → [09](09_validacion_benchmark.md).
4. Correr swissgeol como oráculo en el benchmark (Docker o venv aislado).
5. Reusar listas de palabras clave (`matching_params.yml`, `de`) para agua, coordenadas y cota.
6. Contactar a swisstopo: adaptador vectorial, CRS alemanes, símbolo DIN de agua, Schraffur.
   Qué ganamos cada uno y borradores de issues/correo: [13 Colaboración](13_colaboracion_swisstopo.md).

Up: [Índice](README.md)

Related: [13 Colaboración](13_colaboracion_swisstopo.md) · [14 Licencias](14_licencias_terceros.md) · [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [04 Schraffur](04_schraffur_din4023.md) · [06 Grundwasser](06_grundwasser.md) · [07 Coordenadas](07_coordenadas.md) · [09 Validación](09_validacion_benchmark.md) · [11 Decisiones](11_decisiones.md)
