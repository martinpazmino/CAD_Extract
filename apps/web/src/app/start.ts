// Schritt-App im Vollbild: Kopf mit den fuenf Schritten, darunter der Schritt (und im Schritt Lage/Modell der
// Viewer), unten Zurueck/Weiter. Jeder Schritt fuehrt zum naechsten und zieht ihn nach (Modell rechnen, Viewer).
// Adresse: #/<projekt>/<schritt>/<bohrung> - Neuladen oder Lesezeichen fuehren an dieselbe Stelle.
import "../viewer/viewer.css";
import "./app.css";
import { html, nothing, render } from "lit";
import { api } from "./api";
import { S, SCHRITTE, gehe, neu, oeffnen, projekteLaden, versuchen, zeichnenSetzen, type SchrittId } from "./store";
import { schrittGutachten } from "./schritt_gutachten";
import { schrittBohrungen } from "./schritt_bohrungen";
import { schrittLage } from "./schritt_lage";
import { schrittEinheiten } from "./schritt_einheiten";
import { schrittModell } from "./schritt_modell";

const WEITER: Record<SchrittId, string> = {
  gutachten: "", bohrungen: "Weiter: Lage", lage: "Weiter: Einheiten", einheiten: "Weiter: Modell", modell: "",
};

function schrittZustand(id: SchrittId): "" | "ok" | "warn" {
  const z = S.z;
  if (!z) return "";
  const st = z.pruefstand;
  if (id === "gutachten") return "ok";
  if (id === "bohrungen") return st.unklassifiziert_offen ? "warn" : st.bohrungen[0] === st.bohrungen[1] && st.bohrungen[1] ? "ok" : "";
  if (id === "lage") {
    const ohne = z.viewer.bohrungen.filter((b) => b.x === null).length;
    return ohne ? "warn" : "ok";
  }
  if (id === "einheiten" || id === "modell") return S.modell?.fehler ? "warn" : S.modell?.bericht ? "ok" : "";
  return "";
}

function kopf() {
  const z = S.z;
  return html`
    <header class="kopf">
      <div class="marke" @click=${() => gehe("gutachten")} title="Start">
        <span class="logo">⛰</span>
        <span><b>GroundTwin</b> · Baugrundmodell</span>
      </div>
      <nav class="schritte" aria-label="Schritte">
        ${SCHRITTE.map((s) => {
          const aus = s.id !== "gutachten" && !z;
          const zst = schrittZustand(s.id);
          return html`
            <button class=${`schritt-knopf ${S.schritt === s.id ? "aktiv" : ""} ${zst}`} ?disabled=${aus}
              aria-current=${S.schritt === s.id ? "step" : "false"} @click=${() => gehe(s.id)} title=${s.kurz}>
              <span class="nr">${zst === "ok" && S.schritt !== s.id ? "✓" : zst === "warn" ? "!" : s.nr}</span>
              <span class="titel">${s.titel}</span>
            </button>`;
        })}
      </nav>
      <div class="projekt">
        ${z ? html`<span class="projektname" title=${z.dokumente.map((d) => d.datei).join(", ")}>${z.name}</span>
          <details class="menue">
            <summary title="Projekt">⋯</summary>
            <div class="menue-inhalt" @click=${menueZu}>
              <button @click=${() => gehe("gutachten")}>Anderes Projekt öffnen</button>
              <button @click=${zuruecksetzen}>Alle Korrekturen verwerfen …</button>
              <a href="viewer.html" target="_blank" rel="noopener">Viewer allein öffnen</a>
              ${S.info ? html`<a href=${S.info.quellcode} target="_blank" rel="noopener">Quellcode (${S.info.lizenz})</a>` : nothing}
            </div>
          </details>` : nothing}
      </div>
    </header>`;
}

function menueZu(ev: Event) {
  (ev.currentTarget as HTMLElement).closest("details")?.removeAttribute("open");
}

// Menue schliesst auch bei einem Klick daneben
document.addEventListener("click", (ev) => {
  for (const d of document.querySelectorAll<HTMLDetailsElement>("details.menue[open]")) {
    if (!d.contains(ev.target as Node)) d.removeAttribute("open");
  }
});

async function zuruecksetzen() {
  if (!S.sig || !confirm("Alle Korrekturen, Lagen, Prüfhaken und Eincheckungen dieses Projekts verwerfen?")) return;
  const z = await versuchen(() => api.zuruecksetzen(S.sig));
  if (z) await oeffnen(S.sig, "bohrungen");
}

function fuss() {
  if (S.schritt === "gutachten") return nothing;
  const i = SCHRITTE.findIndex((s) => s.id === S.schritt);
  const zurueck = SCHRITTE[i - 1];
  const weiter = SCHRITTE[i + 1];
  const st = S.z?.pruefstand;
  return html`
    <footer class="fuss">
      ${zurueck ? html`<button @click=${() => gehe(zurueck.id)}>← ${zurueck.titel}</button>` : nothing}
      <span class="fuss-status">${st ? `${st.bohrungen[0]}/${st.bohrungen[1]} Bohrungen · ${st.schichten[0]}/${st.schichten[1]} Schichten geprüft` : ""}
        ${st?.unklassifiziert_offen ? html` · <span class="warnung">⚠ ${st.unklassifiziert_offen} nicht klassifiziert</span>` : nothing}</span>
      <span class="fueller"></span>
      ${weiter && WEITER[S.schritt] ? html`<button class="primaer" @click=${() => gehe(weiter.id)}>${WEITER[S.schritt]} →</button>` : nothing}
    </footer>`;
}

function inhalt() {
  if (S.schritt === "gutachten" || !S.z) return schrittGutachten();
  if (S.schritt === "bohrungen") return schrittBohrungen();
  if (S.schritt === "lage") return schrittLage();
  if (S.schritt === "einheiten") return schrittEinheiten();
  return schrittModell();
}

function app() {
  return html`
    ${kopf()}
    <main class=${`inhalt schritt-${S.schritt}`}>
      <section id="schritt" class="schritt">${inhalt()}</section>
    </main>
    ${fuss()}
    <div class="meldungen" aria-live="polite">
      ${S.meldungen.map((m) => html`<div class=${`meldung ${m.art}`}>${m.text}</div>`)}
    </div>
    ${S.beschaeftigt ? html`<div class="beschaeftigt"><div class="kreisel"></div><span>${S.beschaeftigt}</span></div>` : nothing}`;
}

// Der Viewer liegt ausserhalb von lit (er wird nie neu gezeichnet): #buehne ist ein festes Element in <main>.
const wurzel = document.getElementById("app")!;
let buehne: HTMLElement | null = null;
function zeichnen() {
  render(app(), wurzel);
  const main = wurzel.querySelector("main")!;
  if (!buehne) {
    buehne = document.createElement("div");
    buehne.id = "buehne";
    buehne.className = "buehne";
  }
  if (buehne.parentElement !== main) main.append(buehne);      // main bleibt dasselbe Element: nur beim ersten Mal
  document.body.dataset.schritt = S.schritt;
}
zeichnenSetzen(zeichnen);

async function ausAdresse() {
  const [sig, schritt, bid] = location.hash.replace(/^#\/?/, "").split("/").map(decodeURIComponent);
  if (sig && sig !== S.sig) {
    await oeffnen(sig, (schritt as SchrittId) || undefined);
    if (bid && S.schritt === "bohrungen") {
      const { bohrungWaehlen } = await import("./store");
      await bohrungWaehlen(bid);
    }
  } else if (!sig) {
    await gehe("gutachten");
  }
}

window.addEventListener("hashchange", () => void ausAdresse());
S.info = (await versuchen(() => api.info())) ?? null;
neu();
await projekteLaden();
await ausAdresse();
(window as unknown as { app: typeof S }).app = S;              // fuer die Pruefungen (scripts/check_app.mjs)
