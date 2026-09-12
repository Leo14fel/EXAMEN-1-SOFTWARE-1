$ErrorActionPreference = "Stop"

Write-Host "Backend tests..."
Push-Location backend
& .\.venv\Scripts\python.exe -m pytest
& .\.venv\Scripts\python.exe -m compileall app
Pop-Location

Write-Host "Frontend checks..."
Push-Location frontend
npm run typecheck
npm run test
npm run build
Pop-Location

Write-Host "Todos los checks terminaron correctamente."
