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
| D53 | **Visor con los controles del TwinBimM del usuario** (BUI oscuro W&F, barra Sichtbarkeit/Auswahl, ViewCube, engranaje, ⌖ Koord., Highlighter/Hider, posproducción) | Lo que el usuario ya maneja; misma librería That Open | [20 §1](20_lage_pruefung_viewer.md#1-controles-del-visor-como-twinbimm) | Decidido |
| D54 | **IFC en metros con unidad explícita** (`assign_unit` sin argumentos pone mm) | El modelo salía 1000× pequeño en todo visor y la georreferencia mal | Prueba `calculate_unit_scale == 1` | Verificado |
| D55 | **Cámara para modelos grandes**: near/far en cada movimiento, rejilla según escena, render bajo demanda con posproducción sólo en reposo | near/far fijos 1/1000 cortaban todo lo > 1 km; navegación fluida | Trasse 6 km: far 24,6 km, near 0,02 m de cerca | Verificado |
| D56 | **Marco del visor = IFC local al origen fijo del proyecto**, cargado sin `COORDINATE_TO_ORIGIN` | Chinchetas, plano e IFC deben coincidir al cm | BK 1 de la trasse exacto | Verificado |
| D57 | **Lage a mano en el visor sobre el PDF del plano** (imagen PyMuPDF), calibración por 2 puntos (semejanza / afín por ejes), eventos numerados con firma de proyecto | Casi ningún Gutachten trae coordenadas en el perfil; sí un Lageplan o un Längsschnitt | Plano: ≤ 0,45 m; Schnitt: ≤ 0,01 m ([20 §3](20_lage_pruefung_viewer.md#3-lage-sondeos-sobre-el-plano-antes-de-modelar)) | Verificado |
| D58 | **Estado del proyecto aparte de la extracción** (`ui/projekt.py`) y guardado automático por firma | Trazabilidad (qué vino del PDF, qué puso una persona) y no perder horas de revisión | 15 pruebas de la app | Decidido |
| D59 | **Tablas antes del modelo, botón *Erzeugen*, después nachführen automático**; las marcas de revisión no entran en la clave de geometría | Petición del usuario; marcar 50 capas no debe recalcular 50 veces | E2E 7/7 | Verificado |
| D60 | **Prüfstand + Einchecken** con contadores y huella del modelo; IFC con `Geprueft`/`Korrigiert`/`Pruefstand` generado al descargar | "Einchecken de la confidence": estado de revisión fechado y comprobable | `test_einchecken`, E2E | Decidido |
| D61 | **Delimitación = envolvente convexa + buffer** (auto 5–100 m, a mano hasta 5 km) con presupuesto de 30 000 nodos también para raster manual | Modelos > 5 km sin agotar memoria | `test_grosse_modellgrenze_von_hand` | Decidido |
| D62 | **Página con esqueleto fijo de contenedores** | Un elemento nuevo encima del componente lo volvía a montar (X13) | E2E: *Erzeugen* sin remontar | Verificado |
| D63 | **App por pasos a pantalla completa (FastAPI + página web con el visor integrado)** en vez de Streamlit; Streamlit sólo para Excel v1 | Petición del usuario ("como una historia con pasos"); navegación estable sin reruns; un proceso, un puerto, sin Node | [21 §1](21_app_schritte_normen.md#1-arranque-y-arquitectura); E2E 19/19 | Verificado |
| D64 | **Avisos = capas sin clasificar** (y sin revisar), no confianza baja | Petición del usuario: lo que hay que mirar es lo que no se pudo extraer | `test_warnung_bei_unklassifizierten_schichten_und_vorschlag` | Decidido |
| D65 | **Mini base de datos de normas** (DIN 4023, EN ISO 14688-1, DIN 18196) con evidencia por entrada (`DIN4023`/`praxis`/`darstellung`); lee cada descripción; la propuesta para una capa sin clasificar sólo se aplica con un clic | Las abreviaturas son casi siempre las mismas; sin el texto de la norma (de pago) hay que decir de dónde viene cada dato | 19 pruebas; 13 rellenos de Berlín marcados ([21 §3](21_app_schritte_normen.md#3-mini-base-de-datos-de-normas)) | Decidido |
| D66 | **Colores DIN 4023** en modelador, IFC, visor y app (Kies amarillo, Sand naranja, Schluff oliva, Ton violeta, Mudde lila …) | Los anteriores contradecían la norma (Kies/Sand cambiados) | `test_farben_nach_din_4023` | Decidido |
| D67 | **Calibración nueva**: escala por distancia medida (o 1:n) + punto de referencia con coordenada + giro (plano) / escala vertical (sección) + **candado**; sustituye los dos puntos de pase de D57; las calibraciones antiguas se convierten | Petición del usuario; más fácil de entender y de comprobar (1:n visible) | UI: 1:500 · 10,0° exacto; marcas 0,3 px | Verificado |
| D68 | **Arrastre de sondeos sólo con el plano bloqueado; en el plano x/y; en la sección la altura sólo sin GOK del PDF** (regla también en el servidor) | Petición del usuario; una GOK medida no se toca con el ratón | `check.mjs` C, `test_gok_nur_ohne_gok_aus_dem_pdf_verschiebbar` | Verificado |
| D69 | **Diámetro de las columnas** por proyecto y por sondeo; automático `clamp(extensión/300, 0,8, 12)` m; mismo valor en visor e IFC (`CPset_Darstellung`) | Petición del usuario; columnas visibles en una trasse de 6 km | `test_durchmesser_projekt_und_je_bohrung` | Decidido |
| D70 | **IFC con la descripción y su lectura por norma en cada capa** (`CPset_Bodenansprache`) y las descripciones de cada unidad (`CPset_Modelleinheit.Beschreibungen`), textos largos como `IfcText` | Trazabilidad completa en el modelo, no sólo en la app | IFC válido sin errores | Verificado |
| D71 | **Barra del visor sólo con iconos** (grupos propios, no `bim-toolbar-section`) y **ayuda "?" en cada ajuste** | Petición del usuario: la barra no cabía; cada ajuste debe explicarse | ~460 px; M26 | Verificado |
| D72 | **Subir una extracción en JSON** además de PDFs | Reabrir extracciones exportadas o hechas por línea de comandos | `test_extraktion_als_json_hochladen` | Decidido |
| D73 | **El visor decide la posproducción**: imagen simple mientras algo se mueve (cámara, carga, arrastre), un fotograma con sombras al terminar, **nunca en Lage**; sin redibujar por mover el ratón; GTAO sigue la proyección | El plano parpadeaba y salía negro en la GPU del usuario (M29, M30) | `check.mjs` B (0 de 14 fotogramas con posproducción), `check_app.mjs` C2 (0 de 31) | Verificado |
| D74 | **Origen del proyecto desde el punto de referencia** del plano calibrado si ningún sondeo tiene posición; la cámara acompaña los cambios de origen y los saltos del plano en la vista previa | Sin esto el primer sondeo soltado movía el origen 6000 km y plano y sondeos desaparecían (M31) | `test_ursprung_vom_bezugspunkt_wenn_keine_bohrung_lage_hat`, `test_plan_ohne_koordinaten_nullpunkt_und_system_vom_plan`, C2 | Verificado |
| D75 | **EPSG como lista** (DE/AT/CH, 21 sistemas verificados con pyproj) con **aviso de plausibilidad** de Rechts-/Hochwert, no bloqueo; un código desconocido queda visible y marcado; el visor usa el EPSG del plano si los sondeos no traen ninguno | Petición del usuario; "EPSG 52" en el HUD (M33) | C2: R 74.848,90 → aviso; 565 000 → ✓ 25832 | Decidido |
| D76 | **Modo Lage con la navegación "Plan" de That Open**: el botón izquierdo desplaza el plano, no gira | En una vista desde arriba un giro accidental pierde el plano | C2 (desplazar sin perder la vista) | Decidido |

## Preguntas abiertas

1. ~~¿Quién aporta muestras?~~ → corpus público ([12](12_corpus_publico.md), D16). 3 recibidos
   ([15](15_resultados_pdfs_reales.md)); faltan 5–7 no vistos (subirlos o permitir los dominios).
2. ~~¿Uso interno o terceros?~~ → interno primero, terceros más adelante (D17, D18, [14](14_licencias_terceros.md)).
3. ¿Hay Lageplan, tabla de coordenadas o LandXML del eje en los proyectos? ([07](07_coordenadas.md)) → con
   Lageplan o Längsschnitt en PDF ya se colocan en el visor ([20](20_lage_pruefung_viewer.md), D57).
4. ¿Quién envía los issues y el correo a swisstopo, y en nombre de qué organización? ([13](13_colaboracion_swisstopo.md))

Up: [Índice](README.md)

Related: [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md) · [10 Plan](10_plan_implementacion.md) · [09 Validación](09_validacion_benchmark.md) · [18 Modelador de capas](18_modelador_capas.md) · [20 Lage y Prüfstand](20_lage_pruefung_viewer.md) · [21 App por pasos y normas](21_app_schritte_normen.md)
