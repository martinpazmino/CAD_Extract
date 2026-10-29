// Schritt 3 · Lage: Unterlage (Lageplan oder Laengsschnitt) hochladen, kalibrieren (Strecke messen -> Massstab,
// Bezugspunkt mit Koordinate, Drehung bzw. Hoehenmassstab), sperren, dann die Bohrungen im Viewer daraufziehen.
// Ohne Koordinaten: Reihe mit Abstaenden oder Stationen. Dazu der Durchmesser der Bohrsaeulen.
import { html, nothing } from "lit";
import { live } from "lit/directives/live.js";
import { api, type Zustand } from "./api";
import { hilfe } from "./hilfe";
import { epsgAuswahl, lagePruefen, systemText } from "./epsg";
import { S, aendern, melden, neu, versuchen, viewerAktualisieren, zustandUebernehmen } from "./store";
import { kalibrierungText, massstabszahl } from "../viewer/lage";
import type { Bildpunkt } from "../viewer/lage";
import type { Kalibrierung, Massstab } from "../viewer/kanal";

const zahl = (v: number | null | undefined, s = 2) =>
  v === null || v === undefined || !Number.isFinite(v) ? "" : v.toLocaleString("de-DE", { minimumFractionDigits: s, maximumFractionDigits: s });
const eingabe = (e: Event) => {
  const t = (e.target as HTMLInputElement).value.trim().replace(",", ".");
  return t === "" ? null : Number(t);
};

interface Entwurf {
  schluessel: string;                         // Unterlage + gespeicherte Kalibrierung, aus der er entstand
  massArt: "strecke" | "n";
  p1: Bildpunkt | null; p2: Bildpunkt | null; meter: number | null; n: number | null;
  hoeheArt: "gleich" | "n" | "strecke";
  h1: Bildpunkt | null; h2: Bildpunkt | null; hoeheMeter: number | null; hoeheN: number | null;
  bezug: Bildpunkt | null; x: number | null; y: number | null;
  drehung: number; epsg: number | null;
}

let e: Entwurf | null = null;
let waehlt = "";                              // welcher Punkt gerade im Plan gewaehlt wird
let neueArt: "plan" | "schnitt" = "plan";

function schluessel(z: Zustand) {
  const u = z.unterlage;
  return u ? `${u.sha}/${u.seite}/${u.art}/${JSON.stringify(u.kalibrierung)}` : "";
}

/** Entwurf aus der gespeicherten Kalibrierung (neu, wenn sich Unterlage oder Kalibrierung auf dem Server aendern). */
function entwurf(z: Zustand): Entwurf | null {
  const u = z.unterlage;
  if (!u) return (e = null);
  if (e && e.schluessel === schluessel(z)) return e;
  const k = u.kalibrierung;
  const strecke = (m: Massstab | null | undefined) => (m && !("n" in m) ? m : null);
  const s = strecke(k?.massstab);
  const h = strecke(k?.hoehe);
  e = {
    schluessel: schluessel(z),
    massArt: k?.massstab && "n" in k.massstab ? "n" : "strecke",
    p1: s ? { u: s.u1, v: s.v1 } : null, p2: s ? { u: s.u2, v: s.v2 } : null, meter: s?.meter ?? null,
    n: k?.massstab && "n" in k.massstab ? k.massstab.n : null,
    hoeheArt: !k?.hoehe ? "gleich" : "n" in k.hoehe ? "n" : "strecke",
    h1: h ? { u: h.u1, v: h.v1 } : null, h2: h ? { u: h.u2, v: h.v2 } : null, hoeheMeter: h?.meter ?? null,
    hoeheN: k?.hoehe && "n" in k.hoehe ? k.hoehe.n : null,
    bezug: k?.bezug ? { u: k.bezug.u, v: k.bezug.v } : null, x: k?.bezug?.x ?? null, y: k?.bezug?.y ?? null,
    drehung: k?.drehung ?? 0, epsg: k?.epsg ?? z.viewer.epsg ?? null,
  };
  return e;
}

/** Vollstaendiger Entwurf -> Kalibrierung (sonst null). */
function kalibrierung(z: Zustand, gesperrt = false): Kalibrierung | null {
  const d = e;
  const u = z.unterlage;
  if (!d || !u) return null;
  let massstab: Massstab | null = null;
  if (d.massArt === "n" && d.n && d.n > 0) massstab = { n: d.n };
  if (d.massArt === "strecke" && d.p1 && d.p2 && d.meter && d.meter > 0) {
    massstab = { u1: d.p1.u, v1: d.p1.v, u2: d.p2.u, v2: d.p2.v, meter: d.meter };
  }
  if (!massstab || !d.bezug || d.x === null || d.y === null) return null;
  let hoehe: Massstab | null = null;
  if (u.art === "schnitt" && d.hoeheArt === "n" && d.hoeheN && d.hoeheN > 0) hoehe = { n: d.hoeheN };
  if (u.art === "schnitt" && d.hoeheArt === "strecke" && d.h1 && d.h2 && d.hoeheMeter && d.hoeheMeter > 0) {
    hoehe = { u1: d.h1.u, v1: d.h1.v, u2: d.h2.u, v2: d.h2.v, meter: d.hoeheMeter };
  }
  return { massstab, hoehe, bezug: { ...d.bezug, x: d.x, y: d.y }, drehung: u.art === "plan" ? d.drehung : 0,
           epsg: u.art === "plan" ? d.epsg : null, gesperrt };
}

/** Vorschau im Viewer und Hilfsmarken nach jeder Eingabe. */
function vorschau() {
  const z = S.z!;
  S.entwurf = kalibrierung(z);
  const v = S.viewer;
  if (v && e) {
    v.editor.hilfsmarken({ strecke: e.massArt === "strecke" ? [e.p1, e.p2] : [], hoehe: e.hoeheArt === "strecke" ? [e.h1, e.h2] : [],
                           bezug: e.bezug });
    if (S.entwurf) v.editor.vorschau(S.entwurf);
  }
  neu();
}

async function punkt(welcher: "p1" | "p2" | "h1" | "h2" | "bezug") {
  const v = S.viewer;
  if (!v || !e) return;
  waehlt = welcher;
  neu();
  const p = await v.editor.bildpunktWaehlen();
  waehlt = "";
  if (!p || !e || S.z?.unterlage?.kalibrierung?.gesperrt) {       // abgebrochen (Esc, Sperren, Ziehen)
    neu();
    return;
  }
  e[welcher] = p;
  vorschau();
}

async function uebernehmen(sperren: boolean) {
  S.viewer?.editor.waehlenAbbrechen();                  // offene Punktwahl blockiert sonst das Ziehen
  const k = kalibrierung(S.z!, sperren);
  if (!k) {
    melden("Für die Kalibrierung fehlen Maßstab oder Bezugspunkt.", "warn");
    return;
  }
  if (await aendern([{ op: "kalibrierung", wert: k }])) {
    S.entwurf = null;
    melden(sperren ? "Plan kalibriert und gesperrt – jetzt die Bohrungen ziehen." : "Kalibrierung übernommen.", "ok");
    await S.viewer?.ansicht(S.z?.unterlage?.art === "schnitt" ? "sued" : "oben");     // Plan in neuer Groesse zeigen
  }
}

async function sperre(an: boolean) {
  const u = S.z!.unterlage;
  if (!u?.kalibrierung) return;
  await aendern([{ op: "kalibrierung", wert: { ...u.kalibrierung, gesperrt: an } }]);
}

async function hochladen(ev: Event) {
  const input = ev.target as HTMLInputElement;
  const f = input.files?.[0];
  input.value = "";
  if (!f) return;
  const z = await versuchen(() => api.unterlage(S.sig, f, neueArt, 0), "Unterlage wird gelesen …");
  if (z) {
    zustandUebernehmen(z);
    S.entwurf = null;
    neu();
    await viewerAktualisieren();
    await S.viewer?.lageModus(true);
    await S.viewer?.ansicht(z.unterlage?.art === "schnitt" ? "sued" : "oben");
  }
}

async function seiteOderArt(seite: number, art: string) {
  const z = await versuchen(() => api.unterlageSeite(S.sig, seite, art), "Seite wird gelesen …");
  if (z) {
    zustandUebernehmen(z);
    S.entwurf = null;
    neu();
    await viewerAktualisieren();
    await S.viewer?.ansicht(art === "schnitt" ? "sued" : "oben");
  }
}

async function unterlageEntfernen() {
  if (!confirm("Unterlage mit ihrer Kalibrierung entfernen? Gesetzte Bohrungen behalten ihre Lage.")) return;
  const z = await versuchen(() => api.unterlageEntfernen(S.sig));
  if (z) {
    zustandUebernehmen(z);
    S.entwurf = null;
    neu();
    await viewerAktualisieren();
  }
}

// ------------------------------------------------------------------ Teile
const abschnitt = (titel: unknown, inhalt: unknown, offen = true) =>
  html`<details class="abschnitt" ?open=${offen}><summary>${titel}</summary><div class="abschnitt-inhalt">${inhalt}</div></details>`;

function punktKnopf(titel: string, welcher: "p1" | "p2" | "h1" | "h2" | "bezug", p: Bildpunkt | null, aus: boolean) {
  return html`<button class=${`punkt ${waehlt === welcher ? "aktiv" : ""} ${p ? "gesetzt" : ""}`} ?disabled=${aus}
    @click=${() => punkt(welcher)}>${waehlt === welcher ? "… im Plan klicken" : p ? `${titel} ✓` : titel}</button>`;
}

/** Passt der Bezugspunkt zum gewaehlten System? (Hinweis, keine Sperre) */
function systemPruefung(d: Entwurf) {
  const p = lagePruefen(d.epsg, d.x, d.y);
  return p ? html`<p class=${`klein ${p.ok ? "ok" : "warn"}`}>${p.ok ? "✓" : "⚠"} ${p.text}</p>` : nothing;
}

function kalibrierenTeil(z: Zustand) {
  const u = z.unterlage!;
  const d = entwurf(z)!;
  const gesperrt = !!u.kalibrierung?.gesperrt;
  const plan = u.art === "plan";
  const px = d.p1 && d.p2 ? Math.hypot(d.p2.u - d.p1.u, d.p2.v - d.p1.v) : null;
  const k = kalibrierung(z);
  const n = k ? massstabszahl(k.massstab, u.mm_pro_px) : null;
  const mitLage = z.viewer.bohrungen.filter((b) => b.x !== null && (plan ? !/Plan|Viewer/.test(b.quelle) : b.gok_bekannt));
  return html`
    <p class=${`status ${u.kalibrierung ? (gesperrt ? "ok" : "") : "warn"}`}>
      ${u.kalibrierung ? html`${gesperrt ? "🔒 gesperrt · " : ""}${kalibrierungText(u)}${plan ? ` · ${systemText(u.kalibrierung.epsg)}` : ""}` : "nicht kalibriert"}
      ${S.entwurf && JSON.stringify({ ...S.entwurf, gesperrt: false }) !== JSON.stringify({ ...(u.kalibrierung ?? {}), gesperrt: false })
        ? html`<br><span class="leise">Vorschau: ${kalibrierungText(u, S.entwurf)} (noch nicht übernommen)</span>` : nothing}
    </p>
    ${gesperrt ? html`
      <p class="leise klein">Der Plan liegt fest. Bohrungen im Viewer ziehen – ${plan ? "nur in x/y" : "entlang der Station; die Höhe nur ohne GOK aus dem PDF"}.</p>
      <button @click=${() => sperre(false)}>🔓 Entsperren (neu kalibrieren)</button>` : html`
      <fieldset class="gruppe">
        <legend>1 · Maßstab ${hilfe("massstab")}</legend>
        <div class="umschalter">
          <label><input type="radio" name="massart" .checked=${d.massArt === "strecke"} @change=${() => { d.massArt = "strecke"; vorschau(); }}> Strecke messen</label>
          <label><input type="radio" name="massart" .checked=${d.massArt === "n"} @change=${() => { d.massArt = "n"; vorschau(); }}> 1:n eingeben</label>
        </div>
        ${d.massArt === "strecke" ? html`
          <div class="zeile">${punktKnopf("Punkt 1", "p1", d.p1, false)}${punktKnopf("Punkt 2", "p2", d.p2, false)}</div>
          <div class="zeile">
            <span class="leise klein">${px ? `gemessen ${zahl(px, 0)} px` : "zwei Punkte anklicken"}</span>
            <label class="inline">wahre Länge <input type="number" step="0.01" min="0" class="kurz" .value=${live(d.meter === null ? "" : String(d.meter))}
              @input=${(ev: Event) => { d.meter = eingabe(ev); vorschau(); }}> m</label>
          </div>` : html`
          <label class="inline">Maßstab 1: <input type="number" step="1" min="1" class="kurz" .value=${live(d.n === null ? "" : String(d.n))}
            @input=${(ev: Event) => { d.n = eingabe(ev); vorschau(); }}></label>`}
        ${n ? html`<p class="leise klein">ergibt 1:${Math.round(n).toLocaleString("de-DE")}</p>` : nothing}
      </fieldset>
      ${plan ? nothing : html`
        <fieldset class="gruppe">
          <legend>Höhenmaßstab ${hilfe("hoehe")}</legend>
          <div class="umschalter">
            <label><input type="radio" name="hoeheart" .checked=${d.hoeheArt === "gleich"} @change=${() => { d.hoeheArt = "gleich"; vorschau(); }}> wie Länge</label>
            <label><input type="radio" name="hoeheart" .checked=${d.hoeheArt === "n"} @change=${() => { d.hoeheArt = "n"; vorschau(); }}> 1:n</label>
            <label><input type="radio" name="hoeheart" .checked=${d.hoeheArt === "strecke"} @change=${() => { d.hoeheArt = "strecke"; vorschau(); }}> messen</label>
          </div>
          ${d.hoeheArt === "n" ? html`<label class="inline">Höhe 1: <input type="number" step="1" min="1" class="kurz"
              .value=${live(d.hoeheN === null ? "" : String(d.hoeheN))} @input=${(ev: Event) => { d.hoeheN = eingabe(ev); vorschau(); }}></label>` : nothing}
          ${d.hoeheArt === "strecke" ? html`
            <div class="zeile">${punktKnopf("Höhe oben", "h1", d.h1, false)}${punktKnopf("Höhe unten", "h2", d.h2, false)}</div>
            <label class="inline">Höhenunterschied <input type="number" step="0.01" min="0" class="kurz"
              .value=${live(d.hoeheMeter === null ? "" : String(d.hoeheMeter))} @input=${(ev: Event) => { d.hoeheMeter = eingabe(ev); vorschau(); }}> m</label>` : nothing}
        </fieldset>`}
      <fieldset class="gruppe">
        <legend>2 · Bezugspunkt ${hilfe("bezug")}</legend>
        <div class="zeile">${punktKnopf("Punkt im Plan wählen", "bezug", d.bezug, false)}</div>
        <div class="zeile">
          <label class="feld schmal"><span>${plan ? "Rechtswert" : "Station [m]"}</span>
            <input type="number" step="0.01" .value=${live(d.x === null ? "" : String(d.x))} @input=${(ev: Event) => { d.x = eingabe(ev); vorschau(); }}></label>
          <label class="feld schmal"><span>${plan ? "Hochwert" : "Höhe [m NHN]"}</span>
            <input type="number" step="0.01" .value=${live(d.y === null ? "" : String(d.y))} @input=${(ev: Event) => { d.y = eingabe(ev); vorschau(); }}></label>
        </div>
        ${plan ? html`
          <label class="feld breit"><span>Koordinatensystem (EPSG) ${hilfe("epsg")}</span>
            ${epsgAuswahl(d.epsg, (c) => { d.epsg = c; vorschau(); })}</label>
          ${systemPruefung(d)}` : nothing}
        ${mitLage.length ? html`
          <label class="inline klein">oder von Bohrung
            <select @change=${(ev: Event) => {
              const b = z.viewer.bohrungen.find((x) => x.id === (ev.target as HTMLSelectElement).value);
              if (b) { d.x = b.x; d.y = plan ? b.y : b.gok; vorschau(); }
            }}>
              <option value="">–</option>
              ${mitLage.map((b) => html`<option value=${b.id}>${b.code}</option>`)}
            </select></label>` : nothing}
      </fieldset>
      ${plan ? html`
        <fieldset class="gruppe">
          <legend>3 · Drehung ${hilfe("drehung")}</legend>
          <div class="zeile">
            <label class="inline"><input type="number" step="0.1" class="kurz" .value=${live(String(d.drehung))}
              @input=${(ev: Event) => { d.drehung = eingabe(ev) ?? 0; vorschau(); }}> ° gegen den Uhrzeigersinn</label>
          </div>
        </fieldset>` : nothing}
      <div class="zeile knopfzeile">
        <button ?disabled=${!k} @click=${() => uebernehmen(false)}>Übernehmen</button>
        <button class="primaer" ?disabled=${!k} @click=${() => uebernehmen(true)}>🔒 Übernehmen und sperren</button>
        ${hilfe("sperren")}
      </div>
      ${u.kalibrierung ? html`<button class="link klein" @click=${() => aendern([{ op: "kalibrierung", wert: null }])}>Kalibrierung zurücksetzen</button>` : nothing}`}`;
}

function unterlageTeil(z: Zustand) {
  const u = z.unterlage;
  if (!u) {
    return html`
      <p class="leise klein">Lageplan (von oben) oder Längsschnitt (von der Seite) als PDF – er liegt im Viewer unter den Bohrungen.</p>
      <div class="umschalter">
        <label><input type="radio" name="neueart" .checked=${neueArt === "plan"} @change=${() => { neueArt = "plan"; }}> Lageplan</label>
        <label><input type="radio" name="neueart" .checked=${neueArt === "schnitt"} @change=${() => { neueArt = "schnitt"; }}> Längsschnitt</label>
      </div>
      <label class="datei-knopf"><input type="file" accept=".pdf,application/pdf" @change=${hochladen}>PDF wählen …</label>`;
  }
  return html`
    <p><b>${u.name}</b> <span class="leise">· ${u.art === "plan" ? "Lageplan" : "Längsschnitt"}</span></p>
    <div class="zeile">
      ${(u.seiten ?? 1) > 1 ? html`<label class="inline">Seite <select @change=${(ev: Event) => seiteOderArt(Number((ev.target as HTMLSelectElement).value), u.art)}>
          ${Array.from({ length: u.seiten }, (_, i) => html`<option value=${i} .selected=${i === u.seite}>${i + 1}</option>`)}
        </select></label>` : nothing}
      <label class="inline">Ansicht <select @change=${(ev: Event) => seiteOderArt(u.seite, (ev.target as HTMLSelectElement).value)}>
        <option value="plan" .selected=${u.art === "plan"}>Lageplan</option>
        <option value="schnitt" .selected=${u.art === "schnitt"}>Längsschnitt</option>
      </select></label>
    </div>
    <label class="inline">Deckkraft ${hilfe("deckkraft")}
      <input type="range" min="0.1" max="1" step="0.05" .value=${String(S.viewer?.editor.deckkraft ?? 0.85)}
        @input=${(ev: Event) => { if (S.viewer) { S.viewer.editor.deckkraft = Number((ev.target as HTMLInputElement).value); S.viewer.editor.bildSichtbarkeit(); } }}></label>
    <button class="link klein" @click=${unterlageEntfernen}>Unterlage entfernen</button>`;
}

function bohrungenTeil(z: Zustand) {
  const u = z.unterlage;
  const frei = !u || !!u.kalibrierung?.gesperrt;
  const ohne = z.viewer.bohrungen.filter((b) => b.x === null);
  const reihe = z.lage_modus === "reihe";
  return html`
    ${!frei ? html`<p class="warnung">Erst kalibrieren und sperren (🔒) – dann die Bohrungen ziehen.</p>` : nothing}
    ${ohne.length ? html`
      <p class="klein">Ohne Lage (${ohne.length}) – in den Viewer ziehen ${hilfe("ohne_lage")}</p>
      <div class="parkplatz">
        ${ohne.map((b) => html`<span class="park ${frei ? "" : "gesperrt"}" title="In den Viewer ziehen"
          @pointerdown=${(ev: PointerEvent) => S.viewer?.editor.ziehenStart(ev, b.id, true)}>${b.code}</span>`)}
      </div>` : html`<p class="leise klein">Alle Bohrungen im Modell haben eine Lage.</p>`}
    ${reihe ? reiheTeil(z) : nothing}`;
}

function reiheTeil(z: Zustand) {
  const ids = z.reihe.map((r) => r.id);
  const schieben = (i: number, um: number) => {
    const neu_ = [...ids];
    const [x] = neu_.splice(i, 1);
    neu_.splice(Math.max(0, Math.min(neu_.length, i + um)), 0, x);
    void aendern([{ op: "reihe", reihenfolge: neu_ }], { leise: true });
  };
  return html`
    <div class="zeile">
      <label class="inline">Standardabstand ${hilfe("standardabstand")}
        <input type="number" step="1" min="1" class="kurz" .value=${live(String(z.reihe_standard))}
          @change=${(ev: Event) => aendern([{ op: "reihe", standard: eingabe(ev) }])}> m</label>
    </div>
    <table class="tabelle kompakt reihe">
      <thead><tr><th></th><th>Bohrung</th><th>Abstand [m] ${hilfe("reihe")}</th><th>Station [m]</th></tr></thead>
      <tbody>
        ${z.reihe.map((r, i) => html`
          <tr>
            <td class="pfeile"><button class="symbol" ?disabled=${i === 0} title="nach vorn" @click=${() => schieben(i, -1)}>▲</button><button class="symbol"
              ?disabled=${i === ids.length - 1} title="nach hinten" @click=${() => schieben(i, 1)}>▼</button></td>
            <td>${r.code}</td>
            <td><input type="number" step="0.1" min="0" class="kurz" ?disabled=${i === 0} .value=${live(r.abstand === null ? "" : String(r.abstand))}
              @change=${(ev: Event) => aendern([{ op: "reihe", abstand: { [r.id]: eingabe(ev) } }], { leise: true })}></td>
            <td><input type="number" step="0.1" class="kurz" .value=${live(String(r.station))} title=${r.quelle_text}
              @change=${(ev: Event) => aendern([{ op: "reihe", station: { [r.id]: eingabe(ev) } }], { leise: true })}></td>
          </tr>`)}
      </tbody>
    </table>`;
}

/** Hilfsmarken (Strecke, Bezugspunkt) nur beim Kalibrieren; gesperrt zeigt der Plan nur die Bohrungen. */
function hilfsmarkenNachziehen(z: Zustand) {
  const v = S.viewer;
  if (!v) return;
  if (!z.unterlage || z.unterlage.kalibrierung?.gesperrt || !e) v.editor.hilfsmarken({});
  else v.editor.hilfsmarken({ strecke: e.massArt === "strecke" ? [e.p1, e.p2] : [], hoehe: e.hoeheArt === "strecke" ? [e.h1, e.h2] : [],
                              bezug: e.bezug });
}

export function schrittLage() {
  const z = S.z!;
  entwurf(z);
  hilfsmarkenNachziehen(z);
  return html`
    <div class="app-panel links">
      ${abschnitt(html`Lage der Bohrungen ${hilfe("lage_art")}`, html`
        <div class="umschalter">
          <label><input type="radio" name="lagemodus" .checked=${z.lage_modus === "koordinaten"}
            @change=${() => aendern([{ op: "lage_modus", wert: "koordinaten" }])}> Koordinaten (Lageplan)</label>
          <label><input type="radio" name="lagemodus" .checked=${z.lage_modus === "reihe"}
            @change=${() => aendern([{ op: "lage_modus", wert: "reihe" }])}> Reihe (Längsschnitt)</label>
        </div>`)}
      ${abschnitt(html`Unterlage ${hilfe("unterlage")}`, unterlageTeil(z))}
      ${z.unterlage ? abschnitt(html`Kalibrieren`, kalibrierenTeil(z)) : nothing}
      ${abschnitt(html`Bohrungen setzen`, bohrungenTeil(z))}
      ${abschnitt(html`Darstellung`, html`
        <label class="inline">Ø Bohrsäulen ${hilfe("durchmesser")}
          <input type="number" step="0.1" min="0" class="kurz" placeholder=${`auto ${zahl(z.durchmesser_auto, 1)}`}
            .value=${live(z.durchmesser === null ? "" : String(z.durchmesser))}
            @change=${(ev: Event) => aendern([{ op: "durchmesser", wert: eingabe(ev) }])}> m</label>
        <p class="leise klein">Je Bohrung im Schritt Bohrungen (Ø Säule). Leer = automatisch nach Modellgröße.</p>`, false)}
      ${z.hinweise.length ? html`<div class="hinweisliste">${z.hinweise.map((h) => html`<p class="klein">ℹ ${h}</p>`)}</div>` : nothing}
    </div>`;
}
