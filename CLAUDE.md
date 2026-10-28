# Geo_Agent / CAD_Extract — memoria del proyecto

## Objetivo
Desde un Bodengutachten en PDF construir el **Baugrundmodell**: sondeos validados y trazables →
Supabase → geometrías IFC 4.3 en That Open Engine. Arquitectura: `docs/ARQUITECTURA_BAUGRUNDMODELL.md`.
La app actual (`app.py`, `geo_agent/`, Streamlit) es v1: posiciones fijas, 0/58 sondeos en PDFs ajenos.

## Leer antes de tocar la extracción
- `docs/16_lecciones_aprendidas.md`: reglas explícitas (proceso P1–P12, entrada E, geometría G, etiquetas L/T, texto B, agua W, segundas fuentes S, swissgeol R, modelo M, entorno X). Respetarlas.
- `docs/17_algoritmo_extraccion.md`: especificación del algoritmo (etapas, parámetros, confianza).
- `docs/15_resultados_pdfs_reales.md`: resultados ciegos y de entrenamiento.
- `docs/11_decisiones.md`: decisiones D1–D62.
- `docs/18_modelador_capas.md`: modelo de capas (N3) y visor That Open.
- `docs/19_app_v2.md`: app Streamlit v2 (PDF → revisión → modelo → visor).
- `docs/20_lage_pruefung_viewer.md`: visor con controles de TwinBimM, modelos > 5 km, Lage sobre plano, Prüfstand.

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
- App: `streamlit run app.py` (Windows: `start.bat`). Página v2 en `ui/baugrundmodell.py`; estado del proyecto
  (correcciones, Reihe, Lage, eventos del visor, Prüfstand, einchecken) en `ui/projekt.py`; extracción/modelo en
  `ui/pipeline.py` (pruebas: `pytest tests`). La extracción se usa desde `spikes/extraktion_v2/prototyp_v4.py` sin tocarla.
- Flujo (docs/20): tablas antes del modelo → Lage sobre PDF del plano (2 puntos) o fila con distancias propias →
  *Baugrundmodell erzeugen* → nachführen automático → Einchecken. Eventos del visor con `nr` + firma de proyecto.
- `services/modeler` (paquete `baugrundmodell`): `python -m baugrundmodell modelo.ifc a.json [...] --bericht informe.json`;
  pruebas `cd services/modeler && python -m pytest tests`. Todo cambio: contactos exactos, sólidos cerrados, IFC sin
  errores, **unidad METRE** (M17).
- `apps/web` (controles del TwinBimM, editor de Lage): tras cambiar el visor `npm run build` y **subir `apps/web/dist`**
  (la app lo usa sin Node); web-ifc 0.0.77 (X9). Prueba: `python scripts/testplan.py <planes>` y en `apps/web`
  `node scripts/check.mjs <modelo.ifc> <planes> <capturas>` (17 comprobaciones).
- Punta a punta: app sin pantalla en un puerto y `node scripts/check_app.mjs http://localhost:<puerto> <capturas>
  --plan <planes>` (o `--pdf <archivo>`). Reiniciar la app después de compilar el visor (X12); `pkill`/`pgrep -f` en un
  comando aparte (X3, X19).

## Entorno (sesiones en la nube)
- Webs municipales bloqueadas por la política de red; pypi y GitHub accesibles. Los PDFs los sube el usuario.
- Dependencias pesadas en venvs del scratchpad: `venv` (pymupdf, opencv, rapidocr), `sgvenv` (swissgeol).
- Rama de trabajo indicada en la sesión; no crear PR sin que lo pidan.
