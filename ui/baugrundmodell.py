"""Seite v2: Bodengutachten (PDF) -> Tabellen pruefen -> Lage setzen -> Baugrundmodell erzeugen -> nachfuehren.

Ablauf (docs/20_lage_pruefung_viewer.md):
1. PDF hochladen: Bohrungen und Schichten werden erkannt und als Tabellen gezeigt, noch ohne Modell.
2. Pruefen: Werte korrigieren, Bohrungen/Schichten als geprueft markieren (Pruefstand oben).
3. Lage: Koordinaten aus dem PDF, aus der Tabelle oder im Viewer auf einem Lageplan gesetzt; ohne Koordinaten
   eine Reihe mit eigenen Abstaenden (BK1 -> BK2 10 m, BK2 -> BK3 15 m) oder Stationen aus dem Laengsschnitt.
4. "Baugrundmodell erzeugen"; danach rechnet jede Aenderung das Modell automatisch nach.
5. Einchecken: der Pruefstand wird mit Zeit, Zaehlern und Modell-Fingerabdruck festgehalten.
Der Projektstand (alle Korrekturen) wird automatisch gesichert und beim gleichen PDF wieder geladen.
"""
from __future__ import annotations

import hashlib
import json
from collections import Counter
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

from ui import pipeline as pl
from ui import projekt as pj
from ui import viewer

BEISPIELE = {
    "Berlin V-67b-VE – echte Daten, georeferenziert (5 Bohrungen)": "berlin_v67b.json",
    "Talheim – echte Daten ohne Koordinaten (Reihe)": "talheim.json",
    "Demo – synthetisch, 12 Bohrungen mit Linse": "demo_synthetisch.json",
    "Trasse – synthetisch, 6 km, 51 Bohrungen": "trasse_synthetisch.json",
    "Synthetisches Bohrprofil-PDF (Upload-Ablauf)": "synthetisch_bohrprofil.pdf",
}
LAGE_TEXT = {pj.LAGE_KOORDINATEN: "Koordinaten (Lageplan)", pj.LAGE_REIHE: "Reihe (Längsschnitt)"}
ART_TEXT = {"plan": "Lageplan (Draufsicht)", "schnitt": "Längsschnitt (Seitenansicht)"}

CSS = """
<style>
.block-container { padding-top: 2.2rem; }
.kopf h1 { font-size: 1.7rem; margin: 0 0 .2rem 0; }
.kopf p { color: #5f6b7a; margin: 0 0 .6rem 0; }
.schritte { display: grid; grid-template-columns: repeat(auto-fit, minmax(190px, 1fr)); gap: .8rem; margin: .6rem 0 1rem; }
.schritt { border: 1px solid #dde2e8; border-radius: 10px; padding: .9rem 1rem; background: #fff; }
.schritt b { display: block; margin-bottom: .25rem; }
.schritt span { color: #5f6b7a; font-size: .9rem; }
.schritt .nr { display: inline-grid; place-items: center; width: 1.6rem; height: 1.6rem; border-radius: 50%;
  background: #e6f0d0; color: #3d5a00; font-weight: 600; margin-bottom: .4rem; }
.leiste { display: flex; flex-wrap: wrap; gap: .4rem; margin: .2rem 0 .6rem; }
.chip { border-radius: 999px; padding: .15rem .6rem; font-size: .82rem; background: #eef1f5; color: #1d2330; }
.chip.ok { background: #e3f4e8; color: #17663a; }
.chip.warn { background: #fff6dd; color: #9a6700; }
.abschnitt { font-weight: 600; font-size: 1.05rem; margin: .4rem 0 .2rem; }
</style>
"""


def chips(eintraege: list[tuple[str, str]]) -> None:
    html = "".join(f'<span class="chip {art}">{text}</span>' for text, art in eintraege if text)
    st.markdown(f'<div class="leiste">{html}</div>', unsafe_allow_html=True)


def zahl(v, default=None):
    f = pj.zahl(v)
    return default if f is None else f


# ---------------------------------------------------------------- Projektstand (Sitzung + Platte)
def projekt_ablage(signatur: str) -> Path:
    return pl.ARBEIT / "projekte" / f"{signatur}.json"


def projekt_fuer(docs: list[dict], signatur: str) -> pj.Projekt:
    alle: dict = st.session_state.setdefault("projekte", {})
    if signatur not in alle:
        datei = projekt_ablage(signatur)
        p = None
        if datei.exists():
            try:
                p = pj.laden(json.loads(datei.read_text(encoding="utf-8")))
                st.toast("Gespeicherter Projektstand geladen (Korrekturen, Lage, Prüfung).", icon="💾")
            except (ValueError, TypeError, KeyError):
                p = None                                   # alte oder kaputte Ablage: neu beginnen
        alle[signatur] = p or pj.neues_projekt(docs, signatur)
    return alle[signatur]


def sichern(p: pj.Projekt) -> None:
    text = json.dumps(pj.speichern(p), ensure_ascii=False)
    schluessel = f"_gesichert_{p.signatur}"
    if st.session_state.get(schluessel) != text:
        datei = projekt_ablage(p.signatur)
        datei.parent.mkdir(parents=True, exist_ok=True)
        datei.write_text(text, encoding="utf-8")
        st.session_state[schluessel] = text


def ereignis_text(e: dict, codes: dict[str, str]) -> str:
    code = codes.get(str(e.get("id")), str(e.get("id", "")))
    return {"lage": lambda: f"{code}: Lage übernommen (R {e['x']:,.2f} · H {e['y']:,.2f})",
            "station": lambda: f"{code}: Station {e['station']:,.2f} m übernommen",
            "gok": lambda: f"{code}: GOK {e['gok']:,.2f} m NHN übernommen",
            "kalibrierung": lambda: "Unterlage kalibriert",
            "geprueft": lambda: f"{code}: {'als geprüft markiert' if e.get('wert') else 'Prüfung zurückgenommen'}",
            }.get(e.get("typ"), lambda: "Änderung aus dem Viewer übernommen")()


# ---------------------------------------------------------------- Modell (gecacht nach Eingabe)
@st.cache_resource(max_entries=6, show_spinner=False)
def modell_gecacht(schluessel: str, _e: dict):
    """Geometrie nach Eingabe-Schluessel; _e enthaelt alle Eingaben dieses Schluessels (auch eingefrorene)."""
    m = pl.modell_bauen(_e["docs"], _e["vorgabe"], _e["methode"], _e["puffer"], _e["raster"], _e["basis"],
                        tuple(_e["ursprung"]))
    return m, pl.bericht(m)


@st.cache_data(max_entries=6, show_spinner=False)
def viewer_ifc(schluessel: str, _m, _docs) -> bytes:
    return pl.ifc_bytes(_m, _docs)


@st.cache_data(max_entries=8, show_spinner=False)
def unterlage_gerendert(sha: str, seite: int, _pdf: bytes) -> dict:
    return pl.unterlage_rendern(_pdf, seite)


# ================================================================ Seite
st.markdown(CSS, unsafe_allow_html=True)
st.markdown('<div class="kopf"><h1>Baugrundmodell aus dem Bodengutachten</h1>'
            '<p>PDF hochladen · Tabellen prüfen · Bohrungen auf Lageplan oder Längsschnitt setzen · '
            'Baugrundmodell erzeugen (IFC 4.3) · jede Änderung rechnet nach · Prüfstand einchecken.</p></div>',
            unsafe_allow_html=True)

with st.sidebar:
    st.subheader("1 · Gutachten")
    dateien = st.file_uploader("Bohrprofile / Anlagen (PDF, mehrere möglich)", type="pdf", accept_multiple_files=True)
    beispiel = st.selectbox("… oder ein Beispiel", ["–"] + list(BEISPIELE), disabled=bool(dateien))
    st.subheader("2 · Optionen")
    ocr_da = pl.ocr_verfuegbar()
    ocr = st.toggle("OCR für Scans und SHX-Text", value=ocr_da, disabled=not ocr_da,
                    help="Liest Raster-PDFs ohne Textlage." if ocr_da else
                    "Nicht installiert: pip install -r requirements-ocr.txt")
    methode = st.radio("Interpolation", ["idw", "tps"], horizontal=True,
                       format_func={"idw": "IDW", "tps": "Dünnplatten-Spline"}.get)
    ueberhoehung = st.select_slider("Überhöhung im Viewer", [1, 2, 5, 10, 20], value=5)
    gok_relativ = st.checkbox("Fehlende GOK: Gelände = 0 m (relativ)", value=True,
                              help="Nur wenn keine Bohrung eine GOK hat; wird markiert.")
    with st.expander("Modellgrenze und Raster"):
        st.caption("Das Modell reicht über die konvexe Hülle der Bohrungen hinaus um den Puffer. Automatisch: "
                   "halber Bohrabstand (5–100 m); für Trassen über 5 km bleibt die Knotenzahl begrenzt.")
        puffer_auto = st.checkbox("Puffer automatisch", value=True)
        puffer = st.number_input("Puffer um die Bohrungen [m]", 1.0, 5000.0, 100.0, 10.0, disabled=puffer_auto)
        raster_auto = st.checkbox("Raster automatisch", value=True)
        raster = st.number_input("Rasterweite [m]", 0.5, 500.0, 5.0, 0.5, disabled=raster_auto)
        basis_auto = st.checkbox("Modellbasis = tiefste Endteufe", value=True)
        basis = st.number_input("Modellbasis [m NHN]", -2000.0, 5000.0, 0.0, 1.0, disabled=basis_auto)
    einstellungen = pj.Einstellungen(methode, None if puffer_auto else float(puffer), None if raster_auto else float(raster),
                                     None if basis_auto else float(basis), gok_relativ)

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
      <div class="schritt"><div class="nr">2</div><b>Tabellen prüfen</b>
        <span>Bohrungen und Schichten korrigieren und als geprüft markieren – noch vor dem Modell.</span></div>
      <div class="schritt"><div class="nr">3</div><b>Lage setzen</b>
        <span>Lageplan oder Längsschnitt (PDF) im Viewer unterlegen, Bohrungen an ihren Platz ziehen.</span></div>
      <div class="schritt"><div class="nr">4</div><b>Modell erzeugen</b>
        <span>Schichtflächen und geschlossene Körper; jede Änderung rechnet automatisch nach.</span></div>
      <div class="schritt"><div class="nr">5</div><b>Einchecken & Export</b>
        <span>Prüfstand festhalten; IFC 4.3, JSON und Prüfbericht herunterladen.</span></div>
    </div>""", unsafe_allow_html=True)
    st.info("⬅️ PDF in der Seitenleiste hochladen oder ein Beispiel wählen.")
    st.stop()

# ---------------------------------------------------------------- Seitengeruest
# Feste Reihenfolge der Bereiche: der Viewer-iframe bleibt an derselben Stelle und wird bei Reruns nicht neu
# eingehaengt (sonst verliert er Kamera und laedt neu, z. B. wenn "Erzeugen" Elemente davor ersetzt).
oben, bereich_daten, bereich_modell, bereich_viewer, bereich_ergebnisse = (st.container() for _ in range(5))

# ---------------------------------------------------------------- Extraktion
with oben:
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
p = projekt_fuer(docs, signatur)
codes = {bid: b["code"] for bid, _, b in pj.bohrungen(docs)}
ereignis = st.session_state.get("viewer")
if pj.ereignis_anwenden(p, ereignis):
    st.toast(ereignis_text(ereignis, codes), icon="📍")

with st.sidebar:
    st.subheader("3 · Projekt")
    st.caption(f"Projekt {signatur} · Stand wird automatisch gesichert.")
    if st.button("Korrekturen verwerfen", help="Alle Korrekturen, Lagen, Prüfhaken und Eincheckungen dieses "
                                                "Projekts löschen und neu beginnen."):
        projekt_ablage(signatur).unlink(missing_ok=True)
        st.session_state["projekte"].pop(signatur, None)
        st.session_state.pop(f"_gesichert_{signatur}", None)
        st.rerun()

with oben:
    alle = [b for _, _, b in pj.bohrungen(pj.wirksame_docs(docs, p))]
    schichten = [ly for b in alle for ly in b.get("layers") or []]
    k = st.columns(5)
    k[0].metric("Bohrungen erkannt", len(alle), border=True)
    k[1].metric("Schichten", len(schichten), border=True)
    k[2].metric("mit Koordinaten", sum(1 for b in alle if b.get("x") is not None), border=True)
    k[3].metric("mit GOK", sum(1 for b in alle if b.get("gok_nhn") is not None), border=True)
    k[4].metric("mit Grundwasser", sum(1 for b in alle if b.get("groundwater")), border=True)
    if not alle:
        st.warning("In den Dokumenten wurde keine Bohrung erkannt. Ist eine Seite mit Bohrprofilen dabei? "
                   "Bei Scans OCR einschalten.")
        st.stop()

# ---------------------------------------------------------------- Pruefstand und Einchecken
bereich_pruefstand = oben.container(border=True)

# ---------------------------------------------------------------- Tabellen (vor dem Modell)
tab_bohr, tab_schicht, tab_lage = bereich_daten.tabs(["📍 Bohrungen", "🪨 Schichten", "🗺️ Lage & Unterlage"])

with tab_bohr:
    st.caption("Grau = aus dem PDF. **Modell, Geprüft, GOK, Rechtswert, Hochwert, EPSG** sind änderbar; "
               "Eingetragenes wird im Modell als *manuell* markiert. Lage auch im Viewer setzbar (*Lage bearbeiten*).")
    tabelle = pd.DataFrame(pj.bohrungen_zeilen(docs, p))
    bearbeitet = st.data_editor(
        tabelle, key=f"bohr_{signatur}_{p.version}", hide_index=True, width="stretch",
        disabled=[c for c in tabelle.columns if c not in ("Modell", "Geprüft", "GOK [m NHN]", "Rechtswert", "Hochwert", "EPSG")],
        column_order=["Modell", "Geprüft", "Bohrung", "Dokument", "Seite", "GOK [m NHN]", "Endteufe [m]", "Rechtswert",
                      "Hochwert", "EPSG", "Lage aus", "Schichten geprüft", "Konfidenz", "min. Konfidenz", "Grundwasser",
                      "Hinweise"],
        column_config={
            "Modell": st.column_config.CheckboxColumn("Modell", help="Bohrung ins Baugrundmodell aufnehmen"),
            "Geprüft": st.column_config.CheckboxColumn("Geprüft", help="Ganze Bohrung geprüft (alle Schichten)"),
            "GOK [m NHN]": st.column_config.NumberColumn(format="%.2f"),
            "Endteufe [m]": st.column_config.NumberColumn(format="%.2f"),
            "Rechtswert": st.column_config.NumberColumn(format="%.2f"),
            "Hochwert": st.column_config.NumberColumn(format="%.2f"),
            "EPSG": st.column_config.NumberColumn(format="%d", min_value=1000, max_value=99999),
            "Konfidenz": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="%.2f"),
            "min. Konfidenz": st.column_config.ProgressColumn(min_value=0.0, max_value=1.0, format="%.2f"),
            "Hinweise": st.column_config.TextColumn(width="large"),
        })
    pj.bohrungen_uebernehmen(docs, p, bearbeitet.to_dict("records"))

with tab_schicht:
    zeilen_b = pj.bohrungen_zeilen(docs, p)
    mit_schichten = [z for z in zeilen_b if z["Schichten geprüft"] != "0/0"]

    def bohrung_text(bid: str) -> str:
        z = next(z for z in zeilen_b if z["id"] == bid)
        gep, ges = (int(t) for t in z["Schichten geprüft"].split("/"))
        zeichen = "✅" if gep == ges else ("⚠️" if (z["min. Konfidenz"] or 1) < pj.UNSICHER else "◻️")
        return f"{zeichen} {z['Bohrung']} – {gep}/{ges} geprüft · {z['Dokument']}"

    if not mit_schichten:
        st.info("Keine Schichten erkannt.")
    else:
        ids = [z["id"] for z in mit_schichten]
        offen = [z["id"] for z in mit_schichten if z["Schichten geprüft"].split("/")[0] != z["Schichten geprüft"].split("/")[1]]
        c1, c2 = st.columns([4, 1])
        wahl = c1.selectbox("Bohrung", ids, format_func=bohrung_text, key=f"schicht_wahl_{signatur}")
        if c2.button("Nächste ungeprüfte →", disabled=not offen, width="stretch"):
            rest = [i for i in offen if ids.index(i) > ids.index(wahl)] or offen
            st.session_state[f"schicht_wahl_{signatur}"] = rest[0]
            st.rerun()
        df = pd.DataFrame(pj.schichten_zeilen(docs, p, wahl))
        neu_s = st.data_editor(
            df, key=f"sch_{signatur}_{wahl}_{p.version}", hide_index=True, width="stretch",
            disabled=[c for c in df.columns if c not in ("von", "bis", "Bodenart", "Geprüft")],
            column_order=["Geprüft", "von", "bis", "Bodenart", "Konfidenz", "Korrigiert", "Beschreibung", "Hinweise", "Quelle"],
            column_config={
                "von": st.column_config.NumberColumn("von [m]", format="%.2f", min_value=0.0),
                "bis": st.column_config.NumberColumn("bis [m]", format="%.2f", min_value=0.0),
                "Bodenart": st.column_config.SelectboxColumn(options=pj.bodenarten(docs), required=True),
                "Geprüft": st.column_config.CheckboxColumn(help="Schicht geprüft; eine Korrektur gilt als geprüft"),
                "Konfidenz": st.column_config.ProgressColumn("Konfidenz (Extraktion)", min_value=0.0, max_value=1.0,
                                                             format="%.2f"),
                "Beschreibung": st.column_config.TextColumn(width="large"),
            })
        if pj.schichten_uebernehmen(docs, p, wahl, neu_s.to_dict("records")):
            st.rerun()                                    # Spalte "Korrigiert" und Pruefstand neu
        c1, c2, _ = st.columns([2, 2, 3])
        if c1.button("✅ Alle Schichten dieser Bohrung geprüft", width="stretch"):
            pj.alle_schichten_pruefen(docs, p, wahl, True)
            p.version += 1
            st.rerun()
        if c2.button("Prüfung zurücknehmen", width="stretch"):
            pj.alle_schichten_pruefen(docs, p, wahl, False)
            p.bohrung.setdefault(wahl, {})["geprueft"] = False
            p.version += 1
            st.rerun()
        # Uebersicht aller Profile mit den wirksamen (korrigierten) Werten
        profil = []
        for bid, d, b in pj.bohrungen(pj.wirksame_docs(docs, p)):
            gok = b.get("gok_nhn")
            for ly in b.get("layers") or []:
                profil.append({"Bohrung": b["code"], "von": ly["top_depth"], "bis": ly["bottom_depth"],
                               "von NHN": None if gok is None else gok - ly["top_depth"],
                               "bis NHN": None if gok is None else gok - ly["bottom_depth"],
                               "Bodenart": ly.get("soil_class") or "unklassifiziert",
                               "Geprüft": "ja" if ly.get("geprueft") else "nein", "Konfidenz": ly.get("confidence")})
        dfp = pd.DataFrame(profil)
        nhn = dfp["von NHN"].notna().all()
        hoehe = st.radio("Höhenbezug", ["m NHN", "Tiefe unter GOK"] if nhn else ["Tiefe unter GOK"], horizontal=True)
        oben, unten = ("von NHN", "bis NHN") if hoehe == "m NHN" else ("von", "bis")
        arten = sorted(dfp["Bodenart"].unique())
        balken = alt.Chart(dfp).mark_bar(size=26, stroke="#1d2330", strokeWidth=0.4).encode(
            x=alt.X("Bohrung:N", sort=None, title=None),
            y=alt.Y(f"{oben}:Q", title=hoehe, scale=alt.Scale(zero=False, reverse=hoehe != "m NHN")), y2=f"{unten}:Q",
            color=alt.Color("Bodenart:N", scale=alt.Scale(domain=arten, range=[pj.bodenart_farbe(a) for a in arten])),
            opacity=alt.condition(alt.datum.Geprüft == "ja", alt.value(1.0), alt.value(0.55)),
            tooltip=["Bohrung", "von", "bis", "Bodenart", "Konfidenz", "Geprüft"])
        st.altair_chart(balken.properties(height=330), width="stretch")
        st.caption("Blasse Balken: noch nicht geprüft.")

with tab_lage:
    modus = st.radio("Lage der Bohrungen", [pj.LAGE_KOORDINATEN, pj.LAGE_REIHE], format_func=LAGE_TEXT.get,
                     index=[pj.LAGE_KOORDINATEN, pj.LAGE_REIHE].index(p.lage_modus), horizontal=True,
                     key=f"modus_{signatur}_{p.version}",
                     help="Koordinaten: Rechts-/Hochwert je Bohrung (PDF, Tabelle oder im Viewer auf dem Lageplan). "
                          "Reihe: Bohrungen nebeneinander mit Abständen bzw. Stationen (Längsschnitt).")
    if modus != p.lage_modus:
        p.lage_modus = modus
    if p.lage_modus == pj.LAGE_REIHE:
        c1, c2 = st.columns([1, 3])
        standard = c1.number_input("Standardabstand [m]", 1.0, 5000.0, float(p.reihe["standard"]), 1.0,
                                   key=f"standard_{signatur}_{p.version}")
        if standard != p.reihe["standard"]:
            p.reihe["standard"] = float(standard)
        c2.caption("Eigene Abstände je Bohrung eintragen (z. B. BK1 → BK2 10 m, BK2 → BK3 15 m) oder eine Station "
                   "setzen; Reihenfolge über **Nr**. Ohne Eintrag gilt der Standardabstand. Im Viewer: Bohrungen "
                   "im Längsschnitt an ihre Säule ziehen (Umschalt: Ansatzhöhe).")
        reihe_ids = [z["id"] for z in pj.bohrungen_zeilen(docs, p) if z["Modell"]]
        df_r = pd.DataFrame(pj.reihe_zeilen(docs, p, reihe_ids))
        neu_r = st.data_editor(
            df_r, key=f"reihe_{signatur}_{p.version}", hide_index=True, width="stretch",
            disabled=["id", "Bohrung", "Quelle"], column_order=["Nr", "Bohrung", "Abstand zum Vorgänger [m]", "Station [m]", "Quelle"],
            column_config={"Nr": st.column_config.NumberColumn(format="%d", min_value=1, step=1),
                           "Abstand zum Vorgänger [m]": st.column_config.NumberColumn(format="%.2f", min_value=0.0),
                           "Station [m]": st.column_config.NumberColumn(format="%.2f")})
        if pj.reihe_uebernehmen(docs, p, reihe_ids, neu_r.to_dict("records")):
            p.version += 1
            st.rerun()

    st.markdown('<div class="abschnitt">Unterlage (PDF)</div>', unsafe_allow_html=True)
    st.caption("Lageplan (von oben) oder Längsschnitt (von der Seite) als PDF: er liegt im Viewer unter den Bohrungen. "
               "Mit zwei Passpunkten kalibrieren, dann die Bohrungen an ihren Platz ziehen.")
    c1, c2, c3 = st.columns([3, 2, 1])
    plan = c1.file_uploader("Plan-PDF", type="pdf", key=f"unterlage_{signatur}_{p.unterlage_zaehler}")
    art = c2.radio("Ansicht", ["plan", "schnitt"], format_func=ART_TEXT.get, horizontal=True,
                   index=0 if (p.unterlage or {}).get("art", "plan" if p.lage_modus == pj.LAGE_KOORDINATEN else "schnitt") == "plan" else 1,
                   key=f"art_{signatur}_{p.unterlage_zaehler}")
    seite = int(c3.number_input("Seite", 1, 999, int((p.unterlage or {}).get("seite", 0)) + 1, 1,
                                key=f"seite_{signatur}_{p.unterlage_zaehler}")) - 1
    if plan is not None:
        pdf = plan.getvalue()
        sha = hashlib.sha256(pdf).hexdigest()[:16]
        alt_u = p.unterlage or {}
        if (alt_u.get("sha"), alt_u.get("seite"), alt_u.get("art")) != (sha, seite, art):
            bild = unterlage_gerendert(sha, seite, pdf)
            datei = pl.ARBEIT / "unterlagen" / f"{sha}_{min(seite, bild['seiten'] - 1)}.png"
            datei.parent.mkdir(parents=True, exist_ok=True)
            datei.write_bytes(bild["png"])
            p.unterlage = {"sha": sha, "seite": min(seite, bild["seiten"] - 1), "seiten": bild["seiten"], "art": art,
                           "name": plan.name, "datei": str(datei), "breite": bild["breite"], "hoehe": bild["hoehe"],
                           "mm_pro_px": bild["mm_pro_px"],
                           "kalibrierung": alt_u.get("kalibrierung") if (alt_u.get("sha"), alt_u.get("seite"), alt_u.get("art")) == (sha, seite, art) else None}
            gewuenscht = pj.LAGE_KOORDINATEN if art == "plan" else pj.LAGE_REIHE
            if p.lage_modus != gewuenscht:
                p.lage_modus = gewuenscht
                st.toast(f"Lage auf „{LAGE_TEXT[gewuenscht]}“ gestellt (passend zur Unterlage).", icon="🗺️")
            p.version += 1
    if p.unterlage:
        u = p.unterlage
        kal = u.get("kalibrierung")
        chips([(f"{u['name']} · S. {u['seite'] + 1}/{u.get('seiten', 1)}", ""), (ART_TEXT[u["art"]], ""),
               ("kalibriert (2 Passpunkte)" if kal else "nicht kalibriert – im Viewer zwei Passpunkte setzen",
                "ok" if kal else "warn"), (f"EPSG {kal['epsg']}" if kal and kal.get("epsg") else "", "")])
        c1, c2, c3 = st.columns(3)
        if c1.button("🗺️ Im Viewer bearbeiten", type="primary", width="stretch"):
            st.session_state["bearbeiten"] = st.session_state.get("bearbeiten", 0) + 1
        if c2.button("Kalibrierung zurücksetzen", disabled=not kal, width="stretch"):
            u["kalibrierung"] = None
            p.version += 1
        if c3.button("Unterlage entfernen", width="stretch"):
            p.unterlage = None
            p.unterlage_zaehler += 1
            p.version += 1
            st.rerun()
    elif st.button("🗺️ Bohrungen im Viewer setzen (ohne Unterlage)"):
        st.session_state["bearbeiten"] = st.session_state.get("bearbeiten", 0) + 1

# ---------------------------------------------------------------- Modell
vorb = pj.modell_eingabe(docs, p, einstellungen)
ursprung = pj.ursprung(p, vorb)
epsgs = Counter(b.get("crs_epsg") for d in vorb.docs for b in d["boreholes"] if b.get("crs_epsg"))
epsg = epsgs.most_common(1)[0][0] if epsgs else None

with bereich_modell:
    st.markdown('<div class="abschnitt">Baugrundmodell</div>', unsafe_allow_html=True)
    modell = bericht = None
    ifc_viewer: bytes | None = None
    fingerabdruck: str | None = None                # Schluessel der Modell-Eingaben (fuer das Einchecken)
    modellfehler = ""
    if not p.erzeugt:
        bereit = len(vorb.lage)
        c1, c2 = st.columns([2, 5])
        if c1.button("🧱 Baugrundmodell erzeugen", type="primary", width="stretch", disabled=not bereit):
            p.erzeugt = True
        c2.caption(f"{bereit} Bohrungen mit Lage bereit. Erst Tabellen prüfen und die Lage setzen – der Viewer zeigt die "
                   "Bohrungen schon jetzt; nach dem Erzeugen rechnet jede Änderung das Modell automatisch nach.")
        for h in vorb.hinweise:
            st.caption(f"• {h}")
    if p.erzeugt:
        c1, c2, c3 = st.columns([2, 2, 4])
        p.auto = c1.toggle("Automatisch nachführen", value=p.auto, help="Jede Änderung (Tabelle, Viewer, Einstellungen) "
                                                                        "rechnet das Modell sofort neu.")
        # Pruef-Haken gehoeren nicht zur Geometrie: Haken setzen rechnet nicht neu (sie stehen im Export-IFC)
        eingabe = {"docs": pl.ohne_pruefvermerke(vorb.docs), "vorgabe": p.vorgabe, "methode": einstellungen.methode,
                   "puffer": einstellungen.puffer, "raster": einstellungen.raster, "basis": einstellungen.basis,
                   "ursprung": list(ursprung)}
        schluessel = hashlib.sha256(json.dumps(eingabe, sort_keys=True).encode()).hexdigest()[:16]
        stand = st.session_state.setdefault("modellstand", {})
        eingaben: dict = st.session_state.setdefault("modelleingaben", {})
        eingaben[schluessel] = eingabe
        if p.auto or signatur not in stand or c2.button("Jetzt neu rechnen", type="primary", disabled=stand.get(signatur) == schluessel):
            stand[signatur] = schluessel
        aktuell = stand[signatur]
        for alt_k in [k for k in eingaben if k not in (aktuell, schluessel)][:-8]:    # nur die letzten Eingaben behalten
            eingaben.pop(alt_k)
        if aktuell != schluessel:
            c3.warning("Änderungen seit dem letzten Rechnen – *Jetzt neu rechnen* oder automatisch nachführen.", icon="⏸️")
        try:
            with st.spinner("Baugrundmodell wird gerechnet …"):
                e_aktuell = eingaben.get(aktuell, eingabe)
                modell, bericht = modell_gecacht(aktuell, e_aktuell)
                ifc_viewer = viewer_ifc(aktuell, modell, e_aktuell["docs"])
                fingerabdruck = aktuell
        except ValueError as err:
            modellfehler = str(err)
        if modell is None:
            st.warning(f"**Noch kein Baugrundmodell:** {modellfehler}. Jede Bohrung braucht eine Lage und eine GOK – "
                       "in *Bohrungen* eintragen, im Viewer setzen oder unter *Lage* „Reihe“ wählen.")
        else:
            pr = bericht["pruefungen"]
            lagen = {x["lage"] for x in bericht["bohrungen"]}
            chips([(f"{len(bericht['einheiten'])} Einheiten", ""), (f"{len(bericht['bohrungen'])} Bohrungen im Modell", ""),
                   (f"Lage: EPSG:{bericht['epsg']}" if bericht["epsg"] else
                    "Lage: schematisch" if "schematisch" in lagen else "Lage: Reihe" if any(l.startswith("Reihe") for l in lagen)
                    else "Lage: lokales System", "" if bericht["epsg"] else "warn"),
                   (f"Fläche {bericht['parameter']['flaeche_m2'] / 1e6:.2f} km²" if bericht["parameter"]["flaeche_m2"] > 1e5
                    else f"Fläche {bericht['parameter']['flaeche_m2']:,.0f} m²", ""),
                   (f"Puffer {bericht['parameter']['puffer_m']:.0f} m · Raster {bericht['parameter']['raster_m']:.1f} m", ""),
                   (f"Abweichung an Bohrungen {pr['max_abweichung_an_bohrungen_m']:.2f} m",
                    "ok" if pr["max_abweichung_an_bohrungen_m"] < 0.01 else "warn"),
                   ("Körper geschlossen" if pr["alle_koerper_geschlossen"] else "Körper offen",
                    "ok" if pr["alle_koerper_geschlossen"] else "warn"),
                   (f"{len(bericht['ausgeschlossen']) + len(vorb.nicht_im_modell)} nicht im Modell",
                    "warn" if bericht["ausgeschlossen"] or vorb.nicht_im_modell else "")])
            for h in dict.fromkeys(vorb.hinweise + bericht["hinweise"]):
                st.warning(h, icon="⚠️")

# ---------------------------------------------------------------- Viewer
with bereich_viewer:
    if viewer.verfuegbar():
        titel = Path(docs[0]["document"]["file"]).stem if len(docs) == 1 else f"{len(docs)} Dokumente"
        unterlage_args = None
        if p.unterlage and Path(p.unterlage["datei"]).exists():
            u = p.unterlage
            unterlage_args = {"url": viewer.ablegen(Path(u["datei"]).read_bytes(), "png"), "name": u["name"], "art": u["art"],
                              "breite": u["breite"], "hoehe": u["hoehe"], "mm_pro_px": u["mm_pro_px"],
                              "kalibrierung": u.get("kalibrierung")}
        viewer.zeigen(ifc_viewer, titel=titel, ueberhoehung=ueberhoehung, hoehe=780, key="viewer", projekt=signatur,
                      ursprung=list(ursprung), epsg=epsg, modus=p.lage_modus,
                      bohrungen=pj.viewer_bohrungen(docs, p, vorb, bericht), unterlage=unterlage_args, nr=p.viewer_nr,
                      bearbeiten=st.session_state.get("bearbeiten", 0))
        st.caption("Viewer: links ziehen = drehen, rechts = verschieben, Rad = zoomen (zur Maus) · Würfel und *Oben/Süd* für "
                   "Ansichten · **Lage bearbeiten**: Bohrungen auf Plan/Schnitt ziehen · Klick auf eine Bohrung: Details "
                   "und *Als geprüft markieren*.")
    else:
        st.error("Viewer nicht gebaut: `cd apps/web && npm install && npm run build`.")

# ---------------------------------------------------------------- Pruefstand (oben, nach allen Aenderungen dieses Laufs)
with bereich_pruefstand:
    stand_p = pj.pruefstand(docs, p)
    (bg, bn), (sg, sn) = stand_p["bohrungen"], stand_p["schichten"]
    c1, c2, c3 = st.columns([3, 3, 2])
    c1.progress(bg / bn if bn else 0.0, text=f"Bohrungen geprüft: **{bg}/{bn}**")
    c2.progress(sg / sn if sn else 0.0, text=f"Schichten geprüft: **{sg}/{sn}**")
    letzter = p.eincheckungen[-1] if p.eincheckungen else None
    with c3.popover("✅ Stand einchecken", width="stretch"):
        st.markdown("Hält den Prüfstand fest (Zeit, Zähler, Fingerabdruck des Modells). Das IFC trägt ihn unter "
                    "*CPset_Baugrundmodell.Pruefstand*.")
        kommentar = st.text_input("Kommentar", placeholder="z. B. Schichten BK1–BK5 mit Anlage 2 verglichen")
        if st.button("Einchecken", type="primary"):
            eintrag = pj.einchecken(docs, p, fingerabdruck, kommentar)
            st.toast(f"Eingecheckt: {pj.stand_text(eintrag)}", icon="✅")
            st.rerun()
    geaendert = pj.seit_einchecken_geaendert(docs, p, fingerabdruck)
    chips([(f"⚠ {stand_p['unsicher_ungeprueft']} unsichere Schichten ungeprüft" if stand_p["unsicher_ungeprueft"] else
            "keine unsicheren Schichten offen", "warn" if stand_p["unsicher_ungeprueft"] else "ok"),
           (f"✎ {stand_p['korrigiert']} Schichten korrigiert", "" if stand_p["korrigiert"] else ""),
           (f"📍 {stand_p['manuelle_lage']} Lagen manuell", ""),
           (f"Eingecheckt: {pj.stand_text(letzter)}" + (" · seitdem geändert" if geaendert else "") if letzter else
            "noch nicht eingecheckt", "warn" if (geaendert or not letzter) else "ok")])

# ---------------------------------------------------------------- Ergebnisse
tab_einheit, tab_bericht, tab_protokoll, tab_export = bereich_ergebnisse.tabs(
    ["🧱 Modelleinheiten", "🧾 Prüfbericht", "✅ Prüfprotokoll", "📦 Export"])

with tab_einheit:
    if bericht is None:
        st.info("Erst wenn ein Modell erzeugt ist.")
    else:
        einheiten = pd.DataFrame([{
            "Farbe": e["farbe"], "Einheit": e["name"], "Bodenarten": ", ".join(e["bodenarten"]),
            "Volumen [m³]": e["volumen_m3"], "max. Mächtigkeit [m]": e["maechtigkeit_max_m"],
            "vorhanden": len(e["bohrungen"]["vorhanden"]), "fehlt": len(e["bohrungen"]["fehlt"]),
            "unbekannt": len(e["bohrungen"]["unbekannt"]), "Hinweise": "; ".join(e["hinweise"])}
            for e in bericht["einheiten"]])
        stil = einheiten.style.format({"Volumen [m³]": "{:,.0f}", "max. Mächtigkeit [m]": "{:.2f}"})
        faerben = getattr(stil, "map", None) or stil.applymap          # pandas < 2.1: applymap
        st.dataframe(faerben(lambda f: f"background-color: {f}; color: {f}", subset=["Farbe"]),
                     hide_index=True, width="stretch")
        st.markdown("**Einheiten festlegen** – umbenennen, Bodenarten zusammenlegen (`Sand, Kies`), Reihenfolge "
                    "von oben nach unten. Ohne Festlegung korreliert das Programm selbst.")
        vorlage = pd.DataFrame([{"Einheit": v["name"], "Bodenarten": ", ".join(v["bodenarten"])}
                                for v in (p.vorgabe or bericht["vorlage_einheiten"])])
        neu_v = st.data_editor(vorlage, key=f"vorgabe_{signatur}_{p.version}", num_rows="dynamic", hide_index=True,
                               width="stretch")
        c1, c2 = st.columns(2)
        if c1.button("Mit diesen Einheiten rechnen", type="primary"):
            p.vorgabe = [{"name": str(z["Einheit"]).strip(),
                          "bodenarten": [t.strip() for t in str(z["Bodenarten"]).split(",") if t.strip()]}
                         for z in neu_v.to_dict("records") if str(z.get("Einheit") or "").strip()]
            st.rerun()
        if c2.button("Automatisch korrelieren", disabled=p.vorgabe is None):
            p.vorgabe = None
            st.rerun()

with tab_bericht:
    if bericht is None:
        st.info("Erst wenn ein Modell erzeugt ist.")
    else:
        raus = vorb.nicht_im_modell + bericht["ausgeschlossen"]
        if raus:
            st.markdown("**Nicht im Modell**")
            st.dataframe(pd.DataFrame(raus).rename(columns={"code": "Bohrung", "dokument": "Dokument", "grund": "Grund"}),
                         hide_index=True, width="stretch")
        st.markdown("**Einheiten je Bohrung** (✓ vorhanden · – fehlt · ? unter der Endteufe)")
        zeichen = {"vorhanden": "✓", "fehlt": "–", "unbekannt": "?"}
        matrix = pd.DataFrame([{"Bohrung": x["code"], "Lage": x["lage"], "Höhe": x["hoehe"],
                                **{e["einheit"]: zeichen[e["status"]] for e in x["einheiten"]}} for x in bericht["bohrungen"]])
        st.dataframe(matrix, hide_index=True, width="stretch")
        hinweise = [f"{x['code']}: {h}" for x in bericht["bohrungen"] for h in x["hinweise"]] + bericht["hinweise"]
        if hinweise:
            st.markdown("**Hinweise**")
            for h in hinweise:
                st.caption(f"• {h}")
        st.markdown("**Parameter**")
        st.json(bericht["parameter"], expanded=False)

with tab_protokoll:
    st.caption("Jedes Einchecken hält den Prüfstand fest: wie viele Bohrungen und Schichten geprüft, wie viele unsicher "
               "offen, korrigiert und manuell gesetzt – und den Fingerabdruck des Modells. Ändert sich danach etwas, "
               "steht oben *seitdem geändert*.")
    if p.eincheckungen:
        st.dataframe(pd.DataFrame([{"Nr": e["nr"], "Zeit": e["zeit"],
                                    "Bohrungen geprüft": "{}/{}".format(*e["stand"]["bohrungen"]),
                                    "Schichten geprüft": "{}/{}".format(*e["stand"]["schichten"]),
                                    "unsicher offen": e["stand"]["unsicher_ungeprueft"],
                                    "korrigiert": e["stand"]["korrigiert"], "Lage manuell": e["stand"]["manuelle_lage"],
                                    "Modell": e["modell"] or "–", "Kommentar": e["kommentar"]}
                                   for e in reversed(p.eincheckungen)]), hide_index=True, width="stretch")
    else:
        st.info("Noch nicht eingecheckt – oben *Stand einchecken*.")
    korrekturen = [{"Bohrung": codes.get(k.split("/")[0], k), "Schicht": int(k.split("/")[1]) + 1,
                    **{s: v for s, v in o.items()}} for k, o in sorted(p.schicht.items())
                   if any(s in o for s in ("oben", "unten", "bodenart"))]
    if korrekturen:
        st.markdown("**Korrigierte Schichten**")
        st.dataframe(pd.DataFrame(korrekturen), hide_index=True, width="stretch")

with tab_export:
    stamm = Path(docs[0]["document"]["file"]).stem if len(docs) == 1 else "baugrundmodell"
    c1, c2 = st.columns(2)
    with c1:
        st.markdown("**Modell**")
        if modell is not None:
            letzter = p.eincheckungen[-1] if p.eincheckungen else None
            pruef = pj.stand_text(letzter) if letzter else "nicht eingecheckt"
            modell_jetzt, docs_jetzt = modell, vorb.docs
            st.download_button("⬇️ Baugrundmodell (IFC 4.3, mit Prüfstand)",
                               lambda: pl.ifc_bytes(modell_jetzt, docs_jetzt, pruefstand=pruef), f"{stamm}.ifc",
                               "application/x-step", type="primary", width="stretch",
                               help="Enthält je Bohrung und Schicht Geprueft/Korrigiert und den letzten Check-in.")
            st.download_button("⬇️ Prüfbericht (JSON)", pl.json_bytes(bericht), f"{stamm}_bericht.json",
                               "application/json", width="stretch")
            st.download_button("⬇️ Einheiten-Vorlage (JSON, für --einheiten)",
                               pl.json_bytes(bericht["vorlage_einheiten"]), f"{stamm}_einheiten.json",
                               "application/json", width="stretch")
        else:
            st.caption("Noch kein Modell.")
    with c2:
        st.markdown("**Daten**")
        st.download_button("⬇️ Extraktion (kanonisches JSON)", pl.json_bytes(docs if len(docs) > 1 else docs[0]),
                           f"{stamm}_extraktion.json", "application/json", width="stretch")
        st.download_button("⬇️ Modell-Eingabe mit Korrekturen (JSON)", pl.json_bytes(vorb.docs),
                           f"{stamm}_modell_eingabe.json", "application/json", width="stretch")
        st.download_button("⬇️ Projektstand (JSON: Korrekturen, Lage, Prüfung)", pl.json_bytes(pj.speichern(p)),
                           f"{stamm}_projekt.json", "application/json", width="stretch")
    st.caption("IFC öffnen: hier im Viewer, in apps/web (`npm run dev`) oder in jedem IFC-4.3-Programm. "
               "Kommandozeile: `python -m baugrundmodell modell.ifc extraktion.json` (services/modeler).")

sichern(p)
