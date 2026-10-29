"""Projektzustand der Baugrundmodell-App: Korrekturen des Nutzers, Lage (Koordinaten oder Reihe), Unterlage mit
Kalibrierung, Durchmesser der Bohrsaeulen, Pruefstand und Eincheckungen.

Ohne Oberflaeche testbar; die App (server/, apps/web) ruft nur aendern() und zustand() auf. Das kanonische JSON der
Extraktion bleibt unveraendert: alles, was der Nutzer aendert, liegt hier und wird beim Rechnen auf eine Kopie
angewendet und dort markiert (coord_source, gok_source, geprueft, korrigiert). Warnungen gelten Schichten, die nicht
klassifiziert werden konnten (Bodenart "unklassifiziert"), nicht einer niedrigen Konfidenz. Jede Beschreibung wird
nach Norm gedeutet (services/modeler/baugrundmodell/normen.py); ein Vorschlag wird nur auf Wunsch uebernommen.
Beschreibung: docs/20 (Lage, Pruefung) und docs/21 (Schritt-App, Normen, Kalibrierung).
"""
from __future__ import annotations

import copy
import math
import re
import sys
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path

_MODELLIERER = str(Path(__file__).resolve().parents[1] / "services" / "modeler")
if _MODELLIERER not in sys.path:
    sys.path.insert(0, _MODELLIERER)

from baugrundmodell.ifc4x3 import FARBEN  # noqa: E402,F401  (Farben nach DIN 4023, fuer aeltere Aufrufer)
from baugrundmodell.modell import standard_durchmesser  # noqa: E402
from baugrundmodell.normen import (UNKLASSIFIZIERT, bekannt, deuten, farbinfo, klassen_liste,  # noqa: E402
                                   vorschlag)

LAGE_KOORDINATEN = "koordinaten"          # Lageplan: Rechts-/Hochwert (aus dem PDF, eingetragen oder im Viewer gesetzt)
LAGE_REIHE = "reihe"                      # Laengsschnitt: Bohrungen in einer Reihe, Stationen je Bohrung
SCHRITTE = ("gutachten", "bohrungen", "lage", "einheiten", "modell")


@dataclass
class Einstellungen:
    methode: str = "idw"
    puffer: float | None = None             # None = automatisch (docs/18 §7)
    raster: float | None = None
    basis: float | None = None
    gok_relativ: bool = True                # fehlt die GOK bei allen: 0 m (relativ, markiert)


@dataclass
class Vorbereitung:
    docs: list[dict]                        # Eingabe fuer den Modellierer
    hinweise: list[str] = field(default_factory=list)
    nicht_im_modell: list[dict] = field(default_factory=list)
    lage: dict[str, tuple] = field(default_factory=dict)   # id -> (x, y, Quelle) der Bohrungen mit Lage


@dataclass
class Projekt:
    signatur: str
    name: str = ""
    lage_modus: str = LAGE_KOORDINATEN
    bohrung: dict[str, dict] = field(default_factory=dict)   # id -> {modell, geprueft, gok, x, y, epsg, quelle, durchmesser}
    schicht: dict[str, dict] = field(default_factory=dict)   # "id/k" -> {oben, unten, bodenart, geprueft}
    reihe: dict = field(default_factory=lambda: {"standard": 20.0, "reihenfolge": [], "abstand": {}, "station": {}})
    unterlage: dict | None = None
    punkte: list[dict] = field(default_factory=list)          # freie Punkte auf dem Plan: {id, x, y} (noch ohne Bohrung)
    punkt_zaehler: int = 0
    ursprung: tuple[float, float] | None = None
    erzeugt: bool = False
    auto: bool = True
    vorgabe: list[dict] | None = None
    eincheckungen: list[dict] = field(default_factory=list)
    viewer_nr: int = 0                      # zuletzt angewendetes Viewer-Ereignis (Ereignisse mit laufender Nummer)
    unterlage_zaehler: int = 0
    version: int = 0                        # steigt bei jeder Aenderung (die Oberflaeche erkennt veralteten Stand)
    einstellungen: dict = field(default_factory=lambda: asdict(Einstellungen()))
    durchmesser: float | None = None        # Bohrsaeulen in m; None = automatisch nach Modellgroesse
    ueberhoehung: int = 5
    schritt: str = "bohrungen"              # zuletzt offener Schritt der App
    angelegt: str = ""
    geaendert: str = ""


# ---------------------------------------------------------------- Grundlagen
def natuerlich(code: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", code)]


def de(v: float, stellen: int = 2) -> str:
    """Zahl wie in der Oberflaeche: 5.933.000,25."""
    return f"{float(v):,.{stellen}f}".replace(",", "§").replace(".", ",").replace("§", ".")


def zahl(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f                         # NaN -> None


def _gleich(a, b, tol: float = 1e-6) -> bool:
    a, b = zahl(a), zahl(b)
    return (a is None and b is None) or (a is not None and b is not None and abs(a - b) <= tol)


def jetzt() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def bohrungen(docs: list[dict]) -> list[tuple[str, dict, dict]]:
    """(id, Dokument, Bohrung) in Dokumentreihenfolge; id = 'Dokumentindex:Bohrungsindex'."""
    return [(f"{di}:{bi}", d, b) for di, d in enumerate(docs) for bi, b in enumerate(d["boreholes"])]


def _bohrung(docs: list[dict], bid: str) -> dict:
    for i, _, b in bohrungen(docs):
        if i == bid:
            return b
    raise KeyError(f"Bohrung {bid} gibt es nicht")


def doppelte(docs: list[dict]) -> dict[str, str]:
    """id -> Dokument, in dem derselbe Code schon vorkam (das erste Vorkommen bleibt im Modell)."""
    gesehen: dict[str, str] = {}
    out = {}
    for bid, d, b in bohrungen(docs):
        if b["code"] in gesehen:
            out[bid] = gesehen[b["code"]]
        else:
            gesehen[b["code"]] = d["document"]["file"]
    return out


def bodenarten(docs: list[dict]) -> list[str]:
    """Auswahl fuer die Schichttabelle: Klassen der Normen-Datenbank und alle, die die Extraktion geliefert hat."""
    aus_docs = {ly.get("soil_class") for _, _, b in bohrungen(docs) for ly in b.get("layers") or [] if ly.get("soil_class")}
    norm = [k["klasse"] for k in klassen_liste()]
    return norm + sorted(aus_docs - set(norm))


def bodenart_farbe(klasse: str | None) -> str:
    """Farbe nach DIN 4023 (Normen-Datenbank); unbekannt/unklassifiziert hellgrau."""
    return farbinfo(klasse if bekannt(klasse) else None)["hex"]


def neues_projekt(docs: list[dict], signatur: str) -> Projekt:
    p = Projekt(signatur)
    hat_lage = any(b.get("x") is not None and b.get("y") is not None for _, _, b in bohrungen(docs))
    p.lage_modus = LAGE_KOORDINATEN if hat_lage else LAGE_REIHE
    p.reihe["reihenfolge"] = [bid for bid, _, b in sorted(bohrungen(docs), key=lambda t: natuerlich(t[2]["code"]))]
    p.name = Path(docs[0]["document"]["file"]).stem if len(docs) == 1 else f"{len(docs)} Dokumente"
    p.angelegt = p.geaendert = jetzt()
    return p


def einstellungen(p: Projekt) -> Einstellungen:
    felder = Einstellungen.__dataclass_fields__
    return Einstellungen(**{k: v for k, v in (p.einstellungen or {}).items() if k in felder})


# ---------------------------------------------------------------- wirksame Werte (Extraktion + Korrekturen)
def _basis_modell(bid: str, b: dict, doppelt: dict) -> bool:
    return bool(b.get("layers")) and bid not in doppelt


def wert(p: Projekt, bid: str, b: dict, schluessel: str, doppelt: dict | None = None):
    """Wirksamer Wert einer Bohrung: Korrektur, sonst Extraktion."""
    o = p.bohrung.get(bid, {})
    if schluessel in o:
        return o[schluessel]
    return {"modell": lambda: _basis_modell(bid, b, doppelt or {}), "geprueft": lambda: False,
            "gok": lambda: b.get("gok_nhn"), "x": lambda: b.get("x"), "y": lambda: b.get("y"),
            "epsg": lambda: b.get("crs_epsg"), "quelle": lambda: b.get("coord_source") or "",
            "durchmesser": lambda: None}[schluessel]()


def schicht_wert(p: Projekt, bid: str, k: int, ly: dict, schluessel: str):
    o = p.schicht.get(f"{bid}/{k}", {})
    if schluessel in o:
        return o[schluessel]
    return {"oben": ly["top_depth"], "unten": ly["bottom_depth"], "bodenart": ly.get("soil_class") or UNKLASSIFIZIERT,
            "geprueft": False}[schluessel]


def schicht_geprueft(p: Projekt, bid: str, b: dict, k: int, ly: dict) -> bool:
    return bool(schicht_wert(p, bid, k, ly, "geprueft")) or bool(wert(p, bid, b, "geprueft"))


def schicht_unklassifiziert(p: Projekt, bid: str, k: int, ly: dict) -> bool:
    return schicht_wert(p, bid, k, ly, "bodenart") in (None, "", UNKLASSIFIZIERT)


def schicht_offen(p: Projekt, bid: str, b: dict, k: int, ly: dict) -> bool:
    """Warnung: Schicht nicht klassifiziert und noch nicht geprueft (wer sie prueft, nimmt sie zur Kenntnis)."""
    return schicht_unklassifiziert(p, bid, k, ly) and not schicht_geprueft(p, bid, b, k, ly)


def wirksame_docs(docs: list[dict], p: Projekt) -> list[dict]:
    """Kopie der Extraktion mit allen Korrekturen, markiert. Lage und Modell-Auswahl macht modell_eingabe."""
    neu = copy.deepcopy(docs)
    for bid, d, b in bohrungen(neu):
        o = p.bohrung.get(bid, {})
        if "gok" in o:
            b["gok_nhn"], b["gok_source"] = zahl(o["gok"]), "manuell"
        if any(s in o for s in ("x", "y", "epsg")):
            b["x"], b["y"] = zahl(wert(p, bid, b, "x")), zahl(wert(p, bid, b, "y"))
            epsg = zahl(wert(p, bid, b, "epsg"))
            b["crs_epsg"] = int(epsg) if epsg else None
            b["coord_source"] = o.get("quelle") or "manuell"
        b["geprueft"] = bool(o.get("geprueft", False))
        for k, ly in enumerate(b.get("layers") or []):
            lo = p.schicht.get(f"{bid}/{k}", {})
            korrigiert = any(s in lo for s in ("oben", "unten", "bodenart"))
            if korrigiert:
                ly["konfidenz_extraktion"] = ly.get("confidence")
                ly["top_depth"] = float(lo.get("oben", ly["top_depth"]))
                ly["bottom_depth"] = float(lo.get("unten", ly["bottom_depth"]))
                art = lo.get("bodenart", ly.get("soil_class"))
                ly["soil_class"] = None if art in (None, "", UNKLASSIFIZIERT) else art
                ly["confidence"] = 1.0                    # vom Menschen festgelegt
                ly["korrigiert"] = True
                ly["issues"] = list(ly.get("issues") or []) + ["manuell korrigiert"]
            ly["geprueft"] = bool(lo.get("geprueft", False)) or b["geprueft"]
        if b.get("layers"):
            b["end_depth"] = max(ly["bottom_depth"] for ly in b["layers"])
    return neu


# ---------------------------------------------------------------- Listen fuer die Oberflaeche
def bohrungen_liste(docs: list[dict], p: Projekt) -> list[dict]:
    """Eine Zeile je Bohrung (wirksame Werte, Pruef- und Warnzaehler)."""
    doppelt = doppelte(docs)
    out = []
    for bid, d, b in bohrungen(docs):
        schichten = b.get("layers") or []
        konf = [ly.get("confidence") or 0.0 for ly in schichten]
        hinweise = list(b.get("issues") or [])
        if bid in doppelt:
            hinweise.insert(0, f"doppelt (auch in {doppelt[bid]})")
        modell = bool(wert(p, bid, b, "modell", doppelt))
        gok = zahl(wert(p, bid, b, "gok"))
        out.append({
            "id": bid, "code": b["code"], "dokument": d["document"]["file"],
            "seite": int((b.get("provenance") or [{}])[0].get("page", 0) or 0) + 1,
            "modell": modell, "entfernt": not modell, "geprueft": bool(wert(p, bid, b, "geprueft")),
            "gok": gok, "gok_pdf": b.get("gok_nhn") is not None,
            "gok_quelle": "manuell" if "gok" in p.bohrung.get(bid, {}) else ("PDF" if b.get("gok_nhn") is not None else ""),
            "endteufe": max((zahl(schicht_wert(p, bid, k, ly, "unten")) or 0.0 for k, ly in enumerate(schichten)),
                            default=b.get("end_depth")),
            "x": zahl(wert(p, bid, b, "x")), "y": zahl(wert(p, bid, b, "y")), "epsg": zahl(wert(p, bid, b, "epsg")),
            "lage_aus": wert(p, bid, b, "quelle"),
            "schichten_n": len(schichten),
            "schichten_geprueft": sum(schicht_geprueft(p, bid, b, k, ly) for k, ly in enumerate(schichten)),
            "unklassifiziert": sum(schicht_unklassifiziert(p, bid, k, ly) for k, ly in enumerate(schichten)),
            "offen": sum(schicht_offen(p, bid, b, k, ly) for k, ly in enumerate(schichten)),
            "korrigiert": sum(any(s in p.schicht.get(f"{bid}/{k}", {}) for s in ("oben", "unten", "bodenart"))
                              for k, _ in enumerate(schichten)),
            "konfidenz_min": round(min(konf), 2) if konf else None,
            "grundwasser": ", ".join(f"{g['depth']:.2f} m" for g in b.get("groundwater") or []) or
                           (b.get("groundwater_status") or ""),
            "durchmesser": zahl(wert(p, bid, b, "durchmesser")),
            "doppelt_in": doppelt.get(bid),
            "hinweise": hinweise})
    return out


def schichten_liste(docs: list[dict], p: Projekt, bid: str) -> list[dict]:
    """Schichten einer Bohrung mit Quelle (Seite, Rahmen im PDF) und Deutung nach Norm."""
    b = _bohrung(docs, bid)
    d = next(d for i, d, _ in bohrungen(docs) if i == bid)
    out = []
    for k, ly in enumerate(b.get("layers") or []):
        lo = p.schicht.get(f"{bid}/{k}", {})
        pv = (ly.get("provenance") or [{}])[0]
        art = schicht_wert(p, bid, k, ly, "bodenart")
        norm = deuten(ly.get("description_raw"), None if art == UNKLASSIFIZIERT else art)
        vs = vorschlag(ly) if art == UNKLASSIFIZIERT else None
        out.append({"k": k, "von": float(schicht_wert(p, bid, k, ly, "oben")), "bis": float(schicht_wert(p, bid, k, ly, "unten")),
                    "bodenart": art, "farbe": bodenart_farbe(art),
                    "geprueft": schicht_geprueft(p, bid, b, k, ly),
                    "korrigiert": any(s in lo for s in ("oben", "unten", "bodenart")),
                    "unklassifiziert": art == UNKLASSIFIZIERT, "offen": schicht_offen(p, bid, b, k, ly),
                    "konfidenz": ly.get("confidence"), "beschreibung": ly.get("description_raw") or "",
                    "hinweise": list(ly.get("issues") or []),
                    "quelle": {"dokument": d["document"]["file"], "seite": int(pv.get("page") or 0) + 1,
                               "bbox": pv.get("bbox"), "methode": pv.get("method")},
                    "norm": {"benennung": norm.benennung, "din4023": norm.din4023, "iso14688": norm.iso14688,
                             "bodengruppe": norm.bodengruppe, "konsistenz": norm.konsistenz, "lagerung": norm.lagerung,
                             "kalk": norm.kalk, "feuchte": norm.feuchte, "bodenfarbe": norm.bodenfarbe,
                             "klasse": norm.klasse, "farbe": norm.farbe, "farbname": norm.farbname,
                             "sicher": norm.sicher, "hinweise": norm.hinweise},
                    "vorschlag": vs})
    return out


# ---------------------------------------------------------------- Aenderungen
def _bohrung_setzen(docs: list[dict], p: Projekt, bid: str, feld: str, w) -> bool:
    """Ein Feld einer Bohrung setzen; gleich dem PDF-Wert (oder None) -> Korrektur entfaellt."""
    b = _bohrung(docs, bid)
    o = p.bohrung.setdefault(bid, {})
    vorher = dict(o)
    if feld in ("modell", "geprueft"):
        ursprung = _basis_modell(bid, b, doppelte(docs)) if feld == "modell" else False
        if bool(w) == ursprung:
            o.pop(feld, None)
        else:
            o[feld] = bool(w)
    elif feld == "gok":
        if w is None or _gleich(w, b.get("gok_nhn")):
            o.pop("gok", None)
        else:
            o["gok"] = zahl(w)
    elif feld in ("x", "y", "epsg"):
        neu = {s: zahl(o.get(s, b.get({"x": "x", "y": "y", "epsg": "crs_epsg"}[s]))) for s in ("x", "y", "epsg")}
        neu[feld] = zahl(w)
        if all(_gleich(neu[s], b.get({"x": "x", "y": "y", "epsg": "crs_epsg"}[s])) for s in neu):
            for s in ("x", "y", "epsg", "quelle"):
                o.pop(s, None)
        else:
            o.update(neu, quelle="manuell (Tabelle)")
    elif feld == "durchmesser":
        d = zahl(w)
        if d is None or d <= 0:
            o.pop("durchmesser", None)
        else:
            o["durchmesser"] = round(d, 3)
    else:
        raise ValueError(f"unbekanntes Feld {feld}")
    if not o:
        p.bohrung.pop(bid, None)
    return o != vorher


def _schicht_setzen(docs: list[dict], p: Projekt, bid: str, k: int, feld: str, w) -> bool:
    b = _bohrung(docs, bid)
    ly = b["layers"][k]
    schl = f"{bid}/{k}"
    o = p.schicht.setdefault(schl, {})
    vorher = dict(o)
    war_korrigiert = any(s in o for s in ("oben", "unten", "bodenart"))
    if feld in ("oben", "unten"):
        ursprung = ly["top_depth"] if feld == "oben" else ly["bottom_depth"]
        if w is None or _gleich(w, ursprung):
            o.pop(feld, None)
        else:
            o[feld] = zahl(w)
    elif feld == "bodenart":
        art = w or UNKLASSIFIZIERT
        if art == (ly.get("soil_class") or UNKLASSIFIZIERT):
            o.pop("bodenart", None)
        else:
            o["bodenart"] = art
    elif feld == "geprueft":
        o["geprueft"] = bool(w)
        if not w and wert(p, bid, b, "geprueft"):
            # Haken an einer Schicht weg, die Bohrung war als ganze geprueft: die anderen Schichten bleiben geprueft
            p.bohrung.setdefault(bid, {})["geprueft"] = False
            for j, _ in enumerate(b["layers"]):
                if j != k:
                    p.schicht.setdefault(f"{bid}/{j}", {}).setdefault("geprueft", True)
    else:
        raise ValueError(f"unbekanntes Feld {feld}")
    if feld != "geprueft" and not war_korrigiert and any(s in o for s in ("oben", "unten", "bodenart")):
        o["geprueft"] = True                              # wer korrigiert, hat die Schicht geprueft
    if not o:
        p.schicht.pop(schl, None)
    return o != vorher


def alle_schichten_pruefen(docs: list[dict], p: Projekt, bid: str, geprueft: bool = True) -> None:
    b = _bohrung(docs, bid)
    for k, _ in enumerate(b.get("layers") or []):
        p.schicht.setdefault(f"{bid}/{k}", {})["geprueft"] = geprueft
    if not geprueft:
        p.bohrung.setdefault(bid, {})["geprueft"] = False


def alle_pruefen(docs: list[dict], p: Projekt, geprueft: bool = True) -> int:
    """Alle Schichten aller Bohrungen im Modell als geprueft markieren (oder zuruecknehmen); Anzahl Bohrungen."""
    doppelt = doppelte(docs)
    n = 0
    for bid, _, b in bohrungen(docs):
        if not wert(p, bid, b, "modell", doppelt):
            continue
        alle_schichten_pruefen(docs, p, bid, geprueft)
        _bohrung_setzen(docs, p, bid, "geprueft", geprueft)
        n += 1
    return n


def _gok_aus_pdf(docs: list[dict] | None, bid: str) -> bool:
    if docs is None:
        return False
    try:
        return _bohrung(docs, bid).get("gok_nhn") is not None
    except KeyError:
        return False


# ---------------------------------------------------------------- Punkte auf dem Plan (setzen, zuordnen, loeschen)
LAGE_VOM_PLAN = ("Plan (kalibriert)", "manuell (Viewer)")


def _plan_gesperrt(p: Projekt) -> dict:
    """Punkte nur auf einem kalibrierten und gesperrten Lageplan (sonst sind ihre Koordinaten bedeutungslos)."""
    u = p.unterlage or {}
    kal = u.get("kalibrierung") or {}
    if u.get("art", "plan") != "plan" or not kal.get("bezug") or not kal.get("gesperrt"):
        raise ValueError("Punkte nur auf einem kalibrierten und gesperrten Lageplan (🔒)")
    return kal


def _punkt(p: Projekt, pid) -> dict:
    for pt in p.punkte:
        if pt["id"] == pid:
            return pt
    raise ValueError(f"Punkt {pid} gibt es nicht")


def _lage_vom_plan(p: Projekt, bid: str, x: float, y: float, kal: dict) -> bool:
    """Lage einer Bohrung aus dem Plan; True = eine gesetzte Lage wurde ersetzt."""
    o = p.bohrung.setdefault(bid, {})
    ersetzt = o.get("quelle") in LAGE_VOM_PLAN
    o.update(x=round(float(x), 3), y=round(float(y), 3), quelle="Plan (kalibriert)")
    if kal.get("epsg"):
        o["epsg"] = int(kal["epsg"])
    return ersetzt


def _lage_weg(p: Projekt, bid: str) -> tuple[float, float]:
    """Gesetzte Lage (Plan, Viewer, Tabelle) einer Bohrung entfernen; zurueck kommt sie als (x, y)."""
    o = p.bohrung.get(bid, {})
    if o.get("x") is None or o.get("y") is None:
        raise ValueError("keine gesetzte Lage")
    xy = (float(o["x"]), float(o["y"]))
    for s in ("x", "y", "epsg", "quelle"):
        o.pop(s, None)
    if not o:
        p.bohrung.pop(bid, None)
    return xy


def _neuer_punkt(p: Projekt, x: float, y: float) -> str:
    p.punkt_zaehler += 1
    pid = f"P{p.punkt_zaehler}"
    p.punkte.append({"id": pid, "x": round(float(x), 3), "y": round(float(y), 3)})
    return pid


def aendern(docs: list[dict], p: Projekt, op: dict) -> str:
    """Eine Aenderung aus der App anwenden. Rueckgabe: kurze Meldung; ValueError bei ungueltiger Eingabe."""
    art = op.get("op")
    codes = {bid: b["code"] for bid, _, b in bohrungen(docs)}
    bid = op.get("id")
    if bid is not None and bid not in codes:
        raise ValueError(f"Bohrung {bid} gibt es nicht")
    code = codes.get(bid, "")
    meldung = ""
    if art == "bohrung":
        _bohrung_setzen(docs, p, bid, op["feld"], op.get("wert"))
        meldung = f"{code}: {op['feld']} übernommen"
    elif art in ("entfernen", "wiederherstellen"):
        _bohrung_setzen(docs, p, bid, "modell", art == "wiederherstellen")
        meldung = f"{code} {'aus dem Modell entfernt' if art == 'entfernen' else 'wieder im Modell'}"
    elif art == "schicht":
        _schicht_setzen(docs, p, bid, int(op["k"]), op["feld"], op.get("wert"))
        meldung = f"{code}, Schicht {int(op['k']) + 1}: {op['feld']} übernommen"
    elif art == "vorschlag":                              # Deutung nach Norm fuer eine unklassifizierte Schicht
        ly = _bohrung(docs, bid)["layers"][int(op["k"])]
        if not schicht_unklassifiziert(p, bid, int(op["k"]), ly):
            raise ValueError("Schicht ist schon klassifiziert")
        vs = vorschlag(ly)
        if not vs:
            raise ValueError("kein Vorschlag nach Norm")
        _schicht_setzen(docs, p, bid, int(op["k"]), "bodenart", vs["klasse"])
        meldung = f"{code}, Schicht {int(op['k']) + 1}: {vs['klasse']} übernommen ({vs['din4023']})"
    elif art == "bohrung_pruefen":
        alle_schichten_pruefen(docs, p, bid, bool(op.get("wert", True)))
        _bohrung_setzen(docs, p, bid, "geprueft", bool(op.get("wert", True)))
        meldung = f"{code}: {'alle Schichten geprüft' if op.get('wert', True) else 'Prüfung zurückgenommen'}"
    elif art == "alle_pruefen":
        n = alle_pruefen(docs, p, bool(op.get("wert", True)))
        meldung = f"{n} Bohrungen {'vollständig geprüft' if op.get('wert', True) else 'Prüfung zurückgenommen'}"
    elif art == "lage_modus":
        if op["wert"] not in (LAGE_KOORDINATEN, LAGE_REIHE):
            raise ValueError("Lage: koordinaten oder reihe")
        p.lage_modus = op["wert"]
    elif art == "reihe":
        reihe_aendern(docs, p, op)
        meldung = "Reihe übernommen"
    elif art == "lage":                                  # im Viewer auf den Plan gezogen (nur x/y)
        kal = (p.unterlage or {}).get("kalibrierung") or {}
        o = p.bohrung.setdefault(bid, {})
        o.update(x=float(op["x"]), y=float(op["y"]), quelle="Plan (kalibriert)" if kal else "manuell (Viewer)")
        if kal.get("epsg"):                               # sonst bleibt das System der Bohrung (PDF/Tabelle)
            o["epsg"] = int(kal["epsg"])
        meldung = f"{code}: Lage R {de(op['x'])} · H {de(op['y'])}"
    elif art == "punkt":                                 # Klick in den gesperrten Plan: Bohrung setzen oder freier Punkt
        kal = _plan_gesperrt(p)
        x, y = zahl(op.get("x")), zahl(op.get("y"))
        if x is None or y is None:
            raise ValueError("Punkt ohne Koordinate")
        ziel = op.get("bohrung")
        if ziel:
            if ziel not in codes:
                raise ValueError(f"Bohrung {ziel} gibt es nicht")
            ersetzt = _lage_vom_plan(p, ziel, x, y, kal)
            meldung = f"{codes[ziel]}: Lage R {de(x)} · H {de(y)}{' (ersetzt)' if ersetzt else ''}"
        else:
            pid = _neuer_punkt(p, x, y)
            meldung = f"Punkt {pid}: R {de(x)} · H {de(y)} – einer Bohrung zuordnen"
    elif art == "punkt_zuordnen":                        # freier Punkt -> Lage der Bohrung
        kal = _plan_gesperrt(p)
        pt = _punkt(p, op.get("punkt"))
        ziel = op.get("bohrung")
        if ziel not in codes:
            raise ValueError(f"Bohrung {ziel} gibt es nicht")
        p.punkte.remove(pt)
        ersetzt = _lage_vom_plan(p, ziel, pt["x"], pt["y"], kal)
        meldung = f"{pt['id']} → {codes[ziel]}{' (Lage ersetzt)' if ersetzt else ''}"
    elif art == "punkt_loeschen":
        pt = _punkt(p, op.get("punkt"))
        p.punkte.remove(pt)
        meldung = f"Punkt {pt['id']} gelöscht"
    elif art == "lage_entfernen":                        # gesetzte Lage weg: Koordinaten aus dem PDF oder ohne Lage
        try:
            _lage_weg(p, bid)
        except ValueError:
            raise ValueError(f"{code}: keine gesetzte Lage") from None
        b = _bohrung(docs, bid)
        meldung = f"{code}: Lage entfernt – {'wieder Koordinaten aus dem PDF' if b.get('x') is not None else 'wieder ohne Lage'}"
    elif art == "lage_loesen":                           # Zuordnung loesen: die Lage bleibt als freier Punkt
        try:
            x, y = _lage_weg(p, bid)
        except ValueError:
            raise ValueError(f"{code}: keine gesetzte Lage") from None
        meldung = f"{code}: Zuordnung gelöst – Punkt {_neuer_punkt(p, x, y)}"
    elif art == "lage_umhaengen":                        # Lage einer Bohrung an eine andere geben
        kal = _plan_gesperrt(p)
        ziel = op.get("nach")
        if ziel not in codes or ziel == bid:
            raise ValueError("Ziel-Bohrung ungültig")
        try:
            x, y = _lage_weg(p, bid)
        except ValueError:
            raise ValueError(f"{code}: keine gesetzte Lage") from None
        ersetzt = _lage_vom_plan(p, ziel, x, y, kal)
        meldung = f"Lage von {code} → {codes[ziel]}{' (ersetzt)' if ersetzt else ''}"
    elif art == "station":
        p.reihe["station"][bid] = float(op["station"])
        p.reihe["abstand"].pop(bid, None)
        meldung = f"{code}: Station {de(op['station'])} m"
    elif art == "gok":                                   # Ansatzhoehe im Schnitt gezogen: nur ohne GOK aus dem PDF
        if _gok_aus_pdf(docs, bid):
            raise ValueError(f"{code}: GOK steht im PDF – Höhe nur in der Tabelle änderbar")
        p.bohrung.setdefault(bid, {})["gok"] = float(op["gok"])
        meldung = f"{code}: GOK {de(op['gok'])} m NHN"
    elif art == "geprueft":
        _bohrung_setzen(docs, p, bid, "geprueft", bool(op["wert"]))
        meldung = f"{code}: {'als geprüft markiert' if op['wert'] else 'Prüfung zurückgenommen'}"
    elif art == "kalibrierung":
        if p.unterlage is None:
            raise ValueError("keine Unterlage")
        p.unterlage["kalibrierung"] = kalibrierung_pruefen(op.get("wert"), p.unterlage.get("art", "plan"))
        meldung = "Kalibrierung übernommen" if op.get("wert") else "Kalibrierung zurückgesetzt"
    elif art == "einstellungen":
        felder = Einstellungen.__dataclass_fields__
        neu = {k: v for k, v in op.items() if k in felder}
        if neu.get("methode", "idw") not in ("idw", "tps"):
            raise ValueError("Interpolation: idw oder tps")
        p.einstellungen = {**p.einstellungen, **neu}
    elif art == "durchmesser":
        d = zahl(op.get("wert"))
        p.durchmesser = None if d is None or d <= 0 else round(d, 3)
    elif art == "ueberhoehung":
        p.ueberhoehung = int(op["wert"])
    elif art == "vorgabe":
        w = op.get("wert")
        p.vorgabe = None if not w else [{"name": str(v["name"]).strip(),
                                         "bodenarten": [str(t).strip() for t in v.get("bodenarten") or [] if str(t).strip()]}
                                        for v in w if str(v.get("name") or "").strip()]
    elif art == "erzeugen":
        p.erzeugt = True
    elif art == "auto":
        p.auto = bool(op["wert"])
    elif art == "schritt":
        if op["wert"] not in SCHRITTE:
            raise ValueError("unbekannter Schritt")
        p.schritt = op["wert"]
        return ""                                         # kein neuer Stand
    else:
        raise ValueError(f"unbekannte Änderung {art}")
    p.version += 1
    p.geaendert = jetzt()
    return meldung


# ---------------------------------------------------------------- Reihe (Laengsschnitt)
def _reihenfolge(docs: list[dict], p: Projekt) -> list[str]:
    alle = [bid for bid, _, _ in bohrungen(docs)]
    bekannt_ = [bid for bid in p.reihe["reihenfolge"] if bid in alle]
    return bekannt_ + [bid for bid in alle if bid not in bekannt_]


def stationen(docs: list[dict], p: Projekt, ids: list[str] | None = None) -> dict[str, tuple[float, str]]:
    """Station je Bohrung entlang der Reihe: im Schnitt gesetzt (absolut) > Abstand zum Vorgaenger > Standardabstand."""
    reihe = [bid for bid in _reihenfolge(docs, p) if ids is None or bid in ids]
    out: dict[str, tuple[float, str]] = {}
    vorher = None
    for bid in reihe:
        if bid in p.reihe["station"]:
            s, q = float(p.reihe["station"][bid]), "Schnitt"
        elif vorher is None:
            s, q = 0.0, "Start"
        elif bid in p.reihe["abstand"]:
            s, q = vorher + float(p.reihe["abstand"][bid]), "manuell"
        else:
            s, q = vorher + float(p.reihe["standard"]), "Standard"
        out[bid] = (s, q)
        vorher = s
    return out


def reihe_liste(docs: list[dict], p: Projekt, ids: list[str] | None = None) -> list[dict]:
    if ids is None:
        doppelt = doppelte(docs)
        ids = [bid for bid, _, b in bohrungen(docs) if wert(p, bid, b, "modell", doppelt)]
    st = stationen(docs, p, ids)
    codes = {bid: b["code"] for bid, _, b in bohrungen(docs)}
    out, vorher = [], None
    for nr, (bid, (s, q)) in enumerate(st.items(), start=1):
        out.append({"id": bid, "nr": nr, "code": codes[bid], "abstand": None if vorher is None else round(s - vorher, 3),
                    "station": round(s, 3), "quelle": q,
                    "quelle_text": {"Schnitt": "im Schnitt gesetzt", "manuell": "Abstand manuell",
                                    "Standard": "Standardabstand", "Start": "Anfang"}[q]})
        vorher = s
    return out


def reihe_aendern(docs: list[dict], p: Projekt, op: dict) -> None:
    """op: standard (m), reihenfolge (ids), abstand {id: m|None}, station {id: m|None}."""
    if op.get("standard") is not None:
        s = zahl(op["standard"])
        if s is None or s <= 0:
            raise ValueError("Standardabstand muss positiv sein")
        p.reihe["standard"] = s
    if op.get("reihenfolge"):
        alle = [bid for bid, _, _ in bohrungen(docs)]
        neu = [bid for bid in op["reihenfolge"] if bid in alle]
        p.reihe["reihenfolge"] = neu + [bid for bid in _reihenfolge(docs, p) if bid not in neu]
    for bid, a in (op.get("abstand") or {}).items():
        p.reihe["station"].pop(bid, None)
        if zahl(a) is None:
            p.reihe["abstand"].pop(bid, None)
        else:
            p.reihe["abstand"][bid] = zahl(a)
    for bid, s in (op.get("station") or {}).items():
        if zahl(s) is None:
            p.reihe["station"].pop(bid, None)
        else:
            p.reihe["station"][bid] = zahl(s)
            p.reihe["abstand"].pop(bid, None)


# ---------------------------------------------------------------- Kalibrierung der Unterlage
def _strecke_px(s: dict) -> float:
    return math.hypot(float(s["u2"]) - float(s["u1"]), float(s["v2"]) - float(s["v1"]))


def kalibrierung_pruefen(k: dict | None, art: str) -> dict | None:
    """Neue Kalibrierung (docs/21 §4): Massstab aus einer gemessenen Strecke (zwei Punkte + wahre Laenge) oder aus
    der Angabe 1:n, Bezugspunkt im Bild mit Koordinate, Drehung (Plan) bzw. Hoehenmassstab (Schnitt), Sperre.

    {"massstab": {"u1", "v1", "u2", "v2", "meter"} | {"n": 500},
     "hoehe": {"u1", "v1", "u2", "v2", "meter"} | {"n": 100} | None   (nur Schnitt; None = wie die Laenge),
     "bezug": {"u", "v", "x", "y"}, "drehung": Grad (Plan, gegen den Uhrzeigersinn), "epsg", "gesperrt"}
    """
    if not k:
        return None
    if "punkte" in k and "massstab" not in k:                    # alte Kalibrierung (zwei Passpunkte)
        return kalibrierung_aus_punkten(k["punkte"], art, k.get("epsg"))
    aus: dict = {"gesperrt": bool(k.get("gesperrt"))}
    for name in ("massstab", "hoehe"):
        m = k.get(name)
        if not m:
            continue
        if "n" in m:
            n = zahl(m["n"])
            if not n or n <= 0:
                raise ValueError("Maßstab 1:n mit positivem n")
            aus[name] = {"n": n}
        else:
            werte = {s: zahl(m.get(s)) for s in ("u1", "v1", "u2", "v2", "meter")}
            if any(v is None for v in werte.values()) or werte["meter"] <= 0:
                raise ValueError("Strecke: zwei Bildpunkte und die wahre Länge in m")
            if _strecke_px(werte) < 10:
                raise ValueError("Strecke zu kurz: Punkte weiter auseinander setzen")
            aus[name] = werte
    if "massstab" not in aus:
        raise ValueError("Maßstab fehlt: Strecke messen oder 1:n eingeben")
    b = k.get("bezug") or {}
    bezug = {s: zahl(b.get(s)) for s in ("u", "v", "x", "y")}
    if any(v is None for v in bezug.values()):
        raise ValueError("Bezugspunkt: Bildpunkt und Koordinate eintragen")
    aus["bezug"] = bezug
    aus["drehung"] = float(zahl(k.get("drehung")) or 0.0) if art == "plan" else 0.0
    aus["epsg"] = int(k["epsg"]) if art == "plan" and zahl(k.get("epsg")) else None
    return aus


def meter_je_pixel(m: dict, mm_pro_px: float) -> float:
    """Massstab einer Kalibrierung in m je Bildpixel: aus der Strecke oder aus 1:n und dem Papiermass des Bilds."""
    if "n" in m:
        return float(m["n"]) * mm_pro_px / 1000.0
    return float(m["meter"]) / _strecke_px(m)


def bild_zu_welt(kal: dict, art: str, mm_pro_px: float, u: float, v: float) -> tuple[float, float]:
    """Bildpixel (u nach rechts, v nach unten) -> Welt: Plan (Rechtswert, Hochwert), Schnitt (Station, Hoehe NHN).
    Gleiche Formel wie apps/web/src/lage.ts (abbildung)."""
    s = meter_je_pixel(kal["massstab"], mm_pro_px)
    b = kal["bezug"]
    du, dv = u - b["u"], v - b["v"]
    if art == "plan":
        t = -math.radians(kal.get("drehung") or 0.0)            # Plan gegen Gitternord gedreht: Welt dreht zurueck
        a, c = du * s, -dv * s
        return b["x"] + a * math.cos(t) - c * math.sin(t), b["y"] + a * math.sin(t) + c * math.cos(t)
    sh = meter_je_pixel(kal["hoehe"], mm_pro_px) if kal.get("hoehe") else s
    return b["x"] + du * s, b["y"] - dv * sh


def kalibrierung_aus_punkten(punkte: list, art: str, epsg=None) -> dict:
    """Alte Kalibrierung (zwei Passpunkte u, v, x, y) in die neue Form: Strecke, Bezug = Punkt 1, Drehung."""
    p1, p2 = ({"u": q[0], "v": q[1], "x": q[2], "y": q[3]} if isinstance(q, (list, tuple)) else q for q in punkte[:2])
    if art == "plan":
        meter = math.hypot(p2["x"] - p1["x"], p2["y"] - p1["y"])
        bild = math.atan2(-(p2["v"] - p1["v"]), p2["u"] - p1["u"])
        welt = math.atan2(p2["y"] - p1["y"], p2["x"] - p1["x"])
        return {"massstab": {"u1": p1["u"], "v1": p1["v"], "u2": p2["u"], "v2": p2["v"], "meter": meter},
                "bezug": {"u": p1["u"], "v": p1["v"], "x": p1["x"], "y": p1["y"]},
                "drehung": round(math.degrees(bild - welt), 6), "epsg": epsg, "gesperrt": False}
    return {"massstab": {"u1": p1["u"], "v1": 0.0, "u2": p2["u"], "v2": 0.0, "meter": abs(p2["x"] - p1["x"])},
            "hoehe": {"u1": 0.0, "v1": p1["v"], "u2": 0.0, "v2": p2["v"], "meter": abs(p2["y"] - p1["y"])},
            "bezug": {"u": p1["u"], "v": p1["v"], "x": p1["x"], "y": p1["y"]}, "drehung": 0.0, "epsg": None,
            "gesperrt": False}


# ---------------------------------------------------------------- Eingabe fuer den Modellierer
def modell_eingabe(docs: list[dict], p: Projekt, e: Einstellungen | None = None) -> Vorbereitung:
    """Korrekturen anwenden, Auswahl, GOK-Regel und Lage nach Modus; alles Angenommene als Hinweis."""
    e = e or einstellungen(p)
    neu = wirksame_docs(docs, p)
    doppelt = doppelte(docs)
    hinweise: list[str] = []
    raus: list[dict] = []
    gewaehlt: list[tuple[str, dict]] = []
    for bid, d, b in bohrungen(neu):
        if not wert(p, bid, b, "modell", doppelt):
            raus.append({"id": bid, "code": b["code"], "dokument": d["document"]["file"],
                         "grund": f"doppelt (auch in {doppelt[bid]})" if bid in doppelt and "modell" not in p.bohrung.get(bid, {})
                         else ("keine Schichten" if not b.get("layers") else "entfernt")})
            b["_raus"] = True
        else:
            gewaehlt.append((bid, b))
    for d in neu:
        d["boreholes"] = [b for b in d["boreholes"] if not b.pop("_raus", False)]

    ohne_gok = [b for _, b in gewaehlt if b.get("gok_nhn") is None]
    if ohne_gok and e.gok_relativ and len(ohne_gok) == len(gewaehlt):
        for b in ohne_gok:
            b["gok_nhn"], b["gok_source"] = 0.0, "relativ"
        hinweise.append("Keine Ansatzhoehen (GOK) im PDF: Hoehen relativ, Gelaende = 0 m.")
    elif ohne_gok:
        hinweise.append(f"{len(ohne_gok)} Bohrungen ohne GOK bleiben draussen (GOK in der Tabelle eintragen).")

    lage: dict[str, tuple] = {}
    if p.lage_modus == LAGE_REIHE:
        reihe_ids = [bid for bid, b in gewaehlt if b.get("gok_nhn") is not None]
        st = stationen(docs, p, reihe_ids)
        nur_standard = all(q in ("Start", "Standard") for _, q in st.values())
        for bid, b in gewaehlt:
            if bid not in st:
                continue
            s, q = st[bid]
            quelle = ("schematisch" if nur_standard or q == "Standard" else
                      "Reihe (Station im Schnitt gesetzt)" if q == "Schnitt" else "Reihe (Abstand manuell)")
            b["x"], b["y"], b["crs_epsg"], b["coord_source"] = s, 0.0, None, quelle
            lage[bid] = (s, 0.0, quelle)
        if nur_standard:
            hinweise.append(f"Bohrungen in einer Reihe mit Standardabstand {p.reihe['standard']:g} m – Abstaende "
                            "nicht vermessen, nur zur Anschauung (Abstaende eintragen oder im Schnitt setzen).")
        else:
            hinweise.append("Bohrungen in einer Reihe (Laengsschnitt): Abstaende gesetzt, Querlage unbekannt.")
    else:
        for bid, b in gewaehlt:
            if b.get("x") is not None and b.get("y") is not None:
                lage[bid] = (float(b["x"]), float(b["y"]), b.get("coord_source") or "PDF")
        ohne = sum(1 for bid, b in gewaehlt if bid not in lage)
        if ohne:
            hinweise.append(f"{ohne} Bohrungen ohne Koordinaten bleiben draussen (eintragen, im Viewer auf den Plan "
                            "setzen oder Lage 'Reihe' waehlen).")
    return Vorbereitung(neu, hinweise, raus, lage)


def ursprung(p: Projekt, vorb: Vorbereitung) -> tuple[float, float]:
    """Fester lokaler Nullpunkt des Projekts: verschiebt sich nur, wenn die Bohrungen weit davon entfernt liegen.
    Hat noch keine Bohrung eine Lage, gilt der Bezugspunkt eines kalibrierten Lageplans: sonst laege der Plan
    Millionen Meter vom Nullpunkt der Szene (Gleitkomma der Grafikkarte, docs/16 M31)."""
    if not vorb.lage:
        kal = (p.unterlage or {}).get("kalibrierung") or {}
        bezug = kal.get("bezug") if (p.unterlage or {}).get("art", "plan") == "plan" else None
        if p.lage_modus == LAGE_KOORDINATEN and bezug:
            mitte = (float(bezug["x"]), float(bezug["y"]))
            if p.ursprung is None or math.hypot(mitte[0] - p.ursprung[0], mitte[1] - p.ursprung[1]) > 20000:
                p.ursprung = (round(mitte[0], -2), round(mitte[1], -2))
        return p.ursprung or (0.0, 0.0)
    xs = [v[0] for v in vorb.lage.values()]
    ys = [v[1] for v in vorb.lage.values()]
    mitte = (sum(xs) / len(xs), sum(ys) / len(ys))
    if p.ursprung is None or math.hypot(mitte[0] - p.ursprung[0], mitte[1] - p.ursprung[1]) > 20000:
        p.ursprung = (round(mitte[0], -2), round(mitte[1], -2))
    return p.ursprung


def durchmesser_auto(vorb: Vorbereitung) -> float:
    """Automatischer Saeulendurchmesser wie im Modellierer (Darstellung nach Modellgroesse)."""
    if not vorb.lage:
        return standard_durchmesser(20.0)
    xs = [v[0] for v in vorb.lage.values()]
    ys = [v[1] for v in vorb.lage.values()]
    return standard_durchmesser(max(max(xs) - min(xs), max(ys) - min(ys), 20.0))


def durchmesser_je_code(docs: list[dict], p: Projekt) -> dict[str, float]:
    return {b["code"]: float(p.bohrung[bid]["durchmesser"]) for bid, _, b in bohrungen(docs)
            if p.bohrung.get(bid, {}).get("durchmesser")}


# ---------------------------------------------------------------- Viewer
def viewer_bohrungen(docs: list[dict], p: Projekt, vorb: Vorbereitung, bericht: dict | None) -> list[dict]:
    """Stecknadeln fuer den Viewer: alle Bohrungen im Modell, mit Lage oder (ohne) zum Platzieren."""
    doppelt = doppelte(docs)
    im_modell = {x["code"] for x in (bericht or {}).get("bohrungen", [])}
    raus = {a["code"]: a["grund"] for a in (bericht or {}).get("ausgeschlossen", [])}
    ohne_gok_raus = any("ohne GOK bleiben draussen" in h for h in vorb.hinweise)
    wirksam = {bid: b for bid, _, b in bohrungen(wirksame_docs(docs, p))}
    auto = p.durchmesser or durchmesser_auto(vorb)
    out = []
    for bid, _, b0 in bohrungen(docs):
        if not wert(p, bid, b0, "modell", doppelt):
            continue
        b = wirksam[bid]
        schichten = b.get("layers") or []
        konf = [ly.get("confidence") or 0.0 for ly in schichten]
        x, y, quelle = vorb.lage.get(bid, (None, None, ""))
        gok = b.get("gok_nhn")
        if bericht is None:                               # vor dem Erzeugen: was ins Modell kaeme
            drin = bid in vorb.lage and (gok is not None or not ohne_gok_raus)
            grund = "" if drin else ("ohne Lage" if bid not in vorb.lage else "ohne GOK")
        else:
            drin, grund = b["code"] in im_modell, raus.get(b["code"], "")
        offen = sum(not ly.get("soil_class") and not ly.get("geprueft") for ly in schichten)
        out.append({"id": bid, "code": b["code"], "x": x, "y": y, "quelle": quelle,
                    "gok": 0.0 if gok is None else float(gok), "gok_bekannt": gok is not None,
                    "gok_pdf": b0.get("gok_nhn") is not None,
                    "ende": float(b.get("end_depth") or (schichten[-1]["bottom_depth"] if schichten else 0.0)),
                    "geprueft": bool(b.get("geprueft")),
                    "schichten_geprueft": sum(bool(ly.get("geprueft")) for ly in schichten), "schichten_n": len(schichten),
                    "konfidenz": round(min(konf), 2) if konf else None,
                    "unklassifiziert": sum(not ly.get("soil_class") for ly in schichten), "offen": offen,
                    "durchmesser": float(p.bohrung.get(bid, {}).get("durchmesser") or auto),
                    "im_modell": drin, "grund": grund,
                    # je Schicht: Tiefe oben/unten, Farbe, Bodenart, Konfidenz, geprueft
                    "schichten": [[float(ly["top_depth"]), float(ly["bottom_depth"]), bodenart_farbe(ly.get("soil_class")),
                                   ly.get("soil_class") or UNKLASSIFIZIERT, round(float(ly.get("confidence") or 0.0), 2),
                                   bool(ly.get("geprueft"))] for ly in schichten]})
    return out


def speichern(p: Projekt) -> dict:
    """Projektstand als JSON (Korrekturen, Lage, Pruefung, Eincheckungen) - die Extraktion bleibt eigene Datei."""
    return {"format": "geo_agent-projekt/2", **asdict(p)}


def laden(d: dict) -> Projekt:
    werte = {k: v for k, v in d.items() if k in Projekt.__dataclass_fields__}
    p = Projekt(**werte)
    if p.ursprung is not None:
        p.ursprung = (float(p.ursprung[0]), float(p.ursprung[1]))
    u = p.unterlage or {}
    if u.get("kalibrierung") and "punkte" in u["kalibrierung"]:           # Projekt aus App v2 (zwei Passpunkte)
        u["kalibrierung"] = kalibrierung_aus_punkten(u["kalibrierung"]["punkte"], u.get("art", "plan"),
                                                     u["kalibrierung"].get("epsg"))
    return p


def ereignis_anwenden(p: Projekt, ereignis: dict | None, docs: list[dict] | None = None) -> bool:
    """Ereignis aus dem Viewer mit laufender Nummer 'nr'; jedes nur einmal. True = Projekt geaendert.
    Mit docs werden die Regeln geprueft (GOK aus dem PDF ist im Schnitt nicht verschiebbar)."""
    if not ereignis or int(ereignis.get("nr", 0)) <= p.viewer_nr:
        return False
    if ereignis.get("projekt") not in (None, "", p.signatur):          # Ereignis eines anderen Projekts
        return False
    p.viewer_nr = int(ereignis["nr"])
    typ = ereignis.get("typ")
    if typ == "gok" and _gok_aus_pdf(docs, ereignis["id"]):
        return False
    if typ == "lage":
        kal = (p.unterlage or {}).get("kalibrierung") or {}
        o = p.bohrung.setdefault(ereignis["id"], {})
        o.update(x=float(ereignis["x"]), y=float(ereignis["y"]),
                 quelle="Plan (kalibriert)" if kal else "manuell (Viewer)")
        if kal.get("epsg"):
            o["epsg"] = int(kal["epsg"])
    elif typ == "station":
        p.reihe["station"][ereignis["id"]] = float(ereignis["station"])
        p.reihe["abstand"].pop(ereignis["id"], None)
    elif typ == "gok":
        p.bohrung.setdefault(ereignis["id"], {})["gok"] = float(ereignis["gok"])
    elif typ == "kalibrierung" and p.unterlage is not None:
        wert_ = ereignis.get("wert")
        if wert_ is None and "punkte" in ereignis:
            wert_ = {"punkte": ereignis["punkte"], "epsg": ereignis.get("epsg")}
        p.unterlage["kalibrierung"] = kalibrierung_pruefen(wert_, p.unterlage.get("art", "plan"))
    elif typ == "geprueft":
        p.bohrung.setdefault(ereignis["id"], {})["geprueft"] = bool(ereignis["wert"])
    else:
        return False
    p.version += 1
    return True


# ---------------------------------------------------------------- Pruefstand und Einchecken
def pruefstand(docs: list[dict], p: Projekt) -> dict:
    doppelt = doppelte(docs)
    b_ges = b_gep = s_ges = s_gep = unklass = offen = korrigiert = 0
    for bid, _, b in bohrungen(docs):
        if not wert(p, bid, b, "modell", doppelt):
            continue
        b_ges += 1
        b_gep += bool(wert(p, bid, b, "geprueft"))
        for k, ly in enumerate(b.get("layers") or []):
            s_ges += 1
            s_gep += schicht_geprueft(p, bid, b, k, ly)
            unklass += schicht_unklassifiziert(p, bid, k, ly)
            offen += schicht_offen(p, bid, b, k, ly)
            korrigiert += any(s in p.schicht.get(f"{bid}/{k}", {}) for s in ("oben", "unten", "bodenart"))
    manuell = sum(1 for o in p.bohrung.values() if "x" in o) + len(p.reihe["station"]) + len(p.reihe["abstand"])
    entfernt = sum(1 for o in p.bohrung.values() if o.get("modell") is False)
    return {"bohrungen": [b_gep, b_ges], "schichten": [s_gep, s_ges], "unklassifiziert": unklass,
            "unklassifiziert_offen": offen, "korrigiert": korrigiert, "manuelle_lage": manuell, "entfernt": entfernt}


def stand_text(eintrag: dict) -> str:
    b, s = eintrag["stand"]["bohrungen"], eintrag["stand"]["schichten"]
    return f"v{eintrag['nr']} · {eintrag['zeit']} · {b[0]}/{b[1]} Bohrungen, {s[0]}/{s[1]} Schichten geprueft"


def einchecken(docs: list[dict], p: Projekt, modell: str | None, kommentar: str = "") -> dict:
    """Pruefstand festhalten. modell: Fingerabdruck des Modells = Schluessel seiner Eingaben (nicht das IFC: dessen
    Kopf traegt eine Uhrzeit, nach einem Neustart haette dasselbe Modell einen anderen Hash)."""
    eintrag = {"nr": len(p.eincheckungen) + 1, "zeit": jetzt(),
               "stand": pruefstand(docs, p), "modell": modell[:12] if modell else None, "kommentar": kommentar}
    p.eincheckungen.append(eintrag)
    p.version += 1
    return eintrag


def seit_einchecken_geaendert(docs: list[dict], p: Projekt, modell: str | None) -> bool:
    if not p.eincheckungen:
        return False
    letzter = p.eincheckungen[-1]
    return letzter["stand"] != pruefstand(docs, p) or letzter["modell"] != (modell[:12] if modell else None)
