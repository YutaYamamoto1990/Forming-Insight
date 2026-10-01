param(
    [Parameter(Mandatory = $true)][string]$ComputeExe,
    [ValidateRange(1024, 65535)][int]$Port = 6500,
    [ValidateRange(1, 86400)][int]$ServerTimeoutSeconds = 660,
    [string]$ProcessId,
    [string]$ConfigFile
)

$ErrorActionPreference = 'Stop'
$agentRoot = Split-Path $PSScriptRoot -Parent
if ($ProcessId) {
    if ($ProcessId -notmatch '^[a-z0-9][a-z0-9-]*$') { throw 'Invalid process id' }
    $definition = Get-Content -LiteralPath (Join-Path $agentRoot "processes/$ProcessId/process.json") -Raw | ConvertFrom-Json
    if (-not $ConfigFile) { $ConfigFile = Join-Path $agentRoot 'config/user-config.json' }
    $configuration = Get-Content -LiteralPath $ConfigFile -Raw | ConvertFrom-Json
    $clientTimeout = 600
    if ($null -ne $configuration.timeout_seconds) { $clientTimeout = $configuration.timeout_seconds }
    if ($null -ne $definition.timeout_seconds) { $clientTimeout = $definition.timeout_seconds }
    if ($null -ne $configuration.processes.$ProcessId.timeout_seconds) { $clientTimeout = $configuration.processes.$ProcessId.timeout_seconds }
    if ($clientTimeout -is [bool] -or $clientTimeout -le 0) { throw 'Invalid client timeout' }
    $requiredTimeout = [int][math]::Ceiling($clientTimeout + 60)
    if ($PSBoundParameters.ContainsKey('ServerTimeoutSeconds') -and $ServerTimeoutSeconds -lt $requiredTimeout) { throw 'Server timeout must exceed process timeout by at least 60 seconds' }
    $ServerTimeoutSeconds = [math]::Max($ServerTimeoutSeconds, $requiredTimeout)
}
$computePath = (Resolve-Path -LiteralPath $ComputeExe).Path
if ([IO.Path]::GetFileName($computePath) -ne 'rhino.compute.exe') {
    throw 'Specify the installed Rhino 8 Hops rhino.compute.exe.'
}
$listener = [Net.Sockets.TcpListener]::new([Net.IPAddress]::Loopback, $Port)
try { $listener.Start() } finally { $listener.Stop() }
$serviceId = (Get-Date -Format 'yyyyMMdd-HHmmss') + '-' + ([guid]::NewGuid().ToString('N').Substring(0, 8))
$serviceRoot = Join-Path $agentRoot ('workspace/services/' + $serviceId)
New-Item -ItemType Directory -Path $serviceRoot | Out-Null
$logRoot = Join-Path $serviceRoot 'logs'
New-Item -ItemType Directory -Path $logRoot | Out-Null
$previousTimeout = $env:RHINO_COMPUTE_TIMEOUT
$previousLogPath = $env:RHINO_COMPUTE_LOG_PATH
try {
    # Process-scoped only. Do not modify the user's machine or profile settings.
    $env:RHINO_COMPUTE_TIMEOUT = [string]$ServerTimeoutSeconds
    $env:RHINO_COMPUTE_LOG_PATH = $logRoot
    $computeProcess = Start-Process -FilePath $computePath -ArgumentList @('--port', $Port, '--childcount', '1', '--spawn-on-startup') -WorkingDirectory $serviceRoot -WindowStyle Hidden -PassThru -RedirectStandardOutput (Join-Path $logRoot 'stdout.log') -RedirectStandardError (Join-Path $logRoot 'stderr.log')
} finally {
    $env:RHINO_COMPUTE_TIMEOUT = $previousTimeout
    $env:RHINO_COMPUTE_LOG_PATH = $previousLogPath
}
$state = [ordered]@{
    pid = $computeProcess.Id
    url = 'http://localhost:' + $Port
    started_at = $computeProcess.StartTime.ToString('o')
    server_timeout_seconds = $ServerTimeoutSeconds
    status = 'starting'
    logs = $logRoot
}
$state | ConvertTo-Json | Set-Content -LiteralPath (Join-Path $serviceRoot 'server.json') -Encoding utf8
$state | ConvertTo-Json
# This starts the service; it does not claim that Rhino or Grasshopper is ready.
