// Headless-Pruefung des Viewers (Chromium/Playwright) in drei Teilen, mit Bildern:
//   A  grosses Modell (Trasse > 5 km): Laden, Kamera-Grenzen, Ansichten, Koordinaten, Auswahl, Transparenz, Schnitt
//   B  Lageplan (scripts/testplan.py): ohne Postproduktion (kein Flackern); ungesperrt nicht ziehbar; Strecke (zwei
//      Bildpunkte) -> Massstab, Bezug, Drehung, gesperrt; Bohrungen ohne Lage auf den Plan ziehen
//   C  Laengsschnitt: 1:500/1:100 mit Bezugspunkt; entlang der Reihe ziehen, GOK aus dem PDF bleibt, ohne GOK ziehbar
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
const ohnePost = () => page.evaluate(() => window.viewer.schatten(false));
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
  await page.goto(`http://localhost:4174/viewer.html?ifc=modelle/${basename(ifcQuelle)}&ueberhoehung=5`);
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

  // ---------------------------------------------------------------- B: Lageplan (Kalibrierung wie in der App: Strecke, Bezug, Drehung)
  const wPlan = JSON.parse(readFileSync(join(planOrdner, "wahrheit_plan.json"), "utf8"));
  const argsPlan = JSON.parse(readFileSync(join(planOrdner, "args_plan.json"), "utf8"));
  await page.goto("http://localhost:4174/viewer.html?bohrungen=modelle/args_plan.json");
  await page.waitForFunction(() => (window.baugrund?.renders ?? 0) >= 1, null, { timeout: 60000 });
  await ohnePost();
  await ruhe(2000);
  s = await st();
  pruefe("Lageplan: Bohrungen und Unterlage", s.lage.nadeln === 12 && s.lage.ohneLage === 2 && s.lage.unterlage?.art === "plan",
         JSON.stringify(s.lage));
  await knopf("Lage bearbeiten").click();
  await ruhe(2500);
  const ortho = await page.evaluate(() => {
    const o = window.viewer.world.camera.threeOrtho;
    return { art: window.viewer.world.camera.projection.current, richtig: o.right > o.left && o.top > o.bottom };
  });
  pruefe("Lage-Modus: Draufsicht orthografisch, Rahmen richtig herum", ortho.art === "Orthographic" && ortho.richtig, JSON.stringify(ortho));
  // Flackern (docs/16 X22): im Lage-Modus nie ein Bild mit Postproduktion, auch wenn "Kanten und Schatten" an ist;
  // die Umgebungsverdeckung rechnet orthografisch (PERSPECTIVE_CAMERA folgt der Kamera)
  const takt = await page.evaluate(async () => {
    const v = window.viewer;
    const r = v.world.renderer;
    const z = { bilder: 0, post: 0 };
    const upd = r.postproduction.update.bind(r.postproduction);
    r.postproduction.update = (...a) => { z.post += 1; return upd(...a); };
    const weg = () => { z.bilder += 1; };
    r.onAfterUpdate.add(weg);
    v.schatten(true);
    const el = r.three.domElement.getBoundingClientRect();
    for (let i = 0; i < 12; i++) {
      r.three.domElement.dispatchEvent(new PointerEvent("pointermove", { clientX: el.left + 300 + i * 7, clientY: el.top + 300, buttons: 1,
                                                                        bubbles: true }));
      await new Promise((f) => setTimeout(f, 60));
    }
    await new Promise((f) => setTimeout(f, 300));
    r.onAfterUpdate.remove(weg);
    r.postproduction.update = upd;
    v.schatten(false);
    return { ...z, perspektive: r.postproduction.aoPass.gtaoMaterial.defines.PERSPECTIVE_CAMERA };
  });
  pruefe("Lage-Modus ohne Postproduktion (kein Flackern), Verdeckung orthografisch", takt.bilder > 0 && takt.post === 0 && takt.perspektive === 0,
         JSON.stringify(takt));
  const schirm = (u, v_) => page.evaluate(([a, b]) => window.viewer.editor.bildZuSchirm(a, b), [u, v_]);
  const marke = (c) => page.evaluate((c_) => {
    const e = window.viewer.editor;
    return e.markenPunkt([...e.nadeln.values()].find((n) => n.daten.code === c_).daten.id);
  }, c);
  // ungesperrt: Bohrungen lassen sich nicht ziehen (erst kalibrieren und sperren)
  const vorher = (await ereignisse()).length;
  const b2a = await marke("B 2");
  await ziehen(b2a, { x: b2a.x + 60, y: b2a.y + 30 });
  pruefe("Ungesperrter Plan: Bohrung bleibt liegen", (await ereignisse()).length === vorher);
  // Bildpunkte waehlen wie in der App: B 1 und B 11 anklicken
  async function waehlen(code) {
    const p = await schirm(...wPlan.bohrungen[code].px);
    const versprechen = page.evaluate(() => window.viewer.editor.bildpunktWaehlen());
    await ruhe(200);
    await page.mouse.click(p.x, p.y);
    return await versprechen;
  }
  const p1 = await waehlen("B 1");
  const p2 = await waehlen("B 11");
  const w1 = wPlan.bohrungen["B 1"];
  const w2 = wPlan.bohrungen["B 11"];
  const kal = { massstab: { u1: p1.u, v1: p1.v, u2: p2.u, v2: p2.v, meter: Math.hypot(w2.x - w1.x, w2.y - w1.y) },
                bezug: { u: p1.u, v: p1.v, x: w1.x, y: w1.y }, drehung: 10, epsg: 25832, gesperrt: true };
  await page.evaluate((a) => window.viewer.setzen(a), { ...argsPlan, unterlage: { ...argsPlan.unterlage, kalibrierung: kal } });
  await ruhe(1500);
  s = await st();
  pruefe("Massstab aus der Strecke, Drehung, gesperrt", /1:(49\d|50\d)\b/.test(s.lage.text) && /Drehung 10,0/.test(s.lage.text) &&
         s.lage.unterlage.gesperrt, s.lage.text);
  const b7 = await marke("B 7");
  const sym7 = await schirm(...wPlan.bohrungen["B 7"].px);
  pruefe("Plan und Bohrungen decken sich (B 7)", Math.hypot(b7.x - sym7.x, b7.y - sym7.y) < 4, `${Math.hypot(b7.x - sym7.x, b7.y - sym7.y).toFixed(1)} px`);
  // Bohrungen ohne Lage: aus einer Liste (wie in der App) auf ihr Symbol ziehen
  for (const code of wPlan.ohne_lage) {
    await page.evaluate((c) => {
      const e = window.viewer.editor;
      const id = [...e.nadeln.values()].find((n) => n.daten.code === c).daten.id;
      const el = document.createElement("div");
      el.className = "park-test";
      el.textContent = c;
      Object.assign(el.style, { position: "fixed", left: "20px", top: "300px", padding: "6px", background: "#333", zIndex: 999 });
      el.addEventListener("pointerdown", (ev) => e.ziehenStart(ev, id, true));
      document.body.append(el);
    }, code);
    const von = await page.locator(".park-test").boundingBox();
    const ziel = await schirm(...wPlan.bohrungen[code].px);
    await ziehen({ x: von.x + von.width / 2, y: von.y + von.height / 2 }, ziel);
    await page.evaluate(() => document.querySelector(".park-test")?.remove());
    const e = (await ereignisse()).filter((x) => x.typ === "lage").at(-1);
    const wahr = wPlan.bohrungen[code];
    const abw = e ? Math.hypot(e.x - wahr.x, e.y - wahr.y) : Infinity;
    pruefe(`${code} auf den Plan gezogen`, abw < 0.5, e ? `R ${e.x} H ${e.y} (Abweichung ${abw.toFixed(2)} m)` : "kein Ereignis");
  }
  await page.screenshot({ path: `${aus}/B1_lageplan.png` });
  const b2 = await marke("B 2");
  await ziehen(b2, { x: b2.x + 60, y: b2.y + 30 });
  const e2 = (await ereignisse()).filter((x) => x.typ === "lage").at(-1);
  pruefe("Gesperrter Plan: Marke B 2 verschoben (nur x/y)", e2 && Math.hypot(e2.x - 565045, e2.y - 5933010) > 1 && !("gok" in e2),
         e2 ? `R ${e2.x} H ${e2.y}` : "");
  await page.screenshot({ path: `${aus}/B2_verschoben.png` });

  // ---------------------------------------------------------------- C: Laengsschnitt (1:500 / 1:100, Bezug B 1)
  const wS = JSON.parse(readFileSync(join(planOrdner, "wahrheit_schnitt.json"), "utf8"));
  const argsS = JSON.parse(readFileSync(join(planOrdner, "args_schnitt.json"), "utf8"));
  await page.goto("http://localhost:4174/viewer.html?bohrungen=modelle/args_schnitt.json");
  await page.waitForFunction(() => (window.baugrund?.renders ?? 0) >= 1, null, { timeout: 60000 });
  await ohnePost();
  await ruhe(1500);
  await knopf("Lage bearbeiten").click();
  await ruhe(2500);
  const b1 = wS.bohrungen["B 1"];
  // B 5 ohne GOK aus dem PDF: nur sie darf in der Hoehe gezogen werden
  const nadeln = argsS.bohrungen.map((n) => ({ ...n, gok_pdf: n.code !== "B 5" }));
  const kalS = { massstab: { n: 500 }, hoehe: { n: 100 }, bezug: { u: b1.px_top[0], v: b1.px_top[1], x: b1.station, y: b1.gok }, gesperrt: true };
  await page.evaluate((a) => window.viewer.setzen(a), { ...argsS, bohrungen: nadeln, unterlage: { ...argsS.unterlage, kalibrierung: kalS } });
  await ruhe(1500);
  s = await st();
  pruefe("Schnitt kalibriert (Länge 1:500, Höhe 1:100)", /Länge 1:500 · Höhe 1:100/.test(s.lage.text), s.lage.text);
  const heran = (punkt, radius) => page.evaluate(([p, r]) => {
    const k = window.viewer.KAMERA.szeneKugel().clone();
    k.center.set(p.x, p.y, p.z);
    k.radius = r;
    return window.viewer.KAMERA.einpassen(k, false);
  }, [punkt, radius]);
  const bildPunkt = (u, v_) => page.evaluate(([a, b]) => window.viewer.editor.bildPunkt(a, b), [u, v_]);
  const nadelPunkt = (c) => page.evaluate((c_) => {
    const e = window.viewer.editor;
    return e.szenenPunkt([...e.nadeln.values()].find((n) => n.daten.code === c_).daten.id);
  }, c);
  for (const code of ["B 2", "B 3", "B 4"]) {
    const a = await nadelPunkt(code);
    const b = await bildPunkt(...wS.bohrungen[code].px_top);
    await heran({ x: (a.x + b.x) / 2, y: (a.y + b.y) / 2, z: 0 }, Math.abs(a.x - b.x) / 2 + 6);
    await bilder();
    const von = await marke(code);
    const ziel = await schirm(...wS.bohrungen[code].px_top);
    const n = (await ereignisse()).length;
    await ziehen(von, { x: ziel.x, y: von.y - 40 });           // auch nach oben: die GOK aus dem PDF bleibt
    const neu = (await ereignisse()).slice(n);
    const e = neu.find((x) => x.typ === "station");
    const abw = e ? Math.abs(e.station - wS.bohrungen[code].station) : Infinity;
    pruefe(`${code}: Station ${wS.bohrungen[code].station} m, GOK aus dem PDF bleibt`, abw < 0.3 && !neu.some((x) => x.typ === "gok"),
           e ? `Station ${e.station} (Abw. ${abw.toFixed(2)} m)` : "kein Ereignis");
  }
  // B 5 hat keine GOK im PDF: Ziehen setzt Station und Hoehe (1 m ueber der gezeichneten GOK)
  const b5 = wS.bohrungen["B 5"];
  await heran(await nadelPunkt("B 5"), 6);
  await bilder();
  const von5 = await marke("B 5");
  const hoch = await schirm(b5.px_top[0], b5.px_top[1] - (1.0 / wS.massstab_hoehe) * 1000 / argsS.unterlage.mm_pro_px);
  await ziehen(von5, hoch);
  const g = (await ereignisse()).filter((x) => x.typ === "gok").at(-1);
  pruefe("Ohne GOK im PDF: Höhe ziehbar", g && Math.abs(g.gok - (b5.gok + 1)) < 0.3, g ? `GOK ${g.gok} (soll ${(b5.gok + 1).toFixed(2)})` : "kein Ereignis");
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
