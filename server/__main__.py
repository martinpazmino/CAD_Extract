"""Baugrundmodell-App starten: python -m server [--port 8500] [--host 127.0.0.1] [--kein-browser] [--arbeit <ordner>].

Im Netz (Container, docs/22): GEO_AGENT_HOST und PORT aus der Umgebung, GEO_AGENT_ARBEIT fuer den Datenordner,
GEO_AGENT_PASSWORT verlangt eine Anmeldung (HTTP Basic) fuer alles ausser /gesund."""
from __future__ import annotations

import argparse
import os
import sys
import threading
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> None:
    ap = argparse.ArgumentParser(description="GeoIM – Baugrundmodell aus dem Bodengutachten")
    ap.add_argument("--port", type=int, default=int(os.environ.get("PORT") or 8500))
    ap.add_argument("--host", default=os.environ.get("GEO_AGENT_HOST") or "127.0.0.1")
    ap.add_argument("--kein-browser", action="store_true", help="Browser nicht oeffnen")
    ap.add_argument("--arbeit", type=Path, help="Arbeitsordner (Projekte, Zwischenablage); Standard: Temp/geo_agent")
    args = ap.parse_args()

    import uvicorn

    from server.api import app_erstellen

    app = app_erstellen(args.arbeit)
    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}"
    print(f"GeoIM laeuft auf {url}  (Beenden: Strg+C)")
    if args.host not in ("127.0.0.1", "localhost") and not os.environ.get("GEO_AGENT_PASSWORT"):
        print("Achtung: im Netz erreichbar, aber ohne GEO_AGENT_PASSWORT - jeder kann Gutachten sehen und aendern.")
    if not args.kein_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
