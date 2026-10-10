"""Bohrprofil-Parsing (DIN 4023, Vektor-CAD).

Liefert Blatt 1 (Geomodul: eine Zeile je Kernbohrung) und Blatt 2
(Geomodul_Bodenschicht: eine Zeile je konsolidierter Bodenschicht).

Nur Kernbohrungen (Header 'B nn/jj') werden verarbeitet; Sonden (DS), und
Grundwassermessstellen (GWM) werden ausgeschlossen, dienen aber als
X-Grenze fuer das Bodenart-Textband der vorangehenden Bohrung.

Pro Bohrung drei X-Sub-Banden (relativ zum X-Anker = 'B'-Token):
    Tiefen-Spalte : x_label-65 .. x_label+8   -> Paare '(NHN_rel) tiefe'
    Bodenart-Text : x_label+58 .. naechster_Anker-25
    Diagramm      : Rest (ignoriert)
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

import fitz

from . import soil
from .legend import Legend

# Band-Offsets relativ zum X-Anker (CAD M 1:100, seitenuebergreifend stabil)
DEPTH_LEFT = -65.0
DEPTH_RIGHT = 8.0
BODEN_LEFT = 58.0
BODEN_RIGHT_MARGIN = 25.0

_NUM_RE = re.compile(r"^\d+[a-z]?/\d{2}$")
_PREFIX_TOKENS = {"B", "DS", "GWM", "BS", "BK", "RKS"}
_GOK_RE = re.compile(r"NHN\s*([+-]\d+[,.]\d+)\s*m", re.IGNORECASE)
_PAIR_RE = re.compile(r"\(\s*(-?\d+[,.]\d+)\s*\)\s*(\d+[,.]\d+)")


def _f(s: str) -> float:
    return float(s.replace(",", "."))


@dataclass
class Layer:
    top_depth: float
    bottom_depth: float | None
    head_word: str
    bodenart: str
    bodenart_sure: bool
    full_text: str
    nhn_rel: float | None = None


@dataclass
class Borehole:
    bohr_id: str
    page: int
    x_label: float
    gok_nhn: float | None
    total_depth: float | None
    layers: list[Layer] = field(default_factory=list)
    consolidated: list[Layer] = field(default_factory=list)
    nhn_check_ok: bool | None = None
    nhn_check_msg: str = ""

    @property
    def nhn_bottom(self) -> float | None:
        if self.gok_nhn is not None and self.total_depth is not None:
            return round(self.gok_nhn - self.total_depth, 2)
        return None


# ---------------------------------------------------------------------------
# Header / Spaltenerkennung
# ---------------------------------------------------------------------------
def _header_groups(words):
    numtok = [w for w in words if _NUM_RE.match(w[4])]
    if not numtok:
        return []
    rows: dict[int, list] = {}
    for w in numtok:
        rows.setdefault(round(w[1] / 6), []).append(w)
    hy = max(rows, key=lambda k: len(rows[k]))
    yref = sum(w[1] for w in rows[hy]) / len(rows[hy])
    line = sorted((w for w in words if abs(w[1] - yref) < 12), key=lambda w: w[0])

    groups = []
    cur: list = []
    for w in line:
        if _NUM_RE.match(w[4]):
            cur.append(w)
            prefixes = [t[4] for t in cur[:-1] if t[4] in _PREFIX_TOKENS]
            btok = [t for t in cur if t[4] == "B"]
            g = {
                "prefixes": prefixes,
                "num": w[4],
                "xleft": cur[0][0],
                "x_label": btok[0][0] if btok else cur[0][0],
                "yref": yref,
            }
            pfx = set(prefixes)
            if "GWM" in pfx:
                g["type"] = "gwm"
            elif "DS" in pfx:
                g["type"] = "ds"
            elif "BS" in pfx:
                g["type"] = "bs"
            elif "B" in pfx:
                g["type"] = "borehole"
                g["id"] = "B " + w[4]
            else:
                g["type"] = "other"
            groups.append(g)
            cur = []
        elif w[4] in _PREFIX_TOKENS:
            cur.append(w)
        else:
            cur = []
    groups.sort(key=lambda g: g["xleft"])
    return groups


# ---------------------------------------------------------------------------
# Eine Bohrung extrahieren
# ---------------------------------------------------------------------------
def _extract_borehole(words, group, next_xleft, page_idx, legend: Legend) -> Borehole:
    xl = group["x_label"]
    d_lo, d_hi = xl + DEPTH_LEFT, xl + DEPTH_RIGHT
    b_lo = xl + BODEN_LEFT
    b_hi = (next_xleft - BODEN_RIGHT_MARGIN) if next_xleft else (xl + 400)

    yref = group["yref"]
    depth_tokens = [w for w in words if d_lo <= w[0] <= d_hi and w[1] > yref + 5]
    boden_tokens = [w for w in words if b_lo <= w[0] <= b_hi and w[1] > yref + 5]

    bh = Borehole(bohr_id=group["id"], page=page_idx, x_label=xl,
                  gok_nhn=None, total_depth=None)

    # GOK-Marker (oberster NHN+x,xxm in der Tiefenspalte)
    gok_y = None
    gok_candidates = []
    for w in depth_tokens:
        m = _GOK_RE.search(w[4])
        if m:
            gok_candidates.append((w[1], _f(m.group(1))))
    if gok_candidates:
        gok_candidates.sort()
        gok_y, bh.gok_nhn = gok_candidates[0]

    # Tiefen-Paare: pro Y-Zeile zusammenfuegen und Pattern matchen
    drows: dict[int, list] = {}
    for w in depth_tokens:
        drows.setdefault(round(w[1] / 4), []).append(w)
    boundaries = []  # (y, depth, nhn_rel)
    for key in sorted(drows):
        toks = sorted(drows[key], key=lambda t: t[0])
        text = " ".join(t[4] for t in toks)
        ycen = sum(t[1] for t in toks) / len(toks)
        m = _PAIR_RE.search(text)
        if m:
            nhn_rel = _f(m.group(1))
            tiefe = _f(m.group(2))
            boundaries.append((ycen, tiefe, nhn_rel))

    if not boundaries:
        return bh

    # Boundary-Liste in Page-Y-Reihenfolge inkl. GOK (Tiefe 0)
    boundaries.sort(key=lambda b: b[0])
    if gok_y is None:
        # Fallback: oberste Boundary-Y minus etwas
        gok_y = boundaries[0][0] - 20
    pts = [(gok_y, 0.0, bh.gok_nhn)] + boundaries

    bh.total_depth = max(b[1] for b in boundaries)

    # Intervalle -> Schichten
    layers = []
    for i in range(len(pts) - 1):
        y_top, d_top, _ = pts[i]
        y_bot, d_bot, _ = pts[i + 1]
        seg = [w for w in boden_tokens if y_top - 2 <= w[1] < y_bot - 2]
        seg.sort(key=lambda t: (round(t[1] / 4), t[0]))
        if not seg:
            continue
        tokens = _join_hyphen([t[4] for t in seg])
        full_text = " ".join(tokens)
        head_word, cls, sure = _classify_segment(tokens, legend)
        if not sure and layers:
            # Kein eindeutiges Bodenart-Wort -> Fortsetzung der vorigen Schicht
            # (interner Tiefen-Tick innerhalb einer Beschreibung)
            head_word = layers[-1].head_word
            cls = layers[-1].bodenart
        layers.append(Layer(top_depth=round(d_top, 2), bottom_depth=round(d_bot, 2),
                            head_word=head_word, bodenart=cls, bodenart_sure=sure,
                            full_text=full_text, nhn_rel=pts[i + 1][2]))
    bh.layers = layers
    bh.consolidated = _consolidate(layers)

    # NHN-Validierung
    deepest = max(boundaries, key=lambda b: b[1])
    if bh.gok_nhn is not None:
        expected = round(bh.gok_nhn - deepest[1], 2)
        diff = abs(expected - deepest[2])
        bh.nhn_check_ok = diff < 0.06
        bh.nhn_check_msg = (
            f"GOK {bh.gok_nhn:+.2f} - Tiefe {deepest[1]:.2f} = {expected:+.2f} "
            f"(PDF: {deepest[2]:+.2f}) Δ={diff:.2f}"
        )
    return bh


_NOISE_HEAD = {"m", "gw", "tm", "w", "vz", "org", "durch", "bis", "und", "mit",
               "in", "von", "der", "ca", "endtiefe", "kerne", "kernverlust"}


def _join_hyphen(tokens: list[str]) -> list[str]:
    """Verbindet getrennte Woerter ('Mittel-' + 'sand' -> 'Mittelsand')."""
    out: list[str] = []
    skip = False
    for i, t in enumerate(tokens):
        if skip:
            skip = False
            continue
        if t.endswith("-") and i + 1 < len(tokens) and tokens[i + 1][:1].islower():
            out.append(t[:-1] + tokens[i + 1])
            skip = True
        else:
            out.append(t)
    return out


def _classify_segment(tokens: list[str], legend: Legend):
    """Sucht das erste eindeutig klassifizierbare Bodenart-Wort im Segment."""
    # 1) erstes Token mit sicherer Klassifikation
    for w in tokens:
        hw = soil.normalize_head(w)
        if not hw or not hw[0].isalpha() or len(hw) < 2:
            continue
        cls, sure = soil.classify(hw, legend.bodenarten)
        if sure:
            return hw, cls, True
    # 2) erstes 'soil-aehnliches' Wort (gross, kein Rauschwort) -> unsicher
    for w in tokens:
        hw = soil.normalize_head(w)
        if (hw and hw[0].isupper() and len(hw) > 1
                and hw.lower() not in _NOISE_HEAD):
            cls, sure = soil.classify(hw, legend.bodenarten)
            return hw, cls, sure
    return "", "", False


def layer_at_depth(borehole: "Borehole", depth: float) -> Layer | None:
    """Konsolidierte Schicht, in der eine Tiefe (ab GOK) liegt.

    Wird genutzt, um die 'Bodenart auf Tunnel' aus dem Bohrprofil abzuleiten
    (nicht aus dem Laengsschnitt): die Tiefe der Tunnelachse unter GOK faellt in
    genau eine Schicht (Oberkante <= Tiefe < Unterkante).
    """
    best = None
    for ly in borehole.consolidated:
        top = ly.top_depth
        bot = ly.bottom_depth if ly.bottom_depth is not None else (borehole.total_depth or top)
        if top <= depth < bot:
            return ly
        if top <= depth:
            best = ly      # tiefer als die letzte Unterkante -> tiefste Schicht
    return best


def composition_in_range(borehole: "Borehole", d1: float, d2: float) -> dict:
    """Bodenart-Anteile (%) ueber einen Tiefenbereich nach Maechtigkeit.

    Fuer den Tunnelquerschnitt [OK-Tiefe .. Sohle-Tiefe] am Bohrpunkt -> liefert
    den prozentualen Anteil jeder Bodenart, die der Tunnel dort durchfaehrt.
    """
    from collections import defaultdict
    lo, hi = (d1, d2) if d1 <= d2 else (d2, d1)
    acc: dict[str, float] = defaultdict(float)
    for ly in borehole.consolidated:
        top = ly.top_depth
        bot = ly.bottom_depth if ly.bottom_depth is not None else (borehole.total_depth or top)
        ov = min(hi, bot) - max(lo, top)
        if ov > 0:
            acc[ly.bodenart] += ov
    total = sum(acc.values())
    if total <= 0:
        return {}
    return {k: round(v / total * 100) for k, v in sorted(acc.items(), key=lambda kv: -kv[1])}


def _consolidate(layers: list[Layer]) -> list[Layer]:
    """Aufeinanderfolgende gleiche grobe Bodenarten zu einer Schicht."""
    out: list[Layer] = []
    for ly in layers:
        if out and out[-1].bodenart == ly.bodenart:
            out[-1].bottom_depth = ly.bottom_depth
            out[-1].full_text += " | " + ly.full_text
            # Klasse ist sicher, sobald mindestens ein Teil sie bestaetigt hat
            out[-1].bodenart_sure = out[-1].bodenart_sure or ly.bodenart_sure
        else:
            out.append(Layer(top_depth=ly.top_depth, bottom_depth=ly.bottom_depth,
                             head_word=ly.head_word, bodenart=ly.bodenart,
                             bodenart_sure=ly.bodenart_sure, full_text=ly.full_text,
                             nhn_rel=ly.nhn_rel))
    return out


# ---------------------------------------------------------------------------
# Oeffentliche API
# ---------------------------------------------------------------------------
def parse_bohrprofil(doc: fitz.Document, legend: Legend) -> list[Borehole]:
    boreholes: list[Borehole] = []
    for pi in range(doc.page_count):
        page = doc[pi]
        words = page.get_text("words")
        groups = _header_groups(words)
        if not groups:
            continue
        xlefts = [g["xleft"] for g in groups]
        for gi, g in enumerate(groups):
            if g["type"] != "borehole":
                continue
            next_xleft = None
            for x in xlefts:
                if x > g["xleft"] + 1:
                    next_xleft = x
                    break
            bh = _extract_borehole(words, g, next_xleft, pi, legend)
            if bh.layers:
                boreholes.append(bh)
    return boreholes
