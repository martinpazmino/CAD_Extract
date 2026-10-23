// Spike: IFC4X3 (IfcBorehole / IfcGeomodel / IfcGeotechnicalStratum) -> That Open Fragments
//
//   npm install && node thatopen_import_spike.mjs baugrund_spike.ifc default   (Importer-Standard)
//                  node thatopen_import_spike.mjs baugrund_spike.ifc add       (Geotechnik-Klassen ergaenzt)
//
// Befund (fragments 3.6.0 / web-ifc 0.0.78): web-ifc erzeugt Meshes fuer IfcGeotechnicalStratum,
// der IfcImporter verwirft sie aber, solange die Klassen nicht in importer.classes.elements stehen.
import { readFileSync, writeFileSync } from "node:fs";
import * as path from "node:path";
import * as WEBIFC from "web-ifc";
import * as FRAGS from "@thatopen/fragments";

const ifcPath = process.argv[2];
const bytes = new Uint8Array(readFileSync(ifcPath));
const wasmDir = path.resolve("node_modules/web-ifc") + "/";

// 1) web-ifc direkt: welche IFC-Klassen liefern Meshes?
const api = new WEBIFC.IfcAPI();
api.SetWasmPath(wasmDir, true);
await api.Init();
const mid = api.OpenModel(bytes);
console.log("schema:", api.GetModelSchema(mid));
const perType = {};
api.StreamAllMeshes(mid, (mesh) => {
  const t = api.GetNameFromTypeCode(api.GetLineType(mid, mesh.expressID));
  perType[t] = (perType[t] ?? 0) + 1;
});
console.log("web-ifc meshes per type:", perType);
api.CloseModel(mid);

// 2) That Open IfcImporter -> .frag
const importer = new FRAGS.IfcImporter();
importer.wasm = { absolute: true, path: wasmDir };
const geo = [WEBIFC.IFCBOREHOLE, WEBIFC.IFCGEOMODEL, WEBIFC.IFCGEOTECHNICALSTRATUM];
const before = geo.map((c) => importer.classes.elements.has(c));
console.log("geotech classes in default importer.classes.elements:", before);
const mode = process.argv[3] ?? "default";
if (mode === "add") for (const c of geo) importer.classes.elements.add(c);
const frag = await importer.process({ bytes, raw: true });
writeFileSync(`baugrund_${mode}.frag`, frag);
const model = new FRAGS.SingleThreadedFragmentsModel(`m_${mode}`, frag, true);
await model.ready;
console.log(`[${mode}] frag bytes:`, frag.length);
console.log(`[${mode}] categories:`, model.getCategories());
const withGeo = model.getItemsWithGeometry();
console.log(`[${mode}] items with geometry:`, withGeo.length);
const cats = model.getItemsOfCategories([/BOREHOLE/, /GEOMODEL/, /GEOTECHNICALSTRATUM/]);
console.log(`[${mode}] items per geotech category:`, Object.fromEntries(Object.entries(cats).map(([k, v]) => [k, v.length])));
model.dispose();
