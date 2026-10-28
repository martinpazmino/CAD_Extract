"""Ablauf v2 ohne Oberflaeche: PDF -> kanonisches JSON (Extraktion v4) -> Pruefung/Korrekturen -> Baugrundmodell (IFC).

Die Extraktion bleibt in spikes/extraktion_v2/prototyp_v4.py (Regressionsreferenz, docs/17); der
Modellierer in services/modeler (docs/18). Hier nur Verdrahtung, Korrekturen des Nutzers und
Fortschritt; jede Korrektur wird im JSON markiert (coord_source/gok_source), nie still uebernommen.
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[1]
EXTRAKTOR = REPO / "spikes" / "extraktion_v2" / "prototyp_v4.py"
BEISPIELE = REPO / "data" / "beispiele"
sys.path.insert(0, str(REPO / "services" / "modeler"))

from baugrundmodell.einheiten import einheiten_aus_vorgabe  # noqa: E402
from baugrundmodell.modell import bauen, bericht, ifc_schreiben  # noqa: E402

# Arbeitsordner (Zwischenablage, Projekte); mit GEO_AGENT_ARBEIT an einen festen Ort legbar
ARBEIT = Path(os.environ.get("GEO_AGENT_ARBEIT") or Path(tempfile.gettempdir()) / "geo_agent")
_modul = None


def extraktor():
    """prototyp_v4 einmal laden (er haengt seinen Ordner selbst an sys.path)."""
    global _modul
    if _modul is None:
        spec = importlib.util.spec_from_file_location("prototyp_v4", EXTRAKTOR)
        _modul = importlib.util.module_from_spec(spec)
        sys.modules["prototyp_v4"] = _modul
        spec.loader.exec_module(_modul)
    return _modul


def ocr_verfuegbar() -> bool:
    return importlib.util.find_spec("rapidocr_onnxruntime") is not None


def _extraktor_stand() -> str:
    """Fingerabdruck des Extraktors: aendert er sich, wird neu extrahiert."""
    h = hashlib.sha256()
    for f in sorted(EXTRAKTOR.parent.glob("prototyp_v*.py")) + [REPO / "geo_agent" / "soil.py"]:
        h.update(f.read_bytes())
    return h.hexdigest()[:12]


def pdf_extrahieren(name: str, daten: bytes, ocr: bool = True,
                    fortschritt: Callable[[int, int, str], None] | None = None) -> dict:
    """Ein PDF -> kanonisches JSON (auf der Platte zwischengespeichert). fortschritt(seite, seiten, klasse)."""
    sha = hashlib.sha256(daten).hexdigest()
    ablage = ARBEIT / "json" / f"{sha[:24]}_{int(bool(ocr))}_{_extraktor_stand()}.json"
    if ablage.exists():
        doc = json.loads(ablage.read_text(encoding="utf-8"))
        doc["document"]["file"] = Path(name).name
        return doc
    sauber = re.sub(r"[^\w.\-]+", "_", Path(name).name) or "dokument.pdf"
    ziel = ARBEIT / "pdf" / sha[:16] / sauber
    ziel.parent.mkdir(parents=True, exist_ok=True)
    if not ziel.exists():
        ziel.write_bytes(daten)
    (ARBEIT / "ocr").mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("GEO_OCR_CACHE", str(ARBEIT / "ocr"))
    mod = extraktor()
    original = mod.primitives
    seiten = mod.pymupdf.open(ziel).page_count
    zaehler = {"n": 0}

    def mit_fortschritt(page):                       # Fortschritt ohne Eingriff in den Extraktor
        ergebnis = original(page)
        if page.number + 1 > zaehler["n"]:
            zaehler["n"] = page.number + 1
            if fortschritt:
                fortschritt(zaehler["n"], seiten, ergebnis[-1])
        return ergebnis

    alt_ocr = mod.RULES["ocr"], mod.RULES["ocr_supplement"]
    mod.RULES["ocr"] = mod.RULES["ocr_supplement"] = bool(ocr)
    mod.primitives = mit_fortschritt
    try:
        bohrungen, dph = mod.extract(ziel)
        doc = mod.to_canonical(ziel, bohrungen, dph)
    finally:
        mod.primitives = original
        mod.RULES["ocr"], mod.RULES["ocr_supplement"] = alt_ocr
    doc["document"]["file"] = Path(name).name
    ablage.parent.mkdir(parents=True, exist_ok=True)
    ablage.write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    return doc


def pdf_pfad(dokument: dict) -> Path | None:
    """Abgelegtes Gutachten-PDF eines Dokuments (beim Extrahieren unter ARBEIT/pdf/<sha>/ gespeichert)."""
    sha = dokument.get("sha256") or ""
    ordner = ARBEIT / "pdf" / sha[:16]
    if not sha or not ordner.is_dir():
        return None
    return next(iter(sorted(ordner.glob("*.pdf"))), None)


def ist_extrahiert(daten: bytes, ocr: bool) -> bool:
    sha = hashlib.sha256(daten).hexdigest()
    return (ARBEIT / "json" / f"{sha[:24]}_{int(bool(ocr))}_{_extraktor_stand()}.json").exists()


# ---------------------------------------------------------------- Modell
@dataclass
class Ergebnis:
    ifc: bytes
    bericht: dict
    farben: dict[str, str]


def modell_bauen(docs: list[dict], vorgabe: list[dict] | None = None, methode: str = "idw",
                 puffer: float | None = None, raster: float | None = None, basis: float | None = None,
                 ursprung: tuple[float, float] | None = None):
    """Nur die Geometrie (teuer bei Trassen); das IFC schreibt ifc_bytes."""
    return bauen(docs, einheiten_aus_vorgabe(vorgabe) if vorgabe else None, methode, raster, puffer, basis, ursprung)


def ifc_bytes(m, docs: list[dict], pruefstand: str | None = None, durchmesser: float | None = None,
              durchmesser_je: dict[str, float] | None = None) -> bytes:
    ARBEIT.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".ifc", dir=ARBEIT, delete=False) as fh:
        pfad = Path(fh.name)
    try:
        ifc_schreiben(m, pfad, docs, pruefstand=pruefstand, durchmesser=durchmesser, durchmesser_je=durchmesser_je)
        return pfad.read_bytes()
    finally:
        pfad.unlink(missing_ok=True)


def modell_rechnen(docs: list[dict], vorgabe: list[dict] | None = None, methode: str = "idw",
                   puffer: float | None = None, raster: float | None = None, basis: float | None = None,
                   ursprung: tuple[float, float] | None = None, pruefstand: str | None = None,
                   durchmesser: float | None = None, durchmesser_je: dict[str, float] | None = None) -> Ergebnis:
    m = modell_bauen(docs, vorgabe, methode, puffer, raster, basis, ursprung)
    b = bericht(m)
    return Ergebnis(ifc_bytes(m, docs, pruefstand, durchmesser, durchmesser_je), b,
                    {e["name"]: e["farbe"] for e in b["einheiten"]})


def ohne_pruefvermerke(docs: list[dict]) -> list[dict]:
    """Kopie ohne geprueft-Haken: Schluessel fuer die Geometrie (Haken setzen rechnet das Modell nicht neu)."""
    neu = json.loads(json.dumps(docs))
    for d in neu:
        for b in d["boreholes"]:
            b.pop("geprueft", None)
            for ly in b.get("layers") or []:
                ly.pop("geprueft", None)
    return neu


def unterlage_rendern(pdf: bytes, seite: int = 0, max_px: int = 6000) -> dict:
    """Plan-Seite (Lageplan oder Laengsschnitt) als PNG fuer den Viewer: laengste Seite hoechstens max_px,
    hoechstens 300 dpi. Rueckgabe: png (bytes), breite, hoehe (px), seiten, mm_pro_px."""
    import pymupdf
    doc = pymupdf.open(stream=pdf, filetype="pdf")
    seite = max(0, min(int(seite), doc.page_count - 1))
    page = doc[seite]
    r = page.rect                                   # pt (1/72 inch), Ansicht nach /Rotate
    skala = min(max_px / max(r.width, r.height), 300 / 72)
    pix = page.get_pixmap(matrix=pymupdf.Matrix(skala, skala), alpha=False)
    return {"png": pix.tobytes("png"), "breite": pix.width, "hoehe": pix.height, "seiten": doc.page_count,
            "mm_pro_px": 25.4 / 72 / skala}


def json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8")
