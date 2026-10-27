# Geo_Agent / CAD_Extract — memoria del proyecto

## Objetivo
Desde un Bodengutachten en PDF construir el **Baugrundmodell**: sondeos validados y trazables →
Supabase → geometrías IFC 4.3 en That Open Engine. Arquitectura: `docs/ARQUITECTURA_BAUGRUNDMODELL.md`.
La app actual (`app.py`, `geo_agent/`, Streamlit) es v1: posiciones fijas, 0/58 sondeos en PDFs ajenos.

## Leer antes de tocar la extracción
- `docs/16_lecciones_aprendidas.md`: reglas explícitas (proceso P1–P12, entrada E, geometría G, etiquetas L/T, texto B, agua W, segundas fuentes S, swissgeol R, modelo M, entorno X). Respetarlas.
- `docs/17_algoritmo_extraccion.md`: especificación del algoritmo (etapas, parámetros, confianza).
- `docs/15_resultados_pdfs_reales.md`: resultados ciegos y de entrenamiento.
- `docs/11_decisiones.md`: decisiones D1–D45.
- `docs/18_modelador_capas.md`: modelo de capas (N3) y visor That Open.

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

## Modelo y visor
- `services/modeler` (paquete `baugrundmodell`): `python -m baugrundmodell modelo.ifc a.json [...] --bericht informe.json`;
  pruebas `python -m pytest tests` (verdad sintética). Todo cambio: contactos exactos, sólidos cerrados, IFC sin errores.
- `apps/web`: `npm install && npm run dev` (`?ifc=modelle/x.ifc&ueberhoehung=5`); prueba sin pantalla
  `npm run build && node scripts/check.mjs <x.ifc> <capturas>`. web-ifc fijado en 0.0.77 (lección X9).

## Entorno (sesiones en la nube)
- Webs municipales bloqueadas por la política de red; pypi y GitHub accesibles. Los PDFs los sube el usuario.
- Dependencias pesadas en venvs del scratchpad: `venv` (pymupdf, opencv, rapidocr), `sgvenv` (swissgeol).
- Rama de trabajo indicada en la sesión; no crear PR sin que lo pidan.
