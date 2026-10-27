"""Ablauf v2 ohne Oberflaeche: PDF -> kanonisches JSON (Extraktion v4) -> Pruefung/Korrekturen -> Baugrundmodell (IFC).

Die Extraktion bleibt in spikes/extraktion_v2/prototyp_v4.py (Regressionsreferenz, docs/17); der
Modellierer in services/modeler (docs/18). Hier nur Verdrahtung, Korrekturen des Nutzers und
Fortschritt; jede Korrektur wird im JSON markiert (coord_source/gok_source), nie still uebernommen.
"""
from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import os
import re
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

REPO = Path(__file__).resolve().parents[1]
EXTRAKTOR = REPO / "spikes" / "extraktion_v2" / "prototyp_v4.py"
BEISPIELE = REPO / "data" / "beispiele"
sys.path.insert(0, str(REPO / "services" / "modeler"))

from baugrundmodell.einheiten import einheiten_aus_vorgabe  # noqa: E402
from baugrundmodell.ifc4x3 import farbe, farbschluessel, hexfarbe  # noqa: E402
from baugrundmodell.modell import bauen, bericht, ifc_schreiben  # noqa: E402

ARBEIT = Path(tempfile.gettempdir()) / "geo_agent"
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


def ist_extrahiert(daten: bytes, ocr: bool) -> bool:
    sha = hashlib.sha256(daten).hexdigest()
    return (ARBEIT / "json" / f"{sha[:24]}_{int(bool(ocr))}_{_extraktor_stand()}.json").exists()


# ---------------------------------------------------------------- Pruefung und Korrekturen
@dataclass
class Einstellungen:
    ohne_lage: str = "schematisch"           # schematisch | weglassen
    abstand_m: float = 20.0                  # Abstand der schematischen Reihe
    gok_relativ: bool = True                 # fehlt die GOK bei allen: 0 m (relativ, markiert)
    methode: str = "idw"


@dataclass
class Vorbereitung:
    docs: list[dict]                         # Eingabe fuer den Modellierer
    hinweise: list[str] = field(default_factory=list)
    nicht_im_modell: list[dict] = field(default_factory=list)


def _natuerlich(code: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", code)]


def zeilen(docs: list[dict]) -> list[dict]:
    """Eine Tabellenzeile je Bohrung (Schluessel 'd:b'); Doppelte (gleicher Code) standardmaessig aus."""
    out, gesehen = [], {}
    for di, d in enumerate(docs):
        for bi, b in enumerate(d["boreholes"]):
            schichten = b.get("layers") or []
            konf = [ly.get("confidence") or 0 for ly in schichten]
            doppelt = gesehen.get(b["code"])
            hinweise = list(b.get("issues") or [])
            if doppelt:
                hinweise.insert(0, f"doppelt (auch in {doppelt})")
            gesehen.setdefault(b["code"], d["document"]["file"])
            out.append({
                "id": f"{di}:{bi}", "Bohrung": b["code"], "Dokument": d["document"]["file"],
                "Seite": int((b.get("provenance") or [{}])[0].get("page", 0) or 0) + 1,
                "Modell": bool(schichten) and not doppelt,
                "GOK [m NHN]": b.get("gok_nhn"), "Endteufe [m]": b.get("end_depth"),
                "Rechtswert": b.get("x"), "Hochwert": b.get("y"), "EPSG": b.get("crs_epsg"),
                "Lage aus": b.get("coord_source") or "", "Schichten": len(schichten),
                "Konfidenz": round(sum(konf) / len(konf), 2) if konf else None,
                "Grundwasser": ", ".join(f"{g['depth']:.2f} m" for g in b.get("groundwater") or []) or
                               (b.get("groundwater_status") or ""),
                "Hinweise": "; ".join(hinweise),
            })
    return out


def _zahl(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f                     # NaN aus der Tabelle -> None


def vorbereiten(docs: list[dict], tabelle: list[dict], e: Einstellungen) -> Vorbereitung:
    """Korrekturen aus der Tabelle anwenden; fehlende Lage/GOK nach den Einstellungen behandeln."""
    neu = copy.deepcopy(docs)
    hinweise: list[str] = []
    raus: list[dict] = []
    gewaehlt = []
    for z in tabelle:
        di, bi = map(int, z["id"].split(":"))
        b = neu[di]["boreholes"][bi]
        if not z.get("Modell"):
            raus.append({"code": b["code"], "dokument": neu[di]["document"]["file"], "grund": "abgewaehlt"})
            continue
        x, y, gok = _zahl(z.get("Rechtswert")), _zahl(z.get("Hochwert")), _zahl(z.get("GOK [m NHN]"))
        epsg = _zahl(z.get("EPSG"))
        if (x, y) != (_zahl(b.get("x")), _zahl(b.get("y"))) or (epsg or None) != (b.get("crs_epsg") or None):
            b["x"], b["y"] = x, y
            b["crs_epsg"] = int(epsg) if epsg else None
            b["coord_source"] = "manuell" if x is not None else None
        if gok != _zahl(b.get("gok_nhn")):
            b["gok_nhn"], b["gok_source"] = gok, "manuell"
        gewaehlt.append(b)
    for d in neu:                                          # abgewaehlte gar nicht erst an den Modellierer
        d["boreholes"] = [b for b in d["boreholes"] if any(b is g for g in gewaehlt)]

    ohne_gok = [b for b in gewaehlt if b.get("gok_nhn") is None]
    if ohne_gok and e.gok_relativ and len(ohne_gok) == len(gewaehlt):
        for b in ohne_gok:
            b["gok_nhn"], b["gok_source"] = 0.0, "relativ"
        hinweise.append("Keine Ansatzhoehen (GOK) im PDF: Hoehen relativ, Gelaende = 0 m.")
    elif ohne_gok:
        hinweise.append(f"{len(ohne_gok)} Bohrungen ohne GOK bleiben draussen (GOK in der Tabelle eintragen).")

    # Lage: schematische Reihe nur fuer modellierbare Bohrungen (mit GOK) und nur ohne echte Koordinaten
    modellierbar = [b for b in gewaehlt if b.get("gok_nhn") is not None]
    ohne_lage = [b for b in modellierbar if b.get("x") is None or b.get("y") is None]
    mit_lage = [b for b in modellierbar if b.get("x") is not None and b.get("y") is not None]
    if ohne_lage and e.ohne_lage == "schematisch" and not mit_lage:
        for k, b in enumerate(sorted(ohne_lage, key=lambda b: _natuerlich(b["code"]))):
            b["x"], b["y"], b["crs_epsg"], b["coord_source"] = k * e.abstand_m, 0.0, None, "schematisch"
        hinweise.append(f"Keine Koordinaten im PDF: {len(ohne_lage)} Bohrungen schematisch in einer Reihe "
                        f"({e.abstand_m:g} m Abstand, nach Code) – Lage nicht vermessen, nur zur Anschauung.")
    elif ohne_lage:
        hinweise.append(f"{len(ohne_lage)} Bohrungen ohne Koordinaten bleiben draussen "
                        f"(in der Tabelle eintragen, um sie zu modellieren).")
    return Vorbereitung(neu, hinweise, raus)


# ---------------------------------------------------------------- Modell
@dataclass
class Ergebnis:
    ifc: bytes
    bericht: dict
    farben: dict[str, str]


def modell_rechnen(docs: list[dict], vorgabe: list[dict] | None = None, methode: str = "idw") -> Ergebnis:
    m = bauen(docs, einheiten_aus_vorgabe(vorgabe) if vorgabe else None, methode)
    ARBEIT.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(suffix=".ifc", dir=ARBEIT, delete=False) as fh:
        pfad = Path(fh.name)
    try:
        ifc_schreiben(m, pfad, docs)
        daten = pfad.read_bytes()
    finally:
        pfad.unlink(missing_ok=True)
    b = bericht(m)
    return Ergebnis(daten, b, {e["name"]: e["farbe"] for e in b["einheiten"]})


def bodenart_farbe(klasse: str | None) -> str:
    return hexfarbe(farbe(klasse)) if farbschluessel(klasse) else "#d9d9d9"


def json_bytes(obj) -> bytes:
    return json.dumps(obj, ensure_ascii=False, indent=1).encode("utf-8")
