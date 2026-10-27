"""Ablauf der App v2 ohne Oberflaeche (ui/pipeline.py): Korrekturen, schematische Lage, Modell, PDF."""
from __future__ import annotations

import copy
import json
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from ui import pipeline as pl  # noqa: E402

BEISPIELE = REPO / "data" / "beispiele"


def lade(name: str) -> list[dict]:
    return [json.loads((BEISPIELE / name).read_text(encoding="utf-8"))]


def test_schematisch_nur_ohne_koordinaten_und_mit_gok():
    docs = lade("talheim.json")
    v = pl.vorbereiten(docs, pl.zeilen(docs), pl.Einstellungen())
    alle = {b["code"]: b for b in v.docs[0]["boreholes"]}
    assert alle["BK1"]["coord_source"] == "schematisch" and alle["BK1"]["crs_epsg"] is None
    assert alle["GWM1"].get("x") is None                      # ohne GOK: keine Lage erfunden
    assert any("schematisch" in h for h in v.hinweise) and any("ohne GOK" in h for h in v.hinweise)
    assert docs[0]["boreholes"][0].get("coord_source") is None  # Eingabe bleibt unveraendert
    e = pl.modell_rechnen(v.docs)
    assert e.ifc.startswith(b"ISO-10303-21") and len(e.bericht["bohrungen"]) == 8
    gruende = {a["code"]: a["grund"] for a in e.bericht["ausgeschlossen"]}
    assert gruende["GWM1"] == "keine Koordinaten, Ansatzhoehe (GOK) unbekannt"


def test_weglassen_ergibt_kein_modell():
    docs = lade("talheim.json")
    v = pl.vorbereiten(docs, pl.zeilen(docs), pl.Einstellungen(ohne_lage="weglassen"))
    with pytest.raises(ValueError):
        pl.modell_rechnen(v.docs)


def test_manuelle_korrektur_wird_markiert():
    docs = lade("berlin_v67b.json")
    zeilen = pl.zeilen(docs)
    s2a = next(z for z in zeilen if z["Bohrung"] == "S2a")
    s2a.update({"Rechtswert": 394800.0, "Hochwert": 5818400.0, "EPSG": 25833, "GOK [m NHN]": 36.6})
    v = pl.vorbereiten(docs, zeilen, pl.Einstellungen())
    b = next(b for b in v.docs[0]["boreholes"] if b["code"] == "S2a")
    assert b["coord_source"] == "manuell" and b["gok_source"] == "manuell" and b["gok_nhn"] == 36.6
    e = pl.modell_rechnen(v.docs)
    eintrag = next(x for x in e.bericht["bohrungen"] if x["code"] == "S2a")
    assert eintrag["lage"] == "manuell" and eintrag["hoehe"].startswith("manuell")


def test_abwaehlen_und_doppelte():
    docs = lade("berlin_v67b.json") * 2                      # dasselbe Dokument zweimal
    zeilen = pl.zeilen(docs)
    zweite = [z for z in zeilen if z["id"].startswith("1:")]
    assert all(not z["Modell"] for z in zweite) and all("doppelt" in z["Hinweise"] for z in zweite)
    zeilen[0]["Modell"] = False
    v = pl.vorbereiten(docs, zeilen, pl.Einstellungen())
    assert any(r["grund"] == "abgewaehlt" for r in v.nicht_im_modell)


def test_relative_hoehen_wenn_alle_ohne_gok():
    docs = lade("demo_synthetisch.json")
    docs = copy.deepcopy(docs)
    for b in docs[0]["boreholes"]:
        b["gok_nhn"] = None
    v = pl.vorbereiten(docs, pl.zeilen(docs), pl.Einstellungen())
    assert all(b["gok_source"] == "relativ" and b["gok_nhn"] == 0.0 for b in v.docs[0]["boreholes"])
    e = pl.modell_rechnen(v.docs)
    assert any("relative Hoehen" in h for h in e.bericht["hinweise"])


def test_pdf_extraktion_mit_fortschritt_und_ablage(tmp_path, monkeypatch):
    monkeypatch.setattr(pl, "ARBEIT", tmp_path)
    daten = (BEISPIELE / "synthetisch_bohrprofil.pdf").read_bytes()
    seiten = []
    doc = pl.pdf_extrahieren("mein bohrprofil.pdf", daten, ocr=False, fortschritt=lambda i, n, k: seiten.append((i, n, k)))
    assert doc["document"]["file"] == "mein bohrprofil.pdf" and len(doc["boreholes"]) == 3
    assert seiten and seiten[-1][0] == seiten[-1][1]
    assert pl.ist_extrahiert(daten, False)
    t = time.time()
    assert pl.pdf_extrahieren("anders.pdf", daten, ocr=False)["boreholes"] == doc["boreholes"]
    assert time.time() - t < 2.0                              # aus der Ablage
    v = pl.vorbereiten([doc], pl.zeilen([doc]), pl.Einstellungen())
    assert pl.modell_rechnen(v.docs).bericht["pruefungen"]["alle_koerper_geschlossen"]
