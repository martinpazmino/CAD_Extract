// Baugrundmodell-Viewer auf That Open Engine 3.6. Bedienung wie im TwinBimM-Viewer (BUI im W&F-Design,
// ViewCube, Postproduktion, Highlighter/Hider, Werkzeugleiste unten, Zahnrad, Koordinatenanzeige),
// Kamera fuer Trassen ueber 5 km (kamera.ts) und Lage-Editor mit PDF-Unterlage (lage.ts).
// BUI.Component.create erkennt zustandsbehaftete Vorlagen an der Stelligkeit: daher (_zustand) => statt () =>.
// Laeuft allein (?ifc=...) oder als Streamlit-Komponente (ui/viewer.py). Beschreibung: docs/20.
import * as THREE from "three";
import * as OBC from "@thatopen/components";
import * as OBF from "@thatopen/components-front";
import * as FRAGS from "@thatopen/fragments";
import * as BUI from "@thatopen/ui";
import * as BUIC from "@thatopen/ui-obc";
import * as WEBIFC from "web-ifc";
import workerUrl from "@thatopen/fragments/worker?url";
import "./icons";
import { eigenschaften, inhalt, type Inhalt, type Psets } from "./baugrund";
import * as KAMERA from "./kamera";
import { esc, LageEditor } from "./lage";
import { tipp } from "./tipp";
import { ausSzene, hoeheAusSzene, koordinatenText, rahmen } from "./rahmen";
import { eingebettet, ereignis, hoeheSetzen, nrMindestens, projektSetzen, protokoll, starten, type Args, type Nadel } from "./streamlit";

BUI.Manager.init();
BUIC.Manager.init();

// Geotechnik-Klassen: der IfcImporter verwirft sie sonst (Architektur 8.2)
const GEOTECHNIK = [WEBIFC.IFCBOREHOLE, WEBIFC.IFCGEOMODEL, WEBIFC.IFCGEOSLICE, WEBIFC.IFCGEOTECHNICALSTRATUM];
const GRUEN = "#a2c513";                              // W&F-Gruen (Auswahl), wie TwinBimM
const vendor = new URL("vendor/", new URL(import.meta.env.BASE_URL, location.href)).href;
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

// Status fuer automatische Pruefungen (scripts/check.mjs, scripts/check_app.mjs)
const status = {
  geladen: false, ladungen: 0, einheiten: [] as string[], bohrsaeulen: 0, marken: 0, fehler: "", auswahl: "",
  streamlit: eingebettet, kamera: {} as Record<string, unknown>, lage: {} as Record<string, unknown>,
  ereignisse: protokoll, renders: 0,
  instanz: Math.random().toString(36).slice(2, 8),     // neu eingehaengter iframe = neue Instanz
  geladeneIfc: [] as string[],
};
(window as unknown as { baugrund: typeof status }).baugrund = status;

// ------------------------------------------------------------------ Welt
const viewport = $<BUI.Viewport>("viewer");
const components = new OBC.Components();
const world = components.get(OBC.Worlds).create<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBF.PostproductionRenderer>();
world.name = "Baugrund";
world.scene = new OBC.SimpleScene(components);
world.scene.setup();
world.scene.three.background = new THREE.Color(0x1a1d23);
world.renderer = new OBF.PostproductionRenderer(components, viewport);
world.camera = new OBC.OrthoPerspectiveCamera(components);
const raster = components.get(OBC.Grids).create(world);
raster.config.color = new THREE.Color(0x494b50);
viewport.addEventListener("resize", () => {
  world.renderer?.resize();
  world.camera.updateAspect();
  neuZeichnen(4);
});
components.init();
KAMERA.einrichten(world, raster);

// Zeichnen nach Bedarf (RendererMode.MANUAL): waehrend der Bewegung ohne Kanten/Schatten (fluessig auch bei
// Trassen), 50 ms nach dem letzten Bild eines mit Postproduktion; in Ruhe nur ein Bild je Sekunde.
world.renderer.mode = OBC.RendererMode.MANUAL;
let bildBudget = 0;
function neuZeichnen(bilder = 3) {
  bildBudget = Math.max(bildBudget, bilder);
  world.renderer!.needsUpdate = true;
}
world.onBeforeUpdate.add(() => {
  const laedt = [...fragments.list.values()].some((m) => m.isBusy);
  if (bildBudget > 0 || laedt) {
    world.renderer!.needsUpdate = true;
    bildBudget = Math.max(0, bildBudget - 1);
  }
});
world.camera.controls.addEventListener("update", () => neuZeichnen(2));
for (const art of ["pointerdown", "pointermove", "pointerup", "wheel", "dblclick", "keydown", "change"]) {
  document.addEventListener(art, () => neuZeichnen(art === "pointermove" ? 1 : 6), { passive: true, capture: true });
}
window.setInterval(() => neuZeichnen(1), 1000);

const { postproduction } = world.renderer;
postproduction.enabled = true;
postproduction.style = OBF.PostproductionAspect.COLOR_SHADOWS;
postproduction.edgesPass.color = new THREE.Color(0x494b50);
postproduction.aoPass.updateGtaoMaterial({ radius: 0.25, distanceExponent: 1, thickness: 1, scale: 1, samples: 4,
                                            distanceFallOff: 1, screenSpaceRadius: true });
postproduction.aoPass.updatePdMaterial({ lumaPhi: 10, depthPhi: 2, normalPhi: 3, radius: 4, radiusExponent: 1, rings: 2,
                                         samples: 16 });

const caster = components.get(OBC.Raycasters).get(world);
const fragments = components.get(OBC.FragmentsManager);
fragments.init(workerUrl);                             // von Vite mitgeliefert, kein unpkg
fragments.core.models.materials.list.onItemSet.add(({ value: material }) => {
  if ("isLodMaterial" in material && material.isLodMaterial) postproduction.basePass.isolatedMaterials.push(material);
  if (durchscheinend) transparent(material, true);
});
world.camera.controls.addEventListener("rest", () => {
  fragments.core.update(true).then(() => neuZeichnen(4));
  kameraMerken();
});
fragments.list.onItemSet.add(({ value: model }) => {
  model.useCamera(world.camera.three);
  model.getClippingPlanesEvent = () => Array.from(world.renderer!.three.clippingPlanes) || [];
  world.scene.three.add(model.object);
  fragments.core.update(true).then(() => neuZeichnen(10));
});

const ifcLoader = components.get(OBC.IfcLoader);
// COORDINATE_TO_ORIGIN aus: das IFC ist schon lokal zum Projektursprung (rahmen.ts), so stimmt es mit
// den Bohrungen und der Unterlage ueberein.
await ifcLoader.setup({ autoSetWasm: false, wasm: { path: vendor, absolute: true }, webIfc: { COORDINATE_TO_ORIGIN: false } });
ifcLoader.onIfcImporterInitialized.add((importer) => {
  for (const c of GEOTECHNIK) importer.classes.elements.add(c);
});

const highlighter = components.get(OBF.Highlighter);
highlighter.setup({
  world,
  selectMaterialDefinition: {
    color: new THREE.Color(GRUEN), renderedFaces: FRAGS.RenderedFaces.ONE, opacity: 1, transparent: false,
    preserveOriginalMaterial: true, _explicitProps: ["color", "opacity", "transparent"],
  } as unknown as FRAGS.MaterialDefinition,
});
const hider = components.get(OBC.Hider);
const clipper = components.get(OBC.Clipper);
clipper.enabled = true;
clipper.material = new THREE.MeshBasicMaterial({ color: GRUEN, transparent: true, opacity: 0.08, side: THREE.DoubleSide,
                                                 depthWrite: false });

// ------------------------------------------------------------------ Zustand
let modell: FRAGS.FragmentsModel | null = null;
let daten: Inhalt | null = null;
let bohrungNachCode = new Map<string, number>();
let modellUrsprung: [number, number] | null = null;
let projekt = "";
let ifcUrl = "";
let durchscheinend = false;
let schnittWerkzeug = false;
let bezugGesetzt = false;
let nadelnVonStreamlit = false;
let kameraVorLage: ReturnType<typeof KAMERA.kameraZustand> | null = null;
let seiteVorLage = false;
let schmal = false;                                    // Werkzeugleiste nur mit Icons (leisteBreite)
const sichtbar = new Map<number, boolean>();
let nurEinheit: number | null = null;

function meldung(text: string, dauer = 4000) {
  const el = $("meldung");
  el.textContent = text;
  el.hidden = false;
  window.clearTimeout(Number(el.dataset.t));
  el.dataset.t = String(window.setTimeout(() => (el.hidden = true), dauer));
}

function ladeanzeige(text: string | null) {
  $("laden").hidden = text === null;
  if (text !== null) $("laden-text").textContent = text;
}

// ------------------------------------------------------------------ Lage-Editor (Bohrungen, Unterlage)
const editor = new LageEditor(world, viewport, {
  auswahl: (id) => void nadelWaehlen(id),
  meldung,
  neuZeichnen: () => neuZeichnen(6),
  modusGeaendert: () => {
    leisteNeu();
    leisteBreite();
  },
});
viewport.append(editor.panel);
Object.defineProperty(status, "lage", { get: () => editor.status(), enumerable: true });
KAMERA.huelleMelden(() => (modell && modell.object.visible ? modell.box : null));

// ------------------------------------------------------------------ Modell laden
async function laden(bytes: Uint8Array, name: string, kameraBehalten: boolean) {
  try {
    ladeanzeige(`${name} wird geladen …`);
    await auswahlAufheben();
    for (const id of [...fragments.list.keys()]) await fragments.core.disposeModel(id);
    clipper.deleteAll();
    modell = await ifcLoader.load(bytes, false, name);
    daten = await inhalt(modell);
    bohrungNachCode = await bohrungsnamen(modell, daten);
    const m = daten.modell;
    const e0 = Number(m.Ursprung_Rechtswert);
    const n0 = Number(m.Ursprung_Hochwert);
    modellUrsprung = Number.isFinite(e0) && Number.isFinite(n0) ? [e0, n0] : null;
    if (!nadelnVonStreamlit && modellUrsprung) [rahmen.e0, rahmen.n0] = modellUrsprung;
    if (!nadelnVonStreamlit && m.Lagebezug !== undefined) rahmen.modus = /Reihe|schematisch/i.test(String(m.Lagebezug)) ? "reihe" : "koordinaten";
    if (!bezugGesetzt) {
      modell.object.updateMatrixWorld(true);
      rahmen.bezug = Math.floor(modell.box.min.y);
      bezugGesetzt = true;
    }
    modellPlatzieren();
    nurEinheit = null;
    sichtbar.clear();
    if (!nadelnVonStreamlit) await nadelnAusIfc();
    await bohrsaeulenSichtbarkeit();
    editor.setSchnittTiefe(Math.max(-modell.box.min.z, modell.box.max.z) + 1);
    modell.object.visible = !editor.aktiv;
    if (durchscheinend) for (const mat of fragments.core.models.materials.list.values()) transparent(mat, true);
    seitenleisteNeu();
    KAMERA.szeneAktualisieren();
    if (!kameraBehalten) await kameraStart();
    await fragments.core.update(true);
    neuZeichnen(10);
    status.geladen = true;
    status.ladungen += 1;
    status.einheiten = daten.einheiten.map((e) => e.name);
    status.bohrsaeulen = daten.bohrsaeulen.length;
    status.marken = editor.nadeln.size;
    $("leer").hidden = true;
    if (!kameraBehalten) meldung(`${name}: ${daten.einheiten.length} Einheiten, ${daten.bohrungen.length} Bohrungen`);
  } catch (err) {
    status.fehler = String((err as Error)?.stack ?? err);
    meldung(`Fehler beim Laden: ${err}`, 10000);
    throw err;
  } finally {
    ladeanzeige(null);
  }
}

async function ladenUrl(url: string, titel: string, kameraBehalten: boolean) {
  ladeanzeige("Modell wird geholt …");
  const antwort = await fetch(url);
  // Fehlt die Datei, liefern manche Server index.html aus: das ist kein IFC
  if (!antwort.ok || (antwort.headers.get("content-type") ?? "").includes("text/html")) {
    ladeanzeige(null);
    status.fehler = `${url}: ${antwort.ok ? "keine IFC-Datei" : `HTTP ${antwort.status}`}`;
    meldung(status.fehler, 10000);
    return;
  }
  await laden(new Uint8Array(await antwort.arrayBuffer()), titel || decodeURIComponent(url.split("/").pop() ?? url),
              kameraBehalten);
}

async function modellEntfernen() {
  await auswahlAufheben();
  for (const id of [...fragments.list.keys()]) await fragments.core.disposeModel(id);
  modell = null;
  daten = null;
  bohrungNachCode.clear();
  status.geladen = false;
  seitenleisteNeu();
  KAMERA.szeneAktualisieren();
}

/** IFC lokal zu seinem Ursprung -> Projektrahmen; Ueberhoehung um die Bezugshoehe. */
function modellPlatzieren() {
  if (!modell) return;
  const [e0, n0] = modellUrsprung ?? [rahmen.e0, rahmen.n0];
  modell.object.position.set(e0 - rahmen.e0, rahmen.bezug * (1 - rahmen.faktor), -(n0 - rahmen.n0));
  modell.object.scale.set(1, rahmen.faktor, 1);
  modell.object.updateMatrixWorld(true);
}

async function bohrungsnamen(m: FRAGS.FragmentsModel, d: Inhalt) {
  const out = new Map<string, number>();
  if (!d.bohrungen.length) return out;
  const namen = await m.getItemsData(d.bohrungen, { attributesDefault: false, attributes: ["Name"] });
  d.bohrungen.forEach((id, i) => out.set(String((namen[i] as Record<string, { value?: unknown }>).Name?.value ?? ""), id));
  return out;
}

/** Ohne Streamlit: Marken aus den IfcBorehole des Modells (Lage aus der Huelle der Saeule). */
async function nadelnAusIfc() {
  if (!modell || !daten) return;
  const nadeln: Nadel[] = [];
  const bohrungen = await modell.getItemsData(daten.bohrungen, {
    attributesDefault: false, attributes: ["Name"],
    relations: { IsDecomposedBy: { attributes: true, relations: false } },
  });
  const zuLokal = modell.object.matrixWorld.clone().invert();
  for (const b of bohrungen as Record<string, any>[]) {
    const kinder = ((b.IsDecomposedBy ?? []) as Record<string, any>[]).map((k) => Number(k._localId?.value));
    if (!kinder.length) continue;
    const box = (await modell.getMergedBox(kinder)).applyMatrix4(zuLokal);   // IFC-Einheiten: y = m NHN
    const [e0, n0] = modellUrsprung ?? [0, 0];
    const code = String(b.Name?.value ?? "");
    nadeln.push({ id: code, code, x: (box.min.x + box.max.x) / 2 + e0, y: -(box.min.z + box.max.z) / 2 + n0, quelle: "IFC",
                  gok: box.max.y, gok_bekannt: true, ende: box.max.y - box.min.y, geprueft: false, schichten_geprueft: 0,
                  schichten_n: kinder.length, konfidenz: null, im_modell: true, grund: "", schichten: [] });
  }
  editor.setzen(nadeln, null);
  editor.setSichtbar(false);
  editor.markenZeigen = true;
}

/** Mit Streamlit zeichnet der Editor die Saeulen (verschiebbar); die IFC-Saeulen bleiben dann aus. */
async function bohrsaeulenSichtbarkeit() {
  if (!modell || !daten?.bohrsaeulen.length) return;
  const zeigen = bohrungenAn && !nadelnVonStreamlit;
  await modell.setVisible(daten.bohrsaeulen, zeigen);
  await fragments.core.update(true);
}

// ------------------------------------------------------------------ Kamera
async function kameraStart() {
  const gemerkt = kameraGemerkt();
  if (gemerkt) {
    await KAMERA.kameraSetzen(gemerkt);
    return;
  }
  await KAMERA.ansicht(editor.aktiv ? (rahmen.modus === "reihe" ? "sued" : "oben") : "iso", false);
}

function kameraMerken() {
  if (!projekt) return;
  const z = KAMERA.kameraZustand();
  if (![...z.pos, ...z.ziel].every(Number.isFinite)) return;
  try {
    sessionStorage.setItem(`kamera:${projekt}`, JSON.stringify(z));
  } catch { /* privater Modus */ }
  status.kamera = kameraInfo();
}

function kameraGemerkt(): ReturnType<typeof KAMERA.kameraZustand> | null {
  if (!projekt) return null;
  try {
    const t = sessionStorage.getItem(`kamera:${projekt}`);
    return t ? JSON.parse(t) : null;
  } catch {
    return null;
  }
}

function kameraInfo() {
  const k = world.camera.three;
  return { near: k.near, far: k.far, projektion: world.camera.projection.current, radius: KAMERA.szeneKugel().radius };
}

async function fokus() {
  const auswahl = highlighter.selection.select;
  if (modell && !OBC.ModelIdMapUtils.isEmpty(auswahl)) {
    const ids = [...(auswahl[modell.modelId] ?? [])];
    if (ids.length) {
      const box = await modell.getMergedBox(ids);
      await KAMERA.einpassen(box.getBoundingSphere(new THREE.Sphere()));
      return;
    }
  }
  const p = editor.ausgewaehlt ? editor.szenenPunkt(editor.ausgewaehlt) : null;
  if (p) {
    await KAMERA.einpassen(new THREE.Sphere(p, Math.max(15, KAMERA.szeneKugel().radius * 0.03)));
    return;
  }
  await KAMERA.einpassen();
}

// ------------------------------------------------------------------ Ueberhoehung
async function ueberhoehen(faktor: number) {
  if (faktor === rahmen.faktor) return;
  rahmen.faktor = faktor;
  clipper.deleteAll();
  modellPlatzieren();
  editor.neuAufbauen();
  KAMERA.szeneAktualisieren();
  await KAMERA.einpassen();
  await fragments.core.update(true);
  leisteNeu();
}

// ------------------------------------------------------------------ Sichtbarkeit und Auswahl (wie TwinBimM)
const original = new Map<THREE.Material, { transparent: boolean; opacity: number; depthWrite: boolean }>();

function transparent(mat: THREE.Material, an: boolean) {
  if (an) {
    if (!original.has(mat)) original.set(mat, { transparent: mat.transparent, opacity: mat.opacity, depthWrite: mat.depthWrite });
    Object.assign(mat, { transparent: true, opacity: 0.25, depthWrite: false });
  } else {
    const o = original.get(mat);
    if (o) Object.assign(mat, o);
  }
  mat.needsUpdate = true;
}

async function durchscheinen(an: boolean) {
  durchscheinend = an;
  for (const mat of fragments.core.models.materials.list.values()) transparent(mat, an);
  if (!an) original.clear();
  await fragments.core.update(true);
  leisteNeu();
}

async function alleZeigen() {
  await hider.set(true);
  nurEinheit = null;
  for (const id of sichtbar.keys()) sichtbar.set(id, true);
  await bohrsaeulenSichtbarkeit();
  seitenleisteNeu();
}

async function auswahlAusblenden(isolieren: boolean) {
  const auswahl = highlighter.selection.select;
  if (OBC.ModelIdMapUtils.isEmpty(auswahl)) {
    meldung("Erst ein Element anklicken.");
    return;
  }
  if (isolieren) await hider.isolate(auswahl);
  else await hider.set(false, auswahl);
}

let farbeEingabe = "#ff8800";
async function einfaerben() {
  const auswahl = highlighter.selection.select;
  if (OBC.ModelIdMapUtils.isEmpty(auswahl)) {
    meldung("Erst ein Element anklicken.");
    return;
  }
  const farbe = new THREE.Color(farbeEingabe);
  if (!highlighter.styles.has(farbeEingabe)) {
    highlighter.styles.set(farbeEingabe, { color: farbe, renderedFaces: FRAGS.RenderedFaces.ONE, opacity: 1, transparent: false });
  }
  await highlighter.highlightByID(farbeEingabe, auswahl, false, false);
  await highlighter.clear("select");
}

async function auswahlAufheben() {
  await highlighter.clear("select").catch(() => {});
  editor.waehlen(null);
  $("eigenschaften").hidden = true;
  status.auswahl = "";
}

let bohrungenAn = true;
async function bohrungenUmschalten() {
  bohrungenAn = !bohrungenAn;
  editor.setSichtbar(bohrungenAn && nadelnVonStreamlit);
  editor.markenZeigen = bohrungenAn;
  await bohrsaeulenSichtbarkeit();
  leisteNeu();
}

// ------------------------------------------------------------------ Eigenschaften
const formatiere = (v: unknown) => {
  if (typeof v === "boolean") return v ? "ja" : "nein";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toLocaleString("de-DE", { maximumFractionDigits: 2 });
  return esc(String(v));
};

function tabelle(werte: Record<string, unknown>) {
  const zeilen = Object.entries(werte)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `<tr><td>${esc(k.replaceAll("_", " "))}</td><td>${formatiere(v)}</td></tr>`);
  return `<table>${zeilen.join("")}</table>`;
}

const rang = (n: string, liste: string[]) => (liste.includes(n) ? liste.indexOf(n) : liste.length);
const REIHENFOLGE = ["CPset_Modelleinheit", "CPset_Schichtenverzeichnis", "CPset_Herkunft"];

function psetsHtml(ps: Psets) {
  return Object.keys(ps).sort((a, b) => rang(a, REIHENFOLGE) - rang(b, REIHENFOLGE))
    .map((n) => `<h3>${esc(n)}</h3>${tabelle(ps[n])}`).join("");
}

function eigenschaftenZeigen(titel: string, html: string, knoepfe: HTMLElement[] = []) {
  $("auswahl-name").textContent = titel;
  $("auswahl-inhalt").innerHTML = html;
  $("auswahl-knoepfe").replaceChildren(...knoepfe);
  $("eigenschaften").hidden = false;
  status.auswahl = titel;
}

highlighter.events.select.onHighlight.add(async (auswahl) => {
  neuZeichnen(6);
  editor.waehlen(null);
  if (!modell) return;
  const ids = [...(auswahl[modell.modelId] ?? [])];
  if (!ids.length) return;
  const info = await eigenschaften(modell, ids[0]);
  const kopf = { Klasse: info.klasse, Beschreibung: info.beschreibung, Teil_von: info.teilVon };
  eigenschaftenZeigen(info.name, tabelle(kopf) + psetsHtml(info.psets));
  for (const li of document.querySelectorAll<HTMLElement>("#einheiten li")) li.classList.toggle("aktiv", li.dataset.id === String(ids[0]));
});
highlighter.events.select.onClear.add(() => {
  neuZeichnen(6);
  if (!editor.ausgewaehlt) $("eigenschaften").hidden = true;
  status.auswahl = editor.ausgewaehlt ? status.auswahl : "";
  for (const li of document.querySelectorAll<HTMLElement>("#einheiten li")) li.classList.remove("aktiv");
});

async function nadelWaehlen(id: string | null) {
  await highlighter.clear("select").catch(() => {});
  editor.waehlen(id);
  const n = id ? editor.nadeln.get(id)?.daten : undefined;
  if (!n) {
    $("eigenschaften").hidden = true;
    return;
  }
  const lage = n.x === null ? "ohne Lage" :
    rahmen.modus === "reihe" ? `Station ${formatiere(n.x)} m` : `R ${formatiere(n.x)} · H ${formatiere(n.y)}`;
  const kopf: Record<string, unknown> = {
    Lage: lage, Lage_aus: n.quelle || "–",
    GOK: n.gok_bekannt ? `${formatiere(n.gok)} m NHN` : "unbekannt (relativ 0 m)",
    Endteufe: `${formatiere(n.ende)} m`,
    Schichten_geprueft: `${n.schichten_geprueft}/${n.schichten_n}`,
    min_Konfidenz: n.konfidenz ?? "–",
    Im_Modell: n.im_modell ? "ja" : `nein${n.grund ? ` (${n.grund})` : ""}`,
    Geprueft: n.geprueft,
  };
  const schichten = n.schichten.map(([o, u, f, art, k]) =>
    `<tr><td><span class="farbe" style="background:${/^#[0-9a-f]{6}$/i.test(String(f)) ? f : "#ccc"}"></span>` +
    `${formatiere(o)}–${formatiere(u)} m</td><td>${esc(String(art ?? ""))}${k !== undefined && k !== null ? ` · ${formatiere(k)}` : ""}</td></tr>`).join("");
  let html = tabelle(kopf) + (schichten ? `<h3>Schichten</h3><table>${schichten}</table>` : "");
  const lid = modell ? bohrungNachCode.get(n.code) : undefined;
  if (modell && lid !== undefined) html += psetsHtml((await eigenschaften(modell, lid)).psets);
  const knoepfe: HTMLElement[] = [];
  if (eingebettet) {
    const b = document.createElement("bim-button") as BUI.Button;
    b.label = n.geprueft ? "Prüfung zurücknehmen" : "Als geprüft markieren";
    b.icon = n.geprueft ? "mdi:close" : "mdi:check-decagram";
    b.addEventListener("click", () => {
      ereignis({ typ: "geprueft", id: n.id, wert: !n.geprueft });
      meldung(`${n.code}: ${n.geprueft ? "Prüfung zurückgenommen" : "als geprüft markiert"} – wird übernommen …`);
    });
    knoepfe.push(b);
  }
  const f = document.createElement("bim-button") as BUI.Button;
  f.label = "Fokus";
  f.icon = "mdi:fit-to-screen-outline";
  f.addEventListener("click", () => fokus());
  knoepfe.push(f);
  eigenschaftenZeigen(`Bohrung ${n.code}`, html, knoepfe);
}

$("auswahl-zu").addEventListener("click", () => auswahlAufheben());
$("seite-umschalten").addEventListener("click", () => {
  const schmal = window.matchMedia("(max-width: 760px)").matches;
  document.body.classList.toggle(schmal ? "seite-auf" : "zu");
});

// ------------------------------------------------------------------ Schnitte
function schnitt(normale: THREE.Vector3) {
  clipper.createFromNormalAndCoplanarPoint(world, normale, KAMERA.szeneKugel().center.clone());
}

// ------------------------------------------------------------------ Seitenleiste (Modell, Einheiten, Bohrungen)
const [seitenleiste, seitenleisteAktualisieren] = BUI.Component.create<BUI.Panel, Record<string, never>>((_zustand) => {
  const m = daten?.modell ?? {};
  const info: string[] = [];
  if (daten) {
    info.push(`${daten.einheiten.length} Einheiten · ${daten.bohrungen.length} Bohrungen`);
    if (m.Lagebezug !== undefined) info.push(String(m.Lagebezug));
    if (m.Modellbasis_NHN !== undefined) info.push(`Basis ${m.Modellbasis_NHN} m NHN`);
    if (m.Pruefstand) info.push(`Prüfstand: ${m.Pruefstand}`);
  }
  const hinweise = String(m.Hinweise ?? "").split(";").map((h) => h.trim()).filter(Boolean);
  const nadeln = [...editor.nadeln.values()].map((s) => s.daten);
  const einheiten = daten?.einheiten ?? [];
  return BUI.html`
    <bim-panel id="seite" label="Baugrundmodell" icon="mdi:layers-triple">
      <bim-panel-section label="Modell" icon="mdi:cube-outline">
        <bim-label class="modellname">${daten?.modellname || (nadeln.length ? "Noch kein Modell erzeugt" : "Kein Modell geladen")}</bim-label>
        ${info.map((t) => BUI.html`<p class="text leise">${t}</p>`)}
        ${eingebettet ? "" : BUI.html`
          <label class="datei"><input type="file" accept=".ifc" @change=${dateiGewaehlt}><span>IFC-Datei öffnen …</span></label>`}
      </bim-panel-section>
      <bim-panel-section label=${`Einheiten (${einheiten.length})`} icon="mdi:layers-outline">
        ${einheiten.length ? BUI.html`<ul id="einheiten" class="liste">${einheiten.map((e) => {
          const vol = Number(e.psets.CPset_Modelleinheit?.Volumen_m3 ?? 0);
          const an = nurEinheit === null ? sichtbar.get(e.localId) !== false : nurEinheit === e.localId;
          return BUI.html`<li data-id=${String(e.localId)} class=${an ? "" : "aus"} @click=${() => einheitWaehlen(e.localId)}>
            <input type="checkbox" .checked=${sichtbar.get(e.localId) !== false} aria-label=${`${e.name} sichtbar`}
              @click=${(ev: Event) => ev.stopPropagation()} @change=${(ev: Event) => einheitSichtbar(e.localId, (ev.target as HTMLInputElement).checked)}>
            <span class="farbe" style=${`background:${/^#[0-9a-f]{6}$/i.test(e.farbe) ? e.farbe : "#cccccc"}`}></span>
            <span class="name">${e.name}</span>
            <span class="wert">${Math.round(vol).toLocaleString("de-DE")} m³</span>
            <button type="button" class="nur" title="Nur diese Einheit zeigen" aria-pressed=${String(nurEinheit === e.localId)}
              @click=${(ev: Event) => { ev.stopPropagation(); void nurDiese(e.localId); }}>◎</button>
          </li>`;
        })}</ul>` : BUI.html`<bim-label class="leise">${daten ? "Kein IfcGeomodel im IFC – nur Bohrsäulen." : "–"}</bim-label>`}
      </bim-panel-section>
      <bim-panel-section label=${`Bohrungen (${nadeln.length})`} icon="mdi:map-marker-radius" ?collapsed=${nadeln.length > 30}>
        ${nadeln.length ? BUI.html`<ul class="liste bohrliste">${nadeln.map((n) => BUI.html`
          <li class=${n.id === editor.ausgewaehlt ? "aktiv" : ""} @click=${() => { void nadelWaehlen(n.id); void fokus(); }}>
            <span class=${`zustand ${n.geprueft ? "ok" : n.konfidenz !== null && n.konfidenz < 0.6 ? "warn" : ""} ${n.im_modell ? "" : "raus"}`}>
              ${n.geprueft ? "✓" : n.x === null ? "◌" : n.konfidenz !== null && n.konfidenz < 0.6 ? "!" : "•"}</span>
            <span class="name">${n.code}</span>
            <span class="wert">${n.schichten_geprueft}/${n.schichten_n}${n.konfidenz !== null ? ` · ${n.konfidenz.toFixed(2)}` : ""}</span>
          </li>`)}</ul>
          <p class="text leise">✓ geprüft · ! Konfidenz &lt; 0,6 · ◌ ohne Lage · grau: nicht im Modell</p>`
        : BUI.html`<bim-label class="leise">–</bim-label>`}
      </bim-panel-section>
      ${hinweise.length || m.Nicht_im_Modell ? BUI.html`
        <bim-panel-section label="Hinweise" icon="mdi:alert-outline" collapsed>
          ${hinweise.map((h) => BUI.html`<p class="text">${h}</p>`)}
          ${m.Nicht_im_Modell ? BUI.html`<p class="text leise">Nicht im Modell: ${String(m.Nicht_im_Modell)}</p>` : ""}
        </bim-panel-section>` : ""}
    </bim-panel>`;
}, {});
$("seitenleiste").append(seitenleiste);
function seitenleisteNeu() {
  seitenleisteAktualisieren();
}

async function einheitWaehlen(id: number) {
  if (!modell) return;
  await highlighter.highlightByID("select", { [modell.modelId]: new Set([id]) }, true, false);
}

async function einheitSichtbar(id: number, an: boolean) {
  if (!modell) return;
  sichtbar.set(id, an);
  await hider.set(an, { [modell.modelId]: new Set([id]) });
  seitenleisteNeu();
}

async function nurDiese(id: number) {
  if (!modell || !daten) return;
  nurEinheit = nurEinheit === id ? null : id;
  for (const e of daten.einheiten) {
    const zeigen = nurEinheit === null ? sichtbar.get(e.localId) !== false : e.localId === nurEinheit;
    await hider.set(zeigen, { [modell.modelId]: new Set([e.localId]) });
  }
  seitenleisteNeu();
}

async function dateiGewaehlt(ev: Event) {
  const f = (ev.target as HTMLInputElement).files?.[0];
  if (f) await laden(new Uint8Array(await f.arrayBuffer()), f.name, false);
}

// ------------------------------------------------------------------ Werkzeugleiste unten (wie TwinBimM)
const FAKTOREN = [1, 2, 5, 10, 20];
const [leiste, leisteAktualisieren] = BUI.Component.create<BUI.Toolbar, Record<string, never>>((_zustand) => BUI.html`
  <bim-toolbar>
    <bim-toolbar-section label="Ansicht" icon="mdi:cube-outline">
      <bim-button ?label-hidden=${schmal} label="Iso" icon="mdi:axis-arrow"
        @click=${() => KAMERA.ansicht("iso")}>${tipp("Isometrisch", "Schräg von Südosten auf die ganze Szene.")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Oben" icon="mdi:arrow-down-bold-box-outline" @click=${() => KAMERA.ansicht("oben")}>${tipp("Draufsicht")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Süd" icon="mdi:arrow-up-bold-box-outline" @click=${() => KAMERA.ansicht("sued")}>${tipp("Ansicht von Süden (Längsschnitt)", "Weitere Seiten: Würfel oben rechts.")}</bim-button>
      <bim-dropdown label="Überhöhung" .value=${[rahmen.faktor]} @change=${(e: Event) => {
        const [v] = (e.target as BUI.Dropdown).value as number[];
        if (v) void ueberhoehen(Number(v));
      }}>
        ${FAKTOREN.map((f) => BUI.html`<bim-option label=${`${f}×`} .value=${f} ?checked=${rahmen.faktor === f}></bim-option>`)}
      </bim-dropdown>
    </bim-toolbar-section>
    <bim-toolbar-section label="Sichtbarkeit" icon="mdi:eye">
      <bim-button ?label-hidden=${schmal} label="Alle anzeigen" icon="mdi:eye" @click=${() => alleZeigen()}>${tipp("Alle einblenden", "Alle ausgeblendeten Elemente wieder einblenden.")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Transparenz" icon="mdi:ghost" ?active=${durchscheinend} @click=${() => durchscheinen(!durchscheinend)}>${tipp("Transparenz-Modus", "Einheiten durchscheinend: Bohrungen und Auswahl im Inneren sichtbar.")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Bohrungen" icon="mdi:map-marker-radius" ?active=${bohrungenAn}
        @click=${() => bohrungenUmschalten()}>${tipp("Bohrungen ein/aus")}</bim-button>
    </bim-toolbar-section>
    <bim-toolbar-section label="Auswahl" icon="mdi:cursor-default-click">
      <bim-button ?label-hidden=${schmal} label="Fokus" icon="mdi:fit-to-screen-outline" @click=${() => fokus()}>${tipp("Kameraausrichtung", "Kamera auf die Auswahl; ohne Auswahl die ganze Szene.")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Ausblenden" icon="mdi:eye-off" @click=${() => auswahlAusblenden(false)}>${tipp("Auswahl ausblenden")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Isolieren" icon="mdi:selection-ellipse" @click=${() => auswahlAusblenden(true)}>${tipp("Auswahl isolieren", "Alle anderen Elemente ausblenden.")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Einfärben" icon="mdi:format-color-fill">
        <bim-context-menu>
          <div class="einfaerben">
            <input type="color" .value=${farbeEingabe} @input=${(e: Event) => (farbeEingabe = (e.target as HTMLInputElement).value)}>
            <bim-button ?label-hidden=${schmal} label="Anwenden" @click=${() => einfaerben()}></bim-button>
          </div>
        </bim-context-menu>
      </bim-button>
    </bim-toolbar-section>
    <bim-toolbar-section label="Schnitt" icon="mdi:content-cut">
      <bim-button ?label-hidden=${schmal} label="O–W" icon="mdi:content-cut"
        @click=${() => schnitt(new THREE.Vector3(0, 0, -1))}>${tipp("Senkrechter Schnitt in Ost-West-Richtung")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="N–S" icon="mdi:content-cut"
        @click=${() => schnitt(new THREE.Vector3(1, 0, 0))}>${tipp("Senkrechter Schnitt in Nord-Süd-Richtung")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Ebene" icon="mdi:vector-square" ?active=${schnittWerkzeug}
        @click=${() => { schnittWerkzeug = !schnittWerkzeug; leisteNeu(); }}>${tipp("Schnittebene per Doppelklick", "Doppelklick auf eine Fläche legt dort eine Ebene. Entf löscht die Ebene unter der Maus.")}</bim-button>
      <bim-button ?label-hidden=${schmal} label="Löschen" icon="mdi:delete-outline" @click=${() => clipper.deleteAll()}>${tipp("Alle Schnitte löschen")}</bim-button>
    </bim-toolbar-section>
    <bim-toolbar-section label="Lage" icon="mdi:map-marker-radius">
      <bim-button ?label-hidden=${schmal} label="Lage bearbeiten" icon="mdi:cursor-move" ?active=${editor.aktiv} ?disabled=${!editor.nadeln.size}
        @click=${() => lageModus(!editor.aktiv)}>${tipp("Bohrungen setzen", "Bohrungen ziehen – auf dem Lageplan (Draufsicht) oder entlang der Reihe im Längsschnitt. Das Modell rechnet nach.")}</bim-button>
    </bim-toolbar-section>
  </bim-toolbar>`, {});
$("leiste").append(leiste);
function leisteNeu() {
  leisteAktualisieren();
}
// Schmale Ansicht (Streamlit-Spalte, Lage-Panel offen): nur Icons, Beschriftung im Tooltip
function leisteBreite() {
  const jetzt = viewport.clientWidth < (editor.aktiv ? 1900 : 1500);
  leiste.labelsHidden = jetzt;
  if (jetzt !== schmal) {
    schmal = jetzt;
    leisteNeu();
  }
}
new ResizeObserver(leisteBreite).observe(viewport);

// ------------------------------------------------------------------ Oben rechts: Koordinaten, Zahnrad, ViewCube
let koordinatenAn = false;
const [einstellungen, einstellungenNeu] = BUI.Component.create<HTMLDivElement, Record<string, never>>((_zustand) => BUI.html`
  <div class="oben-rechts">
    <bim-button class="koord" label="⌖ Koord." ?active=${koordinatenAn}
      @click=${(e: Event) => { koordinatenAn = !koordinatenAn; (e.target as BUI.Button).active = koordinatenAn; $("hud").hidden = !koordinatenAn; }}>${tipp("Koordinaten anzeigen", "Rechts-/Hochwert und Höhe NHN unter der Maus (Reihe: Station).")}</bim-button>
    <bim-button class="zahnrad" icon="mdi:cog">${tipp("Einstellungen")}
      <bim-context-menu>
        <bim-checkbox label="Raster" ?checked=${raster.visible} @change=${(e: Event) => { raster.visible = (e.target as BUI.Checkbox).checked; }}></bim-checkbox>
        <bim-checkbox label="Orbit um Mauspunkt" ?checked=${world.dynamicAnchor}
          @change=${(e: Event) => { world.dynamicAnchor = (e.target as BUI.Checkbox).checked; }}></bim-checkbox>
        <bim-checkbox label="Kanten und Schatten" ?checked=${postproduction.enabled}
          @change=${(e: Event) => { postproduction.enabled = (e.target as BUI.Checkbox).checked; }}></bim-checkbox>
        <bim-dropdown label="Kameraprojektion" .value=${[world.camera.projection.current]} @change=${async (e: Event) => {
          const [p] = (e.target as BUI.Dropdown).value as string[];
          if (p) await world.camera.projection.set(p as OBC.CameraProjection);
        }}>
          <bim-option label="Perspektivisch" .value=${"Perspective"} ?checked=${world.camera.projection.current === "Perspective"}></bim-option>
          <bim-option label="Orthografisch" .value=${"Orthographic"} ?checked=${world.camera.projection.current === "Orthographic"}></bim-option>
        </bim-dropdown>
      </bim-context-menu>
    </bim-button>
  </div>`, {});
viewport.append(einstellungen);

const wuerfel = document.createElement("bim-view-cube") as BUIC.ViewCube;
wuerfel.camera = world.camera.three;
Object.assign(wuerfel, { topText: "OBEN", bottomText: "UNTEN", frontText: "SÜD", backText: "NORD", rightText: "OST", leftText: "WEST" });
wuerfel.classList.add("wuerfel");
viewport.append(wuerfel);
world.camera.controls.addEventListener("update", () => wuerfel.updateOrientation());
for (const [ereignisName, art] of [["topclick", "oben"], ["bottomclick", "unten"], ["frontclick", "sued"], ["backclick", "nord"],
  ["rightclick", "ost"], ["leftclick", "west"]] as const) {
  wuerfel.addEventListener(ereignisName, () => KAMERA.ansicht(art));
}
world.camera.projection.onChanged.add(() => {
  for (const m of fragments.list.values()) m.useCamera(world.camera.three);
  postproduction.updateCamera();
  wuerfel.camera = world.camera.three;
  fragments.core.update(true);
  status.kamera = kameraInfo();
  einstellungenNeu();                                  // Auswahl "Kameraprojektion" nachziehen
});

// Koordinatenanzeige: Treffer im Modell (Fragments-Raycast), sonst Bohrungen/Unterlage, sonst Rasterebene
const hud = $("hud");
const strahl = new THREE.Raycaster();
let hudBild = 0;
let hudMaus = { x: 0, y: 0 };
viewport.addEventListener("pointermove", (ev) => {
  if (!koordinatenAn) return;
  hudMaus = { x: ev.clientX, y: ev.clientY };
  if (!hudBild) hudBild = requestAnimationFrame(hudAktualisieren);
});
async function hudAktualisieren() {
  hudBild = 0;
  const r = world.renderer!.three.domElement.getBoundingClientRect();
  const ndc = new THREE.Vector2(((hudMaus.x - r.left) / r.width) * 2 - 1, -((hudMaus.y - r.top) / r.height) * 2 + 1);
  strahl.setFromCamera(ndc, world.camera.three);
  const ursprung = strahl.ray.origin.clone();
  const eigene = strahl.intersectObjects([editor.gruppe, ...world.scene.three.children.filter((o) => o.name === "Unterlage" && o.visible)], true);
  let p: THREE.Vector3 | null = eigene[0]?.point ?? null;
  let zusatz = "";
  if (!p) {
    const boden = new THREE.Plane(new THREE.Vector3(0, 1, 0), -raster.three.position.y);
    p = strahl.ray.intersectPlane(boden, new THREE.Vector3());
    zusatz = " (Rasterebene)";
  }
  hud.textContent = p ? `${koordinatenText(p)}${zusatz}` : "–";
  // Treffer im Modell kommt aus dem Fragments-Worker (asynchron); naeher als das Bisherige -> ersetzen
  const maus = { ...hudMaus };
  const treffer = modell?.object.visible ? await caster.castRay({ position: ndc }).catch(() => null) : null;
  if (!treffer?.point || maus.x !== hudMaus.x || maus.y !== hudMaus.y) return;
  if (!p || zusatz || treffer.point.distanceTo(ursprung) < p.distanceTo(ursprung)) hud.textContent = koordinatenText(treffer.point);
}

// ------------------------------------------------------------------ Lage-Modus
async function lageModus(an: boolean) {
  if (an === editor.aktiv) return;
  if (an) {
    kameraVorLage = KAMERA.kameraZustand();
    seiteVorLage = document.body.classList.contains("zu");
    document.body.classList.add("zu");                 // Platz fuer Plan und Lage-Panel
    await auswahlAufheben();
  } else {
    document.body.classList.toggle("zu", seiteVorLage);
  }
  highlighter.enabled = !an;
  await editor.umschalten(an);
  // Panel erst nach dem Zeichnen messen (BUI rendert asynchron); die Ansicht zentriert rechts davon
  await new Promise((r) => requestAnimationFrame(() => requestAnimationFrame(r)));
  const panel = editor.panel.getBoundingClientRect();
  const rechts = panel.width > 50 ? panel.right - viewport.getBoundingClientRect().left : 12 + 23 * 16;
  KAMERA.linksFrei(an ? rechts + 8 : 0);
  editor.setSichtbar(bohrungenAn && (nadelnVonStreamlit || an));
  if (modell) modell.object.visible = !an;
  KAMERA.szeneAktualisieren();
  if (an) {
    await world.camera.projection.set("Orthographic");
    await KAMERA.ansicht(rahmen.modus === "reihe" ? "sued" : "oben");
    meldung(rahmen.modus === "reihe"
      ? "Lage: Marken entlang der Reihe ziehen (Umschalt: Höhe). Esc beendet."
      : "Lage: Marken auf dem Plan ziehen. Bohrungen ohne Lage aus der Liste links in die Ansicht ziehen. Esc beendet.", 7000);
  } else {
    if (kameraVorLage) {
      if (!kameraVorLage.ortho) await world.camera.projection.set("Perspective");
      await KAMERA.kameraSetzen(kameraVorLage);
    }
    await fragments.core.update(true);
  }
  leisteNeu();
}

// ------------------------------------------------------------------ Maus und Tastatur
const flaeche = world.renderer.three.domElement;
flaeche.addEventListener("dblclick", async () => {
  if (editor.aktiv) return;
  if (schnittWerkzeug) {
    clipper.create(world);
    return;
  }
  const t = await caster.castRay();
  if (t?.point) await KAMERA.orbitPunkt(t.point);                // Drehpunkt auf den Doppelklick
});
window.addEventListener("keydown", async (ev) => {
  const ziel = ev.target as HTMLElement;
  if (ziel?.closest?.("input, select, textarea, bim-text-input, bim-number-input")) return;
  if (ev.code === "Delete" || ev.code === "Backspace") clipper.delete(world);
  if (ev.key === "Escape") {
    if (editor.escape()) return;
    if (editor.aktiv) await lageModus(false);
    else await auswahlAufheben();
  }
});

// Ablegen einer IFC-Datei (ohne Streamlit)
document.body.addEventListener("dragover", (ev) => {
  if (!ev.dataTransfer?.types.includes("Files")) return;
  ev.preventDefault();
  document.body.classList.add("ziehen");
});
document.body.addEventListener("dragleave", () => document.body.classList.remove("ziehen"));
document.body.addEventListener("drop", async (ev) => {
  ev.preventDefault();
  document.body.classList.remove("ziehen");
  const f = ev.dataTransfer?.files?.[0];
  if (f) await laden(new Uint8Array(await f.arrayBuffer()), f.name, false);
});


// ------------------------------------------------------------------ Streamlit
// Renders koennen waehrend des Ladens kommen: immer nur den neuesten verarbeiten.
let wartend: Args | null = null;
let laeuft = false;
let letzte: Args = {};

async function argsVerarbeiten(a: Args) {
  wartend = a;
  if (laeuft) return;
  laeuft = true;
  try {
    while (wartend) {
      const naechste = wartend;
      wartend = null;
      await argsAnwenden(naechste);
    }
  } catch (err) {
    status.fehler = String(err);
  } finally {
    laeuft = false;
  }
}

async function argsAnwenden(a: Args) {
  status.renders += 1;
  hoeheSetzen(Number(a.hoehe ?? 760));
  nrMindestens(Number(a.nr ?? 0));
  const neu = (a.projekt ?? "") !== projekt;
  if (neu) {
    projekt = a.projekt ?? "";
    projektSetzen(projekt);
    bezugGesetzt = false;
    if (editor.aktiv) await lageModus(false);
  }
  nadelnVonStreamlit = Array.isArray(a.bohrungen);
  rahmen.modus = a.modus ?? "koordinaten";
  rahmen.epsg = a.epsg ?? null;
  if (a.ursprung) [rahmen.e0, rahmen.n0] = a.ursprung;
  if (a.ueberhoehung && a.ueberhoehung !== letzte.ueberhoehung) rahmen.faktor = Number(a.ueberhoehung);
  const nadeln = a.bohrungen ?? [];
  if (!bezugGesetzt && nadeln.length) {
    rahmen.bezug = Math.floor(Math.min(...nadeln.map((n) => n.gok - n.ende)));
    bezugGesetzt = true;
  }
  editor.markenZeigen = bohrungenAn;
  editor.setzen(nadeln, a.unterlage ?? null);
  editor.setSichtbar(bohrungenAn && nadelnVonStreamlit);
  status.marken = editor.nadeln.size;
  const url = a.ifc ?? "";
  if (url && url !== ifcUrl) {
    ifcUrl = url;
    status.geladeneIfc.push(url.split("/").pop() ?? url);
    await ladenUrl(url, a.titel ?? "", !neu && (modell !== null || editor.nadeln.size > 0));
  } else if (!url && modell) {
    ifcUrl = "";
    await modellEntfernen();
  } else {
    modellPlatzieren();
  }
  $("leer").hidden = !!modell || editor.nadeln.size > 0;
  KAMERA.szeneAktualisieren();
  if (neu && !modell) await kameraStart();
  if (a.bearbeiten && a.bearbeiten !== letzte.bearbeiten) await lageModus(true);
  letzte = a;
  seitenleisteNeu();
  leisteNeu();
  if (editor.ausgewaehlt) void nadelWaehlen(editor.ausgewaehlt);
  status.kamera = kameraInfo();
  neuZeichnen(10);
}

(window as unknown as { viewer: unknown }).viewer = {
  world, editor, rahmen, KAMERA, ausSzene, hoeheAusSzene, argsVerarbeiten, lageModus, ueberhoehen,
  modell: () => modell,
};

if (eingebettet) {
  document.body.classList.add("eingebettet");
  starten((a) => void argsVerarbeiten(a));
} else {
  const parameter = new URLSearchParams(location.search);
  const f = Number(parameter.get("ueberhoehung"));
  if (FAKTOREN.includes(f)) rahmen.faktor = f;
  const url = parameter.get("ifc");
  if (url) await ladenUrl(url, "", false);
  // Pruefungen ohne Streamlit: ?bohrungen=<json-url> laedt Stecknadeln wie aus der App
  const nadelUrl = parameter.get("bohrungen");
  if (nadelUrl) {
    const a = (await (await fetch(nadelUrl)).json()) as Args;
    await argsVerarbeiten(a);
  }
  leisteNeu();
}
