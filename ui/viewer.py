"""That-Open-Viewer (apps/web/dist) als Streamlit-Komponente mit Rueckkanal.

Der gebaute Viewer liegt im Repo (apps/web/dist), damit die App ohne Node laeuft; neu bauen mit
`cd apps/web && npm install && npm run build`. Dateien (IFC, Bild der Unterlage) werden nach
dist/modelle/<hash>.<endung> geschrieben und per URL uebergeben (kein Megabyte-Transfer bei jedem Rerun).
Der Viewer meldet Aenderungen (Bohrung verschoben, Station, GOK, Kalibrierung, geprueft) als Ereignis mit
laufender Nummer zurueck; ui/projekt.ereignis_anwenden wendet jede Nummer einmal an (docs/20).
"""
from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path

import streamlit.components.v1 as components

DIST = Path(__file__).resolve().parents[1] / "apps" / "web" / "dist"
MODELLE = DIST / "modelle"
BEHALTEN = 20                                   # so viele erzeugte Dateien je Endung bleiben liegen

# Windows liefert .js/.mjs je nach Registry als text/plain: Module und Worker brauchen JavaScript,
# WebAssembly braucht application/wasm. Streamlit nimmt den Typ aus mimetypes.
for typ, endung in (("text/javascript", ".js"), ("text/javascript", ".mjs"), ("application/wasm", ".wasm"),
                    ("text/css", ".css"), ("text/html", ".html"), ("image/png", ".png")):
    mimetypes.add_type(typ, endung)

_komponente = components.declare_component("baugrund_viewer", path=str(DIST)) if (DIST / "index.html").exists() else None


def verfuegbar() -> bool:
    return _komponente is not None


def ablegen(daten: bytes, endung: str) -> str:
    """Datei fuer den Viewer ablegen; gleicher Inhalt = gleiche URL (der Viewer laedt dann nicht neu)."""
    MODELLE.mkdir(parents=True, exist_ok=True)
    name = f"{hashlib.sha256(daten).hexdigest()[:20]}.{endung}"
    ziel = MODELLE / name
    if not ziel.exists():
        ziel.write_bytes(daten)
        for alt in sorted(MODELLE.glob(f"*.{endung}"), key=lambda p: p.stat().st_mtime)[:-BEHALTEN]:
            alt.unlink(missing_ok=True)
    return f"modelle/{name}"


def zeigen(ifc: bytes | None, titel: str = "", ueberhoehung: int = 5, hoehe: int = 760, key: str = "viewer",
           **weitere) -> dict | None:
    """IFC (oder nur Bohrungen, solange noch kein Modell erzeugt ist) im Viewer zeigen.

    weitere: projekt (Signatur, gleiche = Kamera bleibt), ursprung, epsg, modus, bohrungen (Stecknadeln),
    unterlage (url, art, breite, hoehe, mm_pro_px, kalibrierung), nr (zuletzt angewendetes Ereignis),
    bearbeiten (Zaehler: Aenderung schaltet den Lage-Modus ein). Rueckgabe: letztes Ereignis.
    """
    if _komponente is None:
        raise RuntimeError("Viewer nicht gebaut: cd apps/web && npm install && npm run build")
    url = ablegen(ifc, "ifc") if ifc else None
    return _komponente(ifc=url, titel=titel, ueberhoehung=int(ueberhoehung), hoehe=int(hoehe), key=key,
                       default=None, **weitere)
