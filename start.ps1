param(
    [switch]$Headless,
    [switch]$BackendOnly,
    [switch]$FrontendOnly,
    [switch]$NoBrowser
)

# --- Headless mode ---
if ($Headless -and ($Host.UI.RawUI.WindowTitle -notmatch 'Hidden')) {
    Start-Process pwsh -ArgumentList '-NoProfile', '-File', $PSCommandPath, '-Headless' -WindowStyle Hidden
    exit
}
$WindowStyle = if ($Headless) { 'Hidden' } else { 'Normal' }

$ErrorActionPreference = "Stop"
$RepoRoot = $PSScriptRoot
$ComfyUIPort = 11086
$BackendPort = 11087
$FrontendPort = 11088
$WebRoot = Join-Path $RepoRoot "web_sota"
$HealthEndpoint = "http://127.0.0.1:$BackendPort/health"

Write-Host "=== comfyops-mcp ===" -ForegroundColor Cyan

# --- Prereq check ---
function Require-Command {
    param([string]$Cmd, [string]$WingetId, [string]$Label)
    if (Get-Command $Cmd -ErrorAction SilentlyContinue) { return }
    Write-Host "  $Label not found - installing via winget..." -ForegroundColor Yellow
    if (-not (Get-Command winget -ErrorAction SilentlyContinue)) {
        Write-Host "ERROR: winget unavailable. Install $Label manually." -ForegroundColor Red; exit 1
    }
    winget install --id $WingetId --silent --accept-source-agreements --accept-package-agreements
    $env:PATH = [System.Environment]::GetEnvironmentVariable("PATH","Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("PATH","User")
}

# --- Port zombie kill ---
foreach ($port in @($ComfyUIPort, $BackendPort, $FrontendPort)) {
    Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue | ForEach-Object {
        Write-Host "  Killing zombie on :$port (PID $($_.OwningProcess))" -ForegroundColor Yellow
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
}
Start-Sleep -Milliseconds 500

# --- Frontend deps ---
if (-not $BackendOnly -and -not (Test-Path (Join-Path $WebRoot "node_modules"))) {
    Write-Host "Installing frontend deps..." -ForegroundColor DarkGray
    Push-Location $WebRoot
    npm install
    Pop-Location
}

# --- Start backend ---
if (-not $FrontendOnly) {
    Write-Host "Starting backend on :$BackendPort ..." -ForegroundColor Yellow
    $env:MCP_PORT = "$BackendPort"
    $env:MCP_HOST = "127.0.0.1"
    $backendProc = Start-Process pwsh -NoNewWindow -PassThru -WindowStyle $WindowStyle -ArgumentList @(
        "-NoProfile", "-Command", "uv run python -m comfyops_mcp.server"
    ) -WorkingDirectory $RepoRoot

    $ok = $false
    for ($i = 0; $i -lt 30; $i++) {
        try {
            $r = Invoke-WebRequest -Uri $HealthEndpoint -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
            if ($r.StatusCode -eq 200) { $ok = $true; break }
        } catch {}
        Start-Sleep 1
    }
    if ($ok) {
        Write-Host "Backend ready at $HealthEndpoint" -ForegroundColor Green
    } else {
        Write-Host "WARN: Backend not confirmed after 30s." -ForegroundColor Yellow
    }
}

if ($BackendOnly) {
    Wait-Process -Id $backendProc.Id
    exit
}

# --- Start frontend ---
if (-not $BackendOnly) {
    Write-Host "Starting frontend on :$FrontendPort ..." -ForegroundColor Yellow
    $frontendProc = Start-Process pwsh -NoNewWindow -PassThru -WindowStyle $WindowStyle -ArgumentList @(
        "-NoProfile", "-Command", "npm run dev -- --port $FrontendPort"
    ) -WorkingDirectory $WebRoot
}

# --- Open browser ---
if (-not $NoBrowser -and -not $Headless) {
    Start-Sleep 3
    try { Start-Process "http://127.0.0.1:$FrontendPort" } catch {}
}

Write-Host "=== comfyops-mcp running ===" -ForegroundColor Cyan
Write-Host "ComfyUI   : http://127.0.0.1:$ComfyUIPort"
Write-Host "Backend   : http://127.0.0.1:$BackendPort"
Write-Host "Frontend  : http://127.0.0.1:$FrontendPort"

# Keep alive
try {
    while ($true) {
        Start-Sleep 5
        if ($null -ne $backendProc -and $backendProc.HasExited) {
            Write-Host "Backend exited!" -ForegroundColor Red; break
        }
    }
} finally {
    if ($null -ne $backendProc -and -not $backendProc.HasExited) {
        Stop-Process -Id $backendProc.Id -Force -ErrorAction SilentlyContinue
    }
}
