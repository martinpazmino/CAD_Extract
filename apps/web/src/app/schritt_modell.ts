// Schritt 5 · Modell: das Baugrundmodell im Viewer (Vollbild), rechts Pruefstand, Einchecken, Export und Hinweise.
import { html, nothing } from "lit";
import { api } from "./api";
import { hilfe } from "./hilfe";
import { S, aendern, gehe, modellRechnen, versuchen, zustandUebernehmen, neu, melden } from "./store";

let kommentar = "";

async function einchecken() {
  const r = await versuchen(() => api.einchecken(S.sig, kommentar));
  if (r) {
    zustandUebernehmen(r.zustand);
    kommentar = "";
    melden(`Eingecheckt: v${r.eintrag.nr} · ${r.eintrag.stand.bohrungen[0]}/${r.eintrag.stand.bohrungen[1]} Bohrungen geprüft`, "ok");
    neu();
  }
}

export function schrittModell() {
  const z = S.z!;
  const m = S.modell;
  const b = m?.bericht;
  const st = z.pruefstand;
  const letzter = z.eincheckungen[z.eincheckungen.length - 1];
  const exporte: [string, string][] = [["ifc", "Baugrundmodell (IFC 4.3)"], ["bericht", "Prüfbericht (JSON)"],
    ["einheiten", "Einheiten-Vorlage (JSON)"], ["extraktion", "Extraktion (JSON)"], ["eingabe", "Modell-Eingabe mit Korrekturen (JSON)"],
    ["projekt", "Projektstand (JSON)"]];
  return html`
    <div class="app-panel rechts">
      <section class="abschnitt-flach">
        <h3>Modell</h3>
        ${S.rechnet ? html`<p><span class="kreisel klein"></span> wird gerechnet …</p>` : nothing}
        ${m?.fehler ? html`<p class="warnung">Noch kein Modell: ${m.fehler}</p>
          <button class="link" @click=${() => gehe("lage")}>→ Lage setzen</button>` : nothing}
        ${b ? html`
          <ul class="kennzahlen">
            <li><b>${b.einheiten.length}</b> Einheiten</li>
            <li><b>${b.bohrungen.length}</b> Bohrungen im Modell</li>
            <li class=${b.epsg ? "" : "warn"}>${b.epsg ? `EPSG:${b.epsg}` : "lokales System"}</li>
            <li class=${b.pruefungen.alle_koerper_geschlossen ? "ok" : "warn"}>${b.pruefungen.alle_koerper_geschlossen ? "Körper geschlossen" : "Körper offen"}</li>
            <li class=${b.pruefungen.max_abweichung_an_bohrungen_m < 0.01 ? "ok" : "warn"}>Abweichung an Bohrungen ${b.pruefungen.max_abweichung_an_bohrungen_m.toFixed(3)} m</li>
          </ul>` : nothing}
        <div class="zeile">
          <label class="inline"><input type="checkbox" .checked=${z.auto} @change=${(e: Event) => aendern([{ op: "auto", wert: (e.target as HTMLInputElement).checked }], { leise: true })}>
            automatisch nachführen</label>${hilfe("auto")}
          <span class="fueller"></span>
          <button ?disabled=${S.rechnet} @click=${() => modellRechnen()}>Neu rechnen</button>
        </div>
        <label class="inline">Überhöhung ${hilfe("ueberhoehung")}
          <select @change=${async (e: Event) => {
            const f = Number((e.target as HTMLSelectElement).value);
            await S.viewer?.ueberhoehen(f);                // erst der Viewer (Kamera passt sich an), dann der Stand
            await aendern([{ op: "ueberhoehung", wert: f }], { leise: true });
          }}>
            ${[1, 2, 5, 10, 20].map((f) => html`<option value=${f} .selected=${z.ueberhoehung === f}>${f}×</option>`)}
          </select></label>
      </section>

      <section class="abschnitt-flach">
        <h3>Prüfstand ${hilfe("pruefstand")}</h3>
        <div class="balken"><span>Bohrungen <b>${st.bohrungen[0]}/${st.bohrungen[1]}</b></span><progress max=${st.bohrungen[1] || 1} value=${st.bohrungen[0]}></progress></div>
        <div class="balken"><span>Schichten <b>${st.schichten[0]}/${st.schichten[1]}</b></span><progress max=${st.schichten[1] || 1} value=${st.schichten[0]}></progress></div>
        <p class="klein">${st.unklassifiziert_offen ? html`<span class="warnung">⚠ ${st.unklassifiziert_offen} Schicht(en) nicht klassifiziert</span>
          <button class="link" @click=${() => gehe("bohrungen")}>prüfen</button>` : html`<span class="ok">✓ keine offenen Warnungen</span>`}
          · ${st.korrigiert} korrigiert · ${st.manuelle_lage} Lagen manuell · ${st.entfernt} entfernt</p>
        <p class=${`klein ${letzter && !z.seit_einchecken_geaendert ? "ok" : "warn"}`}>
          ${letzter ? `Eingecheckt: ${z.eingecheckt}${z.seit_einchecken_geaendert ? " · seitdem geändert" : ""}` : "noch nicht eingecheckt"}</p>
        <div class="zeile">
          <input class="breit" placeholder="Kommentar (z. B. BK1–BK5 mit Anlage 2 verglichen)" .value=${kommentar}
            @input=${(e: Event) => { kommentar = (e.target as HTMLInputElement).value; }}>
        </div>
        <div class="zeile"><button class="primaer" @click=${einchecken}>✓ Stand einchecken</button>${hilfe("einchecken")}</div>
        ${z.eincheckungen.length ? html`
          <details class="protokoll"><summary>Protokoll (${z.eincheckungen.length})</summary>
            <ul>${[...z.eincheckungen].reverse().map((e) => html`
              <li><b>v${e.nr}</b> ${e.zeit} · ${e.stand.bohrungen[0]}/${e.stand.bohrungen[1]} Bohrungen, ${e.stand.schichten[0]}/${e.stand.schichten[1]} Schichten
                ${e.kommentar ? html`<div class="leise klein">${e.kommentar}</div>` : nothing}</li>`)}</ul>
          </details>` : nothing}
      </section>

      <section class="abschnitt-flach">
        <h3>Export ${hilfe("export")}</h3>
        <div class="export-liste">
          ${exporte.map(([art, titel]) => html`<a class=${`knopf ${art === "ifc" ? "primaer" : ""}`} href=${api.exportUrl(S.sig, art)}
            download>${titel}</a>`)}
        </div>
      </section>

      ${m && (m.hinweise.length || m.nicht_im_modell.length) ? html`
        <section class="abschnitt-flach">
          <h3>Hinweise</h3>
          ${m.nicht_im_modell.length ? html`<p class="klein"><b>Nicht im Modell:</b> ${m.nicht_im_modell.map((x) => `${x.code} (${x.grund})`).join(", ")}</p>` : nothing}
          ${m.hinweise.map((h) => html`<p class="klein">ℹ ${h}</p>`)}
        </section>` : nothing}
    </div>`;
}
