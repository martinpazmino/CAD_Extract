// End-to-End-Pruefung der Schritt-App (Chromium/Playwright, ohne Bildschirm) gegen den laufenden Server.
//   A  Talheim: Warnung = unklassifizierte Schicht, blaettern (Pfeil, N), G = alle Schichten geprueft und weiter,
//      Schicht klassifizieren, Bohrung entfernen und wiederherstellen, alle Bohrungen geprueft
//   B  Berlin: Vorschlag nach Norm fuer eine unklassifizierte Schicht uebernehmen
//   C  Lageplan (scripts/testplan.py): Strecke messen -> Massstab, Bezugspunkt, Drehung, sperren, Bohrungen ohne Lage
//      aus der Liste auf ihren Kreis ziehen; C2 dasselbe ohne eine einzige Koordinate und mit echten Hoehen (Vorschau im
//      Bild, EPSG-Liste, offene Punktwahl, Nullpunkt, kein Flackern); C3 Punkte setzen, zuordnen, loeschen, Direktaufruf
//   D  Laengsschnitt: 1:500/1:100, Bezugspunkt (Station/Hoehe), sperren, Bohrungen auf ihre Saeule ziehen (GOK aus dem
//      PDF bleibt), Einheit umbenennen, Modell im Viewer, einchecken, IFC mit Bodenansprache
//   E  PDF-Beispiel: Extraktion mit Fortschritt, Quelle der Schicht im PDF
//
//   python -m server --port 8511 --kein-browser --arbeit <leerer-ordner>     (in einem zweiten Terminal)
//   python scripts/testplan.py <plaene>
//   node scripts/check_app.mjs http://localhost:8511 <plaene> <ausgabe>
import { createRequire } from "node:module";
import { mkdirSync, readFileSync } from "node:fs";

const require = createRequire(import.meta.url);
const { chromium } = require(process.env.PLAYWRIGHT_PFAD ?? "playwright");
const [url, plaene, aus = "check_app"] = process.argv.slice(2);
mkdirSync(aus, { recursive: true });
const wPlan = JSON.parse(readFileSync(`${plaene}/wahrheit_plan.json`, "utf8")).bohrungen;
const wSchnitt = JSON.parse(readFileSync(`${plaene}/wahrheit_schnitt.json`, "utf8")).bohrungen;

const browser = await chromium.launch({ args: ["--use-angle=swiftshader", "--enable-unsafe-swiftshader"] });
const page = await browser.newPage({ viewport: { width: 1600, height: 950 } });
const fehler = [];
const pruefungen = [];
page.on("pageerror", (e) => fehler.push(String(e.stack || e)));
page.on("console", (m) => m.type() === "error" && !/favicon/.test(m.text()) && fehler.push(m.text()));
page.on("dialog", (d) => d.accept());

function pruefe(name, ok, info = "") {
  pruefungen.push({ name, ok: !!ok });
  console.log(`${ok ? "OK  " : "FEHL"} ${name}${info ? ` – ${info}` : ""}`);
}
const stand = () => page.evaluate(() => {
  const a = window.app;
  return { schritt: a.schritt, bid: a.bid, z: a.z, rechnet: a.rechnet,
           modell: a.modell && { fehler: a.modell.fehler, ifc: a.modell.ifc, einheiten: a.modell.bericht?.einheiten.map((e) => e.name) } };
});
const ruhe = (ms = 800) => page.waitForTimeout(ms);
const bohrung = async (code) => (await stand()).z.bohrungen.find((b) => b.code === code);
const warte = (f, arg, timeout = 120000) => page.waitForFunction(f, arg, { timeout, polling: 250 });
const schirm = (px) => page.evaluate(([u, v]) => window.viewer.editor.bildZuSchirm(u, v), px);
const markenPunkt = (code) => page.evaluate((c) => {
  const e = window.viewer.editor;
  const s = [...e.nadeln.values()].find((n) => n.daten.code === c);
  return s ? e.markenPunkt(s.daten.id) : null;
}, code);

async function startseite() {
  await page.goto(url);
  await page.waitForSelector(".ablage", { timeout: 60000 });
}

/** Gespeicherten Stand verwerfen (Menue): jede Pruefung beginnt ohne Korrekturen, auch beim zweiten Lauf. */
async function zuruecksetzen() {
  await page.locator(".menue summary").click();
  await page.getByRole("button", { name: /Alle Korrekturen verwerfen/ }).click();
  await warte(() => window.app?.z?.version === 0 && window.app.schritt === "bohrungen" && document.querySelector(".schichten"));
  await ruhe();
}

async function beispiel(titel) {
  await startseite();
  await page.getByRole("button", { name: titel }).click();
  await warte(() => window.app?.schritt && window.app.schritt !== "gutachten" && window.app.z);
  await zuruecksetzen();
}

async function hochladen(datei) {
  await startseite();
  await page.locator('.ablage input[type="file"]').setInputFiles(datei);
  await page.getByRole("button", { name: /Auswerten/ }).click();
  await warte(() => window.app?.schritt && window.app.schritt !== "gutachten" && window.app.z);
  await zuruecksetzen();
}

async function ziehen(von, nach) {
  await page.mouse.move(von.x, von.y);
  await page.mouse.down();
  await page.mouse.move((von.x + nach.x) / 2, (von.y + nach.y) / 2, { steps: 6 });
  await page.mouse.move(nach.x, nach.y, { steps: 6 });
  await page.mouse.up();
}

async function punktKlick(knopf, px) {
  await page.getByRole("button", { name: knopf }).click();
  await ruhe(300);
  const p = await schirm(px);
  await page.mouse.click(p.x, p.y);
  await ruhe(400);
}

async function zuLage() {
  await page.getByRole("button", { name: /Weiter: Lage/ }).click();
  await warte(() => window.baugrund?.lage?.nadeln > 0 && window.viewer?.editor?.aktiv);
  await ruhe(1500);
}

async function unterlageHochladen(datei, art) {
  if (art === "schnitt") await page.getByLabel("Längsschnitt", { exact: true }).check();
  await page.locator('.datei-knopf input[type="file"]').setInputFiles(datei);
  await warte(() => window.baugrund?.lage?.unterlage?.sichtbar);
  await ruhe(2000);
}

try {
  // ---------------------------------------------------------------- A: Talheim
  await beispiel(/Talheim/);
  let z = (await stand()).z;
  pruefe("Warnung = unklassifizierte Schichten", z.pruefstand.unklassifiziert_offen === 2 &&
    (await page.locator(".pruefleiste .plakette.warn").textContent()).includes("2"), JSON.stringify(z.pruefstand));
  const erste = (await stand()).bid;
  await page.keyboard.press("ArrowDown");
  await ruhe(500);
  const zweite = (await stand()).bid;
  pruefe("Pfeil ↓ blättert zur nächsten Bohrung", zweite && zweite !== erste);
  await page.getByRole("button", { name: /Nächste offene/ }).click();
  await ruhe(500);
  const s1 = await stand();
  pruefe("„Nächste offene“ wählt eine Bohrung mit offenen Schichten",
    s1.z.bohrungen.find((b) => b.id === s1.bid)?.schichten_geprueft < s1.z.bohrungen.find((b) => b.id === s1.bid)?.schichten_n);
  const vorG = s1.bid;
  await page.locator("body").click({ position: { x: 5, y: 300 } });
  await page.keyboard.press("g");
  await warte((id) => window.app.bid !== id, vorG, 30000).catch(() => {});
  await ruhe(600);
  const nachG = await stand();
  const b = nachG.z.bohrungen.find((x) => x.id === vorG);
  pruefe("G: alle Schichten geprüft und weiter", b.schichten_geprueft === b.schichten_n && nachG.bid !== vorG,
    `${b.code} ${b.schichten_geprueft}/${b.schichten_n} → ${nachG.z.bohrungen.find((x) => x.id === nachG.bid)?.code}`);
  // unklassifizierte Schicht von BK1 klassifizieren
  await page.locator(".bliste li", { hasText: "BK1" }).first().click();
  await warte(() => document.querySelector(".schichten tr.warn"));
  await page.locator(".schichten tr.warn select").first().selectOption("Schluff");
  await warte(() => window.app.z.pruefstand.unklassifiziert_offen === 1, null, 30000).catch(() => {});
  z = (await stand()).z;
  pruefe("Bodenart gewählt: Warnung weg, Schicht korrigiert", z.pruefstand.unklassifiziert_offen === 1 && z.pruefstand.korrigiert === 1,
    JSON.stringify(z.pruefstand));
  await page.screenshot({ path: `${aus}/A1_bohrungen.png` });
  // entfernen und wiederherstellen
  await page.locator(".bliste li", { hasText: "GWM1" }).first().hover();
  await page.getByRole("button", { name: "GWM1 entfernen" }).click();
  await warte(() => window.app.z.bohrungen.find((b) => b.code === "GWM1")?.entfernt, null, 30000);
  await page.locator("details.entfernt summary").click();
  await page.locator("details.entfernt li", { hasText: "GWM1" }).getByRole("button", { name: "wiederherstellen" }).click();
  await warte(() => !window.app.z.bohrungen.find((b) => b.code === "GWM1")?.entfernt, null, 30000);
  pruefe("Bohrung entfernen und wiederherstellen", !(await bohrung("GWM1")).entfernt);
  await page.getByRole("button", { name: /Alle Bohrungen geprüft/ }).click();
  await warte(() => window.app.z.pruefstand.bohrungen[0] === window.app.z.pruefstand.bohrungen[1], null, 30000);
  z = (await stand()).z;
  pruefe("Alle Bohrungen geprüft (global)", z.pruefstand.schichten[0] === z.pruefstand.schichten[1] && z.pruefstand.unklassifiziert_offen === 0,
    `${z.pruefstand.bohrungen} · ${z.pruefstand.schichten}`);

  // ---------------------------------------------------------------- B: Berlin, Vorschlag nach Norm
  await beispiel(/Berlin/);
  await page.locator(".bliste li", { hasText: "S2a" }).first().click();
  await warte(() => [...document.querySelectorAll(".vorschlag")].length > 0, null, 30000);
  await page.locator(".vorschlag").first().click();
  await warte(() => window.app.z.bohrungen.find((b) => b.code === "S2a")?.korrigiert > 0, null, 30000);
  const s2a = await bohrung("S2a");
  pruefe("Vorschlag nach Norm übernommen (Grobaand → Sand)", s2a.korrigiert === 1, `${s2a.unklassifiziert} weiter unklassifiziert`);
  await page.screenshot({ path: `${aus}/B1_vorschlag.png` });

  // ---------------------------------------------------------------- C: Lageplan kalibrieren und Bohrungen setzen
  await hochladen(`${plaene}/plan_extraktion.json`);
  await zuLage();
  await unterlageHochladen(`${plaene}/plan.pdf`, "plan");
  await punktKlick("Punkt 1", wPlan["B 1"].px);
  await punktKlick("Punkt 2", wPlan["B 4"].px);
  const meter = Math.hypot(wPlan["B 4"].x - wPlan["B 1"].x, wPlan["B 4"].y - wPlan["B 1"].y);
  await page.locator("label.inline", { hasText: "wahre Länge" }).locator("input").fill(meter.toFixed(3));
  await punktKlick("Punkt im Plan wählen", wPlan["B 1"].px);
  await page.locator("label", { hasText: "Rechtswert" }).locator("input").fill(String(wPlan["B 1"].x));
  await page.locator("label", { hasText: "Hochwert" }).locator("input").fill(String(wPlan["B 1"].y));
  await page.locator("fieldset", { hasText: "Drehung" }).locator('input[type="number"]').first().fill("10");
  await ruhe(500);
  await page.getByRole("button", { name: /Übernehmen und sperren/ }).click();
  await warte(() => window.baugrund?.lage?.unterlage?.gesperrt, null, 30000);
  await ruhe(1500);
  const lageText = (await page.evaluate(() => window.baugrund.lage)).text;
  pruefe("Plan kalibriert (Strecke, Bezugspunkt, Drehung) und gesperrt", /1:500 · Drehung 10,0°/.test(lageText), lageText);
  for (const code of ["B 6", "BS 9"]) {
    const park = page.locator(".park", { hasText: new RegExp(`^${code}$`) });
    const kiste = await park.boundingBox();
    const ziel = await schirm(wPlan[code].px);
    await ziehen({ x: kiste.x + kiste.width / 2, y: kiste.y + kiste.height / 2 }, ziel);
    await warte((c) => window.app.z.bohrungen.find((b) => b.code === c)?.x !== null, code, 30000);
    await ruhe(800);
  }
  const fehlerLage = [];
  for (const code of ["B 6", "BS 9"]) {
    const x = await bohrung(code);
    fehlerLage.push(Math.hypot(x.x - wPlan[code].x, x.y - wPlan[code].y));
  }
  pruefe("Bohrungen ohne Lage auf den Plan gezogen (Fehler ≤ 0,5 m)", Math.max(...fehlerLage) <= 0.5,
    fehlerLage.map((f) => f.toFixed(2)).join(" / ") + " m");
  await page.screenshot({ path: `${aus}/C1_plan.png` });

  // ---------------------------------------------------------------- C2: Lageplan, keine Bohrung mit Koordinaten
  // Fall aus der Praxis (RKS ohne Lage): der Plan springt beim Kalibrieren Millionen Meter - die Vorschau bleibt im
  // Bild; EPSG aus der Liste mit Hinweis; eine offene Punktwahl blockiert das Ziehen nicht; Nullpunkt vom
  // Bezugspunkt; im Lage-Modus kein Wechsel zwischen Bild mit und ohne Postproduktion (Flackern).
  await hochladen(`${plaene}/plan_ohne_lage_extraktion.json`);
  await zuLage();
  await unterlageHochladen(`${plaene}/plan.pdf`, "plan");
  await punktKlick("Punkt 1", wPlan["B 1"].px);
  await punktKlick("Punkt 2", wPlan["B 4"].px);
  await page.locator("label.inline", { hasText: "wahre Länge" }).locator("input").fill(meter.toFixed(3));
  await punktKlick("Punkt im Plan wählen", wPlan["B 1"].px);
  const rechtswert = page.locator("label", { hasText: "Rechtswert" }).locator("input");
  const epsgHinweis = page.locator("fieldset", { hasText: "Bezugspunkt" }).locator("p.klein");
  await rechtswert.fill("74848.9");
  await page.locator("label", { hasText: "Hochwert" }).locator("input").fill(String(wPlan["B 1"].y));
  await page.locator("select.epsg").selectOption("25832");
  await ruhe(300);
  const falsch = await epsgHinweis.textContent();
  await rechtswert.fill(String(wPlan["B 1"].x));
  await page.locator("fieldset", { hasText: "Drehung" }).locator('input[type="number"]').first().fill("10");
  await ruhe(800);
  const richtig = await epsgHinweis.textContent();
  pruefe("EPSG aus der Liste, Hinweis wenn Rechts-/Hochwert nicht passen", /keinem System/.test(falsch) && /passt zu EPSG 25832/.test(richtig),
    `${falsch.trim()} | ${richtig.trim()}`);
  const imBild = () => page.evaluate(() => {
    const r = window.viewer.world.renderer.three.domElement.getBoundingClientRect();
    const p = window.viewer.editor.bildZuSchirm(2000, 1500);                 // Planmitte
    return !!p && p.x > r.left && p.x < r.right && p.y > r.top && p.y < r.bottom;
  });
  pruefe("Vorschau: Plan bleibt nach dem Eintragen der Koordinate im Bild", await imBild());
  await page.locator("button.punkt", { hasText: /Punkt im Plan wählen/ }).click();     // Punktwahl offen lassen
  await page.getByRole("button", { name: /Übernehmen und sperren/ }).click();
  await warte(() => window.baugrund?.lage?.unterlage?.gesperrt, null, 30000);
  await ruhe(1500);
  const gesperrt = await page.evaluate(() => ({ waehlt: document.body.classList.contains("waehlt"),
                                                ursprung: [window.viewer.rahmen.e0, window.viewer.rahmen.n0] }));
  pruefe("Sperren: Punktwahl beendet, Nullpunkt vom Bezugspunkt",
    !gesperrt.waehlt && Math.hypot(gesperrt.ursprung[0] - wPlan["B 1"].x, gesperrt.ursprung[1] - wPlan["B 1"].y) < 100,
    JSON.stringify(gesperrt));
  await page.evaluate(() => {
    const r = window.viewer.world.renderer;
    window.__bilder = { einfach: 0, post: 0 };
    const upd = r.postproduction.update.bind(r.postproduction);
    r.postproduction.update = (...a) => { window.__bilder.post += 1; return upd(...a); };
    r.onAfterUpdate.add(() => { window.__bilder.einfach += 1; });
  });
  // Plan verschieben (Kamera) und Maus darueber bewegen: alle Bilder ohne Postproduktion
  const flaeche = await page.evaluate(() => { const r = window.viewer.world.renderer.three.domElement.getBoundingClientRect(); return { x: r.left + r.width * 0.75, y: r.top + r.height * 0.85 }; });
  await page.mouse.move(flaeche.x, flaeche.y);
  await page.mouse.down();
  for (let i = 1; i <= 10; i++) {
    await page.mouse.move(flaeche.x - i * 6, flaeche.y - i * 2);
    await ruhe(40);
  }
  await page.mouse.up();
  for (let i = 0; i < 10; i++) {
    await page.mouse.move(flaeche.x - 80 + i * 9, flaeche.y - 40);
    await ruhe(40);
  }
  await ruhe(800);
  const bilder = await page.evaluate(() => window.__bilder);
  pruefe("Lage-Modus: Bilder ohne Postproduktion (kein Flackern)", bilder.einfach > 0 && bilder.post === 0, JSON.stringify(bilder));
  const fehlerOhne = [];
  let sichtbar = true;
  for (const code of ["B 1", "B 7", "BS 10"]) {
    const park = page.locator(".park", { hasText: new RegExp(`^${code}$`) });
    const kiste = await park.boundingBox();
    const ziel = await schirm(wPlan[code].px);
    await ziehen({ x: kiste.x + kiste.width / 2, y: kiste.y + kiste.height / 2 }, ziel);
    await warte((c) => window.app.z.bohrungen.find((b) => b.code === c)?.x !== null, code, 30000);
    await ruhe(1500);
    const x = await bohrung(code);
    fehlerOhne.push(Math.hypot(x.x - wPlan[code].x, x.y - wPlan[code].y));
    sichtbar &&= (await imBild()) && !!(await markenPunkt(code));
  }
  pruefe("ohne Koordinaten: aus der Liste auf den Plan gezogen, Plan bleibt im Bild (Fehler ≤ 0,5 m)",
    sichtbar && Math.max(...fehlerOhne) <= 0.5, fehlerOhne.map((f) => f.toFixed(2)).join(" / ") + " m");
  await page.screenshot({ path: `${aus}/C2_ohne_lage.png` });

  // ---------------------------------------------------------------- C3: Punkte setzen, zuordnen, loeschen
  const klickAuf = async (code) => {
    const p = await schirm(wPlan[code].px);
    await page.mouse.click(p.x, p.y);
    await ruhe(1500);
  };
  const abwPlan = async (code) => { const b = await bohrung(code); return b.x === null ? Infinity : Math.hypot(b.x - wPlan[code].x, b.y - wPlan[code].y); };
  const freie = async () => (await stand()).z.punkte.length;
  await page.getByRole("button", { name: /Punkte im Plan setzen/ }).click();
  await ruhe(400);
  const p1Code = await page.locator("select.naechste option:checked").textContent();
  await klickAuf(p1Code.trim());
  const p2Code = await page.locator("select.naechste option:checked").textContent();
  await klickAuf(p2Code.trim());
  const abwKlick = [await abwPlan(p1Code.trim()), await abwPlan(p2Code.trim())];
  pruefe("Punkte setzen: je Klick eine Bohrung, danach die nächste ohne Lage (≤ 0,5 m)",
    Math.max(...abwKlick) <= 0.5 && p1Code.trim() !== p2Code.trim(), `${p1Code.trim()} ${abwKlick[0].toFixed(2)} m, ${p2Code.trim()} ${abwKlick[1].toFixed(2)} m`);
  await page.locator("select.naechste").selectOption("");                    // freier Punkt
  await klickAuf("B 4");
  const vorZuordnen = await freie();
  const sichtbarFrei = await page.locator(".punktmarke:not([hidden])").count();
  await page.locator("table.punkte tr.frei select").first().selectOption((await bohrung("B 4")).id);
  await warte((c) => window.app.z.bohrungen.find((b) => b.code === c)?.x !== null, "B 4", 30000);
  await ruhe(800);
  pruefe("Freier Punkt ◆ gesetzt und einer Bohrung zugeordnet", vorZuordnen === 1 && sichtbarFrei === 1 && (await freie()) === 0 &&
    (await abwPlan("B 4")) <= 0.5, `B 4 ${(await abwPlan("B 4")).toFixed(2)} m`);
  await page.locator(".park", { hasText: /^B 5$/ }).click();                // Chip = naechste Bohrung
  await ruhe(300);
  await klickAuf("B 5");
  await page.locator("table.punkte tr").filter({ has: page.locator("button.link", { hasText: new RegExp(`^● ${p1Code.trim()}$`) }) })
    .locator("button.symbol").click();
  await warte((c) => window.app.z.bohrungen.find((b) => b.code === c)?.x === null, p1Code.trim(), 30000);
  await page.locator("select.naechste").selectOption("");
  await klickAuf("B 8");
  const mb = await page.locator(".punktmarke").first().boundingBox();
  await page.mouse.click(mb.x + 6, mb.y + mb.height / 2);
  await ruhe(300);
  await page.keyboard.press("Delete");
  await ruhe(1500);
  const vorSchieben = await freie();
  const fl = await page.evaluate(() => { const r = window.viewer.world.renderer.three.domElement.getBoundingClientRect(); return { x: r.left + r.width * 0.7, y: r.top + r.height * 0.8 }; });
  await page.mouse.move(fl.x, fl.y);
  await page.mouse.down();
  await page.mouse.move(fl.x - 80, fl.y - 30, { steps: 8 });
  await page.mouse.up();
  await ruhe(1200);
  pruefe("Chip als nächste, ✕ in der Liste und Entf im Viewer löschen; Verschieben setzt keinen Punkt",
    (await abwPlan("B 5")) <= 0.5 && (await bohrung(p1Code.trim())).x === null && vorSchieben === 0 && (await freie()) === 0);
  await page.screenshot({ path: `${aus}/C3_punkte.png` });
  await page.keyboard.press("Escape");
  // direkt geoeffnet (#/<projekt>/lage): der orthografische Rahmen stand verkehrt (Bild um 180 Grad gedreht)
  const sigOhne = (await stand()).z.signatur;
  await page.goto("about:blank");                                            // neu laden, nicht nur die Adresse aendern
  await page.goto(`${url}/#/${sigOhne}/lage`);
  await warte(() => window.baugrund?.lage?.unterlage?.sichtbar && window.viewer?.editor?.aktiv);
  await ruhe(2500);
  const direkt = await page.evaluate(() => {
    const o = window.viewer.world.camera.threeOrtho;
    const r = window.viewer.world.renderer.three.domElement.getBoundingClientRect();
    const p = window.viewer.editor.bildZuSchirm(2000, 1500);
    return { rechts: o.right > o.left, oben: o.top > o.bottom, imBild: !!p && p.x > r.left && p.x < r.right && p.y > r.top && p.y < r.bottom };
  });
  pruefe("Direkt geöffnet: orthografischer Rahmen richtig herum, Plan im Bild", direkt.rechts && direkt.oben && direkt.imBild,
    JSON.stringify(direkt));

  // ---------------------------------------------------------------- D: Laengsschnitt
  await hochladen(`${plaene}/schnitt_extraktion.json`);
  pruefe("ohne Koordinaten: Lage = Reihe", (await stand()).z.lage_modus === "reihe");
  await zuLage();
  await unterlageHochladen(`${plaene}/schnitt.pdf`, "schnitt");
  await page.getByLabel("1:n eingeben").check();
  await page.locator("label.inline", { hasText: "Maßstab 1:" }).locator("input").fill("500");
  await page.locator("fieldset", { hasText: "Höhenmaßstab" }).getByLabel("1:n").check();
  await page.locator("label.inline", { hasText: "Höhe 1:" }).locator("input").fill("100");
  await punktKlick("Punkt im Plan wählen", wSchnitt["B 1"].px_top);
  await page.locator("label", { hasText: "Station [m]" }).locator("input").fill("0");
  await page.locator("label", { hasText: "Höhe [m NHN]" }).locator("input").fill(String(wSchnitt["B 1"].gok));
  await page.getByRole("button", { name: /Übernehmen und sperren/ }).click();
  await warte(() => window.baugrund?.lage?.unterlage?.gesperrt, null, 30000);
  await ruhe(1500);
  const schnittText = (await page.evaluate(() => window.baugrund.lage)).text;
  pruefe("Längsschnitt kalibriert (Länge 1:500, Höhe 1:100)", /Länge 1:500 · Höhe 1:100/.test(schnittText), schnittText);
  for (const code of ["B 2", "B 3", "B 4", "B 5", "B 6"]) {
    const von = await markenPunkt(code);
    const ziel = await schirm(wSchnitt[code].px_top);
    if (!von) continue;
    await ziehen(von, { x: ziel.x, y: ziel.y + 25 });         // auch nach unten: die GOK aus dem PDF darf sich nicht aendern
    await warte(([c, s]) => Math.abs((window.app.z.reihe.find((r) => r.code === c)?.station ?? -1) - s) < 1, [code, wSchnitt[code].station], 30000).catch(() => {});
    await ruhe(600);
  }
  z = (await stand()).z;
  const stationFehler = ["B 2", "B 3", "B 4", "B 5", "B 6"].map((c) => Math.abs(z.reihe.find((r) => r.code === c).station - wSchnitt[c].station));
  pruefe("Stationen aus dem Schnitt gezogen (Fehler ≤ 0,2 m)", Math.max(...stationFehler) <= 0.2, stationFehler.map((f) => f.toFixed(2)).join(" / "));
  const gokGleich = ["B 2", "B 3"].every((c) => Math.abs(z.bohrungen.find((b) => b.code === c).gok - wSchnitt[c].gok) < 1e-6);
  pruefe("GOK aus dem PDF bleibt beim Ziehen (nur Station)", gokGleich);
  await page.screenshot({ path: `${aus}/D1_schnitt.png` });
  await page.getByRole("button", { name: /Weiter: Einheiten/ }).click();
  await warte(() => document.querySelector("table.einheiten"), null, 180000);
  // Eingabefeld der Einheit "Kies" (Werte stehen nicht im Text der Zeile: Index ueber value suchen)
  const zeile = await page.evaluate(() => [...document.querySelectorAll("table.vorgabe tbody tr")]
    .findIndex((tr) => tr.querySelector("input")?.value === "Kies"));
  await page.locator("table.vorgabe tbody tr").nth(Math.max(0, zeile)).locator("input").first().fill("Kieslinse");
  await page.getByRole("button", { name: "Mit diesen Einheiten rechnen" }).click();
  await warte(() => window.app.modell?.bericht?.einheiten.some((e) => e.name === "Kieslinse") && !window.app.rechnet, null, 180000);
  pruefe("Einheit umbenannt (Vorgabe) und neu gerechnet", (await stand()).modell.einheiten.includes("Kieslinse"));
  await page.screenshot({ path: `${aus}/D2_einheiten.png` });
  await page.getByRole("button", { name: /Weiter: Modell/ }).click();
  await warte(() => window.baugrund?.geladen && !window.app.rechnet, null, 240000);
  await ruhe(3000);
  const st = await page.evaluate(() => ({ einheiten: window.baugrund.einheiten, marken: window.baugrund.marken }));
  pruefe("Modell im Viewer", st.einheiten.includes("Kieslinse"), JSON.stringify(st));
  await page.locator(".app-panel input.breit").fill("E2E-Prüfung");
  await page.getByRole("button", { name: /Stand einchecken/ }).click();
  await warte(() => window.app.z.eincheckungen.length === 1, null, 30000);
  pruefe("Stand eingecheckt", (await stand()).z.eingecheckt?.startsWith("v1"));
  const sig = (await stand()).z.signatur;
  const ifc = await page.evaluate(async (s) => (await fetch(`/api/projekt/${s}/export/ifc`)).text(), sig);
  pruefe("IFC: Bodenansprache je Schicht, Beschreibungen je Einheit, Prüfstand",
    ifc.includes("CPset_Bodenansprache") && ifc.includes("'Beschreibungen'") && ifc.includes("Kieslinse") && ifc.includes("IFCLABEL('v1 "), `${(ifc.length / 1e6).toFixed(1)} MB`);
  await page.screenshot({ path: `${aus}/D3_modell.png` });

  // ---------------------------------------------------------------- E: PDF mit Extraktion
  await startseite();
  await page.getByRole("button", { name: /Bohrprofil-PDF/ }).click();
  const fortschritt = await warte(() => document.querySelector(".fortschritt-karte"), null, 30000).then(() => true).catch(() => false);
  await warte(() => window.app?.schritt === "bohrungen" && document.querySelector(".schichten"), null, 300000);
  await page.locator(".schichten tbody tr").first().click();
  const bild = await warte(() => {
    const i = document.querySelector(".pdf-seite img");
    return i && i.complete && i.naturalWidth > 0 && document.querySelector(".bbox.schicht-bbox");
  }, null, 60000).then(() => true).catch(() => false);
  pruefe("PDF ausgewertet (Fortschritt) und Schicht im PDF markiert", bild, `Fortschritt sichtbar: ${fortschritt}`);
  await page.screenshot({ path: `${aus}/E1_quelle.png` });
} finally {
  const fehlgeschlagen = pruefungen.filter((p) => !p.ok);
  console.log(`\n${pruefungen.length - fehlgeschlagen.length}/${pruefungen.length} Pruefungen bestanden`);
  console.log("Seitenfehler:", fehler.length ? fehler : "keine");
  await browser.close();
  if (fehler.length || fehlgeschlagen.length) process.exitCode = 1;
}
