---
title: "Längsschnitt: ejes, túnel y geología sin constantes"
date: 2026-10-23
tags: [geo_agent, extraccion, laengsschnitt, tunel, generalizacion]
aliases: [Längsschnitt v2, Generalización Längsschnitt]
---

# Längsschnitt: ejes, túnel y geología sin constantes

**Conclusión:** el método actual (regresiones de ejes, máscara del túnel, validación con `TS=`)
es correcto; lo que hay que generalizar es **cómo se encuentran** las etiquetas, el túnel y la
geología. Además conviene pasar de raster a **polígonos vectoriales**: son más exactos, más
rápidos y producen directamente el `IfcGeoslice` del modelo.

**Estado:** diseño. No probado todavía con PDFs (el spike cubre el Bohrprofil); los supuestos que
reemplaza están en [01 §2](01_diagnostico_layout_fijo.md#längsschnitt-geo_agentlaengsschnittpy).

## 1. Eje X: estaciones

- Regex con variantes: `0+100`, `0+100.000`, `km 1+250,000`, `1+250` (km con 1–2 dígitos).
- Las etiquetas de estación forman una **fila**: agrupar candidatos por `y` (tolerancia ~3 pt),
  quedarse con la fila de más elementos cuyo valor crece con `x`; varias filas → la más larga.
- Ajuste `TM = a·x + b` con residuos; residuo > 0,5 m → etiqueta mal leída o de otra fila.

## 2. Eje Y: NHN

- Candidatos: números `±dd.dd` / `±dd,dd` alineados en una **columna** (mismo borde derecho)
  con espaciado constante y correlación |r| > 0,99 con `y`. Puede haber dos ejes (izquierda y
  derecha): ambos deben dar la misma recta.
- La razón entre escalas `a_y / a_x` es la **Überhöhung** (exageración vertical); si el plano la
  rotula (`Überhöhung 1:10`), se valida.

## 3. Túnel

Orden de preferencia:
1. **Capa OCG** del CAD (`get_drawings()` trae `layer` por path — [verificado](ARQUITECTURA_BAUGRUNDMODELL.md#62-primitivas-una-sola-vez-por-documento-cacheadas)).
2. **Geometría**: polígonos largos en `x` cuyo espesor vertical es casi constante y coincide con
   `Ø / escala_y`; el diámetro sale del texto (`Ø`, `D=`, `Da=`).
3. **Un clic del usuario** en la UI: el perfil guarda la capa/color/estilo elegido.
Validación (ya existe en v1): Sohle detectada = etiquetas `TS=…m`.

## 4. Geología

- **Colores desde la leyenda del propio Längsschnitt**: cada muestra (rectángulo relleno) con
  su nombre a la derecha da el mapa color → Bodenart. Sustituye `DEFAULT_COLOR_MAP`
  (`geo_agent/laengsschnitt.py:28-33`). Mismo patrón que las muestras de Schraffur
  ([04](04_schraffur_din4023.md)).
- **Polígonos vectoriales** en lugar del raster de toda la página: cada path con relleno de
  geología → `shapely.Polygon` en coordenadas `(estación, NHN)` vía las regresiones. Resultado:
  la sección geológica interpretada (= `IfcGeoslice`) y sus **interfaces** entre sondeos, que
  alimentan el modelo 3D ([arquitectura §6.6](ARQUITECTURA_BAUGRUNDMODELL.md#66-längsschnitt-v2), §7.2).
- La composición en el túnel se calcula intersectando el polígono del túnel con los polígonos
  geológicos por estación, en vez de muestrear píxeles.

## 5. Sondeos en la sección

Los Längsschnitte dibujan mini-columnas de los sondeos. El **mismo detector de columnas** del
Bohrprofil ([02 §1](02_bohrprofil_generalizacion.md#1-columnas-por-geometría)) las encuentra; con
la regresión del eje X se obtiene su estación. Validaciones cruzadas: GOK y límites deben
coincidir con el Bohrprofil del mismo ID.

## 6. Terreno y agua

- GOK del terreno: la polilínea del terreno (capa/estilo propio) en lugar del primer píxel de
  color geológico (`geo_agent/laengsschnitt.py:242`).
- Líneas de agua (HGW, MGW, Bemessungswasserstand, normalmente azules y discontinuas) →
  polilíneas en `(estación, NHN)` → [06](06_grundwasser.md).

## 7. Otros arreglos

- Recorrer todas las páginas, no sólo `doc[0]`; región útil = marco del dibujo, no `160…1130 pt`.
- Eliminar la caché global `_NHN_FIT` (`geo_agent/laengsschnitt.py:419`): pasar la regresión al
  generador del Prüfbild.
- Cachear las primitivas (> 150 000 paths) una vez por documento.

Up: [Índice](README.md)

Related: [01 Diagnóstico](01_diagnostico_layout_fijo.md) · [02 Bohrprofil](02_bohrprofil_generalizacion.md) · [04 Schraffur](04_schraffur_din4023.md) · [06 Grundwasser](06_grundwasser.md) · [Arquitectura](ARQUITECTURA_BAUGRUNDMODELL.md)
