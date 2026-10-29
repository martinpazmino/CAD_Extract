// Datentypen des Viewers und Rueckkanal zur Schritt-App. Der Viewer meldet Aenderungen (Bohrung verschoben,
// Station, GOK, geprueft, Punkt gesetzt oder geloescht) als Ereignis; die App (src/app) schickt sie als Aenderung
// an den Server (ui/projekt.aendern) und gibt den neuen Stand zurueck. Allein (viewer.html) werden sie nur
// protokolliert.
import type { Modus } from "./rahmen";

export interface Nadel {
  id: string;
  code: string;
  x: number | null;                     // Rechtswert bzw. Station (absolut); null = noch ohne Lage
  y: number | null;
  quelle: string;
  gok: number;
  gok_bekannt: boolean;
  gok_pdf?: boolean;                    // GOK steht im PDF: im Schnitt nicht verschiebbar
  ende: number;
  geprueft: boolean;
  schichten_geprueft: number;
  schichten_n: number;
  konfidenz: number | null;
  unklassifiziert?: number;
  offen?: number;                       // nicht klassifizierte, ungepruefte Schichten (Warnung)
  durchmesser?: number;                 // Saeule in m
  im_modell: boolean;
  grund: string;
  schichten: [number, number, string, string?, number?, boolean?][];  // Tiefe oben/unten, Farbe, Bodenart, Konfidenz, geprueft
}

export interface Strecke { u1: number; v1: number; u2: number; v2: number; meter: number }
export type Massstab = Strecke | { n: number };

/** Kalibrierung einer Unterlage (docs/21 §4): Massstab, Bezugspunkt mit Koordinate, Drehung bzw. Hoehenmassstab. */
export interface Kalibrierung {
  massstab: Massstab;
  hoehe?: Massstab | null;              // nur Laengsschnitt; fehlt = wie die Laenge
  bezug: { u: number; v: number; x: number; y: number };   // Bildpixel -> Rechts-/Hochwert bzw. Station/Hoehe
  drehung?: number;                     // Lageplan: Grad gegen Gitternord, gegen den Uhrzeigersinn
  epsg?: number | null;
  gesperrt?: boolean;
}

export interface Unterlage {
  url: string;
  name: string;
  art: "plan" | "schnitt";
  breite: number;
  hoehe: number;
  mm_pro_px: number;
  seite?: number;
  seiten?: number;
  kalibrierung: Kalibrierung | null;
}

/** Freier Punkt auf dem gesperrten Lageplan (noch keiner Bohrung zugeordnet). */
export interface Punkt { id: string; x: number; y: number }

export interface Args {
  ifc?: string | null;
  titel?: string;
  ueberhoehung?: number;
  projekt?: string;
  ursprung?: [number, number] | null;
  epsg?: number | null;
  modus?: Modus;
  bohrungen?: Nadel[] | null;
  unterlage?: Unterlage | null;
  punkte?: Punkt[] | null;
}

let nr = 0;
let projekt = "";
let empfaenger: ((e: Record<string, unknown>) => void) | null = null;
export const protokoll: Record<string, unknown>[] = [];

/** Signatur des angezeigten Projekts: jedes Ereignis traegt sie. */
export function projektSetzen(signatur: string) {
  projekt = signatur;
}

/** Die Schritt-App empfaengt die Ereignisse; ohne Empfaenger (viewer.html) nur fuer die Pruefungen protokolliert. */
export function empfaengerSetzen(f: ((e: Record<string, unknown>) => void) | null) {
  empfaenger = f;
}

export function mitApp() {
  return empfaenger !== null;
}

export function ereignis(daten: Record<string, unknown>) {
  nr += 1;
  const wert = { ...daten, nr, projekt };
  protokoll.push(wert);
  empfaenger?.(wert);
  return wert;
}
