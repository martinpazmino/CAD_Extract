"""Baugrundmodell (N3, Layer-Cake) aus kanonischen Extraktions-JSONs: Einheiten -> Flaechen -> Koerper -> IFC.

Ablauf und Parameter: docs/18_modelador_capas.md.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.spatial import cKDTree

from . import __version__
from .einheiten import (Bohrung, Einheit, Kontakt, bohrungen_aus_extraktion, kontakte, korrelieren)
from .flaechen import MIN_MAECHTIGKEIT, PRAESENZ_SCHWELLE, gebiet, netz, schichtmodell
from .ifc4x3 import IfcAusgabe, farbe, hexfarbe
from .koerper import koerper, pruefen, volumen_prismen


@dataclass
class Modell:
    epsg: int | None
    ursprung: tuple[float, float]
    bohrungen: list[Bohrung]
    ausgeschlossen: list[dict]
    einheiten: list[Einheit]
    kontakte: list[list[Kontakt]]
    punkte: np.ndarray                 # lokal (m)
    dreiecke: np.ndarray
    rand: np.ndarray
    flaechen: np.ndarray               # (Einheiten+1, Punkte): Gelaende, Unterkanten
    abstand: np.ndarray                # Abstand jedes Knotens zur naechsten Bohrung (m)
    basis: float
    parameter: dict
    koerper: list[dict] = field(default_factory=list)
    hinweise: list[str] = field(default_factory=list)
    max_abweichung: float = 0.0
    zensurpunkte: int = 0
    ausgeduennt: list[int] = field(default_factory=list)   # Knoten je Einheit, an denen die Ausdehnung endet


def bauen(docs: list[dict], vorgabe: list[Einheit] | None = None, methode: str = "idw",
          raster: float | None = None, puffer: float | None = None, basis: float | None = None) -> Modell:
    bohrungen, ausgeschlossen, epsg = bohrungen_aus_extraktion(docs)
    if not bohrungen:
        raise ValueError("keine modellfaehige Bohrung (Koordinaten, GOK und Schichten noetig)")
    einheiten, zuordnung, hinweise = korrelieren(bohrungen, vorgabe)
    if epsg is None:
        hinweise.append("Lage ohne Georeferenz (lokales System)")
    schema = [b.code for b in bohrungen if b.lage == "schematisch"]
    if schema:
        hinweise.append(f"schematische Lage (Abstaende nicht vermessen, nur zur Anschauung): {', '.join(schema)}")
    relativ = [b.code for b in bohrungen if b.hoehe.startswith("relativ")]
    if relativ:
        hinweise.append(f"relative Hoehen (GOK unbekannt, 0 m gesetzt): {', '.join(relativ)}")
    ks = [kontakte(b, zuordnung[b.code], einheiten) for b in bohrungen]
    ursprung = (round(float(np.mean([b.x for b in bohrungen])), -1), round(float(np.mean([b.y for b in bohrungen])), -1))
    xy_b = np.array([(b.x - ursprung[0], b.y - ursprung[1]) for b in bohrungen])
    if len(bohrungen) > 1:
        nn = float(np.median(cKDTree(xy_b).query(xy_b, k=2)[0][:, 1]))
    else:
        nn = 20.0
    puffer = puffer if puffer is not None else float(np.clip(0.5 * nn, 5.0, 25.0))
    polygon = gebiet(xy_b, puffer)
    flaeche = 0.5 * abs(np.dot(polygon[:, 0], np.roll(polygon[:, 1], 1)) - np.dot(polygon[:, 1], np.roll(polygon[:, 0], 1)))
    raster = raster if raster is not None else float(np.clip(math.sqrt(flaeche) / 40.0, 0.5, 10.0))
    punkte, dreiecke, rand = netz(polygon, xy_b, raster)
    tiefste = min(b.ende for b in bohrungen)
    if basis is None:
        basis = tiefste
    elif basis > tiefste:
        hinweise.append(f"Modellbasis {basis:.2f} m NHN ueber der tiefsten Endteufe {tiefste:.2f}: tiefere Daten abgeschnitten")
    sm = schichtmodell(bohrungen, ks, punkte, xy_b, basis, methode)
    m = Modell(epsg, ursprung, bohrungen, ausgeschlossen, einheiten, ks, punkte, dreiecke, rand, sm["flaechen"],
               sm["abstand"], basis, {"methode": methode, "raster_m": raster, "puffer_m": puffer,
                                      "basis_nhn": basis, "flaeche_m2": float(flaeche),
                                      "praesenz_schwelle": PRAESENZ_SCHWELLE},
               hinweise=hinweise, max_abweichung=sm["max_abweichung_bohrungen"],
               zensurpunkte=sum(len(z) for z in sm["zensur"]), ausgeduennt=sm["ausgeduennt"])
    _koerper(m)
    return m


def _koerper(m: Modell) -> None:
    nummer: dict[str, int] = {}
    for j, e in enumerate(m.einheiten):
        oben, unten = m.flaechen[j], m.flaechen[j + 1]
        d = oben - unten
        nummer[e.klasse] = nummer.get(e.klasse, 0) + 1
        st = {"vorhanden": [], "fehlt": [], "unbekannt": []}
        for b, ks in zip(m.bohrungen, m.kontakte):
            st[ks[j].status].append(b.code)
        info = {"name": e.name, "bodenarten": sorted(e.klassen), "rgb": farbe(sorted(e.klassen)[0], nummer[e.klasse]),
                "bohrungen": st}
        kp = koerper(m.punkte, m.dreiecke, m.rand, oben, unten)
        traeger = d >= MIN_MAECHTIGKEIT
        hinweise = []
        if np.all(np.abs(unten - m.basis) < 1e-6):
            hinweise.append("Unterkante = Modellbasis (keine Bohrung erreicht die Unterkante)")
        if not st["vorhanden"]:
            hinweise.append("in keiner Bohrung angetroffen")
        if m.ausgeduennt and m.ausgeduennt[j]:
            hinweise.append("Ausdehnung begrenzt: endet etwa auf halbem Weg zu Bohrungen ohne diese Einheit")
        if kp is None:
            info.update(knoten=None, flaechen=None, pruefung={"geschlossen": True, "volumen": 0.0}, volumen_m3=0.0)
        else:
            pr = pruefen(*kp)
            info.update(knoten=kp[0], flaechen=kp[1], pruefung=pr,
                        volumen_m3=volumen_prismen(m.punkte, m.dreiecke, oben, unten))
        info.update(maechtigkeit_max=float(d.max()),
                    maechtigkeit_mittel=float(d[traeger].mean()) if traeger.any() else 0.0,
                    max_abstand_bohrung=float(m.abstand[traeger].max()) if traeger.any() else None,
                    hinweise=hinweise)
        m.koerper.append(info)


def ifc_schreiben(m: Modell, pfad, docs: list[dict], bohrsaeulen: bool = True,
                  projekt: str = "Baugrundmodell aus Gutachten") -> dict:
    """IfcGeomodel (Einheiten) + IfcBorehole (Bohrsaeulen der modellierten Bohrungen)."""
    aus = IfcAusgabe(projekt, m.epsg, m.ursprung)
    quellen = sorted({d["document"]["file"] for d in docs})
    n = len(m.einheiten)
    einheiten = []
    for j, k in enumerate(m.koerper):
        if k["knoten"] is None:
            continue
        einheiten.append({
            "name": k["name"], "knoten": k["knoten"], "flaechen": k["flaechen"], "rgb": k["rgb"],
            "geschlossen": k["pruefung"]["geschlossen"], "beschreibung": f"Modelleinheit {j + 1}/{n}",
            "eigenschaften": {
                "Einheit": k["name"], "Reihenfolge": j + 1, "Bodenarten": ", ".join(k["bodenarten"]),
                "Farbe": hexfarbe(k["rgb"]), "Volumen_m3": round(k["volumen_m3"], 1),
                "Maechtigkeit_max_m": round(k["maechtigkeit_max"], 2),
                "Maechtigkeit_mittel_m": round(k["maechtigkeit_mittel"], 2),
                "Max_Abstand_Bohrung_m": round(k["max_abstand_bohrung"], 1) if k["max_abstand_bohrung"] is not None else None,
                "Bohrungen_vorhanden": ", ".join(k["bohrungen"]["vorhanden"]),
                "Bohrungen_fehlt": ", ".join(k["bohrungen"]["fehlt"]),
                "Bohrungen_unbekannt": ", ".join(k["bohrungen"]["unbekannt"]),
                "Geschlossen": bool(k["pruefung"]["geschlossen"]),
                "Hinweise": "; ".join(k["hinweise"])}})
    p = m.parameter
    aus.geomodell(f"Baugrundmodell (Layer-Cake, {p['methode'].upper()})", einheiten, {
        "Verfahren": "Layer-Cake: Einheiten per Schichtfolgen-Korrelation, Flaechen exakt an den Bohrungen",
        "Interpolation": {"idw": "IDW p=2", "tps": "Duennplatten-Spline"}.get(p["methode"], p["methode"]),
        "Raster_m": round(p["raster_m"], 2), "Puffer_m": round(p["puffer_m"], 1),
        "Modellbasis_NHN": round(m.basis, 2), "Lagebezug": f"EPSG:{m.epsg}" if m.epsg else "lokal (ohne Georeferenz)",
        "Bohrungen_im_Modell": ", ".join(b.code for b in m.bohrungen),
        "Nicht_im_Modell": "; ".join(f"{a['code']} ({a['grund']})" for a in m.ausgeschlossen),
        "Quellen": ", ".join(quellen), "Modellierer": f"baugrundmodell {__version__}",
        "Hinweise": "; ".join(m.hinweise)})
    if bohrsaeulen:
        codes = {b.code: b for b in m.bohrungen}
        for d in docs:
            for b in d["boreholes"]:
                vb = codes.get(b["code"])
                if vb is not None and vb.dokument == d["document"]["file"] and abs(vb.x - b["x"]) < 0.5:
                    aus.bohrung(d["document"], b, (vb.x - m.ursprung[0], vb.y - m.ursprung[1]), vb.lage, vb.hoehe)
    aus.schreiben(pfad)
    return {"einheiten": len(einheiten), "bohrungen": len(m.bohrungen)}


def bericht(m: Modell) -> dict:
    """Pruefbericht (JSON): Einheiten, Zuordnung je Bohrung, Ausschluesse, Pruefungen, Vorlage fuer --einheiten."""
    bohr = []
    for bi, (b, ks) in enumerate(zip(m.bohrungen, m.kontakte)):
        zeilen = []
        for j, (e, k) in enumerate(zip(m.einheiten, ks)):
            zeilen.append({"einheit": e.name, "status": k.status, "unterkante_art": k.art,
                           "ok_modell": round(float(m.flaechen[j][bi]), 3),
                           "uk_modell": round(float(m.flaechen[j + 1][bi]), 3)})
        bohr.append({"code": b.code, "dokument": b.dokument, "x": b.x, "y": b.y, "gok": b.gok,
                     "lage": b.lage, "hoehe": b.hoehe,
                     "endteufe_nhn": round(b.ende, 3),
                     "abschnitte": [{"bodenart": a.klasse, "ok": round(a.ok, 3), "uk": round(a.uk, 3)} for a in b.abschnitte],
                     "einheiten": zeilen, "hinweise": b.hinweise})
    return {
        "modellierer": __version__, "epsg": m.epsg, "ursprung": m.ursprung, "parameter": m.parameter,
        "einheiten": [{"name": k["name"], "bodenarten": k["bodenarten"], "farbe": hexfarbe(k["rgb"]),
                       "volumen_m3": round(k["volumen_m3"], 1), "maechtigkeit_max_m": round(k["maechtigkeit_max"], 2),
                       "geschlossen": bool(k["pruefung"]["geschlossen"]), "bohrungen": k["bohrungen"],
                       "hinweise": k["hinweise"]} for k in m.koerper],
        "bohrungen": bohr,
        "ausgeschlossen": m.ausgeschlossen,
        "pruefungen": {"max_abweichung_an_bohrungen_m": round(m.max_abweichung, 4),
                       "alle_koerper_geschlossen": all(k["pruefung"]["geschlossen"] for k in m.koerper),
                       "zensurpunkte": m.zensurpunkte,
                       "netz": {"knoten": int(len(m.punkte)), "dreiecke": int(len(m.dreiecke))}},
        "hinweise": m.hinweise,
        "vorlage_einheiten": [{"name": e.name, "bodenarten": sorted(e.klassen)} for e in m.einheiten],
    }
