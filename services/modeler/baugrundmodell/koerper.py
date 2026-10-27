"""Layer-Cake Schritt 5: geschlossener Koerper je Einheit (Dach-TIN + Sohl-TIN + Seitenwaende).

Wo die Einheit ausduennt (Maechtigkeit < MIN_MAECHTIGKEIT), fallen Dach- und Sohlknoten zusammen;
Dreiecke, die dadurch doppelt und flach werden, entfallen. So bleibt die Huelle geschlossen
(jede Kante gleich oft in beide Richtungen), ohne Flaechen der Dicke 0 zu exportieren.
"""
from __future__ import annotations

from collections import Counter

import numpy as np

from .flaechen import MIN_MAECHTIGKEIT


def koerper(punkte: np.ndarray, dreiecke: np.ndarray, rand: np.ndarray, z_oben: np.ndarray,
            z_unten: np.ndarray) -> tuple[list[tuple[float, float, float]], list[list[int]]] | None:
    """Knoten und Flaechen (Dreiecke, Waende als Drei-/Vierecke, nach aussen orientiert); None ohne Volumen."""
    n = len(punkte)
    duenn = (z_oben - z_unten) < MIN_MAECHTIGKEIT
    oben = np.arange(n)
    unten = np.where(duenn, oben, n + oben)
    flaechen: list[list[int]] = []
    for a, b, c in dreiecke:
        if duenn[a] and duenn[b] and duenn[c]:
            continue
        flaechen.append([oben[a], oben[b], oben[c]])
        flaechen.append([unten[a], unten[c], unten[b]])
    for a, b in rand:                                  # Gebiet links von a->b, Wand schaut nach rechts
        f = [unten[a], unten[b], oben[b], oben[a]]
        f = [v for k, v in enumerate(f) if v != f[k - 1]]
        if len(f) >= 3:
            flaechen.append(f)
    if not flaechen:
        return None
    benutzt = sorted({v for f in flaechen for v in f})
    neu = {v: k for k, v in enumerate(benutzt)}
    knoten = [(float(punkte[v % n, 0]), float(punkte[v % n, 1]),
               float(z_oben[v] if v < n else z_unten[v - n])) for v in benutzt]
    return knoten, [[neu[v] for v in f] for f in flaechen]


def pruefen(knoten: list[tuple[float, float, float]], flaechen: list[list[int]]) -> dict:
    """Geschlossenheit (jede Kante gleich oft hin und zurueck), nicht-mannigfaltige Kanten, Volumen."""
    kanten: Counter = Counter()
    for f in flaechen:
        for k in range(len(f)):
            kanten[(f[k], f[(k + 1) % len(f)])] += 1
    offen = sum(1 for (u, v), c in kanten.items() if kanten.get((v, u), 0) != c)
    mehrfach = sum(1 for (u, v), c in kanten.items() if u < v and c > 1)
    p = np.array(knoten)
    vol = 0.0
    for f in flaechen:
        for k in range(1, len(f) - 1):
            vol += np.dot(p[f[0]], np.cross(p[f[k]], p[f[k + 1]])) / 6.0
    return {"geschlossen": offen == 0, "offene_kanten": offen, "nicht_mannigfaltig": mehrfach, "volumen": vol}


def volumen_prismen(punkte: np.ndarray, dreiecke: np.ndarray, z_oben: np.ndarray, z_unten: np.ndarray) -> float:
    """Kontrollvolumen: Dreiecksflaeche x mittlere Maechtigkeit (exakt fuer stueckweise lineare Flaechen)."""
    p = punkte[dreiecke]
    a = ((p[:, 1, 0] - p[:, 0, 0]) * (p[:, 2, 1] - p[:, 0, 1])
         - (p[:, 2, 0] - p[:, 0, 0]) * (p[:, 1, 1] - p[:, 0, 1])) / 2
    d = (z_oben - z_unten)[dreiecke].mean(1)
    return float((a * d).sum())
