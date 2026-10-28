// Streamlit-Komponente ohne streamlit-component-lib: dasselbe Nachrichtenprotokoll (ui/viewer.py).
// Python -> Viewer: "streamlit:render" mit args. Viewer -> Python: Ereignisse mit laufender Nummer "nr";
// ui/projekt.ereignis_anwenden wendet jede Nummer nur einmal an (Streamlit liefert den letzten Wert bei
// jedem Rerun erneut). Python schickt die zuletzt angewendete Nummer zurueck, damit ein neu eingehaengter
// Viewer nicht wieder bei 1 anfaengt.
import type { Modus } from "./rahmen";

export interface Nadel {
  id: string;
  code: string;
  x: number | null;                     // Rechtswert bzw. Station (absolut); null = noch ohne Lage
  y: number | null;
  quelle: string;
  gok: number;
  gok_bekannt: boolean;
  ende: number;
  geprueft: boolean;
  schichten_geprueft: number;
  schichten_n: number;
  konfidenz: number | null;
  im_modell: boolean;
  grund: string;
  schichten: [number, number, string, string?, number?, boolean?][];  // Tiefe oben/unten, Farbe, Bodenart, Konfidenz, geprueft
}

export interface Passpunkt {
  u: number;                            // Pixel im Bild (nach rechts)
  v: number;                            // Pixel im Bild (nach unten)
  x: number;                            // Rechtswert bzw. Station
  y: number;                            // Hochwert bzw. Hoehe m NHN
}

export interface Unterlage {
  url: string;
  name: string;
  art: "plan" | "schnitt";
  breite: number;
  hoehe: number;
  mm_pro_px: number;
  kalibrierung: { punkte: Passpunkt[]; epsg?: number | null } | null;
}

export interface Args {
  ifc?: string | null;
  titel?: string;
  hoehe?: number;
  ueberhoehung?: number;
  projekt?: string;
  ursprung?: [number, number] | null;
  epsg?: number | null;
  modus?: Modus;
  bohrungen?: Nadel[] | null;
  unterlage?: Unterlage | null;
  nr?: number;
  bearbeiten?: number;                  // Zaehler: jede Erhoehung schaltet den Lage-Modus ein
}

const parameter = new URLSearchParams(location.search);
export const eingebettet = parameter.has("streamlitUrl");

function senden(type: string, daten: Record<string, unknown> = {}) {
  window.parent.postMessage({ isStreamlitMessage: true, type, ...daten }, "*");
}

let nr = 0;
let projekt = "";

/** Signatur des angezeigten Projekts: jedes Ereignis traegt sie (Python verwirft fremde). */
export function projektSetzen(signatur: string) {
  projekt = signatur;
}

export function nrMindestens(n: number) {
  nr = Math.max(nr, Math.floor(n || 0));
}

/** Ereignis an Python; ohne Streamlit nur fuer die Pruefungen protokolliert. */
export function ereignis(daten: Record<string, unknown>) {
  nr += 1;
  const wert = { ...daten, nr, projekt };
  protokoll.push(wert);
  if (eingebettet) senden("streamlit:setComponentValue", { value: wert, dataType: "json" });
  return wert;
}

export const protokoll: Record<string, unknown>[] = [];

export function hoeheSetzen(px: number) {
  if (eingebettet) senden("streamlit:setFrameHeight", { height: px });
}

// Handshake sofort beim Laden (vor dem Einrichten der Welt); Argumente bis zum Start puffern
let wartend: Args | null = null;
let verarbeiter: ((a: Args) => void) | null = null;
if (eingebettet) {
  window.addEventListener("message", (ev) => {
    if (ev.data?.type !== "streamlit:render") return;
    const a = (ev.data.args ?? {}) as Args;
    if (verarbeiter) verarbeiter(a);
    else wartend = a;
  });
  senden("streamlit:setFrameHeight", { height: 760 });
  senden("streamlit:componentReady", { apiVersion: 1 });
}

export function starten(beiArgs: (a: Args) => void) {
  if (!eingebettet) return;
  verarbeiter = beiArgs;
  if (wartend) {
    const a = wartend;
    wartend = null;
    beiArgs(a);
  }
}
