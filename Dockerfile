# GeoIM – Baugrundmodell-App als Container: ein Prozess (FastAPI) liefert API und Oberflaeche (apps/web/dist, im
# Repo gebaut, kein Node noetig). Laeuft auf Render, Railway, Fly.io, Google Cloud Run, Hugging Face Spaces oder
# einem eigenen Server (docs/22_despliegue.md).
#
#   docker build -t geoim .                          (ohne OCR: --build-arg OCR=0, kleiner und ohne Systempakete)
#   docker run -p 8500:8500 -e GEO_AGENT_PASSWORT=… -v geoim-daten:/data geoim
#
# Umgebung: PORT (Plattform), GEO_AGENT_PASSWORT (Anmeldung; ohne = offen!), GEO_AGENT_BENUTZER (optional),
# GEO_AGENT_MAX_MB (Upload-Grenze, 200), GEO_AGENT_ARBEIT (Datenordner, /data - als Volume einhaengen, sonst sind
# Projekte nach einem Neustart weg).
FROM python:3.13-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    GEO_AGENT_HOST=0.0.0.0 \
    PORT=8500 \
    GEO_AGENT_ARBEIT=/data

# OpenCV (OCR) braucht libGL und GLib (Debian trixie: libglib2.0-0t64, aeltere: libglib2.0-0); sonst nichts
ARG OCR=1
RUN if [ "$OCR" = "1" ]; then \
      apt-get update \
      && apt-get install -y --no-install-recommends libgl1 \
      && (apt-get install -y --no-install-recommends libglib2.0-0t64 || apt-get install -y --no-install-recommends libglib2.0-0) \
      && rm -rf /var/lib/apt/lists/*; \
    fi

WORKDIR /app
COPY requirements-server.txt requirements-ocr.txt constraints.txt ./
RUN pip install -r requirements-server.txt -c constraints.txt \
 && if [ "$OCR" = "1" ]; then pip install -r requirements-ocr.txt -c constraints.txt; fi

COPY . .
RUN useradd --create-home --uid 1000 geoim && mkdir -p /data && chown geoim:geoim /data \
 && chmod +x docker/entrypoint.sh

EXPOSE 8500
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s \
  CMD python -c "import os, urllib.request; urllib.request.urlopen('http://127.0.0.1:' + os.environ.get('PORT', '8500') + '/gesund', timeout=4)"
ENTRYPOINT ["docker/entrypoint.sh"]
CMD ["python", "-m", "server", "--kein-browser"]
