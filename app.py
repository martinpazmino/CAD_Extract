"""Geo_Agent – lokales Web-Tool fuer Bodengutachten.

    streamlit run app.py

Seiten: Baugrundmodell (v2: PDF -> Bohrungen -> 3D-Modell IFC 4.3 im That-Open-Viewer) und
Excel nach Vorlage (v1, Layout Hamburg). Dokumentation: docs/19_app_v2.md.
"""
import streamlit as st

from ui import viewer  # noqa: F401  (registriert die MIME-Typen fuer den Viewer, bevor er geladen wird)

st.set_page_config(page_title="Geo_Agent", page_icon="🧱", layout="wide")
seite = st.navigation([
    st.Page("ui/baugrundmodell.py", title="Baugrundmodell", icon="🧱", default=True),
    st.Page("ui/excel_v1.py", title="Excel nach Vorlage (v1)", icon="📊"),
])
seite.run()
