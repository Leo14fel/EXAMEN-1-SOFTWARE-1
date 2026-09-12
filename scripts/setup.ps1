$ErrorActionPreference = "Stop"
$repoRoot = Join-Path $PSScriptRoot ".."

Write-Host "[1/2] Preparando backend..."
Push-Location (Join-Path $repoRoot "backend")
try {
  if (-not (Test-Path ".venv")) {
    python -m venv .venv
  }
  & .\.venv\Scripts\python.exe -m pip install --upgrade pip
  & .\.venv\Scripts\python.exe -m pip install -e ".[dev]"
  if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
} finally {
  Pop-Location
}

Write-Host "[2/2] Preparando frontend..."
Push-Location (Join-Path $repoRoot "frontend")
try {
  npm install
  if (-not (Test-Path ".env")) { Copy-Item ".env.example" ".env" }
} finally {
  Pop-Location
}

Write-Host "Setup terminado. PostgreSQL local en localhost:5432 es la configuracion de desarrollo; Docker Compose es opcional."
