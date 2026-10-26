@echo off
REM Double-click this file on Windows to start the Titan dashboard.
cd /d "%~dp0"
set PY=python
where python >nul 2>nul || set PY=py
echo.
echo  Checking / installing required libraries (first time takes 1-2 minutes)...
%PY% -m pip install -r requirements.txt
echo.
echo  Starting the Titan dashboard... it will open in your browser.
echo  Keep this window open. Close it to stop the dashboard.
%PY% -m streamlit run app.py --server.headless false
pause
