// Kopiert das web-ifc-WASM nach public/vendor: der Viewer laedt nichts von unpkg (IfcLoader.autoSetWasm
// holt es sonst aus dem Netz). Den Fragments-Worker liefert Vite selbst mit (import ...?url in main.ts).
import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";

const require = createRequire(import.meta.url);
const ziel = new URL("../public/vendor/", import.meta.url).pathname;
mkdirSync(ziel, { recursive: true });
const webIfc = dirname(require.resolve("web-ifc"));
for (const f of ["web-ifc.wasm", "web-ifc-mt.wasm"]) copyFileSync(join(webIfc, f), join(ziel, f));
console.log("vendor:", ziel);
