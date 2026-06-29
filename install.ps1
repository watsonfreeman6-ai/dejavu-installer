# Dejavu — AI Skills Marketplace Installer (Windows)
# MIT Licensed. Installs the Dejavu MCP server config.
# The server and catalog are proprietary. This installer is open-source.
#
# Usage (PowerShell):
#   irm https://dejavu.dev/install.ps1 | iex
#   (Do NOT double-click — PowerShell blocks .ps1 by default)

Write-Host "Dejavu — AI Skills Marketplace" -ForegroundColor Cyan
Write-Host "----------------------------------------"

# ── API Key ──────────────────────────────────────────────
$apiKey = $env:DEJAVU_API_KEY
if (-not $apiKey) {
    $apiKey = Read-Host "Enter your Dejavu API key (dk_xxx)"
}
if (-not $apiKey) {
    Write-Host "API key required. Get one at https://dejavu.dev/connect" -ForegroundColor Red
    exit 1
}

# ── Install uv ───────────────────────────────────────────
$uvPath = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvPath) {
    Write-Host "Installing uv (Python package manager)..."
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    $env:Path = "$env:USERPROFILE\.local\bin;$env:Path"
}
Write-Host "✓ uv ready" -ForegroundColor Green

# ── Create ~/.dejavu + device_id ─────────────────────────
$dejavuHome = Join-Path $env:USERPROFILE ".dejavu"
New-Item -ItemType Directory -Force -Path $dejavuHome | Out-Null

$deviceIdPath = Join-Path $dejavuHome "device_id"
if (-not (Test-Path $deviceIdPath)) {
    $deviceId = [guid]::NewGuid().ToString()
    Set-Content -Path $deviceIdPath -Value $deviceId
}
Write-Host "✓ Device registered" -ForegroundColor Green

# ── Download catalog ─────────────────────────────────────
$catalogUrl = "https://github.com/dejavu-app/install/releases/latest/download/catalog.db"
$catalogPath = Join-Path $dejavuHome "catalog.db"
Write-Host "Downloading skill catalog..."
try {
    Invoke-WebRequest -Uri $catalogUrl -OutFile $catalogPath -ErrorAction Stop
    Write-Host "✓ Catalog downloaded" -ForegroundColor Green
} catch {
    Write-Host "⚠ Catalog not available yet — will be seeded on first use" -ForegroundColor Yellow
}

# ── Store API key ────────────────────────────────────────
$configPath = Join-Path $dejavuHome "config.json"
$config = @{}
if (Test-Path $configPath) {
    $config = Get-Content $configPath | ConvertFrom-Json | ConvertTo-Hashtable -Depth 5
}
$config["api_key"] = $apiKey
$config | ConvertTo-Json -Depth 3 | Set-Content $configPath
Write-Host "✓ API key saved" -ForegroundColor Green

# ── Detect clients ───────────────────────────────────────
Write-Host "Detecting MCP clients..."

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
if (-not $scriptDir) { $scriptDir = (Get-Location).Path }

$clientsJson = python3 -c @"
import sys, json
sys.path.insert(0, '$scriptDir\\src')
from client_detector import detect_clients
print(json.dumps(detect_clients()))
"@ 2>$null

if (-not $clientsJson) {
    $clientsJson = "{}"
}

$clients = $clientsJson | ConvertFrom-Json

# ── Write configs ────────────────────────────────────────
$configured = 0
foreach ($client in $clients.PSObject.Properties) {
    $name = $client.Name
    $path = $client.Value
    
    if ($name -eq "claude") {
        Write-Host "ℹ  Claude Desktop: open Settings → Connectors → paste URL + key"
        continue
    }
    
    try {
        $result = python3 -c @"
import sys
sys.path.insert(0, '$scriptDir\\src')
from config_writer import write_config
print(write_config('$path', '$name'))
"@ 2>$null
        if ($result -eq "True") {
            $configured++
            Write-Host "✓ Configured $name" -ForegroundColor Green
        } else {
            Write-Host "  $name already configured — skipped"
        }
    } catch {
        Write-Host "✗ Failed to configure $name" -ForegroundColor Red
    }
}

# ── Set env var ──────────────────────────────────────────
if ($configured -gt 0) {
    try {
        [Environment]::SetEnvironmentVariable("DEJAVU_API_KEY", $apiKey, "User")
        Write-Host "✓ DEJAVU_API_KEY set (effective in new shells)" -ForegroundColor Green
    } catch {
        Write-Host "⚠ Could not set env var" -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "Dejavu installed!" -ForegroundColor Green
Write-Host ""
Write-Host "Your AI agent now has access to:"
Write-Host "  skill_search  — local FTS5, sub-ms, always free"
Write-Host "  skill_execute — gated, content cached locally"
Write-Host "  skill_submit  — share your own skills"
Write-Host ""
Write-Host "Manage devices: https://dejavu.dev/dashboard"

# Helper function for PowerShell < v6
function ConvertTo-Hashtable {
    param([Parameter(ValueFromPipeline)] $InputObject)
    process {
        if ($null -eq $InputObject) { return $null }
        if ($InputObject -is [System.Collections.IEnumerable] -and $InputObject -isnot [string]) {
            $collection = @(
                foreach ($object in $InputObject) {
                    if ($object -is [System.Management.Automation.PSCustomObject]) {
                        ConvertTo-Hashtable $object
                    } else {
                        $object
                    }
                }
            )
            return $collection
        }
        if ($InputObject -is [System.Management.Automation.PSCustomObject]) {
            $hash = @{}
            foreach ($property in $InputObject.PSObject.Properties) {
                $hash[$property.Name] = ConvertTo-Hashtable $property.Value
            }
            return $hash
        }
        return $InputObject
    }
}
