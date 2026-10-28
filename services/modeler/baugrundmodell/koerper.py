"""Layer-Cake Schritt 5: geschlossener Koerper je Einheit (Dach-TIN + Sohl-TIN + Seitenwaende).

Wo die Einheit ausduennt (Maechtigkeit < MIN_MAECHTIGKEIT), fallen Dach- und Sohlknoten zusammen;
Dreiecke, die dadurch doppelt und flach werden, entfallen. So bleibt die Huelle geschlossen
(jede Kante gleich oft in beide Richtungen), ohne Flaechen der Dicke 0 zu exportieren.
Alles vektorisiert (numpy): Trassen ueber 5 km haben 20-30 Tausend Knoten je Flaeche.
"""
from __future__ import annotations

import numpy as np

from .flaechen import MIN_MAECHTIGKEIT


def koerper(punkte: np.ndarray, dreiecke: np.ndarray, rand: np.ndarray, z_oben: np.ndarray,
            z_unten: np.ndarray) -> tuple[np.ndarray, np.ndarray] | None:
    """Knoten (K,3, auf mm gerundet) und Dreiecke (F,3, nach aussen orientiert); None ohne Volumen."""
    n = len(punkte)
    duenn = (z_oben - z_unten) < MIN_MAECHTIGKEIT
    oben = np.arange(n)
    unten = np.where(duenn, oben, n + oben)
    behalten = ~duenn[dreiecke].all(1)
    dach = oben[dreiecke[behalten]]
    sohle = unten[dreiecke[behalten]][:, [0, 2, 1]]
    a, b = rand[:, 0], rand[:, 1]                          # Gebiet links von a->b, Wand schaut nach rechts
    wand = np.vstack([np.c_[unten[a], unten[b], oben[b]], np.c_[unten[a], oben[b], oben[a]]])
    alle = np.vstack([dach, sohle, wand])
    gueltig = (alle[:, 0] != alle[:, 1]) & (alle[:, 1] != alle[:, 2]) & (alle[:, 0] != alle[:, 2])
    alle = alle[gueltig]
    if not len(alle):
        return None
    benutzt, neu = np.unique(alle, return_inverse=True)
    xy = punkte[benutzt % n]
    z = np.where(benutzt < n, z_oben[np.minimum(benutzt, n - 1)], z_unten[np.maximum(benutzt - n, 0)])
    knoten = np.round(np.c_[xy, z], 3)                     # mm: kleineres IFC, Kontakte sind auf cm angegeben
    return knoten, neu.reshape(-1, 3)


def dreiecke_aus(flaechen) -> np.ndarray:
    """Vielecke (Listen von Knotenindizes) als Faecher in Dreiecke zerlegen; (F,3)-Arrays bleiben, wie sie sind."""
    if isinstance(flaechen, np.ndarray) and flaechen.ndim == 2 and flaechen.shape[1] == 3:
        return flaechen
    out = [(f[0], f[k], f[k + 1]) for f in flaechen for k in range(1, len(f) - 1)]
    return np.array(out, dtype=np.int64).reshape(-1, 3)


def pruefen(knoten, flaechen) -> dict:
    """Geschlossenheit (jede Kante gleich oft hin und zurueck), nicht-mannigfaltige Kanten, Volumen."""
    p = np.asarray(knoten, dtype=float)
    f = dreiecke_aus(flaechen)
    n = len(p) + 1
    u = f.ravel()
    v = np.roll(f, -1, axis=1).ravel()
    hin, anzahl = np.unique(u * n + v, return_counts=True)
    zurueck = (hin % n) * n + hin // n
    pos = np.clip(np.searchsorted(hin, zurueck), 0, len(hin) - 1)
    gegen = np.where(hin[pos] == zurueck, anzahl[pos], 0)
    offen = int((gegen != anzahl).sum())
    mehrfach = int(((anzahl > 1) & (hin // n < hin % n)).sum())
    a, b, c = p[f[:, 0]], p[f[:, 1]], p[f[:, 2]]
    vol = float(np.einsum("ij,ij->i", a, np.cross(b, c)).sum() / 6.0)
    return {"geschlossen": offen == 0, "offene_kanten": offen, "nicht_mannigfaltig": mehrfach, "volumen": vol}


def volumen_prismen(punkte: np.ndarray, dreiecke: np.ndarray, z_oben: np.ndarray, z_unten: np.ndarray) -> float:
    """Kontrollvolumen: Dreiecksflaeche x mittlere Maechtigkeit (exakt fuer stueckweise lineare Flaechen)."""
    p = punkte[dreiecke]
    a = ((p[:, 1, 0] - p[:, 0, 0]) * (p[:, 2, 1] - p[:, 0, 1])
         - (p[:, 2, 0] - p[:, 0, 0]) * (p[:, 1, 1] - p[:, 0, 1])) / 2
    d = (z_oben - z_unten)[dreiecke].mean(1)
    return float((a * d).sum())
