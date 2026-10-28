---
title: "20 Visor con controles de TwinBimM, Lage sobre plano y Prüfstand"
date: 2026-10-28
tags: [visor, thatopen, streamlit, lage, pruefung, baugrundmodell]
aliases: [Lage-Editor, Prüfstand, Visor v3]
---

# 20 Visor con controles de TwinBimM, Lage sobre plano y Prüfstand

> [!NOTE]
> Actualizado en [21](21_app_schritte_normen.md):
> - La app ya no es Streamlit.
> - Los avisos son por capas sin clasificar.
> - La **calibración** es escala + punto de referencia + candado (las de dos puntos se convierten).
> - La barra del visor es sólo de iconos.
>
> Los controles TwinBimM, la cámara > 5 km y el Prüfstand de esta nota siguen igual.

Ronda pedida por el usuario sobre la [app v2](19_app_v2.md): replicar los controles de su visor
**TwinBimM** (That Open), corregir los problemas al mover la geometría, preparar todo para
**Baugrundmodelle de más de 5 km**, colocar los sondeos **a mano sobre un PDF del plano** (vista de
arriba o lateral) antes de modelar, **distancias propias en la fila** (BK1 → BK2 10 m, BK2 → BK3
15 m), **ver las tablas antes de generar** el modelo, que el modelo **se ajuste solo** a cada
cambio y poder **"einchecken"** el estado de revisión de la confianza.

```
PDF ──► extracción ──► tablas (Bohrungen · Schichten · Lage & Unterlage)  ◄─┐
                          │  correcciones, geprüft, distancias, plano PDF     │ eventos del visor
                          ▼                                                   │ (lage, station, gok,
            [Baugrundmodell erzeugen] ──► modelo ──► visor That Open ─────────┘  kalibrierung, geprueft)
                          ▲                     │
                          └── cada cambio ◄─────┘   Prüfstand ──► Einchecken ──► IFC con Pruefstand
```

![Trasse sintética de 6 km en el visor: unidad seleccionada en verde W&F, propiedades, coordenadas reales](img/20_visor_trasse_6km.jpg)

## 1. Controles del visor (como TwinBimM)

Se leyó el código del visor del usuario (repositorio `TwinBimM-`, `frontend/src`) y se replicó lo que
aplica a un Baugrundmodell, con la misma librería (`@thatopen/ui` 3.4, `@thatopen/ui-obc` 3.4,
`@thatopen/components-front` 3.6):

| TwinBimM | Aquí | Nota |
|---|---|---|
| Tema oscuro BUI con colores W&F (`--wf-blue`, `--wf-green`) | igual | `html.bim-ui-dark`, fondo `#1a1d23` |
| `PostproductionRenderer` (COLOR_SHADOWS, AO, aristas `#494b50`) | igual | **en movimiento sin sombras**, al parar imagen completa (§2) |
| `bim-view-cube` arriba a la derecha | igual, caras OBEN/UNTEN/SÜD/NORD/OST/WEST | encuadra **toda la escena**, no el origen |
| Barra inferior *Sichtbarkeit*: Alle anzeigen, Transparenz | igual (la transparencia conserva los colores de las unidades) | |
| Barra inferior *Auswahl*: Fokus, Ausblenden, Isolieren, Einfärben | igual (`Highlighter` verde `#a2c513`, `Hider`) | |
| Engranaje: Raster, Kameraprojektion | igual + *Orbit um Mauspunkt* + *Kanten und Schatten* | |
| `⌖ Koord.` con HUD abajo a la izquierda | igual, pero en **Rechtswert / Hochwert / m NHN** (o estación) | |
| Supr borra el plano de corte bajo el ratón | igual | |
| — | *Ansicht* (Iso, Oben, Süd, Überhöhung 1–20×), *Schnitt* (O–W, N–S, doble clic, borrar), *Lage* (editor, §3) | propios del Baugrundmodell |
| Panel lateral con modelos | panel *Baugrundmodell*: modelo, unidades (visibilidad, ◎ sólo esta), sondeos con estado de revisión, avisos | |

Los iconos se empaquetan sin red (`scripts/vendor.mjs` copia del paquete `@iconify-json/mdi` sólo
los que usa `src/`): BUI los pediría si no a `api.iconify.design`, y en la red de la empresa puede no
haber salida. Con poco ancho (columna de Streamlit) la barra muestra sólo iconos con tooltip.

## 2. Mover la geometría y modelos de más de 5 km

Los "problemas al mover la geometría" tenían tres causas, ninguna en los controles en sí:

1. **El IFC declaraba milímetros**: `ifcopenshell.api.unit.assign_unit()` sin argumentos pone
   *MILLIMETRE*, pero el modelador escribe metros. Todo visor mostraba el modelo **1000 veces más
   pequeño** (una trasse de 6 km medía 6 m) y la georreferencia de `IfcMapConversion` quedaba mal.
   Con la cámara de That Open (distancia mínima 6 m, near 1 m) se navegaba "dentro" del modelo.
   Ahora la unidad es METRE explícita y una prueba lo exige (`calculate_unit_scale == 1`).
2. **near/far fijos** (perspectiva 1 / 1000 m, ortográfica 0,1 / 1000 m a 200 m del objetivo): todo
   lo que quedaba a más de 1 km desaparecía. `kamera.ts` los recalcula en cada movimiento con el
   tamaño de la escena y la distancia (near = distancia/1000, far = distancia + 2 radios; en
   ortográfica near negativo).
3. **Raster y vistas fijos**: la rejilla crece con la escena (1 m … 100 m), el ViewCube y las vistas
   encuadran la escena entera y el doble clic fija el punto de giro donde se pulsa.

Un cuarto problema sólo aparecía al abrir la app: el primer encuadre llegaba con el iframe aún a 0 px
de alto y dejaba la cámara en NaN (visor vacío). Ahora el encuadre espera a que el lienzo tenga
tamaño y una cámara no finita se repara sola ([M25](16_lecciones_aprendidas.md#m-modelo-ifc-y-that-open)).

Además el visor **dibuja bajo demanda** (`RendererMode.MANUAL`): mientras la cámara se mueve sin
posproducción (fluido también con 20 000 nodos por superficie), 50 ms después de parar una imagen con
sombras y aristas, en reposo un fotograma por segundo. En portátiles ahorra GPU y batería.

Prueba con la **trasse sintética de 6 km** (51 sondeos, `synthetisch.trasse`, ahora también como
[ejemplo](../data/beispiele/README.md)): carga, far 24,6 km > 6,1 km de longitud, acercarse a 2 m
sin recortes (near 0,02 m), coordenadas del HUD en EPSG:25832.

**Delimitación del modelo** (*Modellgrenze und Raster* en la barra lateral): el modelo ocupa la
envolvente convexa de los sondeos + un buffer. Automático: medio espaciado entre sondeos (5–100 m);
a mano hasta 5 km. La malla se limita a 30 000 nodos también con un raster puesto a mano: si no cabe,
se hace más gruesa y se avisa (prueba `test_grosse_modellgrenze_von_hand`).

## 3. Lage: sondeos sobre el plano antes de modelar

![Lageplan sintético 1:500 girado 10°, calibrado con B 1 y B 11; B 6 y BS 9 arrastrados desde la lista](img/20_lageplan_kalibriert.jpg)

**Unterlage.** En la pestaña *Lage & Unterlage* se sube el PDF del plano y se elige la vista:
*Lageplan (Draufsicht)* o *Längsschnitt (Seitenansicht)* y la página. PyMuPDF la convierte en imagen
(≤ 6000 px, ≤ 300 dpi) y el visor la pone en la escena: el Lageplan horizontal sobre los sondeos, el
Längsschnitt vertical detrás de la fila. *Im Viewer bearbeiten* abre el modo Lage: vista desde arriba
(o desde el sur) ortográfica, encuadrada a la derecha del panel.

**Calibrar con dos puntos de paso.** *Punkt 1* → clic en el plano → coordenadas a mano o *Bohrung*
(toma las de un sondeo con coordenadas del PDF o de la tabla). Igual con el punto 2 y *Kalibrierung
übernehmen*.

- Lageplan: **semejanza** (escala, giro, traslación) con números complejos, `w = A·q + B`,
  `q = u − i·v` (las filas de la imagen bajan). Se muestra escala y giro: *1:500 · Drehung 10,0°*.
- Längsschnitt: **afín por ejes** con escalas propias en estación y altura: *Länge 1:500 · Höhe 1:100
  (Überhöhung 5,0×)*; la exageración del dibujo se deshace, la del visor es aparte.
- Sin calibrar el plano se coloca a 1:1000 (y 1:100 en altura) junto a los sondeos, para empezar.

**Mover sondeos.** Cada sondeo es una chincheta (columna con los colores de sus capas + marca con el
código y el estado: verde revisado, naranja confianza < 0,6, gris fuera del modelo). En modo Lage:

- Lageplan: arrastrar la marca → Rechts-/Hochwert en el sistema del plano (con EPSG si se indicó).
- Längsschnitt: arrastrar a lo largo de la fila → **estación**; con Mayús → **cota de la boca (GOK)**.
- Sondeos **sin posición** aparecen en una lista (*Ohne Lage*) y se arrastran a su sitio.

Cada cambio va a Python como evento y queda marcado: `coord_source = "Plan (kalibriert)"`,
`"manuell (Viewer)"` o `"Reihe (Station im Schnitt gesetzt)"`; la GOK como `gok_source = manuell`.

**Precisión medida** (`apps/web/scripts/check.mjs` con [`scripts/testplan.py`](../scripts/testplan.py),
planos sintéticos con verdad conocida, renderizados por la misma ruta que la app):

| Prueba | Resultado |
|---|---|
| Lageplan 1:500 girado 10°: escala y giro calibrados | 1:499–1:501 · 10,0–10,1° |
| Marca de B 7 sobre su símbolo tras calibrar | 0,1–0,4 px |
| B 6 y BS 9 (sin coordenadas) arrastrados a su símbolo | 0,22–0,45 m |
| Längsschnitt 1:500 / 1:100 calibrado | Länge 1:500 · Höhe 1:100 |
| B 2 y B 3 arrastrados a su columna | estación 10,00 / 25,00 m (error ≤ 0,01 m) |
| Mayús + arrastrar B 4 un metro hacia arriba | GOK 40,78 m (verdad 40,77) |

Para picar con precisión hay que acercarse (el panel lo dice): sin zoom un píxel de pantalla puede
ser medio metro.

## 4. Fila con distancias propias

Sin coordenadas la Lage es una **Reihe** (Längsschnitt). En la tabla de la pestaña *Lage* cada sondeo
tiene **Nr** (orden), **Abstand zum Vorgänger** y **Station**:

- Abstand: BK1 → BK2 **10 m**, BK2 → BK3 **15 m** … (sin dato rige el *Standardabstand*).
- Station: absoluta; la pone también el visor al arrastrar en el Längsschnitt.
- Prioridad: estación puesta > distancia propia > distancia estándar. Con sólo distancias estándar
  el modelo se marca *schematisch*; con distancias propias *Reihe (Abstand manuell)*.

## 5. Tablas antes del modelo, generar y nachführen

![Página: indicadores, Prüfstand, tablas editables y el botón Baugrundmodell erzeugen antes del visor](img/20_app_tabellen_vor_modell.jpg)

1. Al subir el PDF se ven **las tablas** (*Bohrungen*, *Schichten*, *Lage & Unterlage*) y el visor
   ya muestra los sondeos con su posición: **todavía no hay modelo**.
2. *Baugrundmodell erzeugen* lo genera.
3. Desde ahí, **cada cambio** (tabla, visor, ajustes, unidades) recalcula el modelo
   (*Automatisch nachführen*, activado). Desactivado, el modelo queda congelado y aparece *Jetzt neu
   rechnen*.

La geometría se cachea por la entrada **sin las marcas de revisión**: marcar capas como revisadas no
recalcula el modelo ni recarga el visor (el estado de revisión se ve en las chinchetas y va en el IFC
de exportación, que se genera al pulsar la descarga).

El **estado del proyecto** (correcciones, Lage, revisión, unterlage, eincheckungen) vive aparte de la
extracción ([`ui/projekt.py`](../ui/projekt.py)), se guarda solo en disco por firma de los documentos
y se recupera al volver a abrir el mismo PDF; *Korrekturen verwerfen* lo borra.

## 6. Prüfstand y Einchecken

- **Schichten**: tabla editable por sondeo (von, bis, Bodenart, Geprüft) con la confianza de la
  extracción; corregir una capa la marca como revisada y como *korrigiert* (la confianza pasa a 1,0 y
  la original se conserva). *Alle Schichten dieser Bohrung geprüft*, *Nächste ungeprüfte →*.
- **Prüfstand** arriba: sondeos y capas revisados (barras), capas inseguras (< 0,6) sin revisar,
  corregidas, posiciones puestas a mano.
- **Einchecken** guarda una entrada con hora, contadores, comentario y la **huella del modelo** (clave
  de sus entradas: el IFC lleva hora en la cabecera, [M24](16_lecciones_aprendidas.md#m-modelo-ifc-y-that-open));
  si después cambia algo, el chip dice *seitdem geändert*. Historial en la pestaña *Prüfprotokoll*.
- En el **IFC**: `CPset_Herkunft.Geprueft` por sondeo; `CPset_Schichtenverzeichnis.Geprueft`,
  `Korrigiert`, `Konfidenz_Extraktion` por capa; `CPset_Baugrundmodell.Pruefstand` con el último
  einchecken. En el visor, *Als geprüft markieren* en el panel de un sondeo.

## 7. Protocolo visor ↔ Streamlit

| Dirección | Contenido |
|---|---|
| Python → visor (`streamlit:render`) | `ifc` (URL o nada antes de generar), `projekt` (firma: misma firma = la cámara se queda), `ursprung`, `epsg`, `modus`, `bohrungen` (chinchetas), `unterlage` (URL de la imagen, tamaño, calibración), `ueberhoehung`, `nr` (último evento aplicado), `bearbeiten` (contador: abre el modo Lage) |
| visor → Python (`setComponentValue`) | `{typ, nr, projekt, …}` con `typ` ∈ `lage` (x, y), `station`, `gok`, `kalibrierung` (2 puntos, EPSG), `geprueft` |

Cada evento lleva un número creciente y la firma del proyecto: Python aplica cada número una sola
vez (Streamlit repite el último valor en cada rerun) e ignora eventos de otro proyecto. El visor
arranca su contador en el `nr` que recibe, para no repetir números tras volver a montarse.
La página tiene un **esqueleto fijo de contenedores**: el iframe del visor no se vuelve a montar
cuando cambian elementos de arriba (antes pasaba al pulsar *Erzeugen*, [X13](16_lecciones_aprendidas.md#x-entorno-de-trabajo)).

Marco de coordenadas: el IFC es local al origen del proyecto (`ursprung`, fijo, redondeado a 100 m)
y se carga **sin** `COORDINATE_TO_ORIGIN`; three.js x = E − E₀, y = NHN (exagerado alrededor de una
cota de referencia), −z = N − N₀. Así chinchetas, plano e IFC coinciden al centímetro (BK 1 de la
trasse: R 565 000,00 / H 5 932 985,00 / GOK 45,00 como en el caso sintético).

![Pestaña Lage & Unterlage con el Lageplan subido y el visor en modo Lage](img/20_app_lage_unterlage.jpg)

## 8. Piezas

| Archivo | Qué hace |
|---|---|
| [`apps/web/src/main.ts`](../apps/web/src/viewer/viewer.ts) | Mundo, posproducción, Highlighter/Hider/Clipper, barra inferior, engranaje, ViewCube, HUD, panel lateral, Streamlit |
| [`apps/web/src/kamera.ts`](../apps/web/src/viewer/kamera.ts) | near/far dinámicos, rejilla, vistas, encuadre junto al panel |
| [`apps/web/src/lage.ts`](../apps/web/src/viewer/lage.ts) | Chinchetas, plano, calibración, arrastre, lista sin posición, panel Lage |
| [`apps/web/src/rahmen.ts`](../apps/web/src/viewer/rahmen.ts) | Marco de coordenadas y exageración |
| [`apps/web/src/streamlit.ts`](../apps/web/src/viewer/kanal.ts) | Protocolo con Streamlit y eventos numerados |
| [`ui/projekt.py`](../ui/projekt.py) | Estado del proyecto: correcciones, Reihe, Lage, eventos, Prüfstand, einchecken, guardar/cargar |
| `ui/baugrundmodell.py` (eliminado, ver [21](21_app_schritte_normen.md)) | Página: tablas → Lage → erzeugen → visor → resultados |
| [`ui/pipeline.py`](../ui/pipeline.py) | Extracción, `modell_bauen`/`ifc_bytes`, imagen del plano |
| [`scripts/testplan.py`](../scripts/testplan.py) | Lageplan y Längsschnitt sintéticos con verdad conocida |

## 9. Verificación

- `pytest tests` (app, **15**) y `pytest services/modeler/tests` (modelador, **36**): verdes.
- `apps/web/scripts/check.mjs` (Chromium sin pantalla): **17/17** — trasse de 6 km (carga, far,
  near al acercarse, HUD, selección, transparencia, corte), Lageplan (calibración, alineación,
  arrastre de sondeos sin posición y de una marca), Längsschnitt (calibración, estaciones, GOK).
- `scripts/check_app.mjs` con Streamlit: **7/7** — tablas y chinchetas antes del modelo, *Erzeugen*,
  arrastrar BK2 en el visor → evento → Python recalcula → el visor recarga, einchecken, Lageplan
  subido y *Im Viewer bearbeiten*.
- Probado en Linux con SwiftShader (render por software: un fotograma con posproducción tarda
  ~1 s; en un PC con GPU no). **Windows sin probar desde aquí.**

## 10. Límites y siguientes pasos

1. El plano se calibra con 2 puntos: no corrige distorsiones (planos escaneados torcidos); con 3+
   puntos se podría ajustar una afinidad general por mínimos cuadrados con residuos.
2. La delimitación es la envolvente convexa: en trazados curvos incluye terreno sin sondeos; un
   **pasillo** (buffer alrededor del eje) sería más honesto para trasses.
3. Leer los símbolos de sondeo del plano automáticamente (texto + círculo) y proponer la posición
   (docs/07); hoy se arrastran a mano.
4. Modelos de contexto (eje del túnel, terreno) en el mismo visor alineados por georreferencia.
5. Multiusuario y servidor: el estado se guarda en el disco local; con Supabase (arquitectura §5) el
   Prüfstand sería compartido.

Up: [Índice](README.md)

Related: [19 App v2](19_app_v2.md) · [18 Modelador de capas](18_modelador_capas.md) · [11 Decisiones](11_decisiones.md) · [16 Lecciones](16_lecciones_aprendidas.md) · [07 Coordenadas](07_coordenadas.md) · [Visor](../apps/web/README.md)
