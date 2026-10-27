"""That-Open-Viewer (apps/web/dist) als Streamlit-Komponente.

Der gebaute Viewer liegt im Repo (apps/web/dist), damit die App ohne Node laeuft; neu bauen mit
`cd apps/web && npm install && npm run build`. Das IFC wird nach dist/modelle/<hash>.ifc geschrieben
und per URL uebergeben (kein Megabyte-Transfer bei jedem Rerun).
"""
from __future__ import annotations

import hashlib
import mimetypes
from pathlib import Path

import streamlit.components.v1 as components

DIST = Path(__file__).resolve().parents[1] / "apps" / "web" / "dist"
MODELLE = DIST / "modelle"
BEHALTEN = 20                                   # so viele erzeugte IFC bleiben liegen

# Windows liefert .js/.mjs je nach Registry als text/plain: Module und Worker brauchen JavaScript,
# WebAssembly braucht application/wasm. Streamlit nimmt den Typ aus mimetypes.
for typ, endung in (("text/javascript", ".js"), ("text/javascript", ".mjs"), ("application/wasm", ".wasm"),
                    ("text/css", ".css"), ("text/html", ".html")):
    mimetypes.add_type(typ, endung)

_komponente = components.declare_component("baugrund_viewer", path=str(DIST)) if (DIST / "index.html").exists() else None


def verfuegbar() -> bool:
    return _komponente is not None


def zeigen(ifc: bytes, titel: str = "", ueberhoehung: int = 5, hoehe: int = 720, key: str = "viewer") -> None:
    """IFC im Viewer zeigen; gleicher Inhalt = gleiche URL, der Viewer laedt dann nicht neu."""
    if _komponente is None:
        raise RuntimeError("Viewer nicht gebaut: cd apps/web && npm install && npm run build")
    MODELLE.mkdir(parents=True, exist_ok=True)
    name = hashlib.sha256(ifc).hexdigest()[:20] + ".ifc"
    ziel = MODELLE / name
    if not ziel.exists():
        ziel.write_bytes(ifc)
        alte = sorted(MODELLE.glob("*.ifc"), key=lambda p: p.stat().st_mtime)[:-BEHALTEN]
        for p in alte:
            p.unlink(missing_ok=True)
    _komponente(ifc=f"modelle/{name}", titel=titel, ueberhoehung=int(ueberhoehung), hoehe=int(hoehe),
                key=key, default=None)
