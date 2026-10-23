"""swissgeol-Vorhersagen (predictions.json) mit derselben Metrik wie v1/v2 bewerten.

Vorher swissgeol in einer eigenen Umgebung laufen lassen, je Layout:
    boreholes-extract-all -i in_<L> -o out_<L> -p out_<L>/predictions.json --skip-draw-predictions

    python score_swissgeol.py <ordner_mit_synth_pdfs> <ordner_mit_out_L>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))   # Repo-Wurzel -> geo_agent
from geo_agent import soil  # noqa: E402

from eval_utils import load_truth, score  # noqa: E402


def main(synth: Path, outs: Path) -> None:
    for key in ("A", "A2", "A3", "A4", "B"):
        pdf = synth / f"synth_{key}.pdf"
        pred = json.loads((outs / f"out_{key}" / "predictions.json").read_text())[pdf.name]
        found, gw, elev = {}, 0, 0
        for b in pred["boreholes"]:
            name = ((b.get("metadata") or {}).get("name") or {}).get("name")
            if not name:
                continue
            layers, prev = [], 0.0
            for ly in b["layers"]:
                d = ly.get("depths") or {}
                top = (d.get("start") or {}).get("value", prev)
                bot = (d.get("end") or {}).get("value")
                text = (ly.get("material_description") or {}).get("text", "")
                head = soil.normalize_head(text.split(",")[0]) if text else ""
                cls, sure = soil.classify(head) if head else ("", False)
                layers.append((top if top is not None else prev, bot, cls if sure else "", text))
                prev = bot if bot is not None else prev
            found[name] = {"gok": None, "layers": layers}
            gw += bool(b.get("groundwater"))
            elev += (b.get("metadata") or {}).get("elevation") is not None
        print(f"sg  {key:3s}", score(load_truth(pdf), found), f"gw {gw}", f"elevation {elev}",
              f"(Bohrungen erkannt inkl. Fehlalarme: {len(pred['boreholes'])})")


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]))
