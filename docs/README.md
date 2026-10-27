---
title: "Documentación Geo_Agent: índice"
date: 2026-10-23
tags: [indice, geo_agent]
aliases: [Índice, Mapa de documentos]
---

# Documentación Geo_Agent: índice

Punto de entrada. Objetivo del conjunto: pasar de "PDF → Excel para un plano concreto" a una
extracción **independiente del layout**, que recupere todos los datos del Bodengutachten y
alimente un **Baugrundmodell** (Supabase → IFC 4.3 → That Open).

> [!NOTE]
> Resumen en una frase: la extracción actual depende de posiciones y colores fijos; un
> enfoque geométrico/estadístico (probado en PDFs sintéticos), los algoritmos ya maduros de
> swissgeol para la estratigrafía textual y un banco de pruebas con error silencioso como KPI lo
> resuelven. Ver [11 Decisiones](11_decisiones.md).

## Visión general

- [Arquitectura y Baugrundmodell](ARQUITECTURA_BAUGRUNDMODELL.md): evaluación, benchmark de herramientas, arquitectura Supabase + workers + That Open, IFC 4.3; leer primero si se busca el panorama completo.
- [11 Decisiones y conclusiones](11_decisiones.md): todas las conclusiones en una tabla, con evidencia y estado; leer si sólo hay 5 minutos.

## Extracción: problema y solución

- [01 Diagnóstico: supuestos de layout fijos](01_diagnostico_layout_fijo.md): inventario con líneas de código y fallos medidos; leer para entender por qué falla con otra oficina.
- [02 Bohrprofil independiente del layout](02_bohrprofil_generalizacion.md): columnas por geometría, escala por regresión, descripción, fusión; el núcleo de la solución.
- [03 Längsschnitt sin constantes](03_laengsschnitt_generalizacion.md): ejes, túnel, geología vectorial; diseño para el segundo PDF.

## Datos que hoy se pierden

- [04 Schraffur DIN 4023](04_schraffur_din4023.md): la columna gráfica como segunda señal, clasificada con la leyenda.
- [05 Sondierungen DPH/CPT](05_sondierungen.md): digitalizar curvas con ejes calibrados.
- [06 Grundwasser](06_grundwasser.md): símbolo, palabras clave, color y líneas de agua.
- [07 Coordenadas y georreferencia](07_coordenadas.md): tablas, Lageplan, eje; CRS alemanes; desbloquea el 3D.

## Reutilización, medición y plan

- [08 swissgeol: qué reutilizar](08_swissgeol_reutilizacion.md): mapa de módulos, prueba sobre nuestros PDFs, estrategias y licencia.
- [09 Validación y benchmark](09_validacion_benchmark.md): resultados v1 / v2 / swissgeol, formato de verdad, corpus y métricas.
- [10 Plan de implementación](10_plan_implementacion.md): pasos 0–8 con archivos, criterios y esfuerzo.
- [12 Corpus real con Gutachten públicos](12_corpus_publico.md): de dónde sacar 5–10 PDFs reales, cómo evaluarlos sin verdad, uso legal.
- [13 Colaboración con swisstopo](13_colaboracion_swisstopo.md): qué nos dan y qué les damos, primeros pasos, borradores de issues y correo.
- [14 Licencias: interno hoy, terceros mañana](14_licencias_terceros.md): AGPL, opciones, prueba de pypdfium2, capa de primitivas.
- [15 Resultados con PDFs reales](15_resultados_pdfs_reales.md): v1 / v3 / swissgeol con 9 Gutachten públicos, dos pruebas ciegas (v3 0/13 y 11/29), dieciocho lecciones, Schichtenverzeichnis como segunda fuente, OCR como siguiente paso.
- [16 Lecciones aprendidas](16_lecciones_aprendidas.md): **memoria del proyecto**, todas las reglas explícitas (proceso, entrada, geometría, etiquetas, texto, agua, segundas fuentes, swissgeol, IFC/Supabase, entorno).
- [17 Algoritmo de extracción v4](17_algoritmo_extraccion.md): especificación por etapas E0–E9, parámetros y su origen, confianza y salida canónica.
- [18 Modelador de capas y visor That Open](18_modelador_capas.md): Bodenschichten automáticas (unidades por correlación, superficies, sólidos cerrados), IFC 4.3 y visor web; resultados contra verdad sintética y con Berlín.
- [Glosario alemán–español](glosario.md): términos geotécnicos y de swissgeol.

## Código de apoyo

- [Spike extracción v2](../spikes/extraktion_v2/README.md): generador de PDFs sintéticos, prototipo v2, comparativa v1/v2/swissgeol.
- [Spike IFC + That Open](../spikes/ifc_thatopen/README.md): IFC 4.3 geotécnico con IfcOpenShell y su importación en That Open.
- [Corpus público](../spikes/korpus/README.md): manifest, verdad, prueba ciega, regresión, ablación y perturbaciones.
- [Spike Supabase](../spikes/supabase/README.md): migración probada en PostGIS y cargador del JSON canónico.
- [Modelador `baugrundmodell`](../services/modeler/README.md): JSON canónico → unidades → sólidos → IFC 4.3 (`IfcGeomodel`), con pruebas.
- [Visor web](../apps/web/README.md): That Open Engine; unidades, propiedades, cortes, exageración vertical.

## Cómo leer

```
Arquitectura ─► 11 Decisiones
      │
      ▼
01 Diagnóstico ─► 02 Bohrprofil ─► 04 Schraffur
      │               │   └──────► 05 Sondierungen · 06 Grundwasser · 07 Coordenadas
      │               ▼
      └──────────► 03 Längsschnitt
08 swissgeol ─► 13 Colaboración swisstopo
      │              14 Licencias
      ▼
09 Validación ◄─ 12 Corpus público ─► 15 Resultados reales ─► 16 Lecciones · 17 Algoritmo
      ▼                                                               │
10 Plan                                                               ▼
                                                     18 Modelador de capas + visor That Open
```

Up: [README del repositorio](../README.md)
