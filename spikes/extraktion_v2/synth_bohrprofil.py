"""Synthetische Bohrprofil-PDFs (DIN 4023, vereinfacht) mit bekannter Wahrheit.

Erzeugt Vektor-PDFs in mehreren Layouts, um zu pruefen, wie robust ein Parser
gegenueber anderen Bueros / Massstaeben / Schreibweisen ist:

    A   "Referenz"   : so wie geo_agent/bohrprofil.py es erwartet (M 1:100, 'B n/jj',
                       '(NHN) Tiefe'-Paare links, Text bei x_label+60)
    A2  "Massstab"   : gleiche Schreibweise, M 1:50, breitere Saeule
    A3  "Text naeher": wie A, Beschreibung beginnt 10 pt naeher an der Saeule
    A4  "Kopf mittig": wie A, Bohrungsname ueber der Saeulenmitte, Tiefen weiter links
    A5  "Widerspruch": wie A, aber in B 1/19 traegt die 2. Schicht (Text 'Sand') die Kies-Schraffur
                       -> ein Parser mit Signal-Fusion muss das als Issue melden
    B   "anderes Buero": 'BK n' ohne Jahr, Tiefen rechts der Saeule mit Punkt-Dezimal,
                       GOK im Kopf, M 1:50, Hochformat, DPH-Sondierung als Diagramm

Jede Seite enthaelt Schichtsaeulen mit Schraffur (Punkte, Kreise, Striche),
Grundwasser-Dreieck, Legende mit Musterfeldern und eine Koordinatentabelle.
Die Wahrheit wird als JSON neben das PDF geschrieben.

    python synth_bohrprofil.py <ausgabeordner>
"""
from __future__ import annotations

import json
import random
import sys
from dataclasses import dataclass, field
from pathlib import Path

import pymupdf

PT_PER_M_1_100 = 1000 / 100 / 25.4 * 72      # 1 m Natur bei M 1:100 = 28.35 pt

SOILS = {
    # name: (Beschreibungsvorlagen, Schraffur)
    "Mutterboden": (["Mutterboden, humos, dunkelbraun"], "diag"),
    "Sand": (["Mittelsand, feinsandig, schwach schluffig, braun",
              "Feinsand, schwach mittelsandig, hellbraun, mitteldicht"], "dots"),
    "Kies": (["Kies, sandig, grau, dicht", "Grobkies, schwach steinig, grau"], "circles"),
    "Schluff": (["Schluff, tonig, feinsandig, steif, grau"], "vticks"),
    "Ton": (["Ton, schluffig, steif, dunkelgrau", "Ton, halbfest, dunkelgrau, kalkhaltig"], "hdash"),
    "Geschiebemergel": (["Geschiebemergel, Schluff, sandig, kiesig, steif, grau"], "mix"),
}


@dataclass
class Layout:
    name: str
    page_w: float
    page_h: float
    scale: float                 # 100 -> M 1:100
    id_style: str                # "b_slash" -> 'B 1/19'; "bk" -> 'BK 1'
    depth_side: str              # "left_pairs" | "right_plain"
    decimal: str
    col_w: float
    text_dx: float               # Abstand Textbeginn ab rechter Saeulenkante
    pitch: float                 # Abstand zwischen Bohrungen
    x0: float                    # x des ersten Ankers
    top_y: float                 # y der GOK
    n_boreholes: int
    gok_in_header: bool = False
    with_dph: bool = False
    id_dx: float = 0.0           # Versatz des Bohrungsnamens gegenueber dem Anker
    pair_dx: float = 0.0         # zusaetzlicher Versatz der '(NHN) Tiefe'-Paare nach links
    mismatch: bool = False       # absichtlicher Widerspruch Text <-> Schraffur (siehe A5)

    @property
    def pt_per_m(self) -> float:
        return PT_PER_M_1_100 * 100 / self.scale


LAYOUTS = {
    "A": Layout("A", 1190, 842, 100, "b_slash", "left_pairs", ",", 28, 20, 330, 90, 120, 3),
    "A2": Layout("A2", 1190, 1684, 50, "b_slash", "left_pairs", ",", 40, 60, 380, 90, 120, 3),
    "A3": Layout("A3", 1190, 842, 100, "b_slash", "left_pairs", ",", 28, 8, 330, 90, 120, 3),
    "A4": Layout("A4", 1190, 842, 100, "b_slash", "left_pairs", ",", 28, 20, 330, 110, 120, 3,
                 id_dx=18, pair_dx=20),
    "A5": Layout("A5", 1190, 842, 100, "b_slash", "left_pairs", ",", 28, 20, 330, 90, 120, 3, mismatch=True),
    "B": Layout("B", 1000, 1190, 50, "bk", "right_plain", ".", 34, 62, 420, 80, 150, 2,
                gok_in_header=True, with_dph=True),
}


@dataclass
class TruthLayer:
    top: float
    bottom: float
    soil: str
    text: str


@dataclass
class TruthBorehole:
    code: str
    gok: float
    layers: list[TruthLayer]
    gw_depth: float
    gw_date: str
    east: float
    north: float
    dph: list[tuple[float, int]] = field(default_factory=list)   # (Tiefe Unterkante, N10)


def _fmt(v: float, dec: str, signed: bool = False) -> str:
    s = f"{v:+.2f}" if signed else f"{v:.2f}"
    return s.replace(".", dec)


def _hatch(page: pymupdf.Page, r: pymupdf.Rect, kind: str) -> None:
    """Schraffur als EIN Pfad mit vielen Teilelementen (wie bei CAD-Exporten)."""
    sh = page.new_shape()
    step = 7.0
    ys = [r.y0 + step / 2 + i * step for i in range(int(r.height // step))]
    xs = [r.x0 + step / 2 + i * step for i in range(int(r.width // step))]
    if kind == "dots":
        for y in ys:
            for x in xs:
                sh.draw_circle(pymupdf.Point(x, y), 0.45)
        sh.finish(color=None, fill=(0, 0, 0))
    elif kind == "circles":
        for y in ys:
            for x in xs:
                sh.draw_circle(pymupdf.Point(x, y), 1.8)
        sh.finish(color=(0, 0, 0), fill=None, width=0.3)
    elif kind == "hdash":
        for y in ys:
            sh.draw_line(pymupdf.Point(r.x0 + 1, y), pymupdf.Point(r.x1 - 1, y))
        sh.finish(color=(0, 0, 0), width=0.3, dashes="[3 2] 0")
    elif kind == "vticks":
        for y in ys:
            for x in xs:
                sh.draw_line(pymupdf.Point(x, y - 2), pymupdf.Point(x, y + 2))
        sh.finish(color=(0, 0, 0), width=0.3)
    elif kind == "diag":
        for x in [r.x0 + i * step for i in range(-int(r.height // step), int(r.width // step) + 1)]:
            p, q = pymupdf.Point(x, r.y1), pymupdf.Point(x + r.height, r.y0)
            clip = pymupdf.Rect(r)
            # Linie auf das Rechteck beschneiden (einfach: Parameter t)
            t0 = max(0.0, (r.x0 - p.x) / r.height)
            t1 = min(1.0, (r.x1 - p.x) / r.height)
            if t1 > t0:
                a = p + (q - p) * t0
                b = p + (q - p) * t1
                if clip.contains(a) or clip.contains(b):
                    sh.draw_line(a, b)
        sh.finish(color=(0, 0, 0), width=0.3)
    elif kind == "mix":
        for i, y in enumerate(ys):
            if i % 2:
                sh.draw_line(pymupdf.Point(r.x0 + 1, y), pymupdf.Point(r.x1 - 1, y))
            else:
                for x in xs[::2]:
                    sh.draw_circle(pymupdf.Point(x, y), 1.4)
        sh.finish(color=(0, 0, 0), width=0.3)
    sh.commit()


def _random_boreholes(rng: random.Random, lay: Layout) -> list[TruthBorehole]:
    out = []
    for i in range(lay.n_boreholes):
        code = f"B {i + 1}/19" if lay.id_style == "b_slash" else f"BK {i + 1}"
        gok = round(rng.uniform(4.5, 7.5), 2)
        seq = ["Mutterboden", "Sand", rng.choice(["Kies", "Schluff"]), "Sand", "Geschiebemergel", "Ton"]
        d, layers = 0.0, []
        max_depth = 12.0 if lay.scale == 50 else 15.0
        for k, soil in enumerate(seq):
            th = 0.3 if soil == "Mutterboden" else round(rng.uniform(1.0, 3.2), 1)
            top, bottom = d, round(min(d + th, max_depth), 2)
            if k == len(seq) - 1:
                bottom = max_depth
            layers.append(TruthLayer(top, bottom, soil, rng.choice(SOILS[soil][0])))
            d = bottom
            if d >= max_depth:
                break
        gw = round(rng.uniform(1.5, 4.0), 2)
        bh = TruthBorehole(code, gok, layers, gw, f"{rng.randint(1, 28):02d}.03.19",
                           round(565000 + rng.uniform(0, 900), 2), round(5933000 + rng.uniform(0, 400), 2))
        if lay.with_dph:
            n, dd = [], 0.0
            while dd < 8.0:
                dd = round(dd + 0.5, 1)
                n.append((dd, rng.randint(2, 28)))
            bh.dph = n
        out.append(bh)
    return out


def _text_block(page, x, y, text, width, size=7.0):
    """Einfacher Zeilenumbruch; gibt das y unter dem Block zurueck."""
    words, line = text.split(), ""
    for w in words:
        cand = (line + " " + w).strip()
        if pymupdf.get_text_length(cand, fontsize=size) > width and line:
            page.insert_text((x, y), line, fontsize=size)
            y += size * 1.25
            line = w
        else:
            line = cand
    if line:
        page.insert_text((x, y), line, fontsize=size)
        y += size * 1.25
    return y


def draw_borehole(page, lay: Layout, bh: TruthBorehole, x_label: float) -> None:
    ppm = lay.pt_per_m
    top = lay.top_y
    hdr_y = top - 30
    if lay.id_style == "b_slash":
        page.insert_text((x_label + lay.id_dx, hdr_y), "B", fontsize=9)
        page.insert_text((x_label + lay.id_dx + 10, hdr_y), bh.code.split()[1], fontsize=9)
    else:
        page.insert_text((x_label, hdr_y), bh.code, fontsize=9)
    if lay.gok_in_header:
        page.insert_text((x_label, hdr_y + 12), f"Ansatzhoehe: {_fmt(bh.gok, lay.decimal)} m NHN", fontsize=6.5)
    else:
        page.insert_text((x_label - 40 - lay.pair_dx, top - 6), f"NHN{_fmt(bh.gok, lay.decimal, signed=True)}m",
                         fontsize=6.5)

    col_x0 = x_label + 12
    col = pymupdf.Rect(col_x0, top, col_x0 + lay.col_w, top)
    text_x = col.x1 + lay.text_dx
    text_right = (x_label + lay.pitch - 145) if lay.with_dph else (x_label + lay.pitch - 40)
    width = text_right - text_x
    for k, ly in enumerate(bh.layers):
        r = pymupdf.Rect(col.x0, top + ly.top * ppm, col.x1, top + ly.bottom * ppm)
        page.draw_rect(r, color=(0, 0, 0), fill=(1, 1, 1), width=0.5)
        kind = SOILS[ly.soil][1]
        if lay.mismatch and bh.code == "B 1/19" and k == 1:
            kind = SOILS["Kies"][1]                 # Zeichenfehler: Text sagt Sand
        _hatch(page, r, kind)
        yb = r.y1
        nhn = bh.gok - ly.bottom
        if lay.depth_side == "left_pairs":
            page.insert_text((x_label - 62 - lay.pair_dx, yb + 2.5), f"({_fmt(nhn, lay.decimal)})", fontsize=6.5)
            page.insert_text((x_label - 25 - lay.pair_dx, yb + 2.5), _fmt(ly.bottom, lay.decimal), fontsize=6.5)
        else:
            page.insert_text((col.x1 + 4, yb + 2.5), _fmt(ly.bottom, lay.decimal), fontsize=6.5)
            page.insert_text((col.x1 + 30, yb + 2.5), _fmt(nhn, lay.decimal, signed=True), fontsize=6.5)
        _text_block(page, text_x, r.y0 + 7, ly.text, width)

    # Grundwasser: Dreieck mit Spitze nach unten, Spitze = Wasserstand
    yg = top + bh.gw_depth * ppm
    gx = col.x0 - 9 if lay.depth_side == "right_plain" else col.x1 + 4
    page.draw_polyline([(gx, yg - 6), (gx + 7, yg - 6), (gx + 3.5, yg), (gx, yg - 6)],
                       color=(0, 0, 1), fill=(0, 0, 1), closePath=True, width=0.4)
    page.insert_text((gx - 2 if lay.depth_side == "left_pairs" else gx - 48, yg - 8),
                     f"{_fmt(bh.gw_depth, lay.decimal)} {bh.gw_date}", fontsize=5.5, color=(0, 0, 1))

    if lay.with_dph:
        _draw_dph(page, lay, bh, x_label + lay.pitch - 130)


def _draw_dph(page, lay: Layout, bh: TruthBorehole, x0: float) -> None:
    """Rammsondierung DPH: Treppenkurve N10 ueber Tiefe mit Achsenbeschriftung."""
    ppm, top = lay.pt_per_m, lay.top_y
    w = 90.0
    page.insert_text((x0, top - 30), "DPH " + bh.code.split()[1], fontsize=8)
    page.insert_text((x0 + 30, top - 16), "N10", fontsize=6)
    for n in (0, 10, 20, 30):
        page.insert_text((x0 + n / 30 * w - 2, top - 4), str(n), fontsize=5.5)
    page.draw_rect(pymupdf.Rect(x0, top, x0 + w, top + 8.5 * ppm), color=(0.5, 0.5, 0.5), width=0.3)
    for m in range(1, 9):
        page.insert_text((x0 - 10, top + m * ppm + 2), str(m), fontsize=5.5)
    pts, prev = [], 0.0
    for d, n in bh.dph:
        x = x0 + n / 30 * w
        pts += [(x, top + prev * ppm), (x, top + d * ppm)]
        prev = d
    page.draw_polyline(pts, color=(0, 0, 0), width=0.6)


def draw_legend_and_table(page, boreholes: list[TruthBorehole], lay: Layout) -> None:
    lx, ly = 60, 80
    page.insert_text((lx, ly), "ZEICHENERKLAERUNG", fontsize=9)
    page.insert_text((lx + 40, ly + 20), "BODENARTEN", fontsize=8)
    y = ly + 34
    for name, (_, kind) in SOILS.items():
        sw = pymupdf.Rect(lx, y - 9, lx + 28, y + 7)
        page.draw_rect(sw, color=(0, 0, 0), fill=(1, 1, 1), width=0.4)
        _hatch(page, sw, kind)
        page.insert_text((lx + 40, y + 2), name, fontsize=7)
        y += 22
    for hdr in ("KORNGROESSENBEREICH", "NEBENANTEILE", "KALKGEHALT", "KONSISTENZ"):
        y += 6
        page.insert_text((lx + 40, y), hdr, fontsize=8)
        y += 14
    # Koordinatentabelle als echte Tabelle (Linien + Text)
    tx, ty = 420, 80
    page.insert_text((tx, ty), "Lage- und Hoehenverzeichnis der Aufschluesse", fontsize=8)
    cols = [tx, tx + 80, tx + 180, tx + 280, tx + 350]
    hdr = ["Aufschluss", "Ostwert", "Nordwert", "Hoehe [m NHN]"]
    rows = [hdr] + [[b.code, f"{b.east:,.2f}".replace(",", " ").replace(".", ","),
                     f"{b.north:,.2f}".replace(",", " ").replace(".", ","),
                     _fmt(b.gok, ",")] for b in boreholes]
    rh = 14
    for i, row in enumerate(rows):
        yy = ty + 10 + i * rh
        for j, cell in enumerate(row):
            page.insert_text((cols[j] + 3, yy + 10), cell, fontsize=7)
    for i in range(len(rows) + 1):
        page.draw_line((cols[0], ty + 10 + i * rh), (cols[-1], ty + 10 + i * rh), width=0.4)
    for c in cols:
        page.draw_line((c, ty + 10), (c, ty + 10 + len(rows) * rh), width=0.4)


def make(layout_key: str, out_dir: Path, seed: int = 7) -> Path:
    lay = LAYOUTS[layout_key]
    rng = random.Random(seed)
    bhs = _random_boreholes(rng, lay)
    doc = pymupdf.open()
    page = doc.new_page(width=lay.page_w, height=lay.page_h)
    page.insert_text((40, 30), f"Bohrprofile  M 1:{lay.scale:.0f}", fontsize=10)
    for i, bh in enumerate(bhs):
        draw_borehole(page, lay, bh, lay.x0 + i * lay.pitch)
    leg = doc.new_page(width=842, height=595)
    draw_legend_and_table(leg, bhs, lay)
    out_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / f"synth_{layout_key}.pdf"
    doc.save(pdf)
    truth = [{"code": b.code, "gok": b.gok, "gw_depth": b.gw_depth, "gw_date": b.gw_date,
              "east": b.east, "north": b.north, "dph": b.dph,
              "layers": [vars(x) for x in b.layers]} for b in bhs]
    (out_dir / f"synth_{layout_key}.json").write_text(json.dumps(truth, indent=1, ensure_ascii=False))
    return pdf


if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else "out")
    for key in LAYOUTS:
        print("written", make(key, out))
