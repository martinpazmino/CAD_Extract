// End-to-End-Pruefung der Streamlit-App (Chromium/Playwright, ohne Bildschirm):
// Beispiel waehlen bzw. PDF hochladen -> Modell -> Viewer-Komponente geladen? Bilder in <ausgabe>.
//   streamlit run app.py --server.headless true --server.port 8599   (in einem zweiten Terminal)
//   node scripts/check_app.mjs http://localhost:8599 <ausgabe> [beispiel-text ...] [--pdf <datei.pdf>]
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const [url, aus = "check_app", ...rest] = process.argv.slice(2);
mkdirSync(aus, { recursive: true });
const pdfIdx = rest.indexOf("--pdf");
const pdf = pdfIdx >= 0 ? rest[pdfIdx + 1] : null;
const beispiele = pdfIdx >= 0 ? rest.slice(0, pdfIdx) : rest;

const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1500, height: 1100 } });
const fehler = [];
page.on("pageerror", (e) => fehler.push(String(e)));

async function viewerFrame() {
  for (const f of page.frames()) if (f.url().includes("baugrund_viewer")) return f;
  return null;
}

async function ladungen() {
  const f = await viewerFrame();
  return { f, n: f ? ((await f.evaluate(() => window.baugrund?.ladungen ?? 0).catch(() => 0)) ?? 0) : 0 };
}

// Neues Modell = Ladezaehler gestiegen; wird der Viewer neu eingehaengt (neuer iframe), zaehlt er von 0
async function viewerStatus(vorher, timeout = 300000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const f = await viewerFrame();
    const st = f ? await f.evaluate(() => window.baugrund).catch(() => null) : null;
    const schwelle = f === vorher.f ? vorher.n : 0;
    if (st?.fehler || (st?.ladungen ?? 0) > schwelle) return st;
    await page.waitForTimeout(1000);
  }
  return null;
}

async function warteAufLauf() {
  await page.waitForTimeout(800);
  await page.waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, { timeout: 600000 })
    .catch(() => {});
}

try {
  await page.goto(url);
  await page.getByText("Baugrundmodell aus dem Bodengutachten").waitFor({ timeout: 60000 });
  await page.screenshot({ path: `${aus}/0_start.png` });
  let n = 1;
  const laeufe = pdf ? [["pdf", pdf]] : beispiele.map((b) => ["beispiel", b]);
  for (const [art, wert] of laeufe) {
    const vorher = await ladungen();
    if (art === "pdf") {
      await page.locator('[data-testid="stFileUploaderDropzoneInput"]').setInputFiles(wert);
    } else {
      await page.locator('[data-testid="stSidebar"] [data-testid="stSelectbox"]').first().click();
      await page.getByRole("option", { name: wert }).click();
    }
    await warteAufLauf();
    const st = await viewerStatus(vorher);
    const kennzahlen = await page.locator('[data-testid="stMetricValue"]').allTextContents();
    const chips = await page.locator(".chip").allTextContents();
    const warnungen = await page.locator('[data-testid="stAlert"]').allTextContents();
    const ausnahmen = await page.locator('[data-testid="stException"]').allTextContents();
    if (ausnahmen.length) fehler.push(...ausnahmen.map((a) => `[${wert}] ${a.slice(0, 400)}`));
    console.log(`[${wert}] Kennzahlen: ${kennzahlen.join(" | ")}`);
    console.log(`[${wert}] Chips: ${chips.join(" | ")}`);
    console.log(`[${wert}] Hinweise: ${warnungen.map((w) => w.slice(0, 140)).join(" || ")}`);
    console.log(`[${wert}] Viewer: ${JSON.stringify(st)}`);
    await page.waitForTimeout(3000);
    await page.screenshot({ path: `${aus}/${n}_${art}.png`, fullPage: true });
    n += 1;
  }
} finally {
  console.log("Seitenfehler:", fehler.length ? fehler : "keine");
  await browser.close();
}
