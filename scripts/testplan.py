"""Synthetische Unterlagen mit bekannter Wahrheit fuer die Pruefung des Lage-Editors (apps/web/scripts/check.mjs).

Lageplan: Demo-Fall (services/modeler, 12 Bohrungen) im Massstab 1:500, um 10 Grad gedreht, Bohrungen als
Kreise mit Code. Zwei Bohrungen verlieren ihre Koordinaten (muessen im Viewer gesetzt werden).
Laengsschnitt: sechs Bohrungen in einer Reihe mit Stationen 0/10/25/45/60/80 m, Laenge 1:500, Hoehe 1:100.
Ausgabe je Fall: <name>.pdf, <name>.png (ueber ui.pipeline.unterlage_rendern wie in der App), args_<name>.json
(Viewer-Argumente wie aus der App), <name>_extraktion.json (zum Hochladen in die App) und wahrheit_<name>.json;
dazu plan_ohne_lage_extraktion.json (gleicher Plan, keine Bohrung mit Koordinaten, GOK + 300 m bzw. ohne GOK).

    python scripts/testplan.py <ausgabeordner> [--ifc-plan modelle/demo.ifc]
"""
from __future__ import annotations

import copy
import json
import math
import sys
from pathlib import Path

import pymupdf

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "services" / "modeler"))

from baugrundmodell import synthetisch as syn  # noqa: E402
from ui import projekt as pj  # noqa: E402
from ui.pipeline import unterlage_rendern  # noqa: E402

MM = 72 / 25.4                                   # pt je mm
OHNE_LAGE = ("B 6", "BS 9")


def lageplan(aus: Path) -> None:
    doc = syn.dokument(syn.demo())
    massstab, drehung = 500.0, math.radians(10.0)
    e_ref, n_ref = syn.URSPRUNG[0] + 75.0, syn.URSPRUNG[1] + 55.0      # Blattmitte
    breite, hoehe = 420 * MM, 297 * MM                                   # A3 quer

    def blatt(e: float, n: float) -> tuple[float, float]:
        dx, dy = (e - e_ref) / massstab * 1000, (n - n_ref) / massstab * 1000      # mm Papier
        x = dx * math.cos(drehung) - dy * math.sin(drehung)
        y = dx * math.sin(drehung) + dy * math.cos(drehung)
        return breite / 2 + x * MM, hoehe / 2 - y * MM

    pdf = pymupdf.open()
    seite = pdf.new_page(width=breite, height=hoehe)
    seite.draw_rect(pymupdf.Rect(10 * MM, 10 * MM, breite - 10 * MM, hoehe - 10 * MM), color=(0, 0, 0), width=1)
    seite.insert_text((15 * MM, 20 * MM), "Lageplan Bohrungen M 1:500 (synthetisch)", fontsize=14)
    for k in range(-2, 4):                                              # Strassenachse als Beiwerk
        a, b = blatt(e_ref - 120, n_ref + 30 * k), blatt(e_ref + 120, n_ref + 30 * k)
        seite.draw_line(a, b, color=(0.75, 0.75, 0.75), width=0.5)
    wahr = {}
    for b in doc["boreholes"]:
        x, y = blatt(b["x"], b["y"])
        seite.draw_circle((x, y), 2 * MM, color=(0.8, 0, 0), width=1.2)
        seite.draw_line((x - 3 * MM, y), (x + 3 * MM, y), color=(0.8, 0, 0), width=0.6)
        seite.draw_line((x, y - 3 * MM), (x, y + 3 * MM), color=(0.8, 0, 0), width=0.6)
        seite.insert_text((x + 3 * MM, y - 2 * MM), b["code"], fontsize=9)
        wahr[b["code"]] = {"x": b["x"], "y": b["y"], "pt": [x, y]}
    pdf_bytes = pdf.tobytes()
    (aus / "plan.pdf").write_bytes(pdf_bytes)
    bild = unterlage_rendern(pdf_bytes)
    (aus / "plan.png").write_bytes(bild["png"])
    skala = bild["breite"] / breite                                      # px je pt
    for w in wahr.values():
        w["px"] = [w["pt"][0] * skala, w["pt"][1] * skala]

    # Zwei Bohrungen ohne Koordinaten (muessen auf den Plan gesetzt werden)
    for b in doc["boreholes"]:
        if b["code"] in OHNE_LAGE:
            b["x"] = b["y"] = None
            b["coord_source"] = None
    (aus / "plan_extraktion.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")   # fuer die App
    # Gleicher Plan, aber keine Bohrung mit Koordinaten (Gutachten mit RKS ohne Lage): alles wird aus der Liste gezogen
    # oder per Punkt gesetzt. Echte Hoehen (GOK + 300 m) und Bohrungen ohne GOK (BS ..., wie GWM): ueberhoeht liegt die
    # Ziehebene der einen weit ueber, die der anderen unter der Kamera (docs/16 M34)
    ohne = copy.deepcopy(doc)
    ohne["document"]["file"] = "synthetisch_ohne_lage.pdf"
    for b in ohne["boreholes"]:
        b["x"] = b["y"] = b["crs_epsg"] = b["coord_source"] = None
        b["gok_nhn"] = None if b["code"].startswith("BS") else round(b["gok_nhn"] + 300.0, 2)
    (aus / "plan_ohne_lage_extraktion.json").write_text(json.dumps(ohne, ensure_ascii=False), encoding="utf-8")
    args = viewer_args(doc, "plan", bild, "plan.png", "Lageplan.pdf", "koordinaten")
    (aus / "args_plan.json").write_text(json.dumps(args, ensure_ascii=False), encoding="utf-8")
    (aus / "wahrheit_plan.json").write_text(json.dumps({"bohrungen": wahr, "ohne_lage": OHNE_LAGE,
                                                        "massstab": massstab, "drehung_grad": 10.0}), encoding="utf-8")


def laengsschnitt(aus: Path) -> None:
    stationen = [0.0, 10.0, 25.0, 45.0, 60.0, 80.0]
    fall = syn.demo()
    doc = syn.dokument(fall)
    doc["boreholes"] = [copy.deepcopy(b) for b in doc["boreholes"][:6]]
    for b in doc["boreholes"]:
        b["x"] = b["y"] = None
        b["crs_epsg"] = b["coord_source"] = None
    m_l, m_h = 500.0, 100.0
    breite, hoehe = 420 * MM, 297 * MM                                   # A3 quer: 24 m Hoehe bei 1:100
    x0, h_oben = 30 * MM, 42.0                                           # Station 0 bei 30 mm, 42 m NHN bei 25 mm

    def blatt(station: float, h: float) -> tuple[float, float]:
        return x0 + station / m_l * 1000 * MM, 25 * MM + (h_oben - h) / m_h * 1000 * MM

    pdf = pymupdf.open()
    seite = pdf.new_page(width=breite, height=hoehe)
    seite.insert_text((15 * MM, 15 * MM), "Laengsschnitt M 1:500/100 (synthetisch)", fontsize=12)
    wahr = {}
    for b, s in zip(doc["boreholes"], stationen):
        gok = b["gok_nhn"]
        for ly in b["layers"]:
            a, c = blatt(s, gok - ly["top_depth"]), blatt(s, gok - ly["bottom_depth"])
            farbe = tuple(int(pj.bodenart_farbe(ly["soil_class"])[i:i + 2], 16) / 255 for i in (1, 3, 5))
            seite.draw_rect(pymupdf.Rect(a[0] - 1.5 * MM, a[1], a[0] + 1.5 * MM, c[1]), color=(0, 0, 0), fill=farbe, width=0.4)
        top = blatt(s, gok)
        seite.insert_text((top[0] - 4 * MM, top[1] - 2 * MM), b["code"], fontsize=8)
        wahr[b["code"]] = {"station": s, "gok": gok, "ende": b["end_depth"], "px_top_pt": list(top),
                           "px_unten_pt": list(blatt(s, gok - b["end_depth"]))}
    assert all(0 < blatt(s, wahr[c]["gok"] - wahr[c]["ende"])[1] < hoehe for c, s in zip(wahr, stationen)), "Schnitt passt nicht aufs Blatt"
    pdf_bytes = pdf.tobytes()
    (aus / "schnitt.pdf").write_bytes(pdf_bytes)
    bild = unterlage_rendern(pdf_bytes)
    (aus / "schnitt.png").write_bytes(bild["png"])
    skala = bild["breite"] / breite
    for w in wahr.values():
        w["px_top"] = [v * skala for v in w.pop("px_top_pt")]
        w["px_unten"] = [v * skala for v in w.pop("px_unten_pt")]
    (aus / "schnitt_extraktion.json").write_text(json.dumps(doc, ensure_ascii=False), encoding="utf-8")
    args = viewer_args(doc, "schnitt", bild, "schnitt.png", "Laengsschnitt.pdf", "reihe")
    (aus / "args_schnitt.json").write_text(json.dumps(args, ensure_ascii=False), encoding="utf-8")
    (aus / "wahrheit_schnitt.json").write_text(json.dumps({"bohrungen": wahr, "massstab_laenge": m_l,
                                                           "massstab_hoehe": m_h}), encoding="utf-8")


def viewer_args(doc: dict, art: str, bild: dict, png: str, name: str, modus: str) -> dict:
    """Viewer-Argumente genau wie die App sie baut (ohne Modell: Stecknadeln + Unterlage)."""
    p = pj.neues_projekt([doc], f"test-{art}")
    p.lage_modus = modus
    vorb = pj.modell_eingabe([doc], p, pj.Einstellungen())
    ursprung = pj.ursprung(p, vorb)
    return {"projekt": f"test-{art}", "titel": name, "hoehe": 860, "ueberhoehung": 1, "ursprung": list(ursprung),
            "epsg": 25832 if modus == "koordinaten" else None, "modus": modus,
            "bohrungen": pj.viewer_bohrungen([doc], p, vorb, None), "nr": 0, "ifc": None,
            "unterlage": {"url": f"modelle/{png}", "name": name, "art": art, "breite": bild["breite"],
                          "hoehe": bild["hoehe"], "mm_pro_px": bild["mm_pro_px"], "kalibrierung": None}}


if __name__ == "__main__":
    ziel = Path(sys.argv[1])
    ziel.mkdir(parents=True, exist_ok=True)
    lageplan(ziel)
    laengsschnitt(ziel)
    print("geschrieben:", sorted(p.name for p in ziel.iterdir()))
