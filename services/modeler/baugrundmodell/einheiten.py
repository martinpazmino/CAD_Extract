"""Layer-Cake Schritt 1-2 (Architektur 7.2): Bohrungen vorbereiten und Modelleinheiten korrelieren.

Eine Modelleinheit ist eine Bodenart an einer Stelle der Schichtfolge ("Sand 1", "Kies 1", "Sand 2").
Die Schichtfolgen aller Bohrungen werden gegen eine gemeinsame Folge ausgerichtet, wie bei einem
Sequenzalignment (dynamische Programmierung):

  M  Abschnitt passt zur Einheit (gleiche Bodenart; Kosten = Hoehenabstand zur Einheit)
  S  Einheit fehlt in der Bohrung (Ausduennung, Maechtigkeit 0)
  E  derselbe Abschnitt deckt auch die naechste Einheit gleicher Bodenart (Linse dazwischen fehlt)
  C  weiterer Abschnitt in derselben Einheit (nur bei vorgegebenen Einheiten mit mehreren Bodenarten)
  N  Abschnitt passt nirgends -> neue Einheit
  T  Einheit liegt unter der Endteufe -> unbekannt (nicht "fehlt")

Die Folge waechst progressiv (Startbohrung = laengste Folge, dann jeweils die naechstgelegene
Bohrung); danach werden alle Bohrungen gegen die fertige Folge neu ausgerichtet, jede ohne ihre
eigenen Daten in den Hoehenreferenzen (leave-one-out).
"""
from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass, field

UNKLASSIFIZIERT = "unklassifiziert"

# Kosten der Ausrichtung (Hoehen in m)
K_FEHLT = 2.0         # Einheit fehlt (Ausduennung)
K_NEU = 3.0           # Abschnitt passt zu keiner Einheit
K_SPALT = 0.5         # ein Abschnitt deckt zwei Einheiten gleicher Bodenart
K_WEITER = 0.2        # zweiter Abschnitt in derselben Einheit
K_ABSTAND = 1.0       # je m Luecke zwischen Abschnitt und Hoehenbereich der Einheit
K_MITTE = 0.1         # je m Abstand der Mitten
K_UEBER_ENDE = 3.0    # Einheit liegt ganz ueber der Endteufe, soll aber "unbekannt" sein
NACHLAUF_RUNDEN = 4


@dataclass
class Abschnitt:
    """Zusammengefasste Schichten gleicher Bodenart einer Bohrung (Hoehen in m NHN)."""
    klasse: str
    ok: float
    uk: float
    schichten: list[int]


@dataclass
class Bohrung:
    code: str
    x: float
    y: float
    gok: float
    abschnitte: list[Abschnitt]
    dokument: str
    hinweise: list[str] = field(default_factory=list)
    lage: str = "georeferenziert"      # Herkunft der Lage: Koordinatenquelle der Extraktion, manuell, schematisch
    hoehe: str = "m NHN"               # Herkunft der Ansatzhoehe: m NHN, manuell, relativ

    @property
    def ende(self) -> float:
        return self.abschnitte[-1].uk


@dataclass(eq=False)
class Einheit:
    name: str
    klassen: frozenset[str]
    vorgegeben: bool = False

    @property
    def klasse(self) -> str:
        return "/".join(sorted(self.klassen))


@dataclass
class Kontakt:
    """Unterkante einer Einheit in einer Bohrung.

    art: exakt (z), frei (zwischen lo und hi, Gruppe = gleiche Hoehe), zensiert (<= hi, die Bohrung
    endet in der Einheit) oder unbekannt (<= hi, Einheit unter der Endteufe).
    """
    art: str
    status: str                  # vorhanden | fehlt | unbekannt
    z: float | None = None
    lo: float | None = None
    hi: float | None = None
    gruppe: tuple | None = None


# ---------------------------------------------------------------- Vorbereitung
def _system(b: dict) -> str:
    return f"EPSG:{b['crs_epsg']}" if b.get("crs_epsg") else "lokal"


def bohrungen_aus_extraktion(docs: list[dict]) -> tuple[list[Bohrung], list[dict], int | None]:
    """Kanonische Extraktions-JSONs -> modellfaehige Bohrungen; der Rest mit Grund in 'ausgeschlossen'.

    Lage ohne EPSG (manuell, Lageplan, schematisch) ist ein lokales System. Ein Modell hat genau ein
    System: das der meisten Bohrungen (bei Gleichstand das georeferenzierte); Rueckgabe-EPSG None = lokal.
    """
    lagen = Counter(_system(b) for d in docs for b in d["boreholes"] if b.get("x") is not None and b.get("y") is not None)
    system = max(lagen, key=lambda k: (lagen[k], k != "lokal")) if lagen else None
    epsg = int(system.split(":")[1]) if system and system != "lokal" else None
    bohrungen: list[Bohrung] = []
    ausgeschlossen: list[dict] = []
    for d in docs:
        datei = d["document"]["file"]
        for b in d["boreholes"]:
            fehlt = [t for t, f in (("keine Koordinaten", b.get("x") is None or b.get("y") is None),
                                    ("Ansatzhoehe (GOK) unbekannt", b.get("gok_nhn") is None),
                                    ("keine Schichten", not b.get("layers"))) if f]
            grund = ", ".join(fehlt) or None
            if not grund and _system(b) != system:
                grund = f"anderes Koordinatensystem ({_system(b)} statt {system})"
            elif not grund:
                for c in bohrungen:
                    if c.code == b["code"] and abs(c.x - b["x"]) < 0.5 and abs(c.y - b["y"]) < 0.5:
                        grund = f"doppelt (bereits aus {c.dokument})"
                    elif math.hypot(c.x - b["x"], c.y - b["y"]) < 0.1:
                        grund = f"gleiche Lage wie {c.code}"
                    if grund:
                        break
            if grund:
                ausgeschlossen.append({"code": b["code"], "dokument": datei, "grund": grund})
                continue
            vb = _vorbereiten(b, datei)
            if vb.abschnitte:
                bohrungen.append(vb)
            else:
                ausgeschlossen.append({"code": b["code"], "dokument": datei, "grund": "keine gueltigen Schichten"})
    return bohrungen, ausgeschlossen, epsg


def _vorbereiten(b: dict, dokument: str) -> Bohrung:
    gok = float(b["gok_nhn"])
    hinweise: list[str] = []
    roh: list[list] = []                                   # [klasse, oben_m, unten_m, schichtindizes]
    tiefe = 0.0
    for idx, ly in sorted(enumerate(b["layers"]), key=lambda t: t[1]["top_depth"]):
        oben, unten = float(ly["top_depth"]), float(ly["bottom_depth"])
        if unten <= oben:
            hinweise.append(f"Schicht {oben:.2f}-{unten:.2f} m ohne Maechtigkeit verworfen")
            continue
        if oben > tiefe + 0.01:
            hinweise.append(f"Luecke {tiefe:.2f}-{oben:.2f} m ohne Schicht als {UNKLASSIFIZIERT} gefuehrt")
            roh.append([UNKLASSIFIZIERT, tiefe, oben, []])
        elif oben < tiefe - 0.01:
            hinweise.append(f"Ueberlappung bei {oben:.2f} m: Oberkante auf {tiefe:.2f} m gesetzt")
            oben = tiefe
            if unten <= oben:
                continue
        roh.append([ly.get("soil_class") or UNKLASSIFIZIERT, oben, unten, [idx]])
        tiefe = unten
    # unklassifizierte Abschnitte zwischen gleicher Bodenart dieser zuschlagen (markiert, nicht versteckt)
    k = 0
    while k < len(roh):
        if roh[k][0] != UNKLASSIFIZIERT:
            k += 1
            continue
        e = k
        while e + 1 < len(roh) and roh[e + 1][0] == UNKLASSIFIZIERT:
            e += 1
        if 0 < k and e + 1 < len(roh) and roh[k - 1][0] == roh[e + 1][0]:
            for r in roh[k:e + 1]:
                r[0] = roh[k - 1][0]
            hinweise.append(f"unklassifiziert {roh[k][1]:.2f}-{roh[e][2]:.2f} m der umgebenden Bodenart "
                            f"{roh[k - 1][0]} zugeschlagen")
        k = e + 1
    abschnitte: list[Abschnitt] = []
    for klasse, oben, unten, idx in roh:
        if abschnitte and abschnitte[-1].klasse == klasse:
            abschnitte[-1].uk = gok - unten
            abschnitte[-1].schichten += idx
        else:
            abschnitte.append(Abschnitt(klasse, gok - oben, gok - unten, list(idx)))
    lage = b.get("coord_source") or ("georeferenziert" if b.get("crs_epsg") else "lokal")
    hoehe = {"manuell": "manuell (m NHN)", "relativ": "relativ (GOK unbekannt, 0 m gesetzt)"}.get(
        b.get("gok_source") or "", "m NHN")
    return Bohrung(b["code"], float(b["x"]), float(b["y"]), gok, abschnitte, dokument, hinweise, lage, hoehe)


# ---------------------------------------------------------------- Ausrichtung
Ref = tuple[float, float, float, float]               # Oberkante, Unterkante (m NHN), dieselben als Tiefe u. GOK


def _abstand(o1: float, u1: float, o2: float, u2: float) -> float:
    """Luecke zwischen zwei Bereichen (oben > unten) plus Abstand der Mitten, gewichtet."""
    luecke = max(0.0, u1 - o2, u2 - o1)
    return K_ABSTAND * luecke + K_MITTE * abs((o1 + u1) / 2 - (o2 + u2) / 2)


def _hoehe(b: Bohrung, a: Abschnitt, ref: Ref | None) -> float:
    """Kleinerer Abstand von Hoehe (m NHN) und Tiefe unter GOK: tiefe Schichten liegen auf gleicher Hoehe,
    oberflaechennahe (Auffuellung, Decke, Mutterboden) folgen dem Gelaende (Talheim: GOK 749-772 m)."""
    if ref is None:
        return 0.0
    hoehe = _abstand(a.ok, a.uk, ref[0], ref[1])
    tiefe = _abstand(-(b.gok - a.ok), -(b.gok - a.uk), -ref[2], -ref[3])
    return min(hoehe, tiefe)


def _ueber_ende(b: Bohrung, ref: Ref | None) -> float:
    """Strafe, wenn die Einheit nach Hoehe UND nach Tiefe ganz ueber der Endteufe laege."""
    if ref is None:
        return 0.0
    luecke = min(ref[1] - b.ende, (b.gok - b.ende) - ref[3])
    return 0.0 if luecke <= 0 else K_UEBER_ENDE + K_ABSTAND * luecke


def ausrichten(b: Bohrung, einheiten: list[Einheit],
               refs: list[Ref | None]) -> tuple[float, list[tuple]]:
    """Ausrichtung einer Bohrung gegen die Einheitenfolge.

    Zustand (i, j, s): i Abschnitte und j Einheiten verbraucht; s = 0 der letzte Abschnitt gehoert
    zu keiner Einheit, 1 er gehoert zur Einheit j-1, 2 er gehoert zu einer frueheren Einheit und
    danach fehlen Einheiten (offene Ausduennung, nur durch M oder E abschliessbar).
    Rueckgabe: Kosten und Operationen (op, abschnittindex|None, einheitindex).
    """
    A, m, n = b.abschnitte, len(b.abschnitte), len(einheiten)
    kosten: dict[tuple, float] = {(0, 0, 0): 0.0}
    zurueck: dict[tuple, tuple] = {}

    def schieben(von, nach, dk, op):
        k = kosten[von] + dk
        if k < kosten.get(nach, math.inf) - 1e-12:
            kosten[nach] = k
            zurueck[nach] = (von, op)

    for i in range(m + 1):
        for j in range(n + 1):
            for s in range(3):
                if (i, j, s) not in kosten:
                    continue
                st = (i, j, s)
                if i < m and j < n and A[i].klasse in einheiten[j].klassen:
                    schieben(st, (i + 1, j + 1, 1), _hoehe(b, A[i], refs[j]), ("M", i, j))
                if j < n and (i < m or s in (1, 2)):
                    schieben(st, (i, j + 1, 2 if s else 0), K_FEHLT, ("S", None, j))
                if j < n and i == m and s in (0, 1):
                    schieben(st, (i, j + 1, 0), _ueber_ende(b, refs[j]), ("T", None, j))
                if i < m:
                    schieben(st, (i + 1, j, 0), K_NEU, ("N", i, j))
                if s in (1, 2) and i > 0 and j < n and A[i - 1].klasse in einheiten[j].klassen:
                    schieben(st, (i, j + 1, 1), K_SPALT + _hoehe(b, A[i - 1], refs[j]), ("E", i - 1, j))
                if s == 1 and i < m and j > 0 and A[i].klasse in einheiten[j - 1].klassen:
                    schieben(st, (i + 1, j, 1), K_WEITER + _hoehe(b, A[i], refs[j - 1]), ("C", i, j - 1))
    ende = min(((m, n, s) for s in (0, 1) if (m, n, s) in kosten), key=lambda k: kosten[k])
    ops = []
    st = ende
    while st != (0, 0, 0):
        st, op = zurueck[st]
        ops.append(op)
    return kosten[ende], ops[::-1]


# ---------------------------------------------------------------- Korrelation
def _belegung(b: Bohrung, ops: list[tuple]) -> dict[int, Ref]:
    """Bereich je Einheit (Objekt-id) in einer Bohrung, als Hoehe und als Tiefe; bei E der ganze Abschnitt."""
    bel: dict[int, Ref] = {}
    for op, i, e in ops:
        if op in ("M", "C", "E"):
            a = b.abschnitte[i]
            alt = bel.get(id(e))
            ok, uk = (a.ok, a.uk) if alt is None else (max(alt[0], a.ok), min(alt[1], a.uk))
            bel[id(e)] = (ok, uk, b.gok - ok, b.gok - uk)
    return bel


def _referenzen(b: Bohrung, einheiten: list[Einheit], belegungen: dict[str, dict],
                lage: dict[str, tuple[float, float]]) -> list[Ref | None]:
    """Bereich je Einheit an der Stelle von b (Hoehe und Tiefe): IDW-Mittel der anderen Bohrungen (ohne b)."""
    refs: list[Ref | None] = []
    for e in einheiten:
        sw = 0.0
        summe = [0.0, 0.0, 0.0, 0.0]
        for code, bel in belegungen.items():
            if code == b.code or id(e) not in bel:
                continue
            x, y = lage[code]
            w = 1.0 / ((x - b.x) ** 2 + (y - b.y) ** 2 + 1.0)
            sw += w
            summe = [s_ + w * v for s_, v in zip(summe, bel[id(e)])]
        refs.append(tuple(v / sw for v in summe) if sw else None)
    return refs


def _reihenfolge(bohrungen: list[Bohrung]) -> list[Bohrung]:
    """Start: laengste Folge (dann tiefste); danach jeweils die zur Menge naechstgelegene Bohrung."""
    rest = list(bohrungen)
    start = max(rest, key=lambda b: (len(b.abschnitte), b.gok - b.ende))
    folge = [start]
    rest.remove(start)
    while rest:
        nb = min(rest, key=lambda b: min(math.hypot(b.x - c.x, b.y - c.y) for c in folge))
        folge.append(nb)
        rest.remove(nb)
    return folge


def _anwenden(einheiten: list[Einheit], b: Bohrung, ops: list[tuple]) -> tuple[list[Einheit], list[tuple]]:
    """Neue Einheiten (N) einfuegen; Operationen auf Einheit-Objekte umstellen."""
    neu = list(einheiten)
    aus = []
    for op, i, j in ops:
        if op == "N":
            e = Einheit(b.abschnitte[i].klasse, frozenset([b.abschnitte[i].klasse]))
            pos = neu.index(einheiten[j]) if j < len(einheiten) else len(neu)
            neu.insert(pos, e)
            aus.append(("M", i, e))
        else:
            aus.append((op, i, einheiten[j]))
    return neu, aus


def korrelieren(bohrungen: list[Bohrung], vorgabe: list[Einheit] | None = None
                ) -> tuple[list[Einheit], dict[str, list[tuple]], list[str]]:
    """Gemeinsame Einheitenfolge und Zuordnung je Bohrung (Operationen mit Einheit-Objekten)."""
    einheiten = list(vorgabe or [])
    lage = {b.code: (b.x, b.y) for b in bohrungen}
    zuordnung: dict[str, list[tuple]] = {}
    belegungen: dict[str, dict] = {}
    hinweise: list[str] = []
    folge = _reihenfolge(bohrungen)
    for runde in range(NACHLAUF_RUNDEN + 1):
        neu = False
        for b in folge:
            refs = _referenzen(b, einheiten, belegungen, lage)
            _, ops = ausrichten(b, einheiten, refs)
            neu |= any(op == "N" for op, _, _ in ops)
            einheiten, zuordnung[b.code] = _anwenden(einheiten, b, ops)
            belegungen[b.code] = _belegung(b, zuordnung[b.code])
        if runde > 0 and not neu:
            break
    else:
        hinweise.append("Korrelation nach den Nachlaufrunden nicht stabil; letzte Zuordnung verwendet")
    # Einheiten, die keine Bohrung belegt, entfallen (auch vorgegebene: markiert)
    belegt = {id(e) for ops in zuordnung.values() for op, _, e in ops if op in ("M", "C", "E")}
    for e in einheiten:
        if id(e) not in belegt and e.vorgegeben:
            hinweise.append(f"vorgegebene Einheit '{e.name}' in keiner Bohrung gefunden")
    einheiten = [e for e in einheiten if id(e) in belegt]
    for code in zuordnung:
        zuordnung[code] = [o for o in zuordnung[code] if id(o[2]) in belegt]
    if vorgabe:
        hinweise += [f"Bodenart '{e.klasse}' passt in keine vorgegebene Einheit: neue Einheit eingefuegt"
                     for e in einheiten if not e.vorgegeben]
    _benennen(einheiten)
    return einheiten, zuordnung, hinweise


def _benennen(einheiten: list[Einheit]) -> None:
    """Automatische Einheiten: Bodenart, bei Wiederholung durchnummeriert (Sand 1, Sand 2)."""
    auto = [e for e in einheiten if not e.vorgegeben]
    anzahl = Counter(e.klasse for e in auto)
    zaehler: Counter = Counter()
    for e in auto:
        zaehler[e.klasse] += 1
        e.name = f"{e.klasse} {zaehler[e.klasse]}" if anzahl[e.klasse] > 1 else e.klasse


# ---------------------------------------------------------------- Kontakte
def kontakte(b: Bohrung, ops: list[tuple], einheiten: list[Einheit]) -> list[Kontakt]:
    """Unterkante jeder Einheit in Bohrung b (siehe Kontakt)."""
    haupt: dict[int, tuple] = {}
    for op, i, e in ops:
        if op != "C":
            haupt[id(e)] = (op, i)
    folge = [haupt.get(id(e), ("T", None)) for e in einheiten]
    status = {"M": "vorhanden", "E": "vorhanden", "S": "fehlt", "T": "unbekannt"}
    aus: list[Kontakt] = []
    for j, (op, _) in enumerate(folge):
        st = status[op]
        if op == "T":
            aus.append(Kontakt("unbekannt", st, hi=b.ende))
            continue
        k = j + 1
        while k < len(folge) and folge[k][0] == "S":
            k += 1
        if k == len(folge) or folge[k][0] == "T":
            aus.append(Kontakt("zensiert", st, hi=b.ende))
        elif folge[k][0] == "M":
            aus.append(Kontakt("exakt", st, z=b.abschnitte[folge[k][1]].ok))
        else:                                              # E: Grenze irgendwo im geteilten Abschnitt
            a = b.abschnitte[folge[k][1]]
            aus.append(Kontakt("frei", st, lo=a.uk, hi=a.ok, gruppe=(b.code, k)))
    return aus


def einheiten_aus_vorgabe(daten: list[dict]) -> list[Einheit]:
    """Vorgabe des Gutachters: [{"name": "Sande", "bodenarten": ["Sand", "Kies"]}, ...] von oben nach unten."""
    return [Einheit(d["name"], frozenset(d.get("bodenarten") or [d["name"]]), vorgegeben=True) for d in daten]
