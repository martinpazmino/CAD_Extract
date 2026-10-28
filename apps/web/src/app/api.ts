// Schnittstelle zum Server (server/api.py). Alle Aenderungen gehen als Liste von Operationen an
// /api/projekt/<signatur>/aendern (ui/projekt.aendern); die Antwort ist der neue Stand des Projekts.
import type { Kalibrierung, Nadel, Unterlage } from "../viewer/kanal";

export interface Bohrung {
  id: string; code: string; dokument: string; seite: number;
  modell: boolean; entfernt: boolean; geprueft: boolean;
  gok: number | null; gok_pdf: boolean; gok_quelle: string; endteufe: number | null;
  x: number | null; y: number | null; epsg: number | null; lage_aus: string;
  schichten_n: number; schichten_geprueft: number; unklassifiziert: number; offen: number; korrigiert: number;
  konfidenz_min: number | null; grundwasser: string; durchmesser: number | null; doppelt_in: string | null;
  hinweise: string[];
}

export interface Norm {
  benennung: string; din4023: string; iso14688: string; bodengruppe: string | null; konsistenz: string | null;
  lagerung: string | null; kalk: string | null; feuchte: string | null; bodenfarbe: string | null;
  klasse: string | null; farbe: string; farbname: string; sicher: boolean; hinweise: string[];
}

export interface Schicht {
  k: number; von: number; bis: number; bodenart: string; farbe: string;
  geprueft: boolean; korrigiert: boolean; unklassifiziert: boolean; offen: boolean;
  konfidenz: number | null; beschreibung: string; hinweise: string[];
  quelle: { dokument: string; seite: number; bbox: number[] | null; methode: string | null };
  norm: Norm;
  vorschlag: { klasse: string; benennung: string; din4023: string; sicher: boolean; hinweise: string[] } | null;
}

export interface Klasse { klasse: string; name: string; art: string; farbe: string; farbname: string; din4023: string; iso14688: string; beleg: string }

export interface Eincheckung {
  nr: number; zeit: string; modell: string | null; kommentar: string;
  stand: { bohrungen: [number, number]; schichten: [number, number]; unklassifiziert?: number; unklassifiziert_offen?: number;
           korrigiert: number; manuelle_lage: number; entfernt?: number };
}

export interface Pruefstand {
  bohrungen: [number, number]; schichten: [number, number]; unklassifiziert: number; unklassifiziert_offen: number;
  korrigiert: number; manuelle_lage: number; entfernt: number;
}

export interface ReiheZeile { id: string; nr: number; code: string; abstand: number | null; station: number; quelle: string; quelle_text: string }

export interface Einstellungen { methode: string; puffer: number | null; raster: number | null; basis: number | null; gok_relativ: boolean }

export interface Zustand {
  signatur: string; name: string; version: number; schritt: string;
  dokumente: { index: number; datei: string; seiten: number | null; pdf: boolean }[];
  lage_modus: "koordinaten" | "reihe"; erzeugt: boolean; auto: boolean;
  durchmesser: number | null; durchmesser_auto: number; ueberhoehung: number;
  einstellungen: Einstellungen;
  unterlage: (Unterlage & { seite: number; seiten: number; sha: string }) | null;
  reihe: ReiheZeile[]; reihe_standard: number;
  vorgabe: { name: string; bodenarten: string[] }[] | null;
  eincheckungen: Eincheckung[]; pruefstand: Pruefstand; eingecheckt: string | null; seit_einchecken_geaendert: boolean;
  bohrungen: Bohrung[]; klassen: Klasse[];
  hinweise: string[]; nicht_im_modell: { id?: string; code: string; dokument: string; grund: string }[];
  modell: { schluessel: string; aktuell: boolean; ifc: string | null };
  viewer: { bohrungen: Nadel[]; ursprung: [number, number]; epsg: number | null; modus: "koordinaten" | "reihe" };
}

export interface EinheitBericht {
  name: string; bodenarten: string[]; farbe: string; volumen_m3: number; maechtigkeit_max_m: number; geschlossen: boolean;
  bohrungen: { vorhanden: string[]; fehlt: string[]; unbekannt: string[] };
  schichten: { bohrung: string; von: number; bis: number; bodenart: string | null; beschreibung: string }[];
  hinweise: string[];
}

export interface Bericht {
  epsg: number | null; ursprung: [number, number]; parameter: Record<string, number | string>;
  einheiten: EinheitBericht[];
  bohrungen: { code: string; x: number; y: number; gok: number; lage: string; hoehe: string; endteufe_nhn: number;
               einheiten: { einheit: string; status: string; ok_modell: number; uk_modell: number }[]; hinweise: string[] }[];
  ausgeschlossen: { code: string; dokument: string; grund: string }[];
  pruefungen: { max_abweichung_an_bohrungen_m: number; alle_koerper_geschlossen: boolean };
  hinweise: string[];
  vorlage_einheiten: { name: string; bodenarten: string[] }[];
}

export interface ModellErgebnis {
  schluessel: string; fehler: string; bericht: Bericht | null; ifc: string | null;
  hinweise: string[]; nicht_im_modell: { code: string; dokument: string; grund: string }[]; zustand: Zustand;
}

export interface Auftrag {
  id: string; dateien: string[]; fertig: boolean; fehler: string[]; projekt: string | null;
  stand: { datei: string; nr: number; dateien: number; seite: number; seiten: number; klasse: string };
}

export interface ProjektKurz {
  signatur: string; name: string; dokumente: string[]; bohrungen: number; geprueft: number; eincheckungen: number;
  geaendert: string; schritt: string;
}

export type Op = Record<string, unknown> & { op: string };
export type { Kalibrierung };

async function anfrage<T>(pfad: string, init?: RequestInit): Promise<T> {
  const r = await fetch(pfad, init);
  if (!r.ok) {
    let text = `${r.status} ${r.statusText}`;
    try {
      const j = await r.json();
      text = typeof j.detail === "string" ? j.detail : JSON.stringify(j.detail);
    } catch { /* kein JSON */ }
    throw new Error(text);
  }
  return (await r.json()) as T;
}

const json = (daten: unknown): RequestInit => ({ method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(daten) });

export const api = {
  info: () => anfrage<{ version: string; ocr: boolean; beispiele: { name: string; titel: string }[] }>("/api/info"),
  projekte: () => anfrage<ProjektKurz[]>("/api/projekte"),
  beispiel: (name: string) => anfrage<{ projekt?: string; auftrag?: string }>("/api/beispiel", json({ name })),
  gutachten(dateien: File[], ocr: boolean) {
    const f = new FormData();
    for (const d of dateien) f.append("dateien", d, d.name);
    f.append("ocr", String(ocr));
    return anfrage<Auftrag>("/api/gutachten", { method: "POST", body: f });
  },
  auftrag: (id: string) => anfrage<Auftrag>(`/api/auftrag/${id}`),
  zustand: (sig: string) => anfrage<Zustand>(`/api/projekt/${sig}`),
  aendern: (sig: string, ops: Op[]) => anfrage<{ meldungen: string[]; zustand: Zustand }>(`/api/projekt/${sig}/aendern`, json({ ops })),
  zuruecksetzen: (sig: string) => anfrage<Zustand>(`/api/projekt/${sig}/zuruecksetzen`, { method: "POST" }),
  loeschen: (sig: string) => anfrage<{ ok: boolean }>(`/api/projekt/${sig}`, { method: "DELETE" }),
  bohrung: (sig: string, bid: string) => anfrage<{ bohrung: Bohrung; schichten: Schicht[] }>(`/api/projekt/${sig}/bohrung/${encodeURIComponent(bid)}`),
  seite: (sig: string, dokument: number, seite: number) =>
    anfrage<{ url: string; px_je_pt: number; breite_pt: number; hoehe_pt: number; seite: number; seiten: number | null }>(
      `/api/projekt/${sig}/seite/${dokument}/${seite}`),
  unterlage(sig: string, datei: File, art: string, seite: number) {
    const f = new FormData();
    f.append("datei", datei, datei.name);
    f.append("art", art);
    f.append("seite", String(seite));
    return anfrage<Zustand>(`/api/projekt/${sig}/unterlage`, { method: "POST", body: f });
  },
  unterlageSeite: (sig: string, seite: number, art: string) => anfrage<Zustand>(`/api/projekt/${sig}/unterlage/seite`, json({ seite, art })),
  unterlageEntfernen: (sig: string) => anfrage<Zustand>(`/api/projekt/${sig}/unterlage`, { method: "DELETE" }),
  modell: (sig: string) => anfrage<ModellErgebnis>(`/api/projekt/${sig}/modell`, { method: "POST" }),
  einchecken: (sig: string, kommentar: string) => anfrage<{ eintrag: Eincheckung; zustand: Zustand }>(`/api/projekt/${sig}/einchecken`, json({ kommentar })),
  exportUrl: (sig: string, art: string) => `/api/projekt/${sig}/export/${art}`,
};
