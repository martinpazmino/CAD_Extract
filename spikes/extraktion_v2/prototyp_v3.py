"""Prototyp v3: Iteration nach den ersten echten Gutachten (Wachenroth, Talheim).

Was die echten PDFs anders machen als die synthetischen (und was v3 deshalb aendert):
  * Ghostscript/PDF24-Exporte zerlegen alles in Einzelsegmente, ohne Fuellungen
      -> alles (Linien, Rechtecke, Quads) wird zu Segmenten; Saeule = Paar senkrechter
         Kanten, Schichtgrenzen = waagrechte Segmente ueber die volle Saeulenbreite
  * Saeulenraender stueckweise je Schicht gezeichnet, weisse Textmasken ueberall
      -> kollineare Segmente zusammenfuegen; nur gestrichene Kanten bilden Raender
  * Gedrehte Seiten (/Rotate 90): PyMuPDF liefert unrotierte Koordinaten
      -> alle Woerter und Pfade mit page.rotation_matrix in Ansichtskoordinaten
  * Tiefenlabels mit Hinweislinien versetzt (nicht auf Hoehe der Grenze) und je Buero
    mal Oberkante (mit 0,00), mal Unterkante
      -> Zuordnung Label <-> Grenze ueber die REIHENFOLGE, Massstab per Regression
         ueber die Paare; direkte Zuordnung nur, wenn die Labels auf den Linien sitzen
  * GW-Symbol neben der Nachbarsaeule, mit Wasserlinie zur eigenen Saeule
      -> Zuordnung ueber das Ende der waagrechten Wasserlinie
  * 'kein Grundwasser' als ausdruecklicher Befund
  * Fels (Sandstein, Tonstein) und Kuenstliches (Beton, Schwarzdecke) wurden von v1
    als Sand/Steine/Ton klassifiziert -> Substantiv-Regel + Fels/Anthropogen-Liste
  * Dieselbe Bohrung auf Einzelblatt und im Schnitt -> nach ID zusammenfuehren,
    das Blatt mit dem groessten Massstab behalten

Nach dem Blindtest (Hausham/DC-Software, Rednitzhembach/Scan; v3 blind 0/13):
  * Labels mit Einheit ('0.20m'), 'Kein Wasser', GW als Text ('GW 2.53m')
  * Nicht-Normmassstab zulaessig, wenn >= 80 % von >= 3 Labels ihn bestaetigen (DC skaliert seitenfuellend)
  * Hoehenleisten-Dreiecke, Dreiecke mit Kote daneben und GOK-Marke sind kein Grundwasser
  * Scans: Segmente aus dem Bild (OpenCV-Morphologie) + OCR-Textlage, Doppellinien zusammenfuehren
  * Duplikate: Blatt mit Schriftfeld 'Bohrung B 4' / Einzelblatt bevorzugen

Achtung: alle Zahlen nach einer Korrektur sind Trainingszahlen (docs/15).
"""
from __future__ import annotations

import itertools
import re
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prototyp_v2 import (DATE_RE, GOK_RE, PT_TO_M_AT_1_1, classify_hatch, coordinate_table,  # noqa: E402
                         hatch_features, soil, soundings)

ID_RE = re.compile(r"^(B|BK|KB|KRB|RKS|BS|GWM|SCH)\s*(\d+[a-z]?)(/\d{2})?$")
DEPTH_RE = re.compile(r"^\d{1,3}[.,]\d{1,2}\s?m?$")              # DC-Software: '0.20m'
GW_TEXT_RE = re.compile(r"\bGW\b.*?(\d{1,3}[.,]\d{1,2})\s?m\b|(\d{1,3}[.,]\d{1,2})\s?m\s*u\.?\s*GOK", re.I)
SCALE_RE = re.compile(r"(?:M(?:a(?:ss|ß)stab)?\.?|H(?:ö|oe)hen-?Ma(?:ss|ß)stab)?\s*1\s*:\s*(\d{2,4})\b")
NO_GW_RE = re.compile(r"kein(?:\s+|e\s+)(?:Grund)?wasser|GW\s+nicht\s+angetroffen|trocken", re.I)
ROCK_SUFFIX = ("stein", "fels")
ANTHROPOGEN = {"beton": "Beton", "asphalt": "Asphalt", "schwarzdecke": "Schwarzdecke",
               "pflaster": "Pflaster", "anschuettung": "Auffuellung", "anschüttung": "Auffuellung",
               "auffuellung": "Auffuellung", "auffüllung": "Auffuellung", "schotter": "Auffuellung"}
TOPSOIL = {"oberboden", "mutterboden"}
STANDARD_SCALES = (10, 20, 25, 33, 50, 75, 100, 125, 150, 200, 250, 500, 1000)


def plausible_scale(m: float, tol: float = 0.04) -> bool:
    """Zeichnungen verwenden Normmassstaebe; M 1:12 aus einer Tabelle ist ein Fehlalarm."""
    return any(abs(m - s) <= tol * s for s in STANDARD_SCALES)


# ---------------------------------------------------------------------------
# Primitive in Ansichtskoordinaten
# ---------------------------------------------------------------------------
@dataclass
class Seg:
    x0: float
    y0: float
    x1: float
    y1: float
    width: float
    stroked: bool
    dashed: bool = False

    @property
    def horizontal(self) -> bool:
        return abs(self.y1 - self.y0) < 0.3

    @property
    def vertical(self) -> bool:
        return abs(self.x1 - self.x0) < 0.3


def _xform_drawing(d: dict, m: pymupdf.Matrix) -> dict:
    items = []
    for it in d["items"]:
        op = it[0]
        if op == "re":
            items.append(("re", pymupdf.Rect(it[1]) * m))
        elif op == "qu":
            items.append(("qu", pymupdf.Quad(it[1]) * m))
        else:
            items.append((op, *[p * m if hasattr(p, "x") else p for p in it[1:]]))
    return {**d, "items": items, "rect": pymupdf.Rect(d["rect"]) * m}


def raster_segments(page: pymupdf.Page, dpi: int = 200) -> list[Seg]:
    """Gescannte Seite: waagrechte/senkrechte Linien per Morphologie aus dem Bild (wie swissgeol strip logs).

    Liefert dieselben Seg-Objekte wie der Vektorweg, damit Saeulen-/Grenzlogik unveraendert bleibt.
    """
    try:
        import cv2
    except ImportError:                                  # optional: ohne OpenCV kein Rasterweg
        return []
    pix = page.get_pixmap(dpi=dpi, colorspace=pymupdf.csGRAY)
    img = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w)
    binary = (img < 150).astype(np.uint8)
    k = max(15, int(dpi * 0.12))                         # ~3 mm Mindestlaenge
    f = 72.0 / dpi
    out = []
    for kernel, horizontal in ((np.ones((1, k), np.uint8), True), (np.ones((k, 1), np.uint8), False)):
        lines = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel)
        n, _, stats, _ = cv2.connectedComponentsWithStats(lines)
        for x, y, w, h, _area in stats[1:n]:
            if horizontal and h <= 10:                  # Scan: Linien sind 2-4x breiter als im Vektor
                yc = (y + h / 2) * f
                out.append(Seg(x * f, yc, (x + w) * f, yc, h * f, True))
            elif not horizontal and w <= 10:
                xc = (x + w / 2) * f
                out.append(Seg(xc, y * f, xc, (y + h) * f, w * f, True))
    return out


def primitives(page: pymupdf.Page):
    m = page.rotation_matrix
    words = [(pymupdf.Rect(w[:4]) * m, w[4], w[5], w[6]) for w in page.get_text("words")]
    drawings = [_xform_drawing(d, m) for d in page.get_drawings()]
    segs: list[Seg] = []
    area = page.rect.width * page.rect.height
    scanned = len(drawings) < 5 and sum(pymupdf.Rect(i["bbox"]).get_area() for i in page.get_image_info()) > 0.8 * area
    if scanned:                                          # Scan mit OCR-Textlage: Linien aus dem Bild
        segs = raster_segments(page)
    for d in ([] if scanned else drawings):
        stroked = d.get("color") is not None and "s" in d.get("type", "")
        fill = d.get("fill")
        coloured_fill = fill is not None and min(fill) < 0.97          # weisse Masken ignorieren
        if not stroked and not coloured_fill:
            continue
        w = d.get("width") or 0.0
        dashed = d.get("dashes") not in (None, "[] 0", "[] 0.0")
        for it in d["items"]:
            if it[0] == "l":
                pts = [(it[1], it[2])]
            elif it[0] == "re":
                r = it[1]
                pts = [(r.tl, r.tr), (r.tr, r.br), (r.br, r.bl), (r.bl, r.tl)]
            elif it[0] == "qu":
                q = it[1]
                pts = [(q.ul, q.ur), (q.ur, q.lr), (q.lr, q.ll), (q.ll, q.ul)]
            else:
                continue
            for a, b in pts:
                segs.append(Seg(min(a.x, b.x), min(a.y, b.y), max(a.x, b.x), max(a.y, b.y), w, stroked, dashed))
    lines: dict[tuple, list] = defaultdict(list)
    for r, t, b, ln in words:
        lines[(b, ln)].append((r, t))
    text_lines = []
    for ws in lines.values():
        ws.sort(key=lambda x: (x[0].y0, x[0].x0))
        r = pymupdf.Rect(ws[0][0])
        for q, _ in ws[1:]:
            r |= q
        text_lines.append((r, " ".join(t for _, t in ws)))
    return words, text_lines, drawings, segs, scanned


def _merge(segs: list[Seg], axis: str, gap: float = 1.5) -> list[Seg]:
    """Kollineare Segmente (gleiche y bzw. x) zu durchgehenden Linien zusammenfuegen."""
    groups: dict[float, list[Seg]] = defaultdict(list)
    for s in segs:
        groups[round((s.y0 if axis == "h" else s.x0) * 2) / 2].append(s)
    out = []
    for key, ss in groups.items():
        ss.sort(key=lambda s: s.x0 if axis == "h" else s.y0)
        cur = ss[0]
        lo, hi, w, st = (cur.x0, cur.x1, cur.width, cur.stroked) if axis == "h" else (cur.y0, cur.y1, cur.width, cur.stroked)
        for s in ss[1:]:
            a, b = (s.x0, s.x1) if axis == "h" else (s.y0, s.y1)
            if a <= hi + gap:
                hi, w, st = max(hi, b), max(w, s.width), st or s.stroked
            else:
                out.append(Seg(lo, key, hi, key, w, st) if axis == "h" else Seg(key, lo, key, hi, w, st))
                lo, hi, w, st = a, b, s.width, s.stroked
        out.append(Seg(lo, key, hi, key, w, st) if axis == "h" else Seg(key, lo, key, hi, w, st))
    return out


# ---------------------------------------------------------------------------
# Saeulen aus Kantenpaaren
# ---------------------------------------------------------------------------
@dataclass
class Column:
    rect: pymupdf.Rect
    bounds: list[float]          # y aller Grenzen inkl. Ober- und Unterkante
    weight: float                # Strichstaerke der Raender


def find_columns(segs: list[Seg], wmin=8, wmax=80, min_ratio=2.5, merge_tol=0.8) -> list[Column]:
    # Schraffurlinien (gestrichelt oder knapp innerhalb der Raender) sind keine Schichtgrenzen
    H = _merge([s for s in segs if s.horizontal and s.x1 - s.x0 >= 3 and not s.dashed], "h")
    V = [v for v in _merge([s for s in segs if s.vertical and s.y1 - s.y0 >= 3 and s.stroked], "v")
         if v.y1 - v.y0 >= 30]
    V.sort(key=lambda v: v.x0)
    cols = []
    for a, b in itertools.combinations(V, 2):
        w = b.x0 - a.x0
        if not (wmin <= w <= wmax):
            continue
        y0, y1 = max(a.y0, b.y0), min(a.y1, b.y1)
        h = y1 - y0
        if h < min_ratio * w or h < 0.9 * min(a.y1 - a.y0, b.y1 - b.y0):
            continue
        ys = sorted(s.y0 for s in H if s.x0 <= a.x0 + 0.6 and s.x1 >= b.x0 - 0.6 and y0 - 1 <= s.y0 <= y1 + 1)
        bounds = []
        for y in [y0] + ys + [y1]:
            if not bounds or y - bounds[-1] > merge_tol:
                bounds.append(y)
            elif y == y1:
                bounds[-1] = y1                               # doppelte Unterkante -> eine Grenze
        cols.append(Column(pymupdf.Rect(a.x0, y0, b.x0, y1), bounds, min(a.width, b.width)))
    # verschachtelte Kandidaten (Innenstreifen, Rohr einer GWM) -> den mit kraeftigeren Raendern behalten
    cols.sort(key=lambda c: (-round(c.weight, 1), -len(c.bounds), -c.rect.width))
    kept: list[Column] = []
    for c in cols:
        if not any(k.rect.x0 - 1 <= c.rect.x0 and c.rect.x1 <= k.rect.x1 + 1 and
                   min(k.rect.y1, c.rect.y1) - max(k.rect.y0, c.rect.y0) > 0.8 * c.rect.height for k in kept):
            kept.append(c)
    return kept


# ---------------------------------------------------------------------------
# Klassifikation: Substantiv, Fels, Anthropogen
# ---------------------------------------------------------------------------
def classify_v3(text: str) -> str:
    for raw in re.findall(r"[A-Za-zÄÖÜäöüß]+", text):
        w = raw.lower()
        if not raw[0].isupper() or w.endswith(("ig", "haltig", "lich")):
            continue                                   # nur Substantive
        if w in TOPSOIL:
            return "Mutterboden"
        if w in ANTHROPOGEN:
            return ANTHROPOGEN[w]
        if w.endswith(ROCK_SUFFIX) and w != "steine":
            return f"Fels ({raw})"
        cls, sure = soil.classify(raw)
        if sure:
            return cls
    return ""


# ---------------------------------------------------------------------------
# Tiefen: Labels finden und den Grenzen zuordnen
# ---------------------------------------------------------------------------
def label_groups(words, col: Column, cols: list[Column]):
    """Dezimalzahlen-Spalten, die dieser Saeule am naechsten liegen (nicht einer Nachbarsaeule)."""
    def hdist(r, c):
        return max(c.rect.x0 - r.x1, r.x0 - c.rect.x1, 0)
    cands = []
    for r, t, *_ in words:
        if not DEPTH_RE.match(t) or float(t.rstrip("m ").replace(",", ".")) > 150:
            continue
        cy = (r.y0 + r.y1) / 2
        if not (col.rect.y0 - 8 <= cy <= col.rect.y1 + 150) or hdist(r, col) > 110:
            continue
        near = [c for c in cols if c.rect.y0 - 8 <= cy <= c.rect.y1 + 150]
        if min(near, key=lambda c: hdist(r, c)) is not col:
            continue
        cands.append((r, float(t.rstrip("m ").replace(",", "."))))
    groups: dict[int, list] = defaultdict(list)
    for r, v in cands:
        groups[round(r.x0 / 4)].append((r, v))
    out = []
    for g in groups.values():
        g.sort(key=lambda e: e[0].y0)
        g = _longest_non_decreasing(g)                    # versprengte Zahlen (andere Texte) entfernen
        if len(g) >= 2:
            out.append(g)
    return sorted(out, key=lambda g: (-len(g), hdist(g[0][0], col)))


def _longest_non_decreasing(g):
    best = [[e] for e in g]
    for i in range(len(g)):
        for j in range(i):
            if g[j][1] <= g[i][1] and len(best[j]) + 1 > len(best[i]):
                best[i] = best[j] + [g[i]]
    return max(best, key=len) if best else []


def label_support(col: Column, labels, a: float, b: float, tol: float = 0.03) -> int:
    """Wie viele Labelwerte werden von irgendeiner Grenze (Tiefe = a*y+b) bestaetigt?"""
    depths = [a * y + b for y in col.bounds]
    return sum(any(abs(d - v) <= tol for d in depths) for _, v in labels)


def choose_scale(col: Column, groups, scale_txt: list[int]):
    """Kandidaten: direkt, Reihenfolge (je Labelgruppe) und Massstabstext; Auswahl nach Bestaetigung."""
    cands = []
    for g in groups:
        f = fit_depths(col, g)
        if not f:
            continue
        sup = label_support(col, g, f[0], f[1])
        # Normmassstab ODER starke Bestaetigung (DC-Software skaliert Profile seitenfuellend, z. B. 1:35)
        if plausible_scale(f[0] / PT_TO_M_AT_1_1) or (len(g) >= 3 and sup >= 0.8 * len(g)):
            cands.append((sup, f[2], f[0], f[1], f[3], g))
    for m in sorted(set(scale_txt)):
        a = m * PT_TO_M_AT_1_1
        b = -a * col.bounds[0]
        g = groups[0] if groups else []
        pairs = [(y, v) for _, v in g for y in col.bounds if abs(a * y + b - v) <= 0.03]
        cands.append((label_support(col, g, a, b), "massstab-text", a, b, pairs, g))
    if not cands:
        return None
    prio = {"direkt": 2, "reihenfolge": 1, "massstab-text": 0}
    best = max(cands, key=lambda c: (c[0], prio[c[1]]))
    return best[2], best[3], best[1], best[4], best[0], len(best[5])


def fit_depths(col: Column, labels):
    """Liefert (a, b, modus, paare): Tiefe = a*y + b."""
    B = col.bounds
    # direkt: Label sitzt auf der Grenzlinie (Grundlinie oder Mitte)
    direct = []
    for r, v in labels:
        y = min(B, key=lambda yb: min(abs(r.y1 - yb), abs((r.y0 + r.y1) / 2 - yb)))
        if min(abs(r.y1 - y), abs((r.y0 + r.y1) / 2 - y)) <= 4.5:
            direct.append((y, v))
    if len(direct) >= max(2, 0.6 * len(labels)):
        pts = [(B[0], 0.0)] + [p for p in direct if p[0] != B[0]]
        a, b = np.polyfit([p[0] for p in pts], [p[1] for p in pts], 1)
        if a > 0:
            return a, b, "direkt", direct
    # Reihenfolge: k-tes Label <-> k-te Grenze, ueberzaehlige Grenzen/Labels testweise weglassen
    vals = sorted(v for _, v in labels)
    best = None
    for drop_b in range(0, 4):
        for keep in itertools.combinations(range(len(B)), len(B) - drop_b):
            yb = [B[i] for i in keep]
            for vv in (vals, [v for v in vals if v > 0]):
                if len(vv) != len(yb) or len(vv) < 2:
                    continue
                if vv[0] > 0:                                   # Unterkanten -> Oberkante = 0 dazu
                    if B[0] in yb:
                        continue
                    yy, vvv = [B[0]] + yb, [0.0] + vv
                else:
                    yy, vvv = yb, vv
                a, b = np.polyfit(yy, vvv, 1)
                res = float(np.max(np.abs(np.polyval([a, b], yy) - vvv)))
                if a > 0 and (best is None or res < best[0]):
                    best = (res, a, b, list(zip(yy, vvv)))
        if best and best[0] < 0.03:
            break
    if best and best[0] < 0.06:
        return best[1], best[2], "reihenfolge", best[3]
    return None


# ---------------------------------------------------------------------------
# Datenklassen
# ---------------------------------------------------------------------------
@dataclass
class Layer:
    top: float
    bottom: float
    soil: str = ""
    soil_hatch: str = ""
    label_confirmed: bool = False
    issues: list[str] = field(default_factory=list)


@dataclass
class Borehole:
    code: str
    page: int
    scale: float | None
    mode: str
    gok: float | None = None
    layers: list[Layer] = field(default_factory=list)
    gw_depths: list[float] = field(default_factory=list)
    gw_status: str | None = None
    east: float | None = None
    north: float | None = None
    duplicates: list[str] = field(default_factory=list)
    support: float = 0.0
    single_sheet: bool = False
    titled: bool = False


def _groundwater(drawings, segs, col: Column, cols: list[Column], fit, words=()):
    """Dreieck mit Spitze nach unten; Zuordnung ueber die waagrechte Wasserlinie."""
    a, b = fit
    H = [s for s in segs if s.horizontal]
    out = []
    # Hoehenleisten tragen ein Dreieck je Meter: >= 3 gleich ausgerichtete Dreiecke in einer Spalte = Leiste
    tri_x = defaultdict(int)
    for d in drawings:
        it, r = d["items"], d["rect"]
        if len(it) == 3 and all(x[0] == "l" for x in it) and 3 < r.width < 16 and 3 < r.height < 16:
            tri_x[round(r.x0)] += 1
    ruler_x = {x for x, n in tri_x.items() if n >= 3}
    for d in drawings:
        it = d["items"]
        r = d["rect"]
        if not (len(it) == 3 and all(x[0] == "l" for x in it) and 3 < r.width < 16 and 3 < r.height < 16):
            continue
        if any(abs(round(r.x0) - x) <= 1 for x in ruler_x):
            continue
        # Hoehenmarke: Dreieck mit Kote daneben ('741.00m', '~770,17')
        if any(abs((wr.y0 + wr.y1) / 2 - (r.y0 + r.y1) / 2) < 5 and 0 < wr.x0 - r.x1 < 70
               and re.fullmatch(r"~?\d{3,4}[.,]\d{2}\s?m?", t) for wr, t, *_ in words):
            continue
        pts = [x[1] for x in it]
        apex = max(pts, key=lambda p: p.y)
        if sum(abs(p.y - apex.y) < 0.5 for p in pts) != 1 or not (col.rect.y0 <= apex.y <= col.rect.y1 + 2):
            continue
        target = None
        for s in H:                                         # Wasserlinie an der Spitze
            if abs(s.y0 - apex.y) < 1.5 and s.x0 - 2 <= apex.x <= s.x1 + 2 and s.x1 - s.x0 > 15:
                end = s.x1 if abs(s.x1 - apex.x) > abs(s.x0 - apex.x) else s.x0
                target = min(cols, key=lambda c: min(abs(c.rect.x0 - end), abs(c.rect.x1 - end)))
        if target is None:
            target = min(cols, key=lambda c: max(c.rect.x0 - r.x1, r.x0 - c.rect.x1, 0))
        if target is col:
            depth = round(float(a * apex.y + b), 2)
            if depth > 0.05:                                # Dreieck an der GOK = Ansatzpunkt, kein Wasser
                out.append(depth)
    return sorted(set(out))


def extract(pdf: Path):
    doc = pymupdf.open(pdf)
    swatches = []
    found: dict[str, list[Borehole]] = defaultdict(list)
    dph = {}
    for pno, page in enumerate(doc):
        words, lines, drawings, segs, scanned = primitives(page)
        if any("BODENARTEN" in t.upper() for _, t in lines) and not swatches:
            from prototyp_v2 import legend_swatches
            swatches = legend_swatches(page)
        if page.rotation == 0:
            dph.update(soundings(page))
        cols = find_columns(segs, merge_tol=1.6 if scanned else 0.8)   # Scans zeichnen Linien doppelt
        scale_txt = [int(m) for _, t in lines for m in SCALE_RE.findall(t)]
        heads = [(r, re.sub(r"\s+", " ", t.strip())) for r, t in lines if ID_RE.match(re.sub(r"\s+", " ", t.strip()))]
        anchored: list[tuple] = []
        used = set()
        for hr, code in heads:
            hx = (hr.x0 + hr.x1) / 2
            # bei hoehenmaessiger Darstellung steht der Kopf weit ueber der Saeule -> keine y-Grenze
            cand = [c for c in cols if c.rect.y0 > hr.y1 and abs((c.rect.x0 + c.rect.x1) / 2 - hx) < 70
                    and id(c) not in used]
            if not cand:
                continue
            col = max(cand, key=lambda c: (round(c.weight, 1), len(c.bounds), -(c.rect.y0 - hr.y1),
                                           -abs((c.rect.x0 + c.rect.x1) / 2 - hx)))
            used.add(id(col))
            anchored.append((hr, code, col))
        # Tabellen aussortieren: in einer Bodensaeule stehen hoechstens kurze Kuerzel, keine Zahlenreihen
        anchored = [(hr, code, c) for hr, code, c in anchored
                    if sum(1 for r, t, *_ in words if c.rect.contains(r) and re.search(r"\d", t)) <= 2]
        acols = [c for _, _, c in anchored]
        for hr, code, col in anchored:
            hx = (hr.x0 + hr.x1) / 2
            gok = None
            for r, t in lines:
                if hr.y0 - 2 <= r.y0 <= col.rect.y0 + 4 and abs((r.x0 + r.x1) / 2 - hx) < 90 and (m := GOK_RE.search(t)):
                    gok = float((m.group(1) or m.group(2)).replace(",", "."))
            chosen = choose_scale(col, label_groups(words, col, acols), scale_txt)
            if chosen is None:
                continue
            a, b, mode, pairs, support, n_labels = chosen
            fit = (a, b)
            bh = Borehole(code, pno + 1, round(a / PT_TO_M_AT_1_1), f"{mode} ({support}/{n_labels} Labels)", gok)
            bh.support = support / n_labels if n_labels else 0.0
            bh.single_sheet = len(anchored) == 1                  # Einzelblatt schlaegt Schnitt/Uebersicht
            bh.titled = any(re.search(rf"(Bohrung|Bohrprofil|Profil|Sondierung)\s+{re.escape(code)}\b", t)
                            for _, t in lines)                     # Schriftfeld 'Bohrung B 4' 
            prev = 0.0
            depths = [round(float(a * y + b), 2) for y in col.bounds[1:]]
            confirmed = set()                                   # 1:1 - jedes Label bestaetigt nur die naechste Grenze
            for v in {round(v, 2) for _, v in pairs}:
                i = min(range(len(depths)), key=lambda k: abs(depths[k] - v), default=None)
                if i is not None and abs(depths[i] - v) <= 0.03:
                    confirmed.add(i)
            for i, y in enumerate(col.bounds[1:]):
                d = depths[i]
                ly = Layer(prev, d, label_confirmed=i in confirmed)
                if not ly.label_confirmed:
                    ly.issues.append("Grenze ohne bestaetigendes Label")
                rect = pymupdf.Rect(col.rect.x0, a and (prev - b) / a, col.rect.x1, y)
                ly.soil_hatch, _ = classify_hatch(hatch_features(drawings, rect), swatches) if swatches else ("", 0)
                bh.layers.append(ly)
                prev = d
            right_limit = min([c.rect.x0 for c in acols if c.rect.x0 > col.rect.x1 + 5] + [page.rect.x1])
            _assign_text(bh, col, lines, words, fit, mode, pairs, right_limit)
            bh.gw_depths = _groundwater(drawings, segs, col, acols, fit, words)
            near = [(r, t) for r, t in lines if hr.y0 - 2 <= r.y0 <= col.rect.y1 + 60
                    and abs((r.x0 + r.x1) / 2 - (col.rect.x0 + col.rect.x1) / 2) < 170]
            if not bh.gw_depths:                            # Symbol als Schriftzeichen: 'GW 2.53m' im Text
                bh.gw_depths = sorted({float((m.group(1) or m.group(2)).replace(",", "."))
                                       for _, t in near if (m := GW_TEXT_RE.search(t))})
            if not bh.gw_depths and any(NO_GW_RE.search(t) for _, t in near):
                bh.gw_status = "kein Grundwasser"
            found[code].append(bh)
    coords = coordinate_table(doc)
    out = []
    for code, versions in found.items():
        # GOK gefunden, Labels bestaetigen, groesster Massstab (= kleinste Zahl)
        # schwache Bestaetigung (< 50 %) zaehlt nicht mehr als keine
        best = max(versions, key=lambda v: (v.gok is not None, v.titled, v.single_sheet,
                                            round(v.support, 1) if v.support >= 0.5 else 0.0, -(v.scale or 1e9)))
        best.duplicates = [f"S.{v.page} M1:{v.scale}" for v in versions if v is not best]
        if code in coords:
            best.east, best.north = coords[code]
        out.append(best)
    return out, dph


def _assign_text(bh: Borehole, col: Column, lines, words, fit, mode, pairs, right_limit):
    """Beschreibung -> Schicht. Konvention aus den Labels: mit 0,00 = Oberkante, sonst Lage im Intervall."""
    a, b = fit
    by_line: dict[tuple, list] = defaultdict(list)
    for r, t, blk, ln in words:
        if not DEPTH_RE.match(t):                         # Label und Text stehen oft in derselben Zeile
            by_line[(blk, ln)].append((r, t))
    lines = []
    for ws in by_line.values():
        ws.sort(key=lambda x: x[0].x0)
        r = pymupdf.Rect(ws[0][0])
        for q, _ in ws[1:]:
            r |= q
        lines.append((r, " ".join(t for _, t in ws)))
    right = [(r, t) for r, t in lines if col.rect.x1 + 2 < r.x0 < min(col.rect.x1 + 220, right_limit - 5)
             and re.search(r"[A-Za-zÄÖÜäöü]{3}", t) and not DATE_RE.search(t)]
    tops = sorted(v for _, v in pairs)
    if not mode.startswith("direkt") and tops and tops[0] == 0.0:
        lab = sorted([(r, float(t.rstrip("m ").replace(",", "."))) for r, t, *_ in words if DEPTH_RE.match(t)
                      and r.x0 > col.rect.x1 and float(t.rstrip("m ").replace(",", ".")) in tops], key=lambda e: e[0].y0)
        for i, (lr, v) in enumerate(lab):
            nxt = lab[i + 1][0].y0 if i + 1 < len(lab) else lr.y0 + 200
            txt = " ".join(t for r, t in right if lr.y0 - 3 <= r.y0 < nxt - 3 and r.x0 >= lr.x1 - 1)
            for ly in bh.layers:
                if abs(ly.top - v) <= 0.03 and txt:
                    ly.soil = classify_v3(txt.split(",")[0]) or classify_v3(txt)
        return
    for ly in bh.layers:
        y0, y1 = (ly.top - b) / a, (ly.bottom - b) / a
        txt = " ".join(t for r, t in right if y0 - 2 <= (r.y0 + r.y1) / 2 < y1 + 2)
        if txt:
            ly.soil = classify_v3(txt.split(",")[0]) or classify_v3(txt)
