@echo off
REM GroundTwin kostenlos im Netz (docs/22_deployment.md): die App laeuft auf diesem Rechner, Cloudflare gibt ihr eine
REM https-Adresse zum Teilen. Die Gutachten bleiben hier. Das Fenster zeigt Adresse und Passwort; Strg+C beendet.
REM Einmalig vorher: start.bat ausfuehren (installiert alles) und cloudflared installieren:
REM   winget install --id Cloudflare.cloudflared
REM Eigenes Passwort statt eines neuen bei jedem Start:  start_online.bat --passwort MeinPasswort
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Bitte zuerst start.bat ausfuehren: es richtet Python und die Pakete ein.
  pause
  exit /b 1
)
".venv\Scripts\python" scripts\online.py %*
pause
