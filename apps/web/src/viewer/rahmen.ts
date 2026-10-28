// Lagebezug des Viewers. three.js: x = Osten, y = oben, -z = Norden, alles lokal zum Projektursprung
// (e0, n0) wie das IFC aus services/modeler (Koordinaten relativ zum Ursprung, IfcMapConversion).
// Ueberhoehung um eine feste Bezugshoehe: y = bezug + (NHN - bezug) * faktor.
// Im Modus "reihe" (Laengsschnitt) ist die Ost-Achse die Station, Norden ist 0.
import * as THREE from "three";

export type Modus = "koordinaten" | "reihe";

export const rahmen = {
  e0: 0,
  n0: 0,
  bezug: 0,
  faktor: 1,
  modus: "koordinaten" as Modus,
  epsg: null as number | null,
};

export function zuSzene(e: number, n: number, h: number, ziel = new THREE.Vector3()) {
  return ziel.set(e - rahmen.e0, hoeheZuSzene(h), -(n - rahmen.n0));
}

export const hoeheZuSzene = (h: number) => rahmen.bezug + (h - rahmen.bezug) * rahmen.faktor;
export const hoeheAusSzene = (y: number) => rahmen.bezug + (y - rahmen.bezug) / rahmen.faktor;

export function ausSzene(p: THREE.Vector3) {
  return { e: p.x + rahmen.e0, n: -p.z + rahmen.n0, h: hoeheAusSzene(p.y) };
}

const zahl = (v: number, stellen = 2) =>
  v.toLocaleString("de-DE", { minimumFractionDigits: stellen, maximumFractionDigits: stellen });

/** Anzeige eines Szenenpunkts in Landeskoordinaten bzw. Station (Reihe). */
export function koordinatenText(p: THREE.Vector3) {
  const { e, n, h } = ausSzene(p);
  const hoehe = `${zahl(h)} m NHN`;
  if (rahmen.modus === "reihe") return `Station ${zahl(e)} m · ${hoehe}`;
  const system = rahmen.epsg ? ` · EPSG ${rahmen.epsg}` : "";
  return `R ${zahl(e)} · H ${zahl(n)} · ${hoehe}${system}`;
}
