"""Prototyp v2 auf die synthetischen Layouts anwenden und mit der Wahrheit vergleichen.

    python run_prototyp_v2.py <ordner_mit_synth_pdfs>
"""
from __future__ import annotations

import sys
from pathlib import Path

from eval_utils import load_truth, score
from prototyp_v2 import extract


def main(folder: Path) -> None:
    for key in ("A", "A2", "A3", "A4", "A5", "B"):
        pdf = folder / f"synth_{key}.pdf"
        truth = load_truth(pdf)
        bhs, dph = extract(pdf)
        found = {b.code: {"gok": b.gok, "layers": [(ly.top, ly.bottom, ly.soil, ly.text) for ly in b.layers]}
                 for b in bhs}
        s = score(truth, found)
        by_code = {b.code: b for b in bhs}
        n_l = sum(len(t["layers"]) for t in truth)
        hatch_ok = gw_ok = co_ok = gok_ok = 0
        for t in truth:
            b = by_code.get(t["code"])
            if not b:
                continue
            gok_ok += b.gok is not None and abs(b.gok - t["gok"]) < 0.01
            gw_ok += b.gw_depth is not None and abs(b.gw_depth - t["gw_depth"]) <= 0.05
            co_ok += b.east is not None and abs(b.east - t["east"]) < 0.01 and abs(b.north - t["north"]) < 0.01
            for ly, tl in zip(b.layers, t["layers"]):
                hatch_ok += ly.soil_hatch == tl["soil"]
        dph_err = []
        for t in truth:
            steps = dph.get("DPH " + t["code"].split()[1], [])
            for (bot, n), st in zip(t["dph"], steps):
                dph_err.append(abs(st[2] - n))
        scales = sorted({b.scale for b in bhs})
        issues = [f"{b.code} {ly.top}-{ly.bottom}: {i}" for b in bhs for ly in b.layers for i in ly.issues]
        print(f"v2  {key:3s}", s, f"hatch {hatch_ok}/{n_l}", f"gok {gok_ok}/{len(truth)}",
              f"gw {gw_ok}/{len(truth)}", f"coords {co_ok}/{len(truth)}", f"M 1:{scales}",
              f"dph max|dN10|={max(dph_err):.1f} ({len(dph_err)} Stufen)" if dph_err else "",
              f"issues {issues}" if issues else "")


if __name__ == "__main__":
    main(Path(sys.argv[1]))
