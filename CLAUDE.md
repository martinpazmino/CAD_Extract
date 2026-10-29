# Geo_Agent / CAD_Extract — memoria del proyecto

## Objetivo
Desde un Bodengutachten en PDF construir el **Baugrundmodell**: sondeos validados y trazables →
Supabase → geometrías IFC 4.3 en That Open Engine. Arquitectura: `docs/ARQUITECTURA_BAUGRUNDMODELL.md`.
La app actual (`app.py`, `geo_agent/`, Streamlit) es v1: posiciones fijas, 0/58 sondeos en PDFs ajenos.

## Leer antes de tocar la extracción
- `docs/16_lecciones_aprendidas.md`: reglas explícitas (proceso P1–P12, entrada E, geometría G, etiquetas L/T, texto B, agua W, segundas fuentes S, swissgeol R, modelo M, entorno X). Respetarlas.
- `docs/17_algoritmo_extraccion.md`: especificación del algoritmo (etapas, parámetros, confianza).
- `docs/15_resultados_pdfs_reales.md`: resultados ciegos y de entrenamiento.
- `docs/11_decisiones.md`: decisiones D1–D72.
- `docs/18_modelador_capas.md`: modelo de capas (N3) y visor That Open.
- `docs/19_app_v2.md`: app Streamlit v2 (historia; sustituida por la 21).
- `docs/20_lage_pruefung_viewer.md`: visor con controles de TwinBimM, modelos > 5 km, Lage sobre plano, Prüfstand.
- `docs/21_app_schritte_normen.md`: app por pasos (FastAPI + visor), normas de la descripción, calibración nueva.

## Reglas de trabajo
- **Prueba ciega**: con un PDF nuevo, congelar predicciones (`spikes/korpus/blind_test.py freeze`)
  y **subirlas al repo antes de abrir el PDF**; después transcribir la verdad en `spikes/korpus/groundtruth/`.
- Separar siempre cifras ciegas de cifras de entrenamiento.
- Todo cambio en la extracción pasa la regresión sobre PDFs reales, casos de estrés y sintéticos:
  `python spikes/korpus/regression.py --module spikes/extraktion_v2/prototyp_v4.py --real <pdfs> --stress <ordner>
  --synth <ordner> --baseline spikes/korpus/baseline_v4.json` (casos de estrés: `stress_cases.py`; OCR con
  `GEO_OCR_CACHE=<dir>`). Además: `ablation.py` (qué regla protege qué caso) y `perturb.py` (girar/escalar/raster).
- Reglas generales (rasgos del dibujo), nunca excepciones por PDF u oficina.
- Un dato dudoso se **marca** (issue / confianza baja), nunca se esconde. Un sondeo falso es peor que uno perdido.
- PDFs de terceros **no** se suben al repo: sólo URL, `sha256` y datos factuales.
- Documentación en español, notas enlazadas (Up/Related, frontmatter). Código y comentarios en alemán.

## App, modelo y visor
- App por pasos (docs/21): `python -m server` (Windows: `start.bat`, puerto 8500) = FastAPI (`server/`) + página
  `apps/web/dist` (lit + visor). Streamlit (`app.py`, `start_excel.bat`) sólo para Excel v1.
- Reglas del proyecto en `ui/projekt.py` (`aendern(op)`): avisos = capas **unklassifiziert** (no confianza), todo
  revisado, quitar/restaurar, Ø de columnas, calibración (escala por distancia o 1:n + punto de referencia + giro /
  escala vertical + candado), arrastre sólo con candado (plano x/y; sección: altura sólo sin GOK del PDF).
  Extracción/modelo en `ui/pipeline.py`; la extracción se usa desde `spikes/extraktion_v2/prototyp_v4.py` sin tocarla.
- Normas (DIN 4023 / EN ISO 14688-1 / DIN 18196): `services/modeler/baugrundmodell/normen.json` + `normen.py`, con
  evidencia por dato; leer, nunca aplicar en silencio (propuesta con clic). IFC: `CPset_Bodenansprache` por capa.
- `services/modeler` (paquete `baugrundmodell`): `python -m baugrundmodell modelo.ifc a.json [...] --bericht informe.json`;
  pruebas `cd services/modeler && python -m pytest tests`. Todo cambio: contactos exactos, sólidos cerrados, IFC sin
  errores, **unidad METRE** (M17).
- `apps/web` (app por pasos `src/app`, visor `src/viewer`: controles del TwinBimM, editor de Lage): tras cambiar algo
  `npm run build` y **subir `apps/web/dist`** (el servidor lo usa sin Node); web-ifc 0.0.77 (X9). Prueba:
  `python scripts/testplan.py <planes>` y en `apps/web` `node scripts/check.mjs <modelo.ifc> <planes> <capturas>` (18).
- Punta a punta: `python -m server --port <p> --kein-browser --arbeit <vacía>` y `node scripts/check_app.mjs
  http://localhost:<p> <planes> <capturas>` (19 comprobaciones). `pkill`/`pgrep -f` en un comando aparte (X3, X19).

## Entorno (sesiones en la nube)
- Webs municipales bloqueadas por la política de red; pypi y GitHub accesibles. Los PDFs los sube el usuario.
- Dependencias pesadas en venvs del scratchpad: `venv` (pymupdf, opencv, rapidocr), `sgvenv` (swissgeol).
- Rama de trabajo indicada en la sesión; no crear PR sin que lo pidan.
