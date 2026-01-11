@echo off
setlocal

cd /d "%~dp0"

REM 1) Python check
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found. Please install Python 3.10+ from python.org (check "Add to PATH").
  pause
  exit /b 1
)

REM 2) venv create if missing
if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating venv...
  python -m venv .venv
)

REM 3) activate + install deps (idempotent)
call ".venv\Scripts\activate.bat"
python -m pip install -U pip >nul
pip install -e . 

REM 4) run app (GUI)
set PYTHONPATH=%CD%\src
python -m psychrometric.app

pause
endlocal
