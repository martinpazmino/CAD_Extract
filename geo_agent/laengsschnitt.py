"""Laengsschnitt-Parsing (geologischer Schnitt + Vortriebsplan).

Liefert Blatt 3 (Geo_Tunnel: Tunnelgeometrie je Tunnelmeter) und die Grundlage
fuer Blatt 4 (Geo_Spec: Abschnitte mit Bodenart-Anteilen).

Verfahren (alles aus dem PDF abgeleitet, validiert):
  * X -> Tunnelmeter : lineare Regression ueber Stations-Labels (..+...000) bei y~1137.
  * Y -> NHN         : lineare Regression ueber die vertikalen Achsenlabels bei x~323.
  * Tunnelroehre     : nur die grauen Fuellpolygone (RGB ~0.73) als saubere Maske
                       rastern -> pro Tunnelmeter OK (oben) / Sohle (unten) / Achse.
  * Bodenart         : geologische Farbpolygone am Achspunkt abtasten
                       (Naheste bekannte Geologie-Farbe; weiss/schwarz ausgeschlossen).
  * abschnitt_id     : zusammenhaengende Tunnelmeter gleicher Bodenart (Median-
                       glaettung + Mindestlaenge) zu Abschnitten A01, A02, ...
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import fitz
import numpy as np
from PIL import Image, ImageDraw

# Validierte Farb -> Geologie-Zuordnung (Legende "geologischer Laengsschnitt").
# RGB 0..1 wie im PDF; wird intern auf 0..255 skaliert.
DEFAULT_COLOR_MAP: dict[tuple[float, float, float], str] = {
    (1.0, 0.75, 0.0): "Sand",
    (1.0, 1.0, 0.5): "Kies",
    (0.88, 1.0, 1.0): "Lauenburger Ton",
    (0.5, 1.0, 0.87): "Klei",
    (0.87, 0.5, 1.0): "Glimmerton",
}
GREY_TUNNEL = (0.73, 0.73, 0.73)

ZOOM = 2.0
GEO_MATCH_TOL = 40          # Farbabstand (0..765) fuer Geologie-Treffer
PROBE_RANGE = (3, 70)       # Offset (px) ober-/unterhalb der Achse fuer Bodenart


@dataclass
class TunnelPoint:
    tm: int
    ok_nhn: float
    sohle_nhn: float
    achse_nhn: float
    gok_nhn: float | None        # Gelaendeoberkante (Terrain)
    ok_bis_gok: float | None     # Ueberdeckung = GOK - OK
    bodenart: str | None
    bodenart_sure: bool
    bohr_id: str | None = None


@dataclass
class Abschnitt:
    """Ein Abschnitt = Einflusszone EINER Bohrung entlang des Tunnels.

    Die Grenzen liegen jeweils auf der Mitte zwischen zwei benachbarten
    Bohrungen ((TM_i + TM_{i+1})/2); die erste Zone beginnt am Tunnelanfang,
    die letzte endet am Tunnelende.
    """
    abschnitt_id: str
    bohr_id: str | None
    bohr_tm: int | None          # Tunnelmeter der zugehoerigen Bohrung
    tm_start: int                # Zonengrenze links
    tm_end: int                  # Zonengrenze rechts
    bodenart: str | None         # Bodenart auf Tunnel (aus Bohrprofil, s. enrich)
    bodenart_sure: bool = True
    composition: dict = field(default_factory=dict)   # bodenart -> prozent (Zone)
    # Tunnelgeometrie am Bohr-Tunnelmeter (Blatt 3)
    ok_nhn: float | None = None
    achse_nhn: float | None = None
    sohle_nhn: float | None = None
    prozent: int = 0             # Anteil der dominanten Bodenart [%]


@dataclass
class LaengsResult:
    points: list[TunnelPoint]
    abschnitte: list[Abschnitt]
    boreholes_tm: dict[str, int]
    color_map: dict
    x2tm: tuple
    y2nhn: tuple
    tm_range: tuple[int, int]
    preview_png: bytes | None = None
    log: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Regressionen
# ---------------------------------------------------------------------------
def _linfit(samples):
    xs = np.array([s[0] for s in samples], dtype=float)
    ys = np.array([s[1] for s in samples], dtype=float)
    a, b = np.polyfit(xs, ys, 1)
    return (float(a), float(b))


def _regressions(words):
    xt = []
    for w in words:
        m = re.match(r"^(\d)\+(\d{3})\.000$", w[4])
        if m and abs(w[1] - 1137) < 8:
            cx = (w[0] + w[2]) / 2
            xt.append((cx, int(m.group(1)) * 1000 + int(m.group(2))))
    yn = []
    for w in words:
        if 290 < w[0] < 360 and re.match(r"^-?\d+\.\d{2}$", w[4]):
            cy = (w[1] + w[3]) / 2
            yn.append((cy, float(w[4])))
    return _linfit(xt), _linfit(yn), len(xt), len(yn)


# ---------------------------------------------------------------------------
# Raster: Tunnelmaske (nur graue Polygone) + RGB
# ---------------------------------------------------------------------------
def _grey_tunnel_mask(page, color_map_grey=GREY_TUNNEL):
    W = int(page.rect.width * ZOOM)
    H = int(page.rect.height * ZOOM)
    img = Image.new("1", (W, H), 0)
    dr = ImageDraw.Draw(img)
    n = 0
    for d in page.get_drawings():
        f = d.get("fill")
        if not f:
            continue
        if tuple(round(c, 2) for c in f) != color_map_grey:
            continue
        pts = [(q.x * ZOOM, q.y * ZOOM) for it in d["items"] for q in it[1:] if hasattr(q, "x")]
        if len(pts) >= 3:
            dr.polygon(pts, fill=1)
            n += 1
    return np.array(img, dtype=bool), n


def _render_rgb(page):
    pix = page.get_pixmap(matrix=fitz.Matrix(ZOOM, ZOOM))
    arr = np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.height, pix.width, pix.n)
    return arr[:, :, :3].astype(np.int16)


def _geo_palette(color_map):
    return {name: tuple(int(round(c * 255)) for c in rgb) for rgb, name in color_map.items()}


def _geo_label_image(rgb, palette):
    """Vektorisiert: pro Pixel der Index der naechsten Geologie-Farbe (sonst -1).

    Weiss und Schwarz werden ausgeschlossen (cyan/Lauenburger Ton liegt nahe weiss).
    Liefert (label_array[int16], names_list).
    """
    H, W, _ = rgb.shape
    white = (rgb[:, :, 0] > 244) & (rgb[:, :, 1] > 244) & (rgb[:, :, 2] > 244)
    black = rgb.sum(axis=2) < 150
    names = list(palette)
    best = np.full((H, W), 1 << 30, dtype=np.int32)
    arg = np.full((H, W), -1, dtype=np.int16)
    for k, nm in enumerate(names):
        c = palette[nm]
        d = (np.abs(rgb[:, :, 0] - c[0]) + np.abs(rgb[:, :, 1] - c[1])
             + np.abs(rgb[:, :, 2] - c[2]))
        m = d < best
        best[m] = d[m]
        arg[m] = k
    arg[(best >= GEO_MATCH_TOL) | white | black] = -1
    return arg, names


# ---------------------------------------------------------------------------
# Bohrungs-Positionen im Laengsschnitt
# ---------------------------------------------------------------------------
def _borehole_positions(words, x2tm):
    a, b = x2tm
    out: dict[str, int] = {}
    nums = [w for w in words if re.match(r"^\d+[a-z]?/\d{2}$", w[4]) and w[1] < 360]
    for w in nums:
        # passendes 'B' links daneben?
        bs = [t for t in words if t[4] == "B" and abs(t[1] - w[1]) < 6 and 0 < (w[0] - t[2]) < 25]
        bx = bs[0][0] if bs else w[0]
        bid = "B " + w[4]
        tm = int(round(a * bx + b))
        out.setdefault(bid, tm)
    return out


def _nearest_borehole(tm, boreholes_tm):
    if not boreholes_tm:
        return None
    return min(boreholes_tm.items(), key=lambda kv: abs(kv[1] - tm))[0]


# ---------------------------------------------------------------------------
# Hauptfunktion
# ---------------------------------------------------------------------------
def parse_laengsschnitt(doc: fitz.Document, color_map=None, *, make_preview=True,
                        valid_bohr_ids=None) -> LaengsResult:
    color_map = color_map or DEFAULT_COLOR_MAP
    page = doc[0]
    words = page.get_text("words")
    log: list[str] = []

    (Ax, Bx), (Ay, By), nstat, nax = _regressions(words)
    log.append(f"X->Tunnelmeter: {nstat} Stations-Labels, Steigung {Ax:.4f} m/px")
    log.append(f"Y->NHN: {nax} Achsen-Labels, Steigung {Ay:.5f} NHN/px")

    def tm2x(tm):
        return (tm - Bx) / Ax

    def x2tm(x):
        return Ax * x + Bx

    def y2nhn(y):
        return Ay * y + By

    mask, n_grey = _grey_tunnel_mask(page)
    rgb = _render_rgb(page)
    palette = _geo_palette(color_map)
    label, names = _geo_label_image(rgb, palette)
    H, W = mask.shape
    log.append(f"Tunnel: {n_grey} graue Fuellpolygone -> Maske ({int(mask.sum())} px)")

    boreholes_tm = _borehole_positions(words, (Ax, Bx))
    log.append(f"Bohrungen im Laengsschnitt verortet: {len(boreholes_tm)}")
    if valid_bohr_ids is not None:
        valid = set(valid_bohr_ids)
        kept = {k: v for k, v in boreholes_tm.items() if k in valid}
        log.append(f"  davon mit Bohrprofil-Daten (fuer Zuordnung genutzt): {len(kept)}")
        boreholes_tm = kept

    cols = np.where(mask.any(axis=0))[0]
    if len(cols) == 0:
        log.append("WARNUNG: keine Tunnelmaske gefunden!")
        return LaengsResult([], [], boreholes_tm, color_map, (Ax, Bx), (Ay, By), (0, 0), None, log)
    tm_lo, tm_hi = sorted([int(round(x2tm(cols.min() / ZOOM))), int(round(x2tm(cols.max() / ZOOM)))])

    y_start = int(160 * ZOOM)
    y_end = int(1130 * ZOOM)

    # Terrain (GOK) vektorisiert: erste Zeile mit Lauf >=run geologischer Pixel.
    run = 6
    geo_bool = label >= 0
    region = geo_bool[y_start:y_end]
    valid = region.copy()
    valid[:-run] &= region[run:]
    has_terrain = valid.any(axis=0)
    first_terrain = y_start + np.argmax(valid, axis=0)  # je Spalte

    lo, hi = PROBE_RANGE
    points: list[TunnelPoint] = []
    raw_boden: list[str | None] = []
    for tm in range(tm_lo, tm_hi + 1):
        xpx = int(round(tm2x(tm) * ZOOM))
        if xpx < 0 or xpx >= W:
            raw_boden.append(None)
            continue
        ys = np.where(mask[:, xpx])[0]
        if len(ys) < 2:
            raw_boden.append(None)
            continue
        oky = ys.min() / ZOOM
        sohley = ys.max() / ZOOM
        ok_nhn = round(y2nhn(oky), 2)
        sohle_nhn = round(y2nhn(sohley), 2)
        achse_nhn = round((ok_nhn + sohle_nhn) / 2, 2)
        axis_py = int((ys.min() + ys.max()) / 2)

        # Bodenart: Mehrheit der Geologie-Labels im Fenster um die Achse
        y0 = max(0, axis_py - hi)
        y1 = min(H, axis_py + hi)
        col = label[y0:y1, xpx]
        col = col[col >= 0]
        if col.size:
            counts = np.bincount(col, minlength=len(names))
            bodenart = names[int(counts.argmax())]
        else:
            bodenart = None
        raw_boden.append(bodenart)

        # Terrain / Ueberdeckung (Plausibilitaet: GOK > OK)
        gok = None
        ok_bis_gok = None
        if has_terrain[xpx]:
            gok_cand = round(y2nhn(first_terrain[xpx] / ZOOM), 2)
            if gok_cand > ok_nhn + 0.5:
                gok = gok_cand
                ok_bis_gok = round(gok - ok_nhn, 2)

        points.append(TunnelPoint(
            tm=tm, ok_nhn=ok_nhn, sohle_nhn=sohle_nhn, achse_nhn=achse_nhn,
            gok_nhn=gok, ok_bis_gok=ok_bis_gok,
            bodenart=bodenart, bodenart_sure=bodenart is not None,
            bohr_id=_nearest_borehole(tm, boreholes_tm),
        ))

    # ---- Bodenart leicht glaetten (Einzelpixel-Rauschen) ----
    smoothed = _median_filter(raw_boden, 7)
    smoothed_by_tm = {tm_lo + i: g for i, g in enumerate(smoothed)}
    point_by_tm = {}
    for p in points:
        g = smoothed_by_tm.get(p.tm)
        p.bodenart = g
        p.bodenart_sure = g is not None
        point_by_tm[p.tm] = p

    # ---- Abschnitte = Bohrungs-Einflusszonen ----
    abschnitte = _build_borehole_zones(boreholes_tm, tm_lo, tm_hi,
                                       point_by_tm, smoothed_by_tm)
    log.append(f"Abschnitte (Bohrungs-Zonen): {len(abschnitte)} "
               f"(Grenzen je Mitte zwischen benachbarten Bohrungen)")

    n_unsure = sum(1 for p in points if not p.bodenart_sure)
    log.append(f"Tunnelpunkte: {len(points)} (TM {tm_lo}..{tm_hi}), "
               f"ohne Bodenart: {n_unsure}")

    preview = None
    if make_preview:
        preview = _make_preview(page, points, abschnitte, boreholes_tm,
                                tm2x, color_map)

    return LaengsResult(points, abschnitte, boreholes_tm, color_map,
                        (Ax, Bx), (Ay, By), (tm_lo, tm_hi), preview, log)


def _median_filter(seq, win):
    from collections import Counter
    half = win // 2
    out = []
    for i in range(len(seq)):
        w = [x for x in seq[max(0, i - half):i + half + 1] if x]
        out.append(Counter(w).most_common(1)[0][0] if w else None)
    return out


def _build_borehole_zones(boreholes_tm, tm_lo, tm_hi, point_by_tm, smoothed_by_tm):
    """Teilt den Tunnel in Einflusszonen je Bohrung.

    Grenze zwischen Bohrung i und i+1 = (TM_i + TM_{i+1}) / 2.
    Erste Zone beginnt am Tunnelanfang, letzte endet am Tunnelende.
    """
    from collections import Counter
    inrange = sorted(((tm, bid) for bid, tm in boreholes_tm.items()
                      if tm_lo - 1 <= tm <= tm_hi + 1), key=lambda x: x[0])
    if not inrange:
        return []
    tms = [t for t, _ in inrange]
    bounds = [tm_lo]
    for i in range(len(tms) - 1):
        bounds.append(int(round((tms[i] + tms[i + 1]) / 2)))
    bounds.append(tm_hi)

    out: list[Abschnitt] = []
    for i, (btm, bid) in enumerate(inrange):
        a, b = bounds[i], bounds[i + 1]
        comp = Counter()
        for tm in range(a, b + 1):
            g = smoothed_by_tm.get(tm)
            if g:
                comp[g] += 1
        total = sum(comp.values()) or 1
        composition = {k: round(v / total * 100) for k, v in comp.most_common()}
        pt = point_by_tm.get(btm)
        boart = smoothed_by_tm.get(btm) or (comp.most_common(1)[0][0] if comp else None)
        out.append(Abschnitt(
            abschnitt_id=f"A{i + 1:02d}", bohr_id=bid, bohr_tm=btm,
            tm_start=a, tm_end=b, bodenart=boart, composition=composition,
            ok_nhn=pt.ok_nhn if pt else None,
            achse_nhn=pt.achse_nhn if pt else None,
            sohle_nhn=pt.sohle_nhn if pt else None,
            prozent=composition.get(boart, 0) if composition else 0,
        ))
    return out


# ---------------------------------------------------------------------------
# Prüfbild
# ---------------------------------------------------------------------------
_PREVIEW_COLORS = {
    "Sand": (255, 191, 0), "Kies": (235, 235, 90), "Lauenburger Ton": (120, 210, 230),
    "Klei": (90, 210, 180), "Glimmerton": (200, 120, 235),
}


def _make_preview(page, points, abschnitte, boreholes_tm, tm2x, color_map):
    pz = 0.45
    pix = page.get_pixmap(matrix=fitz.Matrix(pz, pz))
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    dr = ImageDraw.Draw(img, "RGBA")
    # OK- und Sohle-Linien
    ok_pts = []
    so_pts = []
    for p in points:
        xpx = tm2x(p.tm) * pz
        # NHN zurueck in Pixel: nutze lineare Beziehung ueber zwei Punkte? -> approximate via stored
        ok_pts.append((xpx, _nhn_to_pix(page, p.ok_nhn, pz)))
        so_pts.append((xpx, _nhn_to_pix(page, p.sohle_nhn, pz)))
    if len(ok_pts) > 1:
        dr.line(ok_pts, fill=(220, 0, 0, 255), width=2)
        dr.line(so_pts, fill=(0, 0, 220, 255), width=2)
    # Abschnitts-Baender unten
    band_y = pix.height - 60
    for ab in abschnitte:
        x0 = tm2x(ab.tm_start) * pz
        x1 = tm2x(ab.tm_end) * pz
        col = _PREVIEW_COLORS.get(ab.bodenart, (150, 150, 150))
        dr.rectangle([min(x0, x1), band_y, max(x0, x1), band_y + 16],
                     fill=col + (200,), outline=(0, 0, 0, 255))
    # Bohrungen
    for bid, tm in boreholes_tm.items():
        x = tm2x(tm) * pz
        dr.line([(x, 40), (x, band_y)], fill=(0, 0, 0, 90), width=1)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# globaler Cache fuer NHN->Pixel im Preview
_NHN_FIT = {}


def _nhn_to_pix(page, nhn, pz):
    # einmalig Y<->NHN Regression cachen
    key = id(page)
    if key not in _NHN_FIT:
        words = page.get_text("words")
        yn = [((w[1] + w[3]) / 2, float(w[4])) for w in words
              if 290 < w[0] < 360 and re.match(r"^-?\d+\.\d{2}$", w[4])]
        ys = np.array([s[0] for s in yn]); ns = np.array([s[1] for s in yn])
        a, b = np.polyfit(ns, ys, 1)   # nhn -> y(pt)
        _NHN_FIT[key] = (a, b)
    a, b = _NHN_FIT[key]
    return (a * nhn + b) * pz
