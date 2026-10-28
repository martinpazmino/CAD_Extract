// Kopiert das web-ifc-WASM nach public/vendor: der Viewer laedt nichts von unpkg (IfcLoader.autoSetWasm
// holt es sonst aus dem Netz). Den Fragments-Worker liefert Vite selbst mit (import ...?url in main.ts).
// Dazu die Icons offline: BUI (iconify-icon) holt jedes Icon sonst zur Laufzeit von api.iconify.design;
// alle in src/ benutzten Namen (prefix:name) kommen aus den @iconify-json-Paketen nach src/icons.gen.json.
import { copyFileSync, mkdirSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join } from "node:path";

const require = createRequire(import.meta.url);
const ziel = new URL("../public/vendor/", import.meta.url).pathname;
mkdirSync(ziel, { recursive: true });
const webIfc = dirname(require.resolve("web-ifc"));
for (const f of ["web-ifc.wasm", "web-ifc-mt.wasm"]) copyFileSync(join(webIfc, f), join(ziel, f));
console.log("vendor:", ziel);

// ------------------------------------------------------------------ Icons
const SAMMLUNGEN = ["mdi", "eos-icons"];
const INTERN = ["eos-icons:loading"];                  // von BUI selbst benutzt (Ladeanzeige der Knoepfe)
const src = new URL("../src/", import.meta.url).pathname;
const namen = new Set(INTERN);
for (const f of readdirSync(src)) {
  if (!f.endsWith(".ts")) continue;
  const text = readFileSync(join(src, f), "utf8");
  for (const m of text.matchAll(/["'`](mdi|eos-icons):([a-z0-9-]+)["'`]/g)) namen.add(`${m[1]}:${m[2]}`);
}
const ausgabe = [];
for (const prefix of SAMMLUNGEN) {
  const daten = require(`@iconify-json/${prefix}/icons.json`);
  const icons = {};
  for (const n of namen) {
    const [p, name] = n.split(":");
    if (p !== prefix) continue;
    let schluessel = name;
    const alias = daten.aliases?.[name];
    if (alias && !alias.rotate && !alias.hFlip && !alias.vFlip) schluessel = alias.parent;
    const icon = daten.icons[schluessel];
    if (!icon) throw new Error(`Icon fehlt: ${n}`);
    icons[name] = icon;
  }
  if (Object.keys(icons).length) {
    ausgabe.push({ prefix, icons, width: daten.width ?? 16, height: daten.height ?? 16 });
  }
}
writeFileSync(join(src, "icons.gen.json"), JSON.stringify(ausgabe));
console.log("icons:", [...namen].sort().join(" "));
