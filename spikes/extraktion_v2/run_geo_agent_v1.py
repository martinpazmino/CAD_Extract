"""Heutigen Parser (geo_agent v1) auf die synthetischen Layouts anwenden.

    python run_geo_agent_v1.py <ordner_mit_synth_pdfs>
"""
from __future__ import annotations

import sys
from pathlib import Path

import pymupdf

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # Repo-Wurzel -> geo_agent
from geo_agent.bohrprofil import parse_bohrprofil  # noqa: E402
from geo_agent.legend import parse_legend  # noqa: E402

from eval_utils import load_truth, score  # noqa: E402

# Grobklassen v1 -> Namen der synthetischen Wahrheit
V1_TO_SYNTH = {"Sand": "Sand", "Kies": "Kies", "Schluff": "Schluff", "Ton": "Ton",
               "Geschiebemergel": "Geschiebemergel", "Mutterboden": "Mutterboden"}


def run(pdf: Path) -> dict:
    doc = pymupdf.open(pdf)
    leg = parse_legend(doc)
    bhs = parse_bohrprofil(doc, leg)
    found = {}
    for b in bhs:
        found[b.bohr_id] = {"gok": b.gok_nhn, "layers": [
            (ly.top_depth, ly.bottom_depth, V1_TO_SYNTH.get(ly.bodenart, ly.bodenart), ly.full_text)
            for ly in b.layers]}
    return found


if __name__ == "__main__":
    folder = Path(sys.argv[1])
    for key in ("A", "A2", "A3", "A4", "A5", "B"):
        pdf = folder / f"synth_{key}.pdf"
        found = run(pdf)
        print(f"v1  {key:3s}", score(load_truth(pdf), found))
