"""Oeffentliche Gutachten laden, sichten und mit v1/v2 auswerten (ohne Wahrheit).

    python screen_corpus.py --download <zielordner>          # laedt manifest.tsv (Netzzugang noetig)
    python screen_corpus.py --screen <ordner_mit_pdfs> <out>  # sichtet + wertet aus, schreibt report.md

Die PDFs sind urheberrechtlich geschuetzt: nur intern zum Testen verwenden, nicht ins Repo
committen (siehe docs/12_public_corpus.md). Der Zielordner sollte ausserhalb des Repos liegen.

Sichtung je Seite: Textzeichen, Vektorpfade, Bilder (Bildflaeche > 80 % und kaum Text = Scan),
Schlagworte (Bohrprofil-Indizien). Auswertung ohne Wahrheit = Selbstkonsistenz:
  v1  Bohrungen, NHN-Arithmetik ok
  v3  Bohrungen, Schichten, abgeleiteter Massstab vs. Text 'M 1:xx', Anteil durch Tiefenlabels
      bestaetigter Grenzen, Issues, GW / 'kein Grundwasser', Koordinaten
Mit Wahrheit (groundtruth/*.json): eval_real.py
Dazu ein Vorschaubild je Bohrprofil-Seite fuer die Sichtpruefung.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import urllib.request
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))                       # Repo-Wurzel -> geo_agent
sys.path.insert(0, str(HERE.parent / "extraktion_v2"))          # Prototyp v2

KEYWORDS = ["bohrprofil", "din 4023", "zeichenerkl", "legende", "rammsondierung", "schichtenverzeichnis",
            "kleinrammbohrung", "rammkernsondierung", "bohrung", "dph", "grundwasser", "nhn", "m nn"]
SCALE_RE = re.compile(r"M(?:a(?:ss|ß)stab)?\s*[.:]?\s*1\s*:\s*(\d{2,4})", re.I)


def sha256(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def download(target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with open(HERE / "manifest.tsv", newline="") as f:
        for row in csv.DictReader(f, delimiter="\t"):
            out = target / f"{row['name']}.pdf"
            try:
                urllib.request.urlretrieve(row["url"], out)
                print("ok  ", row["name"], out.stat().st_size, sha256(out)[:12])
            except Exception as e:                                # noqa: BLE001 - nur melden
                print("FAIL", row["name"], e)


def screen_page(page: pymupdf.Page) -> dict:
    text = page.get_text()
    low = text.lower()
    imgs = page.get_image_info()
    area = page.rect.width * page.rect.height
    img_cov = sum(pymupdf.Rect(i["bbox"]).get_area() for i in imgs) / area if area else 0
    n_paths = len(page.get_cdrawings())
    hits = [k for k in KEYWORDS if k in low]
    scale = [int(m) for m in SCALE_RE.findall(text)]
    kind = "scan" if img_cov > 0.8 and len(text) < 200 else "vector" if n_paths >= 25 else "text"
    return {"chars": len(text), "paths": n_paths, "img_cov": round(img_cov, 2), "kind": kind,
            "hits": hits, "scale_text": scale,
            "bohrprofil_candidate": kind == "vector" and len(hits) >= 2}


def evaluate(pdf: Path, out: Path) -> dict:
    from geo_agent.bohrprofil import parse_bohrprofil
    from geo_agent.legend import parse_legend
    from prototyp_v3 import extract

    doc = pymupdf.open(pdf)
    pages = [screen_page(p) for p in doc]
    cand = [i for i, p in enumerate(pages) if p["bohrprofil_candidate"]]
    res = {"file": pdf.name, "sha256": sha256(pdf), "pages": len(pages),
           "producer": doc.metadata.get("producer"), "creator": doc.metadata.get("creator"),
           "vector_pages": sum(p["kind"] == "vector" for p in pages),
           "scan_pages": sum(p["kind"] == "scan" for p in pages),
           "bohrprofil_pages": [i + 1 for i in cand],
           "scale_text": sorted({s for i in cand for s in pages[i]["scale_text"]})}
    try:
        bhs = parse_bohrprofil(doc, parse_legend(doc))
        res["v1"] = {"boreholes": len(bhs), "nhn_ok": sum(1 for b in bhs if b.nhn_check_ok)}
    except Exception as e:                                       # noqa: BLE001
        res["v1"] = {"error": repr(e)[:120]}
    try:
        bhs, dph = extract(pdf)
        layers = [ly for b in bhs for ly in b.layers]
        res["v3"] = {
            "boreholes": len(bhs), "layers": len(layers),
            "scales": sorted({b.scale for b in bhs}),
            "labels_confirm": round(sum(ly.label_confirmed for ly in layers) / len(layers), 2) if layers else None,
            "issues": sum(len(ly.issues) for ly in layers),
            "gw": sum(bool(b.gw_depths) for b in bhs),
            "no_gw": sum(b.gw_status == "kein Grundwasser" for b in bhs),
            "coords": sum(b.east is not None for b in bhs),
            "soundings": len(dph),
        }
    except Exception as e:                                       # noqa: BLE001
        res["v3"] = {"error": repr(e)[:120]}
    for i in cand[:3]:
        doc[i].get_pixmap(dpi=40).save(out / f"{pdf.stem}_p{i + 1}.png")
    return res


def report(rows: list[dict], out: Path) -> None:
    lines = ["| PDF | Seiten | Vektor/Scan | Bohrprofil-Seiten | M (Text) | v1 Bohrungen (NHN ok) | "
             "v3 Bohrungen / Schichten | v3 M | Labels bestaetigt | Issues | GW / kein GW | Koord. |",
             "|" + "---|" * 12]
    for r in rows:
        v1, v3 = r.get("v1", {}), r.get("v3", {})
        lines.append(
            f"| {r['file']} | {r['pages']} | {r['vector_pages']}/{r['scan_pages']} | "
            f"{','.join(map(str, r['bohrprofil_pages'][:8]))} | {r['scale_text']} | "
            f"{v1.get('boreholes', v1.get('error'))} ({v1.get('nhn_ok', '-')}) | "
            f"{v3.get('boreholes', v3.get('error'))} / {v3.get('layers', '-')} | {v3.get('scales', '-')} | "
            f"{v3.get('labels_confirm', '-')} | {v3.get('issues', '-')} | "
            f"{v3.get('gw', '-')} / {v3.get('no_gw', '-')} | {v3.get('coords', '-')} |")
    (out / "report.md").write_text("\n".join(lines) + "\n")
    (out / "report.json").write_text(json.dumps(rows, indent=1, default=str))
    print("\n".join(lines))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--download", type=Path)
    ap.add_argument("--screen", nargs=2, type=Path, metavar=("PDF_DIR", "OUT_DIR"))
    a = ap.parse_args()
    if a.download:
        download(a.download)
    if a.screen:
        src, out = a.screen
        out.mkdir(parents=True, exist_ok=True)
        report([evaluate(p, out) for p in sorted(src.glob("*.pdf"))], out)


if __name__ == "__main__":
    main()
