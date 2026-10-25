"""Echte Gutachten gegen die Wahrheit in groundtruth/*.json bewerten (v1, v3, swissgeol).

    python eval_real.py <ordner_mit_pdfs> [<ordner_mit_swissgeol_predictions>]

Erwartete Dateinamen im PDF-Ordner: <name>.pdf passend zu groundtruth/<name>.json.
swissgeol (optional): <ordner>/real_out_<name>/predictions.json.
Toleranz Schichtgrenzen 5 cm (bei M 1:75 ist 1 pt = 2,6 cm).
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE.parent / "extraktion_v2"))
from geo_agent.bohrprofil import parse_bohrprofil  # noqa: E402
from geo_agent.legend import parse_legend  # noqa: E402
from prototyp_v3 import extract  # noqa: E402

TOL = 0.05


def norm(code: str) -> str:
    return code.replace(" ", "").upper()


def score(gt: dict, found: dict) -> dict:
    """found: norm(code) -> {"gok", "bottoms", "soils", "gw"}"""
    bhs = gt["boreholes"]
    n_b = sum(len(b["layers"]) for b in bhs)
    hit = {"bh": 0, "bound": 0, "soil": 0, "soil_n": 0, "gok": 0, "gok_n": 0, "gw": 0, "gw_n": 0,
           "bound_false": 0, "gw_false": 0}
    for b in bhs:
        f = found.get(norm(b["code"]))
        if b.get("gok") is not None:
            hit["gok_n"] += 1
        hit["gw_n"] += len(b["gw_depths"])
        if not f:
            continue
        hit["bh"] += 1
        free = list(f["bottoms"])                          # 1:1-Zuordnung: jede gefundene Grenze nur einmal
        for ly in b["layers"]:
            m = min(free, key=lambda x: abs(x - ly["bottom"]), default=None)
            if m is not None and abs(m - ly["bottom"]) <= TOL:
                hit["bound"] += 1
                free.remove(m)
            if "soil" in ly:
                hit["soil_n"] += 1
                mid = (ly["top"] + ly["bottom"]) / 2
                s = next((s for (t, bt, s) in f.get("soils", []) if t <= mid < bt), None)
                if s and (s == ly["soil"] or (ly["soil"].startswith("Fels") and s.startswith("Fels"))):
                    hit["soil"] += 1
        if b.get("gok") is not None and f.get("gok") is not None and abs(f["gok"] - b["gok"]) < 0.01:
            hit["gok"] += 1
        hit["gw"] += sum(any(abs(g - x) <= TOL for x in f.get("gw", [])) for g in b["gw_depths"])
        hit["bound_false"] += len(free)
        hit["gw_false"] += sum(not any(abs(x - g) <= TOL for g in b["gw_depths"]) for x in f.get("gw", []))
    extra = len(set(found) - {norm(b["code"]) for b in bhs})
    has_soil = any("soils" in f for f in found.values())
    return {"Bohrungen": f"{hit['bh']}/{len(bhs)}", "Grenzen": f"{hit['bound']}/{n_b}",
            "Bodenart": f"{hit['soil']}/{hit['soil_n']}" if hit["soil_n"] and has_soil else "-",
            "GOK": f"{hit['gok']}/{hit['gok_n']}", "GW": f"{hit['gw']}/{hit['gw_n']}",
            "falsche Bohrungen": extra, "falsche Grenzen": hit["bound_false"], "falsches GW": hit["gw_false"]}


def run_v1(pdf: Path) -> dict:
    doc = pymupdf.open(pdf)
    out = {}
    for b in parse_bohrprofil(doc, parse_legend(doc)):
        out[norm(b.bohr_id)] = {"gok": b.gok_nhn, "bottoms": [ly.bottom_depth for ly in b.layers],
                                "soils": [(ly.top_depth, ly.bottom_depth, ly.bodenart) for ly in b.layers]}
    return out


def run_v3(pdf: Path) -> tuple[dict, list]:
    bhs, _ = extract(pdf)
    out = {norm(b.code): {"gok": b.gok, "bottoms": [ly.bottom for ly in b.layers],
                          "soils": [(ly.top, ly.bottom, ly.soil) for ly in b.layers], "gw": b.gw_depths}
           for b in bhs}
    return out, bhs


def run_sg(pred: Path, name: str) -> dict:
    p = json.loads(pred.read_text())
    p = next(iter(p.values()))
    out = {}
    for b in p["boreholes"]:
        nm = ((b.get("metadata") or {}).get("name") or {}).get("name")
        if not nm:
            nm = f"?{len(out)}"
        ends = [((ly.get("depths") or {}).get("end") or {}).get("value") for ly in b["layers"]]
        el = ((b.get("metadata") or {}).get("elevation") or {}).get("elevation")
        gw = [g.get("depth") for g in (b.get("groundwater") or []) if g.get("depth") is not None]
        key = norm(nm)
        if key in out:                                     # Duplikat (z. B. Schnitt) -> als falsch zaehlen
            key = f"{key}#dup{len(out)}"
        out[key] = {"gok": el, "bottoms": [e for e in ends if e is not None], "gw": gw}
    return out


def gw_table(pdf: Path) -> dict[str, float]:
    """Grundwasserstaende aus Tabellen (Zellen per Clip lesen, siehe docs/07 §2)."""
    import re
    from prototyp_v3 import ID_RE
    out = {}
    doc = pymupdf.open(pdf)
    for page in doc:
        for tab in page.find_tables().tables:
            for row in tab.rows:
                cells = [" ".join(w[4] for w in page.get_text("words", clip=c)) if c else "" for c in row.cells]
                if len(cells) >= 2 and ID_RE.match(cells[0].strip()):
                    m = re.match(r"^(\d+[.,]\d+)", cells[1].strip())
                    if m:
                        out[cells[0].strip()] = float(m.group(1).replace(",", "."))
    return out


def main(pdf_dir: Path, sg_dir: Path | None) -> None:
    for gt_file in sorted((HERE / "groundtruth").glob("*.json")):
        gt = json.loads(gt_file.read_text())
        pdf = pdf_dir / f"{gt_file.stem}.pdf"
        if not pdf.exists():
            continue
        print(f"== {gt_file.stem}")
        print("   v1 ", score(gt, run_v1(pdf)))
        f3, bhs = run_v3(pdf)
        print("   v3 ", score(gt, f3))
        for b in bhs:
            unconf = sum(not ly.label_confirmed for ly in b.layers)
            print(f"        {b.code:6s} S.{b.page} M1:{b.scale} {b.mode:13s} GOK {b.gok} "
                  f"Grenzen {[ly.bottom for ly in b.layers]} GW {b.gw_depths or b.gw_status} "
                  f"Boden {[ly.soil for ly in b.layers]} unbestaetigt {unconf} dup {b.duplicates}")
        if "gw_table" in gt:
            got = gw_table(pdf)
            ok = sum(abs(got.get(k, -99) - v) < 0.005 for k, v in gt["gw_table"].items())
            print(f"   GW-Tabelle: {ok}/{len(gt['gw_table'])} korrekt, {len(set(got) - set(gt['gw_table']))} zusaetzlich")
        if sg_dir and (sg := sg_dir / f"real_out_{gt_file.stem}" / "predictions.json").exists():
            print("   sg ", score(gt, run_sg(sg, gt_file.stem)))


if __name__ == "__main__":
    main(Path(sys.argv[1]), Path(sys.argv[2]) if len(sys.argv) > 2 else None)
