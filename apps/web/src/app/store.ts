// Zustand der Schritt-App und alle Aktionen: Projekt laden, Aenderungen an den Server, Modell rechnen, Viewer
// nachfuehren. Die Oberflaeche (start.ts, schritt_*.ts) liest S und ruft die Aktionen; nach jeder Aktion wird neu
// gezeichnet. Der Viewer (src/viewer) entsteht beim ersten Schritt, der ihn braucht, und bleibt dann bestehen.
import { api, type Bohrung, type ModellErgebnis, type Op, type Schicht, type Zustand } from "./api";
import type { Kalibrierung } from "../viewer/kanal";
import type { ViewerApi } from "../viewer/viewer";

export const SCHRITTE = [
  { id: "gutachten", nr: 1, titel: "Gutachten", kurz: "PDF hochladen" },
  { id: "bohrungen", nr: 2, titel: "Bohrungen", kurz: "prüfen und korrigieren" },
  { id: "lage", nr: 3, titel: "Lage", kurz: "Plan, Bezugspunkt, Bohrungen setzen" },
  { id: "einheiten", nr: 4, titel: "Einheiten", kurz: "Schichten verbinden" },
  { id: "modell", nr: 5, titel: "Modell", kurz: "3D-Modell, einchecken, Export" },
] as const;
export type SchrittId = (typeof SCHRITTE)[number]["id"];

export interface Meldung { id: number; text: string; art: "" | "ok" | "warn" | "fehler" }

export const S = {
  info: null as Awaited<ReturnType<typeof api.info>> | null,
  projekte: [] as Awaited<ReturnType<typeof api.projekte>>,
  sig: "",
  z: null as Zustand | null,
  schritt: "gutachten" as SchrittId,
  bid: "",                                            // gewaehlte Bohrung (Schritt Bohrungen)
  details: new Map<string, { bohrung: Bohrung; schichten: Schicht[] }>(),
  k: -1,                                              // gewaehlte Schicht
  modell: null as ModellErgebnis | null,
  rechnet: false,
  beschaeftigt: "",                                   // Text fuer die Ladeanzeige
  auftrag: null as Awaited<ReturnType<typeof api.auftrag>> | null,
  meldungen: [] as Meldung[],
  entwurf: null as Kalibrierung | null,               // Kalibrierung in Arbeit (Schritt Lage)
  punktModus: false,                                  // Schritt Lage: Klick in den gesperrten Plan setzt einen Punkt
  naechste: "",                                       // Bohrung, die der naechste Punkt bekommt ("" = freier Punkt)
  filter: "",
  viewer: null as ViewerApi | null,
};

let zeichnen: () => void = () => {};
export function zeichnenSetzen(f: () => void) {
  zeichnen = f;
}
export function neu() {
  zeichnen();
}

let meldungNr = 0;
export function melden(text: string, art: Meldung["art"] = "", dauer = 4500) {
  const m = { id: ++meldungNr, text, art };
  S.meldungen = [...S.meldungen.slice(-3), m];
  neu();
  window.setTimeout(() => {
    S.meldungen = S.meldungen.filter((x) => x.id !== m.id);
    neu();
  }, dauer);
}

export async function versuchen<T>(f: () => Promise<T>, beschaeftigt = ""): Promise<T | undefined> {
  if (beschaeftigt) {
    S.beschaeftigt = beschaeftigt;
    neu();
  }
  try {
    return await f();
  } catch (err) {
    melden(String((err as Error).message ?? err), "fehler", 8000);
    return undefined;
  } finally {
    if (beschaeftigt) {
      S.beschaeftigt = "";
      neu();
    }
  }
}

// ------------------------------------------------------------------ Navigation (Adresse: #/<signatur>/<schritt>/<bohrung>)
export function adresse() {
  const teile = [S.sig, S.schritt !== "gutachten" || S.sig ? S.schritt : "", S.schritt === "bohrungen" ? S.bid : ""];
  const ziel = `#/${teile.filter(Boolean).map(encodeURIComponent).join("/")}`;
  if (location.hash !== ziel) history.replaceState(null, "", ziel);
}

export async function oeffnen(sig: string, schritt?: SchrittId) {
  const z = await versuchen(() => api.zustand(sig), "Projekt wird geladen …");
  if (!z) return;
  S.sig = sig;
  S.z = z;
  S.details.clear();
  S.modell = null;
  S.entwurf = null;
  S.bid = "";
  await gehe(schritt ?? ((z.schritt as SchrittId) || "bohrungen"));
}

export async function gehe(schritt: SchrittId) {
  if (schritt !== "gutachten" && !S.sig) schritt = "gutachten";
  const vorher = S.schritt;
  S.schritt = schritt;
  if (schritt !== "lage") S.punktModus = false;
  if (schritt === "gutachten") void projekteLaden();
  if (schritt === "bohrungen" && S.z && !S.bid) S.bid = naechsteOffene(-1) ?? S.z.bohrungen[0]?.id ?? "";
  if (S.sig && vorher !== schritt) void api.aendern(S.sig, [{ op: "schritt", wert: schritt }]).catch(() => {});
  adresse();
  neu();
  if (schritt === "bohrungen" && S.bid) await detailLaden(S.bid);
  if (schritt === "einheiten" || schritt === "modell") await modellRechnen();
  await viewerSchritt();
}

export async function projekteLaden() {
  S.projekte = (await versuchen(() => api.projekte())) ?? [];
  neu();
}

// ------------------------------------------------------------------ Aenderungen
export async function aendern(ops: Op[], { leise = false } = {}) {
  if (!S.sig) return;
  const r = await versuchen(() => api.aendern(S.sig, ops));
  if (!r) {
    // Fehler: Stand vom Server neu holen (Eingabefelder zeigen wieder den gueltigen Wert)
    S.z = (await versuchen(() => api.zustand(S.sig))) ?? S.z;
    neu();
    await viewerAktualisieren();
    return false;
  }
  zustandUebernehmen(r.zustand);
  if (!leise) for (const m of r.meldungen) melden(m, "ok", 2500);
  neu();
  await nachAenderung();
  return true;
}

export function zustandUebernehmen(z: Zustand) {
  S.z = z;
  S.details.clear();                                    // Schichten (geprueft, Bodenart) neu holen
}

async function nachAenderung() {
  if (S.schritt === "bohrungen" && S.bid) await detailLaden(S.bid);
  if ((S.schritt === "einheiten" || S.schritt === "modell") && S.z?.auto) await modellRechnen();
  await viewerAktualisieren();
}

export async function detailLaden(bid: string) {
  if (!S.sig || !bid) return;
  if (!S.details.has(bid)) {
    const d = await versuchen(() => api.bohrung(S.sig, bid));
    if (!d) return;
    S.details.set(bid, d);
  }
  neu();
}

/** Bohrung waehlen (Schritt Bohrungen); die Schichten kommen aus dem Speicher oder vom Server. */
export async function bohrungWaehlen(bid: string) {
  if (!bid) return;
  S.bid = bid;
  S.k = -1;
  adresse();
  neu();
  await detailLaden(bid);
  vorladen(bid);
}

/** Nachbarn im Voraus laden: Blaettern ohne Wartezeit. */
function vorladen(bid: string) {
  const ids = sichtbareBohrungen().map((b) => b.id);
  const i = ids.indexOf(bid);
  for (const n of [ids[i + 1], ids[i - 1]]) {
    if (n && !S.details.has(n)) void api.bohrung(S.sig, n).then((d) => S.details.set(n, d)).catch(() => {});
  }
}

export function sichtbareBohrungen(): Bohrung[] {
  const alle = S.z?.bohrungen ?? [];
  const f = S.filter.trim().toLowerCase();
  return alle.filter((b) => !b.entfernt && (!f || b.code.toLowerCase().includes(f)));
}

export function naechsteOffene(abIndex: number): string | undefined {
  const liste = sichtbareBohrungen();
  const offen = (b: Bohrung) => b.schichten_geprueft < b.schichten_n || (b.offen > 0 && !b.geprueft);
  const danach = liste.slice(abIndex + 1).find(offen);
  return (danach ?? liste.find(offen))?.id;
}

// ------------------------------------------------------------------ Modell
let rechnenLaeuft: Promise<void> | null = null;
let nochmal = false;

/** Modell rechnen (Server-Cache); bei Aenderungen waehrend des Rechnens einmal nachrechnen. */
export async function modellRechnen() {
  if (!S.sig) return;
  if (rechnenLaeuft) {
    nochmal = true;
    return rechnenLaeuft;
  }
  rechnenLaeuft = (async () => {
    do {
      nochmal = false;
      S.rechnet = true;
      neu();
      const m = await versuchen(() => api.modell(S.sig));
      S.rechnet = false;
      if (m) {
        S.modell = m;
        S.z = m.zustand;
        if (m.fehler) melden(`Noch kein Modell: ${m.fehler}`, "warn", 7000);
      }
      neu();
      await viewerAktualisieren();
    } while (nochmal);
  })();
  try {
    await rechnenLaeuft;
  } finally {
    rechnenLaeuft = null;
  }
}

// ------------------------------------------------------------------ Viewer
let viewerStart: Promise<ViewerApi> | null = null;

async function viewerHolen(): Promise<ViewerApi> {
  if (S.viewer) return S.viewer;
  viewerStart ??= (async () => {
    const { viewerStarten } = await import("../viewer/viewer");
    const v = await viewerStarten(document.getElementById("buehne")!, {
      ereignis: (e) => void viewerEreignis(e),
      leerText: "Noch keine Bohrung mit Lage.",
    });
    S.viewer = v;
    return v;
  })();
  return viewerStart;
}

async function viewerEreignis(e: Record<string, unknown>) {
  const { typ, nr: _nr, projekt: _p, ...rest } = e;
  if (typ === "punkt") {
    await punktGesetzt(Number(rest.x), Number(rest.y));
    return;
  }
  const op = typ === "geprueft" ? { op: "geprueft", id: rest.id, wert: rest.wert } : { op: String(typ), ...rest };
  await aendern([op as Op]);
}

/** Klick in den gesperrten Plan: die gewaehlte Bohrung bekommt die Lage (danach ist die naechste ohne Lage dran),
 *  ohne Wahl entsteht ein freier Punkt. */
export async function punktGesetzt(x: number, y: number) {
  const ziel = S.naechste;
  if (await aendern([{ op: "punkt", x, y, bohrung: ziel || null }]) && ziel) {
    S.naechste = naechsteOhneLage(ziel);
    neu();
  }
}

/** Naechste Bohrung ohne Lage in der Reihenfolge der Liste nach 'nach' ("" = keine mehr). */
export function naechsteOhneLage(nach = ""): string {
  const ohne = (S.z?.viewer.bohrungen ?? []).filter((b) => b.x === null).map((b) => b.id).filter((id) => id !== nach);
  const alle = (S.z?.viewer.bohrungen ?? []).map((b) => b.id);
  const ab = alle.indexOf(nach);
  return ohne.find((id) => alle.indexOf(id) > ab) ?? ohne[0] ?? "";
}

/** Viewer an den Schritt anpassen: Lage-Modus im Schritt Lage, Modell im Schritt Modell. */
export async function viewerSchritt() {
  const braucht = S.schritt === "lage" || S.schritt === "modell";
  if (!braucht || !S.z) return;
  const v = await viewerHolen();
  v.seitenleiste(S.schritt === "modell");
  await new Promise((r) => requestAnimationFrame(() => r(null)));
  v.groesseGeaendert();
  await viewerAktualisieren();
  await v.lageModus(S.schritt === "lage");
}

export async function viewerAktualisieren() {
  const v = S.viewer;
  const z = S.z;
  if (!v || !z || (S.schritt !== "lage" && S.schritt !== "modell")) return;
  const ifc = S.modell && !S.modell.fehler && S.modell.zustand.modell.schluessel === z.modell.schluessel ? S.modell.ifc
    : z.modell.ifc;
  await v.setzen({
    projekt: z.signatur, titel: z.name, ueberhoehung: z.ueberhoehung, ursprung: z.viewer.ursprung, epsg: z.viewer.epsg,
    modus: z.viewer.modus, bohrungen: z.viewer.bohrungen, unterlage: z.unterlage, ifc: ifc ?? null,
    punkte: z.viewer.punkte ?? [],
  });
  if (S.schritt === "lage") v.editor.vorschau(S.entwurf ?? undefined);
}
