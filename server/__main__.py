"""Baugrundmodell-App starten: python -m server [--port 8500] [--kein-browser] [--arbeit <ordner>]."""
from __future__ import annotations

import argparse
import sys
import threading
import webbrowser
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def main() -> None:
    ap = argparse.ArgumentParser(description="Geo_Agent – Baugrundmodell aus dem Bodengutachten")
    ap.add_argument("--port", type=int, default=8500)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--kein-browser", action="store_true", help="Browser nicht oeffnen")
    ap.add_argument("--arbeit", type=Path, help="Arbeitsordner (Projekte, Zwischenablage); Standard: Temp/geo_agent")
    args = ap.parse_args()

    import uvicorn

    from server.api import app_erstellen

    app = app_erstellen(args.arbeit)
    url = f"http://{'localhost' if args.host in ('127.0.0.1', '0.0.0.0') else args.host}:{args.port}"
    print(f"Geo_Agent laeuft auf {url}  (Beenden: Strg+C)")
    if not args.kein_browser:
        threading.Timer(1.5, lambda: webbrowser.open(url)).start()
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
