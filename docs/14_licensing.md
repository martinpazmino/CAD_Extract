---
title: "Licencias: uso interno hoy, terceros mañana"
date: 2026-10-25
tags: [licencias, agpl, pymupdf, saas, decisiones]
aliases: [Licencias, AGPL, Uso por terceros]
---

# Licencias: uso interno hoy, terceros mañana

> [!NOTE]
> **Actualización 2026-10-29:** elegida la opción A. El repositorio se publica bajo **AGPL-3.0-or-later**
> ([`LICENSE`](../LICENSE), [terceros](../THIRD_PARTY_LICENSES.md), D79) y la app enlaza su código fuente (*Quellcode*) para
> cumplir el § 13 cuando está en línea ([22](22_despliegue.md)). B y C siguen abiertas si un día hace falta código cerrado.

**Conclusión:** para el uso **interno** la licencia AGPL de PyMuPDF (y de swissgeol) no plantea
problemas prácticos. Para ofrecer Geo_Agent **a terceros** habrá que elegir entre publicar el
código bajo AGPL, comprar la licencia comercial de PyMuPDF o cambiar la librería PDF. La decisión
puede esperar si desde ya se cumplen dos reglas baratas:
1. **todo PyMuPDF detrás de una capa de primitivas propia**;
2. **no copiar código de swissgeol**, sólo reimplementar sus ideas.

Con eso cambiar de librería queda en un módulo, y es viable: ver la prueba de §3.

> [!IMPORTANT]
> No es asesoramiento jurídico. Antes de ofrecer el servicio a terceros, revisar con un abogado
> la AGPL-3.0 y las condiciones de Artifex.

## 1. Qué exige la AGPL y cuándo

| Escenario | Obligación práctica (AGPL-3.0) |
|---|---|
| Uso interno (empleados, `localhost`, red de la empresa) | Ninguna hacia fuera. Los únicos "usuarios" son internos. |
| Entregar el software a un cliente (instalación) | Entregar también el código fuente de toda la aplicación bajo AGPL |
| **SaaS para terceros** (web) | § 13: ofrecer a los usuarios remotos el código fuente de la versión que ejecutan |

PyMuPDF se distribuye bajo AGPL o bajo **licencia comercial de Artifex** (precio a consultar).
swissgeol es **AGPL-3.0-only** sin licencia alternativa ([08](08_swissgeol_reutilizacion.md)).

## 2. Opciones para terceros

| Opción | Coste | Consecuencia |
|---|---|---|
| A. Publicar Geo_Agent como AGPL | 0 € de licencia | El código es público; el negocio está en el servicio, el soporte y los datos (que no son código) |
| B. Licencia comercial de PyMuPDF | Según Artifex | Código cerrado posible, **salvo** lo que se haya copiado de swissgeol (seguiría siendo AGPL) |
| C. Cambiar a una librería permisiva (pypdfium2) | Trabajo de adaptación (capa de primitivas) | Sin restricción de licencia de PyMuPDF |

Recomendación: decidir cuando haya un caso de negocio concreto. Hasta entonces, mantener abiertas
B y C con las dos reglas de la conclusión.

## 3. Prueba: ¿se puede sustituir PyMuPDF?

Mismo PDF sintético (layout B), primitivas vectoriales que necesita la extracción v2:

| Librería | Licencia | Paths | Segmentos / curvas | Relleno, trazo, guiones | Capas OCG | Tiempo |
|---|---|---|---|---|---|---|
| PyMuPDF 2.0 | AGPL / comercial | 30 | 1 866 ítems (1 704 curvas) | sí | sí, con nombre (`layer`) | 0,35 s |
| **pypdfium2 5.14** | **BSD-3 / Apache-2.0** | **30** (mismos objetos) | 5 839 segmentos (5 112 Bézier) | sí (`GetFillColor`, `GetDashCount`) | marca `OC` presente; nombre de la capa **[a verificar]** | 0,08 s |
| pdfplumber 0.11 / pdfminer.six | MIT | (se aplanan) | 77 líneas, 444 curvas | guiones sí; rectángulos no reconocidos en este PDF | no | 0,16 s |

Lectura: **pypdfium2** conserva el mismo modelo de objetos (un path = un objeto con segmentos y
estilo) y es el candidato natural para la opción C. pdfplumber cambia el modelo y, al ser Python
puro, probablemente sea lento con los > 150 000 paths del Längsschnitt **[a verificar]**.
Faltaría en pypdfium2: agrupar caracteres en palabras (PyMuPDF lo da hecho), `find_tables` y
resolver nombres de capas OCG.

## 4. Capa de primitivas (hacer ya)

```
geo_agent/primitives/
  model.py            Word(text, bbox, font, size, color) · Path(segments, fill, stroke, dashes, layer, bbox)
  pymupdf_backend.py  única importación de pymupdf en todo el extractor
  pdfium_backend.py   (cuando haga falta) misma interfaz con pypdfium2
```

Los extractores (`bohrprofil/`, `laengsschnitt/`, `hatch.py`…) sólo ven `Word` y `Path`. Además
sirve para cachear las primitivas en Storage ([arquitectura §6.2](ARQUITECTURA_BAUGRUNDMODELL.md#62-primitivas-una-sola-vez-por-documento-cacheadas))
y para tests sin PDF.

## 5. Resto de dependencias

| Componente | Licencia | ¿Problema para SaaS cerrado? |
|---|---|---|
| IfcOpenShell | LGPL-3.0 | No (obligaciones sólo al distribuir la librería modificada) |
| That Open (`@thatopen/*`) | MIT | No |
| web-ifc | MPL-2.0 | No (copyleft sólo por archivo modificado) |
| three.js, numpy, shapely, openpyxl | MIT / BSD | No |
| Streamlit | Apache-2.0 | No |
| Supabase (self-hosted) | Apache-2.0 | No |
| GemPy (si se usa) | **[a verificar]** | Revisar antes de integrarlo |

## 6. Otros requisitos cuando lleguen terceros

- **RGPD:** contrato de encargo (AVV) con clientes y con los proveedores (Supabase, hosting, LLM);
  región UE; borrado de documentos.
- **Confidencialidad:** separación por cliente con RLS ya prevista en el
  [esquema](ARQUITECTURA_BAUGRUNDMODELL.md#52-esquema-supabase-borrador-de-migración); cifrado y
  buckets privados.
- **LLM:** contrato sin entrenamiento con los datos y retención mínima, o desactivable por cliente.
- **Responsabilidad:** la app extrae y propone; la interpretación y la firma son del geotécnico
  (DGGT Empf. Nr. 4). Dejarlo en las condiciones de uso y en la UI (estado "no aprobado").
- **Normas DIN:** no reproducir textos de normas; los patrones se toman de la leyenda de cada
  documento.

Up: [Índice](README.md)

Related: [08 swissgeol](08_swissgeol_reutilizacion.md) · [11 Decisiones](11_decisiones.md) · [12 Corpus](12_corpus_publico.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md) · [22 En línea](22_despliegue.md)
