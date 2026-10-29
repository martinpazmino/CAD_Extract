# Colaborar en GeoIM

Gracias por ayudar. GeoIM convierte Bodengutachten en PDF en un Baugrundmodell IFC 4.3. Un sondeo falso
es peor que uno perdido, y por eso el proyecto tiene reglas estrictas sobre cómo se mide y se prueba.
Las reglas completas están en [docs/16 Lecciones aprendidas](docs/16_lecciones_aprendidas.md).

## Preparar el entorno

```bash
python -m venv .venv && . .venv/bin/activate        # Windows: start.bat lo hace solo
pip install -r requirements.txt -c constraints.txt  # Python 3.13; con otra versión, sin -c
pip install -r requirements-ocr.txt -c constraints.txt   # opcional: OCR
cd apps/web && npm ci                                # sólo si se cambia la página o el visor
```

## Antes de cada pull request

1. **Pruebas:** `pytest tests` y `cd services/modeler && pytest tests`.
2. **Página o visor cambiados** (`apps/web/src`):
   - `cd apps/web && npm run build` y **subir `apps/web/dist`**: el servidor la usa sin Node.
   - Comprobar con `scripts/check_app.mjs` (ver [README](README.md#pruebas)).
3. **Extracción cambiada** (`spikes/extraktion_v2/prototyp_v4.py`): regresión sobre PDFs reales, casos
   de estrés y sintéticos. Las cifras no deben empeorar:
   ```bash
   python spikes/korpus/regression.py --module spikes/extraktion_v2/prototyp_v4.py \
     --real <pdfs> --stress <carpeta> --synth <carpeta> --baseline spikes/korpus/baseline_v4.json
   ```
   Si una regla se toca, `ablation.py` muestra qué caso protege.
4. **Modelador cambiado:**
   - contactos exactos;
   - sólidos cerrados;
   - IFC sin errores;
   - unidad METRE.
5. **Dependencias cambiadas:** actualizar `constraints.txt` como se explica en
   [docs/22 §8](docs/22_despliegue.md#8-dependencias-y-versiones).

GitHub ejecuta los puntos 1, 2 (compilación) y la imagen del contenedor en cada push
([Prüfungen](.github/workflows/pruefungen.yml)).

## Reglas del proyecto

- **Prueba ciega con cada PDF nuevo:**
  1. Congelar las predicciones con `spikes/korpus/blind_test.py freeze`.
  2. Subirlas al repositorio **antes** de abrir el PDF.
  3. Después, transcribir la verdad en `spikes/korpus/groundtruth/`.

  Las cifras ciegas y las de entrenamiento van siempre separadas.
- **Reglas generales** basadas en rasgos del dibujo, nunca excepciones para un PDF o una oficina.
- **Lo dudoso se marca** (issue, confianza baja, capa sin clasificar), nunca se esconde.
- **Nada de PDFs de terceros en el repositorio:** sólo URL, `sha256` y datos factuales
  (`spikes/korpus/manifest.tsv`).
- **Normas:** no copiar textos de DIN. La base de datos de normas guarda abreviaturas y colores con
  la evidencia de cada dato. La app propone y nunca aplica una norma en silencio.
- **Idiomas:**
  - documentación en **español**, como notas enlazadas (frontmatter, `Up:` y `Related:`);
  - código, comentarios y textos de la interfaz en **alemán**.
- **Decisiones y lecciones:**
  - una decisión nueva va a [docs/11](docs/11_decisiones.md) (D…);
  - una lección, con la prueba que la vigila, a [docs/16](docs/16_lecciones_aprendidas.md).

## Licencia de las contribuciones

GeoIM se publica bajo la [AGPL-3.0-or-later](LICENSE). Al enviar una contribución, aceptas que se
publique bajo la misma licencia. Código o datos de terceros sólo con una licencia compatible, anotada
en [THIRD_PARTY_LICENSES.md](THIRD_PARTY_LICENSES.md). En concreto, nada de copiar código de
swissgeol: sólo se reimplementan sus ideas ([docs/14](docs/14_licencias_terceros.md)).
