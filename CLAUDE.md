# Geo_Agent / CAD_Extract — memoria del proyecto

## Objetivo
Desde un Bodengutachten en PDF construir el **Baugrundmodell**: sondeos validados y trazables →
Supabase → geometrías IFC 4.3 en That Open Engine. Arquitectura: `docs/ARQUITECTURA_BAUGRUNDMODELL.md`.
La app actual (`app.py`, `geo_agent/`, Streamlit) es v1: posiciones fijas, 0/58 sondeos en PDFs ajenos.

## Leer antes de tocar la extracción
- `docs/16_lecciones_aprendidas.md`: reglas explícitas (P1–P8, L1–L18, …). Respetarlas.
- `docs/17_algoritmo_extraccion.md`: especificación del algoritmo (etapas, parámetros, confianza).
- `docs/15_resultados_pdfs_reales.md`: resultados ciegos y de entrenamiento.
- `docs/11_decisiones.md`: decisiones D1–D32.

## Reglas de trabajo
- **Prueba ciega**: con un PDF nuevo, congelar predicciones (`spikes/korpus/blind_test.py freeze`)
  y **subirlas al repo antes de abrir el PDF**; después transcribir la verdad en `spikes/korpus/groundtruth/`.
- Separar siempre cifras ciegas de cifras de entrenamiento.
- Todo cambio en la extracción pasa la regresión (`spikes/korpus/regression.py`) sobre PDFs reales y sintéticos.
- Reglas generales (rasgos del dibujo), nunca excepciones por PDF u oficina.
- Un dato dudoso se **marca** (issue / confianza baja), nunca se esconde. Un sondeo falso es peor que uno perdido.
- PDFs de terceros **no** se suben al repo: sólo URL, `sha256` y datos factuales.
- Documentación en español, notas enlazadas (Up/Related, frontmatter). Código y comentarios en alemán.

## Entorno (sesiones en la nube)
- Webs municipales bloqueadas por la política de red; pypi y GitHub accesibles. Los PDFs los sube el usuario.
- Dependencias pesadas en venvs del scratchpad: `venv` (pymupdf, opencv, rapidocr), `sgvenv` (swissgeol).
- Rama de trabajo indicada en la sesión; no crear PR sin que lo pidan.
