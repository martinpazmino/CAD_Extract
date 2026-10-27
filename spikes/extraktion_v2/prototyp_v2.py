"""Prototyp v2: layout-unabhaengige Bohrprofil-Extraktion aus Vektor-PDFs.

Statt fester Offsets relativ zum 'B'-Token:
  1. Schichtsaeulen   = vertikal gestapelte, gleich breite Rechtecke (Geometrie)
  2. Name / GOK       = Text ueber der Saeule (generische Regex)
  3. Tiefenmassstab   = Regression y -> Tiefe ueber die Tiefenlabels neben der Saeule
                        (Korrelation > 0.95 wie swissgeol 'AAboveBSidebar'); Grenzen kommen
                        aus der Geometrie, Labels bestaetigen sie
  4. Beschreibung     = linksbuendige Textspalte rechts der Saeule, Zuordnung nach y
  5. Schraffur        = Merkmalsvektor je Schicht, kNN gegen die Musterfelder der Legende
  6. Grundwasser      = Dreieck mit Spitze nach unten neben der Saeule + Datum
  7. Sondierung (DPH) = Treppenkurve im Diagramm, Achsen per Regression kalibriert
  8. Koordinaten      = Tabelle (page.find_tables) mit Ost-/Nordwert, UTM-Plausibilitaet

Nur ein Prototyp: Schwellen sind fuer die synthetischen PDFs gewaehlt, nicht kalibriert.
"""
from __future__ import annotations

import math
import re
import sys
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # Repo-Wurzel -> geo_agent
from geo_agent import soil  # noqa: E402

ID_RE = re.compile(r"^(B|BK|KB|RKS|BS|GWM)\s*(\d+[a-z]?)(/\d{2})?$")
SOUNDING_RE = re.compile(r"^(DPH|DPL|DPM|DS|CPT|SRS)\s*(\d+[a-z]?)(/\d{2})?$")
NUM_RE = re.compile(r"^\(?[+-]?\d+[.,]\d{1,2}\)?$")
GOK_RE = re.compile(r"(?:NHN|NN)\s*([+-]?\d+[.,]\d+)\s*m|([+-]?\d+[.,]\d+)\s*m\s*(?:NHN|NN)", re.I)
DATE_RE = re.compile(r"\b(\d{2})\.(\d{2})\.(\d{2,4})\b")
PT_TO_M_AT_1_1 = 25.4 / 72 / 1000                 # 1 pt Papier in m bei M 1:1


def _f(s: str) -> float:
    return float(s.strip("()").replace(",", "."))


# ---------------------------------------------------------------------------
# Datenklassen (Auszug des kanonischen Modells, mit Provenienz)
# ---------------------------------------------------------------------------
@dataclass
class Layer:
    top: float
    bottom: float
    rect: pymupdf.Rect
    text: str = ""
    soil_text: str = ""
    soil_hatch: str = ""
    hatch_sim: float = 0.0
    label_confirmed: bool = False      # Tiefenlabel bestaetigt die Geometrie-Grenze
    issues: list[str] = field(default_factory=list)

    @property
    def soil(self) -> str:
        return self.soil_text or self.soil_hatch

    @property
    def confidence(self) -> float:
        c = 0.4 if self.label_confirmed else 0.2
        c += 0.3 if self.soil_text else 0.0
        c += 0.3 if self.soil_text and self.soil_text == self.soil_hatch else 0.0
        return round(c, 2)


@dataclass
class Borehole:
    code: str
    page: int
    column: pymupdf.Rect
    gok: float | None = None
    scale: float | None = None          # aus der Regression abgeleitet (1:scale)
    fit_r: float | None = None
    layers: list[Layer] = field(default_factory=list)
    gw_depth: float | None = None
    gw_date: str | None = None
    east: float | None = None
    north: float | None = None


# ---------------------------------------------------------------------------
# 1. Schichtsaeulen
# ---------------------------------------------------------------------------
def _closed_rects(drawings) -> list[pymupdf.Rect]:
    out = []
    for d in drawings:
        items = d["items"]
        if d.get("fill") is None:
            continue
        if len(items) == 1 and items[0][0] == "re":
            out.append(pymupdf.Rect(items[0][1]))
        elif len(items) == 4 and all(it[0] == "l" for it in items):     # Rechteck aus 4 Linien
            r = d["rect"]
            if all(abs(it[1].x - it[2].x) < 0.3 or abs(it[1].y - it[2].y) < 0.3 for it in items):
                out.append(pymupdf.Rect(r))
    return out


def find_columns(drawings, tol: float = 0.8) -> list[list[pymupdf.Rect]]:
    groups: dict[tuple, list] = defaultdict(list)
    for r in _closed_rects(drawings):
        if 8 <= r.width <= 80 and r.height >= 2:
            groups[(round(r.x0 / tol), round(r.x1 / tol))].append(r)
    columns = []
    for rects in groups.values():
        rects.sort(key=lambda r: r.y0)
        chain = [rects[0]]
        for r in rects[1:]:
            if abs(r.y0 - chain[-1].y1) <= tol:
                chain.append(r)
            else:
                if len(chain) >= 2:
                    columns.append(chain)
                chain = [r]
        if len(chain) >= 2:
            columns.append(chain)
    return columns


# ---------------------------------------------------------------------------
# Text-Hilfen
# ---------------------------------------------------------------------------
def text_lines(page) -> list[tuple[pymupdf.Rect, str]]:
    lines: dict[tuple, list] = defaultdict(list)
    for w in page.get_text("words"):
        lines[(w[5], w[6])].append(w)
    out = []
    for ws in lines.values():
        ws.sort(key=lambda w: w[0])
        r = pymupdf.Rect(ws[0][:4])
        for w in ws[1:]:
            r |= pymupdf.Rect(w[:4])
        out.append((r, " ".join(w[4] for w in ws)))
    return out


def _header(lines, col: pymupdf.Rect):
    cx = (col.x0 + col.x1) / 2
    best, gok = None, None
    for r, t in lines:
        if col.y0 - 70 < r.y1 <= col.y0 + 1 and r.x0 - 40 < cx < r.x1 + 60:
            if ID_RE.match(t) and (best is None or r.y1 > best[0].y1):
                best = (r, t)
            m = GOK_RE.search(t)
            if m:
                gok = _f(m.group(1) or m.group(2))
    return (best[1] if best else None), gok


# ---------------------------------------------------------------------------
# 3. Tiefenmassstab je Saeule
# ---------------------------------------------------------------------------
def depth_fit(words, col: pymupdf.Rect, chain):
    """Sucht die Tiefenlabel-Spalte neben der Saeule und passt Tiefe = a*y + b an."""
    cands = []
    for w in words:
        t = w[4]
        if not NUM_RE.match(t) or t.startswith("(") or t[0] in "+-":
            continue                                  # (NHN) bzw. +/-NHN sind keine Tiefen
        r = pymupdf.Rect(w[:4])
        if col.y0 - 5 <= (r.y0 + r.y1) / 2 <= col.y1 + 10 and -120 <= r.x0 - col.x1 <= 60:
            cands.append((r, _f(t)))
    # Spalte = links- ODER rechtsbuendig ausgerichtete Zahlen; beide Gruppierungen pruefen
    clusters: dict[tuple, list] = defaultdict(list)
    for r, v in cands:
        clusters[("x0", round(r.x0 / 8))].append((r, v))
        clusters[("x1", round(r.x1 / 8))].append((r, v))
    best = None
    for entries in sorted(clusters.values(), key=len, reverse=True):
        if len(entries) < 3:
            continue
        ys = np.array([(r.y0 + r.y1) / 2 for r, _ in entries])
        vs = np.array([v for _, v in entries])
        if np.std(ys) == 0 or np.std(vs) == 0:
            continue
        rr = float(np.corrcoef(ys, vs)[0, 1])
        dist = min(abs(entries[0][0].x0 - col.x1), abs(col.x0 - entries[0][0].x1))
        if rr > 0.95 and (best is None or (rr, -dist) > (best[0], -best[1])):
            a, b = np.polyfit(ys, vs, 1)
            best = (rr, dist, a, b, entries)
    return best


# ---------------------------------------------------------------------------
# 5. Schraffur
# ---------------------------------------------------------------------------
HATCH_KEYS = ["dot", "circle", "line_0", "line_45", "line_90", "line_135", "dash"]


def hatch_features(drawings, rect: pymupdf.Rect) -> np.ndarray:
    f = Counter()
    for d in drawings:
        if not d["rect"].intersects(rect):
            continue
        if abs(d["rect"].width - rect.width) < 1 and abs(d["rect"].height - rect.height) < 1:
            continue                                   # Rahmen der Schicht selbst
        filled = d.get("fill") is not None
        dashed = d.get("dashes") not in (None, "[] 0")
        for it in d["items"]:
            if it[0] == "l":
                p, q = it[1], it[2]
                if not rect.contains((p + q) / 2):
                    continue
                if dashed:
                    f["dash"] += abs(q - p)
                else:
                    ang = math.degrees(math.atan2(q.y - p.y, q.x - p.x)) % 180
                    f[f"line_{int(((ang + 22.5) % 180) // 45) * 45}"] += abs(q - p)
            elif it[0] == "c":
                p, q = it[1], it[4]
                if rect.contains((p + q) / 2):
                    f["dot" if filled and abs(q - p) < 1.5 else "circle"] += 0.25
    area = max(rect.width * rect.height, 1.0)
    v = np.array([f[k] / area for k in HATCH_KEYS])
    n = np.linalg.norm(v)
    return v / n if n else v


def legend_swatches(page) -> list[tuple[str, np.ndarray]]:
    drawings = page.get_drawings()
    lines = text_lines(page)
    out = []
    for r in _closed_rects(drawings):
        if not (15 <= r.width <= 60 and 8 <= r.height <= 30):
            continue
        for lr, t in lines:
            if 0 < lr.x0 - r.x1 < 40 and r.y0 - 2 <= (lr.y0 + lr.y1) / 2 <= r.y1 + 2 and t[:1].isupper():
                out.append((t.strip(), hatch_features(drawings, r)))
                break
    return out


def classify_hatch(vec, swatches) -> tuple[str, float]:
    if not swatches or not vec.any():
        return "", 0.0
    sims = [(float(vec @ s), name) for name, s in swatches]
    sim, name = max(sims)
    return name, round(sim, 3)


# ---------------------------------------------------------------------------
# 6. Grundwasser
# ---------------------------------------------------------------------------
def groundwater(drawings, lines, col: pymupdf.Rect):
    for d in drawings:
        it = d["items"]
        r = d["rect"]
        if not (len(it) == 3 and all(x[0] == "l" for x in it) and 3 < r.width < 16 and 3 < r.height < 16):
            continue
        if not (col.x0 - 30 < r.x1 and r.x0 < col.x1 + 30 and col.y0 <= r.y1 <= col.y1):
            continue
        pts = [x[1] for x in it]
        apex = max(pts, key=lambda p: p.y)
        if sum(abs(p.y - apex.y) < 0.5 for p in pts) == 1:             # genau eine Spitze unten
            date = None
            for lr, t in lines:
                if abs(lr.y1 - r.y0) < 14 and abs(lr.x0 - r.x0) < 60 and (m := DATE_RE.search(t)):
                    date = m.group(0)
            return apex.y, date
    return None, None


# ---------------------------------------------------------------------------
# 7. Sondierungsdiagramm (DPH)
# ---------------------------------------------------------------------------
def soundings(page) -> dict[str, list[tuple[float, float, float]]]:
    words = page.get_text("words")
    lines = text_lines(page)
    drawings = page.get_drawings()
    out = {}
    for hr, t in lines:
        m = SOUNDING_RE.match(t)
        if not m:
            continue
        # Achse oben: ganze Zahlen in einer Zeile unter dem Titel -> x -> N10
        ticks = [w for w in words if re.fullmatch(r"\d+", w[4]) and hr.y1 < w[1] < hr.y1 + 35
                 and hr.x0 - 20 < w[0] < hr.x0 + 140]
        rows = defaultdict(list)
        for w in ticks:
            rows[round(w[1])].append(w)
        if not rows:
            continue
        row = max(rows.values(), key=len)
        if len(row) < 3:
            continue
        xs = [(w[0] + w[2]) / 2 for w in row]
        ax, bx = np.polyfit(xs, [float(w[4]) for w in row], 1)
        frame = min((d["rect"] for d in drawings if d.get("fill") is None and d["rect"].y0 > hr.y1
                     and d["rect"].x0 - 5 < xs[0] < d["rect"].x1 and d["rect"].height > 100),
                    key=lambda r: r.y0, default=None)
        if frame is None:
            continue
        # Tiefenlineal links vom Rahmen: ganze Zahlen untereinander -> y -> Tiefe
        ruler = [w for w in words if re.fullmatch(r"\d+", w[4]) and frame.x0 - 25 < w[0] < frame.x0
                 and frame.y0 < w[1] < frame.y1]
        if len(ruler) < 3:
            continue
        ys = [(w[1] + w[3]) / 2 for w in ruler]
        ay, by = np.polyfit(ys, [float(w[4]) for w in ruler], 1)
        steps = []
        for d in drawings:
            if d["rect"] in frame and d.get("fill") is None and len(d["items"]) >= 6 and d["rect"] != frame:
                for it in d["items"]:
                    p, q = it[1], it[2]
                    if abs(p.x - q.x) < 0.3 and abs(q.y - p.y) > 1:     # senkrechtes Segment = Stufe
                        steps.append((round(ay * min(p.y, q.y) + by, 2), round(ay * max(p.y, q.y) + by, 2),
                                      round(ax * p.x + bx, 1)))
        out[t] = steps
    return out


# ---------------------------------------------------------------------------
# 8. Koordinaten aus Tabellen
# ---------------------------------------------------------------------------
def coordinate_table(doc) -> dict[str, tuple[float, float]]:
    out = {}
    for page in doc:
        for tab in page.find_tables().tables:
            # Zellinhalt ueber die Zell-BBox lesen: tab.extract() verliert bei Zahlen wie
            # '565 081,64' Leerzeichen und setzt das Komma in eine eigene Zeile
            rows = [[" ".join(w[4] for w in page.get_text("words", clip=c)) if c else None
                     for c in row.cells] for row in tab.rows]
            if not rows:
                continue
            hdr = [(c or "").lower() for c in rows[0]]
            ie = next((i for i, h in enumerate(hdr) if "ost" in h or "rechts" in h or h.startswith("e")), None)
            iN = next((i for i, h in enumerate(hdr) if "nord" in h or "hoch" in h), None)
            if ie is None or iN is None:
                continue
            for row in rows[1:]:
                code = (row[0] or "").strip()
                if not ID_RE.match(code):
                    continue
                try:
                    e = float(re.sub(r"\s", "", row[ie]).replace(",", "."))
                    n = float(re.sub(r"\s", "", row[iN]).replace(",", "."))
                except (TypeError, ValueError):
                    continue
                if e > 10_000_000:                     # Zonenpraefix '32' abschneiden
                    e -= int(e // 1_000_000) * 1_000_000
                if 280_000 < e < 920_000 and 5_200_000 < n < 6_120_000:   # UTM-Bereich Deutschland
                    out[code] = (e, n)
    return out


# ---------------------------------------------------------------------------
# Gesamtablauf
# ---------------------------------------------------------------------------
def extract(pdf: Path) -> tuple[list[Borehole], dict]:
    doc = pymupdf.open(pdf)
    swatches = []
    for page in doc:
        if any("BODENARTEN" in t.upper() for _, t in text_lines(page)):
            swatches = legend_swatches(page)
    boreholes: list[Borehole] = []
    dph = {}
    for pno, page in enumerate(doc):
        drawings = page.get_drawings()
        words = page.get_text("words")
        lines = text_lines(page)
        dph.update(soundings(page))
        cols = find_columns(drawings)
        for chain in cols:
            col = pymupdf.Rect(chain[0].x0, chain[0].y0, chain[-1].x1, chain[-1].y1)
            code, gok = _header(lines, col)
            if not code:
                continue
            fit = depth_fit(words, col, chain)
            if not fit:
                continue
            rr, _, a, b, entries = fit
            bh = Borehole(code, pno, col, gok=gok, scale=round(abs(a) / PT_TO_M_AT_1_1), fit_r=round(rr, 4))
            # 4. Beschreibungsspalte: linksbuendiger Textblock rechts der Saeule
            right_limit = min([c[0].x0 for c in cols if c[0].x0 > col.x1 + 5] + [page.rect.x1])
            desc = [(r, t) for r, t in lines if col.x1 + 2 < r.x0 < right_limit - 60
                    and col.y0 - 2 <= (r.y0 + r.y1) / 2 <= col.y1 and re.search(r"[A-Za-zÄÖÜäöü]{3}", t)
                    and not DATE_RE.search(t)]
            x_start = Counter(round(r.x0 / 3) for r, _ in desc).most_common(1)
            desc = [(r, t) for r, t in desc if x_start and abs(r.x0 - x_start[0][0] * 3) < 4]
            prev = 0.0
            for rect in chain:
                bottom_geo = round(a * rect.y1 + b, 2)
                lab = [v for r, v in entries if abs((r.y0 + r.y1) / 2 - rect.y1) < 6]
                ly = Layer(prev, lab[0] if lab else bottom_geo, rect)
                ly.label_confirmed = bool(lab) and abs(lab[0] - bottom_geo) <= 0.02
                if not lab:
                    ly.issues.append("Grenze ohne Tiefenlabel")
                ly.text = " ".join(t for r, t in desc if rect.y0 - 2 <= r.y0 < rect.y1 - 2)
                head = soil.normalize_head(ly.text.split(",")[0]) if ly.text else ""
                cls, sure = soil.classify(head) if head else ("", False)
                ly.soil_text = cls if sure else ""
                ly.soil_hatch, ly.hatch_sim = classify_hatch(hatch_features(drawings, rect), swatches)
                if ly.soil_text and ly.soil_hatch and ly.soil_text != ly.soil_hatch:
                    ly.issues.append(f"Text '{ly.soil_text}' != Schraffur '{ly.soil_hatch}'")
                bh.layers.append(ly)
                prev = ly.bottom
            y_gw, bh.gw_date = groundwater(drawings, lines, col)
            if y_gw is not None:
                bh.gw_depth = round(a * y_gw + b, 2)
            boreholes.append(bh)
    coords = coordinate_table(doc)
    for bh in boreholes:
        if bh.code in coords:
            bh.east, bh.north = coords[bh.code]
    return boreholes, dph
