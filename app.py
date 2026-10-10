"""Geo_Agent - Lokales Web-Tool: Baugrund-PDFs -> Excel nach Geo_Template.

Start (lokal, nur localhost):
    streamlit run app.py
"""
from __future__ import annotations

import io

import fitz
import streamlit as st

from geo_agent.legend import parse_legend, DIN_LABELS, Legend
from geo_agent.bohrprofil import parse_bohrprofil
from geo_agent.laengsschnitt import parse_laengsschnitt, DEFAULT_COLOR_MAP
from geo_agent import excel_writer

st.set_page_config(page_title="Geo_Agent – Baugrund → Excel", layout="wide")


# ---------------------------------------------------------------------------
# Gecachte Parser (Schluessel = Datei-Bytes -> einmal pro Upload)
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _parse_bohrprofil(data: bytes):
    doc = fitz.open(stream=data, filetype="pdf")
    leg = parse_legend(doc)
    bhs = parse_bohrprofil(doc, leg)
    # picklebare Rueckgabe
    return leg, bhs


@st.cache_data(show_spinner=False)
def _parse_laengsschnitt(data: bytes, valid_ids: tuple):
    doc = fitz.open(stream=data, filetype="pdf")
    return parse_laengsschnitt(doc, make_preview=True, valid_bohr_ids=list(valid_ids))


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------
st.title("🛠️ Geo_Agent — Baugrunddaten aus PDF → Excel")
st.caption("Lokales Tool. Bohrprofil (DIN 4023) + geologischer Längsschnitt → "
           "`.xlsx` nach fester Vorlage (4 Blätter).")

with st.sidebar:
    st.header("1 · PDFs hochladen")
    f_bohr = st.file_uploader("Bohrprofil-PDF", type="pdf", key="bohr")
    f_laengs = st.file_uploader("Längsschnitt-PDF", type="pdf", key="laengs")

if not (f_bohr and f_laengs):
    st.info("⬅️ Bitte **beide** PDFs in der Seitenleiste hochladen "
            "(Bohrprofil **und** Längsschnitt).")
    st.stop()

bohr_bytes = f_bohr.getvalue()
laengs_bytes = f_laengs.getvalue()

# --- Bohrprofil parsen ---
with st.spinner("Bohrprofil wird ausgewertet…"):
    legend, boreholes = _parse_bohrprofil(bohr_bytes)

if not boreholes:
    st.error("Keine Kernbohrungen erkannt – ist das wirklich das Bohrprofil-PDF?")
    st.stop()

# --- Längsschnitt parsen (langsamer, gecacht) ---
with st.spinner("Längsschnitt wird ausgewertet (Tunnel & Geologie)…"):
    laengs = _parse_laengsschnitt(laengs_bytes, tuple(b.bohr_id for b in boreholes))

# Bodenart auf Tunnel + Anteile aus den Bohrprofil-Schichten ableiten
abschnitte = excel_writer.enrich_abschnitte(boreholes, laengs.abschnitte)

# ===========================================================================
# 2 · Legende & dynamische Spalten
# ===========================================================================
st.header("2 · Spalten-Auswahl")
c1, c2 = st.columns([1, 1])

with c1:
    st.subheader("Feste Spalten (immer dabei)")
    st.markdown(
        "- **Blatt 1 — Geomodul:** Bohr_ID, NHN, Tiefe, Rechtswert, Hochwert\n"
        "- **Blatt 2 — Geomodul_Bodenschicht:** ID, Bodenart, Tiefe(oberkante)\n"
        "- **Blatt 3 — Geo_Tunnel:** Bohr_BID, NHN, OK Tunnel bis GOK, OK Tunnel, "
        "Achse, Tunnelmeter, Bodenart auf Tunnel\n"
        "- **Blatt 4 — Geo_Spec:** bodenart, abschnitt_id, "
        "Prozent_Bodenart_pro_abschnitt, bohr_id, Tunnelmeter"
    )
    st.caption(f"Erkannte Bodenarten in der Legende: {', '.join(legend.bodenarten)}")

with c2:
    st.subheader("Dynamische DIN-Spalten (Blatt 4)")
    present = legend.present_din_keys()
    if not present:
        st.warning("Keine DIN-Sektionen in der Legende gefunden.")
    selected = []
    for key in present:
        if st.checkbox(DIN_LABELS[key], value=True, key=f"din_{key}"):
            selected.append(key)
    missing = [k for k in DIN_LABELS if k not in present]
    if missing:
        st.caption("Nicht in der Legende vorhanden (nicht wählbar): "
                   + ", ".join(DIN_LABELS[k] for k in missing))
    st.caption("ℹ️ CPT-/Sonden-Spalten werden bewusst weggelassen.")

# ===========================================================================
# 3 · Prüf-/Log-Ausgabe
# ===========================================================================
st.header("3 · Erkennung & Validierung")

m1, m2, m3, m4 = st.columns(4)
nhn_ok = sum(1 for b in boreholes if b.nhn_check_ok)
layers_total = sum(len(b.consolidated) for b in boreholes)
layers_unsure = sum(1 for b in boreholes for ly in b.consolidated if not ly.bodenart_sure)
m1.metric("Kernbohrungen", len(boreholes))
m2.metric("NHN-Arithmetik ok", f"{nhn_ok}/{len(boreholes)}")
m3.metric("Bodenschichten", layers_total, f"{layers_unsure} unsicher", delta_color="off")
m4.metric("Abschnitte (Bohrungs-Zonen)", len(abschnitte))

tab_val, tab_tun, tab_log = st.tabs(
    ["🧮 NHN-Validierung (Bohrungen)", "🚇 Tunnel-Vorschau (prüfbar)", "📋 Log"])

with tab_val:
    rows = [{
        "Bohr_ID": b.bohr_id, "Seite": b.page + 1, "GOK NHN": b.gok_nhn,
        "Tiefe": b.total_depth, "NHN Sohle": b.nhn_bottom,
        "Check": "✅" if b.nhn_check_ok else "❌", "Rechnung": b.nhn_check_msg,
    } for b in boreholes]
    st.dataframe(rows, use_container_width=True, hide_index=True)

with tab_tun:
    st.caption("Rot = OK Tunnel, Blau = Sohle (validierte Geometrie), senkrechte "
               "Linien = verortete Bohrungen. Die Bänder unten zeigen die rohe "
               "Längsschnitt-Geologie nur als Sichtprüfung — die **Bodenart auf "
               "Tunnel** in Tabelle/Excel stammt aus den Bohrprofil-Schichten "
               "(Blatt 2) an der Tunneltiefe.")
    if laengs.preview_png:
        st.image(laengs.preview_png, use_container_width=True)
    rows = [{
        "Abschnitt": ab.abschnitt_id, "Bohrung": ab.bohr_id, "Bohr-TM": ab.bohr_tm,
        "Zone von TM": ab.tm_start, "bis TM": ab.tm_end,
        "Bodenart (auf Tunnel)": ab.bodenart, "OK Tunnel": ab.ok_nhn,
        "Achse": ab.achse_nhn, "Sohle": ab.sohle_nhn,
        "Zusammensetzung (Bohrprofil)": ", ".join(f"{k} {v}%" for k, v in ab.composition.items()),
    } for ab in abschnitte]
    st.dataframe(rows, use_container_width=True, hide_index=True)
    with st.expander("Farb→Geologie-Zuordnung (aus Längsschnitt-Legende)"):
        st.table([{"RGB (PDF)": str(k), "Bodenart": v}
                  for k, v in laengs.color_map.items()])

with tab_log:
    st.subheader("Bohrprofil")
    st.code(f"Legende: Seite {(legend.source_page or 0) + 1}, "
            f"DIN-Sektionen: {', '.join(legend.present_din_keys()) or 'keine'}\n"
            f"Kernbohrungen: {len(boreholes)} "
            f"({', '.join(b.bohr_id for b in boreholes)})\n"
            f"NHN-Arithmetik korrekt: {nhn_ok}/{len(boreholes)}\n"
            f"Bodenschichten konsolidiert: {layers_total}, "
            f"davon unsicher (gelb): {layers_unsure}")
    st.subheader("Längsschnitt")
    st.code("\n".join(laengs.log))

# ===========================================================================
# 4 · Excel erzeugen & herunterladen
# ===========================================================================
st.header("4 · Excel erzeugen")
st.write("Markierung in der Datei: 🟩 grün = sicher, 🟨 gelb = unsicher / "
         "nicht klassifizierbar (manuell prüfen).")

if st.button("📊 Excel generieren", type="primary"):
    with st.spinner("Excel wird erstellt…"):
        data = excel_writer.workbook_bytes(boreholes, abschnitte, selected)
    st.success("Fertig! Datei unten herunterladen.")
    st.download_button(
        "⬇️ Geo_Daten.xlsx herunterladen", data=data,
        file_name="Geo_Daten.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
