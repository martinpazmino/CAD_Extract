---
title: "Spike: Supabase/PostGIS con datos extraídos"
date: 2026-10-26
tags: [spike, supabase, postgis]
aliases: [Spike Supabase]
---

# Spike: Supabase/PostGIS con datos extraídos

Comprueba que el JSON canónico de la extracción ([`prototyp_v4.to_canonical`](../extraktion_v2/prototyp_v4.py))
entra en el esquema de la [arquitectura §5.2](../../docs/ARQUITECTURA_BAUGRUNDMODELL.md#52-esquema-supabase-borrador-de-migración)
y que se puede consultar espacialmente.

| Archivo | Qué hace |
|---|---|
| [`migrations/0001_core.sql`](migrations/0001_core.sql) | Migración (copiada de la arquitectura; tipos PostGIS cualificados `extensions.geometry`) |
| [`local_shim.sql`](local_shim.sql) | Sólo para Postgres local: esquema `auth` mínimo que Supabase trae de serie |
| [`load_extraction.py`](load_extraction.py) | Carga documentos, ejecuciones, sondeos (collar PointZ transformado al CRS del proyecto), capas y agua |

```bash
psql -f local_shim.sql -f migrations/0001_core.sql          # en Supabase: sólo la migración
python load_extraction.py --dsn "..." --project "Berlin" --crs 25833 berlin_v67b.json
```

**Resultado (2026-10-26, PostgreSQL 16 + PostGIS 3 local):** migración sin errores (15 tablas);
Berlín: 7 sondeos, 80 capas, 2 niveles de agua, 5 collares en EPSG:25833; Marl: 12 sondeos,
97 capas. Consultas de distancia entre sondeos correctas (422C-460 ↔ 422C-461: 32,2 m).

**Hallazgo:** con `create extension postgis with schema extensions`, el tipo `geometry` no está en
el `search_path` de un Postgres normal; Supabase lo tiene por defecto. La migración cualifica los
tipos (`extensions.geometry`) para funcionar en ambos.

Up: [Índice de documentación](../../docs/README.md)

Related: [Arquitectura](../../docs/ARQUITECTURA_BAUGRUNDMODELL.md) · [17 Algoritmo](../../docs/17_algoritmo_extraccion.md) · [Spike IFC](../ifc_thatopen/README.md)
