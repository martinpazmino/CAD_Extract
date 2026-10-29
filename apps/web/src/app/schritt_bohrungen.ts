// Schritt 2 · Bohrungen pruefen und korrigieren: Liste links (Zustand, Warnung, entfernen), Schichten der gewaehlten
// Bohrung mit Deutung nach Norm, rechts Saeule und die Seite des Gutachtens mit der Schicht markiert.
// Blaettern: Pfeiltasten oder J/K, N = naechste offene, G = alle Schichten geprueft und weiter.
import { html, nothing } from "lit";
import { live } from "lit/directives/live.js";
import { api, type Bohrung, type Schicht } from "./api";
import { hilfe } from "./hilfe";
import { epsgAuswahl, lagePruefen } from "./epsg";
import { saeule } from "./profil";
import { S, aendern, bohrungWaehlen, naechsteOffene, neu, sichtbareBohrungen, versuchen } from "./store";

const zahl = (v: number | null | undefined, s = 2) =>
  v === null || v === undefined ? "" : v.toLocaleString("de-DE", { minimumFractionDigits: s, maximumFractionDigits: s });
const wert = (e: Event) => {
  const t = (e.target as HTMLInputElement).value.trim().replace(",", ".");
  return t === "" ? null : Number(t);
};

const ARTEN: [string, string][] = [["boden", "Böden"], ["organisch", "Organisch"], ["geologisch", "Geologische Benennung"],
                                   ["fels", "Fels"], ["anthropogen", "Anthropogen"], ["unbekannt", "Nicht klassifiziert"]];

let seitenbild: { schluessel: string; daten: Awaited<ReturnType<typeof api.seite>> } | null = null;
let seiteLaedt = "";
let zoom = 0.5;
let entfernteOffen = false;

// ------------------------------------------------------------------ Aktionen
function nachbar(richtung: 1 | -1) {
  const liste = sichtbareBohrungen();
  const i = liste.findIndex((b) => b.id === S.bid);
  const n = liste[Math.min(liste.length - 1, Math.max(0, i + richtung))];
  if (n) void bohrungWaehlen(n.id);
}

function naechsteOffeneWaehlen() {
  const liste = sichtbareBohrungen();
  const id = naechsteOffene(liste.findIndex((b) => b.id === S.bid));
  if (id) void bohrungWaehlen(id);
}

async function allePruefenUndWeiter() {
  const id = S.bid;
  if (!(await aendern([{ op: "bohrung_pruefen", id, wert: true }], { leise: true }))) return;
  const naechste = naechsteOffene(sichtbareBohrungen().findIndex((b) => b.id === id));
  if (naechste && naechste !== id) await bohrungWaehlen(naechste);
}

async function allePruefen(wert_: boolean) {
  const st = S.z!.pruefstand;
  const frage = wert_ ? `Alle Schichten aller ${st.bohrungen[1]} Bohrungen als geprüft markieren?`
    : "Die Prüfung aller Bohrungen zurücknehmen?";
  if (confirm(frage)) await aendern([{ op: "alle_pruefen", wert: wert_ }]);
}

window.addEventListener("keydown", (ev) => {
  if (S.schritt !== "bohrungen" || ev.ctrlKey || ev.metaKey || ev.altKey) return;
  const ziel = ev.target as HTMLElement;
  if (ziel?.closest?.("input, select, textarea, [contenteditable]")) return;     // Tippen in Feldern bleibt Tippen
  const taste = ev.key.toLowerCase();
  if (ev.key === "ArrowDown" || taste === "j") nachbar(1);
  else if (ev.key === "ArrowUp" || taste === "k") nachbar(-1);
  else if (taste === "n") naechsteOffeneWaehlen();
  else if (taste === "g") void allePruefenUndWeiter();
  else return;
  ev.preventDefault();
});

async function seiteHolen(b: Bohrung, sch: Schicht[]) {
  const di = Number(b.id.split(":")[0]);
  const seite = (sch[0]?.quelle.seite ?? b.seite) - 1;
  const schluessel = `${S.sig}/${di}/${seite}`;
  if (seitenbild?.schluessel === schluessel || seiteLaedt === schluessel || !S.z?.dokumente[di]?.pdf) return;
  seiteLaedt = schluessel;
  const d = await versuchen(() => api.seite(S.sig, di, seite));
  seiteLaedt = "";
  if (d) {
    seitenbild = { schluessel, daten: d };
    neu();
  }
}

// ------------------------------------------------------------------ Teile
function zustandZeichen(b: Bohrung) {
  if (b.entfernt) return html`<span class="zeichen raus" title="nicht im Modell">–</span>`;
  if (b.offen > 0) return html`<span class="zeichen warn" title=${`${b.offen} Schicht(en) nicht klassifiziert`}>⚠</span>`;
  if (b.schichten_n && b.schichten_geprueft === b.schichten_n) return html`<span class="zeichen ok" title="alle Schichten geprüft">✓</span>`;
  return html`<span class="zeichen" title="noch zu prüfen">○</span>`;
}

function liste() {
  const alle = S.z!.bohrungen;
  const sichtbar = sichtbareBohrungen();
  const entfernt = alle.filter((b) => b.entfernt);
  return html`
    <aside class="bohrliste-app">
      <input class="suche" type="search" placeholder="Bohrung suchen …" .value=${S.filter}
        @input=${(e: Event) => { S.filter = (e.target as HTMLInputElement).value; neu(); }}>
      <ul class="bliste" role="listbox" aria-label="Bohrungen">
        ${sichtbar.map((b) => html`
          <li role="option" aria-selected=${String(b.id === S.bid)} class=${b.id === S.bid ? "aktiv" : ""}
            @click=${() => bohrungWaehlen(b.id)}>
            ${zustandZeichen(b)}
            <span class="name">${b.code}</span>
            <span class="wert">${b.schichten_geprueft}/${b.schichten_n}</span>
            <button class="symbol leise-knopf" title="Aus dem Modell entfernen" aria-label=${`${b.code} entfernen`}
              @click=${(e: Event) => { e.stopPropagation(); void aendern([{ op: "entfernen", id: b.id }]); }}>🗑</button>
          </li>`)}
      </ul>
      ${entfernt.length ? html`
        <details class="entfernt" ?open=${entfernteOffen} @toggle=${(e: Event) => { entfernteOffen = (e.target as HTMLDetailsElement).open; }}>
          <summary>Entfernt / nicht im Modell (${entfernt.length}) ${hilfe("entfernen")}</summary>
          <ul class="bliste">
            ${entfernt.map((b) => html`
              <li class="raus">
                <span class="name">${b.code}</span>
                <span class="wert klein">${b.doppelt_in ? "doppelt" : b.schichten_n ? "" : "ohne Schichten"}</span>
                <button class="link klein" ?disabled=${!b.schichten_n} @click=${() => aendern([{ op: "wiederherstellen", id: b.id }])}>wiederherstellen</button>
              </li>`)}
          </ul>
        </details>` : nothing}
      <p class="leise klein tasten">↑/↓ blättern · N nächste offene · G alle Schichten geprüft und weiter</p>
    </aside>`;
}

function pruefleiste() {
  const st = S.z!.pruefstand;
  const [bg, bn] = st.bohrungen;
  const [sg, sn] = st.schichten;
  return html`
    <div class="pruefleiste">
      <div class="balken"><span>Bohrungen geprüft <b>${bg}/${bn}</b></span><progress max=${bn || 1} value=${bg}></progress></div>
      <div class="balken"><span>Schichten geprüft <b>${sg}/${sn}</b></span><progress max=${sn || 1} value=${sg}></progress></div>
      <span class=${`plakette ${st.unklassifiziert_offen ? "warn" : "ok"}`}>
        ${st.unklassifiziert_offen ? `⚠ ${st.unklassifiziert_offen} Schicht(en) nicht klassifiziert` : "✓ keine offenen Warnungen"}</span>
      ${hilfe("warnung")}
      <span class="fueller"></span>
      ${hilfe("pruefstand")}
      <button @click=${() => allePruefen(true)} ?disabled=${bg === bn && sg === sn}>✓ Alle Bohrungen geprüft</button>
      <button class="leise-knopf" @click=${() => allePruefen(false)} ?disabled=${!sg}>Zurücknehmen</button>
      ${hilfe("alle_pruefen")}
    </div>`;
}

function feld(titel: string, inhalt: unknown, h?: Parameters<typeof hilfe>[0]) {
  return html`<label class="feld"><span>${titel}${h ? hilfe(h) : nothing}</span>${inhalt}</label>`;
}

/** Passen Rechts-/Hochwert zum Koordinatensystem? Nur der Widerspruch wird gezeigt (Hinweis, keine Sperre). */
function lagePruefung(b: Bohrung) {
  const p = lagePruefen(b.epsg, b.x, b.y);
  return p && !p.ok ? html`<p class="hinweise warn">⚠ ${p.text}</p>` : nothing;
}

function kopf(b: Bohrung) {
  const liste_ = sichtbareBohrungen();
  const i = liste_.findIndex((x) => x.id === b.id);
  const op = (feldname: string) => (e: Event) => aendern([{ op: "bohrung", id: b.id, feld: feldname, wert: wert(e) }]);
  return html`
    <div class="detail-kopf">
      <div class="titelzeile">
        <h2>${b.code}</h2>
        <span class="leise">${b.dokument} · Seite ${b.seite}${b.doppelt_in ? ` · doppelt (auch in ${b.doppelt_in})` : ""}</span>
        <span class="fueller"></span>
        <button title="Vorherige Bohrung (↑)" ?disabled=${i <= 0} @click=${() => nachbar(-1)}>↑ Vorherige</button>
        <button title="Nächste Bohrung (↓)" ?disabled=${i >= liste_.length - 1} @click=${() => nachbar(1)}>↓ Nächste</button>
        <button title="Nächste Bohrung mit offenen Schichten (N)" ?disabled=${!naechsteOffene(i)} @click=${naechsteOffeneWaehlen}>⚠ Nächste offene</button>
      </div>
      <div class="felder">
        ${feld("GOK [m NHN]", html`<input type="number" step="0.01" .value=${live(b.gok === null ? "" : String(b.gok))}
            placeholder="unbekannt" @change=${op("gok")}>
            <small class=${b.gok_quelle === "manuell" ? "manuell" : "leise"}>${b.gok_quelle || "fehlt"}</small>`, "gok")}
        ${feld("Endteufe [m]", html`<output>${zahl(b.endteufe)}</output>`)}
        ${feld("Rechtswert", html`<input type="number" step="0.01" .value=${live(b.x === null ? "" : String(b.x))} @change=${op("x")}>`, "koordinaten")}
        ${feld("Hochwert", html`<input type="number" step="0.01" .value=${live(b.y === null ? "" : String(b.y))} @change=${op("y")}>`)}
        ${feld("Koordinatensystem (EPSG)", epsgAuswahl(b.epsg, (c) => aendern([{ op: "bohrung", id: b.id, feld: "epsg", wert: c }])), "epsg")}
        ${feld("Ø Säule [m]", html`<input type="number" step="0.1" min="0" class="kurz" placeholder=${`auto ${zahl(S.z!.durchmesser ?? S.z!.durchmesser_auto, 1)}`}
            .value=${live(b.durchmesser === null ? "" : String(b.durchmesser))} @change=${op("durchmesser")}>`, "durchmesser")}
        ${feld("Grundwasser", html`<output>${b.grundwasser || "–"}</output>`)}
      </div>
      ${lagePruefung(b)}
      ${b.hinweise.length ? html`<p class="hinweise">ℹ ${b.hinweise.join(" · ")}</p>` : nothing}
    </div>`;
}

function bodenartWahl(b: Bohrung, s: Schicht) {
  const klassen = S.z!.klassen;
  const bekannt = klassen.some((k) => k.klasse === s.bodenart);
  return html`
    <span class="farbfeld" style=${`background:${s.farbe}`}></span>
    <select aria-label="Bodenart" @change=${(e: Event) => aendern([{ op: "schicht", id: b.id, k: s.k, feld: "bodenart",
                                                                     wert: (e.target as HTMLSelectElement).value }])}>
      ${bekannt ? nothing : html`<option .selected=${true} value=${s.bodenart}>${s.bodenart}</option>`}
      ${ARTEN.map(([art, titel]) => html`
        <optgroup label=${titel}>
          ${klassen.filter((k) => k.art === art).map((k) => html`
            <option value=${k.klasse} .selected=${k.klasse === s.bodenart}>${k.name}${k.din4023 ? ` (${k.din4023})` : ""}</option>`)}
        </optgroup>`)}
    </select>`;
}

function schichtTabelle(b: Bohrung, sch: Schicht[]) {
  return html`
    <table class="tabelle schichten">
      <thead><tr>
        <th title="geprüft">✓ ${hilfe("geprueft")}</th><th>von [m] ${hilfe("tiefe")}</th><th>bis [m]</th>
        <th>Bodenart ${hilfe("bodenart")}</th><th>Beschreibung (PDF)</th><th>nach Norm ${hilfe("norm")}</th>
      </tr></thead>
      <tbody>
        ${sch.map((s) => html`
          <tr class=${[s.offen ? "warn" : "", s.korrigiert ? "korrigiert" : "", s.k === S.k ? "gewaehlt" : ""].join(" ")}
            @click=${() => { S.k = s.k; neu(); }}>
            <td><input type="checkbox" .checked=${live(s.geprueft)} aria-label="geprüft"
              @change=${(e: Event) => aendern([{ op: "schicht", id: b.id, k: s.k, feld: "geprueft", wert: (e.target as HTMLInputElement).checked }], { leise: true })}></td>
            <td><input type="number" step="0.01" min="0" class="tief" .value=${live(String(s.von))}
              @change=${(e: Event) => aendern([{ op: "schicht", id: b.id, k: s.k, feld: "oben", wert: wert(e) }])}></td>
            <td><input type="number" step="0.01" min="0" class="tief" .value=${live(String(s.bis))}
              @change=${(e: Event) => aendern([{ op: "schicht", id: b.id, k: s.k, feld: "unten", wert: wert(e) }])}></td>
            <td class="bodenart">${bodenartWahl(b, s)}
              ${s.offen ? html`<div class="warnung">⚠ nicht klassifiziert</div>` : nothing}
              ${s.korrigiert ? html`<div class="leise klein">korrigiert</div>` : nothing}</td>
            <td class="beschreibung">${s.beschreibung || html`<span class="leise">– keine Beschreibung –</span>`}
              ${s.hinweise.length ? html`<div class="leise klein">${s.hinweise.join(" · ")}</div>` : nothing}</td>
            <td class="norm">
              ${s.norm.benennung ? html`<div>${s.norm.benennung}</div>` : nothing}
              ${s.norm.din4023 ? html`<code title="Kurzzeichen nach DIN 4023">${s.norm.din4023}</code>` : nothing}
              ${s.norm.bodengruppe ? html` <code title="Bodengruppe nach DIN 18196">${s.norm.bodengruppe}</code>` : nothing}
              ${[s.norm.konsistenz, s.norm.lagerung, s.norm.kalk, s.norm.bodenfarbe].filter(Boolean).length
                ? html`<div class="leise klein">${[s.norm.konsistenz, s.norm.lagerung, s.norm.kalk, s.norm.bodenfarbe].filter(Boolean).join(" · ")}</div>` : nothing}
              ${s.norm.hinweise.length ? html`<div class="klein hinweis-norm" title=${s.norm.hinweise.join("\n")}>ℹ ${s.norm.hinweise[0]}${s.norm.hinweise.length > 1 ? ` (+${s.norm.hinweise.length - 1})` : ""}</div>` : nothing}
              ${s.vorschlag ? html`
                <button class="vorschlag" @click=${(e: Event) => { e.stopPropagation(); void aendern([{ op: "vorschlag", id: b.id, k: s.k }]); }}
                  title=${`Vorschlag nach Norm: ${s.vorschlag.benennung}${s.vorschlag.sicher ? "" : " (unsicher)"}`}>
                  → ${s.vorschlag.klasse} übernehmen</button>${hilfe("vorschlag")}` : nothing}
            </td>
          </tr>`)}
      </tbody>
    </table>`;
}

function quelle(b: Bohrung, sch: Schicht[]) {
  void seiteHolen(b, sch);
  const di = Number(b.id.split(":")[0]);
  const hatPdf = !!S.z!.dokumente[di]?.pdf;
  const sb = seitenbild?.schluessel === `${S.sig}/${di}/${(sch[0]?.quelle.seite ?? b.seite) - 1}` ? seitenbild.daten : null;
  const gewaehlt = sch.find((s) => s.k === S.k) ?? null;
  const rahmen = (bbox: number[] | null | undefined, klasse: string) => {
    if (!bbox || !sb) return nothing;
    const f = sb.px_je_pt * zoom;
    return html`<div class=${`bbox ${klasse}`} style=${`left:${bbox[0] * f}px;top:${bbox[1] * f}px;width:${(bbox[2] - bbox[0]) * f}px;height:${(bbox[3] - bbox[1]) * f}px`}></div>`;
  };
  const alle = sch.map((s) => s.quelle.bbox).filter((x): x is number[] => !!x && x.length === 4);
  const saeulenRahmen = alle.length ? [Math.min(...alle.map((x) => x[0])), Math.min(...alle.map((x) => x[1])),
                                       Math.max(...alle.map((x) => x[2])), Math.max(...alle.map((x) => x[3]))] : null;
  return html`
    <aside class="quelle-spalte">
      <div class="saeule-rahmen">
        ${saeule(sch.map((s) => ({ k: s.k, von: s.von, bis: s.bis, farbe: s.farbe, warn: s.offen, geprueft: s.geprueft,
                                   titel: `${zahl(s.von)}–${zahl(s.bis)} m: ${s.bodenart}${s.beschreibung ? ` – ${s.beschreibung}` : ""}` })),
                 { hoehe: 420, gewaehlt: S.k, waehlen: (k) => { S.k = k; neu(); } })}
      </div>
      ${!hatPdf ? nothing : html`<div class="pdf-rahmen">
        <div class="pdf-kopf"><b>Quelle im PDF</b> ${hilfe("quelle")}
          <span class="fueller"></span>
          ${hatPdf ? html`<button class="symbol" title="kleiner" @click=${() => { zoom = Math.max(0.25, zoom / 1.4); neu(); }}>−</button>
            <button class="symbol" title="größer" @click=${() => { zoom = Math.min(1.5, zoom * 1.4); neu(); }}>+</button>` : nothing}
        </div>
        ${!sb ? html`<p class="leise klein">Seite wird geladen …</p>` : html`
          ${refScroll(saeulenRahmen, sb.px_je_pt * zoom)}
          <div class="pdf-seite">
            <div class="pdf-flaeche" style=${`width:${sb.breite_pt * sb.px_je_pt * zoom}px;height:${sb.hoehe_pt * sb.px_je_pt * zoom}px`}>
              <img src=${sb.url} alt=${`Seite ${sb.seite + 1}`} draggable="false">
              ${rahmen(saeulenRahmen, "saeule-bbox")}
              ${rahmen(gewaehlt?.quelle.bbox, "schicht-bbox")}
            </div>
          </div>`}
      </div>`}
    </aside>`;
}

// Seite so verschieben, dass die Bohrsaeule sichtbar ist (einmal je Bohrung/Zoom)
let gescrollt = "";
function refScroll(bbox: number[] | null, f: number) {
  const schluessel = `${S.bid}/${zoom}`;
  if (!bbox || gescrollt === schluessel) return nothing;
  requestAnimationFrame(() => {
    const el = document.querySelector<HTMLElement>(".pdf-seite");
    if (!el) return;
    el.scrollLeft = Math.max(0, bbox[0] * f - el.clientWidth / 3);
    el.scrollTop = Math.max(0, bbox[1] * f - 40);
    gescrollt = schluessel;
  });
  return nothing;
}

export function schrittBohrungen() {
  const z = S.z!;
  const d = S.details.get(S.bid);
  const b = z.bohrungen.find((x) => x.id === S.bid);
  const di = b ? Number(b.id.split(":")[0]) : 0;
  const ohnePdf = !z.dokumente[di]?.pdf;
  return html`
    <div class=${`schritt-bohrungen ${ohnePdf ? "ohne-pdf" : ""}`}>
      ${pruefleiste()}
      ${liste()}
      <section class="bohrung-detail">
        ${!b ? html`<p class="leise">Links eine Bohrung wählen.</p>` : html`
          ${kopf(b)}
          ${!d ? html`<p class="leise">Schichten werden geladen …</p>` : html`
            ${schichtTabelle(b, d.schichten)}
            <div class="detail-fuss">
              <button class="primaer" title="Alle Schichten dieser Bohrung als geprüft markieren und zur nächsten offenen (G)"
                @click=${allePruefenUndWeiter}>✓ Alle Schichten geprüft – weiter</button>
              <button class="leise-knopf" ?disabled=${!b.schichten_geprueft}
                @click=${() => aendern([{ op: "bohrung_pruefen", id: b.id, wert: false }])}>Prüfung zurücknehmen</button>
              <span class="fueller"></span>
              <button class="gefahr" @click=${() => aendern([{ op: "entfernen", id: b.id }])}>🗑 Aus dem Modell entfernen</button>
            </div>`}`}
      </section>
      ${b && d ? quelle(b, d.schichten) : html`<aside class="quelle-spalte"></aside>`}
    </div>`;
}
