"""Synthetische Faelle mit bekannter Wahrheit: Einheiten, Kontakte, Koerper, IFC."""
from __future__ import annotations

import math

import numpy as np
import pytest

from baugrundmodell import synthetisch as syn
from baugrundmodell.einheiten import (Abschnitt, Bohrung, ausrichten, bohrungen_aus_extraktion,
                                      einheiten_aus_vorgabe, korrelieren)
from baugrundmodell.flaechen import ZENSUR_MARGE, interpolieren
from baugrundmodell.ifc4x3 import prisma
from baugrundmodell.koerper import pruefen
from baugrundmodell.modell import bauen, bericht, ifc_schreiben


def modell(fall, **kw):
    docs = [syn.dokument(fall)]
    return bauen(docs, **kw), docs


def namen(m):
    return [e.name for e in m.einheiten]


def status(m, einheit):
    j = namen(m).index(einheit)
    return {b.code: ks[j].status for b, ks in zip(m.bohrungen, m.kontakte)}


def maechtigkeit_an(m, einheit, code):
    j, bi = namen(m).index(einheit), [b.code for b in m.bohrungen].index(code)
    return m.flaechen[j][bi] - m.flaechen[j + 1][bi]


@pytest.mark.parametrize("name", sorted(syn.FAELLE))
@pytest.mark.parametrize("methode", ["idw", "tps"])
def test_invarianten(name, methode):
    """Fuer jeden Fall: Kontakte exakt, Maechtigkeit >= 0, Koerper geschlossen, Volumen konsistent."""
    m, _ = modell(syn.FAELLE[name](), methode=methode)
    assert m.max_abweichung < 1e-6
    assert np.all(np.diff(m.flaechen, axis=0) <= 1e-9)
    assert np.all(m.flaechen >= m.basis - 1e-9)
    for k in m.koerper:
        assert k["pruefung"]["geschlossen"], k["name"]
        assert k["pruefung"]["volumen"] == pytest.approx(k["volumen_m3"], rel=1e-6, abs=1e-6)
        assert k["volumen_m3"] >= 0


def test_tps_trifft_geneigte_ebenen():
    """Ebene Wahrheit: der Duennplatten-Spline (mit linearem Trend) gibt sie im ganzen Gebiet wieder."""
    fall = syn.geneigt()
    m, _ = modell(fall, methode="tps")
    assert namen(m) == ["Auffuellung", "Sand", "Geschiebemergel", "Ton"]
    x = m.punkte[:, 0] + m.ursprung[0] - syn.URSPRUNG[0]
    y = m.punkte[:, 1] + m.ursprung[1] - syn.URSPRUNG[1]
    wahr = [np.array([fall.gok(a, b) for a, b in zip(x, y)])] + \
           [np.array([uk(a, b) for a, b in zip(x, y)]) for _, uk in fall.einheiten[:-1]]
    for j, w in enumerate(wahr):
        assert np.abs(m.flaechen[j] - w).max() < 1e-3, j


def test_auskeilen():
    m, _ = modell(syn.auskeilen())
    assert namen(m) == ["Auffuellung", "Sand", "Torf", "Geschiebemergel", "Ton"]
    st = status(m, "Torf")
    assert {c for c, s in st.items() if s == "vorhanden"} == {"B1", "B4", "B7"}
    assert all(s == "fehlt" for c, s in st.items() if c not in {"B1", "B4", "B7"})
    for c in ("B2", "B3", "B5", "B6", "B8", "B9"):
        assert abs(maechtigkeit_an(m, "Torf", c)) < 1e-9
    assert maechtigkeit_an(m, "Torf", "B1") == pytest.approx(2.0, abs=0.01)


def test_linse_teilt_den_sand():
    """Kies nur in B5: die anderen Bohrungen haben einen durchgehenden Sand, der in Sand 1 / Sand 2 geteilt wird."""
    m, _ = modell(syn.linse())
    assert namen(m) == ["Auffuellung", "Sand 1", "Kies", "Sand 2", "Geschiebemergel"]
    assert {c for c, s in status(m, "Kies").items() if s == "vorhanden"} == {"B5"}
    for b, ks in zip(m.bohrungen, m.kontakte):
        if b.code == "B5":
            continue
        sand = next(a for a in b.abschnitte if a.klasse == "Sand")
        j1 = namen(m).index("Sand 1")
        assert ks[j1].art == "frei"                     # Grenze irgendwo im ungeteilten Sand
        assert abs(maechtigkeit_an(m, "Kies", b.code)) < 1e-9
        gesamt = maechtigkeit_an(m, "Sand 1", b.code) + maechtigkeit_an(m, "Sand 2", b.code)
        assert gesamt == pytest.approx(sand.ok - sand.uk, abs=1e-6)
        assert maechtigkeit_an(m, "Sand 1", b.code) > 0 and maechtigkeit_an(m, "Sand 2", b.code) > 0
    # die Linse duennt zu den Nachbarn aus: Ausduennung auf Hoehe der Linsenmitte von B5 (31.25 m NHN)
    bi = [b.code for b in m.bohrungen].index("B1")
    assert m.flaechen[namen(m).index("Kies")][bi] == pytest.approx(31.25, abs=0.01)


def test_linse_bleibt_lokal():
    """Eine Linse aus einer Bohrung liegt nicht duenn unter dem ganzen Gebiet (IDW waere ueberall > 0):
    sie endet etwa auf halbem Weg zu den Nachbarn ohne Kies (Wahrheit: Radius 20 m, Abstand 50 m)."""
    m, _ = modell(syn.linse())
    j = namen(m).index("Kies")
    d = m.flaechen[j] - m.flaechen[j + 1]
    b5 = [b.code for b in m.bohrungen].index("B5")
    r = np.hypot(*(m.punkte - m.punkte[b5]).T)
    assert r[d > 0.005].max() < 30.0
    assert any("Ausdehnung begrenzt" in h for h in m.koerper[j]["hinweise"])
    kegel = math.pi * 20.0 ** 2 * 1.5 / 3
    assert m.koerper[j]["volumen_m3"] < 3 * kegel


def test_zensiert():
    """Ostreihe endet im Sand: tiefere Einheiten dort unbekannt, Sandunterkante unter Endteufe - Marge."""
    m, _ = modell(syn.zensiert())
    kurz = {"B3", "B6", "B9"}
    assert {c for c, s in status(m, "Geschiebemergel").items() if s == "unbekannt"} == kurz
    j = namen(m).index("Sand")
    for bi, b in enumerate(m.bohrungen):
        if b.code in kurz:
            assert m.kontakte[bi][j].art == "zensiert"
            assert m.flaechen[j + 1][bi] <= b.ende - ZENSUR_MARGE + 1e-6


def test_stoerungen_markiert_statt_versteckt():
    m, _ = modell(syn.stoerungen())
    aus = {a["code"]: a["grund"] for a in m.ausgeschlossen}
    assert aus == {"RKS 7": "keine Koordinaten", "RKS 8": "Ansatzhoehe (GOK) unbekannt"}
    b5 = next(b for b in m.bohrungen if b.code == "B5")
    assert any("zugeschlagen" in h for h in b5.hinweise)
    assert namen(m) == ["Auffuellung", "Sand", "Geschiebemergel", "Ton"]


def test_vorgabe_fasst_bodenarten_zusammen():
    """Gutachter-Vorgabe: Sand und Kies eine Einheit -> keine Linse, mehrere Abschnitte je Einheit (C)."""
    vorgabe = einheiten_aus_vorgabe([{"name": "Auffuellung"}, {"name": "Sande und Kiese", "bodenarten": ["Sand", "Kies"]},
                                     {"name": "Geschiebemergel"}])
    m, _ = modell(syn.linse(), vorgabe=vorgabe)
    assert namen(m) == ["Auffuellung", "Sande und Kiese", "Geschiebemergel"]
    assert not m.hinweise
    bi = [b.code for b in m.bohrungen].index("B5")
    assert maechtigkeit_an(m, "Sande und Kiese", "B5") == pytest.approx(
        m.bohrungen[bi].abschnitte[0].uk - m.bohrungen[bi].abschnitte[-1].ok, abs=1e-6)


def test_vorgabe_unbekannte_bodenart_wird_markiert():
    vorgabe = einheiten_aus_vorgabe([{"name": "Auffuellung"}, {"name": "Sand"}, {"name": "Ton"}])
    m, _ = modell(syn.geneigt(), vorgabe=vorgabe)
    assert "Geschiebemergel" in namen(m)
    assert any("Geschiebemergel" in h and "keine vorgegebene" in h for h in m.hinweise)


def test_reihenfolge_der_eingabe_egal():
    fall = syn.demo()
    doc = syn.dokument(fall)
    rueck = dict(doc, boreholes=doc["boreholes"][::-1])
    assert namen(bauen([doc])) == namen(bauen([rueck]))


def test_eine_und_zwei_bohrungen():
    fall = syn.geneigt()
    fall.bohrungen = fall.bohrungen[:1]
    m, _ = modell(fall, methode="tps")
    assert len(m.einheiten) == 4 and all(k["pruefung"]["geschlossen"] for k in m.koerper)
    assert np.ptp(m.flaechen[1]) < 1e-9                          # eine Bohrung: waagerechte Flaechen
    fall = syn.geneigt()
    fall.bohrungen = fall.bohrungen[:2]                          # Bohrlinie: Korridor, TPS faellt auf IDW zurueck
    m, _ = modell(fall, methode="tps")
    assert m.max_abweichung < 1e-6 and all(k["pruefung"]["geschlossen"] for k in m.koerper)


def test_ausrichtung_bevorzugt_hoehe():
    """Zwei Kieslagen in A, eine in B: B's Kies wird der hoehengleichen Lage zugeordnet, die andere fehlt."""
    a = Bohrung("A", 0, 0, 40, [Abschnitt("Sand", 40, 36, []), Abschnitt("Kies", 36, 34, []), Abschnitt("Sand", 34, 30, []),
                                Abschnitt("Kies", 30, 28, []), Abschnitt("Sand", 28, 20, [])], "x")
    b = Bohrung("B", 30, 0, 40, [Abschnitt("Sand", 40, 31, []), Abschnitt("Kies", 31, 28.5, []),
                                 Abschnitt("Sand", 28.5, 20, [])], "x")
    einheiten, zuordnung, _ = korrelieren([a, b])
    assert [e.name for e in einheiten] == ["Sand 1", "Kies 1", "Sand 2", "Kies 2", "Sand 3"]
    ops = {e.name: op for op, _, e in zuordnung["B"]}
    assert ops["Kies 1"] == "S" and ops["Sand 2"] == "E" and ops["Kies 2"] == "M"


def test_unter_endteufe_unbekannt_nicht_fehlend():
    a = Bohrung("A", 0, 0, 40, [Abschnitt("Sand", 40, 30, []), Abschnitt("Ton", 30, 20, [])], "x")
    kurz = Bohrung("K", 10, 0, 40, [Abschnitt("Sand", 40, 35, [])], "x")
    einheiten, zuordnung, _ = korrelieren([a, kurz])
    assert [op for op, _, _ in zuordnung["K"]] == ["M", "T"]
    _, ops = ausrichten(kurz, einheiten, [(40, 30), (30, 20)])
    assert ops[-1][0] == "T"


def test_interpolatoren_exakt():
    xy = np.array([[0.0, 0.0], [10.0, 0.0], [0.0, 10.0], [7.0, 8.0]])
    z = np.array([1.0, 2.0, 3.0, 5.0])
    for meth in ("idw", "tps"):
        assert np.allclose(interpolieren(xy, xy, z, meth), z)


def test_prisma_nach_aussen_orientiert():
    kn, fl = prisma(0.0, 0.0, 10.0, 8.0, r=1.0, n=12)
    p = pruefen(kn, fl)
    assert p["geschlossen"]
    assert p["volumen"] == pytest.approx(2.0 * 0.5 * 12 * math.sin(2 * math.pi / 12), rel=1e-9)


def test_ifc_valide(tmp_path):
    import ifcopenshell
    import ifcopenshell.validate
    m, docs = modell(syn.demo())
    pfad = tmp_path / "demo.ifc"
    ifc_schreiben(m, pfad, docs)
    f = ifcopenshell.open(str(pfad))
    log = ifcopenshell.validate.json_logger()
    ifcopenshell.validate.validate(f, log)
    assert log.statements == []
    gm = f.by_type("IfcGeomodel")
    assert len(gm) == 1 and len(f.by_type("IfcBorehole")) == len(m.bohrungen)
    einheiten = [s for s in f.by_type("IfcGeotechnicalStratum") if (s.Description or "").startswith("Modelleinheit")]
    assert [s.Name for s in einheiten] == namen(m)
    assert all(fs.Closed for fs in f.by_type("IfcPolygonalFaceSet"))
    b = bericht(m)
    assert b["pruefungen"]["alle_koerper_geschlossen"] and b["vorlage_einheiten"][0]["name"] == "Auffuellung"


def test_ausschluss_ohne_koordinaten():
    doc = syn.dokument(syn.geneigt())
    for b in doc["boreholes"]:
        b["x"] = None
    bohrungen, aus, epsg = bohrungen_aus_extraktion([doc])
    assert bohrungen == [] and epsg is None and len(aus) == 9
    with pytest.raises(ValueError):
        bauen([doc])
