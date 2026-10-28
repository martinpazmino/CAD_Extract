// Lage-Editor: jede Bohrung als Stecknadel (Saeule aus den Schichten + ziehbare Marke), dazu eine
// PDF-Unterlage als Bild in der Szene - Lageplan (Draufsicht) oder Laengsschnitt (Seitenansicht) -,
// kalibriert ueber zwei Passpunkte. Ziehen setzt die Lage vor dem Modellieren; Python (ui/projekt.py)
// bekommt jede Aenderung als Ereignis und rechnet das Modell neu. Beschreibung: docs/20.
//
// Lageplan: Bild -> (Rechtswert, Hochwert) als Aehnlichkeit (Massstab, Drehung, Verschiebung).
// Laengsschnitt: Bild -> (Station, Hoehe m NHN) achsparallel mit eigenem Hoehenmassstab (Ueberhoehung
// der Zeichnung). Ohne Kalibrierung liegt das Bild mit 1:1000 bzw. 1:1000/1:100 bei den Bohrungen.
import * as THREE from "three";
import * as OBC from "@thatopen/components";
import * as BUI from "@thatopen/ui";
import { ausSzene, hoeheZuSzene, rahmen, zuSzene } from "./rahmen";
import { eingebettet, ereignis, type Nadel, type Passpunkt, type Unterlage } from "./streamlit";
import { huelleMelden, szeneAktualisieren } from "./kamera";
import { tipp } from "./tipp";

type Welt = OBC.SimpleWorld<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.BaseRenderer>;
type Abbildung = (u: number, v: number) => [number, number];

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

const UNSICHER = 0.6;
const esc = (t: string) => t.replace(/[<>&"]/g, (c) => ({ "<": "&lt;", ">": "&gt;", "&": "&amp;", '"': "&quot;" })[c]!);
const zahlText = (v: number, stellen = 2) =>
  v.toLocaleString("de-DE", { minimumFractionDigits: stellen, maximumFractionDigits: stellen });

// ------------------------------------------------------------------ Kalibrierung (rein rechnerisch, getestet in check.mjs)
/** Bild -> Welt fuer die Unterlage; mitte/hoehe nur fuer den unkalibrierten Startwert. */
export function abbildung(u: Unterlage, mitte: [number, number], oben = 0): Abbildung {
  const p = u.kalibrierung?.punkte ?? [];
  const m = u.mm_pro_px;                                // m je Pixel bei 1:1000
  if (u.art === "plan") {
    if (p.length >= 2) {
      const [a, b] = aehnlichkeit(p[0], p[1]);
      return (uu, vv) => [a[0] * uu - a[1] * -vv + b[0], a[0] * -vv + a[1] * uu + b[1]];
    }
    return (uu, vv) => [mitte[0] + (uu - u.breite / 2) * m, mitte[1] - (vv - u.hoehe / 2) * m];
  }
  if (p.length >= 2 && p[0].u !== p[1].u && p[0].v !== p[1].v) {
    const sx = (p[1].x - p[0].x) / (p[1].u - p[0].u);
    const sy = (p[1].y - p[0].y) / (p[1].v - p[0].v);
    return (uu, vv) => [p[0].x + (uu - p[0].u) * sx, p[0].y + (vv - p[0].v) * sy];
  }
  return (uu, vv) => [mitte[0] + (uu - u.breite / 2) * m, oben - vv * m / 10];
}

/** Komplex: w = A q + B mit q = u - i v (Bildzeilen laufen nach unten), w = x + i y. */
function aehnlichkeit(p1: Passpunkt, p2: Passpunkt): [[number, number], [number, number]] {
  const dq = [p2.u - p1.u, -(p2.v - p1.v)];
  const dw = [p2.x - p1.x, p2.y - p1.y];
  const n = dq[0] ** 2 + dq[1] ** 2 || 1;
  const a: [number, number] = [(dw[0] * dq[0] + dw[1] * dq[1]) / n, (dw[1] * dq[0] - dw[0] * dq[1]) / n];
  const q1 = [p1.u, -p1.v];
  const b: [number, number] = [p1.x - (a[0] * q1[0] - a[1] * q1[1]), p1.y - (a[0] * q1[1] + a[1] * q1[0])];
  return [a, b];
}

/** Massstab und Drehung einer Kalibrierung als Text. */
export function kalibrierungText(u: Unterlage): string {
  const p = u.kalibrierung?.punkte ?? [];
  if (p.length < 2) return "nicht kalibriert";
  const papier = u.mm_pro_px / 1000;                    // m Papier je Pixel
  if (u.art === "plan") {
    const [a] = aehnlichkeit(p[0], p[1]);
    const s = Math.hypot(a[0], a[1]);
    // Drehung des Plans gegen Gitternord, gegen den Uhrzeigersinn positiv (Bild -> Welt dreht entgegen)
    const dreh = -THREE.MathUtils.radToDeg(Math.atan2(a[1], a[0]));
    return `kalibriert · 1:${Math.round(s / papier).toLocaleString("de-DE")} · Drehung ${zahlText(dreh, 1)}°`;
  }
  const sx = Math.abs((p[1].x - p[0].x) / (p[1].u - p[0].u));
  const sy = Math.abs((p[1].y - p[0].y) / (p[1].v - p[0].v));
  return `kalibriert · Länge 1:${Math.round(sx / papier).toLocaleString("de-DE")} · Höhe 1:${Math.round(sy / papier).toLocaleString("de-DE")} (Überhöhung ${zahlText(sx / sy, 1)}×)`;
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
  private readonly materialien = new Map<string, THREE.MeshLambertMaterial>();
  private radius = 0.5;
  private unterlage: Unterlage | null = null;
  private bild: THREE.Mesh<THREE.BufferGeometry, THREE.MeshBasicMaterial> | null = null;
  private texturUrl = "";
  private abb: Abbildung | null = null;
  private passpunkte: (Partial<Passpunkt> & { u?: number; v?: number })[] = [{}, {}];
  private passMarken: HTMLDivElement[] = [];
  private epsg: number | null = null;
  private waehle: number | null = null;                 // Passpunkt, der gerade im Bild gesetzt wird
  private schnittTiefe = 2;
  private ziehen: { id: string; versatz: THREE.Vector3; ebene: THREE.Plane; start: [number, number]; bewegt: boolean;
                    neu: boolean; hoehe: boolean } | null = null;
  private readonly caster = new THREE.Raycaster();
  readonly panel: HTMLElement;
  private readonly panelNeu: () => void;

  constructor(private readonly welt: Welt, huelle: HTMLElement, private readonly r: LageRueckrufe) {
    this.gruppe.name = "Bohrungen (Lage)";
    welt.scene.three.add(this.gruppe);
    this.ebene.className = "marken";
    huelle.append(this.ebene);
    huelleMelden(() => this.kiste());
    welt.renderer!.onAfterUpdate.add(() => this.markenSetzen());
    const flaeche = welt.renderer!.three.domElement;
    flaeche.addEventListener("click", (ev) => this.bildKlick(ev));
    window.addEventListener("pointermove", (ev) => this.ziehenBewegen(ev));
    window.addEventListener("pointerup", (ev) => this.ziehenEnde(ev));
    const [panel, neu] = BUI.Component.create<BUI.Panel, Record<string, never>>((_zustand) => this.panelVorlage(), {});
    this.panel = panel;
    this.panelNeu = () => neu();
    panel.classList.add("lage-panel");
    panel.hidden = true;
  }

  // ---------------------------------------------------------------- Daten
  setzen(nadeln: Nadel[], unterlage: Unterlage | null) {
    const alt = new Set(this.nadeln.keys());
    const ausdehnung = this.ausdehnung(nadeln);
    this.radius = THREE.MathUtils.clamp(ausdehnung / 600, 0.4, 6);
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
    this.unterlageSetzen(unterlage);
    szeneAktualisieren();
    this.panelNeu();
    this.r.neuZeichnen();
  }

  private ausdehnung(nadeln: Nadel[]) {
    const xs = nadeln.filter((n) => n.x !== null).map((n) => n.x!);
    const ys = nadeln.filter((n) => n.y !== null).map((n) => n.y!);
    if (!xs.length) return 50;
    return Math.max(Math.max(...xs) - Math.min(...xs), Math.max(...ys) - Math.min(...ys), 20);
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
    const schichten = s.daten.schichten.length ? s.daten.schichten : [[0, s.daten.ende || 1, "#9aa0a6"]];
    for (const [oben, unten, farbe] of schichten) {
      const h = (Number(unten) - Number(oben)) * rahmen.faktor;
      if (!(h > 0)) continue;
      const m = new THREE.Mesh(new THREE.CylinderGeometry(this.radius, this.radius, h, 16), this.material(String(farbe), blass));
      m.position.y = -Number(oben) * rahmen.faktor - h / 2;
      m.userData.nadel = s.daten.id;
      s.saeule.add(m);
    }
    s.saeule.position.copy(s.oben);
  }

  kiste(): THREE.Box3 | null {
    const b = new THREE.Box3();
    for (const s of this.nadeln.values()) {
      if (!s.oben) continue;
      b.expandByPoint(s.oben);
      b.expandByPoint(new THREE.Vector3(s.oben.x, s.oben.y - (s.daten.ende || 1) * rahmen.faktor, s.oben.z));
    }
    if (this.bild?.visible) {
      this.bild.geometry.computeBoundingBox();
      b.union(this.bild.geometry.boundingBox!);
    }
    if (!b.isEmpty()) b.expandByScalar(this.radius * 2);
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
    const unsicher = n.konfidenz !== null && n.konfidenz < UNSICHER && !n.geprueft;
    s.marke.querySelector("span")!.textContent = n.code;
    s.marke.classList.toggle("geprueft", n.geprueft);
    s.marke.classList.toggle("unsicher", unsicher);
    s.marke.classList.toggle("raus", !n.im_modell);
    s.marke.classList.toggle("gewaehlt", this.ausgewaehlt === n.id);
    const zeilen = [n.code, n.quelle ? `Lage: ${n.quelle}` : "ohne Lage",
                    `GOK ${n.gok_bekannt ? `${zahlText(n.gok)} m NHN` : "unbekannt (relativ)"} · Endteufe ${zahlText(n.ende)} m`,
                    `Schichten geprüft ${n.schichten_geprueft}/${n.schichten_n}` +
                    (n.konfidenz !== null ? ` · min. Konfidenz ${zahlText(n.konfidenz)}` : "")];
    if (!n.im_modell) zeilen.push(`nicht im Modell${n.grund ? `: ${n.grund}` : ""}`);
    if (this.aktiv) zeilen.push(rahmen.modus === "reihe" ? "Ziehen: Station · Umschalt+Ziehen: GOK" : "Ziehen: Lage setzen");
    s.marke.title = zeilen.join("\n");
  }

  waehlen(id: string | null) {
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
    this.passMarkenSetzen(w, h);
  }

  // ---------------------------------------------------------------- Ziehen
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

  /** Start: Marke in der Szene (neu = false) oder Bohrung ohne Lage aus der Liste (neu = true). */
  ziehenStart(ev: PointerEvent, id: string, neu: boolean) {
    if (ev.button !== 0) return;
    const s = this.nadeln.get(id);
    if (!s) return;
    ev.preventDefault();
    ev.stopPropagation();
    if (!this.aktiv || (!s.oben && !neu)) {
      this.ziehen = { id, versatz: new THREE.Vector3(), ebene: new THREE.Plane(), start: [ev.clientX, ev.clientY],
                      bewegt: false, neu: false, hoehe: false };
      return;                                            // nur Klick (Auswahl)
    }
    const oben = s.oben ?? this.startpunkt(s.daten);
    const ebene = this.ziehEbene(oben);
    const treffer = neu ? oben.clone() : this.schnittpunkt(ev, ebene);
    this.ziehen = { id, versatz: treffer ? oben.clone().sub(treffer) : new THREE.Vector3(), ebene,
                    start: [ev.clientX, ev.clientY], bewegt: false, neu, hoehe: ev.shiftKey && rahmen.modus === "reihe" };
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
    if (!s || !this.aktiv) return;
    const p = this.schnittpunkt(ev, z.ebene);
    if (!p) return;
    p.add(z.versatz);
    const alt = s.oben ?? this.startpunkt(s.daten);
    if (rahmen.modus === "reihe") {
      p.z = alt.z;
      if (!(z.hoehe || ev.shiftKey)) p.y = alt.y;
    } else {
      p.y = alt.y;
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
    if (!this.aktiv || !s.oben) return;
    if (z.neu && !this.ueberSzene(ev)) {             // ausserhalb losgelassen: bleibt ohne Lage
      s.oben = null;
      this.saeuleBauen(s);
      return;
    }
    const { e, n, h } = ausSzene(s.oben);
    const runden = (v: number) => Math.round(v * 100) / 100;
    if (rahmen.modus === "reihe") {
      ereignis({ typ: "station", id: z.id, station: runden(e) });
      if (Math.abs(h - s.daten.gok) > 0.005) ereignis({ typ: "gok", id: z.id, gok: runden(h) });
    } else {
      ereignis({ typ: "lage", id: z.id, x: runden(e), y: runden(n) });
    }
    const reihe = rahmen.modus === "reihe";
    s.daten = { ...s.daten, x: runden(e), y: reihe ? 0 : runden(n), gok: reihe ? runden(h) : s.daten.gok,
                quelle: reihe ? "Reihe (Station im Schnitt gesetzt)" : this.unterlage?.kalibrierung ? "Plan (kalibriert)" : "manuell (Viewer)" };
    this.markeBeschriften(s);
    szeneAktualisieren();
    this.panelNeu();
    this.r.meldung(`${s.daten.code} gesetzt: ${this.lageText(s.oben)}${eingebettet ? " – Modell wird angepasst …" : ""}`, 3000);
  }

  private ueberSzene(ev: PointerEvent) {
    const r = this.welt.renderer!.three.domElement.getBoundingClientRect();
    return ev.clientX >= r.left && ev.clientX <= r.right && ev.clientY >= r.top && ev.clientY <= r.bottom &&
      !(ev.target as HTMLElement | null)?.closest?.(".lage-panel");
  }

  private lageText(p: THREE.Vector3) {
    const { e, n, h } = ausSzene(p);
    return rahmen.modus === "reihe" ? `Station ${zahlText(e)} m, GOK ${zahlText(h)} m NHN` : `R ${zahlText(e)} · H ${zahlText(n)}`;
  }

  // ---------------------------------------------------------------- Modus
  async umschalten(aktiv: boolean) {
    this.aktiv = aktiv;
    this.panel.hidden = !aktiv;
    document.body.classList.toggle("lage-aktiv", aktiv);
    this.waehle = null;
    for (const s of this.nadeln.values()) this.markeBeschriften(s);
    this.bildSichtbarkeit();
    szeneAktualisieren();
    this.panelNeu();
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
    if (u.kalibrierung?.epsg) this.epsg = u.kalibrierung.epsg;
    if (u.kalibrierung?.punkte?.length === 2 && this.waehle === null) {
      this.passpunkte = u.kalibrierung.punkte.map((p) => ({ ...p }));
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

  /** Vier Ecken des Bilds ueber die Abbildung in die Szene (affin: Dreiecke bleiben exakt). */
  private bildGeometrie() {
    const u = this.unterlage;
    if (!u || !this.bild) return;
    const mit = [...this.nadeln.values()].filter((s) => s.daten.x !== null);
    const mitte: [number, number] = mit.length
      ? [mit.reduce((a, s) => a + s.daten.x!, 0) / mit.length, mit.reduce((a, s) => a + s.daten.y!, 0) / mit.length]
      : [rahmen.e0, rahmen.n0];
    const oben = mit.length ? Math.max(...mit.map((s) => s.daten.gok)) + 5 : 10;
    this.abb = abbildung(u, mitte, oben);
    const ecken: [number, number][] = [[0, 0], [u.breite, 0], [u.breite, u.hoehe], [0, u.hoehe]];
    const pos: number[] = [];
    let yPlan = -Infinity;
    for (const s of this.nadeln.values()) if (s.oben) yPlan = Math.max(yPlan, s.oben.y);
    if (!Number.isFinite(yPlan)) yPlan = hoeheZuSzene(oben);
    yPlan += Math.max(0.2, this.radius * 0.5);
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

  private bildSichtbarkeit() {
    if (!this.bild) return;
    this.bild.visible = this.aktiv || this.unterlageImModell;
    this.bild.material.opacity = this.deckkraft;
    this.r.neuZeichnen();
  }

  // ---------------------------------------------------------------- Passpunkte
  private bildKlick(ev: MouseEvent) {
    if (this.waehle === null || !this.bild || !this.unterlage) return;
    this.caster.setFromCamera(this.ndc(ev), this.welt.camera.three);
    const [t] = this.caster.intersectObject(this.bild, false);
    if (!t?.uv) {
      this.r.meldung("Passpunkt: bitte auf die Unterlage klicken.", 3000);
      return;
    }
    const k = this.waehle;
    this.passpunkte[k] = { ...this.passpunkte[k], u: t.uv.x * this.unterlage.breite, v: (1 - t.uv.y) * this.unterlage.hoehe };
    this.waehle = null;
    document.body.classList.remove("waehlt");
    this.panelNeu();
    this.r.meldung(`Passpunkt ${k + 1} gesetzt – jetzt seine Koordinaten eintragen oder eine Bohrung wählen.`, 4000);
  }

  private passMarkenSetzen(w: number, h: number) {
    const sichtbar = this.aktiv && !!this.abb && !!this.bild?.visible;
    this.passpunkte.forEach((p, k) => {
      let el = this.passMarken[k];
      if (!el) {
        el = this.passMarken[k] = document.createElement("div");
        el.className = "passpunkt";
        el.textContent = String(k + 1);
        this.ebene.append(el);
      }
      if (!sichtbar || p.u === undefined || p.v === undefined || !this.bild) {
        el.hidden = true;
        return;
      }
      this.punkt.copy(this.bildPunkt(p.u, p.v)!).project(this.welt.camera.three);
      el.hidden = this.punkt.z > 1;
      el.style.transform = `translate(${(((this.punkt.x + 1) / 2) * w).toFixed(1)}px, ${(((1 - this.punkt.y) / 2) * h).toFixed(1)}px)`;
    });
  }

  /** Bildpixel (u nach rechts, v nach unten) -> Szenenpunkt auf der Unterlage (Parallelogramm aus den Ecken). */
  bildPunkt(u: number, v: number) {
    if (!this.bild || !this.unterlage) return null;
    const pos = this.bild.geometry.getAttribute("position");
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

  private passBohrung(k: number, id: string) {
    const s = this.nadeln.get(id);
    if (!s || s.daten.x === null) return;
    const p = this.passpunkte[k];
    if (this.unterlage?.art === "schnitt") Object.assign(p, { x: s.daten.x, y: s.daten.gok });
    else Object.assign(p, { x: s.daten.x, y: s.daten.y! });
    this.panelNeu();
  }

  private kalibrieren() {
    const u = this.unterlage;
    const p = this.passpunkte;
    const voll = p.every((q) => [q.u, q.v, q.x, q.y].every((v) => typeof v === "number" && Number.isFinite(v)));
    if (!u || !voll) {
      this.r.meldung("Für beide Passpunkte Bildpunkt und Koordinaten setzen.", 5000);
      return;
    }
    const punkte = p.map((q) => ({ u: q.u!, v: q.v!, x: q.x!, y: q.y! }));
    if (Math.hypot(punkte[1].u - punkte[0].u, punkte[1].v - punkte[0].v) < 20) {
      this.r.meldung("Passpunkte liegen zu dicht beieinander.", 5000);
      return;
    }
    if (u.art === "schnitt" && (Math.abs(punkte[1].u - punkte[0].u) < 20 || Math.abs(punkte[1].v - punkte[0].v) < 20)) {
      this.r.meldung("Längsschnitt: die Passpunkte müssen sich in Station und Höhe unterscheiden.", 6000);
      return;
    }
    u.kalibrierung = { punkte, epsg: u.art === "plan" ? this.epsg : null };
    ereignis({ typ: "kalibrierung", art: u.art, punkte, epsg: u.kalibrierung.epsg ?? null });
    this.bildGeometrie();
    szeneAktualisieren();
    this.panelNeu();
    this.r.meldung(`Unterlage ${kalibrierungText(u)}.`, 5000);
  }

  // ---------------------------------------------------------------- Panel
  private panelVorlage() {
    const u = this.unterlage;
    const reihe = rahmen.modus === "reihe";
    const ohne = this.ohneLage();
    const mitLage = [...this.nadeln.values()].filter((s) => s.daten.x !== null &&
      !/Plan|Viewer|Reihe|schematisch/.test(s.daten.quelle));
    const hilfe = reihe
      ? "Marken entlang der Reihe ziehen: Station. Mit Umschalttaste: Ansatzhöhe (GOK)."
      : "Marken ziehen: Lage setzen. Klick: Bohrung zeigen.";
    const passpunkt = (k: number) => {
      const p = this.passpunkte[k];
      const gesetzt = p.u !== undefined;
      const eingabe = (schluessel: "x" | "y", titel: string) => BUI.html`
        <label class="feld">${titel}<input type="number" step="0.01" .value=${p[schluessel] === undefined ? "" : String(p[schluessel])}
          @change=${(e: Event) => { const v = parseFloat((e.target as HTMLInputElement).value); p[schluessel] = Number.isFinite(v) ? v : undefined; }}></label>`;
      return BUI.html`
        <div class="passzeile">
          <bim-button label=${`Punkt ${k + 1}`} icon="mdi:crosshairs-gps" ?active=${this.waehle === k}
            @click=${() => { this.waehle = this.waehle === k ? null : k; document.body.classList.toggle("waehlt", this.waehle !== null); this.panelNeu(); }}>${tipp("Passpunkt im Bild setzen", "Danach auf die Unterlage klicken.")}</bim-button>
          <span class="leise">${gesetzt ? `Bild ${Math.round(p.u!)}, ${Math.round(p.v!)} px` : "Bildpunkt fehlt"}</span>
        </div>
        <div class="passzeile">
          ${eingabe("x", reihe || u?.art === "schnitt" ? "Station [m]" : "Rechtswert")}
          ${eingabe("y", reihe || u?.art === "schnitt" ? "Höhe [m NHN]" : "Hochwert")}
          <label class="feld">Bohrung
            <select @change=${(e: Event) => this.passBohrung(k, (e.target as HTMLSelectElement).value)}>
              <option value="">–</option>
              ${(u?.art === "schnitt" ? [...this.nadeln.values()].filter((s) => s.daten.x !== null && s.daten.gok_bekannt) : mitLage)
                .map((s) => BUI.html`<option value=${s.daten.id}>${s.daten.code}</option>`)}
            </select>
          </label>
        </div>`;
    };
    return BUI.html`
      <bim-panel label="Lage bearbeiten" icon="mdi:map-marker-radius">
        <bim-panel-section label="Bohrungen" icon="mdi:map-marker-radius">
          <p class="text">${hilfe}</p>
          ${ohne.length ? BUI.html`
            <p class="text">Ohne Lage (${ohne.length}) – in die Ansicht ziehen:</p>
            <div class="parkplatz">
              ${ohne.map((s) => BUI.html`<span class="park" title="In die Ansicht ziehen"
                @pointerdown=${(e: PointerEvent) => this.ziehenStart(e, s.daten.id, true)}>${s.daten.code}</span>`)}
            </div>` : BUI.html`<p class="text leise">Alle Bohrungen haben eine Lage.</p>`}
        </bim-panel-section>
        <bim-panel-section label="Unterlage (PDF)" icon="mdi:file-pdf-box">
          ${u ? BUI.html`
            <p class="text leise">${u.name} · ${u.art === "plan" ? "Lageplan (Draufsicht)" : "Längsschnitt (Seitenansicht)"}</p>
            <label class="feld">Deckkraft
              <input type="range" min="0.1" max="1" step="0.05" .value=${String(this.deckkraft)}
                @input=${(e: Event) => { this.deckkraft = parseFloat((e.target as HTMLInputElement).value); this.bildSichtbarkeit(); }}>
            </label>
            <bim-checkbox label="Auch in der Modellansicht zeigen" ?checked=${this.unterlageImModell}
              @change=${(e: Event) => { this.unterlageImModell = (e.target as BUI.Checkbox).checked; this.bildSichtbarkeit(); }}></bim-checkbox>
            <p class=${`text ${u.kalibrierung ? "ok" : "warn"}`}>${kalibrierungText(u)}</p>
            <p class="text leise">Zwei Passpunkte: im Bild anklicken (vorher heranzoomen), Koordinaten eintragen oder von einer Bohrung übernehmen.</p>
            ${passpunkt(0)}${passpunkt(1)}
            ${u.art === "plan" ? BUI.html`
              <label class="feld">EPSG (optional)<input type="number" step="1" .value=${this.epsg ? String(this.epsg) : ""}
                @change=${(e: Event) => { const v = parseInt((e.target as HTMLInputElement).value, 10); this.epsg = Number.isFinite(v) ? v : null; }}></label>` : ""}
            <bim-button label="Kalibrierung übernehmen" icon="mdi:check" @click=${() => this.kalibrieren()}></bim-button>`
          : BUI.html`<p class="text leise">Keine Unterlage. Lageplan oder Längsschnitt als PDF in der App unter „Lage & Unterlage“ hochladen.</p>`}
        </bim-panel-section>
      </bim-panel>`;
  }

  /** Info fuer die Pruefungen (check.mjs). */
  status() {
    return {
      nadeln: this.nadeln.size,
      ohneLage: this.ohneLage().length,
      unterlage: this.unterlage ? { art: this.unterlage.art, kalibriert: !!this.unterlage.kalibrierung, sichtbar: !!this.bild?.visible } : null,
      radius: this.radius,
      text: this.unterlage ? kalibrierungText(this.unterlage) : "",
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
    if (this.waehle !== null) {
      this.waehle = null;
      document.body.classList.remove("waehlt");
      this.panelNeu();
      return true;
    }
    return false;
  }
}

export { esc };
