"""HTTP-Schnittstelle der Schritt-App (server/api.py) mit dem TestClient: Projekt oeffnen, pruefen, Lage, Modell,
einchecken, Export; Extraktion als Hintergrundauftrag; Unterlage mit neuer Kalibrierung."""
from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO))
fastapi = pytest.importorskip("fastapi")
from fastapi.testclient import TestClient  # noqa: E402

from server.api import app_erstellen  # noqa: E402
from ui import pipeline as pl  # noqa: E402


@pytest.fixture()
def client(tmp_path, monkeypatch):
    monkeypatch.setattr(pl, "ARBEIT", tmp_path)
    with TestClient(app_erstellen(tmp_path)) as c:
        yield c


def oeffnen(client, name):
    r = client.post("/api/beispiel", json={"name": name})
    assert r.status_code == 200, r.text
    return r.json()["projekt"]


def aendern(client, sig, *ops, status=200):
    r = client.post(f"/api/projekt/{sig}/aendern", json={"ops": list(ops)})
    assert r.status_code == status, r.text
    return r.json()


def test_info_und_beispiele(client):
    info = client.get("/api/info").json()
    assert {"berlin", "talheim", "demo", "trasse", "pdf"} <= {b["name"] for b in info["beispiele"]}
    assert client.get("/api/projekte").json() == []


def test_ganzer_ablauf_mit_beispiel(client):
    sig = oeffnen(client, "demo")
    z = client.get(f"/api/projekt/{sig}").json()
    assert z["name"] == "synthetisch_demo" and len(z["bohrungen"]) == 12 and z["schritt"] == "bohrungen"
    assert len(z["viewer"]["bohrungen"]) == 12 and z["klassen"][0]["klasse"] == "Kies"
    b1 = z["bohrungen"][0]["id"]
    # Schichten mit Deutung nach Norm
    d = client.get(f"/api/projekt/{sig}/bohrung/{b1}").json()
    assert d["schichten"][0]["norm"]["din4023"] == "A" and d["schichten"][0]["farbe"].startswith("#")
    # pruefen, entfernen, Durchmesser
    r = aendern(client, sig, {"op": "bohrung_pruefen", "id": b1, "wert": True},
                {"op": "entfernen", "id": z["bohrungen"][1]["id"]}, {"op": "durchmesser", "wert": 0.6},
                {"op": "schritt", "wert": "lage"})
    assert r["zustand"]["pruefstand"]["bohrungen"] == [1, 11] and r["zustand"]["durchmesser"] == 0.6
    assert r["zustand"]["schritt"] == "lage" and len(r["meldungen"]) == 2
    # ungueltige Aenderung: nichts uebernommen (alles oder nichts)
    fehler = aendern(client, sig, {"op": "durchmesser", "wert": 2.0}, {"op": "gibtsnicht"}, status=400)
    assert "unbekannte" in fehler["detail"]
    assert client.get(f"/api/projekt/{sig}").json()["durchmesser"] == 0.6
    # Modell
    m = client.post(f"/api/projekt/{sig}/modell").json()
    assert not m["fehler"] and m["bericht"]["pruefungen"]["alle_koerper_geschlossen"]
    assert len(m["bericht"]["bohrungen"]) == 11 and m["zustand"]["modell"]["aktuell"]
    ifc = client.get(m["ifc"])
    assert ifc.status_code == 200 and ifc.content.startswith(b"ISO-10303-21")
    # Einchecken und Export (IFC mit Pruefstand)
    e = client.post(f"/api/projekt/{sig}/einchecken", json={"kommentar": "Test"}).json()
    assert e["eintrag"]["nr"] == 1 and not e["zustand"]["seit_einchecken_geaendert"]
    x = client.get(f"/api/projekt/{sig}/export/ifc")
    assert x.status_code == 200 and b"'Pruefstand'" in x.content and b"IFCTEXT('v1 " not in x.content
    assert b"IFCLABEL('v1 " in x.content and 'filename="synthetisch_demo.ifc"' in x.headers["content-disposition"]
    for art in ("bericht", "einheiten", "extraktion", "eingabe", "projekt"):
        assert client.get(f"/api/projekt/{sig}/export/{art}").status_code == 200
    # Liste der Projekte; Zuruecksetzen
    liste = client.get("/api/projekte").json()
    assert liste[0]["signatur"] == sig and liste[0]["eincheckungen"] == 1
    z = client.post(f"/api/projekt/{sig}/zuruecksetzen").json()
    assert z["pruefstand"]["bohrungen"] == [0, 12] and not z["eincheckungen"]


def test_gespeicherter_stand_bleibt(client, tmp_path):
    sig = oeffnen(client, "berlin")
    aendern(client, sig, {"op": "alle_pruefen", "wert": True})
    neu = TestClient(app_erstellen(tmp_path))            # Neustart des Servers: Stand von der Platte
    z = neu.get(f"/api/projekt/{sig}").json()
    assert z["pruefstand"]["bohrungen"][0] == z["pruefstand"]["bohrungen"][1] > 0
    assert oeffnen(neu, "berlin") == sig                 # gleiches Beispiel = gleiches Projekt


def test_stand_aus_der_streamlit_app_wird_uebernommen(client, tmp_path):
    """Projekte der App v2 lagen als projekte/<signatur>.json (ohne Extraktion): beim selben PDF gilt der Stand weiter."""
    import json
    from server.arbeitsplatz import signatur
    from ui import projekt as pj
    docs = [json.loads((REPO / "data" / "beispiele" / "talheim.json").read_text(encoding="utf-8"))]
    sig = signatur(docs)
    p = pj.neues_projekt(docs, sig)
    pj.aendern(docs, p, {"op": "alle_pruefen", "wert": True})
    alt = pj.speichern(p)
    alt.pop("name")
    (tmp_path / "projekte").mkdir(exist_ok=True)
    (tmp_path / "projekte" / f"{sig}.json").write_text(json.dumps(alt), encoding="utf-8")
    assert oeffnen(client, "talheim") == sig
    z = client.get(f"/api/projekt/{sig}").json()
    assert z["pruefstand"]["bohrungen"][0] == z["pruefstand"]["bohrungen"][1] and z["name"] == "talheim"


def test_unterlage_mit_neuer_kalibrierung(client):
    import pymupdf
    sig = oeffnen(client, "berlin")
    pdf = pymupdf.open()
    pdf.new_page(width=420 * 72 / 25.4, height=297 * 72 / 25.4).insert_text((50, 50), "Lageplan 1:500")
    r = client.post(f"/api/projekt/{sig}/unterlage", files={"datei": ("plan.pdf", pdf.tobytes(), "application/pdf")},
                    data={"art": "plan", "seite": "0"})
    assert r.status_code == 200, r.text
    u = r.json()["unterlage"]
    assert u["art"] == "plan" and u["url"].endswith(".png") and client.get(u["url"]).status_code == 200
    kal = {"massstab": {"n": 500}, "bezug": {"u": 100, "v": 100, "x": 394700, "y": 5818300}, "drehung": 0,
           "epsg": 25833, "gesperrt": True}
    z = aendern(client, sig, {"op": "kalibrierung", "wert": kal})["zustand"]
    assert z["unterlage"]["kalibrierung"]["gesperrt"] and z["unterlage"]["kalibrierung"]["massstab"] == {"n": 500}
    s2a = next(b["id"] for b in z["bohrungen"] if b["code"] == "S2a")
    z = aendern(client, sig, {"op": "lage", "id": s2a, "x": 394810.0, "y": 5818420.0})["zustand"]
    assert next(b for b in z["bohrungen"] if b["code"] == "S2a")["lage_aus"] == "Plan (kalibriert)"
    z = client.post(f"/api/projekt/{sig}/unterlage/seite", json={"seite": 0, "art": "schnitt"}).json()
    assert z["unterlage"]["art"] == "schnitt" and z["unterlage"]["kalibrierung"] is None and z["lage_modus"] == "reihe"
    assert client.delete(f"/api/projekt/{sig}/unterlage").json()["unterlage"] is None
    assert client.post(f"/api/projekt/{sig}/unterlage", files={"datei": ("x.pdf", b"kein pdf", "application/pdf")}).status_code == 400


def test_pdf_extraktion_als_auftrag_und_quellseite(client):
    r = client.post("/api/beispiel", json={"name": "pdf"}).json()
    aid = r["auftrag"]
    for _ in range(600):
        a = client.get(f"/api/auftrag/{aid}").json()
        if a["fertig"]:
            break
        time.sleep(0.1)
    assert a["fertig"] and not a["fehler"] and a["projekt"], a
    sig = a["projekt"]
    z = client.get(f"/api/projekt/{sig}").json()
    assert len(z["bohrungen"]) == 3 and z["dokumente"][0]["pdf"]
    b = client.get(f"/api/projekt/{sig}/bohrung/{z['bohrungen'][0]['id']}").json()
    q = b["schichten"][0]["quelle"]
    s = client.get(f"/api/projekt/{sig}/seite/0/{q['seite'] - 1}").json()
    assert s["px_je_pt"] > 0 and client.get(s["url"]).status_code == 200
    assert client.get(f"/api/projekt/{sig}/seite/0/999").status_code == 404


def test_extraktion_als_json_hochladen(client):
    import json
    daten = (REPO / "data" / "beispiele" / "talheim.json").read_bytes()
    a = client.post("/api/gutachten", files={"dateien": ("talheim.json", daten, "application/json")}, data={"ocr": "false"}).json()
    for _ in range(100):
        a = client.get(f"/api/auftrag/{a['id']}").json()
        if a["fertig"]:
            break
        time.sleep(0.05)
    assert a["projekt"] and not a["fehler"]
    assert len(client.get(f"/api/projekt/{a['projekt']}").json()["bohrungen"]) == 10
    a = client.post("/api/gutachten", files={"dateien": ("x.json", json.dumps({"a": 1}).encode(), "application/json")}).json()
    for _ in range(100):
        a = client.get(f"/api/auftrag/{a['id']}").json()
        if a["fertig"]:
            break
        time.sleep(0.05)
    assert a["projekt"] is None and "keine Extraktion" in a["fehler"][0]


def test_unbekanntes(client):
    assert client.get("/api/projekt/abc123/").status_code in (404, 405)
    assert client.get("/api/projekt/000000000000").status_code == 404
    assert client.post("/api/beispiel", json={"name": "gibtsnicht"}).status_code == 404
    assert client.post("/api/gutachten", files={"dateien": ("a.pdf", b"nein", "application/pdf")}).status_code == 400
