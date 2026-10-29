---
title: "Validación y benchmark de la extracción"
date: 2026-10-23
tags: [geo_agent, validacion, benchmark, ground-truth, tests]
aliases: [Benchmark, Ground truth, Validación]
---

# Validación y benchmark de la extracción

**Conclusión:** sin un banco de pruebas, "generalizar" no se puede demostrar. Se necesitan tres
cosas: un **formato de verdad** (adoptado de swissgeol con extensiones), un **corpus** (sintético
para CI + real para calibrar) y **métricas** donde la principal sea la **tasa de error
silencioso**: datos erróneos que la app marca como seguros.

> [!NOTE]
> Con **PDFs reales** (5 Gutachten públicos): v1 0/29. En la **prueba ciega**, v3 0/13 y
> swissgeol 13/13 (con 18 falsos). Tras corregir, v3 llega a 29/29 sondeos y 143/143 límites,
> cifras de entrenamiento. Ver [15 Resultados reales](15_resultados_pdfs_reales.md) y el protocolo
> ciego (D25).

## 1. Resultados actuales (spike, PDFs sintéticos)

Reproducir: [`spikes/extraktion_v2/README.md`](../spikes/extraktion_v2/README.md).

| Layout | v1 actual: límites / Bodenart | v2 prototipo: límites / Bodenart / Schraffur | swissgeol sin cambios: límites / Bodenart |
|---|---|---|---|
| A referencia | 18/18 · 18/18 | 18/18 · 18/18 · 18/18 | 18/18 · 18/18 |
| A2 M 1:50 | 18/18 · 18/18 | 18/18 · 18/18 · 18/18 | 18/18 · 18/18 |
| A3 texto más cerca | 18/18 · **6/18 (7 en verde)** | 18/18 · 18/18 · 18/18 | 18/18 · 18/18 |
| A4 cabecera centrada | **0/18** | 18/18 · 18/18 · 18/18 | 12/18 · 12/18 |
| A5 contradicción texto/Schraffur | 18/18 · 18/18, **sin aviso** | 18/18 · 18/18 · 17/18 + **1 issue correcto** | (no lee Schraffur) |
| B otra oficina + DPH | **0/12** | 12/12 · 12/12 · 12/12 | 0/12 por nombres cruzados* |

Además, v2: GOK 17/17, agua 17/17 (±5 cm), coordenadas 17/17, DPH 32 escalones con error máx.
0,4 N10, escala detectada sin configuración (1:100 y 1:50), sin sondeos ni capas falsas, ~1 s
por PDF. swissgeol: 0 agua, 0 cota, 0 coordenadas y capas falsas desde la leyenda
([08 §4](08_swissgeol_reutilizacion.md#4-prueba-swissgeol-sin-cambios-sobre-nuestros-pdfs)).

\* profundidades y textos correctos, asignados al nombre del diagrama DPH vecino.

> [!WARNING]
> Los PDFs sintéticos los escribió el mismo autor que el prototipo v2. Demuestran que el método
> funciona y que v1 depende del layout; **no** demuestran robustez frente a planos reales. El
> siguiente paso obligatorio es el corpus real (§3).

## 2. Formato de verdad (ground truth)

Base: `ground_truth.json` de swissgeol (`docs/groundtruth-json.md` en su repo): por PDF, lista
de sondeos con `metadata` (coordenadas, cota, nombre, profundidad total), `layers`
(`depth_interval`, `material_description`) y `groundwater` (`depth`, `elevation`, `date`).
Extensiones propias (campos opcionales, compatibles con su lector):

```jsonc
{
  "Bohrprofil_Projekt_X.pdf": [{
    "borehole_index": 0,
    "metadata": {"original_name": "B 18/19", "reference_elevation": 6.20, "total_depth": 35.0,
                 "coordinates": {"E": 565081.64, "N": 5933169.81},
                 "crs_epsg": 25832, "height_datum": "DHHN2016"},              // + propio
    "layers": [{"depth_interval": {"start": 0.0, "end": 0.3},
                "material_description": "Mutterboden, humos, dunkelbraun",
                "soil_class": "Mutterboden", "hatch_class": "Mutterboden",   // + propio
                "din": {"main_fraction": "Mu"}}],                            // + propio
    "groundwater": [{"depth": 2.55, "elevation": 3.65, "date": "2019-03-08",
                     "kind": "angetroffen"}],                                // + kind propio
    "soundings": [{"code": "DPH 1", "quantity": "N10",                      // + propio
                   "values": [[0.0, 0.5, 26], [0.5, 1.0, 19]]}]
  }]
}
```

Ventaja: el mismo archivo sirve para puntuar Geo_Agent **y** swissgeol (`boreholes-score`).

## 3. Corpus

| Corpus | Contenido | Uso |
|---|---|---|
| Sintético | Generador `synth_bohrprofil.py`, ampliable: rotación de página, varias filas de sondeos, sondeos multipágina, rectángulos de 4 líneas, rellenos `/Pattern`, capas delgadas con líneas de referencia, CPT, escaneo simulado (render + OCR) | CI en cada commit |
| Referencia actual | Los PDFs del proyecto actual (no versionados) con su Excel validado | No-regresión de v1 → v2 |
| Real multi-oficina | 5–10 Gutachten **públicos** de oficinas/software distintos (GGU-STRATIG, DC-BOHR, WinBohr, AutoCAD), en un bucket privado; fuentes y criterios en [12](12_corpus_publico.md) | Calibrar umbrales y pesos; medir de verdad |

La verdad real se construye de forma **semi-automática**: correr v2 → corregir en la UI de
revisión → exportar como ground truth (la revisión humana ya es parte del flujo, ver
[arquitectura §4.2](ARQUITECTURA_BAUGRUNDMODELL.md#42-flujo-de-datos)).

## 4. Métricas

| Métrica | Definición | Objetivo |
|---|---|---|
| **Error silencioso** | capas/valores erróneos con confianza alta (verde) / total | **≈ 0**; KPI principal |
| Recall de límites | límites con \|Δ\| ≤ 2 cm / límites verdaderos | ≥ 0,98 |
| Precisión de capas | capas extraídas que existen en la verdad / capas extraídas | ≥ 0,98 (penaliza leyendas leídas como sondeos) |
| Exactitud de Bodenart | por texto, por Schraffur y fusionada | ≥ 0,95 fusionada |
| Cobertura de revisión | valores marcados para revisión / total | reportar (bajo, pero no 0 con datos reales) |
| Metadatos | nombre, GOK (±1 cm), coordenadas (±1 cm), agua (±5 cm) | ≥ 0,95 |
| Sondierungen | error máx. por escalón / RMSE de curva | ≤ 1 N10 |

Los objetivos son propuestas para fijar con el corpus real.

## 5. Integración en CI

1. `pytest` genera el corpus sintético en un directorio temporal.
2. Corre v1 (mientras exista) y v2; compara con la verdad; falla si una métrica baja respecto a
   la última versión aceptada (umbrales en un YAML versionado).
3. Opcional, nocturno: swissgeol como oráculo sobre el mismo corpus.

Up: [Índice](README.md)

Related: [01 Diagnóstico](01_diagnostico_layout_fijo.md) · [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [08 swissgeol](08_swissgeol_reutilizacion.md) · [10 Plan](10_plan_implementacion.md)
