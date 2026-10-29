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
| P10 | **Ablación**: apagar cada regla y ver qué caso empeora. Una regla que no empeora nada no está protegida por ningún test | [`ablation.py`](../spikes/korpus/ablation.py): 22 de 28 reglas protegidas ([tabla](../spikes/korpus/ablation_v4.md)) |
| P11 | Un **caso de estrés por lección**: el fallo real se convierte en un PDF mínimo que lo reproduce. Escribir el caso para una regla sin protección suele destapar un fallo nuevo | [`stress_cases.py`](../spikes/extraktion_v2/stress_cases.py), 17 casos; s15 destapó el fallo de L14 |
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
| E5 | El tamaño de página de un escaneo (o de un PDF impreso reducido) **no** es el del papel: el `M 1:100` del cajetín no da la escala en puntos PDF; mandan las etiquetas. Si el cajetín las contradice, el sondeo sale **sin capas** y con aviso | KB5; perturbación al 70 %: límites falsos 57 → 2 |
| E7 | En raster, una columna dibujada sólo con **rellenos de color sin borde** no da líneas oscuras: hace falta detectar bordes entre colores (gradiente), no sólo umbral de negro | Perturbación raster de Hausham (DC-Software) |
| E6 | El OCR **pierde espacios** (`KeinWasser`, `RKS 1-Betonweg`, `GW2.53m`, `36,25mNHN`): todo patrón de texto debe aceptar espacios opcionales y no depender de `\b` entre letra y cifra | Perturbación raster: GW-Status 3/20 |

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
| L14 | Un grupo de valores en **progresión aritmética** es un **eje** (regla de cotas, escala de un diagrama DPH), no etiquetas de capa, **si** tiene paso redondo (0,1 · 0,25 · 0,3 · 0,5 · 1 m…) y ≥ 8 valores, o más valores que límites la columna. Capas de igual espesor (0,4 · 0,8 · 1,2…) siguen siendo etiquetas | Marl BS 10 (eje DPH); caso s15 (la primera versión de la regla borraba etiquetas reales) |
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
| B3 | Leer la descripción por **norma** con evidencia por dato (DIN 4023 / ISO 14688-1 / DIN 18196 / práctica / sólo color): preparar el texto (coma decimal ≠ separador, palabras pegadas `FeinsandbisMittelsand`, apóstrofos y sobrerrayas), principal = primer sustantivo o Kurzzeichen, *Auffüllung*/*Mutterboden*/nombre geológico + suelo = material; materiales extraños por **inicio de palabra** (`Toneisenstein` no es hierro) | [21 §3](21_app_schritte_normen.md#3-mini-base-de-datos-de-normas) |
| B4 | Lo que la norma lee distinto que la extracción se **marca**, no se cambia: "Sand/Auffullung" es relleno (13 capas de Berlín); `Mg` es ambiguo (Geschiebemergel / made ground); la Bodengruppe sólo si está escrita | Berlín, `test_normen.py` |

## W. Agua

| # | Regla | Evidencia |
|---|---|---|
| W1 | El triángulo puede estar junto a la **columna vecina**; asigna el sondeo el extremo de la **línea de agua** | Talheim |
| L10 | No son agua: triángulos en serie alineada (regla de cotas), triángulo con una cota al lado, triángulo en la GOK | Hausham |
| L10b | El agua también llega como **texto**: `GW 2.53m`, `Wasserstand nach Sondierung 3,00 m`, `Wasseranschnitt 3.8`, "Ruhewasser" | Hausham, Triefenstein, Berlín |
| W2 | "kein Grundwasser", "trocken", "kein Wassereintritt" son **datos**, no ausencias | Wachenroth 6/6, Wesel |
| W3 | Falta: símbolos de la leyenda ("angebohrt" con dos trazos) | Talheim BK2 (único GW perdido del entrenamiento) |
| W4 | Falta: el **símbolo de agua en raster** (▽ ▼ dibujados en un escaneo); hoy sólo se detecta como vector o como texto. Probado: contornos triangulares de OpenCV encuentran la Schraffur (146 GW falsos) y no el símbolo, ni siquiera exigiendo línea de agua → regla apagada; siguiente intento: plantilla del símbolo tomada de la leyenda | Perturbación raster: Hausham GW 4/4 → 0/4 |

## S. Segundas fuentes y contraste

| # | Regla | Evidencia |
|---|---|---|
| S1 | El **Schichtenverzeichnis** (formulario DIN 4022) es la fuente más estable: profundidad en la columna 1, denominación bajo `a)`, agua en la columna 3. Leerlo **siempre** y contrastarlo 1:1 con el perfil | Hausham 9/9 y Triefenstein 5/5 "SV ok"; Wesel 24/24 sólo desde ahí (D30) |
| S2 | Leer números de tablas **por celda** con sus palabras y bbox, nunca desde texto aplanado | `565 081,64` salió como `"56508164\n,"` ([07](07_coordenadas.md)) |
| S3 | El título de un formulario puede estar **espaciado** (`S c h i c h t e n v e r z e i c h n i s`) y el texto **duplicado** (dos capas): normalizar antes de buscar | Wesel |
| S4 | Las Rammsondierungen pueden venir como **tabla de valores** (N10 cada 10 cm) en lugar de curva | Triefenstein S.32–35 |
| S5 | Las coordenadas aparecen en tablas, en cajetines de portales (`Rechtswert (UTM 33N): 394774,3`) o en el Lageplan; sin ellas no hay 3D real | Berlín (en imagen), Halle (tabla de GW 26/26) |
| S6 | El perfil puede ser **sólo una tabla de texto** (Tiefe \| Beschreibung) sin columna gráfica; aceptarla sólo si ≥ 60 % de los intervalos dan una Bodenart (las tablas DPH y de laboratorio no) | A7367 (Suiza) |
| S8 | El Schichtenverzeichnis **escaneado** se lee igual por OCR si el lector usa las primitivas comunes: el OCR pega el marcador al texto (`a)Auffullung`), quita diéresis (`Auffullung`) y espacios (`B1` en una página, `B 1` en otra): comparar códigos **normalizados** y aceptar formas sin diéresis | Perturbación raster: Triefenstein 0/5 → 5/5, Wesel 0/24 → 24/24 |
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
| M8 | **Bajo la Endteufe es desconocido, no ausente**: tratarlo como ausencia acuña las unidades profundas en cada sondeo corto | Caso `zensiert`, Berlín ([18](18_modelador_capas.md)) |
| M9 | La misma Bodenart a otra cota es **otra unidad** (Sand 1 / Sand 2): correlacionar por clase **y** cota, no sólo por nombre | Berlín 422C-461: dos niveles de Kies |
| M10 | Una lente que falta dentro de un Abschnitt continuo: el límite es **libre** dentro del Abschnitt; colocarlo en la mitad interpolada de la lente, no en un límite de capa | Caso `linse`, Berlín 422C-460 |
| M11 | Sondeos como **nodos** de la malla + interpolador exacto ⇒ el modelo reproduce cada contacto (comprobarlo siempre: desviación máxima en el informe) | 0,0 m en todos los casos |
| M12 | IDW sólo llega a 0 en los propios sondeos: una unidad vista en un sondeo se extiende fina bajo todo el solar. Limitar la extensión (indicador de presencia) | Volumen de lente ×6,3 → ×1,9 |
| M13 | Umbrales de espesor en las **superficies**, no sólo en la malla: si no, el volumen del IFC y el del modelo difieren | La prueba de volumen lo detectó (5 m³) |
| M14 | Para leer geología hace falta **exageración vertical** (solar 150 m × 20 m); escalar `model.object` en y alrededor de la base: el raycast de Fragments usa `matrixWorld` y sigue funcionando. Transparencia con `depthWrite: false` | Capturas del visor |
| M15 | Con relieve (Talheim: GOK 749–772 m) la correlación por cota absoluta parte una misma capa superficial en varias unidades: comparar también la **profundidad bajo GOK** y quedarse con la menor distancia | 15 → 6 unidades ([19](19_app_v2.md)) |
| M16 | Un modelo sin coordenadas sólo es honesto como **esquema**: decirlo en la app, en el IFC (`Lage`) y en el visor (`Lagebezug`) | App v2 |
| M17 | `ifcopenshell.api.unit.assign_unit()` **sin argumentos pone milímetros**: con coordenadas en metros el modelo sale 1000× pequeño en cualquier visor y la `IfcMapConversion` queda mal. Unidades explícitas y prueba `calculate_unit_scale == 1` | Trasse de 6 km medía 6 m ([20 §2](20_lage_pruefung_viewer.md#2-mover-la-geometría-y-modelos-de-más-de-5-km)) |
| M18 | Cámara de That Open: perspectiva near 1 / far 1000, ortográfica 0,1 / 1000 a 200 m del objetivo: **todo lo > 1 km desaparece**. Recalcular near/far en cada movimiento con el tamaño de la escena (ortográfica: near negativo) | Trasse: far 24,6 km, near 0,02 m de cerca |
| M19 | Un IFC ya local al origen del proyecto se carga **sin `COORDINATE_TO_ORIGIN`** (web-ifc lo desplaza por defecto): así IFC y escena comparten coordenadas. Para IFC con coordenadas globales grandes hay que dejarlo activo | Chinchetas = IFC al cm |
| M20 | Calibrar un plano con 2 puntos: Lageplan = **semejanza** (complejos, `q = u − i·v` porque las filas bajan); Längsschnitt = **escalas propias** en estación y altura (la exageración del dibujo se deshace). Mostrar escala y giro resultantes para que el usuario detecte un mal punto | 1:500 / 10,0°; 1:500 / 1:100 |
| M21 | BUI 3.4: `Component.create` decide con/sin estado por la **aridad** de la plantilla (`() =>` devuelve un elemento, no `[el, update]`); tooltips con `<bim-tooltip>` dentro del botón (`tooltip-title` obsoleto); `bim-label` corta a una línea (usar `<p>`); `bim-dropdown` necesita `.value` (no sigue a `checked` de las opciones tras el primer render) | Errores y avisos del primer arranque |
| M22 | camera-controls aplica `fitToSphere(…, false)` en el siguiente `update()`: llamar `controls.update(0)` antes de medir la escala de la vista | El desplazamiento junto al panel salía de la pantalla |
| M23 | CSS: un hijo con `display:none` en una rejilla hace que el siguiente ocupe su columna (de 0 px): fijar `grid-column`; y `[hidden]` pierde contra `display:grid/flex` (`[hidden]{display:none!important}`) | Visor de 0 px al plegar el panel; aviso de carga que no se iba |
| M24 | El IFC de ifcopenshell lleva **fecha y hora en la cabecera**: el mismo modelo da otro hash tras reiniciar. Como huella del modelo (einchecken, cachés) usar la **clave de sus entradas**, no los bytes del IFC | *seitdem geändert* falso tras reiniciar la app |
| M25 | Dentro de Streamlit el iframe mide **0 px** hasta que llega `setFrameHeight`: un encuadre en ese momento da aspecto 0/0 y `fitToSphere` deja la cámara en **NaN** sin vuelta atrás (visor negro, marcas ocultas). Encuadrar sólo con tamaño (ResizeObserver, encuadre pendiente) y reparar una cámara no finita | Arranque en frío de la app ([20](20_lage_pruefung_viewer.md)) |
| M26 | BUI: `bim-toolbar-section` pone el `label-hidden` de sus botones según su `vertical` al montarse (y lit no lo vuelve a poner si el valor no cambia): para una barra sólo de iconos, grupos propios (`div`) dentro de `bim-toolbar` | Barra con etiquetas pese a `label-hidden` |
| M27 | Una app lit con un componente ajeno persistente (el visor): dejarlo en un elemento fijo de la plantilla y **no moverlo** de padre (los componentes web se desmontan y vuelven a montar); mostrarlo u ocultarlo con CSS; con `display:none` el encuadre espera al tamaño (M25) | Visor que no se recarga entre *Lage* y *Modell* |
| M28 | Calibrar con **escala (distancia medida o 1:n) + punto de referencia + giro** es tan exacto como dos puntos de pase y más fácil de comprobar; bloquear el plano antes de arrastrar evita mover sondeos sin querer | 1:500 · 10,0° desde la UI; D67 |

## X. Entorno de trabajo

| # | Regla | Evidencia |
|---|---|---|
| X1 | En el entorno de Claude la descarga de Gutachten de webs municipales está **bloqueada** (403/000); pypi y GitHub sí. Los PDFs los sube el usuario | Rondas 1–3 |
| X2 | Probar dependencias pesadas (swissgeol, OCR) en **entornos separados** del scratchpad; swissgeol fija PyMuPDF 1.26.3 | `sgvenv` |
| X3 | `pkill -f patrón` en un comando que contiene ese texto en cualquier parte **se mata a sí mismo** (también con `[p]atrón` si el nombre aparece después en el mismo comando): ejecutar `pkill` en un comando aparte | Exit 144 tres veces |
| X4 | `python -I` no añade la carpeta del script a `sys.path`: los scripts deben insertarla ellos mismos | `ablation.py` |
| X5 | `show_pdf_page` ignora el `/Rotate` de la página origen; compensar al recomponer PDFs | Primera versión de `perturb.py` |
| X6 | OCR caro → **caché por imagen de página** (hash) para que la regresión y la ablación sean rápidas | `GEO_OCR_CACHE` |
| X7 | Cada proceso que carga el modelo OCR ocupa varios GB: 4 procesos de ablación en paralelo **agotaron la memoria y reiniciaron el contenedor**. Cargar el modelo sólo si falla la caché y usar ≤ 2 procesos | Reinicio durante la ablación final |
| X8 | La ablación recarga el módulo en cada configuración: **no editar el módulo mientras corre** (se mezclarían versiones); probar cambios en una copia con otro nombre | Ablación final |
| X9 | **web-ifc 0.0.78**: el `web-ifc.wasm` de navegador no casa con su JS (`StreamMeshes called with 4 arguments, expected 3`); en Node funciona. En el visor, 0.0.77 | `apps/web` |
| X10 | That Open descarga por defecto WASM (`autoSetWasm`) y worker (`getWorker`) de unpkg: copiarlos a `public/vendor` (`npm run vendor`) para trabajar sin red y con versiones fijas | `apps/web` |
| X11 | `vite preview` sirve `dist/`: un IFC copiado a `public/` después del build no se ve; el chequeo copia el IFC a `dist/` | Capturas con volúmenes viejos |
| X12 | Streamlit recarga los módulos al cambiar archivos: recompilar el visor con la app en marcha la deja sin componente (falta `dist/index.html` un instante). Reiniciar la app tras el build | Visor sin cargar en la prueba |
| X13 | Un elemento nuevo encima del componente (p. ej. `st.status` de la extracción) lo **vuelve a montar**: iframe nuevo, estado a cero. Las pruebas detectan el cambio de iframe | `check_app.mjs` |
| X14 | Streamlit sirve los archivos del componente con `mimetypes`; en Windows el registro puede dar `text/plain` para `.js` y bloquear módulos/workers: registrar los tipos en la app | `ui/viewer.py` (precaución; no visto en Windows aún) |
| X15 | Con SwiftShader (Chromium sin GPU) un fotograma con posproducción tarda ~1 s: lo que se actualiza "en cada fotograma" (marcas DOM, estado) va con retraso y los iframes del mismo origen bloquean la página. Las pruebas esperan fotogramas (`requestAnimationFrame` ×2) y leen el estado en el momento; el render bajo demanda lo alivia | `check.mjs`, `check_app.mjs` |
| X16 | `vite build` **vacía `dist/`** (también los IFC de prueba copiados); y un archivo que falta lo contesta el servidor con `index.html`: comprobar el `content-type` antes de pasarlo a web-ifc | `OpenModel … reading 'arguments'` |
| X17 | El guardado automático del proyecto hace que una prueba repetida empiece con el estado anterior: las pruebas de la app pulsan *Alle Korrekturen verwerfen* (menú ⋯) al abrir cada proyecto | `check_app.mjs` |
| X18 | Playwright: `page.mouse` usa coordenadas de la ventana; un iframe bajo el pliegue hay que traerlo a la vista (p. ej. clic en un elemento suyo) antes de arrastrar | Arrastre sin efecto en la app |
| X19 | X3 también vale para `pgrep -f patrón \| xargs kill`: el comando que lo contiene coincide consigo mismo | Exit 144 |
| X20 | Atajos de teclado: ignorarlos sólo en campos de texto, **no** con el foco en un botón (tras pulsar *Nächste* el foco queda en él y ↓ dejaba de funcionar); cerrar los menús tras una acción | `check_app.mjs` A |
| X21 | Playwright: el valor de un `<input>` no forma parte del texto de su fila (`hasText` no lo encuentra): buscar el índice por `value` con `evaluate` | Prueba de *Einheiten* |

Up: [Índice](README.md)

Related: [15 Resultados reales](15_resultados_pdfs_reales.md) · [11 Decisiones](11_decisiones.md) · [09 Validación](09_validacion_benchmark.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md) · [18 Modelador de capas](18_modelador_capas.md) · [21 App por pasos y normas](21_app_schritte_normen.md)
