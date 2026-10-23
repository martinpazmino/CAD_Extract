---
title: "Registro de decisiones y conclusiones"
date: 2026-10-23
tags: [decisiones, adr, conclusiones]
aliases: [Decisiones, ADR, Conclusiones]
---

# Registro de decisiones y conclusiones

Formato breve: decisión · por qué · evidencia · estado. "Propuesta" = falta confirmación del
equipo; "Verificado" = respaldado por una prueba en este repo.

| # | Decisión | Por qué | Evidencia | Estado |
|---|---|---|---|---|
| D1 | **Vector primero**: leer texto y paths del PDF CAD; OCR/raster sólo como fallback | Exactitud de cm, sin errores de OCR | v1 y v2 exactos en PDFs vectoriales | Vigente |
| D2 | **Relaciones en vez de posiciones**: columnas por geometría, escala por regresión, texto por alineación | Las posiciones fijas fallan con otro layout, a veces en silencio | v1: A3 6/18 (7 en verde), A4/B 0 %; v2: 102/102 ([01](01_diagnostico_layout_fijo.md), [02](02_bohrprofil_generalizacion.md)) | Verificado (sintético) |
| D3 | Los **límites de capa salen de la geometría**; las etiquetas los confirman | Dos señales independientes → confianza medible | Prototipo v2, campo `label_confirmed` | Verificado (sintético) |
| D4 | **Schraffur clasificada contra las muestras de la leyenda del propio documento** | Sin datos de entrenamiento; mismo estilo CAD | 101/102 y detección de la contradicción en A5 ([04](04_schraffur_din4023.md)) | Verificado (sintético) |
| D5 | **Bodenart = sustantivo principal**; adjetivos `-ig` nunca; sin "continuación" silenciosa | Era la causa de los errores en verde | A3 en v1 ([01](01_diagnostico_layout_fijo.md)) | Propuesta |
| D6 | **KPI principal = tasa de error silencioso** | Un error visible se corrige; uno verde llega al modelo | [09](09_validacion_benchmark.md) | Propuesta |
| D7 | Perfiles de layout = **pistas**, no posiciones | Generalidad sin perder el ajuste fino por oficina | [02 §7](02_bohrprofil_generalizacion.md#7-qué-queda-como-configuración-perfil) | Propuesta |
| D8 | swissgeol: **portar algoritmos + formato de verdad, usarlo como oráculo, contribuir upstream; no fork ni dependencia del núcleo** | Su núcleo estadístico es robusto; lo alemán/CAD falta; AGPL y API beta | 18/18 en A–A3, fallos en nombres/agua/CRS ([08](08_swissgeol_reutilizacion.md)) | Verificado (sintético) |
| D9 | Código de swissgeol **reimplementado y citado**, no copiado (salvo módulo AGPL aislado) | Mantener abierta la opción de licencia comercial de PyMuPDF | Licencia AGPL-3.0-only | Propuesta |
| D10 | **Coordenadas desde tablas/Lageplan/eje** con validación cruzada de GOK | Desbloquean el 3D; el Bohrprofil no las trae | 17/17 en tabla sintética; trampa de `tab.extract()` ([07](07_coordenadas.md)) | Verificado (tabla) |
| D11 | Números siempre desde **palabras con bbox**, nunca desde texto aplanado | `find_tables().extract()` rompió `565 081,64` | [07 §2](07_coordenadas.md#2-trampa-verificada-en-la-lectura-de-tablas) | Verificado |
| D12 | Längsschnitt: **polígonos vectoriales y colores desde su leyenda**, túnel por capa OCG/geometría/clic | Exactitud, rendimiento y `IfcGeoslice` directo | Diseño ([03](03_laengsschnitt_generalizacion.md)) | Propuesta |
| D13 | Sondierungen y agua como **datos de primera clase** (tablas propias) | Hoy se descartan y aportan al modelo | DPH ±0,4 N10, agua 17/17 ([05](05_sondierungen.md), [06](06_grundwasser.md)) | Verificado (sintético) |
| D14 | That Open: **añadir las clases geotécnicas a `importer.classes.elements`** | Por defecto el IfcImporter las descarta | Spike IFC ([arquitectura §8.2](ARQUITECTURA_BAUGRUNDMODELL.md#82-resultados-del-spike-verificado)) | Verificado |
| D15 | El LLM propone, la geometría decide | Evitar números inventados | [Arquitectura §6.9](ARQUITECTURA_BAUGRUNDMODELL.md#69-dónde-sí-y-dónde-no-usar-un-llm) | Propuesta |

## Preguntas abiertas

1. ¿Cuántas oficinas/plantillas hay que soportar y quién aporta muestras? (decide el paso 8 del
   [plan](10_plan_implementacion.md)).
2. ¿Uso interno o servicio para terceros? (decide D9 y la licencia de PyMuPDF).
3. ¿Hay Lageplan, tabla de coordenadas o LandXML del eje en los proyectos? ([07](07_coordenadas.md))
4. ¿Contactar ya a swisstopo para colaborar? ([08 §7](08_swissgeol_reutilizacion.md#7-plan-concreto))

Up: [Índice](README.md)

Related: [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md) · [10 Plan](10_plan_implementacion.md) · [09 Validación](09_validacion_benchmark.md)
