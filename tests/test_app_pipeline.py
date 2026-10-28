"""App v2 ohne Oberflaeche: Projektzustand (ui/projekt.py) und Ablauf (ui/pipeline.py)."""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from ui import pipeline as pl  # noqa: E402
from ui import projekt as pj  # noqa: E402

BEISPIELE = REPO / "data" / "beispiele"


def lade(name: str) -> list[dict]:
    return [json.loads((BEISPIELE / name).read_text(encoding="utf-8"))]


def projekt(docs):
    return pj.neues_projekt(docs, "test")


def rechnen(docs, p, e=None):
    e = e or pj.Einstellungen()
    v = pj.modell_eingabe(docs, p, e)
    return v, pl.modell_rechnen(v.docs, p.vorgabe, e.methode, e.puffer, e.raster, e.basis, pj.ursprung(p, v))


def zeile(zeilen, code):
    return next(z for z in zeilen if z["Bohrung"] == code)


def test_ohne_koordinaten_reihe_mit_standardabstand():
    docs = lade("talheim.json")
    p = projekt(docs)
    assert p.lage_modus == pj.LAGE_REIHE
    v, e = rechnen(docs, p)
    assert all(q == "schematisch" for _, _, q in v.lage.values())
    assert any("Standardabstand" in h for h in v.hinweise) and any("ohne GOK" in h for h in v.hinweise)
    assert len(e.bericht["bohrungen"]) == 8
    gruende = {a["code"]: a["grund"] for a in e.bericht["ausgeschlossen"]}
    assert gruende["GWM1"] == "keine Koordinaten, Ansatzhoehe (GOK) unbekannt"


def test_reihe_mit_eigenen_abstaenden_und_station_aus_dem_schnitt():
    """BK1 -> BK2 10 m, BK2 -> BK3 15 m; BK4 im Schnitt auf Station 70 gesetzt; danach Standardabstand."""
    docs = lade("talheim.json")
    p = projekt(docs)
    ids = [z["id"] for z in pj.bohrungen_zeilen(docs, p) if z["Modell"]]
    zeilen = pj.reihe_zeilen(docs, p, ids)
    zeile(zeilen, "BK2")["Abstand zum Vorgänger [m]"] = 10.0
    zeile(zeilen, "BK3")["Abstand zum Vorgänger [m]"] = 15.0
    assert pj.reihe_uebernehmen(docs, p, ids, zeilen)
    bk4 = zeile(pj.reihe_zeilen(docs, p, ids), "BK4")["id"]
    assert pj.ereignis_anwenden(p, {"nr": 1, "typ": "station", "id": bk4, "station": 70.0})
    st = {z["Bohrung"]: z["Station [m]"] for z in pj.reihe_zeilen(docs, p, ids)}
    assert st["BK1"] == 0 and st["BK2"] == 10 and st["BK3"] == 25 and st["BK4"] == 70 and st["BK5"] == 90
    v, e = rechnen(docs, p)
    quellen = {e_["code"]: e_["lage"] for e_ in e.bericht["bohrungen"]}
    assert quellen["BK2"] == "Reihe (Abstand manuell)" and quellen["BK4"] == "Reihe (Station im Schnitt gesetzt)"
    x = {b["code"]: b["x"] for b in e.bericht["bohrungen"]}
    assert x["BK3"] == 25 and x["BK4"] == 70
    assert not pj.ereignis_anwenden(p, {"nr": 1, "typ": "station", "id": bk4, "station": 99.0})   # schon angewendet


def test_gok_im_schnitt_gezogen():
    """Ansatzhoehe aus dem Laengsschnitt (Umschalt+Ziehen im Viewer) gilt als manuelle GOK."""
    docs = lade("talheim.json")
    p = projekt(docs)
    bk1 = next(z["id"] for z in pj.bohrungen_zeilen(docs, p) if z["Bohrung"] == "BK1")
    assert pj.ereignis_anwenden(p, {"nr": 1, "typ": "gok", "id": bk1, "gok": 231.45})
    assert zeile(pj.bohrungen_zeilen(docs, p), "BK1")["GOK [m NHN]"] == 231.45
    b = next(b for i, _, b in pj.bohrungen(pj.wirksame_docs(docs, p)) if i == bk1)
    assert b["gok_nhn"] == 231.45 and b["gok_source"] == "manuell"


def test_reihenfolge_aendern():
    docs = lade("talheim.json")
    p = projekt(docs)
    ids = [z["id"] for z in pj.bohrungen_zeilen(docs, p) if z["Modell"]]
    zeilen = pj.reihe_zeilen(docs, p, ids)
    zeile(zeilen, "BK8")["Nr"] = 0.5                     # BK8 an den Anfang
    pj.reihe_uebernehmen(docs, p, ids, zeilen)
    assert pj.reihe_zeilen(docs, p, ids)[0]["Bohrung"] == "BK8"


def test_tabelle_korrektur_und_rueckgaengig():
    docs = lade("berlin_v67b.json")
    p = projekt(docs)
    zeilen = pj.bohrungen_zeilen(docs, p)
    z = zeile(zeilen, "S2a")
    z.update({"Rechtswert": 394800.0, "Hochwert": 5818400.0, "EPSG": 25833, "GOK [m NHN]": 36.6})
    assert pj.bohrungen_uebernehmen(docs, p, zeilen)
    v, e = rechnen(docs, p)
    s2a = next(x for x in e.bericht["bohrungen"] if x["code"] == "S2a")
    assert s2a["lage"] == "manuell (Tabelle)" and s2a["hoehe"].startswith("manuell")
    zeilen = pj.bohrungen_zeilen(docs, p)
    zeile(zeilen, "S2a").update({"Rechtswert": None, "Hochwert": None, "EPSG": None, "GOK [m NHN]": 36.52})
    pj.bohrungen_uebernehmen(docs, p, zeilen)
    assert p.bohrung == {}                               # zurueck auf PDF-Werte: keine Korrektur mehr


def test_verschieben_im_viewer_auf_kalibriertem_plan():
    docs = lade("berlin_v67b.json")
    p = projekt(docs)
    p.unterlage = {"art": "draufsicht", "kalibrierung": None}
    pj.ereignis_anwenden(p, {"nr": 1, "typ": "kalibrierung", "punkte": [[0, 0, 394700, 5818300], [100, 0, 394900, 5818300]],
                             "epsg": 25833})
    s2a = zeile(pj.bohrungen_zeilen(docs, p), "S2a")["id"]
    pj.ereignis_anwenden(p, {"nr": 2, "typ": "lage", "id": s2a, "x": 394810.0, "y": 5818420.0})
    v, e = rechnen(docs, p)
    x = next(b for b in e.bericht["bohrungen"] if b["code"] == "S2a")
    assert x["lage"] == "Plan (kalibriert)" and x["x"] == 394810.0 and e.bericht["epsg"] == 25833
    assert p.version == 2


def test_schichten_korrigieren_und_pruefen(tmp_path):
    import ifcopenshell
    docs = lade("demo_synthetisch.json")
    p = projekt(docs)
    bid = pj.bohrungen_zeilen(docs, p)[0]["id"]
    zeilen = pj.schichten_zeilen(docs, p, bid)
    zeilen[0]["Bodenart"] = "Schluff"
    zeilen[1]["Geprüft"] = True
    assert pj.schichten_uebernehmen(docs, p, bid, zeilen)
    st = pj.pruefstand(docs, p)
    assert st["korrigiert"] == 1 and st["schichten"][0] == 2       # korrigiert zaehlt als geprueft
    eff = pj.wirksame_docs(docs, p)[0]["boreholes"][0]["layers"]
    assert eff[0]["soil_class"] == "Schluff" and eff[0]["korrigiert"] and eff[0]["confidence"] == 1.0
    pj.alle_schichten_pruefen(docs, p, bid)
    zeilen = pj.schichten_zeilen(docs, p, bid)
    assert all(z["Geprüft"] for z in zeilen)
    v, e = rechnen(docs, p)
    pfad = tmp_path / "m.ifc"
    pfad.write_bytes(e.ifc)
    f = ifcopenshell.open(str(pfad))
    korr = [pv.NominalValue.wrappedValue for pv in f.by_type("IfcPropertySingleValue") if pv.Name == "Korrigiert"]
    assert korr == [True]


def test_einchecken():
    docs = lade("demo_synthetisch.json")
    p = projekt(docs)
    eintrag = pj.einchecken(docs, p, "modellschluessel1", "erste Sichtung")
    assert eintrag["nr"] == 1 and eintrag["stand"]["bohrungen"] == [0, 12]
    assert "v1" in pj.stand_text(eintrag) and not pj.seit_einchecken_geaendert(docs, p, "modellschluessel1")
    assert pj.seit_einchecken_geaendert(docs, p, "anderesmodell")     # Modell neu gerechnet (andere Eingaben)
    zeilen = pj.bohrungen_zeilen(docs, p)
    zeilen[0]["Geprüft"] = True
    pj.bohrungen_uebernehmen(docs, p, zeilen)
    assert pj.seit_einchecken_geaendert(docs, p, "modellschluessel1")


def test_relative_hoehen_wenn_alle_ohne_gok():
    docs = lade("demo_synthetisch.json")
    for b in docs[0]["boreholes"]:
        b["gok_nhn"] = None
    p = projekt(docs)
    v, e = rechnen(docs, p)
    assert all(b["gok_source"] == "relativ" for b in v.docs[0]["boreholes"])
    assert any("relative Hoehen" in h for h in e.bericht["hinweise"])


def test_abwaehlen_und_doppelte():
    docs = lade("berlin_v67b.json") * 2
    p = projekt(docs)
    zeilen = pj.bohrungen_zeilen(docs, p)
    zweite = [z for z in zeilen if z["id"].startswith("1:")]
    assert all(not z["Modell"] for z in zweite) and all("doppelt" in z["Hinweise"] for z in zweite)
    zeilen[0]["Modell"] = False
    pj.bohrungen_uebernehmen(docs, p, zeilen)
    v = pj.modell_eingabe(docs, p, pj.Einstellungen())
    gruende = [r["grund"] for r in v.nicht_im_modell]
    assert "abgewaehlt" in gruende and any(g.startswith("doppelt") for g in gruende)


def test_viewer_bohrungen_und_fester_ursprung():
    docs = lade("berlin_v67b.json")
    p = projekt(docs)
    v, e = rechnen(docs, p)
    stecknadeln = pj.viewer_bohrungen(docs, p, v, e.bericht)
    s2a = next(s for s in stecknadeln if s["code"] == "S2a")
    assert s2a["x"] is None and not s2a["im_modell"]       # ohne Lage: im Viewer zum Platzieren
    oben, unten, farbe, art, konf, gep = s2a["schichten"][0]   # je Schicht: Tiefen, Farbe, Bodenart, Konfidenz, geprueft
    assert unten > oben and farbe.startswith("#") and isinstance(art, str) and 0 <= konf <= 1 and gep is False
    assert e.bericht["ursprung"] == list(p.ursprung) or tuple(e.bericht["ursprung"]) == p.ursprung
    alt = p.ursprung
    pj.ereignis_anwenden(p, {"nr": 1, "typ": "lage", "id": next(s["id"] for s in stecknadeln if s["code"] == "422C-460"),
                             "x": 394780.0, "y": 5818330.0})
    v2, e2 = rechnen(docs, p)
    assert p.ursprung == alt                               # Ansicht springt nicht


def test_projekt_speichern_und_laden():
    docs = lade("talheim.json")
    p = projekt(docs)
    ids = [z["id"] for z in pj.bohrungen_zeilen(docs, p)]
    pj.ereignis_anwenden(p, {"nr": 3, "typ": "station", "id": ids[1], "station": 12.5})
    pj.alle_schichten_pruefen(docs, p, ids[0])
    pj.einchecken(docs, p, "abc", "erster Stand")
    p.ursprung = (100.0, 0.0)
    q = pj.laden(json.loads(json.dumps(pj.speichern(p))))
    assert q == p and q.viewer_nr == 3 and q.ursprung == (100.0, 0.0)
    assert pj.pruefstand(docs, q) == pj.pruefstand(docs, p)


def test_vor_dem_erzeugen_zeigt_der_viewer_was_ins_modell_kaeme():
    docs = lade("berlin_v67b.json")
    p = projekt(docs)
    v = pj.modell_eingabe(docs, p, pj.Einstellungen())
    nadeln = {n["code"]: n for n in pj.viewer_bohrungen(docs, p, v, None)}
    assert nadeln["S2a"]["im_modell"] is False and nadeln["S2a"]["grund"] == "ohne Lage"
    assert sum(n["im_modell"] for n in nadeln.values()) == len(v.lage)


def test_plan_seite_rendern():
    pdf = (BEISPIELE / "synthetisch_bohrprofil.pdf").read_bytes()
    r = pl.unterlage_rendern(pdf, 0, max_px=2000)
    assert r["png"][:8] == b"\x89PNG\r\n\x1a\n" and max(r["breite"], r["hoehe"]) <= 2000 and r["seiten"] >= 1


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
    assert time.time() - t < 2.0
    p = projekt([doc])
    v, e = rechnen([doc], p)
    assert e.bericht["pruefungen"]["alle_koerper_geschlossen"]
