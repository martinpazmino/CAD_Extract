"""Baugrundmodell-App ohne Oberflaeche: Projektzustand (ui/projekt.py) und Ablauf (ui/pipeline.py)."""
from __future__ import annotations

import json
import math
import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
from ui import pipeline as pl  # noqa: E402
from ui import projekt as pj  # noqa: E402

BEISPIELE = REPO / "data" / "beispiele"


def lade(name: str) -> list[dict]:
    return [json.loads((BEISPIELE / name).read_text(encoding="utf-8"))]


def projekt(docs):
    return pj.neues_projekt(docs, "test")


def rechnen(docs, p):
    e = pj.einstellungen(p)
    v = pj.modell_eingabe(docs, p, e)
    return v, pl.modell_rechnen(v.docs, p.vorgabe, e.methode, e.puffer, e.raster, e.basis, pj.ursprung(p, v),
                                durchmesser=p.durchmesser, durchmesser_je=pj.durchmesser_je_code(docs, p))


def bid(docs, p, code):
    return next(z["id"] for z in pj.bohrungen_liste(docs, p) if z["code"] == code)


def zeile(docs, p, code):
    return next(z for z in pj.bohrungen_liste(docs, p) if z["code"] == code)


def test_ohne_koordinaten_reihe_mit_standardabstand():
    docs = lade("talheim.json")
    p = projekt(docs)
    assert p.lage_modus == pj.LAGE_REIHE and p.name == "talheim"
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
    pj.aendern(docs, p, {"op": "reihe", "abstand": {bid(docs, p, "BK2"): 10.0, bid(docs, p, "BK3"): 15.0}})
    pj.aendern(docs, p, {"op": "station", "id": bid(docs, p, "BK4"), "station": 70.0})
    st = {z["code"]: z["station"] for z in pj.reihe_liste(docs, p)}
    assert st["BK1"] == 0 and st["BK2"] == 10 and st["BK3"] == 25 and st["BK4"] == 70 and st["BK5"] == 90
    v, e = rechnen(docs, p)
    quellen = {e_["code"]: e_["lage"] for e_ in e.bericht["bohrungen"]}
    assert quellen["BK2"] == "Reihe (Abstand manuell)" and quellen["BK4"] == "Reihe (Station im Schnitt gesetzt)"
    x = {b["code"]: b["x"] for b in e.bericht["bohrungen"]}
    assert x["BK3"] == 25 and x["BK4"] == 70
    # Ereignisse mit laufender Nummer (Viewer): jedes nur einmal
    assert pj.ereignis_anwenden(p, {"nr": 1, "typ": "station", "id": bid(docs, p, "BK5"), "station": 95.0})
    assert not pj.ereignis_anwenden(p, {"nr": 1, "typ": "station", "id": bid(docs, p, "BK5"), "station": 99.0})


def test_gok_nur_ohne_gok_aus_dem_pdf_verschiebbar():
    """Im Schnitt darf die Hoehe nur gezogen werden, wenn das PDF keine GOK hat; sonst nur in der Tabelle."""
    docs = lade("talheim.json")
    p = projekt(docs)
    gwm1 = bid(docs, p, "GWM1")
    assert not zeile(docs, p, "GWM1")["gok_pdf"] and zeile(docs, p, "BK1")["gok_pdf"]
    pj.aendern(docs, p, {"op": "gok", "id": gwm1, "gok": 769.45})
    assert zeile(docs, p, "GWM1")["gok"] == 769.45 and zeile(docs, p, "GWM1")["gok_quelle"] == "manuell"
    b = next(b for i, _, b in pj.bohrungen(pj.wirksame_docs(docs, p)) if i == gwm1)
    assert b["gok_nhn"] == 769.45 and b["gok_source"] == "manuell"
    mit = bid(docs, p, "BK1")
    with pytest.raises(ValueError, match="GOK steht im PDF"):
        pj.aendern(docs, p, {"op": "gok", "id": mit, "gok": 50.0})
    assert not pj.ereignis_anwenden(p, {"nr": 1, "typ": "gok", "id": mit, "gok": 50.0}, docs)
    pj.aendern(docs, p, {"op": "bohrung", "id": mit, "feld": "gok", "wert": 770.5})   # Tabelle: erlaubt
    assert zeile(docs, p, "BK1")["gok"] == 770.5


def test_reihenfolge_aendern():
    docs = lade("talheim.json")
    p = projekt(docs)
    ids = [z["id"] for z in pj.reihe_liste(docs, p)]
    bk8 = bid(docs, p, "BK8")
    pj.aendern(docs, p, {"op": "reihe", "reihenfolge": [bk8] + [i for i in ids if i != bk8]})
    assert pj.reihe_liste(docs, p)[0]["code"] == "BK8"


def test_korrektur_und_rueckgaengig():
    docs = lade("berlin_v67b.json")
    p = projekt(docs)
    s2a = bid(docs, p, "S2a")
    for feld, w in (("x", 394800.0), ("y", 5818400.0), ("epsg", 25833), ("gok", 36.6)):
        pj.aendern(docs, p, {"op": "bohrung", "id": s2a, "feld": feld, "wert": w})
    v, e = rechnen(docs, p)
    x = next(x for x in e.bericht["bohrungen"] if x["code"] == "S2a")
    assert x["lage"] == "manuell (Tabelle)" and x["hoehe"].startswith("manuell")
    for feld, w in (("x", None), ("y", None), ("epsg", None), ("gok", 36.52)):
        pj.aendern(docs, p, {"op": "bohrung", "id": s2a, "feld": feld, "wert": w})
    assert p.bohrung == {}                               # zurueck auf PDF-Werte: keine Korrektur mehr


def test_neue_kalibrierung_plan_und_schnitt():
    """Massstab aus gemessener Strecke oder 1:n, Bezugspunkt mit Koordinate, Drehung; gleiche Formel wie im Viewer."""
    kal = pj.kalibrierung_pruefen({"massstab": {"u1": 0, "v1": 0, "u2": 200, "v2": 0, "meter": 50},
                                   "bezug": {"u": 100, "v": 100, "x": 394700.0, "y": 5818300.0},
                                   "drehung": 90, "epsg": 25833, "gesperrt": True}, "plan")
    assert kal["gesperrt"] and kal["epsg"] == 25833
    assert pj.bild_zu_welt(kal, "plan", 0.1, 100, 100) == (394700.0, 5818300.0)
    # 0.25 m je Pixel; Plan um 90 Grad gegen Gitternord gedreht: Bild-rechts zeigt nach Sueden
    x, y = pj.bild_zu_welt(kal, "plan", 0.1, 140, 100)
    assert x == pytest.approx(394700.0) and y == pytest.approx(5818300.0 - 10.0)
    kal = pj.kalibrierung_pruefen({"massstab": {"n": 500}, "bezug": {"u": 0, "v": 0, "x": 0, "y": 0}}, "plan")
    assert pj.bild_zu_welt(kal, "plan", 0.2, 10, -10) == pytest.approx((1.0, 1.0))      # 0.2 mm/px * 500 = 0.1 m/px
    schnitt = pj.kalibrierung_pruefen({"massstab": {"n": 500}, "hoehe": {"n": 100},
                                       "bezug": {"u": 50, "v": 40, "x": 0.0, "y": 42.0}}, "schnitt")
    assert pj.bild_zu_welt(schnitt, "schnitt", 0.2, 150, 90) == pytest.approx((10.0, 41.0))
    for falsch in ({"massstab": {"n": 500}}, {"bezug": {"u": 0, "v": 0, "x": 0, "y": 0}},
                   {"massstab": {"u1": 0, "v1": 0, "u2": 3, "v2": 0, "meter": 5}, "bezug": {"u": 0, "v": 0, "x": 0, "y": 0}}):
        with pytest.raises(ValueError):
            pj.kalibrierung_pruefen(falsch, "plan")
    # alte Kalibrierung (zwei Passpunkte) wird beim Laden umgerechnet: dieselbe Abbildung
    alt = [[100, 50, 394700.0, 5818300.0], [300, 120, 394780.0, 5818230.0]]
    neu = pj.kalibrierung_aus_punkten(alt, "plan", 25833)
    for u, v, xw, yw in alt:
        assert pj.bild_zu_welt(neu, "plan", 0.1, u, v) == pytest.approx((xw, yw))


def test_verschieben_im_viewer_auf_kalibriertem_plan():
    docs = lade("berlin_v67b.json")
    p = projekt(docs)
    p.unterlage = {"art": "plan", "kalibrierung": None}
    pj.aendern(docs, p, {"op": "kalibrierung", "wert": {"massstab": {"n": 1000}, "drehung": 0, "epsg": 25833,
                                                         "bezug": {"u": 0, "v": 0, "x": 394700, "y": 5818300}}})
    s2a = bid(docs, p, "S2a")
    pj.aendern(docs, p, {"op": "lage", "id": s2a, "x": 394810.0, "y": 5818420.0})
    v, e = rechnen(docs, p)
    x = next(b for b in e.bericht["bohrungen"] if b["code"] == "S2a")
    assert x["lage"] == "Plan (kalibriert)" and x["x"] == 394810.0 and e.bericht["epsg"] == 25833
    assert p.version == 2


def test_warnung_bei_unklassifizierten_schichten_und_vorschlag():
    """Warnung = Schicht nicht klassifiziert (nicht Konfidenz); Pruefen nimmt sie zur Kenntnis; Vorschlag nach Norm."""
    docs = lade("talheim.json")
    p = projekt(docs)
    bk1 = bid(docs, p, "BK1")
    z = zeile(docs, p, "BK1")
    assert z["unklassifiziert"] == 1 and z["offen"] == 1
    sch = pj.schichten_liste(docs, p, bk1)
    leer = next(s for s in sch if s["unklassifiziert"])
    assert leer["offen"] and leer["vorschlag"] is None                 # ohne Beschreibung kein Vorschlag
    st = pj.pruefstand(docs, p)
    assert st["unklassifiziert"] >= 1 and st["unklassifiziert_offen"] == st["unklassifiziert"]
    pj.aendern(docs, p, {"op": "schicht", "id": bk1, "k": leer["k"], "feld": "geprueft", "wert": True})
    assert zeile(docs, p, "BK1")["offen"] == 0 and zeile(docs, p, "BK1")["unklassifiziert"] == 1
    # Vorschlag nach Norm fuer eine unklassifizierte Schicht mit Beschreibung
    docs[0]["boreholes"][0]["layers"][leer["k"]]["description_raw"] = "U, t, s'"
    sch = pj.schichten_liste(docs, p, bk1)
    assert sch[leer["k"]]["vorschlag"]["klasse"] == "Schluff"
    meldung = pj.aendern(docs, p, {"op": "vorschlag", "id": bk1, "k": leer["k"]})
    assert "Schluff" in meldung and zeile(docs, p, "BK1")["unklassifiziert"] == 0
    s = pj.schichten_liste(docs, p, bk1)[leer["k"]]
    assert s["bodenart"] == "Schluff" and s["korrigiert"] and s["norm"]["din4023"] == "U, t, s'"
    with pytest.raises(ValueError):
        pj.aendern(docs, p, {"op": "vorschlag", "id": bk1, "k": leer["k"]})   # schon klassifiziert


def test_schichten_korrigieren_und_pruefen(tmp_path):
    import ifcopenshell
    docs = lade("demo_synthetisch.json")
    p = projekt(docs)
    b0 = pj.bohrungen_liste(docs, p)[0]["id"]
    pj.aendern(docs, p, {"op": "schicht", "id": b0, "k": 0, "feld": "bodenart", "wert": "Schluff"})
    pj.aendern(docs, p, {"op": "schicht", "id": b0, "k": 1, "feld": "geprueft", "wert": True})
    st = pj.pruefstand(docs, p)
    assert st["korrigiert"] == 1 and st["schichten"][0] == 2       # korrigiert zaehlt als geprueft
    eff = pj.wirksame_docs(docs, p)[0]["boreholes"][0]["layers"]
    assert eff[0]["soil_class"] == "Schluff" and eff[0]["korrigiert"] and eff[0]["confidence"] == 1.0
    pj.aendern(docs, p, {"op": "bohrung_pruefen", "id": b0, "wert": True})
    assert all(s["geprueft"] for s in pj.schichten_liste(docs, p, b0))
    v, e = rechnen(docs, p)
    pfad = tmp_path / "m.ifc"
    pfad.write_bytes(e.ifc)
    f = ifcopenshell.open(str(pfad))
    korr = [pv.NominalValue.wrappedValue for pv in f.by_type("IfcPropertySingleValue") if pv.Name == "Korrigiert"]
    assert korr == [True]


def test_alle_bohrungen_geprueft_und_zuruecknehmen():
    docs = lade("demo_synthetisch.json")
    p = projekt(docs)
    assert "12 Bohrungen" in pj.aendern(docs, p, {"op": "alle_pruefen", "wert": True})
    st = pj.pruefstand(docs, p)
    assert st["bohrungen"] == [12, 12] and st["schichten"][0] == st["schichten"][1]
    pj.aendern(docs, p, {"op": "alle_pruefen", "wert": False})
    st = pj.pruefstand(docs, p)
    assert st["bohrungen"] == [0, 12] and st["schichten"][0] == 0


def test_bohrung_entfernen_und_wiederherstellen():
    docs = lade("demo_synthetisch.json")
    p = projekt(docs)
    b1 = bid(docs, p, "B 1")
    pj.aendern(docs, p, {"op": "entfernen", "id": b1})
    assert zeile(docs, p, "B 1")["entfernt"] and pj.pruefstand(docs, p)["entfernt"] == 1
    v, e = rechnen(docs, p)
    assert "B 1" not in [b["code"] for b in e.bericht["bohrungen"]]
    assert {"code": "B 1", "grund": "entfernt"}.items() <= next(r for r in v.nicht_im_modell if r["code"] == "B 1").items()
    assert "B 1" not in [n["code"] for n in pj.viewer_bohrungen(docs, p, v, e.bericht)]
    pj.aendern(docs, p, {"op": "wiederherstellen", "id": b1})
    assert not zeile(docs, p, "B 1")["entfernt"] and p.bohrung == {}


def test_durchmesser_projekt_und_je_bohrung(tmp_path):
    import ifcopenshell
    import ifcopenshell.util.element
    docs = lade("demo_synthetisch.json")
    p = projekt(docs)
    v = pj.modell_eingabe(docs, p)
    auto = pj.durchmesser_auto(v)
    assert all(n["durchmesser"] == auto for n in pj.viewer_bohrungen(docs, p, v, None))
    pj.aendern(docs, p, {"op": "durchmesser", "wert": 0.4})
    pj.aendern(docs, p, {"op": "bohrung", "id": bid(docs, p, "B 2"), "feld": "durchmesser", "wert": 1.5})
    nadeln = {n["code"]: n for n in pj.viewer_bohrungen(docs, p, v, None)}
    assert nadeln["B 1"]["durchmesser"] == 0.4 and nadeln["B 2"]["durchmesser"] == 1.5
    v, e = rechnen(docs, p)
    (tmp_path / "d.ifc").write_bytes(e.ifc)
    f = ifcopenshell.open(str(tmp_path / "d.ifc"))
    dm = {b.Name: ifcopenshell.util.element.get_psets(b)["CPset_Darstellung"]["Durchmesser_m"] for b in f.by_type("IfcBorehole")}
    assert dm["B 1"] == 0.4 and dm["B 2"] == 1.5


def test_einchecken():
    docs = lade("demo_synthetisch.json")
    p = projekt(docs)
    eintrag = pj.einchecken(docs, p, "modellschluessel1", "erste Sichtung")
    assert eintrag["nr"] == 1 and eintrag["stand"]["bohrungen"] == [0, 12]
    assert "v1" in pj.stand_text(eintrag) and not pj.seit_einchecken_geaendert(docs, p, "modellschluessel1")
    assert pj.seit_einchecken_geaendert(docs, p, "anderesmodell")     # Modell neu gerechnet (andere Eingaben)
    pj.aendern(docs, p, {"op": "geprueft", "id": bid(docs, p, "B 1"), "wert": True})
    assert pj.seit_einchecken_geaendert(docs, p, "modellschluessel1")


def test_relative_hoehen_wenn_alle_ohne_gok():
    docs = lade("demo_synthetisch.json")
    for b in docs[0]["boreholes"]:
        b["gok_nhn"] = None
    p = projekt(docs)
    v, e = rechnen(docs, p)
    assert all(b["gok_source"] == "relativ" for b in v.docs[0]["boreholes"])
    assert any("relative Hoehen" in h for h in e.bericht["hinweise"])


def test_doppelte():
    docs = lade("berlin_v67b.json") * 2
    p = projekt(docs)
    zeilen = pj.bohrungen_liste(docs, p)
    zweite = [z for z in zeilen if z["id"].startswith("1:")]
    assert all(z["entfernt"] and z["doppelt_in"] for z in zweite)
    pj.aendern(docs, p, {"op": "entfernen", "id": zeilen[0]["id"]})
    v = pj.modell_eingabe(docs, p)
    gruende = [r["grund"] for r in v.nicht_im_modell]
    assert "entfernt" in gruende and any(g.startswith("doppelt") for g in gruende)


def test_viewer_bohrungen_und_fester_ursprung():
    docs = lade("berlin_v67b.json")
    p = projekt(docs)
    v, e = rechnen(docs, p)
    stecknadeln = pj.viewer_bohrungen(docs, p, v, e.bericht)
    s2a = next(s for s in stecknadeln if s["code"] == "S2a")
    assert s2a["x"] is None and not s2a["im_modell"]       # ohne Lage: im Viewer zum Platzieren
    oben, unten, farbe, art, konf, gep = s2a["schichten"][0]   # je Schicht: Tiefen, Farbe, Bodenart, Konfidenz, geprueft
    assert unten > oben and farbe.startswith("#") and isinstance(art, str) and 0 <= konf <= 1 and gep is False
    assert s2a["gok_pdf"] and s2a["offen"] == s2a["unklassifiziert"] >= 1
    alt = p.ursprung
    pj.aendern(docs, p, {"op": "lage", "id": next(s["id"] for s in stecknadeln if s["code"] == "422C-460"),
                         "x": 394780.0, "y": 5818330.0})
    rechnen(docs, p)
    assert p.ursprung == alt                               # Ansicht springt nicht


def test_farben_nach_din_4023():
    assert pj.bodenart_farbe("Kies") == "#f2cf2c" and pj.bodenart_farbe("Sand") == "#ef8f2f"
    assert pj.bodenart_farbe("unklassifiziert") == pj.bodenart_farbe("Quatsch") == "#e6e6e6"
    assert pj.bodenart_farbe("Fels (Tonstein)") != pj.bodenart_farbe("Fels")
    arten = pj.bodenarten(lade("talheim.json"))
    assert arten.index("Kies") < arten.index("Fels (Tonstein)")


def test_projekt_speichern_und_laden():
    docs = lade("talheim.json")
    p = projekt(docs)
    ids = [z["id"] for z in pj.bohrungen_liste(docs, p)]
    pj.aendern(docs, p, {"op": "station", "id": ids[1], "station": 12.5})
    pj.aendern(docs, p, {"op": "bohrung_pruefen", "id": ids[0], "wert": True})
    pj.aendern(docs, p, {"op": "einstellungen", "methode": "tps", "puffer": 30.0})
    pj.einchecken(docs, p, "abc", "erster Stand")
    p.ursprung = (100.0, 0.0)
    q = pj.laden(json.loads(json.dumps(pj.speichern(p))))
    assert q == p and q.ursprung == (100.0, 0.0) and pj.einstellungen(q).methode == "tps"
    assert pj.pruefstand(docs, q) == pj.pruefstand(docs, p)
    # Projekt aus App v2 mit alter Kalibrierung (zwei Passpunkte) wird umgerechnet
    alt = pj.speichern(p)
    alt["unterlage"] = {"art": "plan", "kalibrierung": {"punkte": [[0, 0, 10, 10], [100, 0, 60, 10]], "epsg": None}}
    q = pj.laden(alt)
    assert q.unterlage["kalibrierung"]["massstab"]["meter"] == 50 and q.unterlage["kalibrierung"]["drehung"] == 0


def test_vor_dem_erzeugen_zeigt_der_viewer_was_ins_modell_kaeme():
    docs = lade("berlin_v67b.json")
    p = projekt(docs)
    v = pj.modell_eingabe(docs, p)
    nadeln = {n["code"]: n for n in pj.viewer_bohrungen(docs, p, v, None)}
    assert nadeln["S2a"]["im_modell"] is False and nadeln["S2a"]["grund"] == "ohne Lage"
    assert sum(n["im_modell"] for n in nadeln.values()) == len(v.lage)


def test_ungueltige_aenderungen():
    docs = lade("demo_synthetisch.json")
    p = projekt(docs)
    for op in ({"op": "gibtsnicht"}, {"op": "entfernen", "id": "9:9"}, {"op": "lage_modus", "wert": "kreis"},
               {"op": "einstellungen", "methode": "kriging"}, {"op": "kalibrierung", "wert": {"massstab": {"n": 500}}}):
        with pytest.raises(ValueError):
            pj.aendern(docs, p, op)
    assert p.version == 0


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
    assert pl.ist_extrahiert(daten, False) and pl.pdf_pfad(doc["document"]).read_bytes() == daten
    t = time.time()
    assert pl.pdf_extrahieren("anders.pdf", daten, ocr=False)["boreholes"] == doc["boreholes"]
    assert time.time() - t < 2.0
    p = projekt([doc])
    v, e = rechnen([doc], p)
    assert e.bericht["pruefungen"]["alle_koerper_geschlossen"]
    assert not math.isnan(e.bericht["parameter"]["durchmesser_auto_m"])
