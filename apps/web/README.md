---
title: "Visor del Baugrundmodell (That Open)"
date: 2026-10-28
tags: [visor, thatopen, ifc, lage]
aliases: [Visor web]
---

# Visor del Baugrundmodell (That Open Engine)

Vite + TypeScript + `@thatopen/components` / `components-front` 3.6 + `@thatopen/ui` / `ui-obc` 3.4.
Abre el IFC 4.3 del [modelador](../../services/modeler/README.md) con los **controles del visor
TwinBimM** (tema oscuro W&F, barra *Sichtbarkeit / Auswahl / Schnitt*, ViewCube, engranaje,
`⌖ Koord.`, posproducción), cámara para **modelos de más de 5 km** y el **editor de Lage**: sondeos
como chinchetas que se arrastran sobre el PDF de un Lageplan o un Längsschnitt calibrado con dos
puntos. Diseño y cifras: [20 Lage y Prüfstand](../../docs/20_lage_pruefung_viewer.md).

```bash
cd apps/web
npm install
cp <modelo.ifc> public/modelle/            # los IFC no se suben al repo
npm run dev                                 # http://localhost:5173/?ifc=modelle/<modelo.ifc>&ueberhoehung=5
npm run build
python ../../scripts/testplan.py <planes>   # Lageplan/Längsschnitt sintéticos con verdad conocida
node scripts/check.mjs <modelo.ifc> <planes> <capturas>   # 17 pruebas sin pantalla (Playwright)
```

| Pieza | Qué hace |
|---|---|
| [`src/main.ts`](src/main.ts) | Mundo, posproducción, Highlighter/Hider/Clipper, barra inferior, engranaje, ViewCube, HUD, panel lateral, Streamlit |
| [`src/kamera.ts`](src/kamera.ts) | near/far en cada movimiento, rejilla según la escena, vistas, encuadre junto al panel |
| [`src/lage.ts`](src/lage.ts) | Chinchetas, plano (imagen) y calibración, arrastre, sondeos sin posición, panel Lage |
| [`src/rahmen.ts`](src/rahmen.ts) | Marco: x = E − E₀, y = NHN (exagerado), −z = N − N₀ |
| [`src/streamlit.ts`](src/streamlit.ts) | Protocolo del componente; eventos numerados con firma de proyecto |
| [`src/baugrund.ts`](src/baugrund.ts) | Unidades, sondeos y propiedades del IFC |

- **Dentro de Streamlit** ([`ui/viewer.py`](../../ui/viewer.py)) es un componente: la app sirve
  `dist/`, escribe IFC e imagen del plano en `dist/modelle/<hash>.*` y pasa URL, chinchetas, origen,
  modo y calibración; el visor devuelve eventos (`lage`, `station`, `gok`, `kalibrierung`,
  `geprueft`). Por eso **`dist/` está en el repo**: después de cambiar el visor, `npm run build` y
  subir `dist/`. Sin Streamlit, `?bohrungen=<args.json>` carga chinchetas y plano como desde la app.
- **Navegación**: izquierda gira, derecha desplaza, rueda acerca hacia el ratón; doble clic fija el
  punto de giro; engranaje: *Orbit um Mauspunkt*. En movimiento sin sombras (fluido), al parar con
  posproducción; en reposo no se redibuja.
- `npm run vendor` (lo llaman `dev` y `build`) copia `web-ifc.wasm` a `public/vendor/` y los iconos
  usados a `src/icons.gen.json`: **nada se descarga de unpkg ni de api.iconify.design**.
- **web-ifc fijado en 0.0.77** ([X9](../../docs/16_lecciones_aprendidas.md#x-entorno-de-trabajo)); las
  clases geotécnicas se añaden al importer ([M2](../../docs/16_lecciones_aprendidas.md#m-modelo-ifc-y-that-open));
  el IFC propio se carga sin `COORDINATE_TO_ORIGIN` ([M19](../../docs/16_lecciones_aprendidas.md#m-modelo-ifc-y-that-open)).

Up: [Índice de documentación](../../docs/README.md)

Related: [20 Lage y Prüfstand](../../docs/20_lage_pruefung_viewer.md) · [18 Modelador de capas](../../docs/18_modelador_capas.md) · [Arquitectura §8.3](../../docs/ARQUITECTURA_BAUGRUNDMODELL.md#83-integración-en-el-frontend-esbozo-api-v36) · [Spike IFC](../../spikes/ifc_thatopen/README.md)
