// Hilfe zu jeder Einstellung: ein "?" neben dem Feld oeffnet eine kurze Erklaerung (Esc oder Klick daneben schliesst).
import { html } from "lit";

export const TEXTE = {
  ocr: ["OCR für Scans", "Liest gescannte PDFs und Text, der nur als Linien gezeichnet ist (SHX). Langsamer; bei Vektor-PDFs nicht nötig."],
  beispiele: ["Beispiele", "Fertig ausgewertete Gutachten zum Ausprobieren. Echte Daten: Berlin (georeferenziert) und Talheim (ohne Koordinaten)."],
  pruefstand: ["Prüfstand", "Wie viele Bohrungen und Schichten Sie geprüft haben. Eine Korrektur zählt als geprüft. Der Stand wird beim Einchecken festgehalten."],
  alle_pruefen: ["Alle geprüft", "Markiert alle Schichten aller Bohrungen im Modell als geprüft – nur wenn Sie alles mit dem Gutachten verglichen haben. Zurücknehmen ist jederzeit möglich."],
  warnung: ["Warnung", "Eine Schicht, deren Bodenart nicht erkannt wurde (unklassifiziert). Bodenart wählen, den Vorschlag nach Norm übernehmen oder die Schicht als geprüft markieren."],
  bodenart: ["Bodenart", "Klasse für das Modell; Farbe nach DIN 4023 (Kies gelb, Sand orange, Schluff oliv, Ton violett …). Gleiche Bodenarten werden zu Einheiten verbunden."],
  norm: ["Deutung nach Norm", "Die Beschreibung aus dem PDF gelesen nach DIN 4023 / DIN EN ISO 14688-1: Hauptanteil, Nebenanteile (schwach ' / stark ¯), Kurzzeichen, Bodengruppe nach DIN 18196 (nur wenn genannt), Konsistenz. Steht auch im IFC (CPset_Bodenansprache)."],
  vorschlag: ["Vorschlag nach Norm", "Für eine unklassifizierte Schicht schlägt die Normen-Datenbank eine Bodenart aus der Beschreibung vor. Sie wird nur übernommen, wenn Sie klicken; danach gilt die Schicht als korrigiert."],
  geprueft: ["Geprüft", "Haken: Schicht mit dem Gutachten verglichen. Steht im IFC (Geprueft) und im Prüfstand."],
  tiefe: ["Tiefe", "Ober- und Unterkante in m unter Geländeoberkante (GOK). Geändertes wird als korrigiert markiert."],
  gok: ["GOK", "Ansatzhöhe der Bohrung in m NHN. Aus dem PDF oder hier eingetragen (manuell). Ohne GOK bei allen Bohrungen rechnet das Modell relativ (Gelände = 0 m)."],
  koordinaten: ["Koordinaten", "Rechts- und Hochwert der Bohrung; leer lassen, wenn die Lage im Schritt Lage auf dem Plan gesetzt wird."],
  entfernen: ["Entfernen", "Die Bohrung kommt nicht ins Modell (sie bleibt in der Liste unter „Entfernt“ und lässt sich wiederherstellen)."],
  quelle: ["Quelle im PDF", "Die Seite des Gutachtens, auf der die Bohrung erkannt wurde; der Rahmen zeigt die gewählte Schicht."],
  lage_art: ["Art der Lage", "Koordinaten: Bohrungen mit Rechts-/Hochwert (aus dem PDF, eingetragen oder auf dem Lageplan gesetzt). Reihe: ohne Koordinaten nebeneinander mit Abständen bzw. Stationen aus dem Längsschnitt."],
  unterlage: ["Unterlage", "Lageplan (Draufsicht) oder Längsschnitt (Seitenansicht) als PDF. Er liegt im Viewer unter den Bohrungen; nach dem Kalibrieren werden die Bohrungen daraufgezogen."],
  massstab: ["Maßstab", "Zwei Punkte auf dem Plan anklicken, deren Abstand Sie kennen (Maßstabsleiste, Bemaßung, zwei Bohrungen), und die wahre Länge in m eintragen. Oder den Maßstab 1:n direkt angeben."],
  bezug: ["Bezugspunkt", "Ein Punkt im Plan mit bekannter Koordinate (Koordinatenkreuz, Bohrung mit Koordinaten): anklicken und Rechts-/Hochwert eintragen – im Längsschnitt Station und Höhe NHN."],
  drehung: ["Drehung", "Winkel, um den der Plan gegen Norden gedreht ist (gegen den Uhrzeigersinn positiv). Nordpfeil nach oben = 0°; Nordpfeil 10° nach links geneigt = 10°."],
  hoehe: ["Höhenmaßstab", "Längsschnitte sind oft überhöht (z. B. Länge 1:500, Höhe 1:100). Ohne Angabe gilt der Längenmaßstab."],
  epsg: ["Koordinatensystem (EPSG)", "System der Rechts-/Hochwerte aus der Liste wählen: in Deutschland meist ETRS89 / UTM 32N (25832), im Osten 33N (25833), ältere Pläne Gauß-Krüger (Rechtswert 7-stellig, erste Ziffer = Zone); dazu Schweiz und Österreich. Passen die Werte nicht zum System (Ziffernzahl, Zonenkennung), erscheint ein Hinweis. Steht im IFC (IfcMapConversion)."],
  sperren: ["Sperren", "Schloss zu: der Plan liegt fest und ändert sich nicht mehr; jetzt die Bohrungen ziehen. Auf dem Lageplan nur in x/y, im Längsschnitt entlang der Station – in der Höhe nur, wenn das PDF keine GOK hat."],
  deckkraft: ["Deckkraft", "Wie stark der Plan die Szene überdeckt."],
  ohne_lage: ["Ohne Lage", "Bohrungen ohne Koordinaten: anklicken und dann in den gesperrten Plan klicken (Punkte setzen) – oder mit der Maus aus der Liste auf den Plan ziehen."],
  punkte: ["Punkte setzen", "Modus an, dann in den gesperrten Lageplan klicken: die gewählte Bohrung bekommt die Lage, danach ist die nächste ohne Lage dran (oder einen Chip anklicken). Mit „freien Punkt“ entsteht ein Punkt ◆, den Sie in der Liste einer Bohrung zuordnen. ✕ löscht einen Punkt bzw. die gesetzte Lage – im Viewer ebenso: Marke anklicken, Entf. Esc beendet den Modus."],
  reihe: ["Reihe", "Bohrungen in einer Linie. Abstand zum Vorgänger je Bohrung eintragen (BK1 → BK2 10 m, BK2 → BK3 15 m) oder eine Station; ohne Eintrag gilt der Standardabstand. Reihenfolge mit den Pfeilen."],
  standardabstand: ["Standardabstand", "Abstand zwischen Bohrungen, für die nichts eingetragen ist (nur zur Anschauung, im Modell als schematisch markiert)."],
  durchmesser: ["Durchmesser", "Dicke der Bohrsäulen im Viewer und im IFC (Darstellung, nicht der Bohrdurchmesser im Feld). Automatisch wächst er mit der Modellgröße, damit Säulen auf langen Trassen sichtbar bleiben."],
  einheiten: ["Einheiten", "Modelleinheiten verbinden gleiche Bodenarten zwischen den Bohrungen (Sand 1, Kies, Sand 2). Umbenennen oder Bodenarten zusammenlegen (z. B. „Sand, Kies“ als eine Einheit); Reihenfolge von oben nach unten."],
  methode: ["Interpolation", "IDW: gewichtetes Mittel der Nachbarbohrungen, ruhig und sicher. Dünnplatten-Spline: glatte Flächen mit Trend, gut bei geneigten Schichten."],
  puffer: ["Puffer", "Wie weit das Modell über die Bohrungen hinausreicht. Automatisch: halber Bohrabstand (5–100 m)."],
  raster: ["Raster", "Maschenweite der Schichtflächen. Automatisch: Gebietsgröße/40, bei großen Modellen gröber (höchstens 30 000 Knoten)."],
  basis: ["Modellbasis", "Unterkante des Modells in m NHN. Automatisch: tiefste Endteufe."],
  gok_relativ: ["Fehlende GOK", "Hat keine Bohrung eine GOK, rechnet das Modell relativ (Gelände = 0 m) – markiert im IFC."],
  auto: ["Automatisch nachführen", "Jede Änderung (Tabelle, Lage, Einheiten) rechnet das Modell sofort neu."],
  einchecken: ["Einchecken", "Hält den Prüfstand fest (Zeit, Zähler, Fingerabdruck des Modells, Kommentar). Das exportierte IFC trägt ihn (CPset_Baugrundmodell.Pruefstand)."],
  export: ["Export", "IFC 4.3 mit Prüfstand, Bodenansprache je Schicht und Beschreibungen je Einheit; dazu Prüfbericht und die Daten als JSON."],
  ueberhoehung: ["Überhöhung", "Höhen im Viewer mal Faktor, damit dünne Schichten sichtbar werden. Die Koordinaten bleiben echt."],
} as const;

export type HilfeSchluessel = keyof typeof TEXTE;

let blase: HTMLDivElement | null = null;
let offenFuer: HTMLElement | null = null;

function schliessen() {
  blase?.remove();
  blase = null;
  offenFuer = null;
}

function zeigen(ev: Event, k: HilfeSchluessel) {
  ev.preventDefault();
  ev.stopPropagation();
  const knopf = ev.currentTarget as HTMLElement;
  if (offenFuer === knopf) {
    schliessen();
    return;
  }
  schliessen();
  const [titel, text] = TEXTE[k];
  blase = document.createElement("div");
  blase.className = "hilfe-blase";
  blase.setAttribute("role", "tooltip");
  blase.innerHTML = `<strong></strong><p></p>`;
  blase.querySelector("strong")!.textContent = titel;
  blase.querySelector("p")!.textContent = text;
  document.body.append(blase);
  const r = knopf.getBoundingClientRect();
  const b = blase.getBoundingClientRect();
  const links = Math.min(Math.max(8, r.left + r.width / 2 - b.width / 2), window.innerWidth - b.width - 8);
  const oben = r.bottom + 8 + b.height > window.innerHeight ? r.top - b.height - 8 : r.bottom + 8;
  Object.assign(blase.style, { left: `${links}px`, top: `${oben}px` });
  offenFuer = knopf;
}

document.addEventListener("click", (ev) => {
  if (blase && !blase.contains(ev.target as Node)) schliessen();
});
document.addEventListener("keydown", (ev) => {
  if (ev.key === "Escape") schliessen();
});

/** "?"-Knopf mit der Erklaerung einer Einstellung. */
export const hilfe = (k: HilfeSchluessel) =>
  html`<button type="button" class="hilfe" title=${TEXTE[k][0]} aria-label=${`Hilfe: ${TEXTE[k][0]}`}
    @click=${(e: Event) => zeigen(e, k)}>?</button>`;
