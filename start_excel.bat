@echo off
REM Excel nach Vorlage (v1, Streamlit): http://localhost:8501. Erst einmal start.bat ausfuehren (legt .venv an).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Bitte zuerst start.bat ausfuehren.
  pause
  exit /b 1
)
start "" /b cmd /c "timeout /t 5 /nobreak >nul & start http://localhost:8501"
".venv\Scripts\python" -m streamlit run app.py --server.headless true --server.port 8501
pause
