[CmdletBinding()]
param(
    [string]$PythonCommand = "python",
    [string]$VirtualEnvironment = ".venv",
    [switch]$SkipInstall,
    [switch]$SkipInfra,
    [switch]$InitializeData
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$ComposeFile = Join-Path $RepoRoot "infra\docker-compose.yml"
$EnvironmentFile = Join-Path $RepoRoot ".env"
$EnvironmentExample = Join-Path $RepoRoot ".env.example"
$VenvRoot = Join-Path $RepoRoot $VirtualEnvironment
$VenvPython = Join-Path $VenvRoot "Scripts\python.exe"
$LockFile = Join-Path $RepoRoot "requirements-dev.lock"

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )

    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $($Arguments -join ' ')"
    }
}

function Resolve-PythonLauncher {
    $command = Get-Command $PythonCommand -ErrorAction SilentlyContinue
    if ($null -ne $command) {
        return @{
            FilePath = $command.Source
            Arguments = @()
        }
    }

    if ($PythonCommand -eq "python") {
        $py = Get-Command "py" -ErrorAction SilentlyContinue
        if ($null -ne $py) {
            return @{
                FilePath = $py.Source
                Arguments = @("-3.12")
            }
        }
    }

    throw "Python 3.12 was not found. Install it or pass -PythonCommand with an executable path."
}

function Assert-Python312 {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [string[]]$Arguments = @()
    )
    $version = & $FilePath @Arguments -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')"
    if ($LASTEXITCODE -ne 0 -or $version.Trim() -ne "3.12") {
        throw "AuRAG requires Python 3.12; detected '$version'."
    }
}

Push-Location $RepoRoot
try {
    Write-Step "Preparing environment configuration"
    if (-not (Test-Path -LiteralPath $EnvironmentFile)) {
        Copy-Item -LiteralPath $EnvironmentExample -Destination $EnvironmentFile
        Write-Warning "Created .env from .env.example. Fill in credentials before initialization or runtime checks."
    }
    else {
        Write-Host ".env already exists; leaving it unchanged."
    }

    if (-not $SkipInstall) {
        Write-Step "Creating or reusing the Python virtual environment"
        if (-not (Test-Path -LiteralPath $VenvRoot)) {
            $launcher = Resolve-PythonLauncher
            Assert-Python312 -FilePath $launcher.FilePath -Arguments $launcher.Arguments
            $uv = Get-Command "uv" -ErrorAction SilentlyContinue
            if ($null -eq $uv) {
                throw "uv was not found. Install uv 0.11 or newer, then rerun bootstrap."
            }
            Invoke-External -FilePath $uv.Source -Arguments @(
                "venv",
                "--python",
                "3.12",
                $VenvRoot
            )
        }
        elseif (-not (Test-Path -LiteralPath $VenvPython)) {
            throw "$VenvRoot exists but does not contain Scripts\python.exe. Move or repair it, then rerun bootstrap."
        }
        else {
            Write-Host "$VirtualEnvironment already exists; reusing it."
        }

        Assert-Python312 -FilePath $VenvPython
        if (-not (Test-Path -LiteralPath $LockFile)) {
            throw "requirements-dev.lock is missing. Regenerate it with uv before bootstrapping."
        }
        $uv = Get-Command "uv" -ErrorAction SilentlyContinue
        if ($null -eq $uv) {
            throw "uv was not found. Install uv 0.11 or newer, then rerun bootstrap."
        }

        Write-Step "Installing locked Python dependencies"
        Invoke-External -FilePath $uv.Source -Arguments @(
            "pip",
            "sync",
            "--python",
            $VenvPython,
            $LockFile
        )

        Write-Step "Installing frontend dependencies with npm ci"
        $npm = Get-Command "npm.cmd" -ErrorAction SilentlyContinue
        if ($null -eq $npm) {
            throw "npm.cmd was not found. Install Node.js 22 or newer."
        }
        $nodeVersion = (& node --version).TrimStart("v").Split(".")
        if ($LASTEXITCODE -ne 0 -or [int]$nodeVersion[0] -lt 22) {
            throw "AuRAG requires Node.js 22 or newer."
        }
        Invoke-External -FilePath $npm.Source -Arguments @("--prefix", "frontend", "ci")
    }
    else {
        Write-Host "Dependency installation skipped."
    }

    if (-not $SkipInfra) {
        Write-Step "Starting Neo4j, Redis, and Qdrant"
        $docker = Get-Command "docker" -ErrorAction SilentlyContinue
        if ($null -eq $docker) {
            throw "Docker was not found. Install Docker Desktop or rerun with -SkipInfra."
        }
        Invoke-External -FilePath $docker.Source -Arguments @(
            "compose",
            "-f",
            $ComposeFile,
            "up",
            "-d",
            "--wait"
        )
    }
    else {
        Write-Host "Infrastructure startup skipped."
    }

    if ($InitializeData) {
        if (-not (Test-Path -LiteralPath $VenvPython)) {
            throw "Data initialization requires $VenvPython. Rerun without -SkipInstall or provide an existing environment."
        }

        Write-Step "Applying the idempotent Neo4j schema and seed"
        Invoke-External -FilePath $VenvPython -Arguments @("-m", "ingestion.loader.load_seed")

        Write-Step "Rebuilding Neo4j and Qdrant chunk indexes"
        Invoke-External -FilePath $VenvPython -Arguments @("-m", "retrieval.index_chunks")
    }
    else {
        Write-Host "Data initialization skipped. Run again with -InitializeData after .env credentials are valid."
    }

    Write-Step "Bootstrap complete"
    Write-Host "Backend:  $VirtualEnvironment\Scripts\python.exe -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000"
    Write-Host "Frontend: npm.cmd --prefix frontend run dev"
    Write-Host "Smoke:    .\scripts\smoke.ps1"
}
finally {
    Pop-Location
}
