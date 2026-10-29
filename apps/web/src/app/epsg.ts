// Koordinatensysteme fuer Lageplaene und Bohrkoordinaten (Deutschland, Oesterreich, Schweiz) als Auswahl statt
// freier Zahl. Codes und Namen nach der EPSG-Datenbank (pyproj 3.8); die Wertebereiche sind die Nutzungsgebiete
// (UTM 32N 5,5-15,5 Grad O, 33N 10,5-17,5 Grad O, Gauss-Krueger-Streifen +-1 Grad, CH, AT) in Rechts-/Hochwert, auf
// 10 km gerundet. Sie pruefen nur, ob eine Koordinate zum gewaehlten System passen kann (Ziffernzahl,
// Zonenkennung) - ein Hinweis, keine Sperre.
import { html, nothing } from "lit";

export interface System {
  code: number;
  name: string;
  gruppe: string;
  e: [number, number];                       // Rechtswert von/bis
  n: [number, number];                       // Hochwert von/bis
  hinweis: string;
}

const DE_UTM = "Deutschland · ETRS89 / UTM (amtlich)";
const DE_GK = "Deutschland · Gauß-Krüger (alt)";
export const SYSTEME: System[] = [
  { code: 25832, name: "ETRS89 / UTM Zone 32N", gruppe: DE_UTM, e: [220000, 1010000], n: [5030000, 6140000],
    hinweis: "Rechtswert 6-stellig, die meisten Länder" },
  { code: 25833, name: "ETRS89 / UTM Zone 33N", gruppe: DE_UTM, e: [150000, 700000], n: [5090000, 6130000],
    hinweis: "Rechtswert 6-stellig, Osten (Berlin, Brandenburg, Sachsen, MV)" },
  { code: 4647, name: "ETRS89 / UTM 32N mit Zone (32…)", gruppe: DE_UTM, e: [32230000, 33000000], n: [5200000, 6140000],
    hinweis: "Rechtswert 8-stellig, beginnt mit 32" },
  { code: 5650, name: "ETRS89 / UTM 33N mit Zone (33…)", gruppe: DE_UTM, e: [33150000, 33540000], n: [5200000, 6130000],
    hinweis: "Rechtswert 8-stellig, beginnt mit 33" },
  { code: 31466, name: "DHDN / Gauß-Krüger Zone 2", gruppe: DE_GK, e: [2300000, 2700000], n: [5200000, 6130000],
    hinweis: "Rechtswert 7-stellig, beginnt mit 2" },
  { code: 31467, name: "DHDN / Gauß-Krüger Zone 3", gruppe: DE_GK, e: [3300000, 3700000], n: [5200000, 6130000],
    hinweis: "Rechtswert 7-stellig, beginnt mit 3" },
  { code: 31468, name: "DHDN / Gauß-Krüger Zone 4", gruppe: DE_GK, e: [4300000, 4700000], n: [5200000, 6130000],
    hinweis: "Rechtswert 7-stellig, beginnt mit 4" },
  { code: 31469, name: "DHDN / Gauß-Krüger Zone 5", gruppe: DE_GK, e: [5310000, 5700000], n: [5200000, 6130000],
    hinweis: "Rechtswert 7-stellig, beginnt mit 5" },
  { code: 2398, name: "Krassowski (42/83) / Gauß-Krüger Zone 4", gruppe: DE_GK, e: [4300000, 4700000], n: [5200000, 6130000],
    hinweis: "neue Länder vor ETRS89, Rechtswert beginnt mit 4" },
  { code: 2399, name: "Krassowski (42/83) / Gauß-Krüger Zone 5", gruppe: DE_GK, e: [5300000, 5700000], n: [5200000, 6130000],
    hinweis: "neue Länder vor ETRS89, Rechtswert beginnt mit 5" },
  { code: 3068, name: "DHDN / Soldner Berlin", gruppe: "Deutschland · andere", e: [-40000, 90000], n: [-40000, 80000],
    hinweis: "Berlin, alte Katasterkoordinaten (5-stellig)" },
  { code: 2056, name: "CH1903+ / LV95", gruppe: "Schweiz", e: [2450000, 2870000], n: [1030000, 1340000],
    hinweis: "E 2 xxx xxx, N 1 xxx xxx" },
  { code: 21781, name: "CH1903 / LV03", gruppe: "Schweiz", e: [450000, 870000], n: [30000, 340000],
    hinweis: "Y 6-stellig, X 5–6-stellig (alt)" },
  { code: 31254, name: "MGI / Austria GK West", gruppe: "Österreich", e: [-110000, 170000], n: [110000, 340000],
    hinweis: "Rechtswert um 0 (±), Hochwert ohne 5 000 000" },
  { code: 31255, name: "MGI / Austria GK Central", gruppe: "Österreich", e: [-160000, 170000], n: [90000, 460000],
    hinweis: "Rechtswert um 0 (±), Hochwert ohne 5 000 000" },
  { code: 31256, name: "MGI / Austria GK East", gruppe: "Österreich", e: [-160000, 100000], n: [100000, 480000],
    hinweis: "Rechtswert um 0 (±), Hochwert ohne 5 000 000" },
  { code: 31257, name: "MGI / Austria GK M28 (BMN)", gruppe: "Österreich", e: [40000, 320000], n: [110000, 340000],
    hinweis: "Bundesmeldenetz West" },
  { code: 31258, name: "MGI / Austria GK M31 (BMN)", gruppe: "Österreich", e: [290000, 620000], n: [90000, 460000],
    hinweis: "Bundesmeldenetz Mitte" },
  { code: 31259, name: "MGI / Austria GK M34 (BMN)", gruppe: "Österreich", e: [590000, 850000], n: [100000, 480000],
    hinweis: "Bundesmeldenetz Ost" },
  { code: 32632, name: "WGS 84 / UTM Zone 32N", gruppe: "GPS (WGS 84)", e: [220000, 1010000], n: [5030000, 6140000],
    hinweis: "wie ETRS89 / UTM 32N (Abweichung < 1 m)" },
  { code: 32633, name: "WGS 84 / UTM Zone 33N", gruppe: "GPS (WGS 84)", e: [150000, 700000], n: [5090000, 6130000],
    hinweis: "wie ETRS89 / UTM 33N (Abweichung < 1 m)" },
];

const NACH_CODE = new Map(SYSTEME.map((s) => [s.code, s]));

export function system(code: number | null | undefined) {
  return code ? NACH_CODE.get(code) ?? null : null;
}

/** Kurzer Name fuer Anzeigen ("EPSG 25832 · ETRS89 / UTM Zone 32N"). */
export function systemText(code: number | null | undefined) {
  if (!code) return "ohne System (lokal)";
  const s = system(code);
  return s ? `EPSG ${code} · ${s.name}` : `EPSG ${code} (nicht in der Liste)`;
}

const drin = (s: System, x: number, y: number) => x >= s.e[0] && x <= s.e[1] && y >= s.n[0] && y <= s.n[1];

/** Systeme, zu denen Rechts-/Hochwert passen koennen (ohne WGS-84-Dubletten). */
export function passendeSysteme(x: number | null, y: number | null) {
  if (x === null || y === null || !Number.isFinite(x) || !Number.isFinite(y)) return [];
  return SYSTEME.filter((s) => s.gruppe !== "GPS (WGS 84)" && drin(s, x, y));
}

/** Pruefung einer Koordinate gegen das gewaehlte System: null = nichts zu sagen. */
export function lagePruefen(code: number | null, x: number | null, y: number | null): { ok: boolean; text: string } | null {
  if (x === null || y === null || !Number.isFinite(x) || !Number.isFinite(y)) return null;
  const passend = passendeSysteme(x, y);
  const liste = passend.slice(0, 3).map((s) => `${s.code} (${s.name})`).join(", ");
  if (!code) return passend.length ? { ok: false, text: `Kein System gewählt – die Werte passen zu ${liste}.` } : null;
  const s = system(code);
  if (!s) return { ok: false, text: `EPSG ${code} ist nicht in der Liste – bitte prüfen.` };
  if (drin(s, x, y)) return { ok: true, text: `passt zu EPSG ${code} (${s.hinweis})` };
  return { ok: false, text: passend.length
    ? `Rechts-/Hochwert passen nicht zu EPSG ${code} (${s.hinweis}), aber zu ${liste}.`
    : `Rechts-/Hochwert passen zu keinem System der Liste – Ziffern prüfen (z. B. fehlende Zonenkennung).` };
}

/** Auswahlliste; ein unbekannter Code (aus dem PDF) bleibt sichtbar und markiert, statt zu verschwinden. */
export function epsgAuswahl(code: number | null, aendern: (code: number | null) => void, titel = "Koordinatensystem") {
  const gruppen = [...new Set(SYSTEME.map((s) => s.gruppe))];
  const unbekannt = code !== null && !system(code);
  return html`
    <select class="epsg" aria-label=${titel} title=${systemText(code)}
      @change=${(ev: Event) => { const v = (ev.target as HTMLSelectElement).value; aendern(v === "" ? null : Number(v)); }}>
      <option value="" .selected=${code === null}>– ohne (lokal) –</option>
      ${unbekannt ? html`<option value=${String(code)} .selected=${true}>EPSG ${code} – nicht in der Liste ⚠</option>` : nothing}
      ${gruppen.map((g) => html`
        <optgroup label=${g}>
          ${SYSTEME.filter((s) => s.gruppe === g).map((s) => html`
            <option value=${String(s.code)} .selected=${s.code === code}>${s.code} · ${s.name}</option>`)}
        </optgroup>`)}
    </select>`;
}
