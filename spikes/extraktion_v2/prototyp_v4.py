"""Prototyp v4: Extraktion nach der Spezifikation docs/17_algoritmo_extraccion.md.

Stufen (je Seite, dann je Dokument):
  E0  Seitenklasse: vektor | vektor_ohne_text (AutoCAD-SHX) | raster (Bild ohne Text) | raster_ocr (Scan)
  E1  Primitive: Woerter (Textlage oder OCR) und Segmente (Vektor oder Bild), in Ansichtskoordinaten
  E2  Koepfe: Kuerzel mit Zusatz ('RKS 1 - Weg'), 'Bohrung <Code>' auch zweizeilig, Fremdcodes
  E3  Saeulen: Paare senkrechter Kanten, Grenzen = durchgehende Waagrechte ueber die volle Breite
  E4  Tiefen: Labelgruppen (ohne Achsen, Probenpaare, Tabellen), Massstab = Kandidat mit den
      meisten bestaetigten Labels (direkt / Reihenfolge / Massstabstext)
  E5  Schichten: 1:1-Bestaetigung je Grenze; unbestaetigte Grenze mit gleicher Schraffur
      ober- und unterhalb ist eine Schraffurlinie (Doppellinie Schwarzdecke)
  E6  Bodenart: Substantiv -> Fels/Anthropogen -> DIN-/ISO-Kuerzel; Originaltext bleibt erhalten
  E7  Grundwasser: Symbol + Wasserlinie, 'GW 2.53m', 'Wasseranschnitt 3.8', 'kein Wasser' als Befund
  E8  Zweitquellen: Schichtenverzeichnis (DIN 4022), Koordinatentabelle, Rechts-/Hochwert im Text
  E9  Zusammenfuehren: Duplikate, Abgleich Profil <-> SV, Konfidenz, kanonisches JSON (Arquitectura §5.1)

Jede Regel aus docs/16 ist in RULES einzeln abschaltbar (Ablation: regression.py --disable).
Stand: Trainingszahlen; die einzige ehrliche Zahl ist die naechste Blindrunde (docs/15).
"""
from __future__ import annotations

import hashlib
import itertools
import json
import os
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
HEAD_RE = re.compile(r"^((?:B|BK|KB|KRB|RKS|BS|GWM|SCH)\s*\d+[a-z]?(?:/\d{2})?)(?:\s+[-–:]\s+\S.*)?$")
DEPTH_RE = re.compile(r"^\d{1,3}[.,]\d{1,2}\s?m?$")              # DC-Software: '0.20m'
GW_TEXT_RE = re.compile(r"\bGW\b.*?(\d{1,3}[.,]\d{1,2})\s?m\b|(\d{1,3}[.,]\d{1,2})\s?m\s*u\.?\s*GOK", re.I)
SCALE_RE = re.compile(r"(?:M(?:a(?:ss|ß)stab)?\.?|H(?:ö|oe)hen-?Ma(?:ss|ß)stab)?\s*1\s*:\s*(\d{2,4})\b")
NO_GW_RE = re.compile(r"kein(?:\s+|e\s+)(?:Grund)?wasser|GW\s+nicht\s+angetroffen|trocken", re.I)
ROCK_SUFFIX = ("stein", "fels")
ANTHROPOGEN = {"beton": "Beton", "asphalt": "Asphalt", "schwarzdecke": "Schwarzdecke",
               "pflaster": "Pflaster", "anschuettung": "Auffuellung", "anschüttung": "Auffuellung",
               "auffuellung": "Auffuellung", "auffüllung": "Auffuellung", "schotter": "Auffuellung"}
TOPSOIL = {"oberboden", "mutterboden", "humus"}
# Hauptbodenart als Kuerzel am Anfang der Beschreibung (DIN 4023 bzw. EN ISO 14688)
ABBR_RE = re.compile(r"^\s*(Mu|Mg|Gr|Sa|Si|Cl|Co|A|[fmg]?S|[fmg]?G|U|T|X|H|F)(?=[\s,(?´'*]|$)")
ABBR = {"Mu": "Mutterboden", "Mg": "Auffuellung", "A": "Auffuellung", "Gr": "Kies", "G": "Kies",
        "Sa": "Sand", "S": "Sand", "Si": "Schluff", "U": "Schluff", "Cl": "Ton", "T": "Ton",
        "Co": "Steine", "X": "Steine", "H": "Torf", "F": "Mudde"}
STANDARD_SCALES = (10, 20, 25, 33, 50, 75, 100, 125, 150, 200, 250, 500, 1000)

# Regeln aus docs/16 (Lektion in Klammern); False = fuer Ablationen abgeschaltet
RULES = {
    "rotation": True,            # L2   Ansichtskoordinaten bei /Rotate
    "dashed_exclusion": True,    # G2   gestrichelte Waagrechte sind Schraffur
    "table_filter": True,        # G4   Zahlen in der Saeule = Tabelle
    "nonstandard_scale": True,   # L9   Nicht-Normmassstab bei starker Bestaetigung
    "head_suffix": True,         # L13  'RKS 1 - Betonweg 0+050'
    "generic_heads": True,       # T1   'Bohrung 422C-460', Archivcodes 'S 2a'
    "axis_filter": True,         # L14  arithmetische Folgen sind Achsen
    "paired_filter": True,       # L15  Probenspalte Von/Bis
    "labelless_column": True,    # L15b Saeule ohne Labels neben Saeulen mit Labels
    "top_convention": True,      # L3   Labels an der Oberkante (mit 0,00)
    "abbreviations": True,       # L16  DIN-4023-/ISO-Kuerzel
    "gw_symbol_filter": True,    # L10  Leisten-, Koten- und GOK-Dreiecke sind kein Wasser
    "gw_text": True,             # L10b 'GW 2.53m'
    "gw_description": True,      # L10b 'Wasseranschnitt 3.8' in der Schichtbeschreibung
    "dup_preference": True,      # L12  Einzelblatt/Titel vor Schnitt
    "sv_source": True,           # S1   Schichtenverzeichnis als Zweitquelle
    "ocr": True,                 # L17/L18 OCR fuer Seiten ohne Textlage
    "coords_text": True,         # S5   Rechts-/Hochwert im Text
    "hatch_continuity": True,    # L6   Doppellinie innerhalb einer Schicht
    "label_snap": True,          # T2   bestaetigte Grenze = gedruckter Labelwert
    "scan_with_vectors": True,   # E2   Scan mit OCR-Textlage trotz Vektorrauschen
    "single_sheet_anchor": True, # T3   ein Kopf + ein Profil auf der Seite gehoeren zusammen
    "depth_table": True,         # S6   Schichtenliste als Texttabelle (Tiefe | Beschreibung)
    "ocr_supplement": True,      # L18b eigene OCR ergaenzt eine luckenhafte OCR-Textlage
    "label_first": True,         # T4   Labels bilden eine saubere Gerade, Linien nicht: Labels sind die Daten
}

CODE_TOKEN = r"[A-Z0-9][A-Za-z0-9]*(?:[-/.][A-Za-z0-9]+)*"
GENERIC_HEAD_RE = re.compile(r"^(?:Bohrung|[A-ZÄÖÜ][a-zäöü]*bohrung|Bohrprofil|Aufschluss|Rammkernsondierung)"
                             r"\s*(?:Nr\.?)?\s*:?\s*(.{0,20}?)\s*$")
FREE_CODE_RE = re.compile(r"[A-Z0-9][A-Z0-9 ./\-]{0,14}?[a-z]?")             # 'SST KB 5', 'RB 2 / I', '422C-460'
GOK_EXTRA_RE = re.compile(r"(?:H(?:ö|oe)he|Kote|Ansatzh(?:ö|oe)he|Gel(?:ä|ae)ndeh(?:ö|oe)he|Bezugspunkt)[^\d\n]{0,30}?"
                          r"([+-]?\d{1,4}[.,]\d{1,2})|(\d{1,4}[.,]\d{1,2})\s*m\s*(?:ü|ue)\.?\s*(?:M\.|NN|NHN)", re.I)
LV_COORD_RE = re.compile(r"Koordinaten\D{0,5}?(\d['’ ]?\d{3}\s?\d{3}(?:[.,]\d+)?|\d{3}\s?\d{3}(?:[.,]\d+)?)\s*/\s*"
                         r"(\d['’ ]?\d{3}\s?\d{3}(?:[.,]\d+)?|\d{3}\s?\d{3}(?:[.,]\d+)?)")
ARCHIVE_HEAD_RE = re.compile(r"^(S\s*\d+[a-z]?)$")            # Archivbohrungen 'S 1', 'S2a'
WATER_DESC_RE = re.compile(r"Wasser(?:anschnitt|stand|spiegel|zutritt)\s*(?:bei|in|:)?\s*(\d{1,2}[.,]\d{1,2})", re.I)
COORD_E_RE = re.compile(r"(?:Rechtswert|Ostwert|Easting|\bRW\b)(?:\D|UTM\d{2}N?){0,30}?(\d{6,8}(?:[.,]\d+)?)", re.I)
COORD_N_RE = re.compile(r"(?:Hochwert|Nordwert|Northing|\bHW\b)(?:\D|UTM\d{2}N?){0,30}?(\d{7}(?:[.,]\d+)?)", re.I)
UTM_ZONE_RE = re.compile(r"UTM\s*(3[23])", re.I)


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


_OCR = None


def ocr_words(page: pymupdf.Page, dpi: int | None = None, min_conf: float = 0.5) -> list[tuple]:
    """Text aus dem Seitenbild (RapidOCR/ONNX, Apache-2.0), als Woerter in Ansichtskoordinaten.

    Ein OCR-Kasten ist eine Zeile; die Woerter darin bekommen anteilige x-Bereiche.
    """
    global _OCR
    if _OCR is None:
        try:
            from rapidocr_onnxruntime import RapidOCR
            _OCR = RapidOCR()
        except ImportError:                              # ohne OCR bleibt die Seite stumm (und wird gemeldet)
            _OCR = False
    if not _OCR:
        return []
    if dpi is None:                                      # ~3300 px lange Seite: kleine Seiten (verkleinert) schaerfer
        dpi = int(min(300, max(200, 3300 / (max(page.rect.width, page.rect.height) / 72))))
    pix = page.get_pixmap(dpi=dpi)
    cache = None
    if os.environ.get("GEO_OCR_CACHE"):                  # Cache je Seitenbild (Tests laufen oft)
        cache = Path(os.environ["GEO_OCR_CACHE"]) / (hashlib.md5(pix.samples).hexdigest() + f"_{dpi}.json")
    if cache and cache.exists():
        res = json.loads(cache.read_text())
    else:
        img = np.ascontiguousarray(np.frombuffer(pix.samples, dtype=np.uint8).reshape(pix.h, pix.w, pix.n)[:, :, :3])
        res, _ = _OCR(img)
        res = [[[[float(c) for c in q] for q in box], txt, float(conf)] for box, txt, conf in (res or [])]
        if cache:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text(json.dumps(res))
    f = 72.0 / dpi
    out = []
    for i, (box, txt, conf) in enumerate(res or []):
        if float(conf) < min_conf or not txt.strip():
            continue
        xs, ys = [q[0] * f for q in box], [q[1] * f for q in box]
        x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
        txt = txt.strip()
        pos = 0
        for tok in txt.split():
            k = txt.index(tok, pos)
            a, b = k / len(txt), (k + len(tok)) / len(txt)
            out.append((pymupdf.Rect(x0 + a * (x1 - x0), y0, x0 + b * (x1 - x0), y1), tok, 100000 + i, 0))
            pos = k + len(tok)
    return out


def page_class(page: pymupdf.Page, words, drawings) -> str:
    """E0: vektor | vektor_ohne_text | raster | raster_ocr."""
    m = page.rotation_matrix
    imgs = [r for r in (pymupdf.Rect(i["bbox"]) * m & page.rect for i in page.get_image_info()) if not r.is_empty]
    cov = min(1.0, sum(r.get_area() for r in imgs) / max(page.rect.get_area(), 1.0))
    inside = sum(1 for r, *_ in words if any(i.contains((r.tl + r.br) / 2) for i in imgs))
    if cov > 0.45 and inside < 10:
        return "raster"                                  # Bild ohne Textlage (Portal-Screenshot, Archivscan)
    if cov > 0.8 and (len(drawings) < 5 or RULES["scan_with_vectors"]):
        return "raster_ocr"                              # Scan mit OCR-Textlage (auch mit Vektorrauschen)
    if len(drawings) >= 150 and len(words) < 25:
        return "vektor_ohne_text"                        # AutoCAD mit SHX-Schrift: Text sind Linien
    return "vektor"


def primitives(page: pymupdf.Page):
    m = page.rotation_matrix if RULES["rotation"] else pymupdf.Matrix(1, 1)
    words = [(pymupdf.Rect(w[:4]) * m, w[4], w[5], w[6]) for w in page.get_text("words")]
    drawings = [_xform_drawing(d, m) for d in page.get_drawings()]
    segs: list[Seg] = []
    pclass = page_class(page, words, drawings)
    scanned = pclass in ("raster", "raster_ocr")
    if scanned:                                          # Linien aus dem Bild
        segs = raster_segments(page)
    if (pclass in ("raster", "vektor_ohne_text") and RULES["ocr"]) or (pclass == "raster_ocr" and RULES["ocr_supplement"]):
        native = [r for r, *_ in words]
        words += [w for w in ocr_words(page) if not any((w[0] & r).get_area() > 0.3 * w[0].get_area() for r in native)]
    for d in ([] if scanned and len(drawings) < 5 else drawings):   # Vektoren neben dem Bild behalten
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
    return words, text_lines, drawings, segs, scanned, pclass


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
    H = _merge([s for s in segs if s.horizontal and s.x1 - s.x0 >= 3
                and not (s.dashed and RULES["dashed_exclusion"])], "h")
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
    if RULES["abbreviations"] and (m := ABBR_RE.match(text)):   # 'U, t, s´' -> Schluff, 'fS' -> Sand
        k = m.group(1)
        return ABBR.get(k) or ABBR.get(k[-1], "")
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
        if len(g) >= 2 and not (RULES["axis_filter"] and _arithmetic(g)) and not (RULES["paired_filter"] and _paired(g)):
            out.append(g)
    return sorted(out, key=lambda g: (-len(g), hdist(g[0][0], col)))


def _arithmetic(g, tol: float = 0.011) -> bool:
    """Lineal, Hoehenleiste, Tiefenachse eines Rammdiagramms: >= 5 Werte mit gleichem Abstand (wie swissgeol)."""
    v = [x for _, x in g]
    d = np.diff(v)
    return len(v) >= 5 and d.min() > 0 and float(d.max() - d.min()) <= tol


def _paired(g) -> bool:
    """Probenspalte: Von/Bis-Paare, fast jeder Wert steht doppelt untereinander."""
    v = [round(x, 2) for _, x in g]
    return len(v) >= 6 and len(set(v)) <= 0.7 * len(v)


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
        if plausible_scale(f[0] / PT_TO_M_AT_1_1) or (RULES["nonstandard_scale"] and len(g) >= 3 and sup >= 0.8 * len(g)):
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


def label_line(groups, min_n: int = 5, max_res: float = 0.2):
    """T4: Labelwerte linear ueber ihre Lage (y-Mitte) - unabhaengig von den Linien.

    Liefert (a, b, gruppe) mit Tiefe = a*y + b, wenn >= min_n Labels mit max. Restfehler max_res m passen.
    """
    best = None
    for g in groups:
        if len(g) < min_n:
            continue
        keep = list(range(len(g)))
        while True:                                       # gestapelte Labels (Fuehrungslinien) als Ausreisser
            ys = np.array([(g[i][0].y0 + g[i][0].y1) / 2 for i in keep])
            vs = np.array([g[i][1] for i in keep])
            a, b = np.polyfit(ys, vs, 1)
            res = np.abs(np.polyval([a, b], ys) - vs)
            if res.max() <= max_res or len(keep) - 1 < max(min_n, 0.75 * len(g)):
                break
            keep.pop(int(res.argmax()))
        # Massstab muss ein Normmassstab sein: sonst koennte jede Zahlenreihe eine 'Gerade' bilden
        if a > 0 and res.max() <= max_res and plausible_scale(a / PT_TO_M_AT_1_1):
            # gestapelte Labels (Rest <= 1 m) bleiben Daten; weit abseits (Kote '52,35') gehoert nicht dazu
            g_ok = [e for e in g if abs(a * (e[0].y0 + e[0].y1) / 2 + b - e[1]) <= 1.0]
            if best is None or len(g_ok) > len(best[2]):
                best = (float(a), float(b), g_ok)
    return best


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
    for drop_b in range(0, min(4, len(B) + 1)):
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
    text: str = ""                   # Originalbeschreibung (B2)
    confidence: float = 0.0


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
    cross_check: str = ""            # Abgleich mit dem Schichtenverzeichnis
    crs: int | None = None
    coord_source: str = ""
    page_class: str = ""
    bbox: tuple = ()
    fit: tuple = ()                  # Tiefe = a * y + b (Ansichtskoordinaten der Seite)
    issues: list[str] = field(default_factory=list)
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
        if RULES["gw_symbol_filter"] and any(abs(round(r.x0) - x) <= 1 for x in ruler_x):
            continue
        # Hoehenmarke: Dreieck mit Kote daneben ('741.00m', '~770,17')
        if RULES["gw_symbol_filter"] and any(abs((wr.y0 + wr.y1) / 2 - (r.y0 + r.y1) / 2) < 5 and 0 < wr.x0 - r.x1 < 70
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
            if depth > 0.05 or not RULES["gw_symbol_filter"]:   # Dreieck an der GOK = Ansatzpunkt, kein Wasser
                out.append(depth)
    return sorted(set(out))


SV_CODE_RE = re.compile(r"(?<![A-Za-z0-9])((?:B|BK|KB|KRB|RKS|BS|GWM|SCH)\s*\d+[a-z]?(?:/\d{2})?)(?![\d.,])")
SV_NO_GW_RE = re.compile(r"kein(?:e[nr]?)?\s+(?:Grund)?wasser|Wasser\s+nicht\s+angetroffen", re.I)
SV_GW_RE = re.compile(r"(?:Wasserstand|Wasserspiegel|Grundwasser\w*|\bGW)\D{0,40}?(\d{1,2}[.,]\d{1,2})\s*m\b", re.I)


def schichtenverzeichnis(doc) -> dict[str, dict]:
    """Formblatt 'Schichtenverzeichnis': Spalte 1 'Bis ... m unter Ansatzpunkt', Spalte 2 Bloecke a) bis i).

    Das Formblatt ist genormt und bei allen Bueros gleich aufgebaut: die Tiefe steht links vom a)-Block,
    im Block steht unter a) die Benennung. Liefert je Aufschluss Unterkanten, Benennung und Wasserangaben.
    """
    out: dict[str, dict] = {}
    for pno, page in enumerate(doc):
        txt = page.get_text()
        if "schichtenverzeichnis" not in re.sub(r"\s", "", txt).lower() or "Ansatz" not in txt:   # 'S c h i c h t e n ...' 
            continue
        pw, plines = primitives(page)[:2]                # Ansichtskoordinaten (gedrehte Seiten!)
        ws = {(round(r.x0), round(r.y0), t): (r.x0, r.y0, r.x1, r.y1, t) for r, t, *_ in pw}.values()   # doppelter Text
        hdr = [w for w in ws if w[4].startswith("Ansatz")]
        marks = sorted((w for w in ws if w[4] == "a)"), key=lambda w: w[1])
        if not hdr or not marks:
            continue
        y_hdr = max(w[3] for w in hdr)
        x_a = min(w[0] for w in marks)
        x_col3 = min([w[0] - 4 for w in ws if w[4] in ("Wasserführung", "Bohrwerkzeuge") and w[1] < y_hdr]
                     + [page.rect.width * 0.6])                                  # Spalte 3
        blocks = [w for w in marks if w[1] > y_hdr]
        code = None                                         # 'B 1 Bohrung Nr.', 'Nr.: B 1 / Blatt 1', 'RKS 1 - Weg'
        for r, t in sorted(plines, key=lambda e: (e[0].y0, e[0].x0)):
            if r.y1 <= y_hdr and (m := SV_CODE_RE.search(re.sub(r"\s+", " ", t))):
                code = m.group(1)
                break
        if code is None or not blocks:
            continue
        rec = out.setdefault(code, {"bottoms": [], "names": [], "gw": [], "gw_status": None, "pages": []})
        rec["pages"].append(pno + 1)
        depths = sorted((w for w in ws if w[2] <= x_a + 1 and w[1] > y_hdr and DEPTH_RE.match(w[4])), key=lambda w: w[1])
        for d in depths:
            blk = [b for b in blocks if b[1] < d[1]]
            if not blk:
                continue
            b = blk[-1]
            y_b = min([w[1] for w in ws if w[4] == "b)" and w[1] > b[1] + 1] + [b[1] + 12])
            name = " ".join(w[4] for w in sorted(ws, key=lambda w: (round(w[1]), w[0]))
                            if b[1] - 3 <= w[1] < y_b - 1 and w[0] > b[2] and w[0] < x_col3 - 2)
            rec["bottoms"].append(float(d[4].rstrip("m ").replace(",", ".")))
            rec["names"].append(name)
        flat = " ".join(txt.split())
        rec["gw"] += [float(m.group(1).replace(",", ".")) for m in SV_GW_RE.finditer(flat)]
        if SV_NO_GW_RE.search(flat):
            rec["gw_status"] = "kein Grundwasser"
    return {k: v for k, v in out.items() if v["bottoms"]}


def find_heads(lines) -> list[tuple[pymupdf.Rect, str]]:
    """E2: Koepfe. Kuerzel (mit Zusatz), 'Bohrung <Code>' (auch zweizeilig), Archivcodes."""
    heads = []
    for r, t in lines:
        t = re.sub(r"\s+", " ", t.strip())
        m = HEAD_RE.match(t) if RULES["head_suffix"] else ID_RE.match(t)
        if m:
            heads.append((r, re.sub(r"\s+", " ", m.group(1) if RULES["head_suffix"] else m.group(0))))
            continue
        if not RULES["generic_heads"]:
            continue
        if (m := ARCHIVE_HEAD_RE.match(t)):
            heads.append((r, m.group(1)))
        elif (m := GENERIC_HEAD_RE.match(t)):
            code = m.group(1)
            if not code:                                  # 'Bohrung' / naechste Zeile '422C-460' (OCR: 'RB' + '2 / I')
                below = sorted([(q, u.strip()) for q, u in lines if -4 < q.y0 - r.y1 < 14
                                and q.x0 < r.x1 + 40 and q.x1 > r.x0 - 40], key=lambda e: (e[0].y0, e[0].x0))
                if below:
                    row = [e for e in below if abs(e[0].y0 - below[0][0].y0) < 3]
                    cand = re.sub(r"\s+", " ", " ".join(u for _, u in sorted(row, key=lambda e: e[0].x0)))
                    if FREE_CODE_RE.fullmatch(cand):
                        code = cand
                        for q, _ in row:
                            r = r | q
            if code and FREE_CODE_RE.fullmatch(code) and re.search(r"\d", code) and not DEPTH_RE.match(code) \
                    and not DATE_RE.search(code):
                heads.append((r, re.sub(r"\s*/\s*", "/", code)))
    return heads


def rows(lines, dy: float = 3.0) -> list[tuple]:
    """Zeilen derselben Hoehe zusammenfuegen (Schriftfeld: 'Hoehe in m ue.M.:' und '668.99' sind getrennte Bloecke)."""
    out: list[list] = []
    for r, t in sorted(lines, key=lambda e: (e[0].y0, e[0].x0)):
        if out and abs(out[-1][0].y0 - r.y0) < dy:
            out[-1][0] = out[-1][0] | r
            out[-1][1].append((r.x0, t))
        else:
            out.append([pymupdf.Rect(r), [(r.x0, t)]])
    return [(r, " ".join(t for _, t in sorted(parts))) for r, parts in out]


def page_gok(lines, y_max: float) -> float | None:
    """Ansatzhoehe aus dem Schriftfeld: 'NHN 45,20 m', 'Hoehe in m ue.M.: 668.99', 'Kote Bezugspunkt: ~788.6 m ue. M.'."""
    for r, t in rows(lines):
        if r.y0 > y_max:
            break
        if (m := GOK_RE.search(t)) or (m := GOK_EXTRA_RE.search(t)):
            return float((m.group(1) or m.group(2)).replace(",", "."))
    return None


def depth_table(words, lines, heads):
    """S6: Schichtenliste als Texttabelle - Spalte streng steigender Tiefen ab 0,00, Beschreibung rechts.

    Nur wenn die Seite genau einen Kopf hat und >= 60 % der Intervalle eine Bodenart ergeben
    (Rammsondier- und Labortabellen enthalten Zahlen, keine Bodenbeschreibung).
    """
    if len({c for _, c in heads}) != 1:
        return None
    groups: dict[int, list] = defaultdict(list)
    for r, t, *_ in words:
        if DEPTH_RE.match(t) and float(t.rstrip("m ").replace(",", ".")) <= 150:
            groups[round(r.x1 / 6)].append((r, float(t.rstrip("m ").replace(",", "."))))
    best = None
    for g in groups.values():
        g = _longest_non_decreasing(sorted(g, key=lambda e: e[0].y0))
        if len(g) < 4 or g[0][1] != 0.0 or _arithmetic(g) or any(b[1] <= a[1] for a, b in zip(g, g[1:])):
            continue
        x1 = max(r.x1 for r, _ in g)
        descs = [" ".join(t for r, t in sorted(lines, key=lambda e: e[0].y0)
                          if x1 + 8 < r.x0 < x1 + 320 and ra.y0 - 2 <= r.y0 < rb.y0 - 2)
                 for (ra, _), (rb, _) in zip(g, g[1:])]
        if sum(bool(classify_v3(d.split(",")[0]) or classify_v3(d)) for d in descs) < 0.6 * len(descs):
            continue
        if best is None or len(g) > len(best[0]):
            best = (g, descs)
    return best


def coords_from_text(lines, anchored) -> dict[str, tuple[float, float, int | None]]:
    """E8: 'Rechtswert (UTM 33N): 394774,3' / 'Hochwert ...' -> naechster Kopf derselben Seite."""
    es, ns = [], []
    for r, t in lines:
        tt = t.replace(" ", "")
        if (m := COORD_E_RE.search(tt)):
            es.append((r, float(m.group(1).replace(",", ".")), UTM_ZONE_RE.search(tt)))
        if (m := COORD_N_RE.search(tt)):
            ns.append((r, float(m.group(1).replace(",", "."))))
    out = {}
    for r, t in rows(lines):
        if (m := LV_COORD_RE.search(t)) and anchored:
            e, n = (float(re.sub(r"[ '’]", "", v).replace(",", ".")) for v in m.groups())
            epsg = 21781 if 480000 <= e <= 840000 and 70000 <= n <= 300000 else \
                2056 if 2480000 <= e <= 2840000 and 1070000 <= n <= 1300000 else None
            if epsg:
                out[anchored[0][1]] = (e, n, epsg)
    for re_, e, zone in es:
        n = min(ns, key=lambda q: abs(q[0].x0 - re_.x0) + abs(q[0].y0 - re_.y0), default=None)
        if n is None or abs(n[0].y0 - re_.y0) > 40:
            continue
        if not anchored:
            continue
        cx = (re_.x0 + re_.x1) / 2
        hr, code, col = min(anchored, key=lambda a: abs(((a[2].rect if a[2] else a[0]).x0
                                                        + (a[2].rect if a[2] else a[0]).x1) / 2 - cx))
        epsg = None
        if 200000 <= e <= 900000 and 5000000 <= n[1] <= 6200000:      # UTM ohne Zonenvorsatz
            epsg = 25800 + int(zone.group(1)) if zone else None
        elif 2000000 <= e <= 5999999:                                   # Gauss-Krueger, Zone = 1. Ziffer
            epsg = 31464 + int(str(int(e))[0])
        out[code] = (e, n[1], epsg)
    return out


def extract(pdf: Path):
    doc = pymupdf.open(pdf)
    swatches = []
    found: dict[str, list[Borehole]] = defaultdict(list)
    dph = {}
    xy_text: dict[str, tuple] = {}
    for pno, page in enumerate(doc):
        words, lines, drawings, segs, scanned, pclass = primitives(page)
        if any("BODENARTEN" in t.upper() for _, t in lines) and not swatches:
            from prototyp_v2 import legend_swatches
            swatches = legend_swatches(page)
        if page.rotation == 0:
            dph.update(soundings(page))
        cols = find_columns(segs, merge_tol=1.6 if scanned else 0.8)   # Scans zeichnen Linien doppelt
        scale_txt = [int(m) for _, t in lines for m in SCALE_RE.findall(t)]
        heads = find_heads(lines)
        anchored: list[tuple] = []
        used = set()
        for hr, code in heads:
            hx = (hr.x0 + hr.x1) / 2
            # bei hoehenmaessiger Darstellung steht der Kopf weit ueber der Saeule -> keine y-Grenze
            cand = [c for c in cols if c.rect.y0 > hr.y1 and abs((c.rect.x0 + c.rect.x1) / 2 - hx) < 70
                    and id(c) not in used]
            if RULES["table_filter"]:                    # Spalte voller Tiefenzahlen = Tiefenspalte des Formblatts
                cand = [c for c in cand if sum(1 for r, t, *_ in words if c.rect.contains(r) and DEPTH_RE.match(t)) < 3]
            if not cand:
                continue
            col = max(cand, key=lambda c: (round(c.weight, 1), len(c.bounds), -(c.rect.y0 - hr.y1),
                                           -abs((c.rect.x0 + c.rect.x1) / 2 - hx)))
            used.add(id(col))
            anchored.append((hr, code, col))
        sheet_anchor = False
        if RULES["single_sheet_anchor"] and not anchored and cols and len({c for _, c in heads}) == 1:
            # Einzelblatt: ein Kopf, irgendwo; das Profil ist die Saeule mit den meisten bestaetigten Labels
            # Labels je Kandidat ohne Konkurrenz zuordnen: im Formblatt steht die Tiefenspalte selbst als 'Saeule'
            scored = []
            for c in cols:
                gs = label_groups(words, c, [c])
                ch = choose_scale(c, gs, scale_txt)
                lf = label_line(gs) if RULES["label_first"] else None
                sc = max(ch[4] if ch else 0, len(lf[2]) if lf else 0)
                if sc >= 3:
                    scored.append((sc, len(c.bounds), c))
            scored = [(sc, c) for sc, _, c in sorted(scored, key=lambda e: (e[0], e[1]))]
            if scored:
                anchored = [(heads[0][0], heads[0][1], max(scored, key=lambda e: e[0])[1])]
                sheet_anchor = True
        # Tabellen aussortieren: in einer Bodensaeule stehen hoechstens kurze Kuerzel, keine Zahlenreihen
        if RULES["table_filter"]:
            anchored = [(hr, code, c) for hr, code, c in anchored
                        if sum(1 for r, t, *_ in words if c.rect.contains(r) and re.search(r"\d", t)
                               and not re.fullmatch(r"[0Oo]+", t)) <= 2]     # OCR liest Kies-Kreise als '000'
        acols = [c for _, _, c in anchored]
        chosen_all = [choose_scale(c, label_groups(words, c, acols), scale_txt) for _, _, c in anchored]
        page_has_labels = any(ch and ch[4] > 0 for ch in chosen_all)
        if RULES["coords_text"]:
            xy_text.update(coords_from_text(lines, anchored))
        for (hr, code, col), chosen in zip(anchored, chosen_all):
            hx = (hr.x0 + hr.x1) / 2
            gok = None
            for r, t in lines:
                if hr.y0 - 2 <= r.y0 <= col.rect.y0 + 4 and abs((r.x0 + r.x1) / 2 - hx) < 90 and (m := GOK_RE.search(t)):
                    gok = float((m.group(1) or m.group(2)).replace(",", "."))
            if gok is None and sheet_anchor:                  # Einzelblatt: Kopfdaten irgendwo ueber dem Profil
                gok = page_gok(lines, col.rect.y0)
            if chosen is None:
                continue
            a, b, mode, pairs, support, n_labels = chosen
            if support == 0 and page_has_labels and RULES["labelless_column"] and not sheet_anchor:
                continue                                    # Nachbarsaeulen haben Labels, diese nicht: Ausbau o. ae.
            lf = None
            if RULES["label_first"] and n_labels >= 5 and support < 0.5 * n_labels:
                lf = label_line(label_groups(words, col, [col] if sheet_anchor else acols))
            if lf:                                           # T4: Grenzen = gedruckte Werte, Linien bestaetigen
                la, lb, g = lf
                bh = Borehole(code, pno + 1, round(la / PT_TO_M_AT_1_1), f"labels ({len(g)} Labels)", gok)
                bh.page_class, bh.fit, bh.support = pclass, (la, lb), len(g) / max(n_labels, 1)
                bh.bbox = tuple(round(v, 1) for v in col.rect)
                line_d = [la * y + lb for y in col.bounds]
                prev = 0.0
                for _, v in sorted(g, key=lambda e: e[1]):
                    if v <= prev:
                        continue
                    ly = Layer(prev, v, label_confirmed=True)
                    if not any(abs(d - v) <= 0.3 for d in line_d):
                        ly.issues.append("Label ohne Linie in +-0,3 m")
                    bh.layers.append(ly)
                    prev = v
                _assign_text(bh, col, lines, words, (la, lb), "labels", [(None, v) for _, v in g],
                             min([c.rect.x0 for c in acols if c.rect.x0 > col.rect.x1 + 5] + [page.rect.x1]))
                if any(NO_GW_RE.search(t) for _, t in lines):
                    bh.gw_status = "kein Grundwasser"
                found[code].append(bh)
                continue
            fit = (a, b)
            bh = Borehole(code, pno + 1, round(a / PT_TO_M_AT_1_1), f"{mode} ({support}/{n_labels} Labels)", gok)
            bh.page_class = pclass
            bh.bbox = tuple(round(v, 1) for v in col.rect)
            bh.fit = (float(a), float(b))
            bh.support = support / n_labels if n_labels else 0.0
            bh.single_sheet = len(anchored) == 1                  # Einzelblatt schlaegt Schnitt/Uebersicht
            bh.titled = any(re.search(rf"(Bohrung|Bohrprofil|Profil|Sondierung)\s+{re.escape(code)}\b", t)
                            for _, t in lines)                     # Schriftfeld 'Bohrung B 4'
            bounds = list(col.bounds)
            depths = [round(float(a * y + b), 2) for y in bounds[1:]]
            confirmed = set()                                   # 1:1 - jedes Label bestaetigt nur die naechste Grenze
            label_by_y = {}                                     # Linie (y) -> gedruckter Wert
            for v in {round(v, 2) for _, v in pairs}:
                i = min(range(len(depths)), key=lambda k: abs(depths[k] - v), default=None)
                if i is not None and abs(depths[i] - v) <= 0.03:
                    confirmed.add(i)
                    label_by_y[bounds[i + 1]] = v
            dropped = []
            if RULES["hatch_continuity"] and bh.support >= 0.6:   # E5: Schraffurlinien statt Grenzen (L6)
                drop = set()
                inner = range(1, len(bounds) - 1)               # bounds[i] <-> depths[i - 1]
                for i in inner:
                    if (i - 1) in confirmed:
                        continue
                    # Begleitlinie: <= 2,5 pt neben einer bestaetigten Grenze (doppelt gezeichnete Linie)
                    if any(abs(bounds[i] - bounds[j]) <= 2.5 for j in inner if (j - 1) in confirmed):
                        drop.add(i)
                    # Doppellinie: zwei unbestaetigte Linien <= 8 pt, dazwischen keine Schraffur (Schwarzdecke)
                    j = i + 1
                    if j in inner and (j - 1) not in confirmed and bounds[j] - bounds[i] <= 8 and \
                            not np.any(hatch_features(drawings, pymupdf.Rect(col.rect.x0 + 0.5, bounds[i] + 0.5,
                                                                             col.rect.x1 - 0.5, bounds[j] - 0.5))):
                        drop |= {i, j}
                if drop:
                    dropped = [depths[i - 1] for i in sorted(drop)]
                    bounds = [y for i, y in enumerate(bounds) if i not in drop]
                    depths = [round(float(a * y + b), 2) for y in bounds[1:]]
                    confirmed = {i for i, y in enumerate(bounds[1:]) if y in label_by_y}
            prev = 0.0
            for i, y in enumerate(bounds[1:]):
                # bestaetigte Grenze: gedruckter Wert statt Geometrie (Zeichengenauigkeit +-1 pt)
                d = label_by_y.get(y, depths[i]) if RULES["label_snap"] else depths[i]
                ly = Layer(prev, d, label_confirmed=i in confirmed)
                if not ly.label_confirmed:
                    ly.issues.append("Grenze ohne bestaetigendes Label")
                rect = pymupdf.Rect(col.rect.x0, a and (prev - b) / a, col.rect.x1, y)
                ly.soil_hatch, _ = classify_hatch(hatch_features(drawings, rect), swatches) if swatches else ("", 0)
                bh.layers.append(ly)
                prev = d
            if dropped:
                bh.issues.append(f"Linien ohne Label mit gleicher Schraffur ober-/unterhalb entfernt: {dropped}")
            right_limit = min([c.rect.x0 for c in acols if c.rect.x0 > col.rect.x1 + 5] + [page.rect.x1])
            _assign_text(bh, col, lines, words, fit, mode, pairs, right_limit)
            bh.gw_depths = _groundwater(drawings, segs, col, acols, fit, words)
            near = [(r, t) for r, t in lines if hr.y0 - 2 <= r.y0 <= col.rect.y1 + 60
                    and abs((r.x0 + r.x1) / 2 - (col.rect.x0 + col.rect.x1) / 2) < 170]
            if not bh.gw_depths and RULES["gw_text"]:       # Symbol als Schriftzeichen: 'GW 2.53m' im Text
                bh.gw_depths = sorted({float((m.group(1) or m.group(2)).replace(",", "."))
                                       for _, t in near if (m := GW_TEXT_RE.search(t))})
            if not bh.gw_depths and RULES["gw_description"]:  # 'Wasseranschnitt 3.8' in der Beschreibung
                desc = [(r, t) for r, t in lines if col.rect.y0 - 4 <= r.y0 <= col.rect.y1 + 4
                        and col.rect.x1 < r.x0 < right_limit]
                bh.gw_depths = sorted({float(m.group(1).replace(",", ".")) for _, t in desc
                                       if (m := WATER_DESC_RE.search(t.replace(" ", "")))})
            if not bh.gw_depths and any(NO_GW_RE.search(t) for _, t in near):
                bh.gw_status = "kein Grundwasser"
            found[code].append(bh)
        if RULES["depth_table"] and heads and not anchored and (tab := depth_table(words, lines, heads)):
            g, descs = tab
            code = heads[0][1]
            bh = Borehole(code, pno + 1, None, f"tabelle ({len(g)} Tiefen)", page_gok(lines, g[0][0].y0))
            bh.page_class = pclass
            bh.support = 1.0
            for (ra, va), (rb, vb), d in zip(g, g[1:], descs):
                bh.layers.append(Layer(va, vb, classify_v3(d.split(",")[0]) or classify_v3(d), label_confirmed=True, text=d))
            if any(NO_GW_RE.search(t) for _, t in lines):
                bh.gw_status = "kein Grundwasser"
            if RULES["coords_text"]:
                xy_text.update(coords_from_text(lines, [(heads[0][0], code, None)]))
            found[code].append(bh)
    coords = coordinate_table(doc)
    sv = schichtenverzeichnis(doc) if RULES["sv_source"] else {}
    out = []
    for code, versions in found.items():
        # GOK gefunden, Labels bestaetigen, groesster Massstab (= kleinste Zahl)
        # schwache Bestaetigung (< 50 %) zaehlt nicht mehr als keine
        if RULES["dup_preference"]:
            best = max(versions, key=lambda v: (v.gok is not None, v.titled, v.single_sheet,
                                                not v.mode.startswith("labels"),      # Linien+Labels vor nur Labels
                                                round(v.support, 1) if v.support >= 0.5 else 0.0, -(v.scale or 1e9)))
        else:
            best = max(versions, key=lambda v: v.support)
        best.duplicates = [f"S.{v.page} M1:{v.scale}" for v in versions if v is not best]
        if code in coords:
            best.east, best.north = coords[code]
            best.coord_source = "tabelle"
        elif code in xy_text:
            best.east, best.north, best.crs = xy_text[code]
            best.coord_source = "text"
        if rec := sv.get(code):
            _cross_check(best, rec)
        out.append(best)
    for code, rec in sv.items():                            # nur im Schichtenverzeichnis (Profil = Bild/SHX)
        if code in found:
            continue
        bh = Borehole(code, rec["pages"][0], None, "schichtenverzeichnis", gw_depths=sorted(set(rec["gw"])),
                      gw_status=None if rec["gw"] else rec["gw_status"])
        prev = 0.0
        for d, name in zip(rec["bottoms"], rec["names"]):
            bh.layers.append(Layer(prev, d, classify_v3(name.split(",")[0]) or classify_v3(name),
                                   label_confirmed=True, text=name))
            prev = d
        bh.cross_check = "nur SV"
        out.append(bh)
    for bh in out:
        _confidence(bh)
    return out, dph


def _confidence(bh: "Borehole") -> None:
    """Konfidenz je Schicht (0..1) aus unabhaengigen Signalen; Begruendung steht in docs/17 §E9."""
    sv_ok = bh.cross_check == "SV ok" or bh.cross_check == "nur SV"
    sv_bad = bh.cross_check.startswith("SV abweichend")
    for ly in bh.layers:
        c = 0.4
        c += 0.3 if ly.label_confirmed else 0.0
        c += 0.2 if sv_ok else (-0.2 if sv_bad else 0.0)
        c += 0.1 if ly.soil else 0.0
        if bh.mode.startswith("massstab-text") and bh.support == 0:
            c -= 0.2                                      # nur Massstab, keine Labels (OCR verloren)
        ly.confidence = round(max(0.0, min(1.0, c)), 2)


def _cross_check(bh: Borehole, rec: dict) -> None:
    """Profil gegen Schichtenverzeichnis: Unterkanten muessen 1:1 uebereinstimmen; Luecken fuellen."""
    prof = [ly.bottom for ly in bh.layers]
    miss = [d for d in rec["bottoms"] if not any(abs(d - p) <= 0.03 for p in prof)]
    extra = [p for p in prof if not any(abs(d - p) <= 0.03 for d in rec["bottoms"])]
    bh.cross_check = "SV ok" if not miss and not extra else f"SV abweichend: fehlt {miss}, nur im Profil {extra}"
    for d, name in zip(rec["bottoms"], rec["names"]):
        for ly in bh.layers:
            if abs(ly.bottom - d) <= 0.03 and not ly.soil:
                ly.soil = classify_v3(name.split(",")[0]) or classify_v3(name)
            if abs(ly.bottom - d) <= 0.03 and not ly.text:
                ly.text = name
    if not bh.gw_depths and rec["gw"]:
        bh.gw_depths = sorted(set(rec["gw"]))
    if not bh.gw_depths and not bh.gw_status and rec["gw_status"]:
        bh.gw_status = rec["gw_status"]


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
             and (re.search(r"[A-Za-zÄÖÜäöü]{3}", t) or ABBR_RE.match(t)) and not DATE_RE.search(t)]
    tops = sorted(v for _, v in pairs)
    if RULES["top_convention"] and not mode.startswith("direkt") and tops and tops[0] == 0.0:
        lab = sorted([(r, float(t.rstrip("m ").replace(",", "."))) for r, t, *_ in words if DEPTH_RE.match(t)
                      and r.x0 > col.rect.x1 and float(t.rstrip("m ").replace(",", ".")) in tops], key=lambda e: e[0].y0)
        for i, (lr, v) in enumerate(lab):
            nxt = lab[i + 1][0].y0 if i + 1 < len(lab) else lr.y0 + 200
            txt = " ".join(t for r, t in right if lr.y0 - 3 <= r.y0 < nxt - 3 and r.x0 >= lr.x1 - 1)
            for ly in bh.layers:
                if abs(ly.top - v) <= 0.03 and txt:
                    ly.soil = classify_v3(txt.split(",")[0]) or classify_v3(txt)
                    ly.text = txt
        if lab:                                           # sonst: Labels links -> Lage im Intervall
            return
    for ly in bh.layers:
        y0, y1 = (ly.top - b) / a, (ly.bottom - b) / a
        txt = " ".join(t for r, t in right if y0 - 2 <= (r.y0 + r.y1) / 2 < y1 + 2)
        if txt:
            ly.soil = classify_v3(txt.split(",")[0]) or classify_v3(txt)
            ly.text = txt


# ---------------------------------------------------------------------------
# E9: kanonisches JSON (docs/ARQUITECTURA_BAUGRUNDMODELL.md §5.1) - Eingang fuer Supabase und IFC
# ---------------------------------------------------------------------------
KIND = (("GWM", "gwm"), ("RKS", "rks"), ("KRB", "rks"), ("BS", "rks"), ("SCH", "schurf"),
        ("BK", "kernbohrung"), ("KB", "kernbohrung"), ("B", "kernbohrung"))
METHOD = {"vektor": "vector", "vektor_ohne_text": "vector+ocr", "raster": "raster+ocr", "raster_ocr": "raster+ocr_layer"}


def _kind(code: str) -> str:
    head = re.match(r"[A-Z]+", code)
    for prefix, kind in KIND:
        if head and head.group(0) == prefix:
            return kind
    return "kernbohrung"                                  # Fremdcodes ('422C-460', 'S 2a'): Bohrung


def to_canonical(pdf: Path, boreholes: list, dph: dict | None = None, version: str = "v4") -> dict:
    data = Path(pdf).read_bytes()
    out = {"document": {"file": Path(pdf).name, "sha256": hashlib.sha256(data).hexdigest(),
                        "parser_version": f"prototyp_{version}", "pages": pymupdf.open(pdf).page_count},
           "boreholes": [], "soundings": {k: [list(map(float, st)) for st in v] for k, v in (dph or {}).items()}}
    for bh in boreholes:
        method = "schichtenverzeichnis" if bh.mode == "schichtenverzeichnis" else METHOD.get(bh.page_class, "vector")
        layers = []
        for ly in bh.layers:
            prov = {"page": bh.page - 1, "method": method}
            if bh.fit and bh.bbox:
                a, b = bh.fit
                prov["bbox"] = [bh.bbox[0], round((ly.top - b) / a, 1), bh.bbox[2], round((ly.bottom - b) / a, 1)]
            layers.append({"top_depth": ly.top, "bottom_depth": ly.bottom, "description_raw": ly.text,
                           "soil_class": ly.soil or None, "hatch_class": ly.soil_hatch or None,
                           "confidence": ly.confidence, "label_confirmed": ly.label_confirmed,
                           "issues": ly.issues, "provenance": [prov]})
        gw = [{"depth": d, "nhn": round(bh.gok - d, 2) if bh.gok is not None else None, "kind": "gemessen"}
              for d in bh.gw_depths]
        out["boreholes"].append({
            "code": bh.code, "kind": _kind(bh.code), "gok_nhn": bh.gok,
            "end_depth": bh.layers[-1].bottom if bh.layers else None,
            "x": bh.east, "y": bh.north, "crs_epsg": bh.crs, "coord_source": bh.coord_source or None,
            "layers": layers, "groundwater": gw, "groundwater_status": bh.gw_status,
            "checks": {"label_support": round(bh.support, 2), "scale": bh.scale, "mode": bh.mode,
                       "schichtenverzeichnis": bh.cross_check or None, "duplicates": bh.duplicates},
            "issues": bh.issues,
            "provenance": [{"page": bh.page - 1, "bbox": list(bh.bbox) if bh.bbox else None, "method": method}]})
    return out


if __name__ == "__main__":                                # python prototyp_v4.py <pdf> [<out.json>]
    src = Path(sys.argv[1])
    bhs, dph = extract(src)
    js = json.dumps(to_canonical(src, bhs, dph), indent=1, ensure_ascii=False)
    if len(sys.argv) > 2:
        Path(sys.argv[2]).write_text(js)
    else:
        print(js)
