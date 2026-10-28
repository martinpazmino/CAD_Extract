// End-to-End-Pruefung der Streamlit-App (Chromium/Playwright, ohne Bildschirm), Bilder in <ausgabe>:
//   A  Beispiel waehlen: Tabellen und Bohrungen im Viewer vor dem Modell -> "Baugrundmodell erzeugen" -> Modell
//   B  im Viewer eine Bohrung entlang der Reihe ziehen -> Ereignis -> Python rechnet nach -> Viewer laedt neu
//   C  Stand einchecken
//   D  Lageplan-PDF hochladen (scripts/testplan.py) -> Unterlage im Viewer -> "Im Viewer bearbeiten"
//
//   streamlit run app.py --server.headless true --server.port 8599   (in einem zweiten Terminal)
//   node scripts/check_app.mjs http://localhost:8599 <ausgabe> [--plan <plan-ordner>] [--pdf <datei.pdf>]
import { createRequire } from "node:module";
import { mkdirSync } from "node:fs";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PFAD ?? "playwright");
const argv = process.argv.slice(2);
const [url, aus = "check_app"] = argv;
const option = (name) => (argv.includes(name) ? argv[argv.indexOf(name) + 1] : null);
const planOrdner = option("--plan");
const pdf = option("--pdf");
mkdirSync(aus, { recursive: true });

const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1500, height: 1200 } });
const fehler = [];
const pruefungen = [];
page.on("pageerror", (e) => fehler.push(String(e)));

function pruefe(name, ok, info = "") {
  pruefungen.push({ name, ok: !!ok });
  console.log(`${ok ? "OK  " : "FEHL"} ${name}${info ? ` – ${info}` : ""}`);
}

async function viewerFrame() {
  for (const f of page.frames()) if (f.url().includes("baugrund_viewer")) return f;
  return null;
}

async function viewerStatus() {
  const f = await viewerFrame();
  return f ? await f.evaluate(() => ({ ...window.baugrund, ereignisse: undefined })).catch(() => null) : null;
}

async function warteAufLauf() {
  await page.waitForTimeout(800);
  await page.waitForFunction(() => !document.querySelector('[data-testid="stStatusWidget"]'), null, { timeout: 600000 })
    .catch(() => {});
  await page.waitForTimeout(500);
}

async function warteViewer(bedingung, timeout = 300000) {
  const start = Date.now();
  while (Date.now() - start < timeout) {
    const st = await viewerStatus();
    if (st && (st.fehler || bedingung(st))) return st;
    await page.waitForTimeout(1000);
  }
  return await viewerStatus();
}

async function ausnahmen(wo) {
  const a = await page.locator('[data-testid="stException"]').allTextContents();
  if (a.length) fehler.push(...a.map((t) => `[${wo}] ${t.slice(0, 400)}`));
}

/** Aktion in Streamlit ausfuehren und warten, bis der Viewer den neuen Stand gerendert hat. */
async function mitRender(aktion, timeout = 120000) {
  const vorher = (await viewerStatus())?.renders ?? 0;
  await aktion();
  await warteAufLauf();
  return await warteViewer((s) => s.renders > vorher, timeout);
}

async function beispiel(name) {
  await page.locator('[data-testid="stSidebar"] [data-testid="stSelectbox"]').first().click();
  await page.getByRole("option", { name }).click();
  await warteAufLauf();
  // gespeicherten Projektstand verwerfen: jede Pruefung beginnt ohne Korrekturen
  await page.getByRole("button", { name: "Korrekturen verwerfen" }).click();
  await warteAufLauf();
}

try {
  await page.goto(url);
  await page.getByText("Baugrundmodell aus dem Bodengutachten").waitFor({ timeout: 60000 });
  await page.screenshot({ path: `${aus}/0_start.png` });

  if (pdf) {
    await page.locator('[data-testid="stFileUploaderDropzoneInput"]').first().setInputFiles(pdf);
    await warteAufLauf();
    await ausnahmen("pdf");
    pruefe("PDF ausgewertet", await page.getByText("Bohrungen erkannt").count());
  }

  // ---------------------------------------------------------------- A: vor dem Modell, dann erzeugen
  await beispiel("Talheim – echte Daten ohne Koordinaten (Reihe)");
  await ausnahmen("talheim");
  let st = await warteViewer((s) => s.lage?.nadeln > 0 && !s.geladen, 120000);
  pruefe("Tabellen vor dem Modell", await page.locator('[data-testid="stDataFrame"]').count() >= 1);
  pruefe("Viewer zeigt Bohrungen vor dem Modell", st?.lage?.nadeln >= 8 && !st.geladen, `${st?.lage?.nadeln} Bohrungen, Modell ${st?.geladen}`);
  await page.screenshot({ path: `${aus}/A1_vor_dem_modell.png`, fullPage: true });
  await mitRender(() => page.getByRole("button", { name: "Baugrundmodell erzeugen" }).click());
  st = await warteViewer((s) => s.geladen);
  await ausnahmen("erzeugen");
  pruefe("Modell erzeugt und im Viewer", st?.geladen && st.einheiten.length > 0, `${st?.einheiten?.length} Einheiten`);
  console.log("Viewer nach dem Erzeugen:", JSON.stringify({ instanz: st?.instanz, ifc: st?.geladeneIfc, renders: st?.renders }));
  const chips = await page.locator(".chip").allTextContents();
  console.log("Chips:", chips.join(" | "));
  await page.screenshot({ path: `${aus}/A2_modell.png`, fullPage: true });

  // ---------------------------------------------------------------- B: im Viewer ziehen -> Python rechnet nach
  const frame = await viewerFrame();
  await frame.locator('bim-button[label="Lage bearbeiten"]').first().click();      // scrollt den Viewer ins Bild
  await page.waitForTimeout(4000);
  const rahmen = await page.locator('iframe[title*="baugrund_viewer"]').boundingBox();
  // Marken folgen der Kamera erst im naechsten Bild (SwiftShader: langsam): Bilder abwarten, bei Bedarf wiederholen
  const bilder = () => frame.evaluate(() => new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r))));
  const vorher = st.ladungen;
  // Lage-Modus aktiv und Kamera in Ruhe (beim ersten Laden nach dem Start dauert die Kamerafahrt in SwiftShader)
  await frame.waitForFunction(() => window.viewer?.editor?.aktiv && !window.viewer.world.camera.controls.active,
                              null, { timeout: 60000, polling: 250 }).catch(() => {});
  const t0 = Date.now();
  const sichtbar = await frame.waitForFunction(() => {
    const e = window.viewer.editor;
    const s = [...e.nadeln.values()].find((n) => n.daten.code === "BK2");
    return !!e.markenPunkt(s.daten.id);
  }, null, { timeout: 90000, polling: 500 }).then(() => true).catch(() => false);
  console.log(`Marke BK2 sichtbar: ${sichtbar} nach ${Date.now() - t0} ms`);
  for (let versuch = 0; versuch < 3; versuch++) {
    await bilder();
    const marke = await frame.evaluate(() => {
      const e = window.viewer.editor;
      const s = [...e.nadeln.values()].find((n) => n.daten.code === "BK2");
      return { punkt: e.markenPunkt(s.daten.id), station: s.daten.x };
    });
    console.log("Marke BK2:", JSON.stringify(marke), "Rahmen:", JSON.stringify(rahmen));
    if (marke.punkt) {
      const von = { x: rahmen.x + marke.punkt.x, y: rahmen.y + marke.punkt.y };
      await page.mouse.move(von.x, von.y);
      await page.mouse.down();
      await page.mouse.move(von.x - 25, von.y, { steps: 6 });
      await page.mouse.move(von.x - 50, von.y, { steps: 6 });
      await page.mouse.up();
    }
    if ((await frame.evaluate(() => window.baugrund.ereignisse.length)) > 0) break;
    await page.waitForTimeout(3000);
  }
  console.log("Ereignisse im Viewer:", JSON.stringify(await frame.evaluate(() => window.baugrund.ereignisse)));
  await warteAufLauf();
  st = await warteViewer((s) => s.ladungen > vorher, 120000);
  const toast = await page.locator('[data-testid="stToast"]').allTextContents();
  pruefe("Ziehen im Viewer -> Modell nachgefuehrt", st?.ladungen > vorher, `Ladungen ${vorher} -> ${st?.ladungen}; ${toast.join(" | ").slice(0, 120)}`);
  console.log("Viewer nach dem Ziehen:", JSON.stringify({ instanz: st?.instanz, ifc: st?.geladeneIfc, renders: st?.renders }));
  await page.screenshot({ path: `${aus}/B1_gezogen.png`, fullPage: true });

  // ---------------------------------------------------------------- C: einchecken
  await page.getByRole("button", { name: "Stand einchecken" }).click();
  await page.getByRole("button", { name: "Einchecken", exact: true }).click();
  await warteAufLauf();
  const eingecheckt = (await page.locator(".chip").allTextContents()).find((c) => c.startsWith("Eingecheckt"));
  pruefe("Stand eingecheckt", !!eingecheckt, eingecheckt ?? "");
  await ausnahmen("einchecken");

  // ---------------------------------------------------------------- D: Lageplan hochladen, im Viewer bearbeiten
  if (planOrdner) {
    await beispiel("Demo – synthetisch, 12 Bohrungen mit Linse");
    await page.getByRole("tab", { name: /Lage & Unterlage/ }).click();
    await page.locator('[data-testid="stFileUploaderDropzoneInput"]').nth(1).setInputFiles(`${planOrdner}/plan.pdf`);
    await warteAufLauf();
    st = await warteViewer((s) => s.lage?.unterlage?.art === "plan", 120000);
    pruefe("Lageplan als Unterlage im Viewer", st?.lage?.unterlage?.art === "plan", JSON.stringify(st?.lage?.unterlage));
    await page.getByRole("button", { name: "Im Viewer bearbeiten" }).click();
    await warteAufLauf();
    await page.waitForTimeout(4000);
    const aktiv = await (await viewerFrame()).evaluate(() => window.viewer.editor.aktiv);
    pruefe("„Im Viewer bearbeiten“ schaltet den Lage-Modus ein", aktiv);
    await ausnahmen("lageplan");
    await page.screenshot({ path: `${aus}/D1_lageplan.png`, fullPage: true });
  }
} finally {
  const fehlgeschlagen = pruefungen.filter((p) => !p.ok);
  console.log(`\n${pruefungen.length - fehlgeschlagen.length}/${pruefungen.length} Pruefungen bestanden`);
  console.log("Seitenfehler:", fehler.length ? fehler : "keine");
  await browser.close();
  if (fehler.length || fehlgeschlagen.length) process.exitCode = 1;
}
