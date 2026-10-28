"""Projektzustand der App v2: Korrekturen des Nutzers, Lage (Koordinaten oder Reihe), Unterlage, Pruefstand.

Ohne Streamlit testbar. Das kanonische JSON der Extraktion bleibt unveraendert: alles, was der Nutzer
aendert, liegt hier und wird beim Rechnen auf eine Kopie angewendet und dort markiert (coord_source,
gok_source, geprueft, korrigiert). Ereignisse aus dem Viewer (Bohrung verschoben, Station im Schnitt,
Kalibrierung der Unterlage) kommen ueber ereignis_anwenden herein. Beschreibung: docs/20.
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

from baugrundmodell.ifc4x3 import FARBEN, farbe, farbschluessel, hexfarbe  # noqa: E402

LAGE_KOORDINATEN = "koordinaten"          # Lageplan: Rechts-/Hochwert (aus dem PDF, eingetragen oder im Viewer gesetzt)
LAGE_REIHE = "reihe"                      # Laengsschnitt: Bohrungen in einer Reihe, Stationen je Bohrung
UNSICHER = 0.6                            # Konfidenz darunter: zuerst pruefen


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
    lage_modus: str = LAGE_KOORDINATEN
    bohrung: dict[str, dict] = field(default_factory=dict)   # id -> {modell, geprueft, gok, x, y, epsg, quelle}
    schicht: dict[str, dict] = field(default_factory=dict)   # "id/k" -> {oben, unten, bodenart, geprueft}
    reihe: dict = field(default_factory=lambda: {"standard": 20.0, "reihenfolge": [], "abstand": {}, "station": {}})
    unterlage: dict | None = None
    ursprung: tuple[float, float] | None = None
    erzeugt: bool = False
    auto: bool = True
    vorgabe: list[dict] | None = None
    eincheckungen: list[dict] = field(default_factory=list)
    viewer_nr: int = 0                      # zuletzt angewendetes Viewer-Ereignis
    unterlage_zaehler: int = 0              # neue Unterlage: Upload-Feld leeren
    version: int = 0                        # steigt bei Aenderungen von aussen: Tabellen-Editoren neu aufbauen


# ---------------------------------------------------------------- Grundlagen
def natuerlich(code: str):
    return [int(t) if t.isdigit() else t.lower() for t in re.split(r"(\d+)", code)]


def zahl(v) -> float | None:
    try:
        f = float(v)
    except (TypeError, ValueError):
        return None
    return None if f != f else f                         # NaN aus der Tabelle -> None


def _gleich(a, b, tol: float = 1e-6) -> bool:
    a, b = zahl(a), zahl(b)
    return (a is None and b is None) or (a is not None and b is not None and abs(a - b) <= tol)


def bohrungen(docs: list[dict]) -> list[tuple[str, dict, dict]]:
    """(id, Dokument, Bohrung) in Dokumentreihenfolge; id = 'Dokumentindex:Bohrungsindex'."""
    return [(f"{di}:{bi}", d, b) for di, d in enumerate(docs) for bi, b in enumerate(d["boreholes"])]


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
    """Auswahl fuer die Schichttabelle: bekannte Bodenarten und alle, die die Extraktion geliefert hat."""
    aus_docs = {ly.get("soil_class") for _, _, b in bohrungen(docs) for ly in b.get("layers") or [] if ly.get("soil_class")}
    return sorted({k for k in FARBEN if k} | aus_docs | {"unklassifiziert"})


def bodenart_farbe(klasse: str | None) -> str:
    return hexfarbe(farbe(klasse)) if farbschluessel(klasse) else "#d9d9d9"


def neues_projekt(docs: list[dict], signatur: str) -> Projekt:
    p = Projekt(signatur)
    hat_lage = any(b.get("x") is not None and b.get("y") is not None for _, _, b in bohrungen(docs))
    p.lage_modus = LAGE_KOORDINATEN if hat_lage else LAGE_REIHE
    p.reihe["reihenfolge"] = [bid for bid, _, b in sorted(bohrungen(docs), key=lambda t: natuerlich(t[2]["code"]))]
    return p


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
            "epsg": lambda: b.get("crs_epsg"), "quelle": lambda: b.get("coord_source") or ""}[schluessel]()


def schicht_wert(p: Projekt, bid: str, k: int, ly: dict, schluessel: str):
    o = p.schicht.get(f"{bid}/{k}", {})
    if schluessel in o:
        return o[schluessel]
    return {"oben": ly["top_depth"], "unten": ly["bottom_depth"], "bodenart": ly.get("soil_class") or "unklassifiziert",
            "geprueft": False}[schluessel]


def schicht_geprueft(p: Projekt, bid: str, b: dict, k: int, ly: dict) -> bool:
    return bool(schicht_wert(p, bid, k, ly, "geprueft")) or bool(wert(p, bid, b, "geprueft"))


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
                ly["soil_class"] = None if art in (None, "", "unklassifiziert") else art
                ly["confidence"] = 1.0                    # vom Menschen festgelegt
                ly["korrigiert"] = True
                ly["issues"] = list(ly.get("issues") or []) + ["manuell korrigiert"]
            ly["geprueft"] = bool(lo.get("geprueft", False)) or b["geprueft"]
        if b.get("layers"):
            b["end_depth"] = max(ly["bottom_depth"] for ly in b["layers"])
    return neu


# ---------------------------------------------------------------- Tabelle Bohrungen
def bohrungen_zeilen(docs: list[dict], p: Projekt) -> list[dict]:
    doppelt = doppelte(docs)
    out = []
    for bid, d, b in bohrungen(docs):
        schichten = b.get("layers") or []
        konf = [ly.get("confidence") or 0.0 for ly in schichten]
        geprueft = sum(schicht_geprueft(p, bid, b, k, ly) for k, ly in enumerate(schichten))
        hinweise = list(b.get("issues") or [])
        if bid in doppelt:
            hinweise.insert(0, f"doppelt (auch in {doppelt[bid]})")
        out.append({
            "id": bid, "Modell": bool(wert(p, bid, b, "modell", doppelt)), "Geprüft": bool(wert(p, bid, b, "geprueft")),
            "Bohrung": b["code"], "Dokument": d["document"]["file"],
            "Seite": int((b.get("provenance") or [{}])[0].get("page", 0) or 0) + 1,
            "GOK [m NHN]": zahl(wert(p, bid, b, "gok")), "Endteufe [m]": b.get("end_depth"),
            "Rechtswert": zahl(wert(p, bid, b, "x")), "Hochwert": zahl(wert(p, bid, b, "y")),
            "EPSG": zahl(wert(p, bid, b, "epsg")), "Lage aus": wert(p, bid, b, "quelle"),
            "Schichten geprüft": f"{geprueft}/{len(schichten)}",
            "Konfidenz": round(sum(konf) / len(konf), 2) if konf else None,
            "min. Konfidenz": round(min(konf), 2) if konf else None,
            "Grundwasser": ", ".join(f"{g['depth']:.2f} m" for g in b.get("groundwater") or []) or
                           (b.get("groundwater_status") or ""),
            "Hinweise": "; ".join(hinweise)})
    return out


def bohrungen_uebernehmen(docs: list[dict], p: Projekt, zeilen: list[dict]) -> bool:
    """Aenderungen aus der Tabelle in die Korrekturen; gleich dem PDF-Wert -> Korrektur entfaellt."""
    doppelt = doppelte(docs)
    alt = {z["id"]: z for z in bohrungen_zeilen(docs, p)}
    basis = {bid: b for bid, _, b in bohrungen(docs)}
    geaendert = False
    for z in zeilen:
        bid = z["id"]
        b, vorher = basis[bid], alt[bid]
        o = p.bohrung.setdefault(bid, {})
        for spalte, schluessel, ursprung in (("Modell", "modell", _basis_modell(bid, b, doppelt)),
                                             ("Geprüft", "geprueft", False)):
            if bool(z[spalte]) != bool(vorher[spalte]):
                geaendert = True
                if bool(z[spalte]) == ursprung:
                    o.pop(schluessel, None)
                else:
                    o[schluessel] = bool(z[spalte])
        if not _gleich(z["GOK [m NHN]"], vorher["GOK [m NHN]"]):
            geaendert = True
            if _gleich(z["GOK [m NHN]"], b.get("gok_nhn")):
                o.pop("gok", None)
            else:
                o["gok"] = zahl(z["GOK [m NHN]"])
        lage_neu = [z["Rechtswert"], z["Hochwert"], z["EPSG"]]
        lage_alt = [vorher["Rechtswert"], vorher["Hochwert"], vorher["EPSG"]]
        if not all(_gleich(a, c) for a, c in zip(lage_neu, lage_alt)):
            geaendert = True
            if all(_gleich(a, c) for a, c in zip(lage_neu, [b.get("x"), b.get("y"), b.get("crs_epsg")])):
                for s in ("x", "y", "epsg", "quelle"):
                    o.pop(s, None)
            else:
                o.update(x=zahl(z["Rechtswert"]), y=zahl(z["Hochwert"]), epsg=zahl(z["EPSG"]), quelle="manuell (Tabelle)")
        if not o:
            p.bohrung.pop(bid, None)
    return geaendert


# ---------------------------------------------------------------- Tabelle Schichten einer Bohrung
def schichten_zeilen(docs: list[dict], p: Projekt, bid: str) -> list[dict]:
    b = next(b for i, _, b in bohrungen(docs) if i == bid)
    d = next(d for i, d, _ in bohrungen(docs) if i == bid)
    out = []
    for k, ly in enumerate(b.get("layers") or []):
        lo = p.schicht.get(f"{bid}/{k}", {})
        pv = (ly.get("provenance") or [{}])[0]
        out.append({"k": k, "von": float(schicht_wert(p, bid, k, ly, "oben")), "bis": float(schicht_wert(p, bid, k, ly, "unten")),
                    "Bodenart": schicht_wert(p, bid, k, ly, "bodenart"), "Geprüft": schicht_geprueft(p, bid, b, k, ly),
                    "Korrigiert": any(s in lo for s in ("oben", "unten", "bodenart")),
                    "Konfidenz": ly.get("confidence"), "Beschreibung": ly.get("description_raw") or "",
                    "Hinweise": "; ".join(ly.get("issues") or []),
                    "Quelle": f"{d['document']['file']} S.{int(pv.get('page') or 0) + 1}"})
    return out


def schichten_uebernehmen(docs: list[dict], p: Projekt, bid: str, zeilen: list[dict]) -> bool:
    b = next(b for i, _, b in bohrungen(docs) if i == bid)
    alt = {z["k"]: z for z in schichten_zeilen(docs, p, bid)}
    geaendert = False
    for z in zeilen:
        k = int(z["k"])
        ly = b["layers"][k]
        vorher = alt[k]
        o = p.schicht.setdefault(f"{bid}/{k}", {})
        for spalte, schluessel, ursprung in (("von", "oben", ly["top_depth"]), ("bis", "unten", ly["bottom_depth"])):
            if not _gleich(z[spalte], vorher[spalte]):
                geaendert = True
                if _gleich(z[spalte], ursprung):
                    o.pop(schluessel, None)
                else:
                    o[schluessel] = zahl(z[spalte])
        if (z["Bodenart"] or "unklassifiziert") != vorher["Bodenart"]:
            geaendert = True
            if (z["Bodenart"] or "unklassifiziert") == (ly.get("soil_class") or "unklassifiziert"):
                o.pop("bodenart", None)
            else:
                o["bodenart"] = z["Bodenart"]
        korrigiert_jetzt = any(s_ in o for s_ in ("oben", "unten", "bodenart")) and not vorher["Korrigiert"]
        if korrigiert_jetzt and not bool(z["Geprüft"]):
            o["geprueft"] = True                          # wer korrigiert, hat die Schicht geprueft
        elif bool(z["Geprüft"]) != bool(vorher["Geprüft"]):
            geaendert = True
            o["geprueft"] = bool(z["Geprüft"])
            if not o["geprueft"] and wert(p, bid, b, "geprueft"):
                # Haken an einer Schicht weg, die Bohrung war als ganze geprueft: die anderen Schichten bleiben geprueft
                p.bohrung.setdefault(bid, {})["geprueft"] = False
                for j, _ in enumerate(b["layers"]):
                    if j != k:
                        p.schicht.setdefault(f"{bid}/{j}", {}).setdefault("geprueft", True)
        if not o:
            p.schicht.pop(f"{bid}/{k}", None)
    return geaendert


def alle_schichten_pruefen(docs: list[dict], p: Projekt, bid: str, geprueft: bool = True) -> None:
    b = next(b for i, _, b in bohrungen(docs) if i == bid)
    for k, _ in enumerate(b.get("layers") or []):
        p.schicht.setdefault(f"{bid}/{k}", {})["geprueft"] = geprueft


# ---------------------------------------------------------------- Reihe (Laengsschnitt)
def _reihenfolge(docs: list[dict], p: Projekt) -> list[str]:
    alle = [bid for bid, _, _ in bohrungen(docs)]
    bekannt = [bid for bid in p.reihe["reihenfolge"] if bid in alle]
    return bekannt + [bid for bid in alle if bid not in bekannt]


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


def reihe_zeilen(docs: list[dict], p: Projekt, ids: list[str]) -> list[dict]:
    st = stationen(docs, p, ids)
    codes = {bid: b["code"] for bid, _, b in bohrungen(docs)}
    out, vorher = [], None
    for nr, (bid, (s, q)) in enumerate(st.items(), start=1):
        out.append({"id": bid, "Nr": nr, "Bohrung": codes[bid],
                    "Abstand zum Vorgänger [m]": None if vorher is None else round(s - vorher, 3),
                    "Station [m]": round(s, 3), "Quelle": {"Schnitt": "im Schnitt gesetzt", "manuell": "Abstand manuell",
                                                           "Standard": "Standardabstand", "Start": "Anfang"}[q]})
        vorher = s
    return out


def reihe_uebernehmen(docs: list[dict], p: Projekt, ids: list[str], zeilen: list[dict]) -> bool:
    alt = {z["id"]: z for z in reihe_zeilen(docs, p, ids)}
    geaendert = False
    neu = sorted(zeilen, key=lambda z: (zahl(z["Nr"]) if zahl(z["Nr"]) is not None else 1e9, alt[z["id"]]["Nr"]))
    if [z["id"] for z in neu] != [z["id"] for z in sorted(alt.values(), key=lambda z: z["Nr"])]:
        rest = [bid for bid in _reihenfolge(docs, p) if bid not in ids]
        p.reihe["reihenfolge"] = [z["id"] for z in neu] + rest
        geaendert = True
    for z in zeilen:
        bid, vorher = z["id"], alt[z["id"]]
        if not _gleich(z["Station [m]"], vorher["Station [m]"], 1e-3) and zahl(z["Station [m]"]) is not None:
            p.reihe["station"][bid] = zahl(z["Station [m]"])
            p.reihe["abstand"].pop(bid, None)
            geaendert = True
        elif not _gleich(z["Abstand zum Vorgänger [m]"], vorher["Abstand zum Vorgänger [m]"], 1e-3):
            a = zahl(z["Abstand zum Vorgänger [m]"])
            p.reihe["station"].pop(bid, None)
            if a is None:
                p.reihe["abstand"].pop(bid, None)
            else:
                p.reihe["abstand"][bid] = a
            geaendert = True
    return geaendert


# ---------------------------------------------------------------- Eingabe fuer den Modellierer
def modell_eingabe(docs: list[dict], p: Projekt, e: Einstellungen) -> Vorbereitung:
    """Korrekturen anwenden, Auswahl, GOK-Regel und Lage nach Modus; alles Angenommene als Hinweis."""
    neu = wirksame_docs(docs, p)
    doppelt = doppelte(docs)
    hinweise: list[str] = []
    raus: list[dict] = []
    gewaehlt: list[tuple[str, dict]] = []
    for bid, d, b in bohrungen(neu):
        if not wert(p, bid, b, "modell", doppelt):
            raus.append({"code": b["code"], "dokument": d["document"]["file"],
                         "grund": f"doppelt (auch in {doppelt[bid]})" if bid in doppelt and "modell" not in p.bohrung.get(bid, {})
                         else ("keine Schichten" if not b.get("layers") else "abgewaehlt")})
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
                            "nicht vermessen, nur zur Anschauung (Abstaende in 'Lage' eintragen oder im Schnitt setzen).")
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
    """Fester lokaler Nullpunkt des Projekts: verschiebt sich nur, wenn die Bohrungen weit davon entfernt liegen."""
    if not vorb.lage:
        return p.ursprung or (0.0, 0.0)
    xs = [v[0] for v in vorb.lage.values()]
    ys = [v[1] for v in vorb.lage.values()]
    mitte = (sum(xs) / len(xs), sum(ys) / len(ys))
    if p.ursprung is None or math.hypot(mitte[0] - p.ursprung[0], mitte[1] - p.ursprung[1]) > 20000:
        p.ursprung = (round(mitte[0], -2), round(mitte[1], -2))
    return p.ursprung


# ---------------------------------------------------------------- Viewer
def viewer_bohrungen(docs: list[dict], p: Projekt, vorb: Vorbereitung, bericht: dict | None) -> list[dict]:
    """Stecknadeln fuer den Viewer: alle gewaehlten Bohrungen, mit Lage oder (ohne) zum Platzieren."""
    doppelt = doppelte(docs)
    im_modell = {x["code"] for x in (bericht or {}).get("bohrungen", [])}
    raus = {a["code"]: a["grund"] for a in (bericht or {}).get("ausgeschlossen", [])}
    ohne_gok_raus = any("ohne GOK bleiben draussen" in h for h in vorb.hinweise)
    wirksam = {bid: b for bid, _, b in bohrungen(wirksame_docs(docs, p))}
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
        out.append({"id": bid, "code": b["code"], "x": x, "y": y, "quelle": quelle,
                    "gok": 0.0 if gok is None else float(gok), "gok_bekannt": gok is not None,
                    "ende": float(b.get("end_depth") or (schichten[-1]["bottom_depth"] if schichten else 0.0)),
                    "geprueft": bool(b.get("geprueft")),
                    "schichten_geprueft": sum(bool(ly.get("geprueft")) for ly in schichten), "schichten_n": len(schichten),
                    "konfidenz": round(min(konf), 2) if konf else None,
                    "im_modell": drin, "grund": grund,
                    # je Schicht: Tiefe oben/unten, Farbe, Bodenart, Konfidenz, geprueft
                    "schichten": [[float(ly["top_depth"]), float(ly["bottom_depth"]), bodenart_farbe(ly.get("soil_class")),
                                   ly.get("soil_class") or "unklassifiziert", round(float(ly.get("confidence") or 0.0), 2),
                                   bool(ly.get("geprueft"))] for ly in schichten]})
    return out


def speichern(p: Projekt) -> dict:
    """Projektstand als JSON (Korrekturen, Lage, Pruefung, Eincheckungen) - die Extraktion bleibt eigene Datei."""
    return {"format": "geo_agent-projekt/1", **asdict(p)}


def laden(d: dict) -> Projekt:
    werte = {k: v for k, v in d.items() if k in Projekt.__dataclass_fields__}
    p = Projekt(**werte)
    if p.ursprung is not None:
        p.ursprung = (float(p.ursprung[0]), float(p.ursprung[1]))
    return p


def ereignis_anwenden(p: Projekt, ereignis: dict | None) -> bool:
    """Ereignis aus dem Viewer (laufende Nummer 'nr'); jedes nur einmal. True = Projekt geaendert."""
    if not ereignis or int(ereignis.get("nr", 0)) <= p.viewer_nr:
        return False
    if ereignis.get("projekt") not in (None, "", p.signatur):          # Ereignis eines anderen Projekts
        return False
    p.viewer_nr = int(ereignis["nr"])
    typ = ereignis.get("typ")
    if typ == "lage":
        kal = (p.unterlage or {}).get("kalibrierung") or {}
        o = p.bohrung.setdefault(ereignis["id"], {})
        o.update(x=float(ereignis["x"]), y=float(ereignis["y"]),
                 quelle="Plan (kalibriert)" if kal else "manuell (Viewer)")
        if kal.get("epsg"):                               # sonst bleibt das System der Bohrung (PDF/Tabelle)
            o["epsg"] = int(kal["epsg"])
    elif typ == "station":
        p.reihe["station"][ereignis["id"]] = float(ereignis["station"])
        p.reihe["abstand"].pop(ereignis["id"], None)
    elif typ == "gok":                                    # Ansatzhoehe im Laengsschnitt gezogen
        p.bohrung.setdefault(ereignis["id"], {})["gok"] = float(ereignis["gok"])
    elif typ == "kalibrierung" and p.unterlage is not None:
        p.unterlage["kalibrierung"] = {"punkte": ereignis["punkte"], "epsg": ereignis.get("epsg")}
    elif typ == "geprueft":
        p.bohrung.setdefault(ereignis["id"], {})["geprueft"] = bool(ereignis["wert"])
    else:
        return False
    p.version += 1
    return True


# ---------------------------------------------------------------- Pruefstand und Einchecken
def pruefstand(docs: list[dict], p: Projekt) -> dict:
    doppelt = doppelte(docs)
    b_ges = b_gep = s_ges = s_gep = unsicher = korrigiert = 0
    for bid, _, b in bohrungen(docs):
        if not wert(p, bid, b, "modell", doppelt):
            continue
        b_ges += 1
        b_gep += bool(wert(p, bid, b, "geprueft"))
        for k, ly in enumerate(b.get("layers") or []):
            s_ges += 1
            gep = schicht_geprueft(p, bid, b, k, ly)
            s_gep += gep
            unsicher += (not gep) and (ly.get("confidence") or 0.0) < UNSICHER
            korrigiert += any(s in p.schicht.get(f"{bid}/{k}", {}) for s in ("oben", "unten", "bodenart"))
    manuell = sum(1 for o in p.bohrung.values() if "x" in o) + len(p.reihe["station"]) + len(p.reihe["abstand"])
    return {"bohrungen": [b_gep, b_ges], "schichten": [s_gep, s_ges], "unsicher_ungeprueft": unsicher,
            "korrigiert": korrigiert, "manuelle_lage": manuell}


def stand_text(eintrag: dict) -> str:
    b, s = eintrag["stand"]["bohrungen"], eintrag["stand"]["schichten"]
    return f"v{eintrag['nr']} · {eintrag['zeit']} · {b[0]}/{b[1]} Bohrungen, {s[0]}/{s[1]} Schichten geprueft"


def einchecken(docs: list[dict], p: Projekt, modell: str | None, kommentar: str = "") -> dict:
    """Pruefstand festhalten. modell: Fingerabdruck des Modells = Schluessel seiner Eingaben (nicht das IFC: dessen
    Kopf traegt eine Uhrzeit, nach einem Neustart haette dasselbe Modell einen anderen Hash)."""
    eintrag = {"nr": len(p.eincheckungen) + 1, "zeit": datetime.now().strftime("%Y-%m-%d %H:%M"),
               "stand": pruefstand(docs, p), "modell": modell[:12] if modell else None, "kommentar": kommentar}
    p.eincheckungen.append(eintrag)
    return eintrag


def seit_einchecken_geaendert(docs: list[dict], p: Projekt, modell: str | None) -> bool:
    if not p.eincheckungen:
        return False
    letzter = p.eincheckungen[-1]
    return letzter["stand"] != pruefstand(docs, p) or letzter["modell"] != (modell[:12] if modell else None)
