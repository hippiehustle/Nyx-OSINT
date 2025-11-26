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
            $output = python --version 2>&1
            if ($output -match "Python (\d+\.\d+\.\d+)") {
                return [Version]$matches[1]
            }
        }
        return [Version]"0.0.0"
    }
    catch {
        return [Version]"0.0.0"
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

    $pythonVersion = Get-PythonVersion

    if ($pythonVersion -ge $REQUIRED_PYTHON_VERSION) {
        Write-Success "Python $pythonVersion found"
        return $true
    }
    else {
        Write-Warning "Python $REQUIRED_PYTHON_VERSION+ is required (found: $pythonVersion)"
        return $false
    }
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
    Write-Info "Installing Python dependencies..."

    Push-Location $SCRIPT_DIR

    try {
        # Configure Poetry
        poetry config virtualenvs.in-project true
        Write-VerboseLog "Configured Poetry to use local virtualenv"

        # Install dependencies
        if ($ShowVerbose) {
            poetry install
        }
        else {
            poetry install 2>&1 | Out-Null
        }

        Write-Success "Dependencies installed"
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
        Write-Info "Installing Playwright browsers..."

        try {
            poetry run playwright install chromium
            Write-Success "Playwright browsers installed"
        }
        catch {
            Write-Warning "Failed to install Playwright browsers: $_"
        }
    }
    else {
        Write-Warning "Skipping Playwright installation"
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

async def init():
    await initialize_database()
    print('Database initialized')

asyncio.run(init())
'@

        $initScript | poetry run python -

        Write-Success "Database initialized"
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

    # Check 1: Python import
    Write-Host "  Checking Python package... " -NoNewline
    try {
        poetry run python -c "import nyx; print(nyx.__version__)" | Out-Null
        Write-Host "✓" -ForegroundColor Green
        $script:CHECKS_PASSED++
    }
    catch {
        Write-Host "✗" -ForegroundColor Red
    }

    # Check 2: CLI command
    Write-Host "  Checking CLI command... " -NoNewline
    try {
        poetry run nyx-cli --version | Out-Null
        Write-Host "✓" -ForegroundColor Green
        $script:CHECKS_PASSED++
    }
    catch {
        Write-Host "✗" -ForegroundColor Red
    }

    # Check 3: Configuration
    Write-Host "  Checking configuration... " -NoNewline
    if (Test-Path (Join-Path $SCRIPT_DIR ".env")) {
        Write-Host "✓" -ForegroundColor Green
        $script:CHECKS_PASSED++
    }
    else {
        Write-Host "✗" -ForegroundColor Red
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
    }

    Write-Host ""

    if ($script:CHECKS_PASSED -ge 3) {
        Write-Success "Installation verified ($script:CHECKS_PASSED/$script:CHECKS_TOTAL checks passed)"
        return $true
    }
    else {
        Write-Error "Installation verification failed ($script:CHECKS_PASSED/$script:CHECKS_TOTAL checks passed)"
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
    Write-Host "  Python: $(Get-PythonVersion)"
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
    Test-Installation
    Write-Host ""

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
