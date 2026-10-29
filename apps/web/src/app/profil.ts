// Bohrsaeulen als SVG: eine Bohrung mit ihren Schichten (Schritt Bohrungen) und alle Bohrungen nach Einheiten auf
// gemeinsamer Hoehe (Schritt Einheiten). Farben nach DIN 4023 kommen vom Server (Normen-Datenbank).
import { html, svg, nothing } from "lit";
import type { Bericht } from "./api";

export interface Saeulenschicht {
  k: number;
  von: number;
  bis: number;
  farbe: string;
  titel: string;
  warn?: boolean;
  geprueft?: boolean;
}

const zahl = (v: number, s = 2) => v.toLocaleString("de-DE", { minimumFractionDigits: s, maximumFractionDigits: s });

function schritt(spanne: number) {
  for (const s of [0.5, 1, 2, 5, 10, 20, 50, 100]) if (spanne / s <= 12) return s;
  return 200;
}

/** Eine Bohrsaeule (Tiefe nach unten); Klick waehlt eine Schicht. */
export function saeule(sch: Saeulenschicht[], opt: { hoehe: number; gewaehlt?: number; waehlen?: (k: number) => void }) {
  const ende = Math.max(1, ...sch.map((s) => s.bis));
  const oben = 12;
  const m = (opt.hoehe - oben - 14) / ende;
  const x0 = 34;
  const b = 46;
  const st = schritt(ende);
  const marken = [];
  for (let t = 0; t <= ende + 1e-9; t += st) marken.push(t);
  return html`<svg class="saeule" viewBox="0 0 150 ${opt.hoehe}" width="150" height=${opt.hoehe} role="img" aria-label="Bohrsäule">
    <defs>
      <pattern id="schraffur-warn" width="6" height="6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)">
        <rect width="6" height="6" fill="#e6e6e6"></rect><line x1="0" y1="0" x2="0" y2="6" stroke="#f0a33a" stroke-width="3"></line>
      </pattern>
    </defs>
    ${marken.map((t) => svg`
      <line x1=${x0 - 5} x2=${x0} y1=${oben + t * m} y2=${oben + t * m} class="achse"></line>
      <text x=${x0 - 7} y=${oben + t * m + 3} class="achse-text" text-anchor="end">${zahl(t, st < 1 ? 1 : 0)}</text>`)}
    <line x1=${x0} x2=${x0} y1=${oben} y2=${oben + ende * m} class="achse"></line>
    ${sch.map((s) => svg`
      <g class=${`schicht ${s.k === opt.gewaehlt ? "gewaehlt" : ""} ${s.warn ? "warn" : ""}`} @click=${() => opt.waehlen?.(s.k)}>
        <title>${s.titel}</title>
        <rect x=${x0 + 4} y=${oben + s.von * m} width=${b} height=${Math.max(1, (s.bis - s.von) * m)}
          fill=${s.warn ? "url(#schraffur-warn)" : s.farbe}></rect>
        ${s.geprueft ? svg`<text x=${x0 + b + 9} y=${oben + ((s.von + s.bis) / 2) * m + 4} class="haken">✓</text>` : nothing}
        ${(s.bis - s.von) * m > 11 ? svg`<text x=${x0 + b + 22} y=${oben + s.bis * m - 2} class="tiefe">${zahl(s.bis)}</text>` : nothing}
      </g>`)}
  </svg>`;
}

/** Alle Bohrungen des Modells nebeneinander in m NHN, gefaerbt nach Modelleinheit (Ober-/Unterkante aus dem Modell). */
export function einheitenProfil(bericht: Bericht, opt: { hoehe: number; gewaehlt?: string; waehlen?: (name: string) => void }) {
  const bohr = [...bericht.bohrungen].sort((a, b) => a.x - b.x || a.y - b.y);
  if (!bohr.length) return nothing;
  const farbe = new Map(bericht.einheiten.map((e) => [e.name, e.farbe]));
  const zmax = Math.max(...bohr.map((b) => b.gok));
  const zmin = Math.min(...bohr.map((b) => b.endteufe_nhn));
  const oben = 22;
  const links = 44;
  const spalte = Math.max(38, Math.min(70, 900 / bohr.length));
  const breite = links + bohr.length * spalte + 10;
  const m = (opt.hoehe - oben - 10) / Math.max(1, zmax - zmin);
  const y = (z: number) => oben + (zmax - z) * m;
  const st = schritt(zmax - zmin);
  const marken = [];
  for (let z = Math.ceil(zmin / st) * st; z <= zmax + 1e-9; z += st) marken.push(z);
  return html`<svg class="einheitenprofil" viewBox="0 0 ${breite} ${opt.hoehe}" width=${breite} height=${opt.hoehe} role="img"
      aria-label="Einheiten je Bohrung">
    ${marken.map((z) => svg`
      <line x1=${links - 4} x2=${breite} y1=${y(z)} y2=${y(z)} class="raster"></line>
      <text x=${links - 6} y=${y(z) + 3} class="achse-text" text-anchor="end">${zahl(z, st < 1 ? 1 : 0)}</text>`)}
    ${bohr.map((b, i) => {
      const x = links + i * spalte + spalte * 0.2;
      const w = spalte * 0.6;
      return svg`
        <text x=${x + w / 2} y=${oben - 8} class="code" text-anchor="middle">${b.code}</text>
        ${b.einheiten.filter((e) => e.status === "vorhanden" && e.ok_modell - e.uk_modell > 1e-3).map((e) => svg`
          <rect x=${x} y=${y(e.ok_modell)} width=${w} height=${Math.max(0.8, (e.ok_modell - e.uk_modell) * m)}
            fill=${farbe.get(e.einheit) ?? "#ccc"} class=${`einheit ${opt.gewaehlt === e.einheit ? "gewaehlt" : ""}`}
            @click=${() => opt.waehlen?.(e.einheit)}>
            <title>${b.code}: ${e.einheit} ${zahl(e.ok_modell)} bis ${zahl(e.uk_modell)} m NHN</title>
          </rect>`)}
        <line x1=${x - 3} x2=${x + w + 3} y1=${y(b.endteufe_nhn)} y2=${y(b.endteufe_nhn)} class="endteufe"></line>`;
    })}
  </svg>`;
}
