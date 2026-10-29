"""Spike: Baugrundmodell (synthetisch) -> IFC4X3 mit IfcBorehole / IfcGeomodel / IfcGeotechnicalStratum.

Ziel: pruefen, ob That Open (web-ifc + @thatopen/fragments IfcImporter) diese
Entitaeten mit Geometrie importiert.  Ergebnis + Ablauf: docs/ARCHITECTURE_BAUGRUNDMODELL.md (Kap. 8).

    pip install ifcopenshell numpy
    python baugrund_ifc_spike.py baugrund_spike.ifc
"""
import sys

import numpy as np
import ifcopenshell.api as api
# ifcopenshell.api-Untermodule muessen explizit importiert werden
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

OUT = sys.argv[1] if len(sys.argv) > 1 else "baugrund_spike.ifc"

# --- synthetische Bohrungen (lokale Koordinaten in m, NHN in m) -------------
BOREHOLES = [
    {"id": "B 1/19", "x": 0.0,   "y": 0.0,  "gok": 6.2, "layers": [("Auffuellung", 0.0, 1.5), ("Sand", 1.5, 7.0), ("Geschiebemergel", 7.0, 14.0), ("Lauenburger Ton", 14.0, 25.0)]},
    {"id": "B 2/19", "x": 60.0,  "y": 10.0, "gok": 5.8, "layers": [("Auffuellung", 0.0, 1.0), ("Sand", 1.0, 9.5), ("Geschiebemergel", 9.5, 12.0), ("Lauenburger Ton", 12.0, 25.0)]},
    {"id": "B 3/19", "x": 120.0, "y": -5.0, "gok": 5.1, "layers": [("Auffuellung", 0.0, 2.0), ("Sand", 2.0, 6.0), ("Geschiebemergel", 6.0, 16.0), ("Lauenburger Ton", 16.0, 25.0)]},
]
UNITS = ["Auffuellung", "Sand", "Geschiebemergel", "Lauenburger Ton"]   # stratigraphische Reihenfolge
COLORS = {"Auffuellung": (0.6, 0.6, 0.6), "Sand": (1.0, 0.75, 0.0),
          "Geschiebemergel": (0.55, 0.75, 0.45), "Lauenburger Ton": (0.53, 0.82, 0.9)}

f = api.project.create_file(version="IFC4X3")
project = api.root.create_entity(f, ifc_class="IfcProject", name="Baugrundmodell Spike")
api.unit.assign_unit(f)
model3d = api.context.add_context(f, context_type="Model")
body = api.context.add_context(f, context_type="Model", context_identifier="Body",
                               target_view="MODEL_VIEW", parent=model3d)
# Georeferenzierung: ETRS89 / UTM 32N, lokaler Ursprung
api.georeference.add_georeferencing(f)
api.georeference.edit_georeferencing(
    f, projected_crs={"Name": "EPSG:25832"},
    coordinate_operation={"Eastings": 565000.0, "Northings": 5933000.0, "OrthogonalHeight": 0.0})

site = api.root.create_entity(f, ifc_class="IfcSite", name="Baufeld")
api.aggregate.assign_object(f, products=[site], relating_object=project)

styles = {}
for u, rgb in COLORS.items():
    st = api.style.add_style(f, name=u)
    api.style.add_surface_style(f, style=st, ifc_class="IfcSurfaceStyleShading",
                                attributes={"SurfaceColour": {"Name": None, "Red": rgb[0], "Green": rgb[1], "Blue": rgb[2]}})
    styles[u] = st


def prism(cx, cy, z_top, z_bot, r=0.6, n=12):
    """Geschlossener n-eckiger Zylinder (Bohrsaeulen-Abschnitt)."""
    ang = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = [(cx + r * np.cos(a), cy + r * np.sin(a)) for a in ang]
    verts = [(x, y, z_top) for x, y in ring] + [(x, y, z_bot) for x, y in ring]
    faces = [list(range(n))[::-1], list(range(n, 2 * n))]
    for i in range(n):
        j = (i + 1) % n
        faces.append([i, j, n + j, n + i])
    return verts, faces


def add_mesh(product, verts, faces, unit):
    rep = api.geometry.add_mesh_representation(f, context=body, vertices=[verts], faces=[faces])
    api.style.assign_representation_styles(f, shape_representation=rep, styles=[styles[unit]])
    api.geometry.assign_representation(f, product=product, representation=rep)
    api.geometry.edit_object_placement(f, product=product)


# --- 1) Faktendaten: IfcBorehole mit Strata als Saeulen --------------------
for bh in BOREHOLES:
    b = api.root.create_entity(f, ifc_class="IfcBorehole", name=bh["id"])
    api.spatial.assign_container(f, products=[b], relating_structure=site)
    api.geometry.edit_object_placement(f, product=b)
    strata = []
    for unit, top, bot in bh["layers"]:
        s = api.root.create_entity(f, ifc_class="IfcGeotechnicalStratum", name=f"{bh['id']} {unit}",
                                   predefined_type="SOLID")
        v, fc = prism(bh["x"], bh["y"], bh["gok"] - top, bh["gok"] - bot)
        add_mesh(s, v, fc, unit)
        ps = api.pset.add_pset(f, product=s, name="Pset_GeotechnicalStratumCommon")
        api.pset.edit_pset(f, pset=ps, properties={"Status": "EXISTING"})
        cps = api.pset.add_pset(f, product=s, name="CPset_Schichtenverzeichnis")
        api.pset.edit_pset(f, pset=cps, properties={"Bodenart": unit, "Tiefe_OK_m": top, "Tiefe_UK_m": bot,
                                                     "Quelle": "Bohrprofil.pdf S.1 (bbox ...)"})
        strata.append(s)
    api.aggregate.assign_object(f, products=strata, relating_object=b)

# --- 2) Interpretation: IfcGeomodel mit Schichtkoerpern (Layer-Cake) -------
xs = np.array([b["x"] for b in BOREHOLES]); ys = np.array([b["y"] for b in BOREHOLES])


def idw(gx, gy, vals, p=2.0):
    d = np.hypot(gx[..., None] - xs, gy[..., None] - ys) + 1e-6
    w = 1.0 / d ** p
    return (w * vals).sum(-1) / w.sum(-1)


gx, gy = np.meshgrid(np.linspace(-20, 140, 17), np.linspace(-30, 30, 7))
# Grenzflaechen: GOK, dann Unterkante jeder Einheit
surfaces = [idw(gx, gy, np.array([b["gok"] for b in BOREHOLES]))]
for k, unit in enumerate(UNITS):
    z = idw(gx, gy, np.array([b["gok"] - [l for l in b["layers"] if l[0] == unit][0][2] for b in BOREHOLES]))
    surfaces.append(np.minimum(z, surfaces[-1]))          # Stratigraphie erzwingen: nie ueber Oberkante


def volume_between(top, bot):
    ny, nx = top.shape
    vid = lambda i, j, layer: layer * nx * ny + i * nx + j
    verts = [(gx[i, j], gy[i, j], top[i, j]) for i in range(ny) for j in range(nx)] + \
            [(gx[i, j], gy[i, j], bot[i, j]) for i in range(ny) for j in range(nx)]
    faces = []
    for i in range(ny - 1):
        for j in range(nx - 1):
            a, b_, c, d = vid(i, j, 0), vid(i, j + 1, 0), vid(i + 1, j + 1, 0), vid(i + 1, j, 0)
            faces += [[a, b_, c], [a, c, d]]
            a, b_, c, d = vid(i, j, 1), vid(i, j + 1, 1), vid(i + 1, j + 1, 1), vid(i + 1, j, 1)
            faces += [[a, c, b_], [a, d, c]]
    border = [(0, j) for j in range(nx)] + [(i, nx - 1) for i in range(1, ny)] + \
             [(ny - 1, j) for j in range(nx - 2, -1, -1)] + [(i, 0) for i in range(ny - 2, 0, -1)]
    for k in range(len(border)):
        (i0, j0), (i1, j1) = border[k], border[(k + 1) % len(border)]
        faces.append([vid(i0, j0, 0), vid(i0, j0, 1), vid(i1, j1, 1), vid(i1, j1, 0)])
    return verts, faces


geomodel = api.root.create_entity(f, ifc_class="IfcGeomodel", name="Baugrundmodell v1 (Layer-Cake, IDW)")
api.spatial.assign_container(f, products=[geomodel], relating_structure=site)
api.geometry.edit_object_placement(f, product=geomodel)
bodies = []
for k, unit in enumerate(UNITS):
    s = api.root.create_entity(f, ifc_class="IfcGeotechnicalStratum", name=unit, predefined_type="SOLID")
    v, fc = volume_between(surfaces[k], surfaces[k + 1])
    add_mesh(s, v, fc, unit)
    bodies.append(s)
api.aggregate.assign_object(f, products=bodies, relating_object=geomodel)

f.write(OUT)
print("written", OUT, "entities:", {c: len(f.by_type(c)) for c in
      ["IfcBorehole", "IfcGeomodel", "IfcGeotechnicalStratum", "IfcPolygonalFaceSet", "IfcMapConversion"]})
