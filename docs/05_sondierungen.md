---
title: "Sondierungen: digitalizar curvas DPH/CPT"
date: 2026-10-23
tags: [geo_agent, extraccion, sondierungen, dph, cpt]
aliases: [Sondierungen, Rammsondierung, Drucksondierung]
---

# Sondierungen: digitalizar curvas DPH/CPT

**Conclusión:** las Sondierungen (Rammsondierung DPH/DPL/DPM, Drucksondierung CPT) se descartan
hoy (`geo_agent/bohrprofil.py:32`, README: "CPT-/Sonden-Spalten bewusst weggelassen"), pero en
un PDF vectorial sus curvas son **polilíneas exactas**. Con los ejes calibrados por regresión
(la misma técnica que en el Längsschnitt) se digitalizan sin pérdida.

**Estado:** probado para DPH en el layout sintético B (`soundings` en
[`prototyp_v2.py`](../spikes/extraktion_v2/prototyp_v2.py)): **32 escalones**, error máximo
**0,4 golpes N10** (redondeo de la regresión sobre el centro de las etiquetas). CPT: diseño.

## 1. Qué contienen

| Tipo | Norma | Curva | Valor |
|---|---|---|---|
| DPL / DPM / DPH / DPSH | DIN EN ISO 22476-2 | escalones cada 10 cm | `N10` (golpes / 10 cm) |
| CPT / CPTu | DIN EN ISO 22476-1 | continua | `q_c` [MN/m²], `f_s`, `R_f`, (`u_2`) |
| SPT (en el Bohrprofil) | DIN EN ISO 22476-3 | números sueltos | `N30` |

Uso posterior (Lagerungsdichte, consistencia, parámetros del modelo): correlaciones normadas a
cargo del geotécnico; la app sólo entrega los datos con procedencia.

## 2. Algoritmo

1. **Encontrar el diagrama**: título con regex `^(DPH|DPL|DPM|DS|CPT|SRS)\s*\d+…` y el marco
   (rectángulo sin relleno, alto) debajo.
2. **Eje de valores**: números enteros en una fila bajo el título (`0 10 20 30`) → ajuste
   `N10 = a·x + b`. Aceptar sólo si forman progresión aritmética (≥ 3).
3. **Eje de profundidad**: regla de enteros a la izquierda del marco (`1 2 3 …`) → `Tiefe = c·y + d`;
   si el diagrama comparte eje con el Bohrprofil, reutilizar su regresión ([02 §3](02_bohrprofil_generalizacion.md#3-escala-vertical-por-regresión)).
4. **Curva**: el path sin relleno con ≥ 6 segmentos dentro del marco. DPH: cada segmento
   vertical es un escalón `(Tiefe_oben, Tiefe_unten, N10)`. CPT: muestrear la polilínea cada
   2 cm.
5. **Varias curvas** (CPT: `q_c` y `R_f`): separar por color, grosor, trazo o capa OCG, y asignar
   cada una a su eje (un CPT suele tener dos escalas horizontales).
6. **Validar**: profundidad monótona, valores dentro del eje, última profundidad = Endtiefe
   rotulada.

## 3. Casos especiales

- Valores que salen del eje se rotulan como texto en el borde (`N10 > 50`, `76`) → leer el texto
  en lugar de la curva y marcar `censurado`.
- Ejes logarítmicos (algunos CPT): ajustar sobre `log10(valor)`.
- Diagrama partido en varias páginas → concatenar por profundidad.
- Escaneos: sólo raster → Fast Line Detector / vectorización (swissgeol tiene la detección de
  líneas en raster, [08](08_swissgeol_reutilizacion.md)); confianza menor.

## 4. Modelo de datos

```sql
create table soundings (
  id uuid primary key default gen_random_uuid(),
  project_id uuid not null references projects on delete cascade,
  code text not null,                      -- 'DPH 1', 'CPT 3'
  kind text not null,                      -- 'DPH' | 'DPL' | 'CPT' ...
  collar geometry(PointZ),
  provenance jsonb not null default '[]',
  unique (project_id, code)
);
create table sounding_values (
  sounding_id uuid references soundings on delete cascade,
  depth_top numeric(7,2), depth_bottom numeric(7,2),
  quantity text not null,                  -- 'N10' | 'qc' | 'fs' | 'Rf'
  value real, censored boolean default false
);
```

Encaja junto a `boreholes` en el esquema de la [arquitectura §5.2](ARQUITECTURA_BAUGRUNDMODELL.md#52-esquema-supabase-borrador-de-migración);
en IFC, `Pset_SolidStratumCapacity.NValue` puede recibir valores agregados por estrato.

Up: [Índice](README.md)

Related: [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [09 Validación](09_validacion_benchmark.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md)
