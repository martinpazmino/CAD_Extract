---
title: "Corpus real: Gutachten públicos para probar la extracción"
date: 2026-10-25
tags: [corpus, validacion, gutachten, datos]
aliases: [Corpus público, Gutachten de prueba]
---

# Corpus real: Gutachten públicos para probar la extracción

**Conclusión:** no hace falta esperar a tener Gutachten propios. En Alemania se publican muchos
Baugrundgutachten completos, con Bohrprofile DIN 4023, Rammsondierungen y Lageplan, en la
participación pública de **Bebauungspläne**, en **Planfeststellungen** (UVP-Verbund) y en portales
de **transparencia** (p. ej. Hamburgo). Hay 16 candidatos de 8 Länder en
[`spikes/korpus/manifest.tsv`](../spikes/korpus/manifest.tsv) y un script que los descarga, filtra y
evalúa.

**Estado (2026-10-25):** la descarga automática está bloqueada por la red del entorno de Claude
(403 en `www.dresden.de`, `daten.transparenz.hamburg.de`, `www.ditzingen.de`, …). El equipo subió
a mano **3 PDFs** (Wachenroth, Talheim, Halle), con verdad transcrita en
[`spikes/korpus/groundtruth/`](../spikes/korpus/groundtruth/talheim.json). Resultados:
[15](15_resultados_pdfs_reales.md). Faltan **5–7 más, no vistos**, para medir la generalidad de
verdad.

## 1. Cómo desbloquearlo (elige una)

1. **Permitir los dominios** en la configuración del entorno (Network access → Allowed domains):
   los hosts de la columna `url` del manifest. Después: `python screen_corpus.py --download <dir>`.
2. **Descargar a mano** (navegador) los PDFs que interesen, dejarlos en una carpeta fuera del
   repo y ejecutar `python screen_corpus.py --screen <dir> <salida>`.
3. Subirlos a la sesión de Claude para que los evalúe (no se commitean).

## 2. Qué buscar (5–10 bien elegidos > 50 al azar)

| Criterio | Por qué |
|---|---|
| Distinto **software** (`Producer`/`Creator`: GGU-STRATIG, DC-BOHR, WinBohr, AutoCAD…) | Es lo que más cambia el layout |
| Distintas **oficinas** y **Länder** | Convenciones locales (IDs, `NHN`/`NN`, CRS) |
| Con **Rammsondierung DPH** y, si hay, **CPT** | [05](05_sondierungen.md) |
| Con **Lageplan** y/o tabla de coordenadas | [07](07_coordenadas.md) |
| Al menos 1–2 con **Längsschnitt / Baugrundschnitt** (ideal: túnel, p. ej. `offenstetten`) | [03](03_laengsschnitt_generalizacion.md) |
| Al menos 1 **escaneado** | Medir la ruta OCR y que el filtro lo detecte |

El script ya informa de `producer/creator`, páginas vectoriales vs. escaneadas, páginas
candidatas a Bohrprofil y la escala rotulada (`M 1:…`).

## 3. Evaluación sin verdad (primera pasada)

Sin ground truth sólo se mide **autoconsistencia** (`screen_corpus.py`):

| Indicador | Señal de problema |
|---|---|
| Sondeos detectados v1 / v2 vs. sondeos rotulados en la portada/Lageplan | faltan o sobran sondeos |
| Escala de la regresión (v2) vs. `M 1:…` del texto | columna o etiquetas mal encontradas |
| % límites confirmados por etiqueta | geometría y texto no coinciden |
| % texto = Schraffur | clasificador de Schraffur o parser de texto fallan |
| Aritmética NHN (v1) | profundidades mal leídas |
| Issues por capa | dónde mirar primero |

Más una miniatura de cada página de Bohrprofil para revisión visual. Con eso se eligen los 5–10
documentos y se crea la **verdad semi-automática** (v2 → corrección humana → `ground_truth.json`,
[09 §2](09_validacion_benchmark.md#2-formato-de-verdad-ground-truth)).

## 4. Uso legal de los PDFs

> [!IMPORTANT]
> No es asesoramiento jurídico. Los Gutachten son obras protegidas de las oficinas que los
> firman, aunque estén publicados.

- **Uso interno para pruebas.** Para esto parece aplicar el § 44b UrhG (*Text und Data Mining*
  sobre obras accesibles legalmente). Si el titular ha excluido el TDM de forma legible por
  máquina, no se usa. Las copias se borran cuando ya no hacen falta.
- **No redistribuir:** los PDFs no van al repo (`data/*.pdf` ya está en `.gitignore`). El repo sólo
  guarda el manifest (URL + nota) y, cuando existan, los `sha256` y la verdad anotada.
- **Datos personales:** los Gutachten nombran a ingenieros, propietarios o direcciones. No
  publicar extractos fuera del equipo.
- Para el uso con **terceros** el corpus de pruebas no cambia, pero sí la licencia del software
  ([14](14_licencias_terceros.md)).

## 5. Otras fuentes a explorar

- Bases de datos de sondeos de los servicios geológicos de los Länder (p. ej. NIBIS/LBEG,
  geoportales de Hamburgo o Berlín). Suelen ser **escaneos** de Schichtenverzeichnisse: sirven
  para la ruta OCR, no para la vectorial.
- Ejemplos sintéticos compartibles: el generador
  [`synth_bohrprofil.py`](../spikes/extraktion_v2/synth_bohrprofil.py) no tiene restricciones y
  sirve para reproducir errores ante terceros, p. ej. swisstopo ([13](13_colaboracion_swisstopo.md)).

Up: [Índice](README.md)

Related: [09 Validación](09_validacion_benchmark.md) · [10 Plan](10_plan_implementacion.md) · [14 Licencias](14_licencias_terceros.md) · [13 swisstopo](13_colaboracion_swisstopo.md)
