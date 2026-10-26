---
title: "Resultados con PDFs reales (ronda 1, tres rondas ciegas y banco de pruebas)"
date: 2026-10-25
tags: [corpus, validacion, resultados, extraccion]
aliases: [Resultados reales, Primera ronda corpus]
---

# Resultados con PDFs reales (ronda 1, tres rondas ciegas y banco de pruebas)

**Conclusión:**
- **v1 (actual):** 0 de 58 sondeos en nueve Gutachten públicos.
- **Ronda 1** (3 PDFs): v3 funciona después de siete cambios que los sintéticos no revelaban.
- **Prueba ciega 2** (2 PDFs nuevos, código congelado): **v3 sacó 0 de 13**. swissgeol sacó
  13/13 sondeos, pero ninguna cota y 18 sondeos inventados.
- **Prueba ciega 4** (4 ejemplos suizos de swissgeol, otro dominio): v3 y v4 **0 de 3**, sin falsos (§8.2).
- **v4 + banco de pruebas** (entrenamiento, §8): 87/92 sondeos, 541/541 límites (538 exactos al cm),
  0 datos falsos; robusto al giro, conservador en raster; cadena completa PDF → PostGIS → IFC → That Open.
- **Prueba ciega 3** (4 PDFs nuevos, predicciones congeladas en el repo): **v3 sacó 11 de 29**,
  con cota 12/23 y 1 sondeo falso. swissgeol sacó 12 de 29 (uno sin capas), sin cotas y con 25 sondeos falsos
  (§7). Los 18 sondeos que faltan están en un raster sin texto (11) o en un título con sufijo (5)
  o un dibujo AutoCAD con texto convertido en líneas (1), más una instancia equivocada.

La lección es que la geometría da precisión y control de falsos positivos, mientras que la
tolerancia a formatos de texto desconocidos es el punto fuerte de swissgeol. **La solución es
combinar ambas** (§6). Tras corregir las causas generales, v3 llega a **29/29 sondeos y 143/143
límites**, incluido un PDF escaneado.

> [!WARNING]
> Las cifras **después** de cada corrección son de *entrenamiento*. Las únicas cifras honestas de
> generalidad son las de las pruebas ciegas: **0/13** (§6.1), **11/29** (§7.1) y **0/3** (§8.2, Suiza).
> La próxima ronda con Gutachten alemanes nuevos debe medirse con v4 congelado ([12](12_corpus_publico.md)).

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

## 7. Prueba ciega 3: Triefenstein, Marl, Wesel y Berlín

### 7.1 Resultado ciego

Protocolo reforzado: las predicciones de v3 (commit `36e3554`) y de swissgeol se congelaron y
**se subieron al repo antes de abrir los PDFs** (commits `5325ead` y `2d4d5e7`,
[`spikes/korpus/frozen/runde3/`](../spikes/korpus/frozen/runde3/marl_251.json), con `sha256` del
PDF); la verdad vino después (`acc5cd5`). Así el orden queda demostrado por el historial de git.

| PDF | Oficina / software | Qué es | **v3 (ciego)** | swissgeol (ciego) |
|---|---|---|---|---|
| Triefenstein B-Plan 41 (BY) | Geotechnik Badel | Vectorial, 5 RKS en hojas sueltas a M 1:30 y 1:25, títulos `RKS 1 - Betonweg 0+050`, descripciones sólo en abreviaturas DIN 4023; DPH como **tabla de valores** | **0/5** | 0/5 · **15 sondeos falsos** |
| Marl B-Plan 251 (NRW) | Dr. Spang · **IDAT/GeoDin** | Vectorial, 12 BS a M 1:50 con columna de muestras Von/Bis junto a las etiquetas, Längsschnitt con DPH, ejecución de GWM en la hoja de BS 10 | **12/12** (BS 10 tomado del corte) · 91/97 límites · **GOK 12/12** · 1 sondeo falso | 11/12 · 87/97 · GOK 0/12 · 6 falsos |
| Wesel Anlage 12 (NRW) | Asmus + Prabucki · **AutoCAD** | 1 sondeo de 38 m, perfil a M 1:200 con **texto SHX convertido en líneas** (sin capa de texto); Schichtenverzeichnis DIN 4022 como texto; fotos de testigos | **0/1** | 1/1 · 0/24 límites · 3 falsos |
| Berlín V-67b-VE | GuD Consult | Voruntersuchung sin sondeos propios: 11 sondeos de terceros (Geoportal Berlin y archivo) como **imágenes raster sin texto**, con CPT y coordenadas UTM 33N en la imagen | **0/11** | 0/11 · 1 falso |
| **Total** | | | **11/29 correctos** (+1 instancia equivocada) · 91/200 límites · GOK 12/23 · GW 0/4 · 1 falso | 12/29 (1 sin capas) · 87/200 · GOK 0/23 · GW 0/4 · **25 falsos** |

v3 fue preciso donde leyó (Marl: 87/87 límites en los 11 sondeos correctos y todas las cotas),
pero se cayó entero por detalles de formato que un humano ni ve. swissgeol volvió a encontrar
profundidades donde v3 no, a cambio de muchos falsos y ninguna cota.

### 7.2 Por qué falló y qué se cambió después

| # | Causa | Cambio (general) | Efecto (entrenamiento) |
|---|---|---|---|
| L13 | Título con sufijo: `RKS 1 - Betonweg 0+050` (nombre y estación) | La cabecera acepta `<código> - <texto>` | Triefenstein 0/5 → **5/5 · 24/24 · GW 2/2** |
| L14 | La escala de profundidad del diagrama DPH del corte (1,00 … 10,00) pasó por etiquetas de BS 10 | Grupos de etiquetas en **progresión aritmética** (≥ 5 valores, mismo paso) = eje o regla, no límites. swissgeol ya lo hacía y no lo habíamos portado ([08](08_swissgeol_reutilizacion.md)) | Marl BS 10 correcto, 97/97 |
| L15 | IDAT pone una columna de muestras con pares Von/Bis (`0,20 / 0,60`) junto a las etiquetas; el plano de ejecución de la GWM parecía un segundo sondeo | Grupo con valores duplicados = columna de muestras. Una columna sin etiquetas confirmadas, cuando las vecinas sí tienen, no es un perfil. Sin ninguna etiqueta en la página (OCR perdido) se mantiene la escala del cajetín | 0 sondeos falsos. La primera versión de esta regla rompió B 4 de Rednitzhembach y el conjunto de entrenamiento lo detectó |
| L16 | Descripción sólo con abreviaturas (`U, t, s´`, `fS, ms´`, `A (S, u´)`) | Fracción principal desde la abreviatura DIN 4023 / EN ISO 14688 | Bodenart Triefenstein 18/24, Marl 18/23 |
| L17 | AutoCAD con fuentes SHX: las etiquetas son líneas y el perfil no se puede leer sin OCR | **Schichtenverzeichnis** (formulario DIN 4022, igual en todas las oficinas) como segunda fuente: profundidad en la columna 1, denominación bajo `a)` y agua en la columna 3. Contraste 1:1 con el perfil | Wesel **1/1 · 24/24**; contraste "SV ok" en 14/14 sondeos de Hausham y Triefenstein |
| L18 | Sondeos de terceros como **raster sin capa de texto** (capturas del Geoportal, escaneos de archivo); códigos `422C-460`; CPT | Sin cambio: hace falta un paso de **OCR** (ocrmypdf/Tesseract) antes del pipeline; el adaptador raster (L11) ya cubre las líneas | Berlín sigue en 0/11 |

### 7.3 Acumulado de los nueve PDFs (después de las correcciones = entrenamiento)

| | v1 | v3 | swissgeol (sin cambios) |
|---|---|---|---|
| Sondeos | 0/58 | **47/58** (los 11 restantes son el raster de Berlín) | 31/58 |
| Límites | 0/343 | **288/343** (+1 falso, marcado) | 156/343 |
| GOK | 0/50 | **39/50** | 6/50 |
| Nivel freático | 0/12 | **9/12** | 4/12 |
| Bodenart (capas con verdad) | — | **119/132** | (no clasifica) |
| Sondeos falsos | 0 | **0** | **55** |

Los sintéticos no cambian (102/102). Reproducir: `python spikes/korpus/eval_real.py <pdfs>`.

### 7.4 Qué aprendimos

1. **El cuello de botella ya no es la geometría sino la entrada:** de los 18 sondeos perdidos,
   12 no tenían texto legible (raster o SHX). El OCR pasa a ser un componente, no un extra.
2. **El Schichtenverzeichnis es la fuente más estable:** es un formulario normado, viene en texto
   incluso cuando el dibujo es una imagen, y sirve para verificar cada perfil ([02](02_bohrprofil_generalizacion.md)).
3. **Reglas pequeñas, efectos grandes:** un sufijo en el título tumbó un Gutachten entero (0/5). La
   detección de cabeceras debe ser tolerante y la validación geométrica estricta (D26).
4. **El conjunto de entrenamiento como prueba de regresión** atrapó una regla que rompía
   Rednitzhembach. Cada cambio se mide contra los nueve PDFs y los sintéticos.

## 8. Banco de pruebas, algoritmo v4 y cadena completa (2026-10-26)

Todo lo de esta sección es **entrenamiento** salvo §8.2 (ronda 4, ciega). Algoritmo:
[17](17_algoritmo_extraccion.md); reglas: [16](16_lecciones_aprendidas.md).

### 8.1 El banco de pruebas

| Capa | Qué es | Herramienta |
|---|---|---|
| Real | 13 PDFs con verdad: 9 Gutachten alemanes + 4 ejemplos suizos de swissgeol | [`regression.py`](../spikes/korpus/regression.py) |
| Estrés | 13 PDFs mínimos, **uno por lección** (título con sufijo, página girada, eje DPH, columna de muestras, abreviaturas, SHX + SV, raster, código de terceros…) | [`stress_cases.py`](../spikes/extraktion_v2/stress_cases.py) |
| Sintético | 6 layouts con Schraffur, agua, DPH y coordenadas | `synth_bohrprofil.py` |
| Perturbación | los 13 reales girados 90°, reducidos al 70 % y rasterizados a 150 dpi sin texto, con la misma verdad | [`perturb.py`](../spikes/korpus/perturb.py) |
| Ablación | cada regla apagada por separado | [`ablation.py`](../spikes/korpus/ablation.py) |

Nueva métrica: **límites exactos** (al centímetro, como están impresos) además de la tolerancia de 5 cm.

### 8.2 Ronda 4 ciega: ejemplos suizos de swissgeol

Predicciones congeladas y subidas antes de abrir los PDFs (v3 `6162150`, v4 `68f0b54`). Dominio
distinto (Suiza, escaneos con capa OCR, francés), verdad con códigos `RB 2/I`, `SST KB5`, `MGR01`.

| | v3 (ciego) | v4 (ciego) | v4 después (entrenamiento) |
|---|---|---|---|
| Sondeos | 0/3 | 0/3 | 2/3 (el francés sigue en 0) |
| Límites | 0/26 | 0/26 | 26/26 exactos |
| Falsos | 0 | 0 | 0 |

Causas y cambios: cabecera `Sondierbohrung : SST KB 5` (T1), código partido por el OCR (`RB` + `2 / I`),
capa OCR que pierde texto (L18b), escaneo con ruido vectorial (E2), columna de profundidades del
formulario (T5), etiquetas apiladas con escala en puntos que no es la del papel (E5, T4) y perfil sólo
como **tabla de texto** (S6). El documento francés (profundidades negativas al inicio de cada
descripción) queda fuera.

### 8.3 v3 frente a v4 en el mismo conjunto (13 reales + 13 estrés + 6 sintéticos)

| | v3 | **v4** |
|---|---|---|
| Sondeos | 76/92 | **87/92** |
| Límites (±5 cm) | 451/541 | **541/541** |
| Límites exactos (al cm) | 414/541 | **538/541** |
| Bodenart | 282/295 | 300/315 |
| GOK | 65/81 | **74/81** |
| Nivel freático | 30/35 | **33/35** |
| Coordenadas | 17/25 | **25/25** |
| Sondeos / límites / agua falsos | 0 / 3 / 0 | **0 / 0 / 0** |

Lo que falta: 4 sondeos de archivo de Berlín (escaneos de baja calidad) y el francés; Bodenart con
líneas de referencia oblicuas (Marl); "trocken" sólo en el texto del informe (Triefenstein).

### 8.4 Perturbaciones (misma verdad, 13 PDFs reales)

| Variante | Sondeos | Límites | Exactos | Falsos (sondeos / límites / agua) | Coordenadas |
|---|---|---|---|---|---|
| Original | 56/61 | 369/369 | 366/369 | 0 / 0 / 0 | 7/7 |
| Girado 90° | 56/61 | 369/369 | 366/369 | 0 / 0 / 0 | 7/7 |
| Reducido al 70 % | 54/61 | 300/369 | 293/369 | 1 / 2 / 0 | 6/7 |
| Raster 150 dpi sin texto | 40/61 | 150/369 | 144/369 | **0 / 0 / 0** | 4/7 |

- **Giro:** robusto. La primera versión destapó un fallo real (el lector del SV ignoraba la rotación)
  y otro de la propia herramienta (`show_pdf_page` ignora `/Rotate`, X5).
- **Escala:** era la mayor debilidad (57 límites falsos). El texto `1:75` del cajetín ya no vale si
  el PDF está reducido: ahora, si contradice las etiquetas, el sondeo sale sin capas y con aviso (E5).
  Talheim reducido sigue sin capas: sus etiquetas están desplazadas con líneas de referencia.
- **Raster:** conservador, sin ningún dato falso. Pierde lo que depende de texto pequeño (Marl a 150 dpi),
  el Schichtenverzeichnis leído por OCR (Wesel), títulos de Triefenstein, el símbolo ▽ en imagen
  (W4, intento descartado) y columnas de sólo relleno de color (E7).

### 8.5 Ablación: qué regla protege qué caso

Cada una de las 28 reglas de `RULES` se apagó por separado sobre el conjunto completo
([tabla](../spikes/korpus/ablation_v4.md)). **22 reglas están protegidas por al menos un caso**:
apagarlas empeora algo medible. Las de más efecto:

| Regla apagada | Qué se rompe |
|---|---|
| `rotation` (L2) | Talheim 10/10 → 0/10, Wesel 24/24 → 0, caso girado |
| `generic_heads` (T1) | Berlín 7/11 → 1/11, los dos suizos, caso de código de terceros |
| `ocr` (L18) | Berlín 7/11 → 0/11, caso raster |
| `label_snap` (T2) | límites exactos: Berlín 55 → 37, Talheim 65 → 45, Rednitzhembach 13 → 6 |
| `abbreviations` (L16) | Bodenart Marl 18 → 0, Triefenstein 18 → 1 |
| `gw_symbol_filter` (L10) | 54 niveles de agua falsos en Hausham |
| `axis_filter` (L14) | 7 límites falsos en Marl |
| `sv_source` (S1) | Wesel 1/1 → 0/1, caso SHX |

Sin caso que las proteja: `dashed_exclusion` y `table_filter` (sus fallos los cubren otras
reglas), `top_convention` y `single_sheet_anchor` (ningún caso actual los necesita),
`scale_contradiction` (sólo la protege la perturbación al 70 %) y `raster_gw_symbol` (apagada).
Siguiente paso: un caso de estrés para cada una (P10).

### 8.6 La regresión como red de seguridad

Durante la noche la batería atrapó **cinco** errores propios antes de subirlos: la regla de
Schraffur que borraba capas finas reales (Wachenroth, Rednitzhembach), `Bohrung` sin sufijo que dejó
de reconocerse (Berlín 7 → 2), el modo "etiqueta primero" que coló una cota como profundidad (Marl),
los triángulos raster que inventaron 146 niveles de agua, y la regla de escala que borraba un
sondeo de Berlín. Ninguno llegó al resultado final (P5).

### 8.7 Cadena completa con datos reales (el objetivo)

PDF → `prototyp_v4` → JSON canónico (procedencia y confianza por capa) →
[PostGIS con el esquema Supabase](../spikes/supabase/README.md) (56 sondeos, 383 capas de 10
Gutachten; Berlín en EPSG:25833 con distancias correctas; LV03 suizo transformado a LV95) →
[IFC 4.3](../spikes/ifc_thatopen/README.md) (0 errores de esquema) → That Open (69 estratos con
geometría, 7 sondeos de Berlín). Las capas con confianza < 0,6 (9 de 383) quedan marcadas para revisión.

## 9. Próximos pasos

1. **Quinta ronda ciega con Gutachten alemanes nuevos** (los 4 bloqueados de la ronda 3:
   Wolfsburg/GGU, NLWKN, Böblingen, Königslutter), con v4 congelado y subido antes de mirar. Es la
   única cifra que dirá si v4 generaliza.
2. Raster: Schichtenverzeichnis por OCR, bordes de rellenos de color (E7), símbolo de agua por
   plantilla de la leyenda (W4).
3. DPH desde **tablas** (Triefenstein: N10 cada 10 cm como texto) y CPT (Berlín) en el modelo de
   datos ([05](05_sondierungen.md)).
4. Muestras de leyenda desde segmentos → Schraffur y símbolos de agua con datos reales.
5. Llevar las lecciones L1–L18 al plan de implementación ([10](10_plan_implementacion.md)).

Up: [Índice](README.md)

Related: [12 Corpus](12_corpus_publico.md) · [09 Validación](09_validacion_benchmark.md) · [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [08 swissgeol](08_swissgeol_reutilizacion.md) · [11 Decisiones](11_decisiones.md)
