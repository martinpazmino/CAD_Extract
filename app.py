"""Geo_Agent – Excel nach Vorlage (v1, Layout Hamburg) als Streamlit-Seite.

    streamlit run app.py          (Windows: start_excel.bat)

Das Baugrundmodell (PDF -> Bohrungen pruefen -> Lage -> Einheiten -> IFC 4.3 im That-Open-Viewer) ist die
Schritt-App: python -m server (Windows: start.bat), Beschreibung in docs/21_app_schritte_normen.md.
"""
import streamlit as st

st.set_page_config(page_title="Geo_Agent – Excel v1", page_icon="📊", layout="wide")
st.info("Das **Baugrundmodell** ist jetzt eine eigene Schritt-App: `start.bat` bzw. `python -m server` "
        "(http://localhost:8500).", icon="🧱")
st.navigation([st.Page("ui/excel_v1.py", title="Excel nach Vorlage (v1)", icon="📊", default=True)]).run()
