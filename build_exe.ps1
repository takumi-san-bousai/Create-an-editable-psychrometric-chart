$ErrorActionPreference = "Stop"

# Use available Python
$PY = (Get-Command python3.13 -ErrorAction SilentlyContinue).Source
if (-not $PY) {
  $PY = (Get-Command python -ErrorAction SilentlyContinue).Source
}
if (-not $PY) {
  throw "Python not found. Install Python 3.10+ and ensure 'python' is in PATH."
}

# venv
if (!(Test-Path ".\.venv")) {
  & $PY -m venv .venv
}
.\.venv\Scripts\activate

python -m pip install -U pip
python -m pip install -U pyinstaller

# install project
pip install -e .

# build exe
pyinstaller `
  --noconfirm `
  --clean `
  --name psychrimetric `
  --onefile `
  --windowed `
  -m psychrimetric.app

Write-Host ""
Write-Host "Built: dist\psychrimetric.exe"
