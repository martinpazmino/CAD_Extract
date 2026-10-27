"""Synthetische Baugrundfaelle mit bekannter Wahrheit (Tests, Demo-Modell fuer den Viewer).

Jede Einheit ist durch ihre Unterkante z(x, y) in m NHN gegeben (lokale Koordinaten zum Ursprung);
Bohrprofile entstehen durch Abteufen an den Bohrpunkten. Ausgabe im kanonischen Extraktionsformat.

    python -m baugrundmodell.synthetisch <fall> <ausgabe.json>      (Faelle: siehe FAELLE)
"""
from __future__ import annotations

import json
import math
import sys
from dataclasses import dataclass, field
from typing import Callable

URSPRUNG = (565000.0, 5933000.0)
EPSG = 25832


@dataclass
class Fall:
    name: str
    gok: Callable[[float, float], float]
    einheiten: list[tuple[str, Callable[[float, float], float]]]       # (Bodenart, Unterkante NHN)
    bohrungen: list[tuple[str, float, float, float]]                   # (Code, x, y, Endteufe m u. GOK)
    extra: list[dict] = field(default_factory=list)                    # weitere kanonische Bohrungen


def profil(fall: Fall, x: float, y: float, endteufe: float) -> list[tuple[str, float, float]]:
    """(Bodenart, Tiefe oben, Tiefe unten) in m unter GOK."""
    gok = fall.gok(x, y)
    z_ende = gok - endteufe
    oben = gok
    schichten = []
    for klasse, uk in fall.einheiten:
        unten = max(min(uk(x, y), oben), z_ende)
        if oben - unten > 0.005:
            schichten.append((klasse, round(gok - oben, 2), round(gok - unten, 2)))
        oben = unten
        if oben <= z_ende + 1e-9:
            break
    if oben > z_ende + 0.005:                                          # letzte Einheit bis zur Endteufe
        schichten.append((fall.einheiten[-1][0], round(gok - oben, 2), round(endteufe, 2)))
    return schichten


def schicht(klasse: str | None, oben: float, unten: float) -> dict:
    return {"top_depth": oben, "bottom_depth": unten, "description_raw": klasse or "", "soil_class": klasse,
            "hatch_class": None, "confidence": 1.0, "label_confirmed": True, "issues": [],
            "provenance": [{"page": 0, "method": "synthetisch", "bbox": None}]}


def bohrung(code: str, x: float | None, y: float | None, gok: float | None, schichten: list[dict]) -> dict:
    return {"code": code, "kind": "Bohrung", "gok_nhn": gok,
            "end_depth": schichten[-1]["bottom_depth"] if schichten else None,
            "x": None if x is None else URSPRUNG[0] + x, "y": None if y is None else URSPRUNG[1] + y,
            "crs_epsg": EPSG if x is not None else None, "coord_source": "synthetisch" if x is not None else None,
            "layers": schichten, "groundwater": [], "groundwater_status": None,
            "checks": {"label_support": 1.0, "scale": None, "mode": "synthetisch", "schichtenverzeichnis": None,
                       "duplicates": []},
            "issues": [], "provenance": [{"page": 0, "method": "synthetisch", "bbox": None}]}


def dokument(fall: Fall) -> dict:
    bh = []
    for code, x, y, ende in fall.bohrungen:
        bh.append(bohrung(code, x, y, round(fall.gok(x, y), 2),
                          [schicht(k, o, u) for k, o, u in profil(fall, x, y, ende)]))
    return {"document": {"file": f"synthetisch_{fall.name}.pdf", "sha256": "0" * 64,
                         "parser_version": "synthetisch", "pages": 1},
            "boreholes": bh + fall.extra, "soundings": []}


def _raster(ende: float) -> list[tuple[str, float, float, float]]:
    return [(f"B{3 * i + j + 1}", 50.0 * j, 50.0 * i, ende) for i in range(3) for j in range(3)]


def _gok(x, y):
    return 40.0 + 0.02 * x - 0.01 * y


def geneigt() -> Fall:
    """Ebene, geneigte Schichten; jede Bohrung trifft jede Einheit (TPS muss die Ebenen exakt treffen)."""
    return Fall("geneigt", _gok, [
        ("Auffuellung", lambda x, y: _gok(x, y) - 1.0),
        ("Sand", lambda x, y: 34.0 - 0.03 * x),
        ("Geschiebemergel", lambda x, y: 28.0 + 0.02 * y - 0.01 * x),
        ("Ton", lambda x, y: -100.0)], _raster(18.0))


def auskeilen() -> Fall:
    """Torf nur im Westen (Maechtigkeit 2 m bei x=0, 0 ab x=50)."""
    return Fall("auskeilen", _gok, [
        ("Auffuellung", lambda x, y: _gok(x, y) - 1.0),
        ("Sand", lambda x, y: 34.0 - 0.03 * x),
        ("Torf", lambda x, y: 34.0 - 0.03 * x - max(0.0, 2.0 - 0.04 * x)),
        ("Geschiebemergel", lambda x, y: 26.0 + 0.02 * y - 0.01 * x),
        ("Ton", lambda x, y: -100.0)], _raster(18.0))


def linse() -> Fall:
    """Kieslinse im Sand nur an der mittleren Bohrung B5."""
    def kies_dicke(x, y):
        return max(0.0, 1.5 * (1 - math.hypot(x - 50, y - 50) / 20.0))
    return Fall("linse", _gok, [
        ("Auffuellung", lambda x, y: _gok(x, y) - 1.0),
        ("Sand", lambda x, y: 32.0),
        ("Kies", lambda x, y: 32.0 - kies_dicke(x, y)),
        ("Sand", lambda x, y: 26.0),
        ("Geschiebemergel", lambda x, y: -100.0)], _raster(18.0))


def zensiert() -> Fall:
    """Wie 'geneigt', aber die Ostreihe (x=100) endet nach 6 m im Sand."""
    f = geneigt()
    f.name = "zensiert"
    f.bohrungen = [(c, x, y, 6.0 if x == 100.0 else e) for c, x, y, e in f.bohrungen]
    return f


def stoerungen() -> Fall:
    """Wie 'geneigt' plus: unklassifizierte Zwischenschicht, Bohrung ohne Koordinaten, ohne GOK."""
    f = geneigt()
    f.name = "stoerungen"
    code, x, y, e = f.bohrungen[4]
    gok = round(f.gok(x, y), 2)
    p = profil(f, x, y, e)
    k, o, u = p[1]                                                     # Sand in zwei Teile, Mitte unklassifiziert
    schichten = [schicht(*p[0]), schicht(k, o, o + 1.0), schicht(None, o + 1.0, o + 1.3), schicht(k, o + 1.3, u)] + \
                [schicht(*s) for s in p[2:]]
    f.bohrungen = f.bohrungen[:4] + f.bohrungen[5:]
    f.extra = [bohrung(code, x, y, gok, schichten),
               bohrung("RKS 7", None, None, 39.0, [schicht("Sand", 0.0, 3.0)]),
               bohrung("RKS 8", 20.0, 20.0, None, [schicht("Sand", 0.0, 3.0)])]
    return f


def demo() -> Fall:
    """Demo fuer den Viewer: Auffuellung, Sand mit Kieslinse, auskeilender Torf, Geschiebemergel, Ton;
    unregelmaessige Bohrpunkte, flache Kleinbohrungen."""
    def gok(x, y):
        return 38.0 + 0.015 * x - 0.008 * y + 0.6 * math.sin(x / 40.0)

    def kies(x, y):
        return max(0.0, 2.0 * (1 - math.hypot(x - 70, y - 40) / 45.0))

    def torf(x, y):
        return max(0.0, 1.8 - 0.025 * (x + 0.3 * y))

    def sand_uk(x, y):
        return 31.5 - 0.02 * x + 0.5 * math.cos(y / 35.0)

    punkte = [(0, 0, 15), (45, 10, 15), (95, -5, 15), (140, 15, 20), (20, 60, 15), (70, 40, 20),
              (120, 70, 15), (5, 110, 15), (60, 95, 6), (110, 120, 6), (150, 90, 20), (35, 35, 5)]
    return Fall("demo", gok, [
        ("Auffuellung", lambda x, y: gok(x, y) - 0.8 - 0.4 * math.sin(y / 25.0)),
        ("Sand", lambda x, y: 34.0 - 0.01 * x),
        ("Kies", lambda x, y: 34.0 - 0.01 * x - kies(x, y)),
        ("Sand", sand_uk),
        ("Torf", lambda x, y: sand_uk(x, y) - torf(x, y)),
        ("Geschiebemergel", lambda x, y: 25.0 + 0.015 * y - 0.01 * x),
        ("Ton", lambda x, y: -100.0)],
        [(f"BS {k + 1}" if e < 10 else f"B {k + 1}", float(x), float(y), float(e)) for k, (x, y, e) in enumerate(punkte)])


FAELLE = {f.__name__: f for f in (geneigt, auskeilen, linse, zensiert, stoerungen, demo)}


if __name__ == "__main__":
    fall = FAELLE[sys.argv[1]]()
    with open(sys.argv[2], "w") as fh:
        json.dump(dokument(fall), fh, ensure_ascii=False, indent=1)
