"""HTTP-Schnittstelle der Baugrundmodell-App (FastAPI). Die Oberflaeche (apps/web, Schritt-App) liegt gebaut in
apps/web/dist und wird hier mit ausgeliefert: ein Prozess, ein Port, kein Node noetig (docs/21).

    python -m server            -> http://127.0.0.1:8500

Im Netz (docs/22): GEO_AGENT_PASSWORT schuetzt alles mit HTTP-Basic-Anmeldung, GEO_AGENT_MAX_MB begrenzt Uploads,
/gesund antwortet ohne Anmeldung (Health-Check der Plattform). Lizenz AGPL-3.0-or-later (LICENSE).
"""
from __future__ import annotations

import base64
import binascii
import os
import secrets
from pathlib import Path

from fastapi import FastAPI, File, Form, HTTPException, Request, UploadFile
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from ui import pipeline as pl

from .arbeitsplatz import BEISPIELE, Arbeitsplatz

DIST = Path(__file__).resolve().parents[1] / "apps" / "web" / "dist"
VERSION = "3.0"
LIZENZ = "AGPL-3.0-or-later"
QUELLCODE = "https://github.com/martinpazmino/GeoIM"          # AGPL § 13: Quelltext fuer Nutzer im Netz


def anmeldung_ok(kopf: str | None, passwort: str, benutzer: str = "") -> bool:
    """HTTP-Basic-Anmeldung pruefen (zeitkonstant); ohne festen Benutzer zaehlt nur das Passwort."""
    if not kopf or not kopf.lower().startswith("basic "):
        return False
    try:
        name, _, wort = base64.b64decode(kopf[6:].strip()).decode("utf-8").partition(":")
    except (binascii.Error, UnicodeDecodeError):
        return False
    name_ok = secrets.compare_digest(name.encode(), benutzer.encode()) if benutzer else True
    return secrets.compare_digest(wort.encode(), passwort.encode()) and name_ok


class Aenderungen(BaseModel):
    ops: list[dict]


class Kommentar(BaseModel):
    kommentar: str = ""


class Beispiel(BaseModel):
    name: str
    ocr: bool = False


class Seite(BaseModel):
    seite: int = 0
    art: str = "plan"


def app_erstellen(arbeit: Path | None = None, passwort: str | None = None, max_mb: float | None = None) -> FastAPI:
    """passwort / max_mb: sonst aus GEO_AGENT_PASSWORT (leer = ohne Anmeldung, nur fuer localhost gedacht) und
    GEO_AGENT_MAX_MB (Standard 200 MB je Anfrage)."""
    ap = Arbeitsplatz(arbeit)
    app = FastAPI(title="GeoIM – Baugrundmodell", version=VERSION)
    app.state.arbeitsplatz = ap
    passwort = os.environ.get("GEO_AGENT_PASSWORT", "") if passwort is None else passwort
    benutzer = os.environ.get("GEO_AGENT_BENUTZER", "")
    max_mb = float(os.environ.get("GEO_AGENT_MAX_MB") or 200) if max_mb is None else max_mb
    quellcode = os.environ.get("GEO_AGENT_QUELLCODE") or QUELLCODE

    @app.middleware("http")
    async def zugang(request: Request, call_next):
        """Im Netz: Anmeldung fuer alles ausser der Pruefung /gesund; zu grosse Anfragen gleich abweisen."""
        if request.url.path != "/gesund":
            if passwort and not anmeldung_ok(request.headers.get("authorization"), passwort, benutzer):
                return Response("Anmeldung erforderlich", status_code=401,
                                headers={"WWW-Authenticate": 'Basic realm="GeoIM", charset="UTF-8"'})
            laenge = request.headers.get("content-length", "")
            if laenge.isdigit() and int(laenge) > max_mb * 1024 * 1024:
                return JSONResponse({"detail": f"Anfrage zu groß (höchstens {max_mb:g} MB)"}, status_code=413)
        return await call_next(request)

    @app.exception_handler(KeyError)
    async def nicht_gefunden(_: Request, err: KeyError):
        return JSONResponse({"detail": f"nicht gefunden: {err.args[0] if err.args else ''}"}, status_code=404)

    @app.exception_handler(ValueError)
    async def ungueltig(_: Request, err: ValueError):
        return JSONResponse({"detail": str(err)}, status_code=400)

    # ------------------------------------------------------------ Start
    @app.get("/gesund")
    def gesund():
        """Lebenszeichen fuer die Plattform (ohne Anmeldung, ohne Daten)."""
        return {"ok": True, "version": VERSION}

    @app.get("/api/info")
    def info():
        return {"version": VERSION, "ocr": pl.ocr_verfuegbar(), "lizenz": LIZENZ, "quellcode": quellcode,
                "beispiele": [{"name": k, "titel": t} for k, (t, _) in BEISPIELE.items()]}

    @app.get("/api/projekte")
    def projekte():
        return ap.liste()

    @app.post("/api/gutachten")
    async def gutachten(dateien: list[UploadFile] = File(...), ocr: bool = Form(True)):
        inhalt = [(f.filename or "dokument.pdf", await f.read()) for f in dateien]
        if not inhalt or not all(d[:5] == b"%PDF-" or n.lower().endswith(".json") for n, d in inhalt):
            raise ValueError("bitte PDF-Dateien hochladen (oder eine Extraktion als JSON)")
        return ap.extrahieren(inhalt, ocr and pl.ocr_verfuegbar()).als_dict()

    @app.get("/api/auftrag/{aid}")
    def auftrag(aid: str):
        return ap.auftrag(aid).als_dict()

    @app.post("/api/beispiel")
    def beispiel(b: Beispiel):
        if b.name not in BEISPIELE:
            raise KeyError(b.name)
        return ap.beispiel(b.name, b.ocr and pl.ocr_verfuegbar())

    # ------------------------------------------------------------ Projekt
    @app.get("/api/projekt/{sig}")
    def zustand(sig: str):
        return ap.zustand(sig)

    @app.delete("/api/projekt/{sig}")
    def loeschen(sig: str):
        ap.loeschen(sig)
        return {"ok": True}

    @app.post("/api/projekt/{sig}/aendern")
    def aendern(sig: str, a: Aenderungen):
        meldungen = ap.aendern(sig, a.ops)
        return {"meldungen": meldungen, "zustand": ap.zustand(sig)}

    @app.post("/api/projekt/{sig}/zuruecksetzen")
    def zuruecksetzen(sig: str):
        ap.zuruecksetzen(sig)
        return ap.zustand(sig)

    @app.get("/api/projekt/{sig}/bohrung/{bid}")
    def bohrung(sig: str, bid: str):
        return ap.bohrung(sig, bid)

    @app.get("/api/projekt/{sig}/seite/{dokument}/{seite}")
    def seite(sig: str, dokument: int, seite: int):
        return ap.seite(sig, dokument, seite)

    @app.post("/api/projekt/{sig}/unterlage")
    async def unterlage(sig: str, datei: UploadFile = File(...), art: str = Form("plan"), seite: int = Form(0)):
        daten = await datei.read()
        if daten[:5] != b"%PDF-":
            raise ValueError("bitte ein PDF hochladen")
        ap.unterlage_setzen(sig, datei.filename or "unterlage.pdf", daten, art, seite)
        return ap.zustand(sig)

    @app.post("/api/projekt/{sig}/unterlage/seite")
    def unterlage_seite(sig: str, s: Seite):
        ap.unterlage_setzen(sig, "", None, s.art, s.seite)
        return ap.zustand(sig)

    @app.delete("/api/projekt/{sig}/unterlage")
    def unterlage_entfernen(sig: str):
        ap.unterlage_entfernen(sig)
        return ap.zustand(sig)

    @app.post("/api/projekt/{sig}/modell")
    def modell(sig: str):
        erg = ap.modell(sig)
        return {**erg, "zustand": ap.zustand(sig)}

    @app.post("/api/projekt/{sig}/einchecken")
    def einchecken(sig: str, k: Kommentar):
        eintrag = ap.einchecken(sig, k.kommentar)
        return {"eintrag": eintrag, "zustand": ap.zustand(sig)}

    @app.get("/api/projekt/{sig}/export/{art}")
    def export(sig: str, art: str):
        inhalt, name, typ = ap.export(sig, art)
        return Response(inhalt, media_type=typ, headers={"Content-Disposition": f'attachment; filename="{name}"'})

    # ------------------------------------------------------------ Dateien und Oberflaeche
    app.mount("/dateien", StaticFiles(directory=ap.web), name="dateien")
    if (DIST / "index.html").exists():
        app.mount("/", StaticFiles(directory=DIST, html=True), name="app")
    return app
