@echo off
REM Geo_Agent starten (Windows): Doppelklick oder "start.bat" in der Eingabeaufforderung.
REM Baugrundmodell-App (Schritt-App im Browser): http://localhost:8500 - der Browser oeffnet sich selbst.
REM Beim ersten Start wird .venv angelegt und alles installiert (einige Minuten).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Erste Einrichtung: virtuelle Umgebung .venv ...
  py -3 -m venv .venv 2>nul || python -m venv .venv
  if not exist ".venv\Scripts\python.exe" (
    echo Python 3.10 oder neuer wird gebraucht: https://www.python.org/downloads/
    pause
    exit /b 1
  )
  ".venv\Scripts\python" -m pip install --upgrade pip
  ".venv\Scripts\python" -m pip install -r requirements.txt || (pause & exit /b 1)
  ".venv\Scripts\python" -m pip install -r requirements-ocr.txt || echo OCR nicht installiert: Scans werden nicht gelesen.
)
REM fehlende Pakete einer neueren Version nachinstallieren (z. B. fastapi nach einem Update)
".venv\Scripts\python" -c "import fastapi, uvicorn, multipart" 2>nul || ".venv\Scripts\python" -m pip install -r requirements.txt
".venv\Scripts\python" -m server --port 8500
pause
