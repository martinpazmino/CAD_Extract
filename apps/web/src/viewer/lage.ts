// Lage-Editor: jede Bohrung als Stecknadel (Saeule aus den Schichten + ziehbare Marke), dazu eine
// PDF-Unterlage als Bild in der Szene - Lageplan (Draufsicht) oder Laengsschnitt (Seitenansicht).
// Kalibrierung (docs/21 §4): Massstab aus einer gemessenen Strecke (zwei Bildpunkte + wahre Laenge) oder 1:n,
// ein Bezugspunkt im Bild mit seiner Koordinate, beim Lageplan die Drehung, beim Schnitt der Hoehenmassstab.
// Ist der Plan gesperrt, werden die Bohrungen gezogen: auf dem Plan nur in x/y, im Schnitt entlang der
// Station und in der Hoehe nur, wenn das PDF keine GOK hat. Jede Aenderung geht als Ereignis an die App.
import * as THREE from "three";
import * as OBC from "@thatopen/components";
import { ausSzene, hoeheZuSzene, rahmen, zuSzene } from "./rahmen";
import { ereignis, mitApp, type Kalibrierung, type Massstab, type Nadel, type Unterlage } from "./kanal";
import { huelleMelden, szeneAktualisieren } from "./kamera";

type Welt = OBC.SimpleWorld<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.BaseRenderer>;
type Abbildung = (u: number, v: number) => [number, number];
export interface Bildpunkt { u: number; v: number }

interface Stecknadel {
  daten: Nadel;
  saeule: THREE.Group;
  marke: HTMLDivElement;
  oben: THREE.Vector3 | null;           // Szenenpunkt der GOK; null = ohne Lage
}

export interface LageRueckrufe {
  auswahl: (id: string | null) => void;
  meldung: (text: string, dauer?: number) => void;
  neuZeichnen: () => void;
  modusGeaendert: (aktiv: boolean) => void;
}

export interface Hilfsmarken {
  strecke?: (Bildpunkt | null)[];       // gemessene Strecke (Massstab)
  hoehe?: (Bildpunkt | null)[];         // Schnitt: gemessene Hoehe
  bezug?: Bildpunkt | null;             // Bezugspunkt
}

const esc = (t: string) => t.replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" })[c]!);
const zahlText = (v: number, stellen = 2) =>
  v.toLocaleString("de-DE", { minimumFractionDigits: stellen, maximumFractionDigits: stellen });

// ------------------------------------------------------------------ Kalibrierung (rein rechnerisch, geprueft in check.mjs)
/** Massstab in m je Bildpixel: aus der Strecke oder aus 1:n und dem Papiermass des Bilds (mm je Pixel). */
export function meterJePixel(m: Massstab, mmProPx: number) {
  if ("n" in m) return (m.n * mmProPx) / 1000;
  return m.meter / (Math.hypot(m.u2 - m.u1, m.v2 - m.v1) || 1);
}

/** Massstabszahl n (1:n) einer Kalibrierung. */
export function massstabszahl(m: Massstab, mmProPx: number) {
  return meterJePixel(m, mmProPx) / (mmProPx / 1000);
}

/** Bild -> Welt fuer die Unterlage; gleiche Formel wie ui/projekt.bild_zu_welt. mitte/oben nur unkalibriert. */
export function abbildung(u: Unterlage, mitte: [number, number], oben = 0, k: Kalibrierung | null = u.kalibrierung): Abbildung {
  if (k?.massstab && k.bezug) {
    const s = meterJePixel(k.massstab, u.mm_pro_px);
    const b = k.bezug;
    if (u.art === "plan") {
      const t = -THREE.MathUtils.degToRad(k.drehung ?? 0);       // Plan gegen Gitternord gedreht: Welt dreht zurueck
      const c = Math.cos(t);
      const sn = Math.sin(t);
      return (uu, vv) => {
        const a = (uu - b.u) * s;
        const d = -(vv - b.v) * s;
        return [b.x + a * c - d * sn, b.y + a * sn + d * c];
      };
    }
    const sh = k.hoehe ? meterJePixel(k.hoehe, u.mm_pro_px) : s;
    return (uu, vv) => [b.x + (uu - b.u) * s, b.y - (vv - b.v) * sh];
  }
  const m = u.mm_pro_px;                                // m je Pixel bei 1:1000
  if (u.art === "plan") return (uu, vv) => [mitte[0] + (uu - u.breite / 2) * m, mitte[1] - (vv - u.hoehe / 2) * m];
  return (uu, vv) => [mitte[0] + (uu - u.breite / 2) * m, oben - (vv * m) / 10];
}

/** Massstab, Drehung bzw. Ueberhoehung einer Kalibrierung als Text. */
export function kalibrierungText(u: Unterlage, k: Kalibrierung | null = u.kalibrierung): string {
  if (!k?.massstab || !k.bezug) return "nicht kalibriert";
  const n = Math.round(massstabszahl(k.massstab, u.mm_pro_px)).toLocaleString("de-DE");
  if (u.art === "plan") return `1:${n} · Drehung ${zahlText(k.drehung ?? 0, 1)}°`;
  const h = k.hoehe ? massstabszahl(k.hoehe, u.mm_pro_px) : massstabszahl(k.massstab, u.mm_pro_px);
  const ueber = massstabszahl(k.massstab, u.mm_pro_px) / h;
  return `Länge 1:${n} · Höhe 1:${Math.round(h).toLocaleString("de-DE")} (Überhöhung ${zahlText(ueber, 1)}×)`;
}

// ------------------------------------------------------------------ Editor
export class LageEditor {
  readonly gruppe = new THREE.Group();
  aktiv = false;
  sichtbar = true;                                      // Saeulen der Bohrungen zeigen
  markenZeigen = true;                                  // Marken (Code, Zustand) zeigen
  unterlageImModell = false;
  deckkraft = 0.85;
  readonly nadeln = new Map<string, Stecknadel>();
  ausgewaehlt: string | null = null;

  private readonly ebene = document.createElement("div");
  private readonly linien = document.createElementNS("http://www.w3.org/2000/svg", "svg");
  private readonly materialien = new Map<string, THREE.MeshLambertMaterial>();
  private radiusAuto = 0.5;
  private unterlage: Unterlage | null = null;
  private entwurf: Kalibrierung | null | undefined = undefined;   // Vorschau einer noch nicht uebernommenen Kalibrierung
  private bild: THREE.Mesh<THREE.BufferGeometry, THREE.MeshBasicMaterial> | null = null;
  private texturUrl = "";
  private abb: Abbildung | null = null;
  private hilfe: Hilfsmarken = {};
  private hilfeMarken: HTMLDivElement[] = [];
  private waehlen: ((p: Bildpunkt | null) => void) | null = null;
  private schnittTiefe = 2;
  private ziehen: { id: string; versatz: THREE.Vector3; ebene: THREE.Plane; start: [number, number]; bewegt: boolean;
                    neu: boolean; hoehe: boolean } | null = null;
  private readonly caster = new THREE.Raycaster();

  constructor(private readonly welt: Welt, huelle: HTMLElement, private readonly r: LageRueckrufe) {
    this.gruppe.name = "Bohrungen (Lage)";
    welt.scene.three.add(this.gruppe);
    this.ebene.className = "marken";
    this.linien.classList.add("hilfslinien");
    this.ebene.append(this.linien);
    huelle.append(this.ebene);
    huelleMelden(() => this.kiste());
    welt.renderer!.onAfterUpdate.add(() => this.markenSetzen());
    const flaeche = welt.renderer!.three.domElement;
    flaeche.addEventListener("click", (ev) => this.bildKlick(ev));
    window.addEventListener("pointermove", (ev) => this.ziehenBewegen(ev));
    window.addEventListener("pointerup", (ev) => this.ziehenEnde(ev));
  }

  // ---------------------------------------------------------------- Daten
  setzen(nadeln: Nadel[], unterlage: Unterlage | null) {
    const alt = new Set(this.nadeln.keys());
    this.radiusAuto = THREE.MathUtils.clamp(this.ausdehnung(nadeln) / 600, 0.4, 6);
    for (const n of nadeln) {
      alt.delete(n.id);
      let s = this.nadeln.get(n.id);
      if (!s) {
        s = { daten: n, saeule: new THREE.Group(), marke: this.markeBauen(n.id), oben: null };
        this.gruppe.add(s.saeule);
        this.nadeln.set(n.id, s);
      }
      s.daten = n;
      if (this.ziehen?.id !== n.id) this.lageAus(s);
      this.saeuleBauen(s);
      this.markeBeschriften(s);
    }
    for (const id of alt) this.entfernen(id);
    if (unterlage?.url !== this.unterlage?.url || JSON.stringify(unterlage?.kalibrierung) !== JSON.stringify(this.unterlage?.kalibrierung)) {
      this.entwurf = undefined;                         // gespeicherter Stand gilt
    }
    this.unterlageSetzen(unterlage);
    szeneAktualisieren();
    this.r.neuZeichnen();
  }

  private ausdehnung(nadeln: Nadel[]) {
    const xs = nadeln.filter((n) => n.x !== null).map((n) => n.x!);
    const ys = nadeln.filter((n) => n.y !== null).map((n) => n.y!);
    if (!xs.length) return 50;
    return Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys), 20);
  }

  private radius(n: Nadel) {
    return n.durchmesser && n.durchmesser > 0 ? n.durchmesser / 2 : this.radiusAuto;
  }

  private lageAus(s: Stecknadel) {
    const n = s.daten;
    s.oben = n.x === null || n.y === null ? null : zuSzene(n.x, n.y, n.gok);
  }

  private entfernen(id: string) {
    const s = this.nadeln.get(id);
    if (!s) return;
    s.saeule.removeFromParent();
    for (const m of s.saeule.children as THREE.Mesh[]) m.geometry.dispose();
    s.marke.remove();
    this.nadeln.delete(id);
  }

  /** Ueberhoehung geaendert: Saeulen und Unterlage neu. */
  neuAufbauen() {
    for (const s of this.nadeln.values()) {
      this.lageAus(s);
      this.saeuleBauen(s);
    }
    this.bildGeometrie();
    szeneAktualisieren();
  }

  private material(farbe: string, blass: boolean) {
    const schluessel = `${farbe}|${blass}`;
    let m = this.materialien.get(schluessel);
    if (!m) {
      m = new THREE.MeshLambertMaterial({ color: new THREE.Color(farbe), transparent: blass, opacity: blass ? 0.35 : 1 });
      this.materialien.set(schluessel, m);
    }
    return m;
  }

  private saeuleBauen(s: Stecknadel) {
    for (const m of s.saeule.children as THREE.Mesh[]) m.geometry.dispose();
    s.saeule.clear();
    s.saeule.visible = s.oben !== null && this.sichtbar;
    if (!s.oben) return;
    const blass = !s.daten.im_modell;
    const r = this.radius(s.daten);
    const schichten = s.daten.schichten.length ? s.daten.schichten : [[0, s.daten.ende || 1, "#9aa0a6"]];
    for (const [oben, unten, farbe] of schichten) {
      const h = (Number(unten) - Number(oben)) * rahmen.faktor;
      if (!(h > 0)) continue;
      const m = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, 16), this.material(String(farbe), blass));
      m.position.y = -Number(oben) * rahmen.faktor - h / 2;
      m.userData.nadel = s.daten.id;
      s.saeule.add(m);
    }
    s.saeule.position.copy(s.oben);
  }

  kiste(): THREE.Box3 | null {
    const b = new THREE.Box3();
    let rmax = 0;
    for (const s of this.nadeln.values()) {
      if (!s.oben) continue;
      b.expandByPoint(s.oben);
      b.expandByPoint(new THREE.Vector3(s.oben.x, s.oben.y - (s.daten.ende || 1) * rahmen.faktor, s.oben.z));
      rmax = Math.max(rmax, this.radius(s.daten));
    }
    if (this.bild?.visible) {
      this.bild.geometry.computeBoundingBox();
      b.union(this.bild.geometry.boundingBox!);
    }
    if (!b.isEmpty()) b.expandByScalar(rmax * 2);
    return b.isEmpty() ? null : b;
  }

  // ---------------------------------------------------------------- Marken (DOM, konstante Groesse)
  private markeBauen(id: string) {
    const el = document.createElement("div");
    el.className = "nadel";
    el.dataset.id = id;
    el.innerHTML = `<i></i><span></span>`;
    el.addEventListener("pointerdown", (ev) => this.ziehenStart(ev, id, false));
    this.ebene.append(el);
    return el;
  }

  private markeBeschriften(s: Stecknadel) {
    const n = s.daten;
    const offen = (n.offen ?? 0) > 0 && !n.geprueft;
    s.marke.querySelector("span")!.textContent = n.code;
    s.marke.classList.toggle("geprueft", n.geprueft);
    s.marke.classList.toggle("offen", offen);
    s.marke.classList.toggle("raus", !n.im_modell);
    s.marke.classList.toggle("gewaehlt", this.ausgewaehlt === n.id);
    const zeilen = [n.code, n.quelle ? `Lage: ${n.quelle}` : "ohne Lage",
                    `GOK ${n.gok_bekannt ? `${zahlText(n.gok)} m NHN` : "unbekannt (relativ)"}${n.gok_pdf ? " (PDF)" : ""} · Endteufe ${zahlText(n.ende)} m`,
                    `Schichten geprüft ${n.schichten_geprueft}/${n.schichten_n}` +
                    (n.unklassifiziert ? ` · ${n.unklassifiziert} nicht klassifiziert` : "")];
    if (!n.im_modell) zeilen.push(`nicht im Modell${n.grund ? `: ${n.grund}` : ""}`);
    if (this.aktiv) zeilen.push(this.ziehHinweis(n));
    s.marke.title = zeilen.join("\n");
  }

  private ziehHinweis(n: Nadel) {
    if (!this.ziehenErlaubt()) return "Erst die Unterlage kalibrieren und sperren, dann ziehen";
    if (rahmen.modus === "reihe") return n.gok_pdf ? "Ziehen: Station (GOK aus dem PDF bleibt)" : "Ziehen: Station und GOK";
    return "Ziehen: Lage (Rechts-/Hochwert)";
  }

  waehlenNadel(id: string | null) {
    this.ausgewaehlt = id;
    for (const s of this.nadeln.values()) s.marke.classList.toggle("gewaehlt", s.daten.id === id);
  }

  private readonly punkt = new THREE.Vector3();
  private markenSetzen() {
    const { clientWidth: w, clientHeight: h } = this.ebene;
    const kam = this.welt.camera.three;
    const belegt = new Set<string>();
    const zelle = 46;
    for (const s of this.nadeln.values()) {
      const p = s.oben;
      if (!p || !this.markenZeigen) {
        s.marke.hidden = true;
        continue;
      }
      this.punkt.copy(p).project(kam);
      const drin = this.punkt.z < 1 && this.punkt.z > -1.5 && Math.abs(this.punkt.x) <= 1.05 && Math.abs(this.punkt.y) <= 1.05;
      s.marke.hidden = !drin;
      if (!drin) continue;
      const x = ((this.punkt.x + 1) / 2) * w;
      const y = ((1 - this.punkt.y) / 2) * h;
      s.marke.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
      // Beschriftung nur, wo noch Platz ist (dichte Bohrreihen auf Kilometern)
      const k = `${Math.floor(x / zelle)}:${Math.floor(y / (zelle / 2))}`;
      const frei = !belegt.has(k) || s.daten.id === this.ausgewaehlt || s.daten.id === this.ziehen?.id;
      belegt.add(k);
      s.marke.classList.toggle("ohne-text", !frei);
    }
    this.hilfeSetzen(w, h);
  }

  // ---------------------------------------------------------------- Ziehen
  /** Ohne Unterlage frei; mit Unterlage erst, wenn sie kalibriert und gesperrt ist (der Plan bewegt sich nicht mehr). */
  ziehenErlaubt() {
    return !this.unterlage || !!this.unterlage.kalibrierung?.gesperrt;
  }

  private ndc(ev: { clientX: number; clientY: number }) {
    const r = this.welt.renderer!.three.domElement.getBoundingClientRect();
    return new THREE.Vector2(((ev.clientX - r.left) / r.width) * 2 - 1, -((ev.clientY - r.top) / r.height) * 2 + 1);
  }

  private schnittpunkt(ev: { clientX: number; clientY: number }, ebene: THREE.Plane) {
    this.caster.setFromCamera(this.ndc(ev), this.welt.camera.three);
    return this.caster.ray.intersectPlane(ebene, new THREE.Vector3());
  }

  private ziehEbene(oben: THREE.Vector3) {
    // Reihe: senkrechte Ebene durch die Achse (z = 0); Lageplan: waagerecht in Hoehe der GOK
    return rahmen.modus === "reihe"
      ? new THREE.Plane(new THREE.Vector3(0, 0, 1), -oben.z)
      : new THREE.Plane(new THREE.Vector3(0, 1, 0), -oben.y);
  }

  /** Start: Marke in der Szene (neu = false) oder Bohrung ohne Lage aus der Liste der App (neu = true). */
  ziehenStart(ev: PointerEvent, id: string, neu: boolean) {
    if (ev.button !== 0 || this.waehlen) return;
    const s = this.nadeln.get(id);
    if (!s) return;
    ev.preventDefault();
    ev.stopPropagation();
    if (!this.aktiv || (!s.oben && !neu) || !this.ziehenErlaubt()) {
      this.ziehen = { id, versatz: new THREE.Vector3(), ebene: new THREE.Plane(), start: [ev.clientX, ev.clientY],
                      bewegt: false, neu: false, hoehe: false };
      if (this.aktiv && !this.ziehenErlaubt()) this.r.meldung("Erst die Unterlage kalibrieren und sperren (Schloss), dann Bohrungen ziehen.", 5000);
      return;                                            // nur Klick (Auswahl)
    }
    const oben = s.oben ?? this.startpunkt(s.daten);
    const ebene = this.ziehEbene(oben);
    const treffer = neu ? oben.clone() : this.schnittpunkt(ev, ebene);
    this.ziehen = { id, versatz: treffer ? oben.clone().sub(treffer) : new THREE.Vector3(), ebene,
                    start: [ev.clientX, ev.clientY], bewegt: false, neu,
                    hoehe: rahmen.modus === "reihe" && !s.daten.gok_pdf };
    this.welt.camera.controls.enabled = false;
    document.body.classList.add("zieht");
  }

  /** Bohrung ohne Lage: Hoehe der GOK, Lage ergibt sich aus der Maus. */
  private startpunkt(n: Nadel) {
    const ziel = this.welt.camera.controls.getTarget(new THREE.Vector3());
    return new THREE.Vector3(ziel.x, hoeheZuSzene(n.gok), rahmen.modus === "reihe" ? 0 : ziel.z);
  }

  private ziehenBewegen(ev: PointerEvent) {
    const z = this.ziehen;
    if (!z) return;
    const weg = Math.hypot(ev.clientX - z.start[0], ev.clientY - z.start[1]);
    if (!z.bewegt && weg < 4) return;
    z.bewegt = true;
    const s = this.nadeln.get(z.id);
    if (!s || !this.aktiv || !this.ziehenErlaubt()) return;
    const p = this.schnittpunkt(ev, z.ebene);
    if (!p) return;
    p.add(z.versatz);
    const alt = s.oben ?? this.startpunkt(s.daten);
    if (rahmen.modus === "reihe") {
      p.z = alt.z;
      if (!z.hoehe) p.y = alt.y;                         // GOK aus dem PDF: nur entlang der Station
    } else {
      p.y = alt.y;                                       // Lageplan: nur x/y
    }
    s.oben = p;
    s.saeule.visible = this.sichtbar;
    if (!s.saeule.children.length) this.saeuleBauen(s);
    s.saeule.position.copy(p);
    this.r.meldung(`${s.daten.code}: ${this.lageText(p)}`, 1500);
  }

  private ziehenEnde(ev: PointerEvent) {
    const z = this.ziehen;
    if (!z) return;
    this.ziehen = null;
    this.welt.camera.controls.enabled = true;
    document.body.classList.remove("zieht");
    const s = this.nadeln.get(z.id);
    if (!s) return;
    if (!z.bewegt) {
      if (!z.neu) this.r.auswahl(z.id);
      return;
    }
    if (!this.aktiv || !s.oben || !this.ziehenErlaubt()) return;
    if (z.neu && !this.ueberSzene(ev)) {             // ausserhalb losgelassen: bleibt ohne Lage
      s.oben = null;
      this.saeuleBauen(s);
      return;
    }
    const { e, n, h } = ausSzene(s.oben);
    const runden = (v: number) => Math.round(v * 100) / 100;
    const reihe = rahmen.modus === "reihe";
    if (reihe) {
      ereignis({ typ: "station", id: z.id, station: runden(e) });
      if (z.hoehe && Math.abs(h - s.daten.gok) > 0.005) ereignis({ typ: "gok", id: z.id, gok: runden(h) });
    } else {
      ereignis({ typ: "lage", id: z.id, x: runden(e), y: runden(n) });
    }
    s.daten = { ...s.daten, x: runden(e), y: reihe ? 0 : runden(n), gok: reihe && z.hoehe ? runden(h) : s.daten.gok,
                quelle: reihe ? "Reihe (Station im Schnitt gesetzt)" : this.unterlage?.kalibrierung ? "Plan (kalibriert)" : "manuell (Viewer)" };
    this.markeBeschriften(s);
    szeneAktualisieren();
    this.r.meldung(`${s.daten.code} gesetzt: ${this.lageText(s.oben)}${mitApp() ? " – Modell wird angepasst …" : ""}`, 3000);
  }

  private ueberSzene(ev: PointerEvent) {
    const r = this.welt.renderer!.three.domElement.getBoundingClientRect();
    return ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom &&
      !(ev.target as HTMLElement | null)?.closest?.(".app-panel, .lage-panel");
  }

  private lageText(p: THREE.Vector3) {
    const { e, n, h } = ausSzene(p);
    return rahmen.modus === "reihe" ? `Station ${zahlText(e)} m, GOK ${zahlText(h)} m NHN` : `R ${zahlText(e)} · H ${zahlText(n)}`;
  }

  // ---------------------------------------------------------------- Modus
  async umschalten(aktiv: boolean) {
    this.aktiv = aktiv;
    document.body.classList.toggle("lage-aktiv", aktiv);
    if (!aktiv) this.waehlenAbbrechen();
    for (const s of this.nadeln.values()) this.markeBeschriften(s);
    this.bildSichtbarkeit();
    szeneAktualisieren();
    this.r.modusGeaendert(aktiv);
  }

  setSichtbar(v: boolean) {
    this.sichtbar = v;
    for (const s of this.nadeln.values()) s.saeule.visible = v && s.oben !== null;
  }

  ohneLage() {
    return [...this.nadeln.values()].filter((s) => !s.oben);
  }

  // ---------------------------------------------------------------- Unterlage
  private unterlageSetzen(u: Unterlage | null) {
    this.unterlage = u;
    if (!u) {
      this.bild?.removeFromParent();
      this.bild?.geometry.dispose();
      this.bild?.material.map?.dispose();
      this.bild = null;
      this.texturUrl = "";
      this.abb = null;
      return;
    }
    if (!this.bild) {
      const mat = new THREE.MeshBasicMaterial({ transparent: true, opacity: this.deckkraft, side: THREE.DoubleSide,
                                                 depthWrite: false, toneMapped: false });
      this.bild = new THREE.Mesh(new THREE.BufferGeometry(), mat);
      this.bild.name = "Unterlage";
      this.bild.renderOrder = 1;
      this.welt.scene.three.add(this.bild);
    }
    if (this.texturUrl !== u.url) {
      this.texturUrl = u.url;
      new THREE.TextureLoader().load(u.url, (t) => {
        t.colorSpace = THREE.SRGBColorSpace;
        t.anisotropy = this.welt.renderer!.three.capabilities.getMaxAnisotropy();
        this.bild!.material.map?.dispose();
        this.bild!.material.map = t;
        this.bild!.material.needsUpdate = true;
        this.r.neuZeichnen();
      }, undefined, () => this.r.meldung(`Unterlage nicht geladen: ${u.name}`, 8000));
    }
    this.bildGeometrie();
    this.bildSichtbarkeit();
  }

  /** Kalibrierung, die gerade gilt: Vorschau (Entwurf in der App) oder gespeichert. */
  kalibrierung(): Kalibrierung | null {
    return this.entwurf !== undefined ? this.entwurf : this.unterlage?.kalibrierung ?? null;
  }

  /** Vorschau einer Kalibrierung, bevor sie uebernommen ist (undefined = gespeicherte gilt wieder). */
  vorschau(k: Kalibrierung | null | undefined) {
    this.entwurf = k;
    this.bildGeometrie();
    szeneAktualisieren();
    this.r.neuZeichnen();
  }

  /** Vier Ecken des Bilds ueber die Abbildung in die Szene (affin: Dreiecke bleiben exakt). */
  private bildGeometrie() {
    const u = this.unterlage;
    if (!u || !this.bild) return;
    const mit = [...this.nadeln.values()].filter((s) => s.daten.x !== null);
    const mitte: [number, number] = mit.length
      ? [mit.reduce((a, s) => a + s.daten.x!, 0) / mit.length, mit.reduce((a, s) => a + s.daten.y!, 0) / mit.length]
      : [rahmen.e0, rahmen.n0];
    const oben = mit.length ? Math.max(...mit.map((s) => s.daten.gok)) + 5 : 10;
    this.abb = abbildung(u, mitte, oben, this.kalibrierung());
    const ecken: [number, number][] = [[0, 0], [u.breite, 0], [u.breite, u.hoehe], [0, u.hoehe]];
    const pos: number[] = [];
    let yPlan = -Infinity;
    for (const s of this.nadeln.values()) if (s.oben) yPlan = Math.max(yPlan, s.oben.y);
    if (!Number.isFinite(yPlan)) yPlan = hoeheZuSzene(oben);
    yPlan += Math.max(0.2, this.radiusAuto * 0.5);
    for (const [uu, vv] of ecken) {
      const [x, y] = this.abb(uu, vv);
      const p = u.art === "plan" ? zuSzene(x, y, 0).setY(yPlan) : zuSzene(x, 0, y).setZ(-this.schnittTiefe);
      pos.push(p.x, p.y, p.z);
    }
    const g = this.bild.geometry;
    g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
    g.setAttribute("uv", new THREE.Float32BufferAttribute([0, 1, 1, 1, 1, 0, 0, 0], 2));
    g.setIndex([0, 3, 1, 1, 3, 2]);
    g.computeBoundingBox();
    g.computeBoundingSphere();
  }

  /** Laengsschnitt hinter das Modell legen (Modellbreite quer zur Reihe). */
  setSchnittTiefe(t: number) {
    this.schnittTiefe = Math.max(1, t);
    this.bildGeometrie();
  }

  bildSichtbarkeit() {
    if (!this.bild) return;
    this.bild.visible = this.aktiv || this.unterlageImModell;
    this.bild.material.opacity = this.deckkraft;
    this.r.neuZeichnen();
  }

  // ---------------------------------------------------------------- Bildpunkte waehlen (Strecke, Bezugspunkt)
  /** Naechster Klick auf die Unterlage liefert den Bildpunkt (Pixel); Esc oder ein neuer Aufruf bricht ab (null). */
  bildpunktWaehlen(): Promise<Bildpunkt | null> {
    this.waehlenAbbrechen();
    if (!this.bild || !this.unterlage) return Promise.resolve(null);
    document.body.classList.add("waehlt");
    return new Promise((fertig) => {
      this.waehlen = fertig;
    });
  }

  waehlenAbbrechen() {
    const f = this.waehlen;
    this.waehlen = null;
    document.body.classList.remove("waehlt");
    f?.(null);
  }

  private bildKlick(ev: MouseEvent) {
    if (!this.waehlen || !this.bild || !this.unterlage) return;
    this.caster.setFromCamera(this.ndc(ev), this.welt.camera.three);
    const [t] = this.caster.intersectObject(this.bild, false);
    if (!t?.uv) {
      this.r.meldung("Bitte auf die Unterlage klicken.", 3000);
      return;
    }
    const f = this.waehlen;
    this.waehlen = null;
    document.body.classList.remove("waehlt");
    f({ u: t.uv.x * this.unterlage.breite, v: (1 - t.uv.y) * this.unterlage.hoehe });
  }

  /** Hilfsmarken der Kalibrierung: gemessene Strecke(n) und Bezugspunkt. */
  hilfsmarken(h: Hilfsmarken) {
    this.hilfe = h;
    this.r.neuZeichnen();
  }

  private hilfeSetzen(w: number, h: number) {
    const sichtbar = this.aktiv && !!this.bild?.visible;
    const punkte: [string, Bildpunkt | null | undefined, string][] = [
      ["1", this.hilfe.strecke?.[0], "strecke"], ["2", this.hilfe.strecke?.[1], "strecke"],
      ["H1", this.hilfe.hoehe?.[0], "hoehe"], ["H2", this.hilfe.hoehe?.[1], "hoehe"], ["B", this.hilfe.bezug, "bezug"]];
    const schirm: (THREE.Vector2 | null)[] = [];
    punkte.forEach(([text, p, art], k) => {
      let el = this.hilfeMarken[k];
      if (!el) {
        el = this.hilfeMarken[k] = document.createElement("div");
        el.className = `passpunkt ${art}`;
        el.textContent = text;
        this.ebene.append(el);
      }
      const q = sichtbar && p ? this.bildPunkt(p.u, p.v) : null;
      if (!q) {
        el.hidden = true;
        schirm.push(null);
        return;
      }
      q.project(this.welt.camera.three);
      el.hidden = q.z > 1;
      const x = ((q.x + 1) / 2) * w;
      const y = ((1 - q.y) / 2) * h;
      el.style.transform = `translate(${x.toFixed(1)}px, ${y.toFixed(1)}px)`;
      schirm.push(new THREE.Vector2(x, y));
    });
    const linie = (a: THREE.Vector2 | null, b: THREE.Vector2 | null, art: string) =>
      a && b ? `<line class="${art}" x1="${a.x}" y1="${a.y}" x2="${b.x}" y2="${b.y}"/>` : "";
    this.linien.innerHTML = linie(schirm[0], schirm[1], "strecke") + linie(schirm[2], schirm[3], "hoehe");
  }

  /** Bildpixel (u nach rechts, v nach unten) -> Szenenpunkt auf der Unterlage (Parallelogramm aus den Ecken). */
  bildPunkt(u: number, v: number) {
    if (!this.bild || !this.unterlage) return null;
    const pos = this.bild.geometry.getAttribute("position");
    if (!pos) return null;
    const a = new THREE.Vector3().fromBufferAttribute(pos, 0);
    const b = new THREE.Vector3().fromBufferAttribute(pos, 1).sub(a);
    const d = new THREE.Vector3().fromBufferAttribute(pos, 3).sub(a);
    return a.addScaledVector(b, u / this.unterlage.breite).addScaledVector(d, v / this.unterlage.hoehe);
  }

  /** Bildpixel -> Bildschirm (fuer Pruefungen und Hilfen). */
  bildZuSchirm(u: number, v: number) {
    const p = this.bildPunkt(u, v);
    if (!p) return null;
    p.project(this.welt.camera.three);
    const r = this.welt.renderer!.three.domElement.getBoundingClientRect();
    return { x: r.left + ((p.x + 1) / 2) * r.width, y: r.top + ((1 - p.y) / 2) * r.height };
  }

  /** Info fuer die Pruefungen (check.mjs). */
  status() {
    const u = this.unterlage;
    return {
      nadeln: this.nadeln.size,
      ohneLage: this.ohneLage().length,
      unterlage: u ? { art: u.art, kalibriert: !!u.kalibrierung, gesperrt: !!u.kalibrierung?.gesperrt, sichtbar: !!this.bild?.visible } : null,
      radius: this.radiusAuto,
      text: u ? kalibrierungText(u, this.kalibrierung()) : "",
    };
  }

  /** Bildschirmpunkt einer Marke (fuer Tests und den Fokus). */
  markenPunkt(id: string) {
    const s = this.nadeln.get(id);
    if (!s?.oben || s.marke.hidden) return null;
    const r = s.marke.querySelector("i")!.getBoundingClientRect();      // Punkt, nicht Beschriftung
    return { x: r.left + r.width / 2, y: r.top + r.height / 2 };
  }

  szenenPunkt(id: string) {
    return this.nadeln.get(id)?.oben?.clone() ?? null;
  }

  escape() {
    if (this.waehlen) {
      this.waehlenAbbrechen();
      return true;
    }
    return false;
  }
}

export { esc };
