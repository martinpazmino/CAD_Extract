// Kamera fuer grosse Baugrundmodelle (Trassen ueber 5 km): That Open startet mit near 1 / far 1000
// (perspektivisch) bzw. 0.1 / 1000 (orthografisch) - alles hinter 1 km wird abgeschnitten. Hier werden
// near/far bei jeder Kamerabewegung aus der Szenengroesse und dem Abstand nachgefuehrt, das Raster
// waechst mit dem Modell, und alle Ansichten (Wuerfel, Iso, Oben ...) passen auf die ganze Szene.
import * as THREE from "three";
import * as OBC from "@thatopen/components";

type Welt = OBC.SimpleWorld<OBC.SimpleScene, OBC.OrthoPerspectiveCamera, OBC.BaseRenderer>;

const quellen = new Set<() => THREE.Box3 | null>();
const kugel = new THREE.Sphere(new THREE.Vector3(), 50);
const kiste = new THREE.Box3();
let welt: Welt;
let raster: OBC.SimpleGrid | undefined;

/** Bausteine der Szene (Modell, Bohrungen, Unterlage) melden ihre Huelle hier an. */
export function huelleMelden(quelle: () => THREE.Box3 | null) {
  quellen.add(quelle);
}

export function szeneKugel() {
  return kugel;
}

/** Huelle neu bestimmen (nach Laden, Ziehen, Ueberhoehung); passt Raster und near/far an. */
export function szeneAktualisieren() {
  kiste.makeEmpty();
  for (const q of quellen) {
    const b = q();
    if (b && !b.isEmpty()) kiste.union(b);
  }
  if (kiste.isEmpty()) kiste.setFromCenterAndSize(new THREE.Vector3(), new THREE.Vector3(100, 20, 100));
  kiste.getBoundingSphere(kugel);
  kugel.radius = Math.max(kugel.radius, 5);
  rasterAnpassen();
  grenzenAnpassen();
}

function rasterAnpassen() {
  if (!raster) return;
  const r = kugel.radius;
  const fein = 10 ** Math.max(0, Math.floor(Math.log10(r / 20)));     // 1 m bis 100 m
  raster.config.primarySize = fein;
  raster.config.secondarySize = fein * 10;
  raster.config.distance = Math.max(500, r * 4);
  raster.three.position.y = kiste.min.y - Math.max(0.5, r * 0.002);
}

/** near/far aus Abstand zum Ziel und Szenengroesse: Tiefenaufloesung nah, nichts abgeschnitten fern. */
export function grenzenAnpassen() {
  if (!welt) return;
  const kam = welt.camera.three;
  if (!Number.isFinite(kam.position.x)) {
    nachholen();
    return;
  }
  const abstand = kam.position.distanceTo(kugel.center);
  const weit = abstand + kugel.radius * 2;
  if (kam instanceof THREE.PerspectiveCamera) {
    const ziel = Math.max(welt.camera.controls.distance, 0.01);
    const near = THREE.MathUtils.clamp(ziel / 1000, 0.02, 20);
    const far = Math.max(weit, ziel * 4, 1000);
    if (Math.abs(kam.near - near) / near > 0.05 || Math.abs(kam.far - far) / far > 0.05) {
      kam.near = near;
      kam.far = far;
      kam.updateProjectionMatrix();
    }
  } else {
    // orthografisch: die Kamera steht fest 200 m vor dem Ziel (ProjectionManager); negatives near
    // zeigt auch, was hinter ihr liegt.
    if (Math.abs(kam.far - weit) / weit > 0.05) {
      kam.near = -weit;
      kam.far = weit;
      kam.updateProjectionMatrix();
    }
  }
}

// Encuadre erst mit Groesse: im Streamlit-iframe ist die Flaeche anfangs 0 px hoch (Seitenverhaeltnis 0/0),
// fitToSphere ergaebe NaN und die Kamera bliebe unbrauchbar. Bis dahin wird der letzte Wunsch aufgehoben.
let ausstehend: (() => Promise<void>) | null = null;

function bereit() {
  const el = welt.renderer!.three.domElement;
  return el.clientWidth > 1 && el.clientHeight > 1;
}

function kameraEndlich() {
  const c = welt.camera.controls;
  const p = c.getPosition(new THREE.Vector3());
  const z = c.getTarget(new THREE.Vector3());
  return [p.x, p.y, p.z, z.x, z.y, z.z, welt.camera.three.zoom].every(Number.isFinite);
}

function nachholen() {
  if (!bereit()) return;
  welt.camera.updateAspect();
  if (!kameraEndlich()) {                               // kaputte Kamera (NaN): neu ausrichten
    welt.camera.controls.reset(false);
    ausstehend ??= () => ansicht("iso", false);
  }
  if (ausstehend) {
    const f = ausstehend;
    ausstehend = null;
    void f();
  }
}

export function einrichten(w: Welt, r: OBC.SimpleGrid | undefined) {
  welt = w;
  raster = r;
  new ResizeObserver(nachholen).observe(w.renderer!.three.domElement);
  const controls = w.camera.controls;
  controls.addEventListener("update", grenzenAnpassen);
  controls.maxDistance = 200000;
  controls.dollySpeed = 1.2;
  w.camera.projection.onChanged.add(() => {
    if (raster) raster.fade = w.camera.projection.current === "Perspective";
    grenzenAnpassen();
  });
  szeneAktualisieren();
}

// ------------------------------------------------------------------ Ansichten
// camera-controls: Azimut 0 = Kamera im Sueden (+z) mit Blick nach Norden, PI/2 = im Osten.
export const ANSICHTEN: Record<string, [number, number]> = {
  iso: [Math.PI / 4, THREE.MathUtils.degToRad(55)],
  oben: [0, 1e-4],
  unten: [0, Math.PI - 1e-4],
  sued: [0, Math.PI / 2],
  nord: [Math.PI, Math.PI / 2],
  ost: [Math.PI / 2, Math.PI / 2],
  west: [-Math.PI / 2, Math.PI / 2],
};

export async function ansicht(art: keyof typeof ANSICHTEN | string, sanft = true) {
  if (!welt) return;
  if (!bereit()) {
    ausstehend = () => ansicht(art, false);
    return;
  }
  const [azimut, polar] = ANSICHTEN[art] ?? ANSICHTEN.iso;
  const c = welt.camera.controls;
  // kuerzester Weg: Azimut auf die Seite des aktuellen Winkels legen
  const jetzt = c.azimuthAngle;
  const ziel = azimut + Math.round((jetzt - azimut) / (2 * Math.PI)) * 2 * Math.PI;
  if (freiLinks > 0) {
    await c.rotateTo(ziel, polar, false);            // erst drehen, dann im freien Bereich einpassen
    await einpassen(undefined, false);
    return;
  }
  await Promise.all([c.rotateTo(ziel, polar, sanft), einpassen(undefined, sanft)]);
}

let freiLinks = 0;

/** Ein Panel deckt links so viele Pixel ab (Lage-Editor): Ansichten zentrieren im freien Bereich. */
export function linksFrei(px: number) {
  freiLinks = Math.max(0, px);
}

/** Kugel (Standard: ganze Szene) formatfuellend zeigen, Blickrichtung bleibt. */
export async function einpassen(k?: THREE.Sphere, sanft = true) {
  if (!welt) return;
  if (!bereit()) {
    ausstehend = () => einpassen(k, false);
    return;
  }
  const s = (k ?? kugel).clone();
  s.radius = Math.max(s.radius, 2);
  const breite = welt.renderer!.three.domElement.clientWidth || 1;
  const frei = freiLinks > 0 && breite - freiLinks > 200 ? freiLinks : 0;
  if (frei) s.radius *= breite / (breite - frei);
  grenzenFuer(s);
  await welt.camera.controls.fitToSphere(s, sanft && !frei);
  if (frei) {
    // Mitte des freien Bereichs: Kamera um eine halbe Panelbreite nach links schieben. update(0) wendet
    // Zoom/Abstand der Einpassung sofort an, sonst misst meterProPixel noch die alte Ansicht.
    welt.camera.controls.update(0);
    await welt.camera.controls.truck(-(frei / 2) * meterProPixel(), 0, false);
    welt.camera.controls.update(0);
  }
}

/** Massstab der Ansicht in der Bildmitte (Meter je Bildschirmpixel). */
export function meterProPixel() {
  const kam = welt.camera.three;
  const h = welt.renderer!.three.domElement.clientHeight || 1;
  if (kam instanceof THREE.OrthographicCamera) return (kam.top - kam.bottom) / kam.zoom / h;
  const d = welt.camera.controls.distance;
  return (2 * d * Math.tan(THREE.MathUtils.degToRad((kam as THREE.PerspectiveCamera).fov) / 2)) / h;
}

/** Vorab grosszuegige Grenzen, damit die Kamerafahrt nichts abschneidet. */
function grenzenFuer(s: THREE.Sphere) {
  const kam = welt.camera.three;
  if (kam instanceof THREE.PerspectiveCamera) {
    kam.far = Math.max(kam.far, s.center.distanceTo(kam.position) + s.radius * 4);
    kam.updateProjectionMatrix();
  }
}

/** Kamera um einen Weg in der Szene mitnehmen: Nullpunkt verschoben (rahmen.ts) oder die Unterlage springt beim
 *  Kalibrieren an eine neue Koordinate - was gezeigt wurde, bleibt im Bild. */
export async function verschieben(dx: number, dz: number, dy = 0) {
  if (!welt || (!dx && !dz && !dy) || ![dx, dy, dz].every(Number.isFinite)) return;
  const c = welt.camera.controls;
  const pos = c.getPosition(new THREE.Vector3());
  const ziel = c.getTarget(new THREE.Vector3());
  await c.setLookAt(pos.x + dx, pos.y + dy, pos.z + dz, ziel.x + dx, ziel.y + dy, ziel.z + dz, false);
  grenzenAnpassen();
}

export async function orbitPunkt(p: THREE.Vector3) {
  const c = welt.camera.controls;
  const min = c.minDistance;
  c.minDistance = 0.01;
  c.setOrbitPoint(p.x, p.y, p.z);
  c.minDistance = min;
}

// ------------------------------------------------------------------ Kamera merken (gleiches Projekt)
export function kameraZustand() {
  const c = welt.camera.controls;
  const pos = c.getPosition(new THREE.Vector3());
  const ziel = c.getTarget(new THREE.Vector3());
  const ortho = welt.camera.projection.current === "Orthographic";
  return { pos: pos.toArray(), ziel: ziel.toArray(), ortho, zoom: welt.camera.three.zoom };
}

export async function kameraSetzen(z: ReturnType<typeof kameraZustand>) {
  if (![...z.pos, ...z.ziel].every(Number.isFinite)) {    // gemerkte Kamera unbrauchbar: Startansicht
    await ansicht("iso", false);
    return;
  }
  if (!bereit()) {
    ausstehend = () => kameraSetzen(z);
    return;
  }
  const c = welt.camera.controls;
  await c.setLookAt(...(z.pos as [number, number, number]), ...(z.ziel as [number, number, number]), false);
  if (z.ortho && welt.camera.projection.current !== "Orthographic") await welt.camera.projection.set("Orthographic");
  if (z.ortho) await c.zoomTo(z.zoom, false);
  grenzenAnpassen();
}
