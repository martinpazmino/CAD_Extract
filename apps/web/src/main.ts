// Baugrundmodell-Viewer: IFC4X3 (IfcGeomodel + IfcBorehole aus services/modeler) in That Open Engine.
import * as THREE from "three";
import * as OBC from "@thatopen/components";
import * as FRAGS from "@thatopen/fragments";
import * as WEBIFC from "web-ifc";
import { eigenschaften, inhalt, type Inhalt, type Psets } from "./baugrund";

// Geotechnik-Klassen: der IfcImporter verwirft sie sonst (Architektur 8.2)
const GEOTECHNIK = [WEBIFC.IFCBOREHOLE, WEBIFC.IFCGEOMODEL, WEBIFC.IFCGEOSLICE, WEBIFC.IFCGEOTECHNICALSTRATUM];
const AUSWAHL: FRAGS.MaterialDefinition = {
  color: new THREE.Color("#1e6fd9"), renderedFaces: FRAGS.RenderedFaces.TWO, opacity: 1, transparent: false,
};
// Durchscheinend ohne Tiefenschreiben: sonst verdecken sich die transparenten Koerper gegenseitig
const DURCHSCHEINEND = {
  opacity: 0.28, transparent: true, depthWrite: false, renderedFaces: FRAGS.RenderedFaces.TWO,
  preserveOriginalMaterial: true, _explicitProps: ["opacity", "transparent", "depthWrite", "renderedFaces"],
} as unknown as FRAGS.MaterialDefinition;
const vendor = new URL("vendor/", new URL(import.meta.env.BASE_URL, location.href)).href;

const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

// Status fuer automatische Pruefungen (scripts/check.mjs)
const status = { geladen: false, einheiten: [] as string[], bohrsaeulen: 0, marken: 0, fehler: "", auswahl: "" };
(window as unknown as { baugrund: typeof status }).baugrund = status;

// ------------------------------------------------------------------ Welt
const components = new OBC.Components();
const world = components.get(OBC.Worlds).create<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.SimpleRenderer>();
world.scene = new OBC.SimpleScene(components);
world.scene.setup();
world.scene.three.background = new THREE.Color("#f4f5f7");
world.renderer = new OBC.SimpleRenderer(components, $("viewer"));
world.camera = new OBC.OrthoPerspectiveCamera(components);
components.init();
components.get(OBC.Grids).create(world);
const caster = components.get(OBC.Raycasters).get(world);

const fragments = components.get(OBC.FragmentsManager);
fragments.init(`${vendor}worker.mjs`);
world.camera.controls.addEventListener("rest", () => fragments.core.update(true));
fragments.list.onItemSet.add(({ value: model }) => {
  model.useCamera(world.camera.three);
  world.scene.three.add(model.object);
  fragments.core.update(true);
});

const ifcLoader = components.get(OBC.IfcLoader);
await ifcLoader.setup({ autoSetWasm: false, wasm: { path: vendor, absolute: true } });
ifcLoader.onIfcImporterInitialized.add((importer) => {
  for (const c of GEOTECHNIK) importer.classes.elements.add(c);
});

const clipper = components.get(OBC.Clipper);
clipper.enabled = true;
clipper.material = new THREE.MeshBasicMaterial({
  color: "#1e6fd9", transparent: true, opacity: 0.08, side: THREE.DoubleSide, depthWrite: false,
});

// ------------------------------------------------------------------ Zustand
let modell: FRAGS.FragmentsModel | null = null;
let daten: Inhalt | null = null;
let auswahl: number | null = null;
let durchscheinend = false;
let lage = { y0: 0, basis: 0 };                       // Ausgangslage fuer die Ueberhoehung

function meldung(text: string, dauer = 4000) {
  const el = $("meldung");
  el.textContent = text;
  el.hidden = false;
  window.setTimeout(() => (el.hidden = true), dauer);
}

async function laden(bytes: Uint8Array, name: string) {
  try {
    meldung(`${name} wird geladen …`, 60000);
    for (const id of [...fragments.list.keys()]) await fragments.core.disposeModel(id);
    clipper.deleteAll();
    modell = await ifcLoader.load(bytes, true, name);
    daten = await inhalt(modell);
    lage = { y0: modell.object.position.y, basis: modell.box.min.y };
    auswahl = null;
    $("eigenschaften").hidden = true;
    zeigeModell(name);
    await ueberhoehen(Number($<HTMLSelectElement>("ueberhoehung").value));
    await darstellen();
    await bohrungsmarken();
    await world.camera.fitToItems();
    status.geladen = true;
    status.marken = marken.length;
    status.einheiten = daten.einheiten.map((e) => e.name);
    status.bohrsaeulen = daten.bohrsaeulen.length;
    meldung(`${name}: ${daten.einheiten.length} Einheiten, ${daten.bohrungen.length} Bohrungen`);
  } catch (err) {
    status.fehler = String(err);
    meldung(`Fehler beim Laden: ${err}`, 10000);
    throw err;
  }
}

function zeigeModell(name: string) {
  if (!daten) return;
  const m = daten.modell;
  const teile = [daten.modellname || name, `${daten.einheiten.length} Einheiten`, `${daten.bohrungen.length} Bohrungen`];
  if (m.Modellbasis_NHN !== undefined) teile.push(`Basis ${m.Modellbasis_NHN} m NHN`);
  $("modellinfo").textContent = teile.join(" · ");
  $("ausgeschlossen").textContent = String(m.Nicht_im_Modell ?? "") || "–";
  const liste = $("einheiten");
  liste.replaceChildren();
  if (!daten.einheiten.length) {
    liste.innerHTML = `<li class="leise">Kein IfcGeomodel im IFC – nur Bohrsäulen.</li>`;
  }
  for (const e of daten.einheiten) {
    const li = document.createElement("li");
    li.dataset.id = String(e.localId);
    const volumen = Number(e.psets.CPset_Modelleinheit?.Volumen_m3 ?? 0);
    const box = document.createElement("input");
    box.type = "checkbox";
    box.checked = true;
    box.setAttribute("aria-label", "sichtbar");
    const farbe = document.createElement("span");
    farbe.className = "farbe";
    farbe.style.background = /^#[0-9a-f]{6}$/i.test(e.farbe) ? e.farbe : "#cccccc";
    const name = document.createElement("span");
    name.textContent = e.name;
    const wert = document.createElement("span");
    wert.className = "wert";
    wert.textContent = `${Math.round(volumen).toLocaleString("de-DE")} m³`;
    li.append(box, farbe, name, wert);
    box.addEventListener("click", (ev) => ev.stopPropagation());
    box.addEventListener("change", async () => {
      if (!modell) return;
      await modell.setVisible([e.localId], box.checked);
      await fragments.core.update(true);
    });
    li.addEventListener("click", () => waehlen(e.localId));
    liste.append(li);
  }
}

// Hervorhebungen immer komplett neu: Durchscheinen der Einheiten, darueber die Auswahl
async function darstellen() {
  if (!modell || !daten) return;
  await modell.resetHighlight();
  if (durchscheinend && daten.einheiten.length) {
    await modell.highlight(daten.einheiten.map((e) => e.localId), DURCHSCHEINEND);
  }
  if (auswahl !== null) await modell.highlight([auswahl], AUSWAHL);
  await fragments.core.update(true);
}

// Ueberhoehung: y skalieren, die Modellbasis bleibt auf ihrer Hoehe
async function ueberhoehen(faktor: number) {
  if (!modell) return;
  modell.object.scale.y = faktor;
  modell.object.position.y = lage.y0 + (1 - faktor) * (lage.basis - lage.y0);
  modell.object.updateMatrixWorld(true);
  await fragments.core.update(true);
}

// ------------------------------------------------------------------ Bohrungsmarken
// Code jeder Bohrung ueber ihrer Saeule; Lage lokal gespeichert, damit die Ueberhoehung mitgeht
const markenEbene = document.createElement("div");
markenEbene.id = "marken";
$("viewer").append(markenEbene);
let marken: { el: HTMLDivElement; lokal: THREE.Vector3 }[] = [];

async function bohrungsmarken() {
  markenEbene.replaceChildren();
  marken = [];
  if (!modell || !daten?.bohrungen.length) return;
  const bohrungen = await modell.getItemsData(daten.bohrungen, {
    attributesDefault: false, attributes: ["Name"], relations: { IsDecomposedBy: { attributes: true, relations: false } },
  });
  const zuLokal = modell.object.matrixWorld.clone().invert();
  for (const b of bohrungen as Record<string, any>[]) {
    const kinder = ((b.IsDecomposedBy ?? []) as Record<string, any>[]).map((k) => Number(k._localId?.value));
    if (!kinder.length) continue;
    const box = await modell.getMergedBox(kinder);
    const oben = new THREE.Vector3((box.min.x + box.max.x) / 2, box.max.y, (box.min.z + box.max.z) / 2);
    const el = document.createElement("div");
    el.className = "marke";
    el.textContent = String(b.Name?.value ?? "");
    markenEbene.append(el);
    marken.push({ el, lokal: oben.applyMatrix4(zuLokal) });
  }
}

const punkt = new THREE.Vector3();
world.renderer!.onAfterUpdate.add(() => {
  if (!modell || !marken.length) return;
  const sichtbar = $<HTMLInputElement>("bohrsaeulen").checked;
  const { clientWidth: w, clientHeight: h } = markenEbene;
  for (const m of marken) {
    punkt.copy(m.lokal).applyMatrix4(modell.object.matrixWorld).project(world.camera.three);
    const drin = sichtbar && punkt.z < 1 && Math.abs(punkt.x) <= 1 && Math.abs(punkt.y) <= 1;
    m.el.hidden = !drin;
    if (drin) {
      m.el.style.left = `${((punkt.x + 1) / 2) * w}px`;
      m.el.style.top = `${((1 - punkt.y) / 2) * h - 4}px`;
    }
  }
});

// ------------------------------------------------------------------ Auswahl und Eigenschaften
// Texte aus dem IFC sind Daten: immer maskieren
const esc = (t: string) => t.replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" })[c]!);

function tabelle(werte: Record<string, unknown>) {
  const zeilen = Object.entries(werte)
    .filter(([, v]) => v !== undefined && v !== null && v !== "")
    .map(([k, v]) => `<tr><td>${esc(k.replaceAll("_", " "))}</td><td>${formatiere(v)}</td></tr>`);
  return `<table>${zeilen.join("")}</table>`;
}

function formatiere(v: unknown) {
  if (typeof v === "boolean") return v ? "ja" : "nein";
  if (typeof v === "number") return Number.isInteger(v) ? String(v) : v.toLocaleString("de-DE", { maximumFractionDigits: 2 });
  return esc(String(v));
}

const rang = (n: string, liste: string[]) => (liste.includes(n) ? liste.indexOf(n) : liste.length);

async function waehlen(localId: number | null) {
  if (!modell) return;
  auswahl = localId;
  for (const li of $("einheiten").querySelectorAll("li")) li.classList.toggle("aktiv", li.dataset.id === String(localId));
  await darstellen();
  if (localId === null) {
    $("eigenschaften").hidden = true;
    status.auswahl = "";
    return;
  }
  const info = await eigenschaften(modell, localId);
  $("auswahl-name").textContent = info.name;
  const kopf: Record<string, unknown> = { Klasse: info.klasse, Beschreibung: info.beschreibung, Teil_von: info.teilVon };
  const reihenfolge = ["CPset_Modelleinheit", "CPset_Schichtenverzeichnis", "CPset_Herkunft"];
  const namen = Object.keys(info.psets).sort((a, b) => rang(a, reihenfolge) - rang(b, reihenfolge));
  $("auswahl-inhalt").innerHTML = tabelle(kopf) +
    namen.map((n) => `<h3>${esc(n)}</h3>${tabelle((info.psets as Psets)[n])}`).join("");
  $("eigenschaften").hidden = false;
  status.auswahl = info.name;
}

$("viewer").addEventListener("click", async () => {
  const treffer = (await caster.castRay()) as unknown as { localId?: number } | null;
  await waehlen(treffer?.localId ?? null);
});
$("viewer").addEventListener("dblclick", () => clipper.create(world));
$("auswahl-zu").addEventListener("click", () => waehlen(null));

// ------------------------------------------------------------------ Ansicht
$<HTMLInputElement>("bohrsaeulen").addEventListener("change", async (ev) => {
  if (!modell || !daten) return;
  await modell.setVisible(daten.bohrsaeulen, (ev.target as HTMLInputElement).checked);
  await fragments.core.update(true);
});

$<HTMLInputElement>("transparent").addEventListener("change", async (ev) => {
  durchscheinend = (ev.target as HTMLInputElement).checked;
  await darstellen();
});

$<HTMLSelectElement>("ueberhoehung").addEventListener("change", async (ev) => {
  clipper.deleteAll();
  await ueberhoehen(Number((ev.target as HTMLSelectElement).value));
  await world.camera.fitToItems();
});

function schnitt(normale: THREE.Vector3) {
  if (!modell) return;
  const mitte = new THREE.Box3().setFromObject(modell.object).getCenter(new THREE.Vector3());
  clipper.createFromNormalAndCoplanarPoint(world, normale, mitte);
}
// IFC: x = Osten, y = Norden; three.js: y oben, Norden = -z
$("schnitt-ow").addEventListener("click", () => schnitt(new THREE.Vector3(0, 0, -1)));
$("schnitt-ns").addEventListener("click", () => schnitt(new THREE.Vector3(1, 0, 0)));
$("schnitt-weg").addEventListener("click", () => clipper.deleteAll());

// ------------------------------------------------------------------ Laden
$<HTMLInputElement>("datei").addEventListener("change", async (ev) => {
  const f = (ev.target as HTMLInputElement).files?.[0];
  if (f) await laden(new Uint8Array(await f.arrayBuffer()), f.name);
});
document.body.addEventListener("dragover", (ev) => {
  ev.preventDefault();
  document.body.classList.add("ziehen");
});
document.body.addEventListener("dragleave", () => document.body.classList.remove("ziehen"));
document.body.addEventListener("drop", async (ev) => {
  ev.preventDefault();
  document.body.classList.remove("ziehen");
  const f = ev.dataTransfer?.files?.[0];
  if (f) await laden(new Uint8Array(await f.arrayBuffer()), f.name);
});

const parameter = new URLSearchParams(location.search);
if (parameter.get("ueberhoehung")) $<HTMLSelectElement>("ueberhoehung").value = parameter.get("ueberhoehung")!;
const url = parameter.get("ifc");
if (url) {
  const antwort = await fetch(url);
  if (antwort.ok) await laden(new Uint8Array(await antwort.arrayBuffer()), url.split("/").pop() ?? url);
  else meldung(`${url}: HTTP ${antwort.status}`, 10000);
}
