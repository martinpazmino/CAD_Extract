"""Bodenart-Klassifikation und DIN-Token-Parsing.

Kein hartkodiertes Vokabular: die Ziel-Klassen kommen aus der Legende
(``legend.Legend.bodenarten``).  Hier sind nur die *Regeln*, wie ein im
Bohrprofil-Text gefundenes Kopfwort (z. B. "Feinsand", "Klei") auf eine
groebere Civil-3D-Klasse abgebildet wird, sowie wie DIN-Kuerzel
(kornbereich / nebenanteil / kalkgehalt / konsistenz) aus dem Schichttext
extrahiert werden.
"""
from __future__ import annotations

import re
import unicodedata

# ---------------------------------------------------------------------------
# Bodenart -> grobe Klasse
# ---------------------------------------------------------------------------
# Stamm -> Zielklasse. Reihenfolge = Prioritaet (zuerst passender gewinnt).
# Diese Staemme entsprechen den Eintraegen der Legende-Sektion BODENARTEN;
# 'sand' und 'glimmer' sind die einzigen Vergroeberungsregeln aus der Aufgabe
# (Feinsand/Mittelsand/Grobsand -> Sand; Glimmerschluff -> Glimmerton).
_STEM_RULES = [
    ("glimmer", "Glimmerton"),          # Glimmerton + Glimmerschluff
    ("lauenburg", "Lauenburger Ton"),
    ("geschiebe", "Geschiebemergel"),
    ("mergel", "Geschiebemergel"),
    ("mutterboden", "Mutterboden"),
    ("mudde", "Mudde"),
    ("torf", "Torf"),
    ("sand", "Sand"),                   # Feinsand/Mittelsand/Grobsand/...-Streifen
    ("kies", "Kies"),
    ("klei", "Klei"),                   # Klei, Kleistreifen
    ("schluff", "Schluff"),
    ("stein", "Steine"),
    ("ton", "Ton"),
]


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def normalize_head(text: str) -> str:
    """Erstes 'echtes' Wort eines Schichttextes (die Bodenart-Bezeichnung)."""
    t = text.strip().strip("(),.;:/ ")
    # nur Buchstaben + Bindestrich
    m = re.match(r"[A-Za-zÄÖÜäöüß\-]+", t)
    return m.group(0) if m else t


def classify(head_word: str, legend_bodenarten: list[str] | None = None) -> tuple[str, bool]:
    """Bildet ein Kopfwort auf eine grobe Bodenart-Klasse ab.

    Returns (klasse, sicher).  ``sicher=False`` wenn keine Regel griff und das
    Wort unveraendert zurueckgegeben wird (-> in Excel gelb markieren).
    """
    if not head_word:
        return ("", False)
    h = _strip_accents(head_word).lower()
    for stem, target in _STEM_RULES:
        if stem in h:
            return (target, True)
    # Fallback: gegen Legendennamen matchen (laengster Treffer)
    if legend_bodenarten:
        best = None
        for name in legend_bodenarten:
            n = _strip_accents(name).lower()
            if n and (n in h or h in n):
                if best is None or len(n) > len(best[1]):
                    best = (name, n)
        if best:
            return (best[0], True)
    # unbekannt -> Originalwort, unsicher
    return (head_word.strip().strip("(),.;:/"), False)


# ---------------------------------------------------------------------------
# DIN-Kuerzel pro Schicht
# ---------------------------------------------------------------------------
_KORN_MAP = {"fein": "f", "mittel": "m", "grob": "g"}


def parse_kornbereich(head_word: str, full_text: str) -> str | None:
    """KORNGROESSENBEREICH der Hauptfraktion: f / m / g."""
    h = _strip_accents(head_word).lower()
    for word, code in _KORN_MAP.items():
        if word in h:
            return code
    # Grossbuchstaben-Fraktionen fS / mS / gS im Text
    m = re.search(r"\b([fmg])S\b", full_text)
    if m:
        return m.group(1).lower()
    return None


def parse_nebenanteil(full_text: str) -> str | None:
    """NEBENANTEILE-Staerke aus den Symbolen ' / '' / ¯ / =.

    Rueckgabe in Klartext der staerksten gefundenen Auspraegung.
    """
    t = full_text
    has_double = "''" in t or "”" in t or '"' in t
    has_single = bool(re.search(r"[a-zA-Z]’", t)) or bool(re.search(r"[a-zA-Z]'", t))
    has_eq = "=" in t
    has_macron = "¯" in t or "̄" in t
    # Reihenfolge nach Staerke: sehr stark > stark > schwach > sehr schwach
    if has_eq:
        return "sehr stark"
    if has_macron:
        return "stark"
    if has_single and not has_double:
        return "schwach"
    if has_double:
        return "sehr schwach"
    return None


def parse_kalkgehalt(full_text: str) -> str | None:
    """KALKGEHALT: k++ (stark kalkhaltig) / k+ (kalkhaltig)."""
    if re.search(r"k\+\+", full_text):
        return "k++"
    if re.search(r"k\+", full_text):
        return "k+"
    return None


_KONS_MAP = {
    "hfst": "halbfest",
    "fst": "fest",
    "stf": "steif",
    "wch": "weich",
    "brei": "breiig",
}


def parse_konsistenz(full_text: str) -> str | None:
    """KONSISTENZ: wch/stf/hfst/fst -> Klartext."""
    t = full_text.lower()
    # laengste Kuerzel zuerst, damit 'hfst' nicht als 'fst' erkannt wird
    for code in sorted(_KONS_MAP, key=len, reverse=True):
        if re.search(r"\b" + code + r"\b", t):
            return _KONS_MAP[code]
    return None


# Mapping DIN-Spaltenschluessel -> (Parser, braucht_head_word)
DIN_PARSERS = {
    "kornbereich": ("parse_kornbereich", True),
    "nebenanteil_staerke": ("parse_nebenanteil", False),
    "kalkgehalt": ("parse_kalkgehalt", False),
    "konsistenz": ("parse_konsistenz", False),
}


def parse_din(key: str, head_word: str, full_text: str) -> str | None:
    if key == "kornbereich":
        return parse_kornbereich(head_word, full_text)
    if key == "nebenanteil_staerke":
        return parse_nebenanteil(full_text)
    if key == "kalkgehalt":
        return parse_kalkgehalt(full_text)
    if key == "konsistenz":
        return parse_konsistenz(full_text)
    return None
