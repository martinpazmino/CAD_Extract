---
title: "Visor del Baugrundmodell (That Open)"
date: 2026-10-27
tags: [visor, thatopen, ifc]
aliases: [Visor web]
---

# Visor del Baugrundmodell (That Open Engine)

Vite + TypeScript + `@thatopen/components` 3.6. Abre el IFC 4.3 del
[modelador](../../services/modeler/README.md): unidades del modelo (color, volumen, visibilidad),
sondeos con su código, propiedades con procedencia al hacer clic, unidades translúcidas,
exageración vertical, cortes O–W / N–S y por doble clic. Diseño: [18 Modelador de capas](../../docs/18_modelador_capas.md#5-visor-appsweb).

```bash
cd apps/web
npm install
cp <modelo.ifc> public/modelle/            # los IFC no se suben al repo
npm run dev                                 # http://localhost:5173/?ifc=modelle/<modelo.ifc>&ueberhoehung=5
npm run build && node scripts/check.mjs <modelo.ifc> <carpeta_capturas> 5   # prueba sin pantalla (Playwright)
```

- `npm run vendor` (lo llaman `dev` y `build`) copia `web-ifc.wasm` y el worker de Fragments a
  `public/vendor/`: el visor no descarga nada de unpkg.
- **web-ifc fijado en 0.0.77**: el `web-ifc.wasm` de navegador de 0.0.78 no casa con su propio JS
  (`StreamMeshes called with 4 arguments, expected 3`); en Node 0.0.78 funciona
  ([lección X9](../../docs/16_lecciones_aprendidas.md#x-entorno-de-trabajo)).
- Las clases geotécnicas se añaden al importer en `onIfcImporterInitialized`; sin eso That Open
  descarta los estratos ([M2](../../docs/16_lecciones_aprendidas.md#m-modelo-ifc-y-that-open)).

Up: [Índice de documentación](../../docs/README.md)

Related: [18 Modelador de capas](../../docs/18_modelador_capas.md) · [Arquitectura §8.3](../../docs/ARQUITECTURA_BAUGRUNDMODELL.md#83-integración-en-el-frontend-esbozo-api-v36) · [Spike IFC](../../spikes/ifc_thatopen/README.md)
