---
title: "Schraffur DIN 4023: la columna gráfica como segunda señal"
date: 2026-10-23
tags: [geo_agent, extraccion, schraffur, din4023, clasificacion]
aliases: [Schraffur, Hatch, Signaturen]
---

# Schraffur DIN 4023: la columna gráfica como segunda señal

**Conclusión:** la columna gráfica del Bohrprofil (patrones DIN 4023: puntos = Sand, círculos =
Kies, rayas = Ton/Schluff…) es una señal **independiente del texto** que hoy se ignora
(`geo_agent/bohrprofil.py:13`). Leída de los vectores y comparada con las muestras de la
**leyenda del mismo documento**, clasifica la Bodenart sin entrenamiento previo y permite
detectar errores del texto.

**Estado:** probado en el prototipo (`hatch_features`, `legend_swatches`, `classify_hatch` en
[`prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py)): **101/102 capas** de los 6 layouts
sintéticos clasificadas correctamente sólo por Schraffur; la restante es la capa de A5 dibujada
a propósito con el patrón equivocado, y el prototipo la reporta como `Text 'Sand' != Schraffur
'Kies'` (v1 no la nota). Con planos reales hay que calibrar (ver §5).

## 1. Por qué la leyenda es el conjunto de entrenamiento

Cada Zeichenerklärung DIN 4023 dibuja una muestra del patrón junto al nombre de la Bodenart.
Esas muestras usan el mismo software, la misma escala de patrón y los mismos estilos que las
columnas del documento. Por eso un vecino más cercano contra las muestras funciona sin datos
etiquetados: el documento trae su propia "verdad".

Detección de muestras: rectángulo con relleno de 15–60 × 8–30 pt con una línea de texto que
empieza en mayúscula a < 40 pt a su derecha (`legend_swatches`).

## 2. Vector de características

Por rectángulo (capa o muestra), recorriendo los **elementos** de cada path (los CAD suelen
exportar todo el patrón como un solo path con cientos de sub-elementos):

| Característica | Cómo se mide |
|---|---|
| `dot` | curvas Bézier pequeñas (< 1,5 pt) **rellenas** → puntos |
| `circle` | curvas Bézier sin relleno o mayores → círculos |
| `line_0/45/90/135` | longitud de segmentos por orientación (bins de 45°) |
| `dash` | longitud de segmentos con patrón de trazo (`dashes ≠ "[] 0"`) |

Se cuenta sólo lo cuyo punto medio cae dentro del rectángulo (los patrones suelen estar
recortados por clip), se excluye el propio marco, se normaliza por área y por norma L2. La
clasificación es similitud coseno contra las muestras; la similitud se guarda como confianza.

## 3. Fusión con el texto

| Texto | Schraffur | Resultado |
|---|---|---|
| Sand | Sand | Sand, confianza alta |
| Sand | Kies | issue "Text ≠ Schraffur", revisión |
| — (no reconocido) | Kies | Kies, confianza media, marcado |
| Sand | — (sin patrón) | Sand, confianza media |

Casos del spike: en A3, v1 clasificó `Kies, sandig` como *Sand* con certeza
([01](01_diagnostico_layout_fijo.md)) y la Schraffur dice *Kies*; en A5 (texto *Sand*, patrón de
*Kies*) la fusión genera exactamente un issue en la capa afectada.

## 4. Colores

Muchos Gutachten colorean las capas (por Bodenart o por Homogenbereich). El color de relleno se
guarda como característica y, si la leyenda tiene muestras coloreadas, se clasifica igual que
el patrón. En el Längsschnitt es la vía principal ([03 §4](03_laengsschnitt_generalizacion.md#4-geología)).

## 5. Riesgos con PDFs reales

- **Rellenos con patrón PDF** (`/Pattern`, tiling patterns): el patrón puede no aparecer como
  geometría en `get_drawings()` **[a verificar]**. Fallback: renderizar capa y muestra a alta
  resolución y comparar imágenes (correlación normalizada / descriptores de textura).
- **Bloques / Form XObjects**: patrones insertados como bloques CAD → comprobar que PyMuPDF los
  aplana **[a verificar]**.
- **Escala de patrón distinta** entre leyenda y columna: la normalización L2 hace el vector
  dependiente de la *proporción* de elementos, no de su densidad; si no basta, normalizar por el
  espaciado detectado.
- **Patrones mixtos** (DIN 4023 combina símbolos: `Sand, kiesig` = puntos + círculos): con
  kNN se obtiene la clase más parecida; para composición, descomponer el vector como
  combinación no negativa de las muestras (NNLS) **[idea, no probada]**.
- Muestras de leyenda en otra página o en otro documento: se guardan por proyecto en Supabase y
  se reutilizan.

## 6. Relación con swissgeol

swissgeol detecta la *posición* de las columnas gráficas (`strip_log_detection.py`: raster,
morfología, círculos de Hough y Fast Line Detector) pero **no clasifica** el patrón. Su detector
sirve como fallback para localizar columnas en escaneos; la clasificación es aporte propio →
candidato a contribución upstream ([08](08_swissgeol_reutilizacion.md)).

Up: [Índice](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [03 Längsschnitt](03_laengsschnitt_generalizacion.md) · [08 swissgeol](08_swissgeol_reutilizacion.md) · [Glosario](glosario.md)
