"""IFC4X3-Ausgabe: Bohrsaeulen (N1: IfcBorehole ⊃ IfcGeotechnicalStratum) und Schichtmodell
(N3: IfcGeomodel ⊃ IfcGeotechnicalStratum als geschlossene Koerper).

Koordinaten lokal zum Ursprung (gerundeter Schwerpunkt), Georeferenz ueber IfcMapConversion.
That Open: die Geotechnik-Klassen muessen in importer.classes.elements stehen (Architektur 8.2).
Description unterscheidet die beiden Ebenen fuer den Viewer: "Modelleinheit" / "Bohrsaeule".
"""
from __future__ import annotations

import numpy as np
import ifcopenshell.api as api
import ifcopenshell.api.aggregate  # noqa: F401
import ifcopenshell.api.context  # noqa: F401
import ifcopenshell.api.geometry  # noqa: F401
import ifcopenshell.api.georeference  # noqa: F401
import ifcopenshell.api.project  # noqa: F401
import ifcopenshell.api.pset  # noqa: F401
import ifcopenshell.api.root  # noqa: F401
import ifcopenshell.api.spatial  # noqa: F401
import ifcopenshell.api.style  # noqa: F401
import ifcopenshell.api.unit  # noqa: F401

from .koerper import dreiecke_aus
from .normen import KLASSEN, UNKLASSIFIZIERT, bekannt, deuten, farbinfo, ifc_eigenschaften


def rgb_aus(hexwert: str) -> tuple[float, float, float]:
    return tuple(int(hexwert[i:i + 2], 16) / 255 for i in (1, 3, 5))


# Farben der Bodenarten nach DIN 4023 (Normen-Datenbank normen.json; "" = unklassifiziert)
FARBEN = {k: rgb_aus(e["farbe"]) for k, e in KLASSEN.items() if k != UNKLASSIFIZIERT}
FARBEN[""] = rgb_aus(KLASSEN[UNKLASSIFIZIERT]["farbe"])
# Wiederholungen derselben Bodenart unterscheidbar: Anteil Weiss (+) bzw. Schwarz (-) je Nummer
ABTOENUNG = (0.0, 0.5, -0.35, 0.75, -0.55)
# Lange Texte als IfcText (IfcLabel ist fuer kurze Bezeichnungen gedacht, 255 Zeichen)
TEXTE = ("Beschreibung", "Beschreibungen", "Benennungen", "Hinweise", "Hinweise_Deutung", "Quelle")


def farbschluessel(klasse: str | None) -> str:
    """Klasse mit eigener Farbe (auch 'Fels (Tonstein)'), sonst '' (unklassifiziert)."""
    return klasse if bekannt(klasse) else ""


def farbe(klasse: str | None, nummer: int = 1) -> tuple[float, float, float]:
    rgb = np.array(rgb_aus(farbinfo(farbschluessel(klasse) or None)["hex"]))
    t = ABTOENUNG[(nummer - 1) % len(ABTOENUNG)]
    rgb = rgb + (1.0 - rgb) * t if t >= 0 else rgb * (1.0 + t)
    return tuple(float(c) for c in np.clip(rgb, 0.0, 1.0))


def hexfarbe(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(c * 255):02x}" for c in rgb)


def prisma(cx: float, cy: float, z_oben: float, z_unten: float, r: float = 0.5, n: int = 12):
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in ang]
    knoten = [(float(x), float(y), float(z_oben)) for x, y in ring] + \
             [(float(x), float(y), float(z_unten)) for x, y in ring]
    flaechen = [list(range(n)), list(range(n, 2 * n))[::-1]]      # nach aussen orientiert
    for i in range(n):
        j = (i + 1) % n
        flaechen.append([i, n + i, n + j, j])
    return knoten, flaechen


class IfcAusgabe:
    def __init__(self, projekt: str, epsg: int | None, ursprung: tuple[float, float]):
        f = self.f = api.project.create_file(version="IFC4X3")
        self.projekt = api.root.create_entity(f, ifc_class="IfcProject", name=projekt)
        # Meter ausdruecklich: assign_unit ohne Angaben setzt Millimeter, alle Koordinaten sind aber in m
        # (sonst zeigt jeder Viewer das Modell 1000-fach verkleinert und die Georeferenz stimmt nicht).
        api.unit.assign_unit(f, units=[api.unit.add_si_unit(f, unit_type=t)
                                       for t in ("LENGTHUNIT", "AREAUNIT", "VOLUMEUNIT")])
        model3d = api.context.add_context(f, context_type="Model")
        self.body = api.context.add_context(f, context_type="Model", context_identifier="Body",
                                            target_view="MODEL_VIEW", parent=model3d)
        self.ursprung = ursprung
        if epsg:
            api.georeference.add_georeferencing(f)
            api.georeference.edit_georeferencing(
                f, projected_crs={"Name": f"EPSG:{epsg}"},
                coordinate_operation={"Eastings": float(ursprung[0]), "Northings": float(ursprung[1]),
                                      "OrthogonalHeight": 0.0})
        self.site = api.root.create_entity(f, ifc_class="IfcSite", name="Baufeld")
        api.aggregate.assign_object(f, products=[self.site], relating_object=self.projekt)
        self._stile: dict[tuple, object] = {}

    def _stil(self, rgb: tuple[float, float, float], name: str):
        schluessel = tuple(round(c, 4) for c in rgb)
        if schluessel not in self._stile:
            st = api.style.add_style(self.f, name=name)
            api.style.add_surface_style(self.f, style=st, ifc_class="IfcSurfaceStyleShading", attributes={
                "SurfaceColour": {"Name": None, "Red": rgb[0], "Green": rgb[1], "Blue": rgb[2]}})
            self._stile[schluessel] = st
        return self._stile[schluessel]

    def _geometrie(self, produkt, knoten, flaechen, rgb, stilname, geschlossen=False):
        """IfcTriangulatedFaceSet: zwei Entitaeten je Koerper statt einer je Flaeche (Trassen: 80k Flaechen)."""
        dreiecke = dreiecke_aus(flaechen) + 1                        # IFC zaehlt ab 1
        punkte = self.f.create_entity("IfcCartesianPointList3D",
                                      CoordList=[tuple(map(float, k)) for k in np.asarray(knoten, dtype=float)])
        flaeche = self.f.create_entity("IfcTriangulatedFaceSet", Coordinates=punkte, Closed=bool(geschlossen),
                                       CoordIndex=[tuple(map(int, d)) for d in dreiecke])
        rep = self.f.create_entity("IfcShapeRepresentation", ContextOfItems=self.body,
                                   RepresentationIdentifier="Body", RepresentationType="Tessellation", Items=[flaeche])
        api.style.assign_representation_styles(self.f, shape_representation=rep,
                                               styles=[self._stil(rgb, stilname)])
        api.geometry.assign_representation(self.f, product=produkt, representation=rep)
        api.geometry.edit_object_placement(self.f, product=produkt)

    def _pset(self, produkt, name: str, werte: dict):
        werte = {k: (self.f.create_entity("IfcText", v) if isinstance(v, str) and (k in TEXTE or len(v) > 255) else v)
                 for k, v in werte.items() if v is not None and v != ""}
        if werte:                                       # leere Psets sind ungueltiges IFC
            ps = api.pset.add_pset(self.f, product=produkt, name=name)
            api.pset.edit_pset(self.f, pset=ps, properties=werte)

    def bohrung(self, dokument: dict, b: dict, xy: tuple[float, float], lage: str, hoehe: str | None = None,
                durchmesser: float = 1.0, durchmesser_quelle: str = "Standard (Darstellung)"):
        """IfcBorehole mit Schichten als Prismen (N1); xy lokal. Durchmesser der Saeule in m (Darstellung)."""
        f = self.f
        ent = api.root.create_entity(f, ifc_class="IfcBorehole", name=b["code"])
        api.spatial.assign_container(f, products=[ent], relating_structure=self.site)
        api.geometry.edit_object_placement(f, product=ent)
        if b.get("groundwater"):
            self._pset(ent, "Pset_BoreholeCommon", {"GroundwaterDepth": float(b["groundwater"][0]["depth"])})
        prov = (b.get("provenance") or [{}])[0]
        self._pset(ent, "CPset_Herkunft", {
            "Dokument": dokument["file"], "SHA256": dokument.get("sha256"), "Parser": dokument.get("parser_version"),
            "Seite": int(prov["page"]) + 1 if prov.get("page") is not None else None, "Methode": prov.get("method"),
            "Lage": lage, "Hoehe": hoehe or ("m NHN" if b.get("gok_nhn") is not None else "relativ (GOK unbekannt)"),
            "Grundwasserstatus": b.get("groundwater_status"),
            "Abgleich_SV": (b.get("checks") or {}).get("schichtenverzeichnis"),
            "Labelbestaetigung": float((b.get("checks") or {}).get("label_support") or 0.0),
            # Pruefung durch den Nutzer (App): nur wenn der Schluessel gesetzt ist
            "Geprueft": bool(b["geprueft"]) if "geprueft" in b else None})
        self._pset(ent, "CPset_Darstellung", {"Durchmesser_m": round(float(durchmesser), 3),
                                               "Durchmesser_Quelle": durchmesser_quelle})
        z0 = b["gok_nhn"] if b.get("gok_nhn") is not None else 0.0
        strata = []
        for ly in b["layers"]:
            s = api.root.create_entity(
                f, ifc_class="IfcGeotechnicalStratum", predefined_type="SOLID",
                name=f"{b['code']} {ly['top_depth']:.2f}-{ly['bottom_depth']:.2f} {ly['soil_class'] or '?'}")
            s.Description = "Bohrsaeule"
            kn, fl = prisma(xy[0], xy[1], z0 - ly["top_depth"], z0 - ly["bottom_depth"], r=float(durchmesser) / 2)
            self._geometrie(s, kn, fl, farbe(ly["soil_class"]), farbschluessel(ly["soil_class"]) or "unbekannt",
                            geschlossen=True)
            self._pset(s, "Pset_GeotechnicalStratumCommon", {"Status": "EXISTING"})
            pv = (ly.get("provenance") or [{}])[0]
            self._pset(s, "CPset_Schichtenverzeichnis", {
                "Bodenart": ly["soil_class"] or "unbekannt", "Beschreibung": ly.get("description_raw"),
                "Tiefe_OK_m": float(ly["top_depth"]), "Tiefe_UK_m": float(ly["bottom_depth"]),
                "Konfidenz": float(ly.get("confidence") or 0.0), "Label_bestaetigt": bool(ly.get("label_confirmed")),
                "Quelle": f"{dokument['file']} S.{int(pv.get('page') or 0) + 1} {pv.get('method')} bbox {pv.get('bbox')}",
                "Geprueft": bool(ly["geprueft"]) if "geprueft" in ly else None,
                "Korrigiert": bool(ly["korrigiert"]) if ly.get("korrigiert") else None,
                "Konfidenz_Extraktion": float(ly["konfidenz_extraktion"]) if ly.get("konfidenz_extraktion") is not None else None,
                "Hinweise": "; ".join(ly.get("issues") or [])})
            # Deutung der Beschreibung nach DIN 4023 / DIN EN ISO 14688-1 / DIN 18196 (normen.py)
            ansprache = ifc_eigenschaften(deuten(ly.get("description_raw"), ly.get("soil_class")))
            ansprache.pop("Beschreibung")                 # steht schon im CPset_Schichtenverzeichnis
            self._pset(s, "CPset_Bodenansprache", ansprache)
            strata.append(s)
        if strata:
            api.aggregate.assign_object(f, products=strata, relating_object=ent)
        return ent

    def geomodell(self, name: str, einheiten: list[dict], eigenschaften: dict):
        """IfcGeomodel mit einem geschlossenen Koerper je Einheit.

        einheiten: [{"name", "knoten", "flaechen", "rgb", "beschreibung", "eigenschaften"}]
        """
        f = self.f
        gm = api.root.create_entity(f, ifc_class="IfcGeomodel", name=name)
        api.spatial.assign_container(f, products=[gm], relating_structure=self.site)
        api.geometry.edit_object_placement(f, product=gm)
        self._pset(gm, "CPset_Baugrundmodell", eigenschaften)
        koerper = []
        for e in einheiten:
            s = api.root.create_entity(f, ifc_class="IfcGeotechnicalStratum", name=e["name"], predefined_type="SOLID")
            s.Description = e.get("beschreibung") or "Modelleinheit"
            self._geometrie(s, e["knoten"], e["flaechen"], e["rgb"], e["name"], geschlossen=e.get("geschlossen", True))
            self._pset(s, "Pset_GeotechnicalStratumCommon", {"Status": "EXISTING"})
            self._pset(s, "CPset_Modelleinheit", e["eigenschaften"])
            koerper.append(s)
        if koerper:
            api.aggregate.assign_object(f, products=koerper, relating_object=gm)
        return gm

    def schreiben(self, pfad) -> None:
        self.f.write(str(pfad))
