// Headless-Pruefung des Viewers (Chromium/Playwright): IFC laden, Einheiten zaehlen, Auswahl, Schnitt, Bilder.
//   npm run build && node scripts/check.mjs <modell.ifc> [ausgabeordner] [ueberhoehung]
// Das IFC wird nach dist/modelle/ kopiert (vite preview liefert nur dist/ aus).
import { createRequire } from "node:module";
import { copyFileSync, mkdirSync } from "node:fs";
import { basename } from "node:path";
import { preview } from "vite";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const quelle = process.argv[2] ?? "public/modelle/demo.ifc";
const aus = process.argv[3] ?? "check";
mkdirSync(aus, { recursive: true });
mkdirSync("dist/modelle", { recursive: true });
copyFileSync(quelle, `dist/modelle/${basename(quelle)}`);
const ifc = `modelle/${basename(quelle)}`;

const server = await preview({ preview: { port: 4174, strictPort: true }, logLevel: "warn" });
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1400, height: 860 } });
const fehler = [];
page.on("pageerror", (e) => fehler.push(String(e)));
page.on("console", (m) => m.type() === "error" && fehler.push(m.text()));
try {
  await page.goto(`http://localhost:4174/?ifc=${ifc}&ueberhoehung=${process.argv[4] ?? "1"}`);
  await page.waitForFunction(() => window.baugrund?.geladen || window.baugrund?.fehler, null, { timeout: 180000 });
  const st = await page.evaluate(() => window.baugrund);
  console.log("Status:", JSON.stringify(st));
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${aus}/1_modell.png` });
  await page.click("#einheiten li:nth-child(1) span:nth-child(3)");
  await page.waitForSelector("#eigenschaften:not([hidden])", { timeout: 20000 });
  await page.waitForTimeout(1500);
  await page.screenshot({ path: `${aus}/2_auswahl.png` });
  console.log("Eigenschaften:", (await page.textContent("#auswahl-inhalt")).slice(0, 300));
  await page.click("#auswahl-zu");
  await page.click("#bohrsaeulen");
  await page.click("#schnitt-ow");
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${aus}/3_schnitt.png` });
  await page.click("#bohrsaeulen");
  await page.click("#transparent");
  await page.click("#schnitt-weg");
  await page.waitForTimeout(2500);
  await page.screenshot({ path: `${aus}/4_durchscheinend.png` });
  // Klick in die Bildmitte: Raycast muss auch mit Ueberhoehung ein Element treffen
  await page.click("#transparent");
  const v = await page.locator("#viewer").boundingBox();
  await page.mouse.click(v.x + v.width / 2, v.y + v.height / 2);
  await page.waitForTimeout(1500);
  console.log("Klick Mitte:", await page.evaluate(() => window.baugrund.auswahl));
  await page.screenshot({ path: `${aus}/5_klick.png` });
} finally {
  console.log("Fehler:", fehler.length ? fehler : "keine");
  await browser.close();
  server.httpServer.close();
}
if (fehler.length) process.exit(1);
