"""Kostenloser Weg ins Netz (scripts/online.py, docs/22_deployment.md): Tunnel-Adresse erkennen, cloudflared finden,
und der ganze Ablauf mit einem nachgebauten cloudflared (Server mit Passwort, Adresse angezeigt, Strg+C beendet alles)."""
from __future__ import annotations

import base64
import os
import re
import signal
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "scripts"))
import online  # noqa: E402


def test_tunnel_url_aus_der_ausgabe_von_cloudflared():
    zeile = "2026-10-29T10:00:02Z INF |  https://seasonal-deck-organisms-sf.trycloudflare.com          |"
    assert online.tunnel_url(zeile) == "https://seasonal-deck-organisms-sf.trycloudflare.com"
    # Fehlermeldungen nennen die API von Cloudflare: das ist keine Adresse zum Teilen
    assert online.tunnel_url('ERR failed to request quick Tunnel: Post "https://api.trycloudflare.com/tunnel": EOF') is None
    assert online.tunnel_url("INF Requesting new quick Tunnel on trycloudflare.com...") is None
    assert online.tunnel_url("INF terms: https://www.cloudflare.com/website-terms/") is None


def test_cloudflared_aus_der_umgebung(monkeypatch, tmp_path):
    monkeypatch.setenv("CLOUDFLARED", str(tmp_path / "cloudflared"))
    assert online.cloudflared_finden() == str(tmp_path / "cloudflared")


def test_passwort_jedes_mal_neu():
    a, b = online.passwort_erzeugen(), online.passwort_erzeugen()
    assert a != b and len(a) >= 12


def freier_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def status(port: int, passwort: str | None = None) -> int:
    anfrage = urllib.request.Request(f"http://127.0.0.1:{port}/api/info")
    if passwort:
        anfrage.add_header("Authorization", "Basic " + base64.b64encode(f"x:{passwort}".encode()).decode())
    oeffner = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with oeffner.open(anfrage, timeout=5) as antwort:
            return antwort.status
    except urllib.error.HTTPError as fehler:
        return fehler.code


@pytest.mark.skipif(sys.platform == "win32", reason="nachgebautes cloudflared ist ein Shell-Skript")
def test_ganzer_ablauf_mit_nachgebautem_cloudflared(tmp_path):
    pytest.importorskip("fastapi")
    cloudflared = tmp_path / "cloudflared"
    cloudflared.write_text("#!/bin/sh\n"
                           "echo 'INF Requesting new quick Tunnel on trycloudflare.com...'\n"
                           "echo 'INF |  https://probe-tunnel-abc.trycloudflare.com      |'\n"
                           "exec sleep 300\n")
    cloudflared.chmod(0o755)
    port = freier_port()
    umgebung = {k: v for k, v in os.environ.items() if k != "GEO_AGENT_PASSWORT"}
    umgebung["CLOUDFLARED"] = str(cloudflared)
    prozess = subprocess.Popen([sys.executable, str(REPO / "scripts" / "online.py"), "--port", str(port),
                                "--arbeit", str(tmp_path / "arbeit")],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=umgebung)
    ausgabe: list[str] = []
    threading.Thread(target=lambda: ausgabe.extend(prozess.stdout), daemon=True).start()
    try:
        ende = time.time() + 120
        while not any("Passwort:" in z for z in ausgabe) and time.time() < ende and prozess.poll() is None:
            time.sleep(0.2)
        text = "".join(ausgabe)
        assert "https://probe-tunnel-abc.trycloudflare.com" in text, text
        passwort = re.search(r"Passwort: (\S+)", text).group(1)
        # der Server hinter dem Tunnel verlangt das angezeigte Passwort
        assert status(port) == 401
        assert status(port, passwort) == 200
        prozess.send_signal(signal.SIGINT)
        assert prozess.wait(timeout=30) == 0
        # Server und Tunnel sind mit beendet
        ende = time.time() + 15
        while status_oder_none(port) is not None and time.time() < ende:
            time.sleep(0.2)
        assert status_oder_none(port) is None
    finally:
        if prozess.poll() is None:
            prozess.kill()


def status_oder_none(port: int) -> int | None:
    try:
        return status(port)
    except OSError:
        return None
