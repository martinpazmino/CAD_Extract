"""Vergleich extrahierter Bohrungen mit der Wahrheit der synthetischen PDFs."""
from __future__ import annotations

import json
from pathlib import Path


def load_truth(pdf: Path) -> list[dict]:
    return json.loads(pdf.with_suffix(".json").read_text())


def score(truth: list[dict], found: dict[str, dict], tol: float = 0.02) -> dict:
    """found: code -> {"gok": float|None, "layers": [(top, bottom, soil, text_head)], ...}

    Kennzahlen je Datei:
      boreholes     gefundene / erwartete Bohrungen
      boundaries    Schichtgrenzen mit |Tiefe - Wahrheit| <= tol (Recall)
      soil_ok       Schichten mit richtiger Bodenart (nach Tiefe zugeordnet)
      text_ok       Schichten, deren Text mit dem erwarteten Kopfwort beginnt
    """
    n_bh = len(truth)
    n_b = n_s = n_t = 0
    hit_bh = hit_b = hit_s = hit_t = 0
    for tb in truth:
        fb = found.get(tb["code"])
        n_b += len(tb["layers"])
        n_s += len(tb["layers"])
        n_t += len(tb["layers"])
        if not fb:
            continue
        hit_bh += 1
        bottoms = [ly[1] for ly in fb["layers"] if ly[1] is not None]
        for tl in tb["layers"]:
            if any(abs(b - tl["bottom"]) <= tol for b in bottoms):
                hit_b += 1
            mid = (tl["top"] + tl["bottom"]) / 2
            cand = [ly for ly in fb["layers"] if ly[0] is not None and ly[1] is not None and ly[0] <= mid < ly[1]]
            if cand:
                if cand[0][2] == tl["soil"]:
                    hit_s += 1
                if cand[0][3] and tl["text"].split(",")[0] in cand[0][3]:
                    hit_t += 1
    return {"boreholes": f"{hit_bh}/{n_bh}", "boundaries": f"{hit_b}/{n_b}",
            "soil_ok": f"{hit_s}/{n_s}", "text_ok": f"{hit_t}/{n_t}"}
