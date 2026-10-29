// Schritt 1 · Gutachten: PDF hochladen (Fortschritt je Seite), Beispiel waehlen oder ein Projekt weiterfuehren.
import { html, nothing } from "lit";
import { api } from "./api";
import { hilfe } from "./hilfe";
import { S, melden, neu, oeffnen, projekteLaden, versuchen } from "./store";

let gewaehlt: File[] = [];
let ocr = true;
let ziehen = false;

async function warten(aid: string) {
  for (;;) {
    const a = await versuchen(() => api.auftrag(aid));
    if (!a) return;
    S.auftrag = a;
    neu();
    if (a.fertig) {
      S.auftrag = null;
      for (const f of a.fehler) melden(f, "fehler", 10000);
      if (a.projekt) {
        gewaehlt = [];
        await oeffnen(a.projekt, "bohrungen");
      } else neu();
      return;
    }
    await new Promise((r) => setTimeout(r, 600));
  }
}

async function auswerten() {
  if (!gewaehlt.length) return;
  const a = await versuchen(() => api.gutachten(gewaehlt, ocr && !!S.info?.ocr));
  if (a) await warten(a.id);
}

async function beispiel(name: string) {
  const r = await versuchen(() => api.beispiel(name), "Beispiel wird geöffnet …");
  if (r?.projekt) await oeffnen(r.projekt, "bohrungen");
  else if (r?.auftrag) await warten(r.auftrag);
}

function dateienSetzen(liste: FileList | null | undefined) {
  gewaehlt = [...(liste ?? [])].filter((f) => /\.(pdf|json)$/i.test(f.name));
  if (liste?.length && !gewaehlt.length) melden("Bitte PDF-Dateien wählen (oder eine Extraktion als JSON).", "warn");
  neu();
}

async function entfernen(sig: string, name: string) {
  if (!confirm(`Projekt „${name}“ mit allen Korrekturen löschen? Das Gutachten selbst bleibt unberührt.`)) return;
  await versuchen(() => api.loeschen(sig));
  await projekteLaden();
}

export function schrittGutachten() {
  const a = S.auftrag;
  const ocrDa = !!S.info?.ocr;
  return html`
    <div class="seite-mitte">
      <section class="karte gross">
        <h2>Bodengutachten auswerten</h2>
        <p class="leise">Bohrprofile, Schichtenverzeichnisse oder ganze Gutachten als PDF – Vektor oder Scan. Die Bohrungen
          werden erkannt; im nächsten Schritt prüfen und korrigieren Sie sie.</p>
        ${a ? html`
          <div class="fortschritt-karte" aria-live="polite">
            <div class="kreisel klein"></div>
            <div>
              <strong>${a.stand.datei || a.dateien[0]}</strong>
              <span class="leise">Datei ${a.stand.nr}/${a.stand.dateien || a.dateien.length}
                ${a.stand.seiten ? html` · Seite ${a.stand.seite}/${a.stand.seiten}${a.stand.klasse ? ` · ${a.stand.klasse}` : ""}` : " · wird geöffnet …"}</span>
              <progress max=${a.stand.seiten || 1} value=${a.stand.seite}></progress>
            </div>
          </div>` : html`
          <label class=${`ablage ${ziehen ? "ueber" : ""}`}
            @dragover=${(e: DragEvent) => { e.preventDefault(); ziehen = true; neu(); }}
            @dragleave=${() => { ziehen = false; neu(); }}
            @drop=${(e: DragEvent) => { e.preventDefault(); ziehen = false; dateienSetzen(e.dataTransfer?.files); }}>
            <input type="file" accept=".pdf,application/pdf,.json,application/json" multiple @change=${(e: Event) => dateienSetzen((e.target as HTMLInputElement).files)}>
            <span class="ablage-icon">⇪</span>
            <strong>${gewaehlt.length ? gewaehlt.map((f) => f.name).join(", ") : "PDF hierher ziehen oder klicken"}</strong>
            <span class="leise">${gewaehlt.length ? `${gewaehlt.length} Datei(en) bereit` : "mehrere Dateien möglich (z. B. Anlagen 2–4) · auch eine Extraktion als JSON"}</span>
          </label>
          <div class="zeile">
            <label class="schalter" title=${ocrDa ? "" : "nicht installiert: pip install -r requirements-ocr.txt"}>
              <input type="checkbox" .checked=${ocr && ocrDa} ?disabled=${!ocrDa} @change=${(e: Event) => { ocr = (e.target as HTMLInputElement).checked; }}>
              OCR für Scans ${ocrDa ? "" : "(nicht installiert)"}
            </label>${hilfe("ocr")}
            <span class="fueller"></span>
            <button class="primaer" ?disabled=${!gewaehlt.length} @click=${auswerten}>Auswerten →</button>
          </div>`}
      </section>

      <div class="zwei-spalten">
        <section class="karte">
          <h3>Beispiele ${hilfe("beispiele")}</h3>
          <ul class="auswahl-liste">
            ${(S.info?.beispiele ?? []).map((b) => html`
              <li><button class="link" ?disabled=${!!a} @click=${() => beispiel(b.name)}>${b.titel}</button></li>`)}
          </ul>
        </section>
        <section class="karte">
          <h3>Zuletzt bearbeitet</h3>
          ${S.projekte.length ? html`
            <table class="tabelle kompakt">
              <thead><tr><th>Projekt</th><th>Bohrungen</th><th>geprüft</th><th>geändert</th><th></th></tr></thead>
              <tbody>
                ${S.projekte.map((p) => html`
                  <tr>
                    <td><button class="link" @click=${() => oeffnen(p.signatur)}>${p.name}</button>
                      <div class="leise klein">${p.dokumente.join(", ")}</div></td>
                    <td class="zahl">${p.bohrungen}</td>
                    <td class="zahl">${p.geprueft}${p.eincheckungen ? html` · <span title="eingecheckt">✓${p.eincheckungen}</span>` : nothing}</td>
                    <td class="leise klein">${p.geaendert}</td>
                    <td><button class="symbol" title="Projekt löschen" aria-label="Projekt löschen" @click=${() => entfernen(p.signatur, p.name)}>🗑</button></td>
                  </tr>`)}
              </tbody>
            </table>` : html`<p class="leise">Noch keine Projekte. Ein Projekt entsteht beim ersten Auswerten und wird automatisch gesichert.</p>`}
        </section>
      </div>
      ${S.info ? html`<p class="leise klein impressum">GeoIM ${S.info.version} · freie Software unter
        <a href=${`${S.info.quellcode}/blob/main/LICENSE`} target="_blank" rel="noopener">${S.info.lizenz}</a> ·
        <a href=${S.info.quellcode} target="_blank" rel="noopener">Quellcode</a> · die App extrahiert und schlägt vor;
        die Interpretation und Freigabe bleibt beim Geotechniker.</p>` : nothing}
    </div>`;
}
