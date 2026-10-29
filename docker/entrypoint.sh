#!/bin/sh
# Start im Container: Datenordner beschreibbar machen (Volumes der Plattformen gehoeren meist root),
# dann ohne root-Rechte weiter (Benutzer geoim, uid 1000 - so verlangt es auch Hugging Face Spaces).
set -e
DATEN="${GEO_AGENT_ARBEIT:-/data}"
mkdir -p "$DATEN" 2>/dev/null || true
if [ "$(id -u)" = "0" ]; then
  [ "$(stat -c %u "$DATEN")" = "1000" ] || chown -R 1000:1000 "$DATEN"
  exec setpriv --reuid=1000 --regid=1000 --init-groups "$@"
fi
exec "$@"
