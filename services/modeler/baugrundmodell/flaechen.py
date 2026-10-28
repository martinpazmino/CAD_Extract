"""Layer-Cake Schritt 3-4 und 6: Modellgebiet, Dreiecksnetz, Grenzflaechen, Verschnitt, Unsicherheit.

Alle Grenzflaechen teilen dasselbe Dreiecksnetz; die Bohrungen sind Knoten des Netzes, damit das
Modell ihre Kontakte exakt trifft (beide Interpolatoren sind exakt an den Stuetzstellen).
"""
from __future__ import annotations

import math
from collections import defaultdict

import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.spatial import ConvexHull, Delaunay, cKDTree

from .einheiten import Bohrung, Kontakt

ZENSUR_MARGE = 0.5        # m: endet eine Bohrung in einer Einheit, reicht diese mindestens so weit tiefer
FREI_RAND = 0.1           # m: freie Grenze (Linse) nicht naeher an Ober-/Unterkante des geteilten Abschnitts
MIN_MAECHTIGKEIT = 0.005  # m: duenner gilt eine Einheit als ausgeduennt (Tiefen sind auf cm angegeben)
ZENSUR_RUNDEN = 12
PRAESENZ_SCHWELLE = 0.5   # Einheit endet, wo der Anteil "vorhanden" der Nachbarbohrungen (IDW) darunter faellt


def gebiet(xy: np.ndarray, puffer: float, n_kreis: int = 24) -> np.ndarray:
    """Konvexe Huelle der Bohrungen + Puffer (auch fuer eine Bohrung oder eine Bohrlinie), gegen den Uhrzeigersinn."""
    w = np.linspace(0, 2 * np.pi, n_kreis, endpoint=False)
    kreis = np.c_[np.cos(w), np.sin(w)] * puffer
    pts = (xy[:, None, :] + kreis[None, :, :]).reshape(-1, 2)
    return pts[ConvexHull(pts).vertices]                  # scipy: 2D-Huelle gegen den Uhrzeigersinn


def netz(polygon: np.ndarray, xy_bohrungen: np.ndarray, raster: float
         ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Dreiecksnetz des Gebiets: Bohrungen (zuerst, Index = Bohrungsindex), verdichteter Rand, Raster innen.

    Rueckgabe: Punkte (N,2), Dreiecke (T,3) gegen den Uhrzeigersinn, Randkanten (R,2) so orientiert,
    dass das Gebiet links liegt.
    """
    rand = []
    for k in range(len(polygon)):
        a, b = polygon[k], polygon[(k + 1) % len(polygon)]
        s = max(1, math.ceil(np.linalg.norm(b - a) / raster))
        rand += [a + (b - a) * t / s for t in range(s)]
    rand = np.array(rand)
    gl = ConvexHull(polygon).equations                     # n.p + c <= 0 innen
    lo, hi = polygon.min(0), polygon.max(0)
    gx, gy = np.meshgrid(np.arange(lo[0], hi[0] + raster, raster), np.arange(lo[1], hi[1] + raster, raster))
    innen = np.c_[gx.ravel(), gy.ravel()]
    abstand_rand = -(innen @ gl[:, :2].T + gl[:, 2]).max(1)
    innen = innen[abstand_rand >= raster / 2]
    if len(innen):
        d, _ = cKDTree(xy_bohrungen).query(innen)
        innen = innen[d >= raster / 2]
    punkte = np.vstack([xy_bohrungen, rand, innen])
    tri = Delaunay(punkte)
    dr = tri.simplices.copy()
    p = punkte[dr]
    flaeche = ((p[:, 1, 0] - p[:, 0, 0]) * (p[:, 2, 1] - p[:, 0, 1])
               - (p[:, 2, 0] - p[:, 0, 0]) * (p[:, 1, 1] - p[:, 0, 1])) / 2
    dr[flaeche < 0] = dr[flaeche < 0][:, [0, 2, 1]]
    dr = dr[np.abs(flaeche) > 1e-9 * raster * raster]
    kanten: dict[tuple[int, int], int] = defaultdict(int)
    for a, b, c in dr:
        for u, v in ((a, b), (b, c), (c, a)):
            kanten[(u, v)] += 1
    rand_k = np.array([(u, v) for (u, v) in kanten if (v, u) not in kanten])
    return punkte, dr, rand_k


def _kollinear(xy: np.ndarray) -> bool:
    if len(xy) < 3:
        return True
    s = np.linalg.svd(xy - xy.mean(0), compute_uv=False)
    return s[1] <= 1e-6 * max(s[0], 1e-9)


def interpolieren(ziel: np.ndarray, xy: np.ndarray, z: np.ndarray, methode: str = "idw") -> np.ndarray:
    """Exakter Interpolator: IDW (p=2) oder Duennplatten-Spline (tps, linearer Trend; braucht 3 nicht
    kollineare Punkte, sonst IDW)."""
    if len(z) == 1:
        return np.full(len(ziel), float(z[0]))
    if methode == "tps" and not _kollinear(xy):
        return RBFInterpolator(xy, z, kernel="thin_plate_spline", degree=1)(ziel)
    d = np.hypot(ziel[:, None, 0] - xy[None, :, 0], ziel[:, None, 1] - xy[None, :, 1])
    out = np.empty(len(ziel))
    treffer = d.min(1) < 1e-9
    out[treffer] = z[d[treffer].argmin(1)]
    w = 1.0 / d[~treffer] ** 2
    out[~treffer] = (w * z).sum(1) / w.sum(1)
    return out


def verschneiden(oben: np.ndarray, roh: list[np.ndarray], basis: float) -> np.ndarray:
    """Stratigraphischer Verschnitt von oben nach unten: z_unterkante_i = min(z_i, z_oberkante_i), >= Basis;
    Reste unter MIN_MAECHTIGKEIT werden zu 0 (Koerper und Volumen sehen dieselbe Ausduennung)."""
    out = [oben]
    for r in roh:
        z = np.maximum(np.minimum(r, out[-1]), basis)
        out.append(np.where(out[-1] - z < MIN_MAECHTIGKEIT, out[-1], z))
    return np.array(out)


def _freie_grenzen(bohrungen: list[Bohrung], kontakte: list[list[Kontakt]],
                   vorlaeufig: list[np.ndarray]) -> dict[tuple[int, int], float]:
    """Linsengrenzen innerhalb eines geteilten Abschnitts: dort, wo die Flaechen aus den exakten Kontakten
    liegen (Mittel der Gruppe = Mitte der ausduennenden Einheit), begrenzt auf den Abschnitt, geordnet."""
    out: dict[tuple[int, int], float] = {}
    for bi, ks in enumerate(kontakte):
        gruppen: dict[tuple, list[int]] = defaultdict(list)
        for j, k in enumerate(ks):
            if k.art == "frei":
                gruppen[k.gruppe].append(j)
        je_abschnitt: dict[tuple, list[tuple]] = defaultdict(list)
        for g, js in gruppen.items():
            lo, hi = ks[js[0]].lo, ks[js[0]].hi
            ziel = float(np.mean([vorlaeufig[j][bi] for j in js]))
            je_abschnitt[(lo, hi)].append((min(js), js, ziel))
        for (lo, hi), gs in je_abschnitt.items():
            gs.sort()
            r = min(FREI_RAND, (hi - lo) / (2 * (len(gs) + 1)))
            z = [min(max(ziel, lo + r), hi - r) for _, _, ziel in gs]
            if any(z[k + 1] > z[k] - MIN_MAECHTIGKEIT for k in range(len(z) - 1)):
                z = [hi - (hi - lo) * (k + 1) / (len(gs) + 1) for k in range(len(gs))]   # gleichmaessig
            for (_, js, _), zz in zip(gs, z):
                for j in js:
                    out[(bi, j)] = zz
    return out


def schichtmodell(bohrungen: list[Bohrung], kontakte: list[list[Kontakt]], punkte: np.ndarray,
                  xy_b: np.ndarray, basis: float, methode: str = "idw") -> dict:
    """Grenzflaechen an allen Netzknoten: Zeile 0 = Gelaende, Zeile j+1 = Unterkante Einheit j.

    1. vorlaeufig aus exakten Kontakten (ohne solche: Mitte der freien Bereiche; ohne alles: Basis)
    2. freie Grenzen (Linsen) festlegen, neu interpolieren
    3. Zensur: endet eine Bohrung in Einheit j, gilt Unterkante_j <= Endteufe - ZENSUR_MARGE; verletzt
       die Flaeche das, wird dort ein Stuetzpunkt gesetzt (iterativ)
    4. Verschnitt von oben nach unten, Basis = tiefste Endteufe
    5. Ausdehnung nicht durchgehender Einheiten begrenzen (_ausdehnung)
    """
    nb, n = len(bohrungen), len(kontakte[0]) if kontakte else 0
    oben = interpolieren(punkte, xy_b, np.array([b.gok for b in bohrungen]), methode)

    def flaeche(daten: dict[int, float]) -> np.ndarray:
        if not daten:
            return np.full(len(punkte), basis)
        bi = np.array(sorted(daten))
        return interpolieren(punkte, xy_b[bi], np.array([daten[i] for i in bi]), methode)

    exakt = [{bi: kontakte[bi][j].z for bi in range(nb) if kontakte[bi][j].art == "exakt"} for j in range(n)]
    vorl = []
    for j in range(n):
        d = exakt[j] or {bi: (kontakte[bi][j].lo + kontakte[bi][j].hi) / 2
                         for bi in range(nb) if kontakte[bi][j].art == "frei"}
        vorl.append(flaeche(d)[:nb])
    frei = _freie_grenzen(bohrungen, kontakte, vorl)
    zensur: list[dict[int, float]] = [{} for _ in range(n)]
    roh: list[np.ndarray | None] = [None] * n
    geaendert = set(range(n))
    for _ in range(ZENSUR_RUNDEN):
        for j in geaendert:                               # nur Flaechen mit neuen Stuetzpunkten neu rechnen
            roh[j] = flaeche({**exakt[j], **{bi: z for (bi, jj), z in frei.items() if jj == j}, **zensur[j]})
        flaechen = verschneiden(oben, roh, basis)
        geaendert = set()
        for bi in range(nb):
            for j, k in enumerate(kontakte[bi]):
                if k.art != "zensiert" or bi in zensur[j]:
                    continue
                grenze = max(k.hi - ZENSUR_MARGE, basis)
                if flaechen[j + 1][bi] > grenze + 1e-6:
                    zensur[j][bi] = grenze
                    geaendert.add(j)
        if not geaendert:
            break
    ausgeduennt = _ausdehnung(flaechen, kontakte, punkte, xy_b)
    abweichung = 0.0
    for bi in range(nb):
        for j, k in enumerate(kontakte[bi]):
            soll = k.z if k.art == "exakt" else frei.get((bi, j))
            if soll is not None:
                abweichung = max(abweichung, abs(flaechen[j + 1][bi] - soll))
    dist, _ = cKDTree(xy_b).query(punkte)
    return {"flaechen": flaechen, "frei": frei, "zensur": zensur, "abstand": dist, "ausgeduennt": ausgeduennt,
            "max_abweichung_bohrungen": abweichung}


def _ausdehnung(flaechen: np.ndarray, kontakte: list[list[Kontakt]], punkte: np.ndarray, xy_b: np.ndarray) -> list[int]:
    """Ausdehnung von Einheiten, die nicht in allen Bohrungen vorkommen (Linsen, Auskeilen).

    IDW-Flaechen erreichen Maechtigkeit 0 nur genau an den Bohrungen ohne die Einheit: eine Linse aus einer
    Bohrung laege sonst duenn unter dem ganzen Gebiet. Indikator vorhanden=1 / fehlt=0 (unbekannt zaehlt
    nicht), IDW-interpoliert; unter PRAESENZ_SCHWELLE wird die Einheit auf ihre Mitte zusammengezogen
    (oberste Einheit auf ihr Dach, unterste auf ihre Sohle). An den Bohrungen aendert sich nichts.
    Rueckgabe: Anzahl zusammengezogener Knoten je Einheit.
    """
    n = flaechen.shape[0] - 1
    anzahl = []
    for j in range(n):
        ind = {bi: 1.0 if ks[j].status == "vorhanden" else 0.0
               for bi, ks in enumerate(kontakte) if ks[j].status != "unbekannt"}
        if not ind or min(ind.values()) == 1.0:
            anzahl.append(0)
            continue
        bi = np.array(sorted(ind))
        weg = interpolieren(punkte, xy_b[bi], np.array([ind[i] for i in bi]), "idw") < PRAESENZ_SCHWELLE
        if j == 0:
            flaechen[1][weg] = flaechen[0][weg]
        elif j == n - 1:
            flaechen[j][weg] = flaechen[j + 1][weg]
        else:
            mitte = (flaechen[j][weg] + flaechen[j + 1][weg]) / 2
            flaechen[j][weg] = mitte
            flaechen[j + 1][weg] = mitte
        anzahl.append(int(weg.sum()))
    return anzahl
