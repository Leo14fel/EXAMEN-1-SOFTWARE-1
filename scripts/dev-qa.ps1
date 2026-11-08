$ErrorActionPreference = "Stop"
$qaRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$qaBackend = Join-Path $qaRoot "backend"
$qaFrontend = Join-Path $qaRoot "frontend"
$qaPython = Join-Path $qaBackend ".venv\Scripts\python.exe"
$qaNode = (Get-Command node -ErrorAction Stop).Source

foreach ($qaPort in @(8001, 5175)) {
  $qaSocket = [Net.Sockets.TcpClient]::new()
  try {
    $qaConnect = $qaSocket.ConnectAsync("127.0.0.1", $qaPort)
    try { [void]$qaConnect.Wait(500) } catch { }
    if ($qaSocket.Connected) { throw "Puerto $qaPort ocupado. No se detuvo ningún proceso existente." }
  } finally { $qaSocket.Dispose() }
}

$qaLogs = Join-Path $qaRoot "artifacts\manual-qa"
New-Item -ItemType Directory -Force -Path $qaLogs | Out-Null
$qaStamp = [DateTime]::UtcNow.ToString("yyyyMMddTHHmmssfffZ")
$qaBackendProcess = Start-Process -FilePath $qaPython -ArgumentList @("-m", "tests.manual.qa_server") -WorkingDirectory $qaBackend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $qaLogs "$qaStamp-backend.out.log") -RedirectStandardError (Join-Path $qaLogs "$qaStamp-backend.err.log")
$qaFrontendProcess = Start-Process -FilePath $qaNode -ArgumentList @(".\node_modules\vite\bin\vite.js", "--config", "vite.qa.config.ts") -WorkingDirectory $qaFrontend -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $qaLogs "$qaStamp-frontend.out.log") -RedirectStandardError (Join-Path $qaLogs "$qaStamp-frontend.err.log")

$qaRecords = @()
foreach ($qaProcess in @($qaBackendProcess, $qaFrontendProcess)) {
  $qaRecords += @{ pid = $qaProcess.Id; startTicks = $qaProcess.StartTime.ToUniversalTime().Ticks }
}
# Record verified direct children as well (Windows venv Python may forward to base Python).
Start-Sleep -Milliseconds 1200
foreach ($qaProcess in @($qaBackendProcess, $qaFrontendProcess)) {
  foreach ($qaChild in @(Get-CimInstance Win32_Process -Filter "ParentProcessId = $($qaProcess.Id)" -ErrorAction SilentlyContinue)) {
    $qaChildProcess = Get-Process -Id $qaChild.ProcessId -ErrorAction SilentlyContinue
    if ($qaChildProcess) { $qaRecords += @{ pid = $qaChildProcess.Id; startTicks = $qaChildProcess.StartTime.ToUniversalTime().Ticks } }
  }
}
@{ startedUtc = [DateTime]::UtcNow.ToString("o"); processes = $qaRecords; ports = @(8001,5175) } | ConvertTo-Json -Depth 4 | Set-Content -LiteralPath (Join-Path $qaLogs "processes.json") -Encoding utf8
Write-Host "Prueba local: http://localhost:5175"
Write-Host "Backend temporal: http://localhost:8001/health/db"
Write-Host "Datos temporales. No es Atlas. Para detener: .\scripts\stop-qa.ps1"
