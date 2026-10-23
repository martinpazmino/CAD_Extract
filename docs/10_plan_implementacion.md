---
title: "Plan de implementación: extracción v2"
date: 2026-10-23
tags: [geo_agent, plan, roadmap, extraccion]
aliases: [Plan extracción v2, Roadmap extracción]
---

# Plan de implementación: extracción v2

**Objetivo:** reemplazar los supuestos fijos de v1 por la extracción geométrica/estadística,
recuperar los datos perdidos y hacerlo medible, sin romper el Excel actual. Este plan detalla las
fases F0–F2 de la [arquitectura §11](ARQUITECTURA_BAUGRUNDMODELL.md#11-hoja-de-ruta) para la parte
de extracción. Estimaciones orientativas para una persona.

| Paso | Contenido | Archivos | Criterio de aceptación | Esfuerzo |
|---|---|---|---|---|
| 0 | **Banco de pruebas**: mover generador sintético y métricas de `spikes/extraktion_v2` a `tests/`; añadir KPI de error silencioso; test de no-regresión del Excel con los PDFs de referencia | `tests/synth/`, `tests/test_extraction.py` | CI verde con v1 en A/A2; fallos documentados de v1 en A3/A4/B | 2–3 días |
| 1 | **Modelo canónico con procedencia** (Pydantic) + adaptador v1 → modelo → Excel | `geo_agent/model.py`, `exporters/excel_writer.py` | Excel idéntico al actual | 2–3 días |
| 2 | **Bohrprofil v2 núcleo**: columnas, cabecera/GOK genéricos, escala por regresión (portar AAboveB de swissgeol), límites geométricos, bloque de descripción | `geo_agent/bohrprofil/{columns,header,scale,text_assign}.py` | A–A5 y B al 100 % en CI; Excel de referencia sin regresión | 1 semana |
| 3 | **Clasificación**: sustantivo vs. adjetivo, eliminar "continuación" silenciosa, Schraffur + fusión + confianza | `geo_agent/soil.py`, `geo_agent/bohrprofil/hatch.py`, `validate/` | Error silencioso = 0 en el corpus; A5 genera su issue | 3–4 días |
| 4 | **Grundwasser y Sondierungen** | `bohrprofil/symbols.py`, `bohrprofil/soundings.py` | Agua ±5 cm; DPH ≤ 1 N10; nuevas hojas/tablas en la salida | 4–5 días |
| 5 | **Coordenadas**: tablas (lectura por celda), cabecera, CRS alemanes; Lageplan después | `lageplan/coord_tables.py`, `lageplan/georef.py` | Rechts-/Hochwert rellenos y verificados contra GOK | 3–4 días (+1 semana Lageplan) |
| 6 | **Längsschnitt v2**: ejes genéricos, colores desde la leyenda, OCG, polígonos vectoriales, mini-columnas | `geo_agent/laengsschnitt/{axes,tunnel,geoslice}.py` | Mismo resultado que v1 en el plano de referencia + un segundo plano distinto | 1–1,5 semanas |
| 7 | **swissgeol**: oráculo en el benchmark, listas de palabras clave, contacto upstream | `tests/oracle_swissgeol.py` | Informe comparativo automático | 2 días |
| 8 | **Corpus real**: 5–10 Gutachten, verdad semi-automática, calibrar umbrales y pesos | bucket privado + `tests/thresholds.yml` | Métricas reales publicadas en [09](09_validacion_benchmark.md) | continuo |

## Orden y dependencias

```
0 ─► 1 ─► 2 ─► 3 ─► 4
          │         └─► 5
          └─────────────► 6
0 ─► 7 (en paralelo)          8 empieza en cuanto 2 esté listo
```

## Reglas para la migración

- v1 sigue disponible detrás de un flag hasta que v2 iguale o mejore todas las métricas del
  corpus de referencia.
- Cada detector nuevo entra con su caso sintético y su métrica.
- Toda constante nueva va al perfil YAML o a `tests/thresholds.yml`, nunca hard-codeada.
- Código portado de swissgeol: reimplementado y citado (licencia, [08 §5](08_swissgeol_reutilizacion.md#5-estrategias-de-reutilización)).

Up: [Índice](README.md)

Related: [09 Validación](09_validacion_benchmark.md) · [11 Decisiones](11_decisiones.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md) · [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [03 Längsschnitt](03_laengsschnitt_generalizacion.md)
