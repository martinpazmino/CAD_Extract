"""Ablation: jede Regel einzeln abschalten und messen, welche Faelle schlechter werden.

    python ablation.py --module ../extraktion_v2/prototyp_v4.py --real <pdfs> --stress <ordner> --synth <ordner> \\
                       [--out ablation.md] [--jobs 2]

Eine Regel, deren Abschalten nichts verschlechtert, ist durch keinen Testfall belegt: entweder fehlt
ein Fall (docs/16) oder die Regel ist ueberfluessig.
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import regression as R  # noqa: E402


def run(job):
    module, args, rule = job
    mod = R.load_module(Path(module).resolve())
    if rule:
        mod.RULES[rule] = False
    out = {}
    for name, pdf, gt in R.cases(args):
        try:
            out[name] = R.score(gt, R.found_dict(mod, pdf))
        except Exception as e:
            out[name] = {"Fehler": repr(e)[:100]}
    return rule, out


def worse(new: dict, old: dict) -> list[str]:
    msgs = []
    for k in R.GOOD:
        if k in old and R.frac(new.get(k, "0/0"))[0] < R.frac(old[k])[0]:
            msgs.append(f"{k} {old[k]}→{new.get(k)}")
    for k in R.BAD:
        if new.get(k, 0) > old.get(k, 0):
            msgs.append(f"{k} {old.get(k, 0)}→{new.get(k)}")
    if "Fehler" in new:
        msgs.append("Absturz")
    return msgs


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--module", required=True)
    ap.add_argument("--real"); ap.add_argument("--stress"); ap.add_argument("--synth")
    ap.add_argument("--out", default="ablation.md"); ap.add_argument("--jobs", type=int, default=2)      # OCR-Modell je Prozess: mehr Jobs sprengen den Speicher
    args = ap.parse_args()
    rules = list(R.load_module(Path(args.module).resolve()).RULES)
    with mp.Pool(args.jobs) as pool:
        res = dict(pool.map(run, [(args.module, args, r) for r in [None] + rules]))
    full = res[None]
    lines = ["| Regel abgeschaltet | verschlechterte Faelle | Details |", "|---|---|---|"]
    for r in rules:
        hits = {n: worse(res[r][n], full[n]) for n in full}
        hits = {n: m for n, m in hits.items() if m}
        det = "; ".join(f"{n.split('/', 1)[1]}: {', '.join(m)}" for n, m in hits.items())
        lines.append(f"| `{r}` | {len(hits)} | {det or '— (kein Testfall belegt die Regel)'} |")
    Path(args.out).write_text("\n".join(lines) + "\n")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
