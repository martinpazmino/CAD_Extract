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

FARBEN = {"Mutterboden": (0.45, 0.3, 0.15), "Auffuellung": (0.6, 0.6, 0.6), "Sand": (1.0, 0.8, 0.3),
          "Kies": (0.95, 0.6, 0.2), "Schluff": (0.7, 0.75, 0.4), "Ton": (0.55, 0.75, 0.9),
          "Torf": (0.35, 0.25, 0.15), "Mudde": (0.3, 0.35, 0.3), "Steine": (0.5, 0.45, 0.4),
          "Beton": (0.8, 0.8, 0.8), "Schwarzdecke": (0.15, 0.15, 0.15), "Fels": (0.6, 0.35, 0.35),
          "Geschiebemergel": (0.55, 0.7, 0.45), "": (0.9, 0.9, 0.9)}
# Wiederholungen derselben Bodenart unterscheidbar: Anteil Weiss (+) bzw. Schwarz (-) je Nummer
ABTOENUNG = (0.0, 0.5, -0.35, 0.75, -0.55)


def farbschluessel(klasse: str | None) -> str:
    klasse = klasse or ""
    return "Fels" if klasse.startswith("Fels") else (klasse if klasse in FARBEN else "")


def farbe(klasse: str | None, nummer: int = 1) -> tuple[float, float, float]:
    rgb = np.array(FARBEN[farbschluessel(klasse)])
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
        api.unit.assign_unit(f)
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
        rep = api.geometry.add_mesh_representation(self.f, context=self.body, vertices=[knoten], faces=[flaechen])
        if geschlossen:
            for item in rep.Items:
                item.Closed = True
        api.style.assign_representation_styles(self.f, shape_representation=rep,
                                               styles=[self._stil(rgb, stilname)])
        api.geometry.assign_representation(self.f, product=produkt, representation=rep)
        api.geometry.edit_object_placement(self.f, product=produkt)

    def _pset(self, produkt, name: str, werte: dict):
        werte = {k: v for k, v in werte.items() if v is not None and v != ""}
        if werte:                                       # leere Psets sind ungueltiges IFC
            ps = api.pset.add_pset(self.f, product=produkt, name=name)
            api.pset.edit_pset(self.f, pset=ps, properties=werte)

    def bohrung(self, dokument: dict, b: dict, xy: tuple[float, float], lage: str, hoehe: str | None = None):
        """IfcBorehole mit Schichten als Prismen (N1); xy lokal."""
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
            "Labelbestaetigung": float((b.get("checks") or {}).get("label_support") or 0.0)})
        z0 = b["gok_nhn"] if b.get("gok_nhn") is not None else 0.0
        strata = []
        for ly in b["layers"]:
            s = api.root.create_entity(
                f, ifc_class="IfcGeotechnicalStratum", predefined_type="SOLID",
                name=f"{b['code']} {ly['top_depth']:.2f}-{ly['bottom_depth']:.2f} {ly['soil_class'] or '?'}")
            s.Description = "Bohrsaeule"
            kn, fl = prisma(xy[0], xy[1], z0 - ly["top_depth"], z0 - ly["bottom_depth"])
            self._geometrie(s, kn, fl, farbe(ly["soil_class"]), farbschluessel(ly["soil_class"]) or "unbekannt",
                            geschlossen=True)
            self._pset(s, "Pset_GeotechnicalStratumCommon", {"Status": "EXISTING"})
            pv = (ly.get("provenance") or [{}])[0]
            self._pset(s, "CPset_Schichtenverzeichnis", {
                "Bodenart": ly["soil_class"] or "unbekannt", "Beschreibung": ly.get("description_raw"),
                "Tiefe_OK_m": float(ly["top_depth"]), "Tiefe_UK_m": float(ly["bottom_depth"]),
                "Konfidenz": float(ly.get("confidence") or 0.0), "Label_bestaetigt": bool(ly.get("label_confirmed")),
                "Quelle": f"{dokument['file']} S.{int(pv.get('page') or 0) + 1} {pv.get('method')} bbox {pv.get('bbox')}",
                "Hinweise": "; ".join(ly.get("issues") or [])})
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
