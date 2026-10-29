"""GroundTwin kostenlos im Netz: die App laeuft auf diesem Rechner, ein Cloudflare Quick Tunnel gibt ihr eine
oeffentliche https-Adresse zum Teilen (docs/22_deployment.md). Die Gutachten bleiben auf diesem Rechner.

    python scripts/online.py [--port 8500] [--passwort <wort>] [--arbeit <ordner>]
    start_online.bat                                    (Windows, nach dem ersten start.bat)

Braucht cloudflared (Windows: winget install --id Cloudflare.cloudflared, macOS: brew install cloudflared).
Ohne --passwort / GEO_AGENT_PASSWORT wird ein Passwort erzeugt und angezeigt: ohne Passwort waere jedes Gutachten
fuer alle mit der Adresse offen. Beenden mit Strg+C beendet Server und Tunnel; die Adresse gilt nur bis dahin.
"""
from __future__ import annotations

import argparse
import os
import queue
import re
import secrets
import shutil
import subprocess
import sys
import threading
import time
import urllib.request
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
# Adresse des Quick Tunnels; api.trycloudflare.com steht nur in Fehlermeldungen
URL_MUSTER = re.compile(r"https://(?!api\.)[a-z0-9-]+\.trycloudflare\.com")
WINDOWS_PFADE = (r"C:\Program Files (x86)\cloudflared\cloudflared.exe", r"C:\Program Files\cloudflared\cloudflared.exe")
INSTALLATION = """cloudflared fehlt. Einmal installieren:
  Windows:  winget install --id Cloudflare.cloudflared   (danach ein neues Fenster oeffnen)
  macOS:    brew install cloudflared
  Linux:    https://developers.cloudflare.com/cloudflare-one/networks/connectors/cloudflare-tunnel/downloads/
Oder den Pfad in CLOUDFLARED angeben."""


def cloudflared_finden() -> str | None:
    """cloudflared aus CLOUDFLARED, dem PATH oder dem Windows-Installationsordner."""
    pfad = os.environ.get("CLOUDFLARED") or shutil.which("cloudflared")
    if pfad:
        return pfad
    return next((p for p in WINDOWS_PFADE if Path(p).exists()), None)


def tunnel_url(zeile: str) -> str | None:
    treffer = URL_MUSTER.search(zeile)
    return treffer.group(0) if treffer else None


def passwort_erzeugen() -> str:
    return secrets.token_urlsafe(9)


def antwortet(port: int) -> bool:
    # ohne Proxy: ein Firmen-Proxy aus HTTP_PROXY kennt 127.0.0.1 dieses Rechners nicht
    oeffner = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with oeffner.open(f"http://127.0.0.1:{port}/gesund", timeout=2):
            return True
    except OSError:
        return False


def zeilen_lesen(prozess: subprocess.Popen, ziel: queue.Queue) -> None:
    """Ausgabe von cloudflared laufend leeren (sonst blockiert der Prozess), jede Zeile in die Schlange."""
    for zeile in prozess.stdout:
        ziel.put(zeile.rstrip())
    ziel.put(None)


def beenden(*prozesse: subprocess.Popen | None) -> None:
    for p in prozesse:
        if p is not None and p.poll() is None:
            p.terminate()
    for p in prozesse:
        if p is not None:
            try:
                p.wait(timeout=10)
            except subprocess.TimeoutExpired:
                p.kill()


def main() -> int:
    ap = argparse.ArgumentParser(description="GroundTwin auf diesem Rechner starten und per Cloudflare Tunnel teilen")
    ap.add_argument("--port", type=int, default=8500)
    ap.add_argument("--passwort", help="Passwort fuer den Zugang (sonst GEO_AGENT_PASSWORT oder ein neues)")
    ap.add_argument("--arbeit", type=Path, help="Arbeitsordner der Projekte (wie bei python -m server)")
    args = ap.parse_args()

    cloudflared = cloudflared_finden()
    if not cloudflared:
        print(INSTALLATION)
        return 1
    if antwortet(args.port):
        # z. B. start.bat: dieser Server hat kein Passwort und darf nicht ins Netz
        print(f"Auf Port {args.port} laeuft schon ein Server. Bitte ihn beenden (start.bat schliessen) "
              f"oder einen anderen Port waehlen: --port {args.port + 1}")
        return 1

    umgebung = dict(os.environ)
    passwort = args.passwort or umgebung.get("GEO_AGENT_PASSWORT") or passwort_erzeugen()
    umgebung["GEO_AGENT_PASSWORT"] = passwort
    befehl = [sys.executable, "-m", "server", "--port", str(args.port), "--host", "127.0.0.1", "--kein-browser"]
    if args.arbeit:
        befehl += ["--arbeit", str(args.arbeit)]
    server = subprocess.Popen(befehl, cwd=REPO, env=umgebung)
    tunnel = None
    try:
        ende = time.time() + 120
        while not antwortet(args.port):
            if server.poll() is not None or time.time() > ende:
                print("Der Server ist nicht gestartet (Meldungen oben).")
                return 1
            time.sleep(0.5)

        print("Tunnel wird aufgebaut ...")
        tunnel = subprocess.Popen([cloudflared, "tunnel", "--no-autoupdate", "--url", f"http://127.0.0.1:{args.port}"],
                                  stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, encoding="utf-8",
                                  errors="replace")
        zeilen: queue.Queue = queue.Queue()
        threading.Thread(target=zeilen_lesen, args=(tunnel, zeilen), daemon=True).start()
        url, letzte, ende = None, [], time.time() + 90
        while url is None and time.time() < ende:
            try:
                zeile = zeilen.get(timeout=1)
            except queue.Empty:
                continue
            if zeile is None:
                break
            letzte = (letzte + [zeile])[-8:]
            url = tunnel_url(zeile)
        if url is None:
            print("Kein Tunnel. Letzte Meldungen von cloudflared:")
            print("\n".join(letzte) or "(keine)")
            return 1

        print("\n" + "=" * 72)
        print(f"  GroundTwin ist online:  {url}")
        print(f"  Benutzer: beliebig      Passwort: {passwort}")
        print("  Adresse und Passwort nur an Personen geben, die die Gutachten sehen duerfen.")
        print("  Die Adresse gilt bis Strg+C; beim naechsten Start gibt es eine neue.")
        print(f"  Auf diesem Rechner weiter: http://localhost:{args.port}")
        print("=" * 72 + "\n", flush=True)

        while server.poll() is None and tunnel.poll() is None:
            try:
                zeile = zeilen.get(timeout=1)
            except queue.Empty:
                continue
            if zeile and " ERR " in zeile:
                print(zeile, flush=True)
        print("Server oder Tunnel wurde beendet.")
        return 1
    except KeyboardInterrupt:
        print("\nBeendet: GroundTwin ist nicht mehr online.")
        return 0
    finally:
        beenden(tunnel, server)


if __name__ == "__main__":
    sys.exit(main())
