"""Normen-Datenbank und Deutung von Schichtbeschreibungen (DIN 4023, DIN EN ISO 14688-1, DIN 18196)."""
import pytest

from baugrundmodell.normen import KLASSEN, NORMEN, deuten, farbinfo, ifc_eigenschaften, klassen_liste, vorschlag


def test_datenbank_vollstaendig():
    # jede Klasse hat eine Farbe und einen Beleg; Normfarben nach DIN 4023
    for k, e in KLASSEN.items():
        assert e["farbe"].startswith("#") and len(e["farbe"]) == 7, k
        assert e.get("beleg"), k
    assert (KLASSEN["Kies"]["farbname"], KLASSEN["Sand"]["farbname"], KLASSEN["Schluff"]["farbname"],
            KLASSEN["Ton"]["farbname"], KLASSEN["Mudde"]["farbname"]) == ("gelb", "orange", "oliv", "violett", "lila")
    assert KLASSEN["Kies"]["din4023"] == "G" and KLASSEN["Kies"]["iso14688"] == "Gr"
    assert "SU*" in NORMEN["bodengruppen_din18196"] and "[]" in NORMEN["bodengruppen_din18196"]
    namen = [x["klasse"] for x in klassen_liste()]
    assert namen.index("Kies") < namen.index("Fels") < namen.index("Fels (Tonstein)") < namen.index("Beton")


@pytest.mark.parametrize("text, klasse, benennung, din", [
    ("mS, fs', u", "Sand", "Mittelsand, schluffig, schwach feinsandig", "mS, u, fs'"),
    ("U, t, s'", "Schluff", "Schluff, tonig, schwach sandig", "U, t, s'"),
    ("G, s*, u'", "Kies", "Kies, stark sandig, schwach schluffig", "G, s̅, u'"),
    ("S, u̅, g'", "Sand", "Sand, stark schluffig, schwach kiesig", "S, u̅, g'"),
    ("f-mS, g", "Sand", "Fein- bis Mittelsand, kiesig", "f-mS, g"),
    ("Feinsand bis Mittelsand, schwach schluffig", "Sand", "Fein- bis Mittelsand, schwach schluffig", "f-mS, u'"),
    ("FeinsandbisMittelsand,Feinkies (vereinzeltvorhanden)/gelbgrau", "Sand",
     "Fein- bis Mittelsand, feinkiesig (Anteil ohne Angabe)", "f-mS, fg(?)"),
    ("Mittelsand bisGrobsand (feinkiesigbismittelkiesig)/grau", "Sand",
     "Mittel- bis Grobsand, feinkiesig bis mittelkiesig", "m-gS, fg"),
    ("Ton, schluffig, steif bis halbfest, dunkelgrau, kalkhaltig", "Ton", "Ton, schluffig", "T, u"),
    ("Tonstein, schluffig, fest, rostbn-gr, mit Toneisensteingeoden,", "Fels (Tonstein)", "Tonstein, schluffig", "Tst, u"),
    ("Mu", "Mutterboden", "Mutterboden", "Mu"),
    ("A (mS, u')", "Auffuellung", "Auffüllung (Mittelsand, schwach schluffig)", "A (mS, u')"),
])
def test_deutung(text, klasse, benennung, din):
    d = deuten(text)
    assert (d.klasse, d.benennung, d.din4023) == (klasse, benennung, din)
    assert d.sicher


def test_ausgeschrieben_mit_allen_angaben():
    d = deuten("Anschüttung, Schluff, stark tonig, kiesig, stark sandig, schwach steinig, weich-steif, TA", "Auffuellung")
    assert d.klasse == "Auffuellung" and d.material["klasse"] == "Schluff"
    assert [(a.klasse, a.stufe) for a in d.nebenanteile] == [("Ton", "stark"), ("Sand", "stark"), ("Kies", ""),
                                                             ("Steine", "schwach")]
    assert (d.konsistenz, d.bodengruppe, d.bodengruppe_name) == ("weich bis steif", "TA", "ausgeprägt plastische Tone")
    assert d.din4023 == "A (U, t̅, s̅, g, x')"
    assert not d.hinweise                                    # stimmt mit der Extraktion ueberein
    d = deuten("Sand, mitteldicht gelagert, feucht, k+")
    assert (d.lagerung, d.feuchte, d.kalk) == ("mitteldicht", "feucht", "kalkhaltig")


def test_unsicheres_wird_markiert():
    d = deuten("Mg")                                         # Geschiebemergel (DIN 4023) oder made ground (ISO)
    assert d.klasse is None and any("mehrdeutig" in h for h in d.hinweise)
    assert deuten("Mg, Ziegelreste").klasse == "Auffuellung"
    assert deuten("Mg, Geschiebe").klasse == "Geschiebemergel"
    d = deuten("Lehm, sandig, braun")
    assert d.klasse == "Lehm" and not d.sicher and d.hinweise
    d = deuten("Sand/Auffullung/grau/trocken", "Sand")      # Auffuellung genannt: Widerspruch zur Extraktion
    assert d.klasse == "Auffuellung" and d.material["klasse"] == "Sand"
    assert any("Extraktion: Sand" in h for h in d.hinweise)
    d = deuten("Kies, sandig, TL")                           # Bodengruppe passt nicht
    assert d.bodengruppe == "TL" and any("passt nicht" in h for h in d.hinweise)
    d = deuten("Kies, sandig, schwach schluffig, [GW]")      # eckige Klammer: Auffuellung aus natuerlichem Boden
    assert d.klasse == "Auffuellung" and d.material["klasse"] == "Kies"
    d = deuten("Schluff, eisenschüssig, mit Ziegel- und Betonresten")
    assert d.klasse == "Schluff" and d.anthropogen and any("Auffüllung prüfen" in h for h in d.hinweise)
    assert deuten("Tonstein, mit Toneisensteingeoden").anthropogen == []
    d = deuten("Grobaand, mittelsandig, feinsandig")        # OCR-Fehler: erkannt, aber unsicher
    assert d.klasse == "Sand" and d.fraktion == "g" and not d.sicher and any("Grobsand" in h for h in d.hinweise)
    d = deuten("Kernverlust")
    assert d.klasse is None and d.sonstiges == ["Kernverlust"]
    assert deuten("").hinweise == ["keine Beschreibung"]


def test_geologische_benennung_mit_material():
    d = deuten("Geschiebemergel, Schluff, sandig, kiesig, steif, grau", "Geschiebemergel")
    assert d.klasse == "Geschiebemergel" and d.material["klasse"] == "Schluff"
    assert (d.benennung, d.din4023) == ("Geschiebemergel (Schluff, sandig, kiesig)", "Mg (U, s, g)")
    assert d.konsistenz == "steif" and not d.hinweise


def test_dezimalzahl_und_beton():
    d = deuten("~770,17 mNN Beton", "Beton")
    assert d.klasse == "Beton" and not d.hinweise


def test_farben():
    assert farbinfo("Kies")["name"] == "gelb"
    assert farbinfo("Fels (Tonstein)")["hex"] == NORMEN["fels"]["Tonstein"]["farbe"]
    assert farbinfo("Fels (Gabbro)")["hex"] == KLASSEN["Fels"]["farbe"]       # unbekannte Felsart: Fels
    assert farbinfo("Schluff", "g")["name"] == "türkis"                      # Grobschluff (DIN 4023:2023)
    assert farbinfo(None)["hex"] == KLASSEN["unklassifiziert"]["farbe"]
    assert farbinfo("Sand")["beleg"] == "DIN4023" and farbinfo("Auffuellung")["beleg"] == "darstellung"


def test_vorschlag_nur_fuer_unklassifizierte():
    assert vorschlag({"soil_class": "Sand", "description_raw": "Kies"}) is None
    v = vorschlag({"soil_class": None, "description_raw": "U, t, s'"})
    assert v["klasse"] == "Schluff" and v["sicher"]
    assert vorschlag({"soil_class": None, "description_raw": "Kernverlust"}) is None


def test_ifc_eigenschaften():
    e = ifc_eigenschaften(deuten("Ton, schluffig, steif, TM"))
    assert e["Beschreibung"] == "Ton, schluffig, steif, TM" and e["Kurzzeichen_DIN4023"] == "T, u"
    assert e["Bodengruppe_DIN18196"] == "TM" and e["Konsistenz"] == "steif" and e["Farbname_DIN4023"] == "violett"
    assert "DIN 4023" in e["Normen"]
