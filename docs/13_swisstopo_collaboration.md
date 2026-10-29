---
title: "Colaboración con swisstopo: qué nos dan y qué les damos"
date: 2026-10-25
tags: [swissgeol, colaboracion, open-source]
aliases: [Colaboración swisstopo, swisstopo]
---

# Colaboración con swisstopo: qué nos dan y qué les damos

**Conclusión:** la colaboración tiene sentido para ambos porque los proyectos se complementan.
swisstopo tiene un núcleo textual/estadístico maduro, una infraestructura de evaluación y
experiencia con documentos muy heterogéneos. Nosotros aportamos lo que a ellos les falta para
**PDFs CAD vectoriales**, la **lectura del dibujo** y las **convenciones alemanas**. El proyecto
invita explícitamente a otras organizaciones a contribuir y a hablar de partnerships
(README de su repo). Empezar con poco riesgo: dos issues con reproductores sintéticos y un
correo de presentación.

## 1. Qué puede aportar swisstopo

| Aporte | Para qué nos sirve | Cómo pedirlo |
|---|---|---|
| Algoritmos probados (columnas AAboveB, emparejamiento, diagonales, continuación) | Núcleo de [02](02_bohrprofil_generalizacion.md) sin reinventar | Ya es público; portar ideas ([08](08_swissgeol_reutilizacion.md)) |
| **Experiencia** con miles de perfiles de layouts desconocidos | Evitar errores que ya resolvieron (OCR, multipágina, tablas) | Conversación técnica / revisión de nuestro diseño |
| **Evaluación**: formato `ground_truth.json`, métricas, `--benchmark` | Medir igual que ellos; comparar resultados | Público; confirmar que las extensiones propias son aceptables |
| **Corpus suizo con verdad** (si pueden compartir una parte) | Probar generalidad con documentos de otro país | Preguntar; sus datos están en un S3 privado |
| Ruta **OCR** (`swissgeol-ocr`, AWS Textract) y modelos BERT de descripciones (HuggingFace `swissgeol/*`) | Gutachten escaneados; clasificación de descripciones en alemán | Público; preguntar por la aplicabilidad al vocabulario DIN |
| Hoja de ruta compartida | Saber qué van a construir (fecha, método de perforación…) para no duplicar | Conversación |

## 2. Qué podemos aportar nosotros

| Aporte | Valor para ellos | Esfuerzo | Ya probado |
|---|---|---|---|
| **Reportes de errores con reproductor sintético** (§4) | Arreglan fallos reales: nombre del diagrama vecino asignado al sondeo, leyenda tratada como sondeo | Bajo | Sí ([08 §4](08_swissgeol_reutilizacion.md#4-prueba-swissgeol-sin-cambios-sobre-nuestros-pdfs)) |
| **Generador de PDFs sintéticos** con verdad | Tests de regresión sin problemas de copyright | Bajo | Sí ([spike](../spikes/extraktion_v2/README.md)) |
| **Líneas desde vectores** (`get_drawings()` → su `Line`) en vez de FLD sobre raster | Exactitud y velocidad en PDFs nativos digitales | Bajo-medio | Diseño ([08 §6](08_swissgeol_reutilizacion.md#6-adaptador-propuesto-líneas-vectoriales-para-su-pipeline)) |
| **Clasificación de Schraffur con la leyenda** | Su detector de strip logs localiza pero no clasifica | Medio | Sí, sintético ([04](04_schraffur_din4023.md)) |
| **Convenciones alemanas**: claves de cota `NHN/NN`, CRS UTM/Gauß-Krüger, símbolo de agua DIN 4023 | Abre el proyecto a perfiles alemanes | Medio | Agua y coordenadas, sintético ([06](06_grundwasser.md), [07](07_coordenadas.md)) |
| **Digitalización de Sondierungen** (DPH/CPT) | Dato nuevo para su base | Medio | DPH, sintético ([05](05_sondierungen.md)) |
| Exportación **IFC 4.3** de sondeos | Puente a BIM / swissgeol 3D | Medio | Sí ([spike IFC](../spikes/ifc_thatopen/README.md)) |

## 3. Forma de colaborar y propiedad intelectual

- Su repo no tiene CLA ni `CONTRIBUTING` (revisado en el commit `776ea39`): las contribuciones
  entran bajo **AGPL-3.0-only**. El copyright de lo que escribimos sigue siendo nuestro, así que
  podemos usar *nuestro* código también bajo otra licencia **[confirmar con ellos y con un
  abogado]**. Lo que no podemos es llevarnos *su* código a un producto cerrado
  ([14](14_licencias_terceros.md)).
- Contribuir piezas **pequeñas y aisladas** (adaptador vectorial, validadores CRS, detector de
  símbolo). El núcleo propio (fusión, Längsschnitt, modelo, IFC) se queda en Geo_Agent.
- Respetar su hoja de ruta: aceptan contribuciones "compatibles con su mandato". Preguntar antes
  de PRs grandes.

## 4. Primeros pasos

Los envía el equipo; Claude no publica nada en repos ajenos.

1. **Issue 1: nombre del sondeo** (borrador abajo) con `synth_B.pdf` adjunto.
2. **Issue 2: la leyenda produce capas o sondeos falsos** con `synth_A.pdf` / `synth_A4.pdf`.
3. **Correo de presentación** al contacto del proyecto (de `publiccode.yml`: Stijn Vermeeren,
   `stijn.vermeeren@swisstopo.ch`).
4. Si responden: PR pequeño con el adaptador de líneas vectoriales y una propuesta de módulo de
   convenciones alemanas.

### Borrador issue 1 (inglés)

```text
Title: Borehole name assigned from neighbouring diagram title (e.g. "DPH 1") instead of the borehole header

Hi, we are evaluating the pipeline on German DIN 4023 borehole profiles (digitally born PDFs).
On a synthetic profile with two boreholes ("BK 1", "BK 2"), each followed by a dynamic probing
diagram titled "DPH 1" / "DPH 2", the layers and depths are extracted correctly, but the
borehole metadata name becomes "DPH 1" / "DPH 2" instead of "BK 1" / "BK 2".

Steps: boreholes-extract-all -i <dir with synth_B.pdf> -o out -p out/predictions.json
Version: commit 776ea39 (2026-10-23), default config.
Attached: synth_B.pdf (synthetic, no copyright restrictions) and its ground truth JSON.
Expected: name taken from the header above the depth sidebar / strip log.
```

### Borrador issue 2 (inglés)

```text
Title: Legend page ("Zeichenerklärung") parsed as a borehole / continuation of the last borehole

On synthetic DIN 4023 profiles whose second page only contains the legend (soil-type swatches
with names), the legend entries become layers: either appended to the last borehole of page 1
as a continuation (9 instead of 6 layers) or as an extra borehole without depths.
Attached: synth_A.pdf, synth_A4.pdf + ground truth. Commit 776ea39, default config.
Possible signal: legend swatches are isolated small rectangles with a name to their right,
not a contiguous strip log; the page also contains a "Zeichenerklärung/Legende" heading.
```

### Borrador correo (inglés)

```text
Subject: German DIN 4023 profiles – possible collaboration on swissgeol-boreholes-dataextraction

Dear Mr Vermeeren,

we are building an internal tool that extracts borehole data from German geotechnical reports
(digitally born CAD PDFs, DIN 4023) and turns it into a 3D ground model (IFC 4.3). We evaluated
your pipeline on synthetic German profiles: the depth-sidebar and description matching worked
very well across layouts; German specifics (NHN elevations, UTM/Gauss-Krüger coordinates,
DIN groundwater symbol) and the two issues we just opened are where it struggled.

We would like to contribute small, isolated pieces where useful to you, for example:
- a line source from PDF vector drawings (exact lines without rasterisation),
- German elevation/coordinate conventions,
- a synthetic DIN 4023 profile generator with ground truth for regression tests,
- (if of interest) classification of strip-log hatch patterns using the document legend.

Would you be open to a short call to check fit with your roadmap? We would also be interested
to know whether a small Swiss test subset with ground truth could be shared for benchmarking.

Kind regards,
<Name>, <Organisation>
```

Up: [Índice](README.md)

Related: [08 swissgeol](08_swissgeol_reutilizacion.md) · [14 Licencias](14_licencias_terceros.md) · [12 Corpus](12_corpus_publico.md) · [11 Decisiones](11_decisiones.md)
