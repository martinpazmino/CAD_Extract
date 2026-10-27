"""Blindtest-Protokoll: erst Vorhersagen einfrieren, dann Wahrheit anlegen, dann bewerten.

    python blind_test.py freeze <ordner_mit_neuen_pdfs> <ausgabe>       # vor dem Anschauen der PDFs
    # ... groundtruth/<name>.json anlegen ...
    python blind_test.py score <ausgabe> [<ordner_swissgeol>]           # bewertet die eingefrorenen Dateien

Die eingefrorenen JSON-Dateien enthalten den Code-Stand (git rev) und koennen per sha256 belegt werden.
"""
from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from eval_real import run_sg, run_v1, run_v3, score  # noqa: E402


def freeze(src: Path, out: Path) -> None:
    out.mkdir(parents=True, exist_ok=True)
    rev = subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=HERE, capture_output=True, text=True).stdout.strip()
    for pdf in sorted(src.glob("*.pdf")):
        v3, bhs = run_v3(pdf)
        detail = [{"code": b.code, "page": b.page, "scale": b.scale, "mode": b.mode, "gok": b.gok,
                   "bottoms": [ly.bottom for ly in b.layers], "soils": [ly.soil for ly in b.layers],
                   "unconfirmed": sum(not ly.label_confirmed for ly in b.layers),
                   "gw": b.gw_depths, "gw_status": b.gw_status, "dups": b.duplicates}
                  for b in bhs]
        sha = hashlib.sha256(pdf.read_bytes()).hexdigest()
        (out / f"{pdf.stem}.json").write_text(json.dumps(
            {"code_rev": rev, "pdf_sha256": sha, "v1": run_v1(pdf), "v3": v3, "v3_detail": detail},
            indent=1, default=float))
        print(pdf.stem, "v3 Bohrungen:", len(v3))


def score_frozen(out: Path, sg_dir: Path | None) -> None:
    for pred_file in sorted(out.glob("*.json")):
        gt_file = HERE / "groundtruth" / pred_file.name
        if not gt_file.exists():
            continue
        gt, pred = json.loads(gt_file.read_text()), json.loads(pred_file.read_text())
        print(f"== {pred_file.stem} (Code-Stand {pred.get('code_rev')})")
        print("   v1 ", score(gt, pred["v1"]))
        print("   v3 ", score(gt, pred["v3"]))
        if "sg" in pred:                                   # mit eingefroren (ab Runde 3)
            print("   sg ", score(gt, pred["sg"]))
        elif sg_dir and (sg := sg_dir / f"real_out_{pred_file.stem}" / "predictions.json").exists():
            print("   sg ", score(gt, run_sg(sg, pred_file.stem)))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "freeze":
        freeze(Path(sys.argv[2]), Path(sys.argv[3]))
    else:
        score_frozen(Path(sys.argv[2]), Path(sys.argv[3]) if len(sys.argv) > 3 else None)
