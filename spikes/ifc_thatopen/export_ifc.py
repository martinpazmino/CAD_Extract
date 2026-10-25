"""Kanonisches Extraktions-JSON (prototyp_v4.to_canonical) -> IFC4X3 (Stufe N1: Bohrsaeulen).

    python export_ifc.py <ausgabe.ifc> <extraktion1.json> [<extraktion2.json> ...]

Jede Bohrung wird IfcBorehole, jede Schicht IfcGeotechnicalStratum (Prisma) mit Herkunft und
Konfidenz in CPset_Schichtenverzeichnis. Mit Koordinaten: georeferenziert (IfcMapConversion,
EPSG aus dem JSON); ohne: Platzhalterposition, ausdruecklich als solche markiert.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

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

COLORS = {"Mutterboden": (0.45, 0.3, 0.15), "Auffuellung": (0.6, 0.6, 0.6), "Sand": (1.0, 0.8, 0.3),
          "Kies": (0.95, 0.6, 0.2), "Schluff": (0.7, 0.75, 0.4), "Ton": (0.55, 0.75, 0.9),
          "Torf": (0.35, 0.25, 0.15), "Mudde": (0.3, 0.35, 0.3), "Steine": (0.5, 0.45, 0.4),
          "Beton": (0.8, 0.8, 0.8), "Schwarzdecke": (0.15, 0.15, 0.15), "Fels": (0.6, 0.35, 0.35),
          "": (0.9, 0.9, 0.9)}


def prism(cx, cy, z_top, z_bot, r=0.5, n=12):
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in ang]
    verts = [(float(x), float(y), float(z_top)) for x, y in ring] + [(float(x), float(y), float(z_bot)) for x, y in ring]
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    return verts, faces


def color_key(soil: str | None) -> str:
    soil = soil or ""
    return "Fels" if soil.startswith("Fels") else (soil if soil in COLORS else "")


def build(out: Path, docs: list[dict]) -> dict:
    f = api.project.create_file(version="IFC4X3")
    project = api.root.create_entity(f, ifc_class="IfcProject", name="Baugrundmodell aus Gutachten")
    api.unit.assign_unit(f)
    model3d = api.context.add_context(f, context_type="Model")
    body = api.context.add_context(f, context_type="Model", context_identifier="Body",
                                   target_view="MODEL_VIEW", parent=model3d)
    bhs = [(d["document"], b) for d in docs for b in d["boreholes"]]
    placed = [b for _, b in bhs if b.get("x") is not None and b.get("crs_epsg")]
    origin = (0.0, 0.0)
    if placed:
        epsg = placed[0]["crs_epsg"]
        origin = (round(np.mean([b["x"] for b in placed]), -1), round(np.mean([b["y"] for b in placed]), -1))
        api.georeference.add_georeferencing(f)
        api.georeference.edit_georeferencing(
            f, projected_crs={"Name": f"EPSG:{epsg}"},
            coordinate_operation={"Eastings": origin[0], "Northings": origin[1], "OrthogonalHeight": 0.0})
    site = api.root.create_entity(f, ifc_class="IfcSite", name="Baufeld")
    api.aggregate.assign_object(f, products=[site], relating_object=project)
    styles = {}
    for k, rgb in COLORS.items():
        st = api.style.add_style(f, name=k or "unbekannt")
        api.style.add_surface_style(f, style=st, ifc_class="IfcSurfaceStyleShading",
                                    attributes={"SurfaceColour": {"Name": None, "Red": rgb[0], "Green": rgb[1], "Blue": rgb[2]}})
        styles[k] = st
    stats = {"boreholes": 0, "strata": 0, "georeferenced": 0, "placeholder": 0}
    for i, (doc, b) in enumerate(bhs):
        geo = b.get("x") is not None and b.get("crs_epsg")
        x, y = (b["x"] - origin[0], b["y"] - origin[1]) if geo else (-50.0 - 15.0 * i, -50.0)
        z0 = b["gok_nhn"] if b.get("gok_nhn") is not None else 0.0
        ent = api.root.create_entity(f, ifc_class="IfcBorehole", name=b["code"])
        api.spatial.assign_container(f, products=[ent], relating_structure=site)
        api.geometry.edit_object_placement(f, product=ent)
        if b["groundwater"]:                             # leere Psets sind ungueltiges IFC
            ps = api.pset.add_pset(f, product=ent, name="Pset_BoreholeCommon")
            api.pset.edit_pset(f, pset=ps, properties={"GroundwaterDepth": float(b["groundwater"][0]["depth"])})
        cps = api.pset.add_pset(f, product=ent, name="CPset_Herkunft")
        prov = b["provenance"][0]
        api.pset.edit_pset(f, pset=cps, properties={
            "Dokument": doc["file"], "SHA256": doc["sha256"], "Parser": doc["parser_version"],
            "Seite": int(prov["page"]) + 1, "Methode": prov["method"],
            "Lage": "georeferenziert" if geo else "unbekannt (Platzhalter)",
            "Hoehe": "m NHN" if b.get("gok_nhn") is not None else "relativ (GOK unbekannt)",
            "Grundwasserstatus": b.get("groundwater_status") or "",
            "Abgleich_SV": b["checks"].get("schichtenverzeichnis") or "",
            "Labelbestaetigung": float(b["checks"]["label_support"])})
        strata = []
        for ly in b["layers"]:
            key = color_key(ly["soil_class"])
            s = api.root.create_entity(f, ifc_class="IfcGeotechnicalStratum",
                                       name=f"{b['code']} {ly['top_depth']:.2f}-{ly['bottom_depth']:.2f} {ly['soil_class'] or '?'}",
                                       predefined_type="SOLID")
            v, fc = prism(x, y, z0 - ly["top_depth"], z0 - ly["bottom_depth"])
            rep = api.geometry.add_mesh_representation(f, context=body, vertices=[v], faces=[fc])
            api.style.assign_representation_styles(f, shape_representation=rep, styles=[styles[key]])
            api.geometry.assign_representation(f, product=s, representation=rep)
            api.geometry.edit_object_placement(f, product=s)
            p2 = api.pset.add_pset(f, product=s, name="Pset_GeotechnicalStratumCommon")
            api.pset.edit_pset(f, pset=p2, properties={"Status": "EXISTING"})
            p3 = api.pset.add_pset(f, product=s, name="CPset_Schichtenverzeichnis")
            pv = ly["provenance"][0]
            api.pset.edit_pset(f, pset=p3, properties={
                "Bodenart": ly["soil_class"] or "", "Beschreibung": ly["description_raw"] or "",
                "Tiefe_OK_m": float(ly["top_depth"]), "Tiefe_UK_m": float(ly["bottom_depth"]),
                "Konfidenz": float(ly["confidence"]), "Label_bestaetigt": bool(ly["label_confirmed"]),
                "Quelle": f"{doc['file']} S.{int(pv['page']) + 1} {pv['method']} bbox {pv.get('bbox')}",
                "Hinweise": "; ".join(ly["issues"])})
            strata.append(s)
        if strata:
            api.aggregate.assign_object(f, products=strata, relating_object=ent)
        stats["boreholes"] += 1
        stats["strata"] += len(strata)
        stats["georeferenced" if geo else "placeholder"] += 1
    f.write(str(out))
    return stats


if __name__ == "__main__":
    out = Path(sys.argv[1])
    docs = [json.loads(Path(p).read_text()) for p in sys.argv[2:]]
    print(build(out, docs))
