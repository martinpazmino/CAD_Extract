"""Schreibt die Ergebnis-.xlsx exakt nach Geo_Template.

Blatt 1 Geomodul                : Bohr_ID, NHN, Tiefe, Rechtswert, Hochwert
Blatt 2 Geomodul_Bodenschicht   : ID, Bodenart, Tiefe(oberkante)
Blatt 3 Geo_Tunnel              : Bohr_BID, NHN, OK Tunnel bis GOK, OK Tunnel,
                                  Achse, Tunnelmeter, Bodenart auf Tunnel
Blatt 4 Geo_Spec  (dynamisch)   : bodenart, abschnitt_id,
                                  Prozent_Bodenart_pro_abschnitt, bohr_id,
                                  Tunnelmeter + dynamische DIN-Spalten.

Zellfaerbung: sicher = gruen, unsicher/nicht klassifizierbar = gelb.
"""
from __future__ import annotations

import io
from collections import Counter

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from . import soil, bohrprofil

GREEN = PatternFill("solid", fgColor="C6EFCE")
YELLOW = PatternFill("solid", fgColor="FFEB9C")
HEADER_FILL = PatternFill("solid", fgColor="305496")
HEADER_FONT = Font(bold=True, color="FFFFFF")

# Spaltenueberschriften der dynamischen DIN-Spalten in Blatt 4
DIN_COL_HEADER = {
    "kornbereich": "kornbereich",
    "nebenanteil_staerke": "nebenanteil_staerke",
    "kalkgehalt": "kalkgehalt",
    "konsistenz": "konsistenz",
}


def _write_sheet(ws, headers, rows, sure):
    ws.append(headers)
    for c in range(1, len(headers) + 1):
        cell = ws.cell(1, c)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(horizontal="center", vertical="center")
    for r_idx, (row, srow) in enumerate(zip(rows, sure), start=2):
        for c_idx, val in enumerate(row, start=1):
            cell = ws.cell(r_idx, c_idx, val)
            ok = srow[c_idx - 1]
            if ok is True:
                cell.fill = GREEN
            elif ok is False:
                cell.fill = YELLOW
            # ok is None -> keine Faerbung (neutral)
    # Spaltenbreiten
    for c in range(1, len(headers) + 1):
        ws.column_dimensions[get_column_letter(c)].width = max(12, len(str(headers[c - 1])) + 3)
    ws.freeze_panes = "A2"


# ---------------------------------------------------------------------------
# Blatt 4: Geo_Spec-Zeilen + DIN-Werte aus den Bohrungen ableiten
# ---------------------------------------------------------------------------
def _din_for(bohr_id, bodenart, key, boreholes_by_id):
    """Haeufigster DIN-Wert dieser Bodenart in der zugeordneten Bohrung."""
    bh = boreholes_by_id.get(bohr_id)
    if not bh:
        return None
    vals = []
    for ly in bh.layers:
        if ly.bodenart != bodenart:
            continue
        v = soil.parse_din(key, ly.head_word, ly.full_text)
        if v:
            vals.append(v)
    if not vals:
        return None
    return Counter(vals).most_common(1)[0][0]


def build_geospec_rows(boreholes, abschnitte, selected_din_keys, min_pct=5):
    """Eine Zeile je (Abschnitt x Bodenart >= min_pct%)."""
    boreholes_by_id = {b.bohr_id: b for b in boreholes}
    headers = ["bodenart", "abschnitt_id", "Prozent_Bodenart_pro_abschnitt",
               "bohr_id", "Tunnelmeter"] + [DIN_COL_HEADER[k] for k in selected_din_keys]
    rows, sure = [], []
    for ab in abschnitte:
        tm = f"{ab.tm_start}-{ab.tm_end}"
        comp = ab.composition or {}
        items = [(k, v) for k, v in comp.items() if v >= min_pct]
        if not items and comp:                       # mind. die dominante Bodenart
            items = [max(comp.items(), key=lambda kv: kv[1])]
        for bodenart, pct in items:
            row = [bodenart, ab.abschnitt_id, pct, ab.bohr_id, tm]
            srow = [True, True, True, ab.bohr_id is not None, True]
            for k in selected_din_keys:
                v = _din_for(ab.bohr_id, bodenart, k, boreholes_by_id)
                row.append(v if v is not None else "")
                srow.append(v is not None)
            rows.append(row)
            sure.append(srow)
    return headers, rows, sure


# ---------------------------------------------------------------------------
# Abschnitte mit Bohrprofil-Daten anreichern (Bodenart auf Tunnel + Anteile)
# ---------------------------------------------------------------------------
def enrich_abschnitte(boreholes, abschnitte):
    """Setzt je Abschnitt Bodenart & Zusammensetzung aus den BOHRPROFIL-Schichten
    (nicht aus dem Laengsschnitt): Tiefe der Tunnelachse/-querschnitt unter der
    GOK der zugehoerigen Bohrung -> Schicht(en) aus Blatt 2.
    """
    import dataclasses
    by_id = {b.bohr_id: b for b in boreholes}
    out = []
    for ab in abschnitte:
        bh = by_id.get(ab.bohr_id)
        bodenart, comp, sure = None, {}, False
        if bh and bh.gok_nhn is not None and ab.achse_nhn is not None:
            achse_depth = round(bh.gok_nhn - ab.achse_nhn, 2)
            ly = bohrprofil.layer_at_depth(bh, achse_depth)
            if ly:
                bodenart = ly.bodenart
                within = bh.total_depth is None or achse_depth <= bh.total_depth + 0.05
                sure = ly.bodenart_sure and within
            if ab.ok_nhn is not None and ab.sohle_nhn is not None:
                comp = bohrprofil.composition_in_range(
                    bh, bh.gok_nhn - ab.ok_nhn, bh.gok_nhn - ab.sohle_nhn)
        out.append(dataclasses.replace(
            ab, bodenart=bodenart, bodenart_sure=sure, composition=comp,
            prozent=comp.get(bodenart, 0) if (comp and bodenart) else 0))
    return out


# ---------------------------------------------------------------------------
# Workbook bauen
# ---------------------------------------------------------------------------
def build_workbook(boreholes, abschnitte, selected_din_keys) -> Workbook:
    wb = Workbook()

    # --- Blatt 1: Geomodul ---
    ws1 = wb.active
    ws1.title = "Geomodul"
    rows, sure = [], []
    for b in boreholes:
        rows.append([b.bohr_id, b.gok_nhn, b.total_depth, "", ""])
        sure.append([True, b.gok_nhn is not None, b.total_depth is not None,
                     False, False])  # Rechts-/Hochwert nicht im PDF -> gelb
    _write_sheet(ws1, ["Bohr_ID", "NHN", "Tiefe", "Rechtswert", "Hochwert"], rows, sure)

    by_id = {b.bohr_id: b for b in boreholes}

    # --- Blatt 2: Geomodul_Bodenschicht ---
    # Wiederholte Bodenarten je Bohrung durchnummerieren: Sand, Sand1, Sand2 ...
    ws2 = wb.create_sheet("Geomodul_Bodenschicht")
    rows, sure = [], []
    for b in boreholes:
        seen: dict[str, int] = {}
        for ly in b.consolidated:
            n = seen.get(ly.bodenart, 0)
            label = ly.bodenart if n == 0 else f"{ly.bodenart}{n}"
            seen[ly.bodenart] = n + 1
            rows.append([b.bohr_id, label, ly.top_depth])
            sure.append([True, ly.bodenart_sure, True])
    _write_sheet(ws2, ["Bohr_ID", "Bodenart", "Tiefe(oberkante)"], rows, sure)

    # --- Blatt 3: Geo_Tunnel (eine Zeile je Bohrungs-Abschnitt) ---
    # NHN = GOK der zugehoerigen Bohrung; OK Tunnel bis GOK = GOK - OK Tunnel;
    # Bodenart auf Tunnel kommt aus den Bohrprofil-Schichten (s. enrich_abschnitte).
    ws3 = wb.create_sheet("Geo_Tunnel")
    rows, sure = [], []
    for ab in abschnitte:
        bh = by_id.get(ab.bohr_id)
        nhn = bh.gok_nhn if bh else None
        ok = ab.ok_nhn
        obg = round(nhn - ok, 2) if (nhn is not None and ok is not None) else None
        rows.append([ab.bohr_id, nhn, obg, ok, ab.achse_nhn, ab.sohle_nhn, ab.bohr_tm,
                     ab.bodenart if ab.bodenart else ""])
        sure.append([ab.bohr_id is not None, nhn is not None, obg is not None,
                     ok is not None, ab.achse_nhn is not None, ab.sohle_nhn is not None,
                     ab.bohr_tm is not None, ab.bodenart_sure if ab.bodenart else False])
    _write_sheet(ws3, ["Bohr_BID", "NHN", "OK Tunnel bis GOK", "OK Tunnel",
                       "Achse", "Sohle Tunnel", "Tunnelmeter", "Bodenart auf Tunnel"], rows, sure)

    # --- Blatt 4: Geo_Spec (dynamisch) ---
    ws4 = wb.create_sheet("Geo_Spec")
    headers, rows, sure = build_geospec_rows(boreholes, abschnitte, selected_din_keys)
    _write_sheet(ws4, headers, rows, sure)

    return wb


def workbook_bytes(boreholes, abschnitte, selected_din_keys) -> bytes:
    wb = build_workbook(boreholes, abschnitte, selected_din_keys)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()
