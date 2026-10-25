"""Regressionstest der Extraktion: echte Gutachten, Stressfaelle (je Lektion) und synthetische Layouts.

    python regression.py --module ../extraktion_v2/prototyp_v4.py --real <pdfs> --stress <stressordner> \\
                         --synth <synthordner> [--baseline baseline.json] [--write] [--disable regel1,regel2]

Echte PDFs: <real>/<name>.pdf mit groundtruth/<name>.json. Stressfaelle und synthetische Layouts tragen
ihre Wahrheit als JSON neben dem PDF (stress_cases.py, synth_bohrprofil.py).
Mit --baseline wird verglichen: weniger Treffer oder mehr Falsche = REGRESSION (Exit-Code 1).
--disable schaltet Regeln eines Moduls mit RULES-Tabelle ab (Ablation, docs/16).
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent / "extraktion_v2"))
from eval_real import norm, score  # noqa: E402

GOOD = ("Bohrungen", "Grenzen", "Bodenart", "GOK", "GW", "XY", "GW-Status")
BAD = ("falsche Bohrungen", "falsche Grenzen", "falsches GW")


def load_module(path: Path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[path.stem] = mod
    spec.loader.exec_module(mod)
    return mod


def found_dict(mod, pdf: Path) -> dict:
    bhs, _ = mod.extract(pdf)
    return {norm(b.code): {"gok": b.gok, "bottoms": [ly.bottom for ly in b.layers],
                           "soils": [(ly.top, ly.bottom, ly.soil) for ly in b.layers], "gw": b.gw_depths,
                           "gw_status": getattr(b, "gw_status", None),
                           "xy": (b.east, b.north) if getattr(b, "east", None) is not None else None}
            for b in bhs}


def synth_truth(pdf: Path) -> dict:
    t = json.loads(pdf.with_suffix(".json").read_text())
    return {"boreholes": [{"code": b["code"], "gok": b["gok"], "gw_depths": [b["gw_depth"]],
                           "xy": [b["east"], b["north"]],
                           "layers": [{"top": ly["top"], "bottom": ly["bottom"], "soil": ly["soil"]}
                                      for ly in b["layers"]]} for b in t]}


def cases(args) -> list[tuple[str, Path, dict]]:
    out = []
    if args.real:
        for gt in sorted((HERE / "groundtruth").glob("*.json")):
            pdf = Path(args.real) / f"{gt.stem}.pdf"
            if pdf.exists():
                out.append((f"real/{gt.stem}", pdf, json.loads(gt.read_text())))
    if args.stress:
        for js in sorted(Path(args.stress).glob("s*.json")):
            out.append((f"stress/{js.stem}", js.with_suffix(".pdf"), json.loads(js.read_text())))
    if args.synth:
        for pdf in sorted(Path(args.synth).glob("synth_*.pdf")):
            out.append((f"synth/{pdf.stem}", pdf, synth_truth(pdf)))
    return out


def frac(v: str) -> tuple[int, int]:
    a, _, b = str(v).partition("/")
    return (int(a), int(b)) if b else (0, 0)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", required=True)
    ap.add_argument("--real"); ap.add_argument("--stress"); ap.add_argument("--synth")
    ap.add_argument("--baseline"); ap.add_argument("--write", action="store_true")
    ap.add_argument("--disable", default="")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()
    mod = load_module(Path(args.module).resolve())
    for r in filter(None, args.disable.split(",")):
        mod.RULES[r] = False
    results, total = {}, {}
    for name, pdf, gt in cases(args):
        t = time.time()
        try:
            res = score(gt, found_dict(mod, pdf))
        except Exception as e:                       # Absturz = alles verloren, aber weiter testen
            res = {"Fehler": repr(e)[:120]}
        results[name] = res
        for k, v in res.items():
            if k in GOOD:
                a, b = frac(v); x = total.setdefault(k, [0, 0]); x[0] += a; x[1] += b
            elif k in BAD:
                total[k] = total.get(k, 0) + v
        if not args.quiet:
            print(f"{name:34s} {time.time() - t:5.1f}s", {k: v for k, v in res.items() if v not in ('0/0', 0, '-')})
    print("SUMME", {k: (f"{v[0]}/{v[1]}" if isinstance(v, list) else v) for k, v in total.items()})
    status = 0
    if args.baseline and Path(args.baseline).exists() and not args.write:
        base = json.loads(Path(args.baseline).read_text())
        for name, res in results.items():
            old = base.get(name)
            if not old:
                continue
            for k in GOOD:
                if k in old and frac(res.get(k, "0/0"))[0] < frac(old[k])[0]:
                    print(f"REGRESSION {name}: {k} {old[k]} -> {res.get(k)}"); status = 1
            for k in BAD:
                if res.get(k, 0) > old.get(k, 0):
                    print(f"REGRESSION {name}: {k} {old.get(k)} -> {res.get(k)}"); status = 1
            if "Fehler" in res:
                print(f"REGRESSION {name}: {res['Fehler']}"); status = 1
        print("OK: keine Regression" if status == 0 else "FEHLGESCHLAGEN")
    if args.write and args.baseline:
        Path(args.baseline).write_text(json.dumps(results, indent=1, ensure_ascii=False))
        print("Baseline geschrieben:", args.baseline)
    return status


if __name__ == "__main__":
    sys.exit(main())
