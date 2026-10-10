"""Parst die Legende eines Bohrprofil-PDF (DIN 4023).

Liefert:
  * die Liste der Bodenart-Bezeichnungen (Sektion BODENARTEN), und
  * welche DIN-Sektionen vorhanden sind (KORNGROESSENBEREICH, NEBENANTEILE,
    KALKGEHALT, KONSISTENZ) -> steuert die dynamischen Spalten von Blatt 4.

Die Legende ist auf jeder Zeichnungsseite (rechts unten) wiederholt; es genuegt
die erste Seite, auf der die Sektionsueberschriften gefunden werden.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

import fitz


def _norm(s: str) -> str:
    s = "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))
    return s.upper().replace("ß", "SS")


# Sektionsueberschrift (normalisiert, Anfang) -> dynamischer Spaltenschluessel
_DIN_SECTIONS = {
    "KORNGR": "kornbereich",          # KORNGROESSENBEREICH
    "NEBENANTEIL": "nebenanteil_staerke",
    "KALKGEHALT": "kalkgehalt",
    "KONSISTENZ": "konsistenz",
}

# Menschlich lesbare Bezeichnungen (fuer Tool-Anzeige)
DIN_LABELS = {
    "kornbereich": "Kornbereich (KORNGRÖSSENBEREICH)",
    "nebenanteil_staerke": "Nebenanteil-Stärke (NEBENANTEILE)",
    "kalkgehalt": "Kalkgehalt (KALKGEHALT)",
    "konsistenz": "Konsistenz (KONSISTENZ)",
}

# Reihenfolge der dynamischen Spalten in der Ausgabe
DIN_ORDER = ["kornbereich", "nebenanteil_staerke", "kalkgehalt", "konsistenz"]


@dataclass
class Legend:
    bodenarten: list[str] = field(default_factory=list)
    din_present: dict[str, bool] = field(default_factory=dict)
    source_page: int | None = None

    def present_din_keys(self) -> list[str]:
        return [k for k in DIN_ORDER if self.din_present.get(k)]


def _find_legend_anchor(words) -> tuple[float, float] | None:
    """Sucht den Anker (x,y) der Sektion 'BODENARTEN'."""
    for w in words:
        if _norm(w[4]).startswith("BODENARTEN"):
            return (w[0], w[1])
    return None


def parse_legend(doc: fitz.Document) -> Legend:
    leg = Legend()
    for pi in range(doc.page_count):
        page = doc[pi]
        words = page.get_text("words")
        norms = {_norm(w[4]) for w in words}
        # Sektionen erkennen
        present = {}
        for prefix, key in _DIN_SECTIONS.items():
            present[key] = any(n.startswith(prefix) for n in norms)
        if not any(present.values()):
            continue
        leg.din_present = present
        leg.source_page = pi

        # BODENARTEN-Namen extrahieren (zwischen 'BODENARTEN' und 'KORNGR...')
        anchor = _find_legend_anchor(words)
        if anchor:
            ax, ay = anchor
            # rechte Legendenspalte: x >= ax, y zwischen BODENARTEN und KORNGR
            korn_y = None
            for w in words:
                if _norm(w[4]).startswith("KORNGR") and w[0] >= ax - 5:
                    korn_y = w[1]
                    break
            y_lo = ay + 4
            y_hi = korn_y - 2 if korn_y else ay + 200
            leg.bodenarten = _extract_bodenarten(words, ax, y_lo, y_hi)
        break
    return leg


def _extract_bodenarten(words, ax, y_lo, y_hi) -> list[str]:
    """Liest pro Zeile die fuehrenden Woerter der ersten Spalte als Name.

    Die Legende ist mehrspaltig: Spalte 1 (Name) bei ``ax``, Spalte 2
    (Adjektiv/Wiederholung) und die Kuerzel folgen deutlich weiter rechts.
    Wir nehmen nur Tokens der ersten Spalte (x0 < ax + 85).
    """
    name_cutoff = ax + 85.0
    rows: dict[int, list] = {}
    for w in words:
        if ax - 5 <= w[0] < name_cutoff and y_lo <= w[1] <= y_hi:
            rows.setdefault(round(w[1] / 5), []).append(w)
    names: list[str] = []
    for key in sorted(rows):
        toks = sorted(rows[key], key=lambda t: t[0])
        name_parts = []
        for t in toks:
            txt = t[4].strip()
            if txt and re.match(r"^[A-ZÄÖÜ][A-Za-zÄÖÜäöüß\-]+$", txt):
                name_parts.append(txt)
            else:
                break
        if len(name_parts) == 2 and name_parts[0] == name_parts[1]:
            name_parts = name_parts[:1]
        if name_parts:
            names.append(" ".join(name_parts))
    # Duplikate entfernen, Reihenfolge erhalten
    seen = set()
    out = []
    for n in names:
        if n not in seen:
            seen.add(n)
            out.append(n)
    return out
