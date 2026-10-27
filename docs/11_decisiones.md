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
| D16 | **Corpus de prueba con Gutachten públicos** (B-Pläne, UVP-Verbund, transparencia); en el repo sólo manifest y verdad, nunca los PDFs | No hay Gutachten propios disponibles; publicados hay muchos | 16 candidatos en 8 Länder ([12](12_corpus_publico.md)); descarga bloqueada por la red del entorno | Decidido (2026-10-25) |
| D17 | **Uso interno primero**; para terceros, decidir entre AGPL / licencia Artifex / pypdfium2 cuando haya caso de negocio | Evitar costes y decisiones prematuras | [14](14_licencias_terceros.md) | Decidido (2026-10-25) |
| D18 | **Todo PyMuPDF detrás de una capa de primitivas** propia | Hace barato cambiar a pypdfium2 (BSD/Apache) | pypdfium2 da los mismos 30 paths con estilo ([14 §3](14_licencias_terceros.md#3-prueba-se-puede-sustituir-pymupdf)) | Verificado (sintético) |
| D19 | **Colaborar con swisstopo** empezando por issues con reproductores sintéticos y un correo; contribuir piezas pequeñas | Beneficio mutuo, bajo riesgo | Borradores en [13](13_colaboracion_swisstopo.md) | Propuesta (envía el equipo) |
| D20 | **Geometría reducida a segmentos** y columna = par de verticales con trazo | Los PDFs regenerados (Ghostscript/PDF24) no tienen rectángulos ni rellenos | Wachenroth 18/18 sólo así ([15](15_resultados_pdfs_reales.md)) | Verificado (real) |
| D21 | **Normalizar la rotación** de página antes de todo | Páginas `/Rotate 90` dan coordenadas sin rotar | Talheim ([15](15_resultados_pdfs_reales.md)) | Verificado (real) |
| D22 | **Escala = candidato que más etiquetas confirma**, sólo escalas normalizadas; etiquetas pueden estar desplazadas y marcar techo o base | Posición de la etiqueta no es fiable entre oficinas | Talheim 65/65; tabla "B 6" descartada ([15](15_resultados_pdfs_reales.md)) | Verificado (real) |
| D23 | **Verdad real en el repo como JSON factual** (con URL y `sha256`), PDFs fuera | Medir sin redistribuir obras ajenas | `spikes/korpus/groundtruth/` | Decidido |
| D24 | Cifras de v3 = conjunto de entrenamiento; **la siguiente ronda se mide sin tocar el código** | Evitar autoengaño | [15](15_resultados_pdfs_reales.md) | Decidido; aplicado en la prueba ciega |
| D25 | **Prueba ciega con predicciones congeladas** en cada ronda nueva | La única medida honesta de generalidad | v3 ciego: 0/13 ([15 §6](15_resultados_pdfs_reales.md#6-prueba-ciega-hausham-y-rednitzhembach)) | Decidido |
| D26 | **Híbrido:** detección de etiquetas tolerante a formatos (como swissgeol) + validación geométrica propia | swissgeol generalizó mejor en profundidades (13/13 ciego) pero inventó 18 sondeos y no leyó cotas; v3 al revés | [15 §6.4](15_resultados_pdfs_reales.md#64-consecuencia-para-la-arquitectura) | Propuesta |
| D27 | **Escaneos por la misma lógica**: segmentos desde la imagen (OpenCV) + capa OCR | Evitar un segundo pipeline | Rednitzhembach 4/4 · 15/15 tras el adaptador | Verificado (entrenamiento) |
| D28 | Escala no normalizada válida si ≥ 80 % de ≥ 3 etiquetas la confirman (revisa D22) | DC-Software ajusta la escala a la hoja | Hausham RKS M ≈ 1:35 | Verificado (entrenamiento) |
| D29 | **Predicciones congeladas se suben al repo antes de abrir los PDFs** (con `sha256`) | El historial de git demuestra el orden congelar → verdad | `spikes/korpus/frozen/runde3/`; v3 ciego 11/29 ([15 §7](15_resultados_pdfs_reales.md#7-prueba-ciega-3-triefenstein-marl-wesel-y-berlín)) | Decidido; aplicado en la ronda 3 |
| D30 | **Schichtenverzeichnis (DIN 4022) como segunda fuente** y contraste 1:1 con el perfil | Formulario normado, en texto aunque el dibujo sea imagen o SHX | Wesel 24/24 sólo desde ahí; "SV ok" en 14/14 sondeos | Verificado (entrenamiento) |
| D31 | **Ejes en progresión aritmética no son etiquetas** (regla, eje DPH), como hace swissgeol | Un eje DPH en el corte suplantó un sondeo | Marl BS 10 | Verificado (entrenamiento) |
| D32 | **OCR como componente del pipeline** para raster sin texto y dibujos con texto SHX | 12 de los 18 sondeos perdidos en la ronda 3 no tenían texto legible | Berlín 0/11 → 7/11 con RapidOCR (ONNX, Apache-2.0) | Verificado (entrenamiento) |
| D33 | **Memoria explícita**: lecciones como reglas en [16](16_lecciones_aprendidas.md) y `CLAUDE.md` en la raíz | Que ninguna persona o agente repita un error ya pagado | 40+ reglas con evidencia | Decidido (2026-10-26) |
| D34 | **Banco de pruebas en tres capas**: PDFs reales con verdad, un caso de estrés por lección y sintéticos; línea base que falla ante cualquier empeoramiento | Atrapó 3 regresiones propias esta noche | [`regression.py`](../spikes/korpus/regression.py) | Decidido |
| D35 | **Perturbaciones** (girar, escalar, rasterizar) de los PDFs con verdad | Encuentran fallos invisibles en los originales | Girar destapó el fallo de rotación del lector de SV | Decidido |
| D36 | **Valor impreso** como profundidad de un límite confirmado (T2) | La geometría tiene ±1 pt de error | Exactos 414 → 509 de 515 | Verificado (entrenamiento) |
| D37 | **Especificación del algoritmo por etapas** con reglas conmutables (`RULES`) para ablación | Precisar qué hace cada regla y medirla | [17](17_algoritmo_extraccion.md) | Decidido |
| D38 | **JSON canónico** como único contrato entre extracción, Supabase e IFC | Una sola forma de los datos con procedencia y confianza | PostGIS y That Open cargan el mismo JSON | Verificado (real: Berlín) |
| D39 | **Unidades de modelo automáticas por alineamiento de secuencias** (clase + cota, programación dinámica con acuñamiento, lente y censura) | Que las Bodenschichten salgan sin dibujar a mano; misma clase a otra cota = otra unidad | Berlín: Sand 1 / Kies 1 / Sand 2 / Kies 2 / Sand 3; 28 pruebas ([18](18_modelador_capas.md)) | Verificado (sintético + real) |
| D40 | **Bajo la Endteufe = desconocido, no ausente** (contacto censurado: base ≤ Endteufe − 0,5 m) | Un sondeo corto no prueba que falten las unidades profundas | Caso `zensiert`; Berlín 3 sondeos de 8 m | Decidido |
| D41 | **Sondeos como nodos de la malla e interpoladores exactos** | El modelo debe respetar cada dato | Desviación 0,0 m en todos los casos | Verificado |
| D42 | **Extensión de unidades parciales por indicador de presencia** (termina a medio camino de sondeos sin ella) | Con IDW una lente de un sondeo quedaba bajo todo el solar | Volumen de lente ×6,3 → ×1,9; cuñas 0,89 → 0,68 | Decidido (compromiso medido) |
| D43 | **El geotécnico confirma las unidades** con `einheiten.json` (plantilla en el informe) | La correlación automática no distingue arenas de distinto origen | Prueba con "Sande und Kiese" | Decidido |
| D44 | **`services/modeler` y `apps/web`** como primeros componentes de la estructura objetivo ([arquitectura §10](ARQUITECTURA_BAUGRUNDMODELL.md#10-estructura-de-repositorio-propuesta)) | Ya no son spikes: tienen pruebas y contrato (JSON → IFC) | — | Decidido |
| D45 | Visor **sin dependencias de red** (WASM y worker locales) y **web-ifc 0.0.77** fijado | 0.0.78 trae un WASM de navegador que no casa con su JS | Error `StreamMeshes … 4 arguments, expected 3` | Verificado |
| D46 | **App v2 = página principal de Streamlit**: PDF → extracción v4 → revisión → modelo → visor, todo automático; la v1 (Excel) queda como segunda página | El objetivo es el Baugrundmodell, no la hoja Excel de un layout | 4 flujos de punta a punta verificados ([19](19_app_v2.md)) | Verificado (Linux) |
| D47 | **Visor como componente Streamlit** con el `dist` compilado **en el repo**; IFC servido por URL con nombre = hash | Arranca sin Node; el IFC no viaja por el websocket en cada rerun | `ui/viewer.py` | Decidido |
| D48 | **Fila esquemática por defecto** si ningún sondeo tiene coordenadas; GOK = 0 si ninguno tiene GOK; siempre marcado | Casi ningún PDF trae coordenadas; sin esto no hay modelo "automático" | Talheim: 8 sondeos, 6 unidades, avisos en app/IFC/visor | Decidido |
| D49 | **Correcciones del usuario en la misma tabla** y marcadas (`manuell`); nunca sobrescriben el JSON de extracción | Trazabilidad: qué vino del PDF y qué puso una persona | Prueba `test_manuelle_korrektur_wird_markiert` | Decidido |
| D50 | **Correlación por el menor entre distancia en cota y en profundidad** | Con relieve las capas superficiales siguen el terreno | Talheim 15 → 6 unidades; sintéticos sin cambio | Verificado |
| D51 | **Extracción cacheada en disco** por `sha256` + OCR + huella del extractor; progreso envolviendo `primitives()` | Rerun inmediato sin tocar el extractor de referencia | `ui/pipeline.py` | Decidido |
| D52 | **Arranque en Windows con `start.bat`** (venv, requisitos, OCR opcional, navegador) | El usuario trabaja en Windows; nada de pasos manuales | No probado en Windows desde aquí | Propuesta (a validar) |

## Preguntas abiertas

1. ~~¿Quién aporta muestras?~~ → corpus público ([12](12_corpus_publico.md), D16). 3 recibidos
   ([15](15_resultados_pdfs_reales.md)); faltan 5–7 no vistos (subirlos o permitir los dominios).
2. ~~¿Uso interno o terceros?~~ → interno primero, terceros más adelante (D17, D18, [14](14_licencias_terceros.md)).
3. ¿Hay Lageplan, tabla de coordenadas o LandXML del eje en los proyectos? ([07](07_coordenadas.md))
4. ¿Quién envía los issues y el correo a swisstopo, y en nombre de qué organización? ([13](13_colaboracion_swisstopo.md))

Up: [Índice](README.md)

Related: [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md) · [10 Plan](10_plan_implementacion.md) · [09 Validación](09_validacion_benchmark.md) · [18 Modelador de capas](18_modelador_capas.md)
