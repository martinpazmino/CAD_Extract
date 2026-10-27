"""Kanonisches Extraktions-JSON (prototyp_v4.to_canonical) -> IFC4X3 (Stufe N1: Bohrsaeulen).

    python export_ifc.py <ausgabe.ifc> <extraktion1.json> [<extraktion2.json> ...]

Jede Bohrung wird IfcBorehole, jede Schicht IfcGeotechnicalStratum (Prisma) mit Herkunft und
Konfidenz in CPset_Schichtenverzeichnis. Mit Koordinaten: georeferenziert (IfcMapConversion,
EPSG aus dem JSON); ohne: Platzhalterposition, ausdruecklich als solche markiert.
Der IFC-Schreiber liegt in services/modeler (baugrundmodell.ifc4x3); das Schichtmodell (N3) erzeugt
`python -m baugrundmodell` dort.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services" / "modeler"))
from baugrundmodell.ifc4x3 import IfcAusgabe  # noqa: E402


def build(out: Path, docs: list[dict]) -> dict:
    bhs = [(d["document"], b) for d in docs for b in d["boreholes"]]
    placed = [b for _, b in bhs if b.get("x") is not None and b.get("crs_epsg")]
    origin = (0.0, 0.0)
    epsg = None
    if placed:
        epsg = placed[0]["crs_epsg"]
        origin = (round(np.mean([b["x"] for b in placed]), -1), round(np.mean([b["y"] for b in placed]), -1))
    aus = IfcAusgabe("Baugrundmodell aus Gutachten", epsg, origin)
    stats = {"boreholes": 0, "strata": 0, "georeferenced": 0, "placeholder": 0}
    for i, (doc, b) in enumerate(bhs):
        geo = b.get("x") is not None and b.get("crs_epsg")
        xy = (b["x"] - origin[0], b["y"] - origin[1]) if geo else (-50.0 - 15.0 * i, -50.0)
        aus.bohrung(doc, b, xy, "georeferenziert" if geo else "unbekannt (Platzhalter)")
        stats["boreholes"] += 1
        stats["strata"] += len(b["layers"])
        stats["georeferenced" if geo else "placeholder"] += 1
    aus.schreiben(out)
    return stats


if __name__ == "__main__":
    out = Path(sys.argv[1])
    docs = [json.loads(Path(p).read_text()) for p in sys.argv[2:]]
    print(build(out, docs))
