"""Normen-Datenbank (normen.json) und Deutung von Schichtbeschreibungen nach DIN 4023, DIN EN ISO 14688-1 und DIN 18196.

Die Extraktion liefert je Schicht den Rohtext (description_raw) und eine grobe Klasse (soil_class). deuten() liest
den Rohtext - ausgeschrieben ("Schluff, stark tonig, kiesig, weich-steif, TA") oder in Kurzzeichen ("mS, fs', u")
- und liefert Hauptanteil, Nebenanteile mit Stufe, Benennung, Kurzzeichen nach DIN 4023 und DIN EN ISO 14688-1,
die genannte Bodengruppe nach DIN 18196, Konsistenz, Lagerungsdichte, Kalkgehalt, Feuchte, Bodenfarbe und
Beimengungen. Nichts wird geraten: die Bodengruppe steht nur, wenn sie im Text steht; Mehrdeutiges (Mg, Lehm,
Nomen ohne Anteil) und Widersprueche zur Extraktion stehen in den Hinweisen. Ein Vorschlag fuer eine
unklassifizierte Schicht wird angezeigt, aber nie still uebernommen (docs/21_normen_bodenansprache.md).
"""
from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path

NORMEN = json.loads(Path(__file__).with_name("normen.json").read_text(encoding="utf-8"))
KLASSEN: dict[str, dict] = NORMEN["klassen"]
FELS: dict[str, dict] = NORMEN["fels"]
UNKLASSIFIZIERT = "unklassifiziert"
NORMSTAND = "DIN 4023:2023-02, DIN EN ISO 14688-1, DIN EN ISO 14689, DIN 18196"

FRAKTION_NAME = {"f": "Fein", "m": "Mittel", "g": "Grob"}
FRAKTION_ISO = {"f": "f", "m": "m", "g": "c"}
ISO_NEBEN = {"Kies": "gr", "Sand": "sa", "Schluff": "si", "Ton": "cl", "Steine": "co", "Bloecke": "bo"}


def _ohne_akzent(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s) if not unicodedata.combining(c))


def _schluessel(wort: str) -> str:
    """Vergleichsform: klein, Umlaute wie ae/oe/ue und wie ohne Punkte (OCR verliert sie, E6)."""
    return wort.lower().replace("ß", "ss")


# ---------------------------------------------------------------- Woerterbuecher aus der Datenbank
_WORT_KLASSE: dict[str, str] = {}
for _k, _e in KLASSEN.items():
    for _w in _e.get("woerter", []):
        _WORT_KLASSE[_schluessel(_w)] = _k
        _WORT_KLASSE[_schluessel(_ohne_akzent(_w))] = _k
_FELS_WORT = {_schluessel(k): k for k in FELS}
_FELS_KURZ = {e["kurz"]: k for k, e in FELS.items() if e.get("kurz")}
_KONSISTENZ = {_schluessel(e["name"]): e["name"] for e in NORMEN["konsistenz"]}
_KONSISTENZ.update({k: e["name"] for e in NORMEN["konsistenz"] for k in e["kurz"]})
_KALK = {e["name"]: e["name"] for e in NORMEN["kalkgehalt"]}
_KALK.update({k: e["name"] for e in NORMEN["kalkgehalt"] for k in e["kurz"]})
_FEUCHTE = {_schluessel(w): w for w in NORMEN["feuchte"]}
_ANTHROPOGEN = tuple(_schluessel(w) for w in NORMEN["anthropogen"])
_VERWITTERUNG = sorted((_schluessel(w) for w in NORMEN["verwitterung"]), key=len, reverse=True)
_GRUPPEN = NORMEN["bodengruppen_din18196"]
_NEBEN = NORMEN["nebenanteile"]
_STUFEN = NORMEN["stufen"]
_HAUPT_KURZ_KLASSE = {e["din4023"]: k for k, e in KLASSEN.items() if e.get("din4023") and k not in ("Geschiebemergel",)}
_ISO_KLASSE = {"Gr": "Kies", "Sa": "Sand", "Si": "Schluff", "Cl": "Ton", "Co": "Steine", "Bo": "Bloecke", "Or": "Torf"}
_FARB_STAEMME = sorted({_schluessel(n) for n in NORMEN["bodenfarben"]} | {"bräun", "röt", "gruen", "weiss", "rost"} |
                       {k for e in NORMEN["bodenfarben"].values() for k in e["kurz"]}, key=len, reverse=True)
_MUSTER = ("gefleckt", "fleckig", "marmoriert", "gestreift", "gebändert", "gebaendert", "bunt", "scheckig")

# ---------------------------------------------------------------- Muster
_STUFE_RE = r"(?P<stufe>sehr\s+schwach|schwach|leicht|gering|mäßig|maessig|sehr\s+stark|stark)"
_NEBEN_WORT_RE = re.compile(
    rf"^(?:{_STUFE_RE}\s*)?(?P<f>fein|mittel|grob)?(?P<n>kiesig|sandig|schluffig|tonig|steinig|blockig|humos|organisch|"
    r"torfig|muddig|anmoorig)(?:\s*(?:-|bis)\s*(?P<f2>fein|mittel|grob)?(?:kiesig|sandig|schluffig|tonig))?$", re.I)
_ADJEKTIV = {"kiesig": "g", "sandig": "s", "schluffig": "u", "tonig": "t", "steinig": "x", "blockig": "y", "humos": "h",
             "organisch": "o"}
_HAUPT_KURZ_RE = re.compile(r"^(?:(?P<f1>[fmg])(?:-(?P<f2>[fmg]))?)?(?P<h>[SGU])(?:\s*-\s*(?P<f3>[fmg])(?P=h))?$")
_ISO_KURZ_RE = re.compile(r"^(?P<f>[fmc])?(?P<h>Gr|Sa|Si)$|^(?P<h2>Cl|Co|Bo|Or)$")
_NEBEN_KURZ_RE = re.compile(r"^(?:(?P<f>[fmg])(?P<n>[sg])|(?P<n2>[sgutxyho]))(?P<z>''|'|\*\*|\*|=)?$")
_GRUPPE_RE = re.compile(r"^(?P<k>\[)?(?P<g>GU\*|GT\*|SU\*|ST\*|GE|GW|GI|SE|SW|SI|GU|GT|SU|ST|UL|UM|UA|TL|TM|TA|OU|OT|OH|OK|HN|HZ)(?(k)\])$")
_KONS_RE = re.compile(r"^(?P<a>breiig|weich|steif|halbfest|fest|brg|brei|wch|stf|hfst|fst)"
                      r"(?:\s*(?:-|bis|/)\s*(?P<b>breiig|weich|steif|halbfest|fest|brg|brei|wch|stf|hfst|fst))?$", re.I)
_LAGER_RE = re.compile(r"^(?P<a>(?:sehr\s+)?(?:locker|mitteldicht|dicht))(?:\s*(?:-|bis)\s*(?P<b>(?:sehr\s+)?(?:locker|mitteldicht|dicht)))?"
                       r"(?:\s+gelagert)?$", re.I)
_KALK_RE = re.compile(r"^(?:(?P<w>kalkfrei|schwach\s+kalkhaltig|kalkhaltig|stark\s+kalkhaltig|kalkig|karbonatfrei|karbonathaltig)"
                      r"|(?P<k>k\s*(?:0|\+\+|\+)))$", re.I)
_SPANNE_RE = re.compile(r"^(?P<f1>fein|mittel|grob)(?:-|\s*(?P<h1>sand|kies|schluff))?\s*(?:bis|-)\s*(?P<f2>fein|mittel|grob)"
                        r"(?P<h>sand|kies|schluff)$", re.I)
_FRAKTION_RE = re.compile(r"^(?P<f>fein|mittel|grob)(?P<h>sand|kies|schluff)$", re.I)
_HAUPT_KLASSE = {"sand": "Sand", "kies": "Kies", "schluff": "Schluff"}
_BEIMENGUNG_ENDUNGEN = ("reste", "resten", "rest", "bröckchen", "broeckchen", "brocken", "stücke", "stuecke", "stucke",
                        "stückchen", "einschlüsse", "einschluesse", "lagen", "linsen", "bänder", "baender", "schmitzen",
                        "nester", "geoden", "beimengungen", "anteile", "splitter")
# Hauptwoerter fuer die Tippfehler-Suche (OCR: "Grobaand" -> "Grobsand"); nur lange Woerter, Abstand 1
_HAUPTWOERTER = sorted({w for w in _WORT_KLASSE if len(w) >= 5 and " " not in w} |
                       {f"{f}{h}" for f in ("fein", "mittel", "grob") for h in ("sand", "kies", "schluff")} |
                       {w for w in _FELS_WORT if len(w) >= 5})


def _abstand(a: str, b: str) -> int:
    """Levenshtein-Abstand (klein, nur fuer kurze Woerter)."""
    vorher = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        jetzt = [i]
        for j, cb in enumerate(b, 1):
            jetzt.append(min(vorher[j] + 1, jetzt[j - 1] + 1, vorher[j - 1] + (ca != cb)))
        vorher = jetzt
    return vorher[-1]


_NICHT_FELS = {"steine", "feldsteine", "pflastersteine", "ziegelstein", "ziegelsteine", "feldstein", "bruchsteine"}


@dataclass
class Anteil:
    klasse: str                     # Modellklasse der Fraktion (Kies, Sand, Schluff, Ton, Steine, Bloecke, Torf, Mudde)
    stufe: str                      # "sehr schwach" | "schwach" | "" | "stark" | "sehr stark" | "?" (Nomen ohne Anteil)
    fraktion: str = ""              # f/m/g oder Spanne "f-m"
    text: str = ""                  # "schwach feinsandig"
    din4023: str = ""               # "fs'"


@dataclass
class Deutung:
    text: str
    klasse: str | None = None       # Modellklasse (Vokabular der Extraktion); None = nicht erkannt
    hauptanteil: str = ""           # "Mittelsand", "Schluff", "Tonstein", "Auffüllung"
    fraktion: str = ""              # f/m/g/"f-m" des Hauptanteils
    material: dict | None = None    # Auffuellung/Mutterboden: Klasse und Fraktion des Materials
    nebenanteile: list[Anteil] = field(default_factory=list)
    benennung: str = ""
    din4023: str = ""
    iso14688: str = ""
    bodengruppe: str | None = None  # DIN 18196, nur wenn genannt
    bodengruppe_name: str = ""
    konsistenz: str | None = None
    lagerung: str | None = None
    kalk: str | None = None
    feuchte: str | None = None
    bodenfarbe: str | None = None
    fels: dict | None = None        # {"art", "kurz", "verwitterung"}
    beimengungen: list[str] = field(default_factory=list)
    anthropogen: list[str] = field(default_factory=list)
    sonstiges: list[str] = field(default_factory=list)
    hinweise: list[str] = field(default_factory=list)
    sicher: bool = False            # Hauptanteil eindeutig erkannt
    farbe: str = KLASSEN[UNKLASSIFIZIERT]["farbe"]   # Anzeige nach DIN 4023 (siehe farbinfo)
    farbname: str = ""

    def als_dict(self) -> dict:
        return asdict(self)


@dataclass
class _Kandidat:
    klasse: str
    fraktionen: list[str]
    name: str
    quelle: str                     # "kurz" | "wort" | "iso"
    alternativen: tuple[str, ...] = ()


# ---------------------------------------------------------------- Farben
def farbinfo(klasse: str | None, fraktion: str = "") -> dict:
    """Farbe einer Modellklasse: {hex, name, beleg}. 'Fels (Tonstein)' nimmt die Felsart, Grobschluff tuerkis."""
    k = klasse or UNKLASSIFIZIERT
    if k.startswith("Fels"):
        art = re.match(r"Fels\s*\((.+)\)", k)
        e = FELS.get(art.group(1).strip()) if art else None
        e = e or KLASSEN["Fels"]
    else:
        e = KLASSEN.get(k) or KLASSEN[UNKLASSIFIZIERT]
        fr = (e.get("fraktionen") or {}).get(fraktion) if fraktion and "-" not in fraktion else None
        if fr and fr.get("farbe"):
            e = fr
    return {"hex": e["farbe"], "name": e.get("farbname", ""), "beleg": e.get("beleg", "darstellung")}


def bekannt(klasse: str | None) -> bool:
    return bool(klasse) and (klasse in KLASSEN or klasse.startswith("Fels")) and klasse != UNKLASSIFIZIERT


ANZEIGE = {"Auffuellung": "Auffüllung", "Bloecke": "Blöcke", "Loess": "Löss", "Loesslehm": "Lösslehm"}


def anzeigename(klasse: str | None) -> str:
    """Name mit Umlauten fuer die Oberflaeche (die Klasse selbst bleibt ASCII wie in der Extraktion)."""
    return ANZEIGE.get(klasse or "", klasse or UNKLASSIFIZIERT)


def klassen_liste() -> list[dict]:
    """Auswahl fuer die Oberflaeche: Modellklassen mit Farbe und Kurzzeichen (Boeden zuerst)."""
    rang = {"boden": 0, "organisch": 1, "geologisch": 2, "fels": 3, "anthropogen": 4, "unbekannt": 5}
    out = [{"klasse": k, "name": anzeigename(k), "art": e["art"], "farbe": e["farbe"], "farbname": e.get("farbname", ""),
            "din4023": e.get("din4023", ""), "iso14688": e.get("iso14688", ""), "beleg": e.get("beleg", "")}
           for k, e in KLASSEN.items()]
    out += [{"klasse": f"Fels ({k})", "name": f"Fels ({k})", "art": "fels", "farbe": e["farbe"], "farbname": e.get("farbname", ""),
             "din4023": e.get("kurz", ""), "iso14688": "", "beleg": e.get("beleg", "")} for k, e in FELS.items()]
    return sorted(out, key=lambda x: (rang.get(x["art"], 9), x["klasse"] != "Fels"))     # sonst Reihenfolge der Datenbank


# ---------------------------------------------------------------- Text vorbereiten
_STRICHE = str.maketrans({"’": "'", "‘": "'", "´": "'", "`": "'", "′": "'", "ʼ": "'", "″": "''", "”": "''", "“": "''",
                          '"': "''", "–": "-", "—": "-", "‐": "-", "‑": "-"})


def _vorbereiten(text: str) -> str:
    t = unicodedata.normalize("NFC", text or "").translate(_STRICHE)
    t = re.sub(r"̿|[̅̄]{2}", "**", t)          # doppelter Ueberstrich: sehr stark
    t = re.sub(r"[̅̄¯‾]", "*", t)                     # Ueberstrich: stark
    t = re.sub(r"(\d),(\d)", r"\1.\2", t)                       # Dezimalkomma ist kein Trenner (770,17 mNN)
    # zusammengeschrieben (PDF-Textlage, OCR): "schwachhumos", "FeinsandbisMittelsand", "MittelsandFeinkies"
    t = re.sub(r"(?i)\b(sehr|schwach|stark)(?=(fein|mittel|grob)?(kiesig|sandig|schluffig|tonig|steinig|humos|organisch))",
               r"\1 ", t)
    t = re.sub(r"(?<=[a-zäöüß])\s*bis\s*(?=(?:[Ff]ein|[Mm]ittel|[Gg]rob)?(?:[Ss]and|[Kk]ies|[Ss]chluff|kiesig|sandig|schluffig|"
               r"tonig)|[A-ZÄÖÜ])", " bis ", t)
    t = re.sub(r"(?<=[a-zäöüß]{3})(?=[A-ZÄÖÜ])", ", ", t)
    return t


def _segmente(t: str) -> list[str]:
    # Klammern: eckige um eine Bodengruppe bleiben ([GW] = Auffuellung aus natuerlichem Boden), sonst Trenner
    t = re.sub(r"\[(?!(?:G[EWIUT]|S[EWIUT]|U[LMA]|T[LMA]|O[UTHK]|H[NZ])\*?\])", ",", t)
    t = re.sub(r"(?<!\*)(?<![A-Z])\]", ",", t)
    t = re.sub(r"[(){}]", ",", t)
    teile = re.split(r"[,;/\n]+|\s+-\s+|\s+u\.\s+|\s+und\s+", t)
    return [s.strip(" .:~-") for s in teile if s.strip(" .:~-")]


# ---------------------------------------------------------------- Deutung
def _stufe_wort(s: str | None) -> str:
    if not s:
        return ""
    return NORMEN["stufe_woerter"].get(re.sub(r"\s+", " ", s.lower()), "")


def _stufe_zeichen(z: str | None) -> str:
    return {"''": "sehr schwach", "'": "schwach", "*": "stark", "**": "sehr stark", "=": "sehr stark"}.get(z or "", "")


def _neben_text(schluessel: str, stufe: str, f2: str = "") -> str:
    adj = _NEBEN[schluessel]["adjektiv"]
    if f2:
        adj = f"{adj} bis {f2}{_NEBEN[schluessel[-1]]['adjektiv']}"
    if stufe == "?":
        return f"{adj} (Anteil ohne Angabe)"
    return f"{stufe} {adj}".strip()


def _kurz_mit_stufe(schluessel: str, stufe: str) -> str:
    if stufe in ("stark", "sehr stark"):
        strich = "̅" if stufe == "stark" else "̿"
        return "".join(c + strich for c in schluessel)
    return schluessel + {"schwach": "'", "sehr schwach": "''", "?": "(?)"}.get(stufe, "")


class _Leser:
    """Sammelt die Angaben einer Beschreibung Segment fuer Segment."""

    def __init__(self, d: Deutung):
        self.d = d
        self.kandidaten: list[_Kandidat] = []
        self.neben: list[tuple[str, str, str]] = []           # (schluessel, stufe, f2)
        self.vermutet = False                                  # ein Hauptwort nur ueber Tippfehler-Suche erkannt

    def segment(self, s: str, tief: int = 0) -> None:
        if not s or tief > 3:
            return
        for pruefung in (self._gruppe, self._haupt_kurz, self._neben_kurz, self._konsistenz, self._lagerung, self._kalk,
                         self._feuchte, self._neben_wort, self._mit, self._farbe, self._verwitterung, self._haupt_wort,
                         self._beimengung, self._tippfehler):
            if pruefung(s):
                return
        woerter = s.split()
        if len(woerter) > 1:
            # Hauptwort am Anfang, dann der Rest ("Sand schwach humos", "Tonstein stark verwittert")
            for n in (2, 1):
                kopf = " ".join(woerter[:n])
                if len(woerter) > n and (self._haupt_kurz(kopf) or self._haupt_wort(kopf)):
                    self.segment(" ".join(woerter[n:]), tief + 1)
                    return
            erkannt = [w for w in woerter if self._ein_wort(w)]
            rest = [w for w in woerter if w not in erkannt]
            if erkannt and rest:
                self.d.sonstiges.append(" ".join(rest))
                return
            if erkannt:
                return
        self.d.sonstiges.append(s)

    def _ein_wort(self, w: str) -> bool:
        return any(p(w) for p in (self._gruppe, self._haupt_kurz, self._neben_kurz, self._konsistenz, self._kalk,
                                  self._feuchte, self._neben_wort, self._farbe, self._haupt_wort, self._beimengung))

    # -------------------------------------------------- Pruefungen (True = Segment verbraucht)
    def _gruppe(self, s: str) -> bool:
        m = _GRUPPE_RE.match(s)
        if not m:
            return False
        g = m.group("g")
        if m.group("k"):
            self.d.bodengruppe, self.d.bodengruppe_name = f"[{g}]", f"{_GRUPPEN['[]']['name']}: {_GRUPPEN[g]['name']}"
        else:
            self.d.bodengruppe, self.d.bodengruppe_name = g, _GRUPPEN[g]["name"]
        return True

    def _haupt_kurz(self, s: str) -> bool:
        m = _HAUPT_KURZ_RE.match(s)
        if m:
            klasse = {"S": "Sand", "G": "Kies", "U": "Schluff"}[m.group("h")]
            fr = [f for f in (m.group("f1"), m.group("f2"), m.group("f3")) if f]
            self.kandidaten.append(_Kandidat(klasse, fr, s, "kurz"))
            return True
        m = _ISO_KURZ_RE.match(s)
        if m:
            klasse = _ISO_KLASSE[m.group("h") or m.group("h2")]
            fr = [{"c": "g"}.get(m.group("f"), m.group("f"))] if m.group("f") else []
            self.kandidaten.append(_Kandidat(klasse, fr, s, "iso"))
            if s == "Gr":
                self.d.hinweise.append("Gr gelesen als Kies (DIN EN ISO 14688-1)")
            return True
        if s == "Mg":
            self.kandidaten.append(_Kandidat("Geschiebemergel", [], s, "kurz", ("Geschiebemergel", "Auffuellung")))
            return True
        if s in _FELS_KURZ:
            self._fels(_FELS_KURZ[s])
            return True
        if s in _HAUPT_KURZ_KLASSE:
            self.kandidaten.append(_Kandidat(_HAUPT_KURZ_KLASSE[s], [], s, "kurz"))
            if s == "H":
                self.d.hinweise.append("H = Torf oder Humus (DIN 4023)")
            return True
        return False

    def _neben_kurz(self, s: str) -> bool:
        m = _NEBEN_KURZ_RE.match(s)
        if not m:
            return False
        schluessel = (m.group("f") + m.group("n")) if m.group("n") else m.group("n2")
        self.neben.append((schluessel, _stufe_zeichen(m.group("z")), ""))
        return True

    def _konsistenz(self, s: str) -> bool:
        m = _KONS_RE.match(s)
        if not m:
            return False
        a = _KONSISTENZ[_schluessel(m.group("a"))]
        b = _KONSISTENZ[_schluessel(m.group("b"))] if m.group("b") else None
        self.d.konsistenz = f"{a} bis {b}" if b and b != a else a
        return True

    def _lagerung(self, s: str) -> bool:
        m = _LAGER_RE.match(s)
        if not m:
            return False
        a, b = (re.sub(r"\s+", " ", (x or "").lower()) for x in (m.group("a"), m.group("b")))
        self.d.lagerung = f"{a} bis {b}" if b else a
        return True

    def _kalk(self, s: str) -> bool:
        m = _KALK_RE.match(s)
        if not m:
            return False
        if m.group("k"):
            self.d.kalk = _KALK[re.sub(r"\s+", "", m.group("k").lower())]
        else:
            w = re.sub(r"\s+", " ", m.group("w").lower())
            self.d.kalk = {"kalkig": "kalkhaltig", "karbonatfrei": "kalkfrei", "karbonathaltig": "kalkhaltig"}.get(w, w)
        return True

    def _feuchte(self, s: str) -> bool:
        w = _FEUCHTE.get(_schluessel(s))
        if w:
            self.d.feuchte = {"naß": "nass", "wassergesaettigt": "wassergesättigt"}.get(w, w)
            return True
        return False

    def _neben_wort(self, s: str) -> bool:
        m = _NEBEN_WORT_RE.match(s)
        if not m:
            return False
        n = m.group("n").lower()
        basis = _ADJEKTIV.get(n) or NORMEN["nebenanteil_woerter"][n]
        f = {"fein": "f", "mittel": "m", "grob": "g"}.get((m.group("f") or "").lower(), "")
        schluessel = f + basis if f and basis in ("s", "g") else basis
        f2 = (m.group("f2") or "").lower()
        self.neben.append((schluessel, _stufe_wort(m.group("stufe")), f2))
        return True

    def _mit(self, s: str) -> bool:
        m = re.match(r"^mit\s+(.+)$", s, re.I)
        if not m:
            return False
        self._beimengung_eintragen(m.group(1))
        return True

    def _farbe(self, s: str) -> bool:
        teile = [t for t in re.split(r"[-\s]+", _schluessel(s)) if t]
        if not teile:
            return False
        stamm = "|".join(re.escape(x) for x in _FARB_STAEMME)
        einzel = re.compile(rf"^(?:(?:hell|dunkel|h|d)?(?:{stamm})(?:lich)?)+$")
        if all(einzel.match(t) or t in _MUSTER or t in ("bis", "und") for t in teile) and \
                any(einzel.match(t) for t in teile):
            self.d.bodenfarbe = f"{self.d.bodenfarbe}, {s}" if self.d.bodenfarbe else s
            return True
        return False

    def _verwitterung(self, s: str) -> bool:
        w = _schluessel(s)
        if any(w == v or w.startswith(v + " ") for v in _VERWITTERUNG) or re.fullmatch(r"(?:mäßig|maessig|sehr|schwach)?\s*hart", w):
            self.d.fels = {**(self.d.fels or {}), "verwitterung": ", ".join(filter(None, [(self.d.fels or {}).get("verwitterung"), s]))}
            return True
        return False

    def _fels(self, art: str) -> None:
        e = FELS.get(art, {})
        self.kandidaten.append(_Kandidat(f"Fels ({art})", [], art, "wort"))
        self.d.fels = {**(self.d.fels or {}), "art": art, "kurz": e.get("kurz", "")}

    def _haupt_wort(self, s: str) -> bool:
        w = _schluessel(s)
        m = _SPANNE_RE.match(s)
        if m:
            h = _HAUPT_KLASSE[m.group("h").lower()]
            if m.group("h1") and m.group("h1").lower() != m.group("h").lower():
                return False
            self.kandidaten.append(_Kandidat(h, [m.group("f1")[0].lower(), m.group("f2")[0].lower()], s, "wort"))
            return True
        m = _FRAKTION_RE.match(s)
        if m:
            self.kandidaten.append(_Kandidat(_HAUPT_KLASSE[m.group("h").lower()], [m.group("f")[0].lower()], s, "wort"))
            return True
        klasse = _WORT_KLASSE.get(w) or _WORT_KLASSE.get(_schluessel(_ohne_akzent(s)))
        if klasse:
            if klasse == "Auffuellung" and w not in ("auffüllung", "auffuellung", "auffullung", "anschüttung", "anschuettung",
                                                      "anschuttung", "aufschüttung", "aufschuettung", "aufschuttung"):
                self.d.anthropogen.append(s)                       # Bauschutt, Schotter, RC-Material
                if w == "schotter":
                    self.d.hinweise.append(f"Schotter mehrdeutig: {NORMEN['mehrdeutig']['Schotter']}")
            self.kandidaten.append(_Kandidat(klasse, [], s, "wort"))
            return True
        if w in _FELS_WORT:
            self._fels(_FELS_WORT[w])
            return True
        if " " not in w and w.endswith("stein") and w not in _NICHT_FELS and len(w) > 6 and \
                not any(w.startswith(a) for a in _ANTHROPOGEN):
            self._fels(s[:1].upper() + s[1:])
            return True
        return False

    def _tippfehler(self, s: str) -> bool:
        w = _schluessel(s)
        if " " in w or len(w) < 5 or not w.isalpha():
            return False
        treffer = [h for h in _HAUPTWOERTER if abs(len(h) - len(w)) <= 1 and _abstand(w, h) == 1]
        if len(treffer) != 1 or not self._haupt_wort(treffer[0]):
            return False
        self.vermutet = True
        self.d.hinweise.append(f"'{s}' gelesen als '{treffer[0].capitalize()}' (Schreib- oder OCR-Fehler?)")
        return True

    def _beimengung(self, s: str) -> bool:
        w = _schluessel(s)
        if " " in w:                                     # mehrere Woerter: einzeln lesen ("770.17 mNN Beton")
            return False
        if w.endswith(_BEIMENGUNG_ENDUNGEN) or _anthropogen(s):
            self._beimengung_eintragen(s)
            return True
        return False

    def _beimengung_eintragen(self, s: str) -> None:
        self.d.beimengungen.append(s)
        if _anthropogen(s):
            self.d.anthropogen.append(s)


def _fraktion_text(fr: list[str]) -> str:
    fr = list(dict.fromkeys(fr))
    if not fr:
        return ""
    if len(fr) == 1:
        return fr[0]
    reihe = "fmg"
    fr.sort(key=reihe.index)
    return f"{fr[0]}-{fr[-1]}"


def _haupt_name(klasse: str, fraktion: str) -> str:
    if klasse.startswith("Fels"):
        art = re.match(r"Fels\s*\((.+)\)", klasse)
        return art.group(1) if art else "Fels"
    e = KLASSEN.get(klasse, {})
    stamm = {"Kies": "kies", "Sand": "sand", "Schluff": "schluff"}.get(klasse)
    if stamm and fraktion:
        teile = fraktion.split("-")
        if len(teile) == 2:
            return f"{FRAKTION_NAME[teile[0]]}- bis {FRAKTION_NAME[teile[1]]}{stamm}"
        return f"{FRAKTION_NAME[teile[0]]}{stamm}"
    return anzeigename(klasse)


def _haupt_kurz(klasse: str, fraktion: str) -> tuple[str, str]:
    """(DIN 4023, ISO 14688-1) des Hauptanteils."""
    if klasse.startswith("Fels"):
        art = re.match(r"Fels\s*\((.+)\)", klasse)
        e = FELS.get(art.group(1)) if art else None
        return ((e or {}).get("kurz") or (art.group(1) if art else "Fels"), "")
    e = KLASSEN.get(klasse, {})
    din, iso = e.get("din4023", ""), e.get("iso14688", "")
    if fraktion and din in ("S", "G", "U"):
        din = fraktion + din
        iso = (FRAKTION_ISO[fraktion] + iso) if "-" not in fraktion else iso
    return din, iso


def deuten(text: str | None, soil_class: str | None = None) -> Deutung:
    """Schichtbeschreibung nach Norm lesen. soil_class: Klasse der Extraktion (nur zum Abgleich, wird nicht geaendert)."""
    d = Deutung(text=text or "")
    if not (text or "").strip():
        d.hinweise.append("keine Beschreibung")
        return _abschliessen(d, soil_class)
    leser = _Leser(d)
    for s in _segmente(_vorbereiten(text)):
        leser.segment(s)

    kand = leser.kandidaten
    haupt: _Kandidat | None = None
    material: _Kandidat | None = None
    if kand:
        auff = next((k for k in kand if k.klasse == "Auffuellung"), None)
        erste = kand[0]
        natuerlich = [k for k in kand if KLASSEN.get(k.klasse, {}).get("art") in ("boden", "organisch", "geologisch")
                      and k.klasse not in ("Auffuellung", "Mutterboden")]
        if erste.klasse in ("Beton", "Asphalt", "Schwarzdecke", "Pflaster"):
            haupt = erste
        elif auff is not None:
            haupt = auff
            material = next((k for k in natuerlich), None)
            if auff is not erste and erste.klasse != "Auffuellung":
                d.hinweise.append(f"Auffüllung genannt (Material: {erste.name}) – nicht gewachsener Boden")
        elif erste.klasse == "Mutterboden":
            haupt, material = erste, next((k for k in natuerlich), None)
        elif KLASSEN.get(erste.klasse, {}).get("art") == "geologisch":
            # "Geschiebemergel, Schluff, sandig, kiesig": geologische Benennung + Bodenart des Materials
            haupt = erste
            material = next((k for k in natuerlich if KLASSEN[k.klasse]["art"] in ("boden", "organisch")), None)
        else:
            haupt = erste
        if haupt.alternativen:                                  # Mg: Geschiebemergel oder Auffuellung
            text_k = _schluessel(text)
            if "geschiebe" in text_k or "mergel" in text_k:
                pass
            elif d.anthropogen or _anthropogen(text):
                haupt = _Kandidat("Auffuellung", [], haupt.name, "kurz")
            else:
                d.hinweise.append(f"Mg mehrdeutig: {NORMEN['mehrdeutig']['Mg']}")
                haupt = _Kandidat(soil_class, [], haupt.name, "kurz") if soil_class in haupt.alternativen else None
        # weitere Hauptwoerter: gleiche Bodenart -> Kornspanne, andere -> Nebenanteil ohne Angabe
        if haupt is not None:
            bezug = material or haupt
            fr = list(bezug.fraktionen)
            for k in kand:
                if k is haupt or k is material or k.klasse in ("Auffuellung",) or k.klasse.startswith("Fels"):
                    continue
                if k.klasse == bezug.klasse:
                    fr += k.fraktionen
                elif k.klasse == "Mutterboden" and haupt.klasse != "Mutterboden":
                    d.hinweise.append(f"{k.name} genannt")
                else:
                    schluessel = _NEBEN_SCHLUESSEL.get(k.klasse)
                    if schluessel:
                        f = _fraktion_text(k.fraktionen)
                        leser.neben.append(((f if len(f) == 1 and schluessel in ("s", "g") else "") + schluessel, "?", ""))
                    else:
                        d.sonstiges.append(k.name)
            bezug.fraktionen = fr

    if haupt is not None and material is None and (d.bodengruppe or "").startswith("[") and \
            KLASSEN.get(haupt.klasse, {}).get("art") in ("boden", "geologisch"):
        material, haupt = haupt, _Kandidat("Auffuellung", [], d.bodengruppe, "gruppe")
        d.hinweise.append(f"Bodengruppe {d.bodengruppe} in eckigen Klammern: Auffüllung aus natürlichem Boden (DIN 18196)")
    if haupt is None and d.bodengruppe:
        g = d.bodengruppe.strip("[]")
        kl = _GRUPPEN[g]["klasse"]
        if kl:
            haupt = _Kandidat("Auffuellung" if d.bodengruppe.startswith("[") else kl, [], d.bodengruppe, "gruppe")
            d.hinweise.append(f"Bodenart nur aus der Bodengruppe {d.bodengruppe} abgeleitet")

    if haupt is not None:
        d.klasse = haupt.klasse
        d.sicher = (haupt.quelle != "gruppe" or material is not None) and haupt.klasse not in ("Lehm", "Mergel") and \
            not leser.vermutet
        if material is not None:
            mf = _fraktion_text(material.fraktionen)
            d.material = {"klasse": material.klasse, "fraktion": mf, "name": _haupt_name(material.klasse, mf)}
            d.fraktion = ""
        else:
            d.fraktion = _fraktion_text(haupt.fraktionen)
        d.hauptanteil = _haupt_name(haupt.klasse, d.fraktion)
        if haupt.klasse in ("Lehm", "Mergel"):
            d.hinweise.append(KLASSEN[haupt.klasse]["hinweis"])
    elif kand:
        d.hinweise.append("Hauptanteil nicht eindeutig")
    else:
        d.hinweise.append("keine Boden- oder Felsart erkannt")

    # Nebenanteile: gleiche Angabe nur einmal (die staerkere gilt)
    gesehen: dict[str, Anteil] = {}
    for schluessel, stufe, f2 in leser.neben:
        if schluessel not in _NEBEN:
            continue
        neu = Anteil(_NEBEN[schluessel]["klasse"], stufe, _NEBEN[schluessel].get("fraktion", ""),
                     _neben_text(schluessel, stufe, f2), _kurz_mit_stufe(schluessel, stufe))
        alt = gesehen.get(schluessel)
        if alt is None or _STUFEN[stufe]["rang"] > _STUFEN[alt.stufe]["rang"]:
            gesehen[schluessel] = neu
    d.nebenanteile = sorted(gesehen.values(), key=lambda a: -_STUFEN[a.stufe]["rang"] if a.stufe != "?" else 1)
    return _abschliessen(d, soil_class)


_BEREICH = {"Kies": "grobkörnig", "Sand": "grobkörnig", "Schluff": "feinkörnig", "Ton": "feinkörnig", "Torf": "organisch",
            "Mudde": "organisch"}


def _anthropogen(s: str) -> bool:
    """Fremdstoff im Text: ein Wort beginnt mit einem Stamm aus der Liste (Betonreste, Ziegelbruch; nicht Toneisenstein)."""
    return any(w.startswith(_ANTHROPOGEN) for w in re.findall(r"[a-zäöüß]+", _schluessel(s)))


_NEBEN_SCHLUESSEL = {"Kies": "g", "Sand": "s", "Schluff": "u", "Ton": "t", "Steine": "x", "Bloecke": "y", "Torf": "h",
                     "Mudde": "o"}


def _abschliessen(d: Deutung, soil_class: str | None) -> Deutung:
    """Benennung, Kurzzeichen, Farbe und Abgleich mit der Extraktion."""
    neben = [a.text for a in d.nebenanteile]
    neben_kurz = [a.din4023 for a in d.nebenanteile]
    if d.klasse:
        if d.material:
            mat = ", ".join([d.material["name"]] + neben)
            d.benennung = f"{d.hauptanteil} ({mat})"
            din_m, _ = _haupt_kurz(d.material["klasse"], d.material["fraktion"])
            kopf = KLASSEN[d.klasse].get("din4023", d.hauptanteil)
            d.din4023 = f"{kopf} ({', '.join(filter(None, [din_m] + neben_kurz))})"
            d.iso14688 = KLASSEN[d.klasse].get("iso14688", "")
        else:
            d.benennung = ", ".join([d.hauptanteil] + neben)
            din, iso = _haupt_kurz(d.klasse, d.fraktion)
            d.din4023 = ", ".join(filter(None, [din or d.hauptanteil] + neben_kurz))
            vorne = next((ISO_NEBEN[a.klasse] for a in d.nebenanteile
                          if a.stufe in ("stark", "sehr stark", "") and a.klasse in ISO_NEBEN), "")
            d.iso14688 = ((vorne if iso[:1] not in "fmc" or iso in ("Cl", "Co") else "") + iso) if iso else ""
        if d.bodengruppe:
            gk = _GRUPPEN[d.bodengruppe.strip("[]")]["klasse"]
            pruef = d.material["klasse"] if d.material else d.klasse
            if gk and pruef in _BEREICH and _BEREICH.get(gk) != _BEREICH[pruef]:
                d.hinweise.append(f"Bodengruppe {d.bodengruppe} ({_BEREICH[gk]}) passt nicht zum Hauptanteil {pruef} "
                                  f"({_BEREICH[pruef]})")
    if d.anthropogen and d.klasse and KLASSEN.get(d.klasse, {}).get("art") not in ("anthropogen",):
        d.hinweise.append(f"Fremdstoffe genannt ({', '.join(d.anthropogen)}): Auffüllung prüfen")
    fi = farbinfo(d.klasse, d.fraktion)
    d.farbe, d.farbname = fi["hex"], fi["name"]
    extr = None if soil_class in (None, "", UNKLASSIFIZIERT) else soil_class
    if extr and d.klasse and extr != d.klasse:
        d.hinweise.append(f"Extraktion: {extr}, nach Norm gelesen: {d.klasse}")
    return d


def vorschlag(ly: dict) -> dict | None:
    """Vorschlag fuer eine unklassifizierte Schicht (nur anzeigen, der Nutzer uebernimmt ihn)."""
    if ly.get("soil_class") not in (None, "", UNKLASSIFIZIERT):
        return None
    d = deuten(ly.get("description_raw"), None)
    if not d.klasse:
        return None
    return {"klasse": d.klasse, "benennung": d.benennung, "din4023": d.din4023, "sicher": d.sicher,
            "hinweise": d.hinweise}


def ifc_eigenschaften(d: Deutung) -> dict:
    """CPset_Bodenansprache: Rohtext und Deutung nach Norm (leere Werte fallen beim Schreiben weg)."""
    return {
        "Beschreibung": d.text,
        "Benennung": d.benennung, "Hauptanteil": d.hauptanteil,
        "Material": d.material["name"] if d.material else None,
        "Nebenanteile": "; ".join(a.text for a in d.nebenanteile),
        "Kurzzeichen_DIN4023": d.din4023, "Kurzzeichen_ISO14688": d.iso14688,
        "Bodengruppe_DIN18196": d.bodengruppe, "Bodengruppe_Benennung": d.bodengruppe_name,
        "Konsistenz": d.konsistenz, "Lagerungsdichte": d.lagerung, "Kalkgehalt": d.kalk, "Feuchte": d.feuchte,
        "Bodenfarbe": d.bodenfarbe,
        "Felsart": (d.fels or {}).get("art"), "Verwitterung": (d.fels or {}).get("verwitterung"),
        "Beimengungen": "; ".join(d.beimengungen), "Anthropogen": "; ".join(d.anthropogen),
        "Farbe_DIN4023": d.farbe, "Farbname_DIN4023": d.farbname,
        "Deutung_eindeutig": d.sicher,
        "Hinweise_Deutung": "; ".join(d.hinweise),
        "Normen": NORMSTAND,
    }
