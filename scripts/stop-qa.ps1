$ErrorActionPreference = "Stop"
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$qaReceipt = Join-Path $qaRoot "artifacts\manual-qa\processes.json"
if (-not (Test-Path -LiteralPath $qaReceipt)) { Write-Host "No hay registro de una prueba local iniciada."; return }
$qaRecords = Get-Content -LiteralPath $qaReceipt -Raw | ConvertFrom-Json
foreach ($qaEntry in @($qaRecords.processes) | Sort-Object pid -Descending) {
  $qaProcess = Get-Process -Id ([int]$qaEntry.pid) -ErrorAction SilentlyContinue
  if ($qaProcess -and $qaProcess.StartTime.ToUniversalTime().Ticks -eq [long]$qaEntry.startTicks) {
    $qaInfo = Get-CimInstance Win32_Process -Filter "ProcessId = $($qaProcess.Id)"
    if ($qaInfo.CommandLine -notmatch 'tests\.manual\.qa_server|vite\.js.*vite\.qa\.config\.ts') {
      Write-Host "Se omitió un proceso que no coincide con la prueba local."
      continue
    }
    Stop-Process -Id $qaProcess.Id
  }
}
Write-Host "Procesos propios de prueba detenidos. Los datos eran temporales."
