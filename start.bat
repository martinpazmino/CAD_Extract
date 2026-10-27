@echo off
REM Geo_Agent starten (Windows): Doppelklick oder "start.bat" in der Eingabeaufforderung.
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
REM headless: keine E-Mail-Abfrage beim ersten Start; der Browser oeffnet sich nach ein paar Sekunden
start "" /b cmd /c "timeout /t 5 /nobreak >nul & start http://localhost:8501"
".venv\Scripts\python" -m streamlit run app.py --server.headless true --server.port 8501
pause
