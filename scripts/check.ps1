$ErrorActionPreference = "Stop"

function Invoke-Check {
  param([string]$Description, [scriptblock]$Command)

  Write-Host $Description
  & $Command
  if ($LASTEXITCODE -ne 0) {
    throw "$Description fallo con codigo de salida $LASTEXITCODE."
  }
}

Push-Location backend
try {
  Invoke-Check "Backend tests..." { & .\.venv\Scripts\python.exe -m pytest }
  Invoke-Check "Backend compileall..." { & .\.venv\Scripts\python.exe -m compileall app }
  Invoke-Check "Backend Ruff..." { & .\.venv\Scripts\python.exe -m ruff check . }
  Invoke-Check "Backend pip check..." { & .\.venv\Scripts\python.exe -m pip check }
} finally {
  Pop-Location
}

Push-Location frontend
try {
  Invoke-Check "Frontend typecheck..." { npm run typecheck }
  Invoke-Check "Frontend tests..." { npm test }
  Invoke-Check "Frontend build..." { npm run build }
} finally {
  Pop-Location
}

Write-Host "Todos los checks terminaron correctamente."
