@echo off
setlocal
cd /d "%~dp0"
python Real_Test.py
if errorlevel 1 (
  echo.
  echo Could not start the application. Install Python and run:
  echo python -m pip install -r requirements.txt
  pause
)
