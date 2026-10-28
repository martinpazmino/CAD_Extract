"""Arbeitsplatz der Baugrundmodell-App: Projekte auf der Platte, Extraktion als Hintergrundauftrag, Modell-Cache,
Unterlagen und Seitenbilder. Ohne Web-Rahmen testbar; server/api.py macht daraus die HTTP-Schnittstelle.

Ablage unter ARBEIT (ui/pipeline.py, mit GEO_AGENT_ARBEIT festlegbar):
  projekte/<signatur>/docs.json      Extraktion (kanonisches JSON je Dokument, unveraendert)
  projekte/<signatur>/projekt.json   Projektstand (Korrekturen, Lage, Pruefung) - ui/projekt.py
  web/modelle/<schluessel>.ifc       Modell fuer den Viewer (Name = Schluessel der Eingaben)
  web/unterlagen/<sha>_<seite>.png   Lageplan/Laengsschnitt als Bild
  web/seiten/<sha>_<seite>.png       Seiten des Gutachtens (Quelle einer Schicht zeigen)
"""
from __future__ import annotations

import hashlib
import json
import shutil
import threading
import traceback
import uuid
from collections import Counter, OrderedDict
from dataclasses import dataclass, field
from pathlib import Path

from ui import pipeline as pl
from ui import projekt as pj

BEISPIELE = {
    "berlin": ("Berlin V-67b-VE – echte Daten, georeferenziert (7 Bohrungen)", "berlin_v67b.json"),
    "talheim": ("Talheim – echte Daten ohne Koordinaten (Reihe)", "talheim.json"),
    "demo": ("Demo – synthetisch, 12 Bohrungen mit Linse", "demo_synthetisch.json"),
    "trasse": ("Trasse – synthetisch, 6 km, 51 Bohrungen", "trasse_synthetisch.json"),
    "pdf": ("Synthetisches Bohrprofil-PDF (ganzer Ablauf mit Extraktion)", "synthetisch_bohrprofil.pdf"),
}
MODELLE_IM_SPEICHER = 6


def extraktion_aus_json(daten: bytes) -> list[dict]:
    """Kanonisches JSON der Extraktion (ein Dokument oder eine Liste) - geprueft, nicht veraendert."""
    try:
        obj = json.loads(daten.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as err:
        raise ValueError("weder PDF noch JSON der Extraktion") from err
    docs = obj if isinstance(obj, list) else [obj]
    if not docs or not all(isinstance(d, dict) and isinstance(d.get("boreholes"), list) and "file" in (d.get("document") or {})
                           for d in docs):
        raise ValueError("JSON ist keine Extraktion (document, boreholes)")
    return docs


def signatur(docs: list[dict]) -> str:
    return hashlib.sha256(json.dumps(docs, sort_keys=True).encode()).hexdigest()[:12]


def json_schreiben(pfad: Path, obj) -> None:
    pfad.parent.mkdir(parents=True, exist_ok=True)
    tmp = pfad.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj, ensure_ascii=False), encoding="utf-8")
    tmp.replace(pfad)                                     # nie halb geschriebene Dateien


@dataclass
class Auftrag:
    """Extraktion eines oder mehrerer PDFs im Hintergrund (Fortschritt je Seite)."""
    id: str
    dateien: list[str]
    stand: dict = field(default_factory=lambda: {"datei": "", "nr": 0, "dateien": 0, "seite": 0, "seiten": 0, "klasse": ""})
    fertig: bool = False
    fehler: list[str] = field(default_factory=list)
    projekt: str | None = None

    def als_dict(self) -> dict:
        return {"id": self.id, "dateien": self.dateien, "stand": self.stand, "fertig": self.fertig,
                "fehler": self.fehler, "projekt": self.projekt}


@dataclass
class Modellstand:
    schluessel: str
    modell: object | None
    bericht: dict | None
    vorb: pj.Vorbereitung
    fehler: str = ""


class Arbeitsplatz:
    def __init__(self, arbeit: Path | None = None):
        self.arbeit = Path(arbeit) if arbeit else pl.ARBEIT
        pl.ARBEIT = self.arbeit                           # Extraktion und Ablage im selben Ordner
        self.web = self.arbeit / "web"
        for unter in ("modelle", "unterlagen", "seiten"):
            (self.web / unter).mkdir(parents=True, exist_ok=True)
        self._projekte: dict[str, tuple[list[dict], pj.Projekt]] = {}
        self._sperren: dict[str, threading.RLock] = {}
        self._sperre = threading.Lock()
        self._extraktion = threading.Lock()               # der Extraktor ist nicht fuer parallele Laeufe gebaut
        self._auftraege: dict[str, Auftrag] = {}
        self._modelle: OrderedDict[str, tuple[object, dict]] = OrderedDict()

    # ------------------------------------------------------------ Projekte
    def ordner(self, sig: str) -> Path:
        if not sig.isalnum():
            raise KeyError(sig)
        return self.arbeit / "projekte" / sig

    def sperre(self, sig: str) -> threading.RLock:
        with self._sperre:
            return self._sperren.setdefault(sig, threading.RLock())

    def anlegen(self, docs: list[dict]) -> str:
        """Projekt zu diesen Dokumenten oeffnen; gibt es schon einen gespeicherten Stand, gilt er weiter."""
        sig = signatur(docs)
        ordner = self.ordner(sig)
        if not (ordner / "docs.json").exists():
            json_schreiben(ordner / "docs.json", docs)
        if sig not in self._projekte:
            p = None
            alt = self.arbeit / "projekte" / f"{sig}.json"           # Stand aus der Streamlit-App v2 (gleiche Signatur)
            for datei in (ordner / "projekt.json", alt):
                if p is None and datei.exists():
                    try:
                        p = pj.laden(json.loads(datei.read_text(encoding="utf-8")))
                    except (ValueError, TypeError, KeyError):
                        p = None                          # kaputter Stand: neu beginnen
            if p is not None and not p.name:
                p.name = pj.neues_projekt(docs, sig).name
            self._projekte[sig] = (docs, p or pj.neues_projekt(docs, sig))
            self.sichern(sig)
        return sig

    def laden(self, sig: str) -> tuple[list[dict], pj.Projekt]:
        if sig not in self._projekte:
            ordner = self.ordner(sig)
            if not (ordner / "docs.json").exists():
                raise KeyError(sig)
            docs = json.loads((ordner / "docs.json").read_text(encoding="utf-8"))
            p = pj.laden(json.loads((ordner / "projekt.json").read_text(encoding="utf-8"))) \
                if (ordner / "projekt.json").exists() else pj.neues_projekt(docs, sig)
            self._projekte[sig] = (docs, p)
        return self._projekte[sig]

    def sichern(self, sig: str) -> None:
        _, p = self._projekte[sig]
        json_schreiben(self.ordner(sig) / "projekt.json", pj.speichern(p))

    def zuruecksetzen(self, sig: str) -> None:
        """Alle Korrekturen, Lagen, Pruefhaken und Eincheckungen verwerfen."""
        with self.sperre(sig):
            docs, _ = self.laden(sig)
            self._projekte[sig] = (docs, pj.neues_projekt(docs, sig))
            self.sichern(sig)

    def loeschen(self, sig: str) -> None:
        with self.sperre(sig):
            self._projekte.pop(sig, None)
            shutil.rmtree(self.ordner(sig), ignore_errors=True)

    def liste(self) -> list[dict]:
        """Zuletzt bearbeitete Projekte (neueste zuerst)."""
        out = []
        for ordner in (self.arbeit / "projekte").glob("*/projekt.json"):
            try:
                d = json.loads(ordner.read_text(encoding="utf-8"))
                docs = json.loads((ordner.parent / "docs.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            n = sum(len(x["boreholes"]) for x in docs)
            gep = sum(1 for o in d.get("bohrung", {}).values() if o.get("geprueft"))
            out.append({"signatur": ordner.parent.name, "name": d.get("name") or ordner.parent.name,
                        "dokumente": [x["document"]["file"] for x in docs], "bohrungen": n, "geprueft": gep,
                        "eincheckungen": len(d.get("eincheckungen") or []), "geaendert": d.get("geaendert") or "",
                        "schritt": d.get("schritt") or "bohrungen"})
        return sorted(out, key=lambda x: x["geaendert"], reverse=True)

    # ------------------------------------------------------------ Aenderungen
    def aendern(self, sig: str, ops: list[dict]) -> list[str]:
        """Aenderungen der Reihe nach; bei einem Fehler bleibt der Stand vor diesem Aufruf (alles oder nichts)."""
        with self.sperre(sig):
            docs, p = self.laden(sig)
            sicherung = pj.speichern(p)
            meldungen = []
            try:
                for op in ops:
                    m = pj.aendern(docs, p, op)
                    if m:
                        meldungen.append(m)
            except (ValueError, KeyError, TypeError, IndexError) as fehler:
                self._projekte[sig] = (docs, pj.laden(sicherung))
                raise ValueError(str(fehler).strip("'\"")) from fehler
            self.sichern(sig)
            return meldungen

    # ------------------------------------------------------------ Zustand fuer die Oberflaeche
    def vorbereitung(self, docs: list[dict], p: pj.Projekt) -> tuple[pj.Vorbereitung, tuple[float, float], str]:
        vorb = pj.modell_eingabe(docs, p)
        ursprung = pj.ursprung(p, vorb)
        return vorb, ursprung, self._schluessel(vorb, p, ursprung)

    def _schluessel(self, vorb: pj.Vorbereitung, p: pj.Projekt, ursprung) -> str:
        """Schluessel der Modell-Eingaben (ohne Pruefhaken: Haken setzen rechnet nicht neu)."""
        e = pj.einstellungen(p)
        eingabe = {"docs": pl.ohne_pruefvermerke(vorb.docs), "vorgabe": p.vorgabe, "methode": e.methode,
                   "puffer": e.puffer, "raster": e.raster, "basis": e.basis, "ursprung": list(ursprung)}
        return hashlib.sha256(json.dumps(eingabe, sort_keys=True).encode()).hexdigest()[:16]

    def zustand(self, sig: str) -> dict:
        with self.sperre(sig):
            docs, p = self.laden(sig)
            vorb, ursprung, schluessel = self.vorbereitung(docs, p)
            gecacht = self._modelle.get(schluessel)
            bericht = gecacht[1] if gecacht else None
            epsgs = Counter(b.get("crs_epsg") for d in vorb.docs for b in d["boreholes"] if b.get("crs_epsg"))
            u = dict(p.unterlage) if p.unterlage else None
            if u:
                u["url"] = f"/dateien/unterlagen/{Path(u['datei']).name}"
                u.pop("datei", None)
                u.pop("pdf", None)
            letzter = p.eincheckungen[-1] if p.eincheckungen else None
            return {
                "signatur": sig, "name": p.name, "version": p.version, "schritt": p.schritt,
                "dokumente": [{"index": i, "datei": d["document"]["file"], "seiten": d["document"].get("pages"),
                               "pdf": pl.pdf_pfad(d["document"]) is not None} for i, d in enumerate(docs)],
                "lage_modus": p.lage_modus, "erzeugt": p.erzeugt, "auto": p.auto,
                "durchmesser": p.durchmesser, "durchmesser_auto": pj.durchmesser_auto(vorb),
                "ueberhoehung": p.ueberhoehung, "einstellungen": p.einstellungen,
                "unterlage": u, "reihe": pj.reihe_liste(docs, p), "reihe_standard": p.reihe["standard"],
                "vorgabe": p.vorgabe, "eincheckungen": p.eincheckungen,
                "pruefstand": pj.pruefstand(docs, p),
                "eingecheckt": pj.stand_text(letzter) if letzter else None,
                "seit_einchecken_geaendert": pj.seit_einchecken_geaendert(docs, p, schluessel),
                "bohrungen": pj.bohrungen_liste(docs, p),
                "klassen": pj.klassen_liste(),
                "hinweise": vorb.hinweise, "nicht_im_modell": vorb.nicht_im_modell,
                "modell": {"schluessel": schluessel, "aktuell": gecacht is not None,
                           "ifc": f"/dateien/modelle/{self._ifc_name(schluessel, docs, p)}"
                           if gecacht and (self.web / "modelle" / self._ifc_name(schluessel, docs, p)).exists() else None},
                "viewer": {"bohrungen": pj.viewer_bohrungen(docs, p, vorb, bericht), "ursprung": list(ursprung),
                           "epsg": epsgs.most_common(1)[0][0] if epsgs else None, "modus": p.lage_modus},
            }

    def bohrung(self, sig: str, bid: str) -> dict:
        with self.sperre(sig):
            docs, p = self.laden(sig)
            zeile = next((z for z in pj.bohrungen_liste(docs, p) if z["id"] == bid), None)
            if zeile is None:
                raise KeyError(bid)
            return {"bohrung": zeile, "schichten": pj.schichten_liste(docs, p, bid)}

    # ------------------------------------------------------------ Modell
    def _ifc_name(self, schluessel: str, docs: list[dict], p: pj.Projekt) -> str:
        """IFC fuer den Viewer: Geometrie-Schluessel + Durchmesser (die Saeulen gehoeren zum IFC, nicht zur Geometrie)."""
        dm = json.dumps([p.durchmesser, pj.durchmesser_je_code(docs, p)], sort_keys=True)
        return f"{schluessel}_{hashlib.sha256(dm.encode()).hexdigest()[:6]}.ifc"

    def modell(self, sig: str) -> dict:
        """Modell rechnen (oder aus dem Speicher) und das IFC fuer den Viewer ablegen."""
        with self.sperre(sig):
            docs, p = self.laden(sig)
            vorb, ursprung, schluessel = self.vorbereitung(docs, p)
            if not p.erzeugt:
                p.erzeugt = True
                self.sichern(sig)
            fehler = ""
            if schluessel not in self._modelle:
                if not vorb.lage:
                    fehler = "keine Bohrung mit Lage – im Schritt Lage setzen oder 'Reihe' wählen"
                else:
                    e = pj.einstellungen(p)
                    try:
                        m = pl.modell_bauen(vorb.docs, p.vorgabe, e.methode, e.puffer, e.raster, e.basis, ursprung)
                        self._modelle[schluessel] = (m, pl.bericht(m))
                        while len(self._modelle) > MODELLE_IM_SPEICHER:
                            self._modelle.popitem(last=False)
                    except ValueError as err:
                        fehler = str(err)
            if fehler:
                return {"schluessel": schluessel, "fehler": fehler, "bericht": None, "ifc": None,
                        "hinweise": vorb.hinweise, "nicht_im_modell": vorb.nicht_im_modell}
            self._modelle.move_to_end(schluessel)
            m, bericht = self._modelle[schluessel]
            name = self._ifc_name(schluessel, docs, p)
            ziel = self.web / "modelle" / name
            if not ziel.exists():
                ziel.write_bytes(pl.ifc_bytes(m, vorb.docs, durchmesser=p.durchmesser,
                                              durchmesser_je=pj.durchmesser_je_code(docs, p)))
                alte = sorted((self.web / "modelle").glob("*.ifc"), key=lambda f: f.stat().st_mtime)[:-20]
                for f in alte:
                    f.unlink(missing_ok=True)
            return {"schluessel": schluessel, "fehler": "", "bericht": bericht, "ifc": f"/dateien/modelle/{name}",
                    "hinweise": list(dict.fromkeys(vorb.hinweise + bericht["hinweise"])),
                    "nicht_im_modell": vorb.nicht_im_modell + bericht["ausgeschlossen"]}

    def einchecken(self, sig: str, kommentar: str) -> dict:
        with self.sperre(sig):
            docs, p = self.laden(sig)
            _, _, schluessel = self.vorbereitung(docs, p)
            eintrag = pj.einchecken(docs, p, schluessel if schluessel in self._modelle else None, kommentar)
            self.sichern(sig)
            return eintrag

    def export(self, sig: str, art: str) -> tuple[bytes, str, str]:
        """(Inhalt, Dateiname, Medientyp) fuer den Download."""
        with self.sperre(sig):
            docs, p = self.laden(sig)
            stamm = p.name or "baugrundmodell"
            vorb, _, schluessel = self.vorbereitung(docs, p)
            if art == "extraktion":
                return pl.json_bytes(docs if len(docs) > 1 else docs[0]), f"{stamm}_extraktion.json", "application/json"
            if art == "eingabe":
                return pl.json_bytes(vorb.docs), f"{stamm}_modell_eingabe.json", "application/json"
            if art == "projekt":
                return pl.json_bytes(pj.speichern(p)), f"{stamm}_projekt.json", "application/json"
        erg = self.modell(sig)
        if erg["fehler"]:
            raise ValueError(erg["fehler"])
        with self.sperre(sig):
            m, bericht = self._modelle[erg["schluessel"]]
            if art == "bericht":
                return pl.json_bytes(bericht), f"{stamm}_bericht.json", "application/json"
            if art == "einheiten":
                return pl.json_bytes(bericht["vorlage_einheiten"]), f"{stamm}_einheiten.json", "application/json"
            if art == "ifc":
                letzter = p.eincheckungen[-1] if p.eincheckungen else None
                inhalt = pl.ifc_bytes(m, vorb.docs, pruefstand=pj.stand_text(letzter) if letzter else "nicht eingecheckt",
                                      durchmesser=p.durchmesser, durchmesser_je=pj.durchmesser_je_code(docs, p))
                return inhalt, f"{stamm}.ifc", "application/x-step"
        raise KeyError(art)

    # ------------------------------------------------------------ Unterlage (Lageplan / Laengsschnitt)
    def unterlage_setzen(self, sig: str, name: str, daten: bytes | None, art: str, seite: int) -> None:
        """Neues PDF (daten) oder nur andere Seite/Ansicht der vorhandenen Unterlage (daten=None)."""
        if art not in ("plan", "schnitt"):
            raise ValueError("Ansicht: plan oder schnitt")
        with self.sperre(sig):
            docs, p = self.laden(sig)
            alt = p.unterlage or {}
            if daten is None:
                if not alt.get("pdf"):
                    raise ValueError("keine Unterlage")
                daten = Path(alt["pdf"]).read_bytes()
                name = alt["name"]
            sha = hashlib.sha256(daten).hexdigest()[:16]
            pdf = self.arbeit / "unterlagen" / f"{sha}.pdf"
            pdf.parent.mkdir(parents=True, exist_ok=True)
            if not pdf.exists():
                pdf.write_bytes(daten)
            bild = pl.unterlage_rendern(daten, seite)
            seite = min(max(0, int(seite)), bild["seiten"] - 1)
            png = self.web / "unterlagen" / f"{sha}_{seite}.png"
            png.write_bytes(bild["png"])
            gleich = (alt.get("sha"), alt.get("seite"), alt.get("art")) == (sha, seite, art)
            p.unterlage = {"sha": sha, "seite": seite, "seiten": bild["seiten"], "art": art, "name": name,
                           "datei": str(png), "pdf": str(pdf), "breite": bild["breite"], "hoehe": bild["hoehe"],
                           "mm_pro_px": bild["mm_pro_px"], "kalibrierung": alt.get("kalibrierung") if gleich else None}
            p.lage_modus = pj.LAGE_KOORDINATEN if art == "plan" else pj.LAGE_REIHE
            p.unterlage_zaehler += 1
            p.version += 1
            self.sichern(sig)

    def unterlage_entfernen(self, sig: str) -> None:
        with self.sperre(sig):
            _, p = self.laden(sig)
            p.unterlage = None
            p.version += 1
            self.sichern(sig)

    # ------------------------------------------------------------ Seiten des Gutachtens (Quelle einer Schicht)
    def seite(self, sig: str, dokument: int, seite: int) -> dict:
        docs, _ = self.laden(sig)
        if not 0 <= dokument < len(docs):
            raise KeyError(dokument)
        pfad = pl.pdf_pfad(docs[dokument]["document"])
        if pfad is None:
            raise KeyError("PDF nicht abgelegt (Beispiel ohne PDF)")
        import pymupdf
        sha = docs[dokument]["document"]["sha256"][:16]
        ziel = self.web / "seiten" / f"{sha}_{seite}.png"
        with pymupdf.open(pfad) as pdf:
            if not 0 <= seite < pdf.page_count:
                raise KeyError(seite)
            r = pdf[seite].rect
            skala = min(2400 / max(r.width, r.height), 200 / 72)
            if not ziel.exists():
                pdf[seite].get_pixmap(matrix=pymupdf.Matrix(skala, skala), alpha=False).save(str(ziel))
        return {"url": f"/dateien/seiten/{ziel.name}", "px_je_pt": skala, "breite_pt": r.width, "hoehe_pt": r.height,
                "seite": seite, "seiten": docs[dokument]["document"].get("pages")}

    # ------------------------------------------------------------ Extraktion im Hintergrund
    def extrahieren(self, dateien: list[tuple[str, bytes]], ocr: bool) -> Auftrag:
        a = Auftrag(uuid.uuid4().hex[:12], [n for n, _ in dateien])
        self._auftraege[a.id] = a
        threading.Thread(target=self._extrahieren, args=(a, dateien, ocr), daemon=True).start()
        return a

    def _extrahieren(self, a: Auftrag, dateien: list[tuple[str, bytes]], ocr: bool) -> None:
        docs = []
        with self._extraktion:
            for nr, (name, daten) in enumerate(dateien, start=1):
                a.stand.update(datei=name, nr=nr, dateien=len(dateien), seite=0, seiten=0, klasse="")
                if not daten.startswith(b"%PDF-"):              # Extraktion als JSON (Export oder Kommandozeile)
                    try:
                        docs += extraktion_aus_json(daten)
                    except ValueError as err:
                        a.fehler.append(f"{name}: {err}")
                    continue

                def melden(seite: int, seiten: int, klasse: str) -> None:
                    a.stand.update(seite=seite, seiten=seiten, klasse=klasse)
                try:
                    docs.append(pl.pdf_extrahieren(name, daten, ocr, melden))
                except Exception as err:                  # ein kaputtes PDF stoppt die anderen nicht
                    a.fehler.append(f"{name}: {type(err).__name__}: {err}")
                    traceback.print_exc()
        if docs and any(d["boreholes"] for d in docs):
            a.projekt = self.anlegen(docs)
        elif docs:
            a.fehler.append("In den Dokumenten wurde keine Bohrung erkannt. Ist eine Seite mit Bohrprofilen dabei? "
                            "Bei Scans OCR einschalten.")
        a.fertig = True

    def auftrag(self, aid: str) -> Auftrag:
        return self._auftraege[aid]

    def beispiel(self, schluessel: str, ocr: bool = False) -> dict:
        """Beispiel oeffnen: JSON direkt als Projekt, das PDF ueber die Extraktion (Auftrag)."""
        _, datei = BEISPIELE[schluessel]
        pfad = pl.BEISPIELE / datei
        if pfad.suffix == ".pdf":
            return {"auftrag": self.extrahieren([(pfad.name, pfad.read_bytes())], ocr).id}
        return {"projekt": self.anlegen([json.loads(pfad.read_text(encoding="utf-8"))])}
