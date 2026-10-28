// Headless-Pruefung des Viewers (Chromium/Playwright) in drei Teilen, mit Bildern:
//   A  grosses Modell (Trasse > 5 km): Laden, Kamera-Grenzen, Ansichten, Koordinaten, Auswahl, Transparenz, Schnitt
//   B  Lageplan (scripts/testplan.py): kalibrieren ueber zwei Bohrungen, Bohrungen ohne Lage auf den Plan ziehen
//   C  Laengsschnitt: kalibrieren (Station/Hoehe), Bohrung entlang der Reihe auf ihre Saeule ziehen
//
//   npm run build && python ../../scripts/testplan.py <plan-ordner>
//   node scripts/check.mjs <modell.ifc> <plan-ordner> [ausgabeordner]
// Die Dateien werden nach dist/modelle/ kopiert (vite preview liefert nur dist/ aus).
import { createRequire } from "node:module";
import { copyFileSync, mkdirSync, readFileSync } from "node:fs";
import { basename, join } from "node:path";
import { preview } from "vite";

const require = createRequire(import.meta.url);
const { chromium } = require("playwright");
const [ifcQuelle = "public/modelle/demo.ifc", planOrdner, aus = "check"] = process.argv.slice(2);
mkdirSync(aus, { recursive: true });
mkdirSync("dist/modelle", { recursive: true });
copyFileSync(ifcQuelle, `dist/modelle/${basename(ifcQuelle)}`);
for (const f of ["plan.png", "schnitt.png", "args_plan.json", "args_schnitt.json"]) {
  if (planOrdner) copyFileSync(join(planOrdner, f), `dist/modelle/${f}`);
}

const server = await preview({ preview: { port: 4174, strictPort: true }, logLevel: "warn" });
const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1500, height: 900 } });
const fehler = [];
const pruefungen = [];
page.on("pageerror", (e) => fehler.push(String(e.stack || e)));
page.on("console", (m) => m.type() === "error" && fehler.push(m.text()));
page.on("request", (r) => !r.url().startsWith("http://localhost") && fehler.push(`externe Anfrage: ${r.url()}`));

function pruefe(name, ok, info = "") {
  pruefungen.push({ name, ok: !!ok, info });
  console.log(`${ok ? "OK  " : "FEHL"} ${name}${info ? ` – ${info}` : ""}`);
}
const st = () => page.evaluate(() => ({ ...window.baugrund, ereignisse: undefined }));
const ereignisse = () => page.evaluate(() => window.baugrund.ereignisse);
const ruhe = (ms = 1500) => page.waitForTimeout(ms);
// Marken (DOM) folgen der Kamera erst im naechsten Bild; SwiftShader braucht dafuer bis zu einer Sekunde
const bilder = (n = 2) => page.evaluate((k) => new Promise((fertig) => {
  const schritt = (i) => (i <= 0 ? fertig() : requestAnimationFrame(() => schritt(i - 1)));
  schritt(k);
}), n);
const ohnePost = () => page.evaluate(() => { window.viewer.world.renderer.postproduction.enabled = false; });
const knopf = (label) => page.locator(`bim-button[label="${label}"]`).first();

async function ziehen(von, nach, umschalt = false) {
  await page.mouse.move(von.x, von.y);
  await page.mouse.down();
  if (umschalt) await page.keyboard.down("Shift");
  await page.mouse.move((von.x + nach.x) / 2, (von.y + nach.y) / 2, { steps: 6 });
  await page.mouse.move(nach.x, nach.y, { steps: 6 });
  await page.mouse.up();
  if (umschalt) await page.keyboard.up("Shift");
  await ruhe(600);
}

try {
  // ---------------------------------------------------------------- A: grosses Modell
  await page.goto(`http://localhost:4174/?ifc=modelle/${basename(ifcQuelle)}&ueberhoehung=5`);
  await page.waitForFunction(() => window.baugrund?.geladen || window.baugrund?.fehler, null, { timeout: 240000 });
  await ruhe(2500);
  let s = await st();
  pruefe("Modell geladen", s.geladen && !s.fehler, `${s.einheiten.length} Einheiten, ${s.marken} Marken`);
  const k = await page.evaluate(() => {
    const v = window.viewer;
    const b = v.modell().box;
    return { far: v.world.camera.three.far, near: v.world.camera.three.near, laenge: b.max.x - b.min.x,
             radius: v.KAMERA.szeneKugel().radius };
  });
  pruefe("Kamera sieht das ganze Modell (far > Laenge)", k.far > k.laenge, `near ${k.near.toFixed(2)} far ${Math.round(k.far)} Laenge ${Math.round(k.laenge)} m`);
  await page.screenshot({ path: `${aus}/A1_iso.png` });

  const v = await page.locator("#viewer").boundingBox();
  const mitte = { x: v.x + v.width / 2, y: v.y + v.height / 2 };
  for (let i = 0; i < 12; i++) {                    // nah heran: near muss mitgehen, sonst wird abgeschnitten
    await page.mouse.move(mitte.x, mitte.y);
    await page.mouse.wheel(0, -400);
    await page.waitForTimeout(120);
  }
  await ruhe(2000);
  const k2 = await page.evaluate(() => ({ near: window.viewer.world.camera.three.near, d: window.viewer.world.camera.controls.distance }));
  pruefe("near folgt der Kamera (nah)", k2.near < k.near || k2.near <= 0.05, `near ${k2.near.toFixed(3)} bei Abstand ${k2.d.toFixed(0)} m`);
  await page.screenshot({ path: `${aus}/A2_nah.png` });

  await knopf("Oben").click();
  await ruhe(2500);
  await page.screenshot({ path: `${aus}/A3_oben.png` });
  await page.locator("bim-button.koord").click();
  await page.mouse.move(mitte.x + 3, mitte.y + 2);
  await ruhe(800);
  const hud = await page.textContent("#hud");
  pruefe("Koordinatenanzeige in Landeskoordinaten", /R 5\d\d\.\d{3}/.test(hud) && /m NHN/.test(hud), hud);

  await page.locator("#einheiten li").first().click();
  await page.waitForSelector("#eigenschaften:not([hidden])", { timeout: 20000 });
  await ruhe();
  const eig = await page.textContent("#auswahl-inhalt");
  pruefe("Auswahl zeigt Eigenschaften", eig.includes("CPset_Modelleinheit"), (await page.textContent("#auswahl-name")));
  await page.screenshot({ path: `${aus}/A4_auswahl.png` });
  await knopf("Iso").click();
  await knopf("Transparenz").click();
  await ruhe(2500);
  await page.screenshot({ path: `${aus}/A5_transparenz.png` });
  await knopf("Transparenz").click();
  await knopf("O–W").click();
  await ruhe(2500);
  await page.screenshot({ path: `${aus}/A6_schnitt.png` });
  await knopf("Löschen").click();

  // ---------------------------------------------------------------- B: Lageplan
  const wPlan = JSON.parse(readFileSync(join(planOrdner, "wahrheit_plan.json"), "utf8"));
  await page.goto("http://localhost:4174/?bohrungen=modelle/args_plan.json");
  await page.waitForFunction(() => (window.baugrund?.renders ?? 0) >= 1, null, { timeout: 60000 });
  await ohnePost();
  await ruhe(2000);
  s = await st();
  pruefe("Lageplan: Bohrungen und Unterlage", s.lage.nadeln === 12 && s.lage.ohneLage === 2 && s.lage.unterlage?.art === "plan",
         JSON.stringify(s.lage));
  await knopf("Lage bearbeiten").click();
  await ruhe(2500);
  pruefe("Lage-Modus: Draufsicht orthografisch", (await page.evaluate(() => window.viewer.world.camera.projection.current)) === "Orthographic");
  const schirm = (u, v_) => page.evaluate(([a, b]) => window.viewer.editor.bildZuSchirm(a, b), [u, v_]);
  async function passpunkt(k, code) {
    await page.locator(`.lage-panel bim-button[label="Punkt ${k + 1}"]`).click();
    const [u, v_] = wPlan.bohrungen[code].px;
    const p = await schirm(u, v_);
    await page.mouse.click(p.x, p.y);
    await ruhe(400);
    await page.locator(".lage-panel select").nth(k).selectOption({ label: code });
  }
  await passpunkt(0, "B 1");
  await passpunkt(1, "B 11");
  await page.locator('.lage-panel bim-button[label="Kalibrierung übernehmen"]').click();
  await ruhe(1500);
  s = await st();
  const kal = (await ereignisse()).find((e) => e.typ === "kalibrierung");
  pruefe("Kalibrierung als Ereignis", kal && kal.punkte.length === 2, JSON.stringify(kal?.punkte?.map((p) => [Math.round(p.u), Math.round(p.v)])));
  pruefe("Massstab und Drehung erkannt", /1:(49\d|50\d)\b/.test(s.lage.text) && /Drehung (9,[6-9]|10,[0-4])/.test(s.lage.text), s.lage.text);
  // Lagepruefung: Marke von B 7 liegt auf ihrem Symbol im Plan
  const b7 = await page.evaluate(() => {
    const e = window.viewer.editor;
    const id = [...e.nadeln.values()].find((n) => n.daten.code === "B 7").daten.id;
    return e.markenPunkt(id);
  });
  const sym7 = await schirm(...wPlan.bohrungen["B 7"].px);
  pruefe("Plan und Bohrungen decken sich (B 7)", Math.hypot(b7.x - sym7.x, b7.y - sym7.y) < 4, `${Math.hypot(b7.x - sym7.x, b7.y - sym7.y).toFixed(1)} px`);
  for (const code of wPlan.ohne_lage) {
    const park = page.locator(".lage-panel .park", { hasText: code });
    const von = await park.boundingBox();
    const ziel = await schirm(...wPlan.bohrungen[code].px);
    await ziehen({ x: von.x + von.width / 2, y: von.y + von.height / 2 }, ziel);
    const e = (await ereignisse()).filter((x) => x.typ === "lage").at(-1);
    const wahr = wPlan.bohrungen[code];
    const abw = e ? Math.hypot(e.x - wahr.x, e.y - wahr.y) : Infinity;
    pruefe(`${code} auf den Plan gezogen`, abw < 0.5, e ? `R ${e.x} H ${e.y} (Abweichung ${abw.toFixed(2)} m)` : "kein Ereignis");
  }
  await page.screenshot({ path: `${aus}/B1_lageplan.png` });
  // Marke verschieben: B 2 um eine Strecke versetzen -> Ereignis mit neuer Lage
  const b2 = await page.evaluate(() => {
    const e = window.viewer.editor;
    return e.markenPunkt([...e.nadeln.values()].find((n) => n.daten.code === "B 2").daten.id);
  });
  await ziehen(b2, { x: b2.x + 60, y: b2.y + 30 });
  const e2 = (await ereignisse()).filter((x) => x.typ === "lage").at(-1);
  pruefe("Marke B 2 verschoben", e2 && Math.hypot(e2.x - 565045, e2.y - 5933010) > 1, e2 ? `R ${e2.x} H ${e2.y}` : "");
  await page.screenshot({ path: `${aus}/B2_verschoben.png` });

  // ---------------------------------------------------------------- C: Laengsschnitt
  const wS = JSON.parse(readFileSync(join(planOrdner, "wahrheit_schnitt.json"), "utf8"));
  await page.goto("http://localhost:4174/?bohrungen=modelle/args_schnitt.json");
  await page.waitForFunction(() => (window.baugrund?.renders ?? 0) >= 1, null, { timeout: 60000 });
  await ohnePost();
  await ruhe(1500);
  await knopf("Lage bearbeiten").click();
  await ruhe(2500);
  const eingaben = page.locator(".lage-panel .passzeile input[type=number]");
  // Wie am Bildschirm: zum Picken und Ziehen heranzoomen (die Zeichnung ist 5-fach ueberhoeht)
  const heran = (punkt, radius) => page.evaluate(([p, r]) => {
    const k = window.viewer.KAMERA.szeneKugel().clone();
    k.center.set(p.x, p.y, p.z);
    k.radius = r;
    return window.viewer.KAMERA.einpassen(k, false);
  }, [punkt, radius]);
  const bildPunkt = (u, v_) => page.evaluate(([a, b]) => window.viewer.editor.bildPunkt(a, b), [u, v_]);
  async function schnittPunkt(k, u, v_, station, hoehe) {
    await heran(await bildPunkt(u, v_), 4);
    await bilder();
    await page.locator(`.lage-panel bim-button[label="Punkt ${k + 1}"]`).click();
    const p = await schirm(u, v_);
    await page.mouse.click(p.x, p.y);
    await ruhe(400);
    await eingaben.nth(2 * k).fill(String(station));
    await eingaben.nth(2 * k + 1).fill(String(hoehe));
  }
  const b1 = wS.bohrungen["B 1"];
  const b6 = wS.bohrungen["B 6"];
  await schnittPunkt(0, ...b1.px_top, b1.station, b1.gok);
  await schnittPunkt(1, ...b6.px_unten, b6.station, Math.round((b6.gok - b6.ende) * 100) / 100);
  await page.locator('.lage-panel bim-button[label="Kalibrierung übernehmen"]').click();
  await ruhe(1500);
  s = await st();
  pruefe("Schnitt kalibriert (Laenge 1:500, Hoehe 1:100)", /Länge 1:(49\d|50\d)\b/.test(s.lage.text) && /Höhe 1:(99|10\d)\b/.test(s.lage.text), s.lage.text);
  const nadelPunkt = (c) => page.evaluate((c_) => {
    const e = window.viewer.editor;
    return e.szenenPunkt([...e.nadeln.values()].find((n) => n.daten.code === c_).daten.id);
  }, c);
  for (const code of ["B 2", "B 3"]) {
    const a = await nadelPunkt(code);
    const b = await bildPunkt(...wS.bohrungen[code].px_top);
    await heran({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: 0 }, Math.abs(a.x - b.x) / 2 + 6);
    await bilder();
    const von = await page.evaluate((c) => {
      const e = window.viewer.editor;
      return e.markenPunkt([...e.nadeln.values()].find((n) => n.daten.code === c).daten.id);
    }, code);
    const ziel = await schirm(...wS.bohrungen[code].px_top);
    await ziehen(von, { x: ziel.x, y: von.y });
    const e = (await ereignisse()).filter((x) => x.typ === "station").at(-1);
    const abw = e ? Math.abs(e.station - wS.bohrungen[code].station) : Infinity;
    pruefe(`${code} entlang der Reihe auf Station ${wS.bohrungen[code].station} m`, abw < 0.3, e ? `Station ${e.station} (Abw. ${abw.toFixed(2)} m)` : "kein Ereignis");
  }
  // Umschalt+Ziehen: Ansatzhoehe von B 4 auf die gezeichnete GOK + 1 m
  const b4 = wS.bohrungen["B 4"];
  await heran(await nadelPunkt("B 4"), 6);
  await bilder();
  const von4 = await page.evaluate(() => {
    const e = window.viewer.editor;
    return e.markenPunkt([...e.nadeln.values()].find((n) => n.daten.code === "B 4").daten.id);
  });
  const hoch = await schirm(b4.px_top[0], b4.px_top[1] - (1.0 / wS.massstab_hoehe) * 1000 / 0.0846667);
  await ziehen(von4, { x: von4.x, y: hoch.y }, true);
  const g = (await ereignisse()).filter((x) => x.typ === "gok").at(-1);
  pruefe("Umschalt+Ziehen setzt die GOK", g && Math.abs(g.gok - (b4.gok + 1)) < 0.3, g ? `GOK ${g.gok} (soll ${(b4.gok + 1).toFixed(2)})` : "kein Ereignis");
  await page.evaluate(() => window.viewer.KAMERA.ansicht("sued", false));
  await bilder();
  await page.screenshot({ path: `${aus}/C1_laengsschnitt.png` });
} finally {
  const fehlgeschlagen = pruefungen.filter((p) => !p.ok);
  console.log(`\n${pruefungen.length - fehlgeschlagen.length}/${pruefungen.length} Pruefungen bestanden`);
  console.log("Seitenfehler:", fehler.length ? fehler.slice(0, 10) : "keine");
  await browser.close();
  server.httpServer.close();
  if (fehler.length || fehlgeschlagen.length) process.exitCode = 1;
}
