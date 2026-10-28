// Schritt 4 · Einheiten: wie die Schichten zwischen den Bohrungen verbunden werden (automatisch korreliert oder
// vorgegeben), Profil aller Bohrungen nach Einheit, Beschreibungen je Einheit und die Einstellungen des Modells.
import { html, nothing } from "lit";
import { live } from "lit/directives/live.js";
import { hilfe } from "./hilfe";
import { einheitenProfil } from "./profil";
import { S, aendern, gehe, neu } from "./store";

const zahl = (v: number | null | undefined, s = 1) =>
  v === null || v === undefined ? "–" : v.toLocaleString("de-DE", { minimumFractionDigits: s, maximumFractionDigits: s });

let gewaehlt = "";
let vorgabe: { name: string; bodenarten: string }[] | null = null;   // Bearbeitung (vor dem Uebernehmen)
let vorgabeFuer = "";

function einstellungen() {
  const e = S.z!.einstellungen;
  const setzen = (feld: string, w: unknown) => aendern([{ op: "einstellungen", [feld]: w }]);
  const autoFeld = (feld: "puffer" | "raster" | "basis", titel: string, einheit: string, standard: number, h: Parameters<typeof hilfe>[0]) => {
    const w = e[feld];
    return html`
      <div class="einstellung">
        <label class="inline"><input type="checkbox" .checked=${w === null} @change=${(ev: Event) =>
          setzen(feld, (ev.target as HTMLInputElement).checked ? null : standard)}> ${titel} automatisch</label>${hilfe(h)}
        ${w === null ? nothing : html`<input type="number" step="any" class="kurz" .value=${live(String(w))}
          @change=${(ev: Event) => setzen(feld, Number((ev.target as HTMLInputElement).value))}> ${einheit}`}
      </div>`;
  };
  const p = S.modell?.bericht?.parameter ?? {};
  return html`
    <section class="karte">
      <h3>Modell</h3>
      <div class="einstellung">
        <span>Interpolation ${hilfe("methode")}</span>
        <label class="inline"><input type="radio" name="methode" .checked=${e.methode === "idw"} @change=${() => setzen("methode", "idw")}> IDW</label>
        <label class="inline"><input type="radio" name="methode" .checked=${e.methode === "tps"} @change=${() => setzen("methode", "tps")}> Dünnplatten-Spline</label>
      </div>
      ${autoFeld("puffer", "Puffer", "m", Number(p.puffer_m ?? 20), "puffer")}
      ${autoFeld("raster", "Raster", "m", Number(p.raster_m ?? 5), "raster")}
      ${autoFeld("basis", "Modellbasis", "m NHN", Math.floor(Number(p.basis_nhn ?? 0)), "basis")}
      <div class="einstellung">
        <label class="inline"><input type="checkbox" .checked=${e.gok_relativ} @change=${(ev: Event) =>
          setzen("gok_relativ", (ev.target as HTMLInputElement).checked)}> fehlende GOK: Gelände = 0 m</label>${hilfe("gok_relativ")}
      </div>
      ${p.raster_m !== undefined ? html`<p class="leise klein">gerechnet: Puffer ${zahl(Number(p.puffer_m), 0)} m · Raster ${zahl(Number(p.raster_m))} m ·
        Basis ${zahl(Number(p.basis_nhn), 2)} m NHN · Fläche ${zahl(Number(p.flaeche_m2) / 1e4, 2)} ha</p>` : nothing}
    </section>`;
}

function vorgabeTeil() {
  const b = S.modell?.bericht;
  if (!b) return nothing;
  const quelle = S.z!.vorgabe ?? b.vorlage_einheiten;
  const kennung = JSON.stringify(quelle);
  if (!vorgabe || vorgabeFuer !== kennung) {
    vorgabe = quelle.map((v) => ({ name: v.name, bodenarten: v.bodenarten.join(", ") }));
    vorgabeFuer = kennung;
  }
  const v = vorgabe;
  const uebernehmen = () => aendern([{ op: "vorgabe", wert: v.filter((x) => x.name.trim()).map((x) => ({
    name: x.name.trim(), bodenarten: x.bodenarten.split(",").map((t) => t.trim()).filter(Boolean) })) }]);
  return html`
    <section class="karte">
      <h3>Einheiten festlegen ${hilfe("einheiten")}</h3>
      <p class="leise klein">${S.z!.vorgabe ? "Vorgegeben (eigene Einheiten)." : "Automatisch korreliert – hier umbenennen oder Bodenarten zusammenlegen."}</p>
      <table class="tabelle kompakt vorgabe">
        <colgroup><col class="pfeil"><col><col><col class="weg"></colgroup>
        <thead><tr><th></th><th>Einheit</th><th>Bodenarten (mit Komma)</th><th></th></tr></thead>
        <tbody>
          ${v.map((x, i) => html`
            <tr>
              <td class="pfeile"><button class="symbol" ?disabled=${i === 0} @click=${() => { v.splice(i - 1, 0, ...v.splice(i, 1)); neu(); }}>▲</button><button
                class="symbol" ?disabled=${i === v.length - 1} @click=${() => { v.splice(i + 1, 0, ...v.splice(i, 1)); neu(); }}>▼</button></td>
              <td><input .value=${live(x.name)} @input=${(ev: Event) => { x.name = (ev.target as HTMLInputElement).value; }}></td>
              <td><input .value=${live(x.bodenarten)} @input=${(ev: Event) => { x.bodenarten = (ev.target as HTMLInputElement).value; }}></td>
              <td><button class="symbol" title="Zeile löschen" @click=${() => { v.splice(i, 1); neu(); }}>✕</button></td>
            </tr>`)}
        </tbody>
      </table>
      <div class="zeile knopfzeile">
        <button class="link" @click=${() => { v.push({ name: "", bodenarten: "" }); neu(); }}>+ Zeile</button>
        <span class="fueller"></span>
        <button ?disabled=${!S.z!.vorgabe} @click=${() => aendern([{ op: "vorgabe", wert: null }])}>Automatisch korrelieren</button>
        <button class="primaer" @click=${uebernehmen}>Mit diesen Einheiten rechnen</button>
      </div>
    </section>`;
}

export function schrittEinheiten() {
  const m = S.modell;
  const b = m?.bericht;
  const einheit = b?.einheiten.find((e) => e.name === gewaehlt);
  return html`
    <div class="schritt-einheiten">
      <div class="spalte">
        ${einstellungen()}
        ${vorgabeTeil()}
      </div>
      <div class="spalte breit">
        ${S.rechnet ? html`<div class="karte"><div class="kreisel klein"></div> Modell wird gerechnet …</div>` : nothing}
        ${m?.fehler ? html`<div class="karte warnung">Noch kein Modell: ${m.fehler}
          <button class="link" @click=${() => gehe("lage")}>→ Lage setzen</button></div>` : nothing}
        ${b ? html`
          <section class="karte">
            <h3>Einheiten (${b.einheiten.length})</h3>
            <table class="tabelle einheiten">
              <thead><tr><th></th><th>Einheit</th><th>Bodenarten</th><th>Volumen [m³]</th><th>max. Mächtigkeit [m]</th>
                <th title="in Bohrungen vorhanden / fehlt / unter der Endteufe">✓ / – / ?</th><th>Hinweise</th></tr></thead>
              <tbody>
                ${b.einheiten.map((e) => html`
                  <tr class=${e.name === gewaehlt ? "gewaehlt" : ""} @click=${() => { gewaehlt = gewaehlt === e.name ? "" : e.name; neu(); }}>
                    <td><span class="farbfeld" style=${`background:${e.farbe}`}></span></td>
                    <td><b>${e.name}</b></td>
                    <td>${e.bodenarten.join(", ")}</td>
                    <td class="zahl">${Math.round(e.volumen_m3).toLocaleString("de-DE")}</td>
                    <td class="zahl">${zahl(e.maechtigkeit_max_m, 2)}</td>
                    <td class="zahl">${e.bohrungen.vorhanden.length} / ${e.bohrungen.fehlt.length} / ${e.bohrungen.unbekannt.length}</td>
                    <td class="klein">${e.hinweise.join("; ")}</td>
                  </tr>`)}
              </tbody>
            </table>
          </section>
          <section class="karte profil-karte">
            <h3>Einheiten je Bohrung <span class="leise klein">(m NHN, Klick wählt die Einheit)</span></h3>
            <div class="profil-scroll">${einheitenProfil(b, { hoehe: 380, gewaehlt, waehlen: (n) => { gewaehlt = n; neu(); } })}</div>
          </section>
          ${einheit ? html`
            <section class="karte">
              <h3><span class="farbfeld" style=${`background:${einheit.farbe}`}></span> ${einheit.name}: Beschreibungen aus dem PDF</h3>
              <table class="tabelle kompakt">
                <thead><tr><th>Bohrung</th><th>Tiefe [m]</th><th>Bodenart</th><th>Beschreibung</th></tr></thead>
                <tbody>${einheit.schichten.map((s) => html`
                  <tr><td>${s.bohrung}</td><td class="zahl">${zahl(s.von, 2)}–${zahl(s.bis, 2)}</td><td>${s.bodenart ?? "unklassifiziert"}</td>
                    <td>${s.beschreibung || html`<span class="leise">–</span>`}</td></tr>`)}</tbody>
              </table>
            </section>` : nothing}` : nothing}
      </div>
    </div>`;
}
