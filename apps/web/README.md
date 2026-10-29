---
title: "Step app and Baugrundmodell viewer (That Open)"
date: 2026-10-28
tags: [viewer, thatopen, ifc, lage]
aliases: [Web viewer]
---

# Step app and Baugrundmodell viewer (That Open Engine)

Vite + TypeScript + lit + `@thatopen/components` / `components-front` 3.6 + `@thatopen/ui` /
`ui-obc` 3.4. Two pages:

- **`index.html`**: the step app (Gutachten → Bohrungen → Lage → Einheiten → Modell), served by
  `python -m server` ([docs/21](../../docs/21_app_schritte_normen.md)).
- **`viewer.html`**: the viewer on its own, which opens an IFC (`?ifc=`) or pins and a plan as from
  the app (`?bohrungen=<args.json>`).

The viewer has:

- The **TwinBimM controls** (dark W&F theme, ViewCube, gear with an explanation of every setting,
  coordinates, postproduction).
- A **compact toolbar** with icons only.
- A camera for **models of more than 5 km**.
- The **Lage editor**: Bohrungen as pins on the PDF of a Lageplan or a Längsschnitt calibrated with
  scale + reference point + lock.

```bash
cd apps/web
npm install
npm run dev                                 # http://localhost:5173 (forwards /api and /dateien to python -m server)
npm run build                               # dist/: served by the Python server (no Node)
python ../../scripts/testplan.py <plans>    # synthetic Lageplan/Längsschnitt with known ground truth
node scripts/check.mjs <model.ifc> <plans> <screenshots>   # 18 headless viewer tests (Playwright)
```

| Piece | What it does |
|---|---|
| [`src/app/start.ts`](src/app/start.ts) | Frame of the app: steps, Zurück/Weiter, warnings, address `#/<project>/<step>/<Bohrung>` |
| [`src/app/store.ts`](src/app/store.ts) | State, changes to the server (`/aendern`), model, viewer per step |
| [`src/app/schritt_*.ts`](src/app) | The five steps; [`hilfe.ts`](src/app/hilfe.ts) the "?" help texts; [`profil.ts`](src/app/profil.ts) SVG columns |
| [`src/viewer/viewer.ts`](src/viewer/viewer.ts) | `viewerStarten()`: world, postproduction, Highlighter/Hider/Clipper, bar, gear, ViewCube, HUD, side panel |
| [`src/viewer/kamera.ts`](src/viewer/kamera.ts) | near/far on every move, grid according to the scene, views, framing |
| [`src/viewer/lage.ts`](src/viewer/lage.ts) | Pins, plan (image) and calibration, picking points on the plan, dragging with the lock and the GOK rule |
| [`src/viewer/kanal.ts`](src/viewer/kanal.ts) | Types and events from the viewer to the app (`lage`, `station`, `gok`, `geprueft`) |
| [`src/viewer/rahmen.ts`](src/viewer/rahmen.ts) | Frame: x = E − E₀, y = NHN (exaggerated), −z = N − N₀ |
| [`src/viewer/baugrund.ts`](src/viewer/baugrund.ts) | Einheiten, Bohrungen and properties of the IFC |

Notes:

- **`dist/` is in the repo**: after changing the app or the viewer, `npm run build` and commit
  `dist/`.
- **Navigation**:
  - Left button rotates, right button pans, the wheel zooms towards the mouse.
  - Double click sets the orbit point; the gear has *Orbit um Mauspunkt*.
  - While moving, no shadows (smooth); when it stops, with postproduction. At rest nothing is redrawn.
- `npm run vendor` (called by `dev` and `build`) copies `web-ifc.wasm` to `public/vendor/` and the
  icons in use to `src/icons.gen.json`: **nothing is downloaded from unpkg or api.iconify.design**.
- **web-ifc pinned at 0.0.77** ([X9](../../docs/16_lessons_learned.md#x-working-environment)).
- The geotechnical classes are added to the importer
  ([M2](../../docs/16_lessons_learned.md#m-model-ifc-and-that-open)).
- Our own IFC is loaded without `COORDINATE_TO_ORIGIN`
  ([M19](../../docs/16_lessons_learned.md#m-model-ifc-and-that-open)).
- The bar does not use `bim-toolbar-section`, because it brings the labels back
  ([M26](../../docs/16_lessons_learned.md#m-model-ifc-and-that-open)).

Up: [Documentation index](../../docs/README.md)

Related: [21 Step app and norms](../../docs/21_app_schritte_normen.md) · [20 Lage and Prüfstand](../../docs/20_lage_pruefung_viewer.md) · [18 Layer modeler](../../docs/18_layer_modeler.md) · [Architecture §8.3](../../docs/ARCHITECTURE_BAUGRUNDMODELL.md#83-frontend-integration-sketch-api-v36) · [IFC spike](../../spikes/ifc_thatopen/README.md)
