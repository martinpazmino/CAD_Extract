"""Kommandozeile:

    python -m baugrundmodell <modell.ifc> <extraktion.json> [...] [--einheiten e.json] [--methode idw|tps]
                             [--raster m] [--puffer m] [--basis m_NHN] [--bericht b.json] [--ohne-bohrsaeulen]

Der Bericht enthaelt unter "vorlage_einheiten" die vorgeschlagenen Einheiten im Format von --einheiten:
umbenennen, Bodenarten zusammenlegen oder Reihenfolge aendern und erneut aufrufen.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .einheiten import einheiten_aus_vorgabe
from .modell import bauen, bericht, ifc_schreiben


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="baugrundmodell", description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("ifc", type=Path)
    ap.add_argument("jsons", type=Path, nargs="+")
    ap.add_argument("--einheiten", type=Path, help="Vorgabe der Einheiten (JSON-Liste, von oben nach unten)")
    ap.add_argument("--methode", choices=["idw", "tps"], default="idw")
    ap.add_argument("--raster", type=float)
    ap.add_argument("--puffer", type=float)
    ap.add_argument("--basis", type=float)
    ap.add_argument("--bericht", type=Path)
    ap.add_argument("--ohne-bohrsaeulen", action="store_true")
    a = ap.parse_args(argv)
    docs = [json.loads(p.read_text()) for p in a.jsons]
    vorgabe = einheiten_aus_vorgabe(json.loads(a.einheiten.read_text())) if a.einheiten else None
    try:
        m = bauen(docs, vorgabe, a.methode, a.raster, a.puffer, a.basis)
    except ValueError as err:
        print(f"Kein Modell: {err}. Lage und GOK ergaenzen (App: Tabelle 'Bohrungen'; JSON: x, y, gok_nhn).")
        return 2
    ifc_schreiben(m, a.ifc, docs, bohrsaeulen=not a.ohne_bohrsaeulen)
    b = bericht(m)
    if a.bericht:
        a.bericht.write_text(json.dumps(b, ensure_ascii=False, indent=1))
    print(f"{a.ifc}: {len(m.bohrungen)} Bohrungen, {len(m.einheiten)} Einheiten, "
          f"Abweichung an Bohrungen {b['pruefungen']['max_abweichung_an_bohrungen_m']} m, "
          f"geschlossen: {b['pruefungen']['alle_koerper_geschlossen']}")
    for e in b["einheiten"]:
        print(f"  {e['name']:<22} {e['volumen_m3']:>12.1f} m3  max {e['maechtigkeit_max_m']:>6.2f} m  "
              f"vorhanden {len(e['bohrungen']['vorhanden'])} fehlt {len(e['bohrungen']['fehlt'])} "
              f"unbekannt {len(e['bohrungen']['unbekannt'])}")
    for x in m.ausgeschlossen:
        print(f"  nicht im Modell: {x['code']} ({x['grund']})")
    for h in m.hinweise:
        print(f"  Hinweis: {h}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
