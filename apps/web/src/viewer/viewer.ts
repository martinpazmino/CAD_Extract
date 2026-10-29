// Baugrundmodell-Viewer auf That Open Engine 3.6. Bedienung wie im TwinBimM-Viewer (BUI im W&F-Design,
// ViewCube, Postproduktion, Highlighter/Hider, kompakte Werkzeugleiste unten, Zahnrad, Koordinatenanzeige),
// Kamera fuer Trassen ueber 5 km (kamera.ts) und Lage-Editor mit PDF-Unterlage (lage.ts).
// Ein Viewer je Seite: viewerStarten() baut ihn in ein Element; die Schritt-App (src/app) steuert ihn ueber die
// zurueckgegebene Schnittstelle, viewer.html (allein.ts) laedt ein IFC. Beschreibung: docs/20, docs/21.
// BUI.Component.create erkennt zustandsbehaftete Vorlagen an der Stelligkeit: daher (_zustand) => statt () =>.
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
import { ereignis, empfaengerSetzen, mitApp, projektSetzen, protokoll, type Args, type Nadel } from "./kanal";

// Geotechnik-Klassen: der IfcImporter verwirft sie sonst (Architektur 8.2)
const GEOTECHNIK = [WEBIFC.IFCBOREHOLE, WEBIFC.IFCGEOMODEL, WEBIFC.IFCGEOSLICE, WEBIFC.IFCGEOTECHNICALSTRATUM];
const GRUEN = "#a2c513";                              // W&F-Gruen (Auswahl), wie TwinBimM
const FAKTOREN = [1, 2, 5, 10, 20];
const $ = <T extends HTMLElement>(id: string) => document.getElementById(id) as T;

const GERUEST = `
  <aside id="seitenleiste"></aside>
  <bim-viewport id="viewer">
    <button id="seite-umschalten" class="ecke" type="button" title="Seitenleiste ein/aus" aria-label="Seitenleiste">☰</button>
    <div id="leiste" class="leiste-unten"></div>
    <div id="hud" class="hud" hidden>–</div>
    <div id="leer" class="leer">
      <strong>Noch kein Modell.</strong>
      <span id="leer-text">Eine IFC-Datei hier ablegen.</span>
    </div>
    <div id="laden" class="laden" hidden><div class="kreisel"></div><span id="laden-text">Lade …</span></div>
    <section id="eigenschaften" hidden>
      <header>
        <h2 id="auswahl-name"></h2>
        <button id="auswahl-zu" type="button" aria-label="Schließen">×</button>
      </header>
      <div id="auswahl-knoepfe"></div>
      <div id="auswahl-inhalt"></div>
    </section>
    <div id="meldung" hidden></div>
  </bim-viewport>`;

export interface ViewerOptionen {
  /** Rueckkanal der Schritt-App: Ereignisse (lage, station, gok, geprueft); ohne = allein (viewer.html). */
  ereignis?: (e: Record<string, unknown>) => void;
  /** Knopf "Lage bearbeiten" in der Werkzeugleiste (allein); in der App schaltet der Schritt "Lage" den Modus. */
  lageKnopf?: boolean;
  /** Text, solange kein Modell und keine Bohrung da ist. */
  leerText?: string;
}

export type ViewerApi = Awaited<ReturnType<typeof viewerStarten>>;

let gestartet = false;

export async function viewerStarten(huelle: HTMLElement, opt: ViewerOptionen = {}) {
  if (gestartet) throw new Error("Es gibt nur einen Viewer je Seite");
  gestartet = true;
  BUI.Manager.init();
  BUIC.Manager.init();
  huelle.classList.add("viewer-rahmen");
  huelle.innerHTML = GERUEST;
  if (opt.leerText) $("leer-text").textContent = opt.leerText;
  if (opt.ereignis) empfaengerSetzen(opt.ereignis);
  const vendor = new URL("vendor/", new URL(import.meta.env.BASE_URL, location.href)).href;

  // Status fuer automatische Pruefungen (scripts/check.mjs, scripts/check_app.mjs)
  const status = {
    geladen: false, ladungen: 0, einheiten: [] as string[], bohrsaeulen: 0, marken: 0, fehler: "", auswahl: "",
    kamera: {} as Record<string, unknown>, lage: {} as Record<string, unknown>,
    ereignisse: protokoll, renders: 0,
    instanz: Math.random().toString(36).slice(2, 8),
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
  viewport.addEventListener("resize", () => groesseGeaendert());
  components.init();
  KAMERA.einrichten(world, raster);

  function groesseGeaendert() {
    world.renderer?.resize();
    world.camera.updateAspect();
    KAMERA.orthoRichten();
    neuZeichnen(4);
  }

  // Zeichnen nach Bedarf (RendererMode.MANUAL), ohne Anlass kein Bild. Die Postproduktion (Umgebungsverdeckung)
  // steuern wir selbst: That Opens Wechsel im MANUAL-Modus (turnOffOnManualMode) zeichnet jedes Bild erst ohne
  // und 50 ms spaeter mit Postproduktion - mit einem Bild je Mausbewegung wechselte das Bild staendig, der Plan
  // flackerte (docs/16 M29). Hier: einfache Bilder nur, solange etwas laeuft (Kamera, Laden, Ziehen), danach ein
  // Bild mit Postproduktion; im Lage-Modus nie (flacher Plan von oben). In Ruhe gleiche Lage = gleiches Bild.
  world.renderer.mode = OBC.RendererMode.MANUAL;
  world.renderer.turnOffOnManualMode = false;
  let bildBudget = 0;
  let schattenGewuenscht = true;                        // Einstellung "Kanten und Schatten"
  let lageAktiv = false;
  let unruhigBis = 0;
  let ruheUhr = 0;
  function neuZeichnen(bilder = 3) {
    bildBudget = Math.max(bildBudget, bilder);
    world.renderer!.needsUpdate = true;
  }
  /** Etwas bewegt sich: bis kurz danach einfache Bilder (fluessig auch bei Trassen), dann eines mit Postproduktion. */
  function unruhig(ms = 150) {
    unruhigBis = Math.max(unruhigBis, performance.now() + ms);
    window.clearTimeout(ruheUhr);
    ruheUhr = window.setTimeout(() => neuZeichnen(1), unruhigBis - performance.now() + 20);
  }
  world.onBeforeUpdate.add(() => {
    const laedt = [...fragments.list.values()].some((m) => m.isBusy);
    if (laedt) unruhig();
    if (bildBudget > 0 || laedt) {
      world.renderer!.needsUpdate = true;
      bildBudget = Math.max(0, bildBudget - 1);
    }
  });
  // Erst unmittelbar vor dem Zeichnen entscheiden: die Kamera bewegt sich im selben Durchlauf nach world.onBeforeUpdate
  world.renderer.onBeforeUpdate.add(() => {
    const soll = schattenGewuenscht && !lageAktiv && performance.now() >= unruhigBis;
    if (postproduction.enabled !== soll) postproduction.enabled = soll;
  });
  world.camera.controls.addEventListener("update", () => {
    unruhig();
    neuZeichnen(2);
  });
  for (const art of ["pointerdown", "pointerup", "wheel", "dblclick", "keydown", "change"]) {
    huelle.addEventListener(art, () => neuZeichnen(6), { passive: true, capture: true });
  }
  // Mausbewegung nur beim Ziehen (Bohrung, Schnittebene); sonst aendert sie das Bild nicht
  huelle.addEventListener("pointermove", (ev) => {
    if (!ev.buttons) return;
    unruhig();
    neuZeichnen(1);
  }, { passive: true, capture: true });

  const { postproduction } = world.renderer;
  postproduction.enabled = true;
  postproduction.style = OBF.PostproductionAspect.COLOR_SHADOWS;
  world.renderer.manualDefaultStyle = postproduction.style;    // kein Stilwechsel je Bild
  verdeckungKamera();

  /** three.js' GTAO kennt die Kameraart nur vom Start (PERSPECTIVE_CAMERA = 1): nach dem Wechsel auf
   *  orthografisch rechnete es die Tiefe mit der Perspektivformel und dem negativen near (kamera.ts) - falsche
   *  Verschattung, je nach Grafikkarte ganz schwarze Bilder (docs/16 M30). */
  function verdeckungKamera() {
    const ao = postproduction.aoPass as unknown as Record<string, THREE.ShaderMaterial | undefined>;
    const perspektivisch = (world.camera.three as THREE.PerspectiveCamera).isPerspectiveCamera ? 1 : 0;
    for (const m of [ao.gtaoMaterial, ao.depthRenderMaterial]) {
      if (m?.defines && m.defines.PERSPECTIVE_CAMERA !== perspektivisch) {
        m.defines.PERSPECTIVE_CAMERA = perspektivisch;
        m.needsUpdate = true;
      }
    }
  }
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
  let nadelnVonApp = false;
  let kameraVorLage: ReturnType<typeof KAMERA.kameraZustand> | null = null;
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
    modusGeaendert: () => leisteNeu(),
  });
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
      if (!nadelnVonApp && modellUrsprung) [rahmen.e0, rahmen.n0] = modellUrsprung;
      if (!nadelnVonApp && m.Lagebezug !== undefined) rahmen.modus = /Reihe|schematisch/i.test(String(m.Lagebezug)) ? "reihe" : "koordinaten";
      if (!bezugGesetzt) {
        modell.object.updateMatrixWorld(true);
        rahmen.bezug = Math.floor(modell.box.min.y);
        bezugGesetzt = true;
      }
      modellPlatzieren();
      nurEinheit = null;
      sichtbar.clear();
      if (!nadelnVonApp) await nadelnAusIfc();
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

  /** Allein: Marken aus den IfcBorehole des Modells (Lage aus der Huelle der Saeule). */
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

  /** Mit der App zeichnet der Editor die Saeulen (verschiebbar); die IFC-Saeulen bleiben dann aus. */
  async function bohrsaeulenSichtbarkeit() {
    if (!modell || !daten?.bohrsaeulen.length) return;
    const zeigen = bohrungenAn && !nadelnVonApp;
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
    if (!projekt || editor.aktiv) return;
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
    editor.waehlenNadel(null);
    $("eigenschaften").hidden = true;
    status.auswahl = "";
  }

  let bohrungenAn = true;
  async function bohrungenUmschalten() {
    bohrungenAn = !bohrungenAn;
    editor.setSichtbar(bohrungenAn && nadelnVonApp);
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
  const REIHENFOLGE = ["CPset_Modelleinheit", "CPset_Bodenansprache", "CPset_Schichtenverzeichnis", "CPset_Herkunft"];

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
    editor.waehlenNadel(null);
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
    editor.waehlenNadel(id);
    const n = id ? editor.nadeln.get(id)?.daten : undefined;
    if (!n) {
      $("eigenschaften").hidden = true;
      return;
    }
    const lage = n.x === null ? "ohne Lage" :
      rahmen.modus === "reihe" ? `Station ${formatiere(n.x)} m` : `R ${formatiere(n.x)} · H ${formatiere(n.y)}`;
    const kopf: Record<string, unknown> = {
      Lage: lage, Lage_aus: n.quelle || "–",
      GOK: n.gok_bekannt ? `${formatiere(n.gok)} m NHN${n.gok_pdf ? " (PDF)" : ""}` : "unbekannt (relativ 0 m)",
      Endteufe: `${formatiere(n.ende)} m`,
      Schichten_geprueft: `${n.schichten_geprueft}/${n.schichten_n}`,
      Nicht_klassifiziert: n.unklassifiziert ?? "–",
      Durchmesser: n.durchmesser ? `${formatiere(n.durchmesser)} m` : "",
      Im_Modell: n.im_modell ? "ja" : `nein${n.grund ? ` (${n.grund})` : ""}`,
      Geprueft: n.geprueft,
    };
    const schichten = n.schichten.map(([o, u, f, art]) =>
      `<tr><td><span class="farbe" style="background:${/^#[0-9a-f]{6}$/i.test(String(f)) ? f : "#ccc"}"></span>` +
      `${formatiere(o)}–${formatiere(u)} m</td><td>${esc(String(art ?? ""))}</td></tr>`).join("");
    let html = tabelle(kopf) + (schichten ? `<h3>Schichten</h3><table>${schichten}</table>` : "");
    const lid = modell ? bohrungNachCode.get(n.code) : undefined;
    if (modell && lid !== undefined) html += psetsHtml((await eigenschaften(modell, lid)).psets);
    const knoepfe: HTMLElement[] = [];
    if (mitApp()) {
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
    huelle.classList.toggle(schmal ? "seite-auf" : "zu");
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
          ${mitApp() ? "" : BUI.html`
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
          ${nadeln.length ? BUI.html`<ul class="liste bohrliste">${nadeln.map((n) => {
            const offen = (n.offen ?? 0) > 0 && !n.geprueft;
            return BUI.html`
            <li class=${n.id === editor.ausgewaehlt ? "aktiv" : ""} @click=${() => { void nadelWaehlen(n.id); void fokus(); }}>
              <span class=${`zustand ${n.geprueft ? "ok" : offen ? "warn" : ""} ${n.im_modell ? "" : "raus"}`}>
                ${n.geprueft ? "✓" : n.x === null ? "◌" : offen ? "!" : "•"}</span>
              <span class="name">${n.code}</span>
              <span class="wert">${n.schichten_geprueft}/${n.schichten_n}</span>
            </li>`;
          })}</ul>
            <p class="text leise">✓ geprüft · ! Schicht nicht klassifiziert · ◌ ohne Lage · grau: nicht im Modell</p>`
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

  // ------------------------------------------------------------------ Werkzeugleiste unten: nur Icons, Name im Tooltip
  // Gruppen als div, nicht bim-toolbar-section: die Section setzt label-hidden ihrer Knoepfe beim Einhaengen zurueck.
  const lageKnopf = opt.lageKnopf ?? !opt.ereignis;
  const knopf = (label: string, icon: string, klick: () => unknown, titel: string, text = "", aktiv = false, aus = false) => BUI.html`
    <bim-button label-hidden label=${label} icon=${icon} ?active=${aktiv} ?disabled=${aus} @click=${klick}>${tipp(titel, text)}</bim-button>`;
  const [leiste, leisteAktualisieren] = BUI.Component.create<BUI.Toolbar, Record<string, never>>((_zustand) => BUI.html`
    <bim-toolbar class="kompakt">
      <div class="leisten-gruppe" role="group" aria-label="Ansicht">
        ${knopf("Iso", "mdi:axis-arrow", () => KAMERA.ansicht("iso"), "Isometrisch", "Schräg von Südosten auf die ganze Szene.")}
        ${knopf("Oben", "mdi:arrow-down-bold-box-outline", () => KAMERA.ansicht("oben"), "Draufsicht")}
        ${knopf("Süd", "mdi:arrow-up-bold-box-outline", () => KAMERA.ansicht("sued"), "Ansicht von Süden", "Längsschnitt; weitere Seiten über den Würfel oben rechts.")}
        <bim-button label-hidden label="Überhöhung" icon="mdi:arrow-expand-vertical" class="faktor">
          <span class="faktor-text">${rahmen.faktor}×</span>
          ${tipp("Überhöhung", "Höhen mal Faktor, damit dünne Schichten sichtbar werden. Koordinaten bleiben echt.")}
          <bim-context-menu>
            ${FAKTOREN.map((f) => BUI.html`<bim-button label=${`${f}×`} ?active=${rahmen.faktor === f} @click=${() => ueberhoehen(f)}></bim-button>`)}
          </bim-context-menu>
        </bim-button>
      </div>
      <div class="leisten-gruppe" role="group" aria-label="Sichtbarkeit">
        ${knopf("Alle anzeigen", "mdi:eye", () => alleZeigen(), "Alle einblenden", "Alle ausgeblendeten Elemente wieder einblenden.")}
        ${knopf("Transparenz", "mdi:ghost", () => durchscheinen(!durchscheinend), "Transparenz", "Einheiten durchscheinend: Bohrungen und Auswahl im Inneren sichtbar.", durchscheinend)}
        ${knopf("Bohrungen", "mdi:map-marker-radius", () => bohrungenUmschalten(), "Bohrungen ein/aus", "", bohrungenAn)}
      </div>
      <div class="leisten-gruppe" role="group" aria-label="Auswahl">
        ${knopf("Fokus", "mdi:fit-to-screen-outline", () => fokus(), "Fokus", "Kamera auf die Auswahl; ohne Auswahl die ganze Szene.")}
        ${knopf("Ausblenden", "mdi:eye-off", () => auswahlAusblenden(false), "Auswahl ausblenden")}
        ${knopf("Isolieren", "mdi:selection-ellipse", () => auswahlAusblenden(true), "Auswahl isolieren", "Alle anderen Elemente ausblenden.")}
        <bim-button label-hidden label="Einfärben" icon="mdi:format-color-fill">${tipp("Auswahl einfärben")}
          <bim-context-menu>
            <div class="einfaerben">
              <input type="color" .value=${farbeEingabe} @input=${(e: Event) => (farbeEingabe = (e.target as HTMLInputElement).value)}>
              <bim-button label="Anwenden" @click=${() => einfaerben()}></bim-button>
            </div>
          </bim-context-menu>
        </bim-button>
      </div>
      <div class="leisten-gruppe" role="group" aria-label="Schnitt">
        ${knopf("O–W", "mdi:arrow-split-horizontal", () => schnitt(new THREE.Vector3(0, 0, -1)), "Schnitt Ost–West", "Senkrechter Schnitt durch die Szenenmitte.")}
        ${knopf("N–S", "mdi:arrow-split-vertical", () => schnitt(new THREE.Vector3(1, 0, 0)), "Schnitt Nord–Süd", "Senkrechter Schnitt durch die Szenenmitte.")}
        ${knopf("Ebene", "mdi:vector-square", () => { schnittWerkzeug = !schnittWerkzeug; leisteNeu(); }, "Schnittebene per Doppelklick", "Doppelklick auf eine Fläche legt dort eine Ebene. Entf löscht die Ebene unter der Maus.", schnittWerkzeug)}
        ${knopf("Löschen", "mdi:delete-outline", () => clipper.deleteAll(), "Alle Schnitte löschen")}
      </div>
      ${lageKnopf ? BUI.html`
        <div class="leisten-gruppe" role="group" aria-label="Lage">
          ${knopf("Lage bearbeiten", "mdi:cursor-move", () => lageModus(!editor.aktiv), "Bohrungen setzen", "Bohrungen auf dem Lageplan oder entlang der Reihe ziehen.", editor.aktiv, !editor.nadeln.size)}
        </div>` : ""}
    </bim-toolbar>`, {});
  $("leiste").append(leiste);
  function leisteNeu() {
    leisteAktualisieren();
  }

  // ------------------------------------------------------------------ Oben rechts: Koordinaten, Zahnrad (mit Hilfe), ViewCube
  let koordinatenAn = false;
  const hilfeText = (text: string) => BUI.html`<p class="text leise einstellung-hilfe">${text}</p>`;
  const [einstellungen, einstellungenNeu] = BUI.Component.create<HTMLDivElement, Record<string, never>>((_zustand) => BUI.html`
    <div class="oben-rechts">
      <bim-button class="koord" label-hidden label="Koordinaten" icon="mdi:crosshairs-gps" ?active=${koordinatenAn}
        @click=${(e: Event) => { koordinatenAn = !koordinatenAn; (e.target as BUI.Button).active = koordinatenAn; $("hud").hidden = !koordinatenAn; }}>${tipp("Koordinaten anzeigen", "Rechts-/Hochwert und Höhe NHN unter der Maus (Reihe: Station).")}</bim-button>
      <bim-button class="zahnrad" label-hidden label="Einstellungen" icon="mdi:cog">${tipp("Einstellungen")}
        <bim-context-menu class="einstellungen">
          <bim-checkbox label="Raster" ?checked=${raster.visible} @change=${(e: Event) => { raster.visible = (e.target as BUI.Checkbox).checked; }}></bim-checkbox>
          ${hilfeText("Bodenraster unter der Szene; die Maschenweite wächst mit dem Modell (1 m bis 100 m).")}
          <bim-checkbox label="Orbit um Mauspunkt" ?checked=${world.dynamicAnchor}
            @change=${(e: Event) => { world.dynamicAnchor = (e.target as BUI.Checkbox).checked; }}></bim-checkbox>
          ${hilfeText("Drehen um den Punkt unter der Maus statt um die Bildmitte. Doppelklick legt den Drehpunkt fest.")}
          <bim-checkbox label="Kanten und Schatten" ?checked=${schattenGewuenscht}
            @change=${(e: Event) => { schattenGewuenscht = (e.target as BUI.Checkbox).checked; neuZeichnen(2); }}></bim-checkbox>
          ${hilfeText("Umgebungsverdeckung in Ruhe; während der Bewegung und beim Setzen der Lage aus (flüssig, kein Flackern).")}
          <bim-dropdown label="Kameraprojektion" .value=${[world.camera.projection.current]} @change=${async (e: Event) => {
            const [p] = (e.target as BUI.Dropdown).value as string[];
            if (p) await world.camera.projection.set(p as OBC.CameraProjection);
          }}>
            <bim-option label="Perspektivisch" .value=${"Perspective"} ?checked=${world.camera.projection.current === "Perspective"}></bim-option>
            <bim-option label="Orthografisch" .value=${"Orthographic"} ?checked=${world.camera.projection.current === "Orthographic"}></bim-option>
          </bim-dropdown>
          ${hilfeText("Orthografisch: maßstäblich ohne Fluchtpunkt (Schnitte, Draufsicht); perspektivisch: räumlicher Eindruck.")}
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
    verdeckungKamera();
    KAMERA.orthoRichten();
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
    KAMERA.strahl(strahl, ndc);
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
  /** links: Pixel, die ein Panel der App links ueber dem Viewer abdeckt (Ansichten zentrieren daneben). */
  async function lageModus(an: boolean, links = 0) {
    if (an === editor.aktiv) {
      KAMERA.linksFrei(an ? links : 0);
      return;
    }
    if (an) {
      kameraVorLage = KAMERA.kameraZustand();
      await auswahlAufheben();
    }
    highlighter.enabled = !an;
    lageAktiv = an;                                      // Plan ohne Postproduktion (kein Flackern)
    await editor.umschalten(an);
    KAMERA.linksFrei(an ? links : 0);
    editor.setSichtbar(bohrungenAn && (nadelnVonApp || an));
    if (modell) modell.object.visible = !an;
    KAMERA.szeneAktualisieren();
    if (an) {
      await world.camera.projection.set("Orthographic");
      await KAMERA.ansicht(rahmen.modus === "reihe" ? "sued" : "oben");
      world.camera.set("Plan");                          // linke Taste verschiebt, kein Drehen: die Draufsicht bleibt
    } else {
      world.camera.set("Orbit");
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
    if (!huelle.offsetParent) return;                                // Viewer gerade nicht sichtbar
    if (ev.code === "Delete" && editor.loeschen()) return;          // Lage-Modus: Punkt bzw. gesetzte Lage
    if (ev.code === "Delete" || ev.code === "Backspace") clipper.delete(world);
    if (ev.key === "Escape") {
      if (editor.escape()) return;
      if (editor.aktiv && lageKnopf) await lageModus(false);
      else await auswahlAufheben();
    }
  });

  // Ablegen einer IFC-Datei (allein)
  if (!opt.ereignis) {
    huelle.addEventListener("dragover", (ev) => {
      if (!ev.dataTransfer?.types.includes("Files")) return;
      ev.preventDefault();
      huelle.classList.add("ziehen");
    });
    huelle.addEventListener("dragleave", () => huelle.classList.remove("ziehen"));
    huelle.addEventListener("drop", async (ev) => {
      ev.preventDefault();
      huelle.classList.remove("ziehen");
      const f = ev.dataTransfer?.files?.[0];
      if (f) await laden(new Uint8Array(await f.arrayBuffer()), f.name, false);
    });
  }

  // ------------------------------------------------------------------ Stand von aussen (App oder Pruefung)
  // Mehrere Staende koennen waehrend des Ladens kommen: immer nur den neuesten verarbeiten.
  let wartend: Args | null = null;
  let laeuft = false;
  let letzte: Args = {};

  async function setzen(a: Args) {
    wartend = a;
    if (laeuft) return;
    laeuft = true;
    try {
      while (wartend) {
        const naechste = wartend;
        wartend = null;
        await anwenden(naechste);
      }
    } catch (err) {
      status.fehler = String(err);
    } finally {
      laeuft = false;
    }
  }

  async function anwenden(a: Args) {
    status.renders += 1;
    const neu = (a.projekt ?? "") !== projekt;
    if (neu) {
      projekt = a.projekt ?? "";
      projektSetzen(projekt);
      bezugGesetzt = false;
    }
    nadelnVonApp = Array.isArray(a.bohrungen);
    rahmen.modus = a.modus ?? "koordinaten";
    rahmen.epsg = a.epsg ?? null;
    if (a.ursprung && !neu && (a.ursprung[0] !== rahmen.e0 || a.ursprung[1] !== rahmen.n0)) {
      // Nullpunkt verschoben (erste Bohrung gesetzt, Plan kalibriert): alles bekommt neue Szenenkoordinaten -
      // die Kamera geht mit, sonst schaut sie ins Leere und Plan und Bohrungen sind weg.
      const [dx, dz] = [rahmen.e0 - a.ursprung[0], a.ursprung[1] - rahmen.n0];
      await KAMERA.verschieben(dx, dz);
      for (const v of kameraVorLage ? [kameraVorLage.pos, kameraVorLage.ziel] : []) {
        v[0] += dx;                                      // gemerkte Modellansicht ebenso
        v[2] += dz;
      }
    }
    if (a.ursprung) [rahmen.e0, rahmen.n0] = a.ursprung;
    if (a.ueberhoehung && a.ueberhoehung !== letzte.ueberhoehung) rahmen.faktor = Number(a.ueberhoehung);
    const nadeln = a.bohrungen ?? [];
    if (!bezugGesetzt && nadeln.length) {
      rahmen.bezug = Math.floor(Math.min(...nadeln.map((n) => n.gok - n.ende)));
      bezugGesetzt = true;
    }
    editor.markenZeigen = bohrungenAn;
    editor.setzen(nadeln, a.unterlage ?? null, a.punkte ?? []);
    editor.setSichtbar(bohrungenAn && nadelnVonApp);
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
    letzte = a;
    seitenleisteNeu();
    leisteNeu();
    if (editor.ausgewaehlt) void nadelWaehlen(editor.ausgewaehlt);
    status.kamera = kameraInfo();
    neuZeichnen(10);
  }

  const api = {
    world, editor, rahmen, KAMERA, status, ausSzene, hoeheAusSzene,
    setzen, lageModus, ueberhoehen, fokus, meldung, groesseGeaendert, nadelWaehlen,
    ansicht: KAMERA.ansicht,
    modell: () => modell,
    /** Einstellung "Kanten und Schatten" (Pruefungen schalten sie fuer SwiftShader ab). */
    schatten(an: boolean) {
      schattenGewuenscht = an;
      einstellungenNeu();
      neuZeichnen(2);
    },
    /** Seitenleiste (Einheiten, Bohrungen) ein oder aus. */
    seitenleiste(an: boolean) {
      huelle.classList.toggle("zu", !an);
    },
    argsVerarbeiten: setzen,                               // Name der Pruefungen (check.mjs)
  };
  (window as unknown as { viewer: typeof api }).viewer = api;
  leisteNeu();
  return api;
}
