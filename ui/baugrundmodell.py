"""Seite v2: Bodengutachten (PDF) -> Bohrungen pruefen -> Baugrundmodell (IFC4X3) im That-Open-Viewer.

Das Modell entsteht automatisch, sobald Bohrungen mit Lage und Hoehe vorliegen; jede Korrektur in der
Tabelle rechnet es neu. Alles Angenommene (schematische Lage, relative Hoehen, Ausschluesse) wird
angezeigt und steht im IFC (docs/19_app_v2.md).
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from ui import pipeline as pl
from ui import viewer

BEISPIELE = {
    "Berlin V-67b-VE – echte Daten, georeferenziert (5 Bohrungen)": "berlin_v67b.json",
    "Talheim – echte Daten ohne Koordinaten (schematisch)": "talheim.json",
    "Demo – synthetisch, 12 Bohrungen mit Linse": "demo_synthetisch.json",
    "Synthetisches Bohrprofil-PDF (Upload-Ablauf)": "synthetisch_bohrprofil.pdf",
}

CSS = """
<style>
.block-container { padding-top: 2.2rem; }
.kopf h1 { font-size: 1.7rem; margin: 0 0 .2rem 0; }
.kopf p { color: #5f6b7a; margin: 0 0 .6rem 0; }
.schritte { display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: .8rem; margin: .6rem 0 1rem; }
.schritt { border: 1px solid #dde2e8; border-radius: 10px; padding: .9rem 1rem; background: #fff; }
.schritt b { display: block; margin-bottom: .25rem; }
.schritt span { color: #5f6b7a; font-size: .9rem; }
.schritt .nr { display: inline-grid; place-items: center; width: 1.6rem; height: 1.6rem; border-radius: 50%;
  background: #e8f1fd; color: #1e6fd9; font-weight: 600; margin-bottom: .4rem; }
.leiste { display: flex; flex-wrap: wrap; gap: .4rem; margin: .2rem 0 .6rem; }
.chip { border-radius: 999px; padding: .15rem .6rem; font-size: .82rem; background: #eef1f5; color: #1d2330; }
.chip.ok { background: #e3f4e8; color: #17663a; }
.chip.warn { background: #fff6dd; color: #9a6700; }
</style>
"""


def chips(eintraege: list[tuple[str, str]]) -> None:
    html = "".join(f'<span class="chip {art}">{text}</span>' for text, art in eintraege)
    st.markdown(f'<div class="leiste">{html}</div>', unsafe_allow_html=True)


# ---------------------------------------------------------------- Eingabe
st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="kopf"><h1>Baugrundmodell aus dem Bodengutachten</h1>'
            '<p>PDF hochladen · Bohrungen werden erkannt und geprüft · die Bodenschichten entstehen '
            'automatisch als 3D-Modell (IFC 4.3) im That-Open-Viewer.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.subheader("1 · Gutachten")
    dateien = st.file_uploader("Bohrprofile / Anlagen (PDF, mehrere möglich)", type="pdf", accept_multiple_files=True)
    beispiel = st.selectbox("… oder ein Beispiel", ["–"] + list(BEISPIELE), disabled=bool(dateien))
    st.subheader("2 · Optionen")
    ocr_da = pl.ocr_verfuegbar()
    ocr = st.toggle("OCR für Scans und SHX-Text", value=ocr_da, disabled=not ocr_da,
                    help="Liest Raster-PDFs ohne Textlage." if ocr_da else
                    "Nicht installiert: pip install -r requirements-ocr.txt")
    ohne_lage = st.radio("Bohrungen ohne Koordinaten", ["schematisch", "weglassen"],
                         format_func={"schematisch": "schematisch in einer Reihe",
                                      "weglassen": "nicht modellieren"}.get,
                         help="Schematisch nur, wenn keine Bohrung Koordinaten hat; wird im Modell markiert.")
    abstand = st.number_input("Abstand der Reihe [m]", 5.0, 500.0, 20.0, 5.0, disabled=ohne_lage != "schematisch")
    gok_relativ = st.checkbox("Fehlende GOK: Gelände = 0 m (relativ)", value=True,
                              help="Nur wenn keine Bohrung eine GOK hat; wird markiert.")
    methode = st.radio("Interpolation", ["idw", "tps"], horizontal=True,
                       format_func={"idw": "IDW", "tps": "Dünnplatten-Spline"}.get)
    ueberhoehung = st.select_slider("Überhöhung im Viewer", [1, 2, 5, 10], value=5)

quellen: list[tuple[str, bytes]] = [(f.name, f.getvalue()) for f in dateien or []]
docs: list[dict] = []
if not quellen and beispiel != "–":
    pfad = pl.BEISPIELE / BEISPIELE[beispiel]
    if pfad.suffix == ".pdf":
        quellen = [(pfad.name, pfad.read_bytes())]
    else:
        docs = [json.loads(pfad.read_text(encoding="utf-8"))]

if not quellen and not docs:
    st.markdown("""<div class="schritte">
      <div class="schritt"><div class="nr">1</div><b>PDF hochladen</b>
        <span>Bohrprofile, Schichtenverzeichnisse oder ganze Gutachten – Vektor oder Scan.</span></div>
      <div class="schritt"><div class="nr">2</div><b>Bohrungen prüfen</b>
        <span>Erkannte Bohrungen, Schichten, GOK und Koordinaten; Fehlendes direkt in der Tabelle ergänzen.</span></div>
      <div class="schritt"><div class="nr">3</div><b>Baugrundmodell</b>
        <span>Modelleinheiten, Schichtflächen und geschlossene Körper entstehen automatisch.</span></div>
      <div class="schritt"><div class="nr">4</div><b>3D & Export</b>
        <span>That-Open-Viewer mit Schnitten; IFC 4.3, JSON und Prüfbericht herunterladen.</span></div>
    </div>""", unsafe_allow_html=True)
    st.info("⬅️ PDF in der Seitenleiste hochladen oder ein Beispiel wählen.")
    st.stop()

# ---------------------------------------------------------------- Extraktion
fehler: list[tuple[str, str]] = []
if quellen:
    neu = [q for q in quellen if not pl.ist_extrahiert(q[1], ocr)]
    status = st.status("Bohrungen werden erkannt …", expanded=bool(neu)) if neu else None
    for name, daten in quellen:
        balken = status.progress(0.0, text=name) if status and (name, daten) in neu else None

        def melden(seite: int, seiten: int, klasse: str, balken=balken, name=name) -> None:
            if balken:
                balken.progress(seite / seiten, text=f"{name} · Seite {seite}/{seiten} · {klasse}")
        try:
            docs.append(pl.pdf_extrahieren(name, daten, ocr, melden))
        except Exception as err:                       # ein kaputtes PDF stoppt die anderen nicht
            fehler.append((name, f"{type(err).__name__}: {err}"))
    if status:
        status.update(label=f"{len(docs)} Dokument(e) ausgewertet", state="complete", expanded=False)
for name, text in fehler:
    st.error(f"**{name}** konnte nicht ausgewertet werden – {text}")
if not docs:
    st.stop()

signatur = hashlib.sha256(json.dumps(docs, sort_keys=True).encode()).hexdigest()[:12]
alle = [b for d in docs for b in d["boreholes"]]
schichten = [ly for b in alle for ly in b.get("layers") or []]
unsicher = sum(1 for ly in schichten if (ly.get("confidence") or 0) < 0.6 or ly.get("issues"))
k = st.columns(5)
k[0].metric("Bohrungen erkannt", len(alle), border=True)
k[1].metric(f"Schichten ({unsicher} prüfen)" if unsicher else "Schichten", len(schichten), border=True,
            help="Prüfen: Konfidenz unter 0,6 oder mit Hinweis aus der Extraktion")
k[2].metric("mit Koordinaten", sum(1 for b in alle if b.get("x") is not None), border=True)
k[3].metric("mit GOK", sum(1 for b in alle if b.get("gok_nhn") is not None), border=True)
k[4].metric("mit Grundwasser", sum(1 for b in alle if b.get("groundwater")), border=True)
if not alle:
    st.warning("In den Dokumenten wurde keine Bohrung erkannt. Ist eine Seite mit Bohrprofilen dabei? "
               "Bei Scans OCR einschalten.")
    st.stop()

bereich_modell = st.container()
tab_bohr, tab_schicht, tab_einheit, tab_bericht, tab_export = st.tabs(
    ["📍 Bohrungen", "🪨 Schichten", "🧱 Modelleinheiten", "🧾 Prüfbericht", "📦 Export"])

# ---------------------------------------------------------------- Bohrungen pruefen
with tab_bohr:
    st.caption("Grau = aus dem PDF; **GOK, Rechtswert, Hochwert, EPSG** und **Modell** sind änderbar. "
               "Eingetragene Werte werden im Modell als *manuell* markiert. EPSG leer = lokales System.")
    tabelle = pd.DataFrame(pl.zeilen(docs))
    bearbeitet = st.data_editor(
        tabelle, key=f"tabelle_{signatur}", hide_index=True, width="stretch",
        disabled=[c for c in tabelle.columns if c not in ("Modell", "GOK [m NHN]", "Rechtswert", "Hochwert", "EPSG")],
        column_order=["Modell", "Bohrung", "Dokument", "Seite", "GOK [m NHN]", "Endteufe [m]", "Rechtswert",
                      "Hochwert", "EPSG", "Lage aus", "Schichten", "Konfidenz", "Grundwasser", "Hinweise"],
        column_config={
            "Modell": st.column_config.CheckboxColumn("Modell", help="Bohrung ins Baugrundmodell aufnehmen"),
            "GOK [m NHN]": st.column_config.NumberColumn(format="%.2f"),
            "Endteufe [m]": st.column_config.NumberColumn(format="%.2f"),
            "Rechtswert": st.column_config.NumberColumn(format="%.2f"),
            "Hochwert": st.column_config.NumberColumn(format="%.2f"),
            "EPSG": st.column_config.NumberColumn(format="%d", min_value=1000, max_value=99999),
            "Konfidenz": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="%.2f"),
            "Hinweise": st.column_config.TextColumn(width="large"),
        })

einstellungen = pl.Einstellungen(ohne_lage, float(abstand), gok_relativ, methode)
vorbereitung = pl.vorbereiten(docs, bearbeitet.to_dict("records"), einstellungen)

# ---------------------------------------------------------------- Modell rechnen
vorgaben: dict = st.session_state.setdefault("vorgaben", {})
vorgabe = vorgaben.get(signatur)


@st.cache_data(show_spinner=False, max_entries=24)
def modell_gecacht(docs_json: str, vorgabe_json: str, methode: str) -> pl.Ergebnis:
    return pl.modell_rechnen(json.loads(docs_json), json.loads(vorgabe_json), methode)


ergebnis: pl.Ergebnis | None = None
modellfehler = ""
with bereich_modell:
    try:
        with st.spinner("Baugrundmodell wird gerechnet …"):
            ergebnis = modell_gecacht(json.dumps(vorbereitung.docs, sort_keys=True), json.dumps(vorgabe), methode)
    except ValueError as err:
        modellfehler = str(err)

    if ergebnis is None:
        st.warning(f"**Noch kein Baugrundmodell:** {modellfehler}. Für ein Modell braucht jede Bohrung "
                   "eine Lage (Rechts-/Hochwert) und eine GOK – in der Tabelle *Bohrungen* eintragen oder "
                   "links *schematisch* wählen.")
        for h in vorbereitung.hinweise:
            st.caption(f"• {h}")
    else:
        b = ergebnis.bericht
        pr = b["pruefungen"]
        warn = list(vorbereitung.hinweise)                # Annahmen der App; der Modellbericht steht unter Pruefbericht
        chips([(f"{len(b['einheiten'])} Einheiten", ""), (f"{len(b['bohrungen'])} Bohrungen im Modell", ""),
               (f"Lage: EPSG:{b['epsg']}" if b["epsg"] else
                "Lage: schematisch" if any(x["lage"] == "schematisch" for x in b["bohrungen"]) else
                "Lage: lokales System", "" if b["epsg"] else "warn"),
               (f"Abweichung an Bohrungen {pr['max_abweichung_an_bohrungen_m']:.2f} m",
                "ok" if pr["max_abweichung_an_bohrungen_m"] < 0.01 else "warn"),
               ("Körper geschlossen" if pr["alle_koerper_geschlossen"] else "Körper offen",
                "ok" if pr["alle_koerper_geschlossen"] else "warn"),
               (f"{len(b['ausgeschlossen']) + len(vorbereitung.nicht_im_modell)} nicht im Modell",
                "warn" if b["ausgeschlossen"] else "")])
        for h in dict.fromkeys(warn):
            st.warning(h, icon="⚠️")
        if viewer.verfuegbar():
            titel = Path(docs[0]["document"]["file"]).stem if len(docs) == 1 else f"{len(docs)} Dokumente"
            viewer.zeigen(ergebnis.ifc, titel=titel, ueberhoehung=ueberhoehung, hoehe=720, key="viewer")
        else:
            st.error("Viewer nicht gebaut: `cd apps/web && npm install && npm run build`. "
                     "Das IFC steht unter *Export* trotzdem bereit.")

# ---------------------------------------------------------------- Lageplan (nach dem Modell: nur was drin ist)
with tab_bohr:
    im_modell = {x["code"] for x in ergebnis.bericht["bohrungen"]} if ergebnis else set()
    lage = [{"Bohrung": b["code"], "x": b["x"], "y": b["y"], "Lage": b.get("coord_source") or "PDF",
             "Modell": "im Modell" if b["code"] in im_modell else "nicht im Modell"}
            for d in vorbereitung.docs for b in d["boreholes"] if b.get("x") is not None and b.get("y") is not None]
    if lage:
        st.markdown("**Lageplan**")
        df = pd.DataFrame(lage)
        punkte = alt.Chart(df).mark_circle(size=90).encode(
            x=alt.X("x:Q", scale=alt.Scale(zero=False), title="Rechtswert / x [m]", axis=alt.Axis(format=",.0f")),
            y=alt.Y("y:Q", scale=alt.Scale(zero=False), title="Hochwert / y [m]", axis=alt.Axis(format=",.0f")),
            color=alt.Color("Modell:N", scale=alt.Scale(domain=["im Modell", "nicht im Modell"],
                                                       range=["#1e6fd9", "#b8c0cc"]), legend=alt.Legend(title=None)),
            tooltip=["Bohrung", "x", "y", "Lage", "Modell"])
        st.altair_chart((punkte + punkte.mark_text(dy=-12, fontSize=11, color="#1d2330").encode(text="Bohrung"))
                        .properties(height=300), width="stretch")

# ---------------------------------------------------------------- Schichten
with tab_schicht:
    zeilen = []
    for d in docs:
        for b in d["boreholes"]:
            gok = b.get("gok_nhn")
            for ly in b.get("layers") or []:
                zeilen.append({"Bohrung": b["code"], "von": ly["top_depth"], "bis": ly["bottom_depth"],
                               "von NHN": None if gok is None else gok - ly["top_depth"],
                               "bis NHN": None if gok is None else gok - ly["bottom_depth"],
                               "Bodenart": ly.get("soil_class") or "unklassifiziert",
                               "Beschreibung": ly.get("description_raw") or "",
                               "Konfidenz": ly.get("confidence"), "Label": bool(ly.get("label_confirmed")),
                               "Hinweise": "; ".join(ly.get("issues") or []),
                               "Quelle": f"{d['document']['file']} S.{(ly.get('provenance') or [{}])[0].get('page', 0) + 1}"})
    if zeilen:
        df = pd.DataFrame(zeilen)
        nhn = df["von NHN"].notna().all()
        hoehe = st.radio("Höhenbezug", ["m NHN", "Tiefe unter GOK"] if nhn else ["Tiefe unter GOK"], horizontal=True)
        oben, unten = ("von NHN", "bis NHN") if hoehe == "m NHN" else ("von", "bis")
        arten = sorted(df["Bodenart"].unique())
        profil = alt.Chart(df).mark_bar(size=34, stroke="#1d2330", strokeWidth=0.4).encode(
            x=alt.X("Bohrung:N", sort=None, title=None),
            y=alt.Y(f"{oben}:Q", title=hoehe, scale=alt.Scale(zero=False, reverse=hoehe != "m NHN")),
            y2=f"{unten}:Q",
            color=alt.Color("Bodenart:N", scale=alt.Scale(domain=arten, range=[pl.bodenart_farbe(a) for a in arten])),
            tooltip=["Bohrung", "von", "bis", "Bodenart", "Beschreibung", "Konfidenz", "Quelle"])
        st.altair_chart(profil.properties(height=380), width="stretch")
        wahl = st.selectbox("Schichten der Bohrung", list(dict.fromkeys(df["Bohrung"])))
        st.dataframe(df[df["Bohrung"] == wahl].drop(columns=["Bohrung", "von NHN", "bis NHN"]),
                     hide_index=True, width="stretch",
                     column_config={"Konfidenz": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0,
                                                                                 format="%.2f")})
    else:
        st.info("Keine Schichten erkannt.")

# ---------------------------------------------------------------- Modelleinheiten
with tab_einheit:
    if ergebnis is None:
        st.info("Erst wenn ein Modell steht.")
    else:
        einheiten = pd.DataFrame([{
            "Farbe": e["farbe"], "Einheit": e["name"], "Bodenarten": ", ".join(e["bodenarten"]),
            "Volumen [m³]": e["volumen_m3"], "max. Mächtigkeit [m]": e["maechtigkeit_max_m"],
            "vorhanden": len(e["bohrungen"]["vorhanden"]), "fehlt": len(e["bohrungen"]["fehlt"]),
            "unbekannt": len(e["bohrungen"]["unbekannt"]), "Hinweise": "; ".join(e["hinweise"])}
            for e in ergebnis.bericht["einheiten"]])
        stil = einheiten.style.format({"Volumen [m³]": "{:,.0f}", "max. Mächtigkeit [m]": "{:.2f}"})
        faerben = getattr(stil, "map", None) or stil.applymap          # pandas < 2.1: applymap
        st.dataframe(faerben(lambda f: f"background-color: {f}; color: {f}", subset=["Farbe"]),
                     hide_index=True, width="stretch")
        st.markdown("**Einheiten festlegen** – umbenennen, Bodenarten zusammenlegen (`Sand, Kies`), Reihenfolge "
                    "von oben nach unten. Ohne Festlegung korreliert das Programm selbst.")
        vorlage = pd.DataFrame([{"Einheit": v["name"], "Bodenarten": ", ".join(v["bodenarten"])}
                                for v in (vorgabe or ergebnis.bericht["vorlage_einheiten"])])
        neu = st.data_editor(vorlage, key=f"vorgabe_{signatur}", num_rows="dynamic", hide_index=True,
                             width="stretch")
        c1, c2 = st.columns([1, 1])
        if c1.button("Mit diesen Einheiten neu rechnen", type="primary"):
            vorgaben[signatur] = [{"name": str(z["Einheit"]).strip(),
                                   "bodenarten": [t.strip() for t in str(z["Bodenarten"]).split(",") if t.strip()]}
                                  for z in neu.to_dict("records") if str(z.get("Einheit") or "").strip()]
            st.rerun()
        if c2.button("Automatisch korrelieren", disabled=vorgabe is None):
            vorgaben.pop(signatur, None)
            st.rerun()

# ---------------------------------------------------------------- Pruefbericht
with tab_bericht:
    if ergebnis is None:
        st.info("Erst wenn ein Modell steht.")
    else:
        b = ergebnis.bericht
        raus = vorbereitung.nicht_im_modell + b["ausgeschlossen"]
        if raus:
            st.markdown("**Nicht im Modell**")
            st.dataframe(pd.DataFrame(raus).rename(columns={"code": "Bohrung", "dokument": "Dokument", "grund": "Grund"}),
                         hide_index=True, width="stretch")
        st.markdown("**Einheiten je Bohrung** (✓ vorhanden · – fehlt · ? unter der Endteufe)")
        zeichen = {"vorhanden": "✓", "fehlt": "–", "unbekannt": "?"}
        matrix = pd.DataFrame([{"Bohrung": x["code"], "Lage": x["lage"], "Höhe": x["hoehe"],
                                **{e["einheit"]: zeichen[e["status"]] for e in x["einheiten"]}} for x in b["bohrungen"]])
        st.dataframe(matrix, hide_index=True, width="stretch")
        hinweise = [f"{x['code']}: {h}" for x in b["bohrungen"] for h in x["hinweise"]] + b["hinweise"]
        if hinweise:
            st.markdown("**Hinweise**")
            for h in hinweise:
                st.caption(f"• {h}")
        st.markdown("**Parameter**")
        st.json(b["parameter"], expanded=False)

# ---------------------------------------------------------------- Export
with tab_export:
    stamm = Path(docs[0]["document"]["file"]).stem if len(docs) == 1 else "baugrundmodell"
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Modell**")
        if ergebnis is not None:
            st.download_button("⬇️ Baugrundmodell (IFC 4.3)", ergebnis.ifc, f"{stamm}.ifc", "application/x-step",
                               type="primary", width="stretch")
            st.download_button("⬇️ Prüfbericht (JSON)", pl.json_bytes(ergebnis.bericht), f"{stamm}_bericht.json",
                               "application/json", width="stretch")
            st.download_button("⬇️ Einheiten-Vorlage (JSON, für --einheiten)",
                               pl.json_bytes(ergebnis.bericht["vorlage_einheiten"]), f"{stamm}_einheiten.json",
                               "application/json", width="stretch")
        else:
            st.caption("Noch kein Modell.")
    with c2:
        st.markdown("**Daten**")
        st.download_button("⬇️ Extraktion (kanonisches JSON)", pl.json_bytes(docs if len(docs) > 1 else docs[0]),
                           f"{stamm}_extraktion.json", "application/json", width="stretch")
        st.download_button("⬇️ Modell-Eingabe mit Korrekturen (JSON)", pl.json_bytes(vorbereitung.docs),
                           f"{stamm}_modell_eingabe.json", "application/json", width="stretch")
    st.caption("IFC öffnen: hier im Viewer, in apps/web (`npm run dev`) oder in jedem IFC-4.3-Programm. "
               "Kommandozeile: `python -m baugrundmodell modell.ifc extraktion.json` (services/modeler).")
