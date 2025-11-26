<#
.SYNOPSIS
    Nyx-OSINT Guided Setup Script for Windows

.DESCRIPTION
    Interactive installation and configuration wizard for Nyx-OSINT platform.
    Handles dependency installation, environment configuration, and database setup.

.PARAMETER Auto
    Run in automated mode without prompts

.PARAMETER ShowVerbose
    Enable verbose output for debugging

.PARAMETER SkipDeps
    Skip dependency installation

.PARAMETER SkipDb
    Skip database initialization

.PARAMETER Config
    Path to configuration file

.EXAMPLE
    .\setup.ps1
    Run interactive setup

.EXAMPLE
    .\setup.ps1 -Auto -ShowVerbose
    Run automated setup with verbose output

.NOTES
    Version: 1.0.0
    Requires: PowerShell 5.1+, Administrator privileges (for some operations)
#>

[CmdletBinding()]
param(
    [switch]$Auto,
    [switch]$ShowVerbose,
    [switch]$SkipDeps,
    [switch]$SkipDb,
    [string]$Config = ""
)

#Requires -Version 5.1

###############################################################################
# CONFIGURATION
###############################################################################

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

$SCRIPT_DIR = Split-Path -Parent $MyInvocation.MyCommand.Path
$LOG_FILE = Join-Path $SCRIPT_DIR "setup.log"
$BACKUP_DIR = Join-Path $SCRIPT_DIR ".setup_backup"
$REQUIRED_PYTHON_VERSION = [Version]"3.12.0"
$SETUP_CONFIG = Join-Path $SCRIPT_DIR ".setup.conf"

# State tracking
$script:ROLLBACK_STEPS = @()
$script:CHECKS_PASSED = 0
$script:CHECKS_TOTAL = 0

###############################################################################
# UTILITY FUNCTIONS
###############################################################################

function Write-Log {
    param([string]$Message)
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "[$timestamp] $Message" | Out-File -Append -FilePath $LOG_FILE -Encoding UTF8
}

function Write-Info {
    param([string]$Message)
    Write-Host "ℹ " -ForegroundColor Blue -NoNewline
    Write-Host $Message
    Write-Log "INFO: $Message"
}

function Write-Success {
    param([string]$Message)
    Write-Host "✓ " -ForegroundColor Green -NoNewline
    Write-Host $Message
    Write-Log "SUCCESS: $Message"
}

function Write-Warning {
    param([string]$Message)
    Write-Host "⚠ " -ForegroundColor Yellow -NoNewline
    Write-Host $Message
    Write-Log "WARNING: $Message"
}

function Write-Error {
    param([string]$Message)
    Write-Host "✗ " -ForegroundColor Red -NoNewline
    Write-Host $Message
    Write-Log "ERROR: $Message"
}

function Write-Fatal {
    param([string]$Message)
    Write-Error $Message
    Write-Error "Setup failed. Check $LOG_FILE for details."
    Invoke-Cleanup
    exit 1
}

function Write-VerboseLog {
    param([string]$Message)
    if ($ShowVerbose) {
        Write-Host "[VERBOSE] " -ForegroundColor Cyan -NoNewline
        Write-Host $Message
        Write-Log "VERBOSE: $Message"
    }
}

###############################################################################
# PROGRESS INDICATORS
###############################################################################

function Write-ProgressBar {
    param(
        [int]$Current,
        [int]$Total,
        [string]$Activity = "Processing"
    )

    $percentComplete = ($Current / $Total) * 100
    Write-Progress -Activity $Activity -PercentComplete $percentComplete -Status "$Current of $Total"
}

###############################################################################
# CLEANUP & ROLLBACK
###############################################################################

function Add-RollbackStep {
    param([scriptblock]$Step)
    $script:ROLLBACK_STEPS += $Step
    Write-VerboseLog "Added rollback step"
}

function Invoke-Cleanup {
    Write-Warning "Rolling back changes..."

    for ($i = $script:ROLLBACK_STEPS.Count - 1; $i -ge 0; $i--) {
        try {
            Write-VerboseLog "Executing rollback step $($i + 1)"
            & $script:ROLLBACK_STEPS[$i]
        }
        catch {
            Write-VerboseLog "Rollback step failed: $_"
        }
    }

    Write-Success "Rollback completed"
}

###############################################################################
# SYSTEM DETECTION
###############################################################################

function Test-Administrator {
    $currentUser = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($currentUser)
    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}

function Test-Command {
    param([string]$Command)
    $null -ne (Get-Command $Command -ErrorAction SilentlyContinue)
}

function Get-PythonVersion {
    try {
        if (Test-Command python) {
            $output = python --version 2>&1 | Out-String
            if ($output -match "Python (\d+\.\d+)\.(\d+)") {
                $major = $matches[1]
                $patch = $matches[2]
                return [PSCustomObject]@{
                    Version = [Version]"$major.$patch"
                    Major = $major
                    IsValid = $major -eq "3.12"
                }
            }
        }
        return [PSCustomObject]@{
            Version = [Version]"0.0.0"
            Major = "0.0"
            IsValid = $false
        }
    }
    catch {
        return [PSCustomObject]@{
            Version = [Version]"0.0.0"
            Major = "0.0"
            IsValid = $false
        }
    }
}

###############################################################################
# USER INTERACTION
###############################################################################

function Read-YesNo {
    param(
        [string]$Prompt,
        [bool]$Default = $false
    )

    if ($Auto) {
        return $Default
    }

    $defaultText = if ($Default) { "[Y/n]" } else { "[y/N]" }

    while ($true) {
        $response = Read-Host "? $Prompt $defaultText"

        if ([string]::IsNullOrWhiteSpace($response)) {
            return $Default
        }

        switch -Regex ($response) {
            '^[Yy]' { return $true }
            '^[Nn]' { return $false }
            default { Write-Warning "Please answer yes or no." }
        }
    }
}

function Read-Input {
    param(
        [string]$Prompt,
        [string]$Default
    )

    if ($Auto) {
        return $Default
    }

    $response = Read-Host "? $Prompt [$Default]"

    if ([string]::IsNullOrWhiteSpace($response)) {
        return $Default
    }

    return $response
}

###############################################################################
# DEPENDENCY CHECKS
###############################################################################

function Test-Python {
    Write-Info "Checking Python installation..."

    $pythonInfo = Get-PythonVersion

    if ($pythonInfo.Version -eq [Version]"0.0.0") {
        Write-Warning "Python not found"
        return $false
    }

    if (-not $pythonInfo.IsValid) {
        Write-Warning "Python $($pythonInfo.Major) found, but Python 3.12 is required"
        Write-Host ""
        Write-Host "  Nyx-OSINT requires Python 3.12 specifically due to package compatibility." -ForegroundColor Yellow
        Write-Host "  Python 3.14 is too new and breaks several dependencies (e.g., Pillow)." -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Solution:" -ForegroundColor Cyan
        Write-Host "    1. Install Python 3.12 from: https://www.python.org/downloads/" -ForegroundColor White
        Write-Host "    2. Configure Poetry to use Python 3.12:" -ForegroundColor White
        Write-Host "       poetry env use python3.12" -ForegroundColor Gray
        Write-Host ""
        return $false
    }

    Write-Success "Python $($pythonInfo.Version) found"
    return $true
}

function Install-Python {
    Write-Info "Installing Python $REQUIRED_PYTHON_VERSION..."

    # Check if winget is available
    if (Test-Command winget) {
        try {
            winget install Python.Python.3.12 --silent --accept-package-agreements --accept-source-agreements

            # Refresh environment variables
            $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path", "User")

            if (Test-Python) {
                Write-Success "Python installed successfully"
                return
            }
        }
        catch {
            Write-Warning "Winget installation failed: $_"
        }
    }

    # Fallback to manual download
    Write-Info "Please download and install Python from: https://www.python.org/downloads/"
    Write-Info "Make sure to check 'Add Python to PATH' during installation"

    if (Read-YesNo "Have you installed Python?" $false) {
        if (-not (Test-Python)) {
            Write-Fatal "Python installation verification failed"
        }
    }
    else {
        Write-Fatal "Python is required to continue"
    }
}

function Test-Poetry {
    Write-Info "Checking Poetry installation..."

    if (Test-Command poetry) {
        $poetryVersion = (poetry --version 2>&1 | Select-String -Pattern "\d+\.\d+\.\d+").Matches.Value
        Write-Success "Poetry $poetryVersion found"
        return $true
    }
    else {
        Write-Warning "Poetry not found"
        return $false
    }
}

function Install-Poetry {
    Write-Info "Installing Poetry..."

    try {
        (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

        # Add Poetry to PATH
        $poetryPath = Join-Path $env:APPDATA "Python\Scripts"
        if ($env:Path -notlike "*$poetryPath*") {
            $env:Path += ";$poetryPath"
        }

        if (Test-Poetry) {
            Write-Success "Poetry installed successfully"
            Add-RollbackStep {
                (Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python - --uninstall
            }
        }
        else {
            Write-Fatal "Poetry installation verification failed"
        }
    }
    catch {
        Write-Fatal "Failed to install Poetry: $_"
    }
}

function Test-Tesseract {
    Write-Info "Checking Tesseract OCR..."

    if (Test-Command tesseract) {
        $tesseractVersion = (tesseract --version 2>&1 | Select-String -Pattern "\d+\.\d+\.\d+").Matches.Value
        Write-Success "Tesseract $tesseractVersion found"
        return $true
    }
    else {
        Write-Warning "Tesseract OCR not found (optional)"
        return $false
    }
}

function Install-Tesseract {
    if (-not (Read-YesNo "Install Tesseract OCR (recommended for image analysis)?" $true)) {
        Write-Warning "Skipping Tesseract installation"
        return
    }

    Write-Info "Installing Tesseract OCR..."

    if (Test-Command winget) {
        try {
            winget install UB-Mannheim.TesseractOCR --silent
            Write-Success "Tesseract installed successfully"
        }
        catch {
            Write-Warning "Failed to install Tesseract: $_"
            Write-Info "Download manually from: https://github.com/UB-Mannheim/tesseract/wiki"
        }
    }
    else {
        Write-Info "Download Tesseract from: https://github.com/UB-Mannheim/tesseract/wiki"
    }
}

###############################################################################
# PROJECT SETUP
###############################################################################

function New-ProjectDirectories {
    Write-Info "Creating project directories..."

    $directories = @(
        "data",
        "data\cache",
        "data\exports",
        "data\profiles",
        "logs",
        "config"
    )

    foreach ($dir in $directories) {
        $fullPath = Join-Path $SCRIPT_DIR $dir
        if (-not (Test-Path $fullPath)) {
            New-Item -ItemType Directory -Path $fullPath -Force | Out-Null
            Write-VerboseLog "Created directory: $dir"
            Add-RollbackStep { Remove-Item -Path $fullPath -Recurse -Force -ErrorAction SilentlyContinue }
        }
    }

    Write-Success "Directories created"
}

function New-EnvironmentFile {
    Write-Info "Configuring environment variables..."

    $envFile = Join-Path $SCRIPT_DIR ".env"
    $envExample = Join-Path $SCRIPT_DIR ".env.example"

    if (Test-Path $envFile) {
        if (Read-YesNo "Existing .env file found. Backup and recreate?" $false) {
            $backupFile = Join-Path $BACKUP_DIR ".env.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
            New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
            Copy-Item $envFile $backupFile
            Write-Success "Backed up existing .env to $backupFile"
            Add-RollbackStep { Copy-Item $backupFile $envFile -Force }
        }
        else {
            Write-Info "Keeping existing .env file"
            return
        }
    }

    if (Test-Path $envExample) {
        Copy-Item $envExample $envFile
        Write-VerboseLog "Copied .env.example to .env"
    }
    else {
        # Create default .env
        @"
# Nyx Environment Variables
NYX_DEBUG=false
NYX_DATA_DIR=./data
NYX_CONFIG_DIR=./config

NYX_DATABASE_URL=sqlite:///./nyx.db
NYX_DATABASE_POOL_SIZE=20
NYX_DATABASE_MAX_OVERFLOW=40

NYX_HTTP_TIMEOUT=10
NYX_HTTP_RETRIES=3
NYX_HTTP_MAX_CONCURRENT_REQUESTS=100

NYX_CACHE_ENABLED=true
NYX_CACHE_TTL=3600
NYX_CACHE_MAX_SIZE=1000

NYX_LOGGING_LEVEL=INFO
NYX_LOGGING_FILE_PATH=logs/nyx.log
"@ | Out-File -FilePath $envFile -Encoding UTF8
        Write-VerboseLog "Created default .env file"
    }

    # Interactive configuration
    if (-not $Auto) {
        Write-Host ""
        Write-Info "Environment Configuration"
        Write-Host "Press Enter to accept defaults, or type your custom value"
        Write-Host ""

        $debug = Read-Input "Enable debug mode?" "false"
        (Get-Content $envFile) -replace 'NYX_DEBUG=.*', "NYX_DEBUG=$debug" | Set-Content $envFile

        $dbUrl = Read-Input "Database URL" "sqlite:///./nyx.db"
        (Get-Content $envFile) -replace 'NYX_DATABASE_URL=.*', "NYX_DATABASE_URL=$dbUrl" | Set-Content $envFile

        $logLevel = Read-Input "Logging level (DEBUG/INFO/WARNING/ERROR)" "INFO"
        (Get-Content $envFile) -replace 'NYX_LOGGING_LEVEL=.*', "NYX_LOGGING_LEVEL=$logLevel" | Set-Content $envFile
    }

    Write-Success "Environment file configured"
}

function New-ConfigFile {
    Write-Info "Setting up configuration file..."

    $configFile = Join-Path $SCRIPT_DIR "config\settings.local.yaml"
    $configTemplate = Join-Path $SCRIPT_DIR "config\settings.yaml"

    if (Test-Path $configFile) {
        if (Read-YesNo "Existing config file found. Backup and recreate?" $false) {
            $backupFile = Join-Path $BACKUP_DIR "settings.local.yaml.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
            New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
            Copy-Item $configFile $backupFile
            Write-Success "Backed up existing config to $backupFile"
        }
        else {
            Write-Info "Keeping existing configuration"
            return
        }
    }

    if (Test-Path $configTemplate) {
        Copy-Item $configTemplate $configFile
        Write-Success "Configuration file created"
    }
    else {
        Write-Warning "Configuration template not found, skipping"
    }
}

function Install-Dependencies {
    Write-Info "Installing Python dependencies (this may take 2-5 minutes)..."

    Push-Location $SCRIPT_DIR

    try {
        # Configure Poetry
        poetry config virtualenvs.in-project true 2>&1 | Out-Null
        Write-VerboseLog "Configured Poetry to use local virtualenv"

        # Install dependencies
        Write-Host "  Installing 40+ packages..." -ForegroundColor Gray

        $installOutput = ""
        if ($ShowVerbose) {
            poetry install
            $installSuccess = $LASTEXITCODE -eq 0
        }
        else {
            $installOutput = poetry install 2>&1 | Out-String
            $installSuccess = $LASTEXITCODE -eq 0
        }

        if (-not $installSuccess) {
            Write-Error "Poetry install failed"
            if (-not $ShowVerbose) {
                Write-Host $installOutput -ForegroundColor Red
            }
            Write-Fatal "Failed to install dependencies. Check the output above for errors."
        }

        # Verify installation by testing import
        Write-Host "  Verifying installation..." -ForegroundColor Gray
        $testImport = poetry run python -c "import nyx; print('OK')" 2>&1 | Out-String

        if ($testImport -match "OK") {
            Write-Success "Dependencies installed and verified"
            return $true
        }
        else {
            Write-Error "Package installation completed but nyx module cannot be imported"
            Write-Host $testImport -ForegroundColor Red
            Write-Host ""
            Write-Host "  This usually means:" -ForegroundColor Yellow
            Write-Host "    - Wrong Python version (need Python 3.12)" -ForegroundColor White
            Write-Host "    - Incompatible package versions" -ForegroundColor White
            Write-Host ""
            Write-Host "  Solution:" -ForegroundColor Cyan
            Write-Host "    poetry env remove python" -ForegroundColor Gray
            Write-Host "    poetry env use python3.12" -ForegroundColor Gray
            Write-Host "    poetry install" -ForegroundColor Gray
            Write-Host ""
            Write-Fatal "Installation verification failed"
        }
    }
    catch {
        Write-Fatal "Failed to install dependencies: $_"
    }
    finally {
        Pop-Location
    }
}

function Install-PlaywrightBrowsers {
    if (Read-YesNo "Install Playwright browser dependencies for web scraping?" $true) {
        Write-Info "Installing Playwright browsers (downloading ~200MB)..."

        try {
            $playwrightOutput = poetry run playwright install chromium 2>&1 | Out-String

            if ($LASTEXITCODE -eq 0 -and $playwrightOutput -match "(Downloaded|chromium)") {
                Write-Success "Playwright browsers installed"
                return $true
            }
            else {
                Write-Warning "Playwright installation may have failed"
                if ($ShowVerbose) {
                    Write-Host $playwrightOutput -ForegroundColor Yellow
                }
                Write-Host "  Web scraping features may be limited" -ForegroundColor Yellow
                return $false
            }
        }
        catch {
            Write-Warning "Failed to install Playwright browsers: $_"
            Write-Host "  Web scraping features may be limited" -ForegroundColor Yellow
            return $false
        }
    }
    else {
        Write-Warning "Skipping Playwright installation. Web scraping features will be limited."
        return $false
    }
}

###############################################################################
# DATABASE SETUP
###############################################################################

function Initialize-Database {
    Write-Info "Initializing database..."

    Push-Location $SCRIPT_DIR

    try {
        $dbFile = Join-Path $SCRIPT_DIR "nyx.db"

        if (Test-Path $dbFile) {
            if (Read-YesNo "Database already exists. Reset it?" $false) {
                $backupFile = Join-Path $BACKUP_DIR "nyx.db.backup.$(Get-Date -Format 'yyyyMMddHHmmss')"
                New-Item -ItemType Directory -Path $BACKUP_DIR -Force | Out-Null
                Copy-Item $dbFile $backupFile
                Write-Success "Backed up database to $backupFile"
                Remove-Item $dbFile
            }
            else {
                Write-Info "Keeping existing database"
                return
            }
        }

        # Initialize database schema
        $initScript = @'
from nyx.core.database import initialize_database
import asyncio
import sys

async def init():
    try:
        # Use SQLite database URL
        db_url = "sqlite+aiosqlite:///./nyx.db"
        await initialize_database(db_url)
        print('DB_INIT_SUCCESS')
        return 0
    except Exception as e:
        print(f'DB_INIT_FAILED: {e}', file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1

sys.exit(asyncio.run(init()))
'@

        $dbOutput = $initScript | poetry run python - 2>&1 | Out-String

        if ($LASTEXITCODE -eq 0 -and $dbOutput -match "DB_INIT_SUCCESS") {
            Write-Success "Database initialized successfully"
            return $true
        }
        else {
            Write-Error "Database initialization failed"
            Write-Host $dbOutput -ForegroundColor Red
            Write-Host ""
            Write-Host "  Common causes:" -ForegroundColor Yellow
            Write-Host "    - Nyx module not properly installed" -ForegroundColor White
            Write-Host "    - Database file permissions" -ForegroundColor White
            Write-Host "    - Missing dependencies" -ForegroundColor White
            Write-Host ""
            Write-Fatal "Database initialization failed. See error above."
        }
    }
    catch {
        Write-Fatal "Failed to initialize database: $_"
    }
    finally {
        Pop-Location
    }
}

###############################################################################
# VERIFICATION
###############################################################################

function Test-Installation {
    Write-Info "Verifying installation..."

    $script:CHECKS_PASSED = 0
    $script:CHECKS_TOTAL = 5
    $script:CRITICAL_CHECKS_PASSED = 0
    $script:CRITICAL_CHECKS_TOTAL = 2
    $failedChecks = @()

    # Check 1: Python import (CRITICAL)
    Write-Host "  Checking Python package... " -NoNewline
    $importTest = poetry run python -c "import nyx; print(nyx.__version__)" 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $importTest -match "\d+\.\d+\.\d+") {
        Write-Host "✓" -ForegroundColor Green
        $script:CHECKS_PASSED++
        $script:CRITICAL_CHECKS_PASSED++
    }
    else {
        Write-Host "✗ CRITICAL" -ForegroundColor Red
        $failedChecks += "Python package import failed"
    }

    # Check 2: CLI command (CRITICAL)
    Write-Host "  Checking CLI command... " -NoNewline
    $cliTest = poetry run nyx-cli --version 2>&1 | Out-String
    if ($LASTEXITCODE -eq 0 -and $cliTest -match "(\d+\.\d+\.\d+|nyx)") {
        Write-Host "✓" -ForegroundColor Green
        $script:CHECKS_PASSED++
        $script:CRITICAL_CHECKS_PASSED++
    }
    else {
        Write-Host "✗ CRITICAL" -ForegroundColor Red
        $failedChecks += "CLI command failed"
    }

    # Check 3: Configuration
    Write-Host "  Checking configuration... " -NoNewline
    if (Test-Path (Join-Path $SCRIPT_DIR ".env")) {
        Write-Host "✓" -ForegroundColor Green
        $script:CHECKS_PASSED++
    }
    else {
        Write-Host "✗" -ForegroundColor Red
        $failedChecks += "Configuration file missing"
    }

    # Check 4: Database
    Write-Host "  Checking database... " -NoNewline
    if (Test-Path (Join-Path $SCRIPT_DIR "nyx.db")) {
        Write-Host "✓" -ForegroundColor Green
        $script:CHECKS_PASSED++
    }
    else {
        Write-Host "⚠ (optional)" -ForegroundColor Yellow
    }

    # Check 5: Directories
    Write-Host "  Checking directories... " -NoNewline
    if ((Test-Path (Join-Path $SCRIPT_DIR "data")) -and (Test-Path (Join-Path $SCRIPT_DIR "logs"))) {
        Write-Host "✓" -ForegroundColor Green
        $script:CHECKS_PASSED++
    }
    else {
        Write-Host "✗" -ForegroundColor Red
        $failedChecks += "Required directories missing"
    }

    Write-Host ""

    # Critical checks must ALL pass
    if ($script:CRITICAL_CHECKS_PASSED -eq $script:CRITICAL_CHECKS_TOTAL) {
        Write-Success "Installation verified ($script:CHECKS_PASSED/$script:CHECKS_TOTAL checks passed)"
        return $true
    }
    else {
        Write-Error "Installation verification failed"
        Write-Host ""
        Write-Host "  Critical checks passed: $script:CRITICAL_CHECKS_PASSED/$script:CRITICAL_CHECKS_TOTAL" -ForegroundColor Red
        Write-Host "  Total checks passed: $script:CHECKS_PASSED/$script:CHECKS_TOTAL" -ForegroundColor Yellow
        Write-Host ""
        Write-Host "  Failed checks:" -ForegroundColor Red
        foreach ($check in $failedChecks) {
            Write-Host "    - $check" -ForegroundColor White
        }
        Write-Host ""
        Write-Host "  The installation is incomplete. Please check the errors above." -ForegroundColor Yellow
        Write-Host "  Most common issue: Wrong Python version (need 3.12, not 3.14)" -ForegroundColor Yellow
        Write-Host ""
        return $false
    }
}

###############################################################################
# MAIN WORKFLOW
###############################################################################

function Show-Banner {
    Write-Host @"
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║   ███╗   ██╗██╗   ██╗██╗  ██╗     ██████╗ ███████╗██╗███╗   ██╗████████╗
║   ████╗  ██║╚██╗ ██╔╝╚██╗██╔╝    ██╔═══██╗██╔════╝██║████╗  ██║╚══██╔══╝
║   ██╔██╗ ██║ ╚████╔╝  ╚███╔╝     ██║   ██║███████╗██║██╔██╗ ██║   ██║
║   ██║╚██╗██║  ╚██╔╝   ██╔██╗     ██║   ██║╚════██║██║██║╚██╗██║   ██║
║   ██║ ╚████║   ██║   ██╔╝ ██╗    ╚██████╔╝███████║██║██║ ╚████║   ██║
║   ╚═╝  ╚═══╝   ╚═╝   ╚═╝  ╚═╝     ╚═════╝ ╚══════╝╚═╝╚═╝  ╚═══╝   ╚═╝
║                                                               ║
║         Professional OSINT Investigation Platform            ║
║                  Guided Setup Wizard v1.0                    ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝
"@
}

function Show-SystemInfo {
    Write-Info "System Information:"
    Write-Host "  OS: Windows $(([System.Environment]::OSVersion.Version).ToString())"
    Write-Host "  PowerShell: $($PSVersionTable.PSVersion)"

    $pythonInfo = Get-PythonVersion
    Write-Host "  Python: " -NoNewline
    if ($pythonInfo.IsValid) {
        Write-Host "$($pythonInfo.Version)" -ForegroundColor Green
    }
    elseif ($pythonInfo.Version -eq [Version]"0.0.0") {
        Write-Host "Not found" -ForegroundColor Red
    }
    else {
        Write-Host "$($pythonInfo.Version) " -ForegroundColor Yellow -NoNewline
        Write-Host "(WARNING: Need 3.12)" -ForegroundColor Red
    }

    Write-Host "  Working Directory: $SCRIPT_DIR"
    Write-Host "  Administrator: $(Test-Administrator)"
    Write-Host ""
}

function Show-Summary {
    Write-Host ""
    Write-Host "╔═══════════════════════════════════════════════════════════════╗"
    Write-Host "║                     SETUP COMPLETE                            ║"
    Write-Host "╚═══════════════════════════════════════════════════════════════╝"
    Write-Host ""
    Write-Success "Nyx-OSINT has been successfully installed!"
    Write-Host ""
    Write-Info "Next Steps:"
    Write-Host ""
    Write-Host "  1. Activate the virtual environment:"
    Write-Host "     PS> poetry shell"
    Write-Host ""
    Write-Host "  2. Run the CLI:"
    Write-Host "     PS> nyx-cli --help"
    Write-Host ""
    Write-Host "  3. Search for a username:"
    Write-Host "     PS> nyx-cli search <username>"
    Write-Host ""
    Write-Host "  4. Launch the GUI:"
    Write-Host "     PS> nyx"
    Write-Host ""
    Write-Host "  5. View documentation:"
    Write-Host "     PS> Get-Content docs\USER_MANUAL.md"
    Write-Host ""
    Write-Info "Configuration:"
    Write-Host "  - Environment: .env"
    Write-Host "  - Settings: config\settings.local.yaml"
    Write-Host "  - Database: nyx.db"
    Write-Host "  - Logs: logs\nyx.log"
    Write-Host ""
    Write-Info "Resources:"
    Write-Host "  - User Manual: docs\USER_MANUAL.md"
    Write-Host "  - API Docs: docs\API.md"
    Write-Host "  - Project Status: PROJECT_STATUS.md"
    Write-Host "  - Setup Log: $LOG_FILE"
    Write-Host ""
}

###############################################################################
# MAIN ENTRY POINT
###############################################################################

function Main {
    # Initialize logging
    "=== Nyx-OSINT Setup Started at $(Get-Date) ===" | Out-File -FilePath $LOG_FILE -Encoding UTF8

    # Show banner
    Clear-Host
    Show-Banner
    Write-Host ""
    Show-SystemInfo

    if (-not $Auto) {
        Write-Host "This wizard will guide you through the installation process."
        Write-Host ""
        if (-not (Read-YesNo "Continue with setup?" $true)) {
            Write-Warning "Setup cancelled by user"
            exit 0
        }
        Write-Host ""
    }

    # Step 1: Dependencies
    if (-not $SkipDeps) {
        Write-Info "=== Step 1/6: Checking Dependencies ==="

        if (-not (Test-Python)) {
            if (Read-YesNo "Install Python $REQUIRED_PYTHON_VERSION?" $true) {
                Install-Python
            }
            else {
                Write-Fatal "Python $REQUIRED_PYTHON_VERSION is required"
            }
        }

        if (-not (Test-Poetry)) {
            if (Read-YesNo "Install Poetry package manager?" $true) {
                Install-Poetry
            }
            else {
                Write-Fatal "Poetry is required"
            }
        }

        if (-not (Test-Tesseract)) {
            Install-Tesseract
        }

        Write-Success "Dependency check completed"
        Write-Host ""
    }

    # Step 2: Project structure
    Write-Info "=== Step 2/6: Setting Up Project Structure ==="
    New-ProjectDirectories
    Write-Host ""

    # Step 3: Configuration
    Write-Info "=== Step 3/6: Configuring Environment ==="
    New-EnvironmentFile
    New-ConfigFile
    Write-Host ""

    # Step 4: Dependencies
    Write-Info "=== Step 4/6: Installing Python Packages ==="
    Install-Dependencies
    Install-PlaywrightBrowsers
    Write-Host ""

    # Step 5: Database
    if (-not $SkipDb) {
        Write-Info "=== Step 5/6: Initializing Database ==="
        if (Read-YesNo "Initialize database now?" $true) {
            Initialize-Database
        }
        else {
            Write-Warning "Skipping database initialization"
        }
        Write-Host ""
    }

    # Step 6: Verification
    Write-Info "=== Step 6/6: Verifying Installation ==="
    $verificationPassed = Test-Installation
    Write-Host ""

    if (-not $verificationPassed) {
        Write-Fatal "Installation verification failed. Please fix the errors above and run setup again."
    }

    # Summary
    Show-Summary

    # Save setup state
    @"
SETUP_COMPLETED=true
SETUP_DATE=$(Get-Date -Format o)
SETUP_VERSION=1.0.0
"@ | Out-File -FilePath $SETUP_CONFIG -Encoding UTF8

    Write-Success "Setup completed successfully!"
    Write-Log "Setup completed successfully"
}

# Run main function
try {
    Main
}
catch {
    Write-Fatal "Unhandled error: $_"
}
