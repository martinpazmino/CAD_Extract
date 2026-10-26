---
title: "Lecciones aprendidas (memoria del proyecto)"
date: 2026-10-26
tags: [lecciones, memoria, extraccion, validacion]
aliases: [Lessons learned, Lecciones, Memoria]
---

# Lecciones aprendidas (memoria del proyecto)

**Para qué sirve esta nota:** todo lo aprendido, escrito como **reglas explícitas** que cualquier
persona (o agente) debe respetar al tocar la extracción. Cada regla dice qué hacer, por qué
(evidencia) y qué prueba la vigila. Si una regla deja de cumplirse, una prueba debe ponerse roja.

**Objetivo del proyecto (no perderlo de vista):** desde un Bodengutachten en PDF, construir el
**Baugrundmodell**: datos de sondeos validados y trazables → Supabase → geometrías IFC 4.3 en
That Open Engine ([Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md)). La extracción no es el fin:
importa que cada dato llegue al modelo **con su procedencia y su confianza**, y que un dato
dudoso quede **marcado**, nunca escondido.

> [!IMPORTANT]
> Las reglas L1–L18 vienen de PDFs reales ([15](15_resultados_pdfs_reales.md)). Las cifras
> después de cada corrección son de entrenamiento; las rondas ciegas dieron **0/13** y **11/29**.
> Una regla nueva sólo se acepta si no rompe el conjunto de regresión (§P5).

## P. Proceso y medición

| # | Regla | Por qué / evidencia |
|---|---|---|
| P1 | **Medir a ciegas antes de corregir.** Congelar predicciones de todo PDF nuevo antes de abrirlo | v3 sacó 29/29 en entrenamiento y **0/13** en la primera ronda ciega ([15 §6](15_resultados_pdfs_reales.md#6-prueba-ciega-hausham-y-rednitzhembach)) |
| P2 | **Subir las predicciones congeladas al repo** (con `sha256` del PDF y revisión del código) **antes** de transcribir la verdad | El historial de git demuestra el orden; ronda 3: `5325ead`/`2d4d5e7` → verdad `acc5cd5` (D29) |
| P3 | Separar siempre **cifras ciegas** de **cifras de entrenamiento** en todo informe | Evita el autoengaño (D24) |
| P4 | La métrica principal es el **error silencioso**: un dato erróneo marcado como seguro. Un sondeo falso es peor que uno no encontrado | v1 marcaba en verde Bodenarten erróneas ([01](01_diagnostico_layout_fijo.md)); swissgeol inventó 55 sondeos en 9 PDFs |
| P5 | **Todo cambio se mide contra el conjunto completo** (PDFs reales + sintéticos) antes de subirlo | Una regla de la ronda 3 rompió B 4 de Rednitzhembach y sólo el conjunto de regresión lo detectó |
| P6 | Una regla nueva debe ser **general** (describir un rasgo del dibujo), nunca una excepción por PDF, oficina o coordenada | Las posiciones fijas de v1 son la causa raíz de su 0/58 |
| P7 | La verdad se transcribe **de la imagen** y se coteja con una segunda fuente (Schichtenverzeichnis, informe) cuando exista | El Schichtenverzeichnis confirmó 14/14 sondeos transcritos |
| P8 | Los PDFs **no** se suben al repo; sólo URL, `sha256` y datos factuales | Uso interno de obras ajenas (D16, D23) |
| P9 | **Perturbar los PDFs que ya funcionan** (girar, escalar, rasterizar) con la misma verdad: encuentra fallos que los originales esconden | Girar Wesel destapó que el lector del Schichtenverzeichnis usaba coordenadas sin rotar |
| P10 | **Ablación**: apagar cada regla y ver qué caso empeora. Una regla que no empeora nada no está protegida por ningún test | [`ablation.py`](../spikes/korpus/ablation.py) |
| P11 | Un **caso de estrés por lección**: el fallo real se convierte en un PDF mínimo que lo reproduce | [`stress_cases.py`](../spikes/extraktion_v2/stress_cases.py), 13 casos |
| P12 | Medir también la **precisión al centímetro** (límites exactos), no sólo la tolerancia de 5 cm | v3 414/515 exactos, v4 509/515 tras T2 |

## E. Entrada: qué tipo de PDF es

| # | Regla | Evidencia |
|---|---|---|
| L1 | No asumir rectángulos ni rellenos: **reducir todo a segmentos** | Ghostscript/PDF24 dejó Wachenroth en 965 segmentos sueltos |
| L2 | **Normalizar la rotación** (`page.rotation_matrix`) de palabras y paths antes de cualquier geometría | Talheim (`/Rotate 90`), Marl S.19, Wesel S.17 (`/Rotate 270`) |
| L11 | **Escaneo = misma lógica**: segmentos desde la imagen (OpenCV) y texto desde la capa OCR | Rednitzhembach 4/4 tras el adaptador raster |
| L17 | **AutoCAD con fuentes SHX**: el texto del dibujo son líneas; no hay capa de texto aunque sea vectorial. Detectarlo (muchos paths, casi sin palabras) y pasar por OCR | Wesel S.17: 1389 paths, 18 "palabras" sueltas |
| L18 | **Raster sin capa de texto** (capturas de portales, escaneos de archivo): hace falta OCR propio | Berlín: 11 sondeos en imágenes; OCR (RapidOCR) lee profundidades y cotas con confianza 0,6–0,9 |
| E1 | Clasificar cada página **antes** de extraer: vector+texto · vector sin texto (SHX) · raster+OCR · raster sin texto | Las cuatro clases aparecieron en 9 Gutachten |
| E2 | Un escaneo puede traer **ruido vectorial** (cientos de paths del software de OCR): con imagen > 80 % es escaneo igual, y se usan segmentos de imagen **y** vectoriales | KB5 suizo: 220 paths |
| E3 | **Todo módulo toma las primitivas de la misma capa normalizada** (E1); nunca `page.get_text()` directo | El lector del SV falló en páginas giradas por saltarse la rotación |
| L18b | La capa OCR de un escaneo **pierde texto** ("2 / I", etiquetas de B 4): complementarla con OCR propio donde no hay palabras | A7367, Rednitzhembach |
| E4 | El OCR lee la Schraffur de Kies (círculos) como `000`: no contar esos tokens como texto | Caso s12 |
| E5 | El tamaño de página de un escaneo **no** es el del papel: el `M 1:100` del cajetín no da la escala en puntos PDF; mandan las etiquetas | KB5 |

## G. Geometría: columna y límites

| # | Regla | Evidencia |
|---|---|---|
| G1 | Columna = **par de verticales con trazo**, ancho 8–80 pt, alto ≥ 2,5 × ancho | Funciona en 7 oficinas distintas |
| G2 | Límite = horizontal **continua** (no discontinua) que toca **ambos bordes** (±0,6 pt; escaneo ±1,6 pt) | L6: la Schraffur de Ton y la doble línea de Schwarzdecke cruzaban la columna |
| G3 | Columnas anidadas (franja interior, tubo de GWM): quedarse con la de **bordes más gruesos** | Talheim GWM |
| G4 | Una columna con números dentro es una **tabla**, no un sondeo | L5: tabla "B 6" de Wachenroth a M 1:12 |
| G5 | Cada límite debe estar **confirmado 1:1 por una etiqueta**; si no, se marca (no se borra) | Talheim BK5: 1 límite extra marcado |

## T. Etiquetas, escala y cabeceras

| # | Regla | Evidencia |
|---|---|---|
| L3 | La **posición** de la etiqueta no es fiable (desplazada, encima, debajo); unas oficinas rotulan el **techo** (con 0,00), otras la **base**. La escala se elige por **cuántas etiquetas confirma** cada candidato (directa, por orden, texto `1:75`) | Talheim 65/65 |
| L8 | Etiquetas con unidad pegada (`0.20m`), coma o punto decimal | Hausham (DC-Software) |
| L9 | Escalas no normalizadas existen (perfil ajustado a la hoja, M ≈ 1:35; Triefenstein 1:30): válidas si ≥ 80 % de ≥ 3 etiquetas las confirman | Hausham RKS, Triefenstein |
| L14 | Un grupo de valores en **progresión aritmética** (≥ 5 valores, mismo paso) es un **eje** (regla de cotas, escala de un diagrama DPH), nunca etiquetas de capa | Marl BS 10 se leyó del eje DPH del corte |
| L15 | Una columna de valores **en pares** (Von/Bis de muestras) no son etiquetas de capa | Marl (IDAT/GeoDin) |
| L15b | Columna sin ninguna etiqueta confirmada mientras las vecinas sí tienen → no es un perfil (p. ej. plano de ejecución de GWM). Si **ninguna** columna de la página tiene etiquetas (OCR perdido), se acepta la escala del cajetín y se marca | Marl GWM 10; Rednitzhembach B 4 |
| L4 | En la representación en altura la cabecera queda muy por encima de la columna: asociar cabecera con la columna **debajo**, sin límite vertical | Wachenroth corte, Talheim |
| L13 | La cabecera puede llevar **sufijo**: `RKS 1 - Betonweg 0+050`, `B 1 Bohrung Nr.` | Triefenstein 0/5 por esta causa |
| T1 | Códigos de terceros no siguen el patrón `B 1`: `422C-460`, `B 7/16`, `S 2a`, `DS 1/17`. La lista de prefijos debe ser **configurable** y ampliarse desde la leyenda y el Lageplan del propio documento | Berlín |
| L12 | El mismo sondeo aparece en hoja propia y en el corte: preferir la **hoja titulada** y con menos sondeos; la confirmación < 50 % no cuenta | Wachenroth B 2, Rednitzhembach B 4 |
| T2 | Un límite confirmado por etiqueta se entrega con el **valor impreso** (3,50), no con la geometría (3,49) | Precisión exacta 414 → 509 de 515 |
| T3 | Hoja con **una sola cabecera**: se ancla a la columna con más etiquetas aunque la cabecera esté lejos (formularios con cabecera centrada) | KB5 |
| T4 | Si las líneas no cuadran pero las etiquetas forman una **recta limpia** con escala normalizada: los límites son las etiquetas, las líneas sólo confirman | KB5 (Schraffur raster crea líneas de más) |
| T5 | Una columna con ≥ 3 profundidades **dentro** es la columna de profundidades del formulario, no el perfil | KB5 |

## B. Texto y Bodenart

| # | Regla | Evidencia |
|---|---|---|
| L7 | Clasificar por el **sustantivo** principal, no por subcadenas: `Sandstein` es roca, `Tonstein` roca, `Beton`/`Schwarzdecke` antrópicos, `Oberboden` = Mutterboden | v1: Sandstein→Sand, Beton→Ton marcados "seguros" |
| L16 | Si no hay sustantivo, usar la **abreviatura** DIN 4023 / EN ISO 14688 del inicio (`U, t, s´` → Schluff; `fS` → Sand; `A (S, u´)` → Auffüllung; `Gr`, `Sa`, `Si`, `Cl`) | Triefenstein, Marl |
| B1 | El texto puede venir con **líneas de referencia** (no centrado en la capa): asignar por la convención de etiquetas o por la línea guía, no sólo por la `y` | Marl BS 10: 5 capas sin Bodenart |
| B2 | Guardar siempre el **texto original** junto a la clase | Trazabilidad (modelo §5.1) |

## W. Agua

| # | Regla | Evidencia |
|---|---|---|
| W1 | El triángulo puede estar junto a la **columna vecina**; asigna el sondeo el extremo de la **línea de agua** | Talheim |
| L10 | No son agua: triángulos en serie alineada (regla de cotas), triángulo con una cota al lado, triángulo en la GOK | Hausham |
| L10b | El agua también llega como **texto**: `GW 2.53m`, `Wasserstand nach Sondierung 3,00 m`, `Wasseranschnitt 3.8`, "Ruhewasser" | Hausham, Triefenstein, Berlín |
| W2 | "kein Grundwasser", "trocken", "kein Wassereintritt" son **datos**, no ausencias | Wachenroth 6/6, Wesel |
| W3 | Falta: símbolos de la leyenda ("angebohrt" con dos trazos) | Talheim BK2 (único GW perdido del entrenamiento) |

## S. Segundas fuentes y contraste

| # | Regla | Evidencia |
|---|---|---|
| S1 | El **Schichtenverzeichnis** (formulario DIN 4022) es la fuente más estable: profundidad en la columna 1, denominación bajo `a)`, agua en la columna 3. Leerlo **siempre** y contrastarlo 1:1 con el perfil | Hausham 9/9 y Triefenstein 5/5 "SV ok"; Wesel 24/24 sólo desde ahí (D30) |
| S2 | Leer números de tablas **por celda** con sus palabras y bbox, nunca desde texto aplanado | `565 081,64` salió como `"56508164\n,"` ([07](07_coordenadas.md)) |
| S3 | El título de un formulario puede estar **espaciado** (`S c h i c h t e n v e r z e i c h n i s`) y el texto **duplicado** (dos capas): normalizar antes de buscar | Wesel |
| S4 | Las Rammsondierungen pueden venir como **tabla de valores** (N10 cada 10 cm) en lugar de curva | Triefenstein S.32–35 |
| S5 | Las coordenadas aparecen en tablas, en cajetines de portales (`Rechtswert (UTM 33N): 394774,3`) o en el Lageplan; sin ellas no hay 3D real | Berlín (en imagen), Halle (tabla de GW 26/26) |
| S6 | El perfil puede ser **sólo una tabla de texto** (Tiefe \| Beschreibung) sin columna gráfica; aceptarla sólo si ≥ 60 % de los intervalos dan una Bodenart (las tablas DPH y de laboratorio no) | A7367 (Suiza) |
| S7 | Etiqueta y valor del cajetín pueden ser **bloques separados** en la misma fila (`Höhe in m ü.M.:` · `668.99`): unir por fila antes de buscar | A7367 |

## R. swissgeol: qué copiar y qué no

| # | Regla | Evidencia |
|---|---|---|
| R1 | Copiar su **tolerancia de formatos** en etiquetas (unidades, OCR, posiciones) y la exclusión de progresiones aritméticas | swissgeol 13/13 en la ronda ciega 2 donde v3 sacó 0 |
| R2 | No copiar su asignación de sondeos sin validación geométrica: genera **muchos falsos** y no lee cotas alemanas | 55 sondeos falsos y 6/50 GOK en 9 PDFs |
| R3 | Licencia AGPL (como PyMuPDF): uso interno sin problema; para terceros, capa de primitivas propia (D17, D18) | [14](14_licencias_terceros.md) |

## M. Modelo, IFC y That Open

| # | Regla | Evidencia |
|---|---|---|
| M1 | IFC 4.3: `IfcBorehole` ⊃ `IfcGeotechnicalStratum`; modelo en `IfcGeomodel`; georreferencia con `IfcMapConversion` + `IfcProjectedCRS` | Spike validado sin errores de esquema |
| M2 | El `IfcImporter` de That Open **descarta** las clases geotécnicas por defecto: añadir `IFCBOREHOLE`, `IFCGEOMODEL`, `IFCGEOTECHNICALSTRATUM` a `importer.classes.elements` | 0 → 16 elementos con geometría |
| M3 | Encapsular el escritor IFC: IFC 4.4 sustituye `IfcGeotechnicalStratum` por `IfcGeoScienceFeature` | Borrador 4.4 |
| M4 | Sin coordenadas, el modelo de sección (estación, NHN) ya aporta valor; con coordenadas locales del Lageplan se puede montar un 3D relativo | [Arquitectura §7.1](ARQUITECTURA_BAUGRUNDMODELL.md#71-escalera-de-niveles-cada-uno-es-entregable) |
| M5 | Un **Pset vacío** es IFC inválido: crear el Pset sólo si hay valores | Exportador: 5 errores de esquema → 0 |
| M6 | PostGIS instalado en `extensions`: **cualificar** `extensions.geometry`, si no la migración sólo funciona dentro de Supabase | [Spike Supabase](../spikes/supabase/README.md) |
| M7 | La cadena completa ya funciona con un PDF real: OCR → JSON canónico → PostGIS → IFC 4.3 georreferenciado → That Open (80 estratos) | Berlín ([15 §8](15_resultados_pdfs_reales.md)) |

## X. Entorno de trabajo

| # | Regla | Evidencia |
|---|---|---|
| X1 | En el entorno de Claude la descarga de Gutachten de webs municipales está **bloqueada** (403/000); pypi y GitHub sí. Los PDFs los sube el usuario | Rondas 1–3 |
| X2 | Probar dependencias pesadas (swissgeol, OCR) en **entornos separados** del scratchpad; swissgeol fija PyMuPDF 1.26.3 | `sgvenv` |
| X3 | `pkill -f patrón` en un comando que contiene ese texto en cualquier parte **se mata a sí mismo** (también con `[p]atrón` si el nombre aparece después en el mismo comando): ejecutar `pkill` en un comando aparte | Exit 144 tres veces |
| X4 | `python -I` no añade la carpeta del script a `sys.path`: los scripts deben insertarla ellos mismos | `ablation.py` |
| X5 | `show_pdf_page` ignora el `/Rotate` de la página origen; compensar al recomponer PDFs | Primera versión de `perturb.py` |
| X6 | OCR caro → **caché por imagen de página** (hash) para que la regresión y la ablación sean rápidas | `GEO_OCR_CACHE` |

Up: [Índice](README.md)

Related: [15 Resultados reales](15_resultados_pdfs_reales.md) · [11 Decisiones](11_decisiones.md) · [09 Validación](09_validacion_benchmark.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md)
