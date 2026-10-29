---
title: "App por pasos y visor del Baugrundmodell (That Open)"
date: 2026-10-28
tags: [visor, thatopen, ifc, lage]
aliases: [Visor web]
---

# App por pasos y visor del Baugrundmodell (That Open Engine)

Vite + TypeScript + lit + `@thatopen/components` / `components-front` 3.6 + `@thatopen/ui` / `ui-obc` 3.4.
Dos páginas:

- **`index.html`**: la app por pasos (Gutachten → Bohrungen → Lage → Einheiten → Modell), servida por
  `python -m server` ([docs/21](../../docs/21_app_schritte_normen.md)).
- **`viewer.html`**: el visor solo, que abre un IFC (`?ifc=`) o chinchetas y plano como desde la app
  (`?bohrungen=<args.json>`).

El visor tiene:

- Los **controles del TwinBimM** (tema oscuro W&F, ViewCube, engranaje con explicación de cada ajuste,
  coordenadas, posproducción).
- Una **barra de herramientas compacta** sólo con iconos.
- Cámara para **modelos de más de 5 km**.
- El **editor de Lage**: sondeos como chinchetas sobre el PDF de un Lageplan o un Längsschnitt calibrado con
  escala + punto de referencia + candado.

```bash
cd apps/web
npm install
npm run dev                                 # http://localhost:5173 (pasa /api y /dateien a python -m server)
npm run build                               # dist/: lo sirve el servidor Python (sin Node)
python ../../scripts/testplan.py <planes>   # Lageplan/Längsschnitt sintéticos con verdad conocida
node scripts/check.mjs <modelo.ifc> <planes> <capturas>   # 18 pruebas del visor sin pantalla (Playwright)
```

| Pieza | Qué hace |
|---|---|
| [`src/app/start.ts`](src/app/start.ts) | Marco de la app: pasos, Zurück/Weiter, avisos, dirección `#/<proyecto>/<paso>/<sondeo>` |
| [`src/app/store.ts`](src/app/store.ts) | Estado, cambios al servidor (`/aendern`), modelo, visor por paso |
| [`src/app/schritt_*.ts`](src/app) | Los cinco pasos; [`hilfe.ts`](src/app/hilfe.ts) las ayudas "?"; [`profil.ts`](src/app/profil.ts) columnas SVG |
| [`src/viewer/viewer.ts`](src/viewer/viewer.ts) | `viewerStarten()`: mundo, posproducción, Highlighter/Hider/Clipper, barra, engranaje, ViewCube, HUD, panel lateral |
| [`src/viewer/kamera.ts`](src/viewer/kamera.ts) | near/far en cada movimiento, rejilla según la escena, vistas, encuadre |
| [`src/viewer/lage.ts`](src/viewer/lage.ts) | Chinchetas, plano (imagen) y calibración, elegir puntos en el plano, arrastre con candado y regla de la GOK |
| [`src/viewer/kanal.ts`](src/viewer/kanal.ts) | Tipos y eventos del visor hacia la app (`lage`, `station`, `gok`, `geprueft`) |
| [`src/viewer/rahmen.ts`](src/viewer/rahmen.ts) | Marco: x = E − E₀, y = NHN (exagerado), −z = N − N₀ |
| [`src/viewer/baugrund.ts`](src/viewer/baugrund.ts) | Unidades, sondeos y propiedades del IFC |

Notas:

- **`dist/` está en el repo**: después de cambiar la app o el visor, `npm run build` y subir `dist/`.
- **Navegación**:
  - Izquierda gira, derecha desplaza, la rueda acerca hacia el ratón.
  - Doble clic fija el punto de giro; en el engranaje está *Orbit um Mauspunkt*.
  - En movimiento sin sombras (fluido); al parar, con posproducción. En reposo no se redibuja.
- `npm run vendor` (lo llaman `dev` y `build`) copia `web-ifc.wasm` a `public/vendor/` y los iconos usados a
  `src/icons.gen.json`: **nada se descarga de unpkg ni de api.iconify.design**.
- **web-ifc fijado en 0.0.77** ([X9](../../docs/16_lecciones_aprendidas.md#x-entorno-de-trabajo)).
- Las clases geotécnicas se añaden al importer ([M2](../../docs/16_lecciones_aprendidas.md#m-modelo-ifc-y-that-open)).
- El IFC propio se carga sin `COORDINATE_TO_ORIGIN` ([M19](../../docs/16_lecciones_aprendidas.md#m-modelo-ifc-y-that-open)).
- La barra no usa `bim-toolbar-section`, porque devuelve las etiquetas
  ([M26](../../docs/16_lecciones_aprendidas.md#m-modelo-ifc-y-that-open)).

Up: [Índice de documentación](../../docs/README.md)

Related: [21 App por pasos y normas](../../docs/21_app_schritte_normen.md) · [20 Lage y Prüfstand](../../docs/20_lage_pruefung_viewer.md) · [18 Modelador de capas](../../docs/18_modelador_capas.md) · [Arquitectura §8.3](../../docs/ARQUITECTURA_BAUGRUNDMODELL.md#83-integración-en-el-frontend-esbozo-api-v36) · [Spike IFC](../../spikes/ifc_thatopen/README.md)
