@echo off
setlocal
cd /d "%~dp0"

call :main > "%~dp0run_log.txt" 2>&1
echo Log written to run_log.txt
pause
exit /b

:main
REM ここに元の中身（pause/endlocalは除く）を置く
where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found.
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating venv...
  python -m venv .venv
)

call ".venv\Scripts\activate.bat"
python -m pip install -U pip
pip install -e .
set PYTHONPATH=%CD%\src
python -m psychrometric.app
exit /b
