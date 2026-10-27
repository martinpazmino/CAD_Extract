// Kopiert web-ifc-WASM und den Fragments-Worker nach public/vendor: der Viewer laedt nichts von unpkg
// (IfcLoader.autoSetWasm und FragmentsManager.getWorker holen sonst Dateien aus dem Netz).
import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";

const require = createRequire(import.meta.url);
const ziel = new URL("../public/vendor/", import.meta.url).pathname;
mkdirSync(ziel, { recursive: true });
const webIfc = dirname(require.resolve("web-ifc"));
for (const f of ["web-ifc.wasm", "web-ifc-mt.wasm"]) copyFileSync(join(webIfc, f), join(ziel, f));
copyFileSync(require.resolve("@thatopen/fragments/worker"), join(ziel, "worker.mjs"));
console.log("vendor:", ziel);
