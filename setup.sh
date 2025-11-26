#!/usr/bin/env bash
###############################################################################
# Nyx-OSINT Guided Setup Script
# Version: 1.0.0
# Description: Interactive installation and configuration wizard
# Platform: Linux, macOS, WSL
# Usage: ./setup.sh [OPTIONS]
#
# Options:
#   --auto              Run in automated mode (no prompts)
#   --config FILE       Use configuration file
#   --verbose           Enable verbose output
#   --skip-deps         Skip dependency installation
#   --skip-db           Skip database initialization
#   --help              Show this help message
#
# Prerequisites:
#   - Python 3.12+ (will be installed if missing)
#   - Git (recommended)
#   - Internet connection
#
###############################################################################

set -euo pipefail  # Exit on error, undefined variables, pipe failures

###############################################################################
# CONFIGURATION
###############################################################################

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="${SCRIPT_DIR}/setup.log"
BACKUP_DIR="${SCRIPT_DIR}/.setup_backup"
REQUIRED_PYTHON_VERSION="3.12"
SETUP_CONFIG="${SCRIPT_DIR}/.setup.conf"

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Setup state tracking
ROLLBACK_STEPS=()
VERBOSE=false
AUTO_MODE=false
SKIP_DEPS=false
SKIP_DB=false

###############################################################################
# UTILITY FUNCTIONS
###############################################################################

log() {
    echo "[$(date +'%Y-%m-%d %H:%M:%S')] $*" >> "$LOG_FILE"
}

info() {
    echo -e "${BLUE}ℹ${NC} $*"
    log "INFO: $*"
}

success() {
    echo -e "${GREEN}✓${NC} $*"
    log "SUCCESS: $*"
}

warning() {
    echo -e "${YELLOW}⚠${NC} $*"
    log "WARNING: $*"
}

error() {
    echo -e "${RED}✗${NC} $*" >&2
    log "ERROR: $*"
}

fatal() {
    error "$*"
    error "Setup failed. Check $LOG_FILE for details."
    cleanup_on_failure
    exit 1
}

verbose() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[VERBOSE]${NC} $*"
        log "VERBOSE: $*"
    fi
}

###############################################################################
# PROGRESS INDICATORS
###############################################################################

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏'
    while ps -p "$pid" > /dev/null 2>&1; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

progress_bar() {
    local current=$1
    local total=$2
    local width=50
    local percentage=$((current * 100 / total))
    local completed=$((width * current / total))
    local remaining=$((width - completed))

    printf "\r["
    printf "%${completed}s" | tr ' ' '█'
    printf "%${remaining}s" | tr ' ' '░'
    printf "] %3d%%" "$percentage"
}

###############################################################################
# CLEANUP & ROLLBACK
###############################################################################

cleanup_on_failure() {
    warning "Rolling back changes..."

    for ((i=${#ROLLBACK_STEPS[@]}-1; i>=0; i--)); do
        verbose "Rollback step: ${ROLLBACK_STEPS[$i]}"
        eval "${ROLLBACK_STEPS[$i]}" 2>&1 | tee -a "$LOG_FILE" || true
    done

    success "Rollback completed"
}

add_rollback() {
    ROLLBACK_STEPS+=("$1")
    verbose "Added rollback step: $1"
}

trap_handler() {
    warning "\nSetup interrupted by user (Ctrl+C)"
    cleanup_on_failure
    exit 130
}

trap trap_handler SIGINT SIGTERM

###############################################################################
# SYSTEM DETECTION
###############################################################################

detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "linux"
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        echo "macos"
    elif [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]; then
        echo "windows"
    else
        echo "unknown"
    fi
}

detect_package_manager() {
    if command -v apt-get &> /dev/null; then
        echo "apt"
    elif command -v dnf &> /dev/null; then
        echo "dnf"
    elif command -v yum &> /dev/null; then
        echo "yum"
    elif command -v pacman &> /dev/null; then
        echo "pacman"
    elif command -v brew &> /dev/null; then
        echo "brew"
    else
        echo "none"
    fi
}

check_command() {
    command -v "$1" &> /dev/null
}

get_python_version() {
    if check_command python3; then
        python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))'
    else
        echo "0.0"
    fi
}

version_ge() {
    printf '%s\n%s\n' "$2" "$1" | sort -V -C
}

###############################################################################
# USER INTERACTION
###############################################################################

prompt_yes_no() {
    local prompt="$1"
    local default="${2:-n}"

    if [[ "$AUTO_MODE" == "true" ]]; then
        [[ "$default" == "y" ]] && return 0 || return 1
    fi

    local yn
    while true; do
        if [[ "$default" == "y" ]]; then
            read -rp "$(echo -e "${CYAN}?${NC} $prompt [Y/n]: ")" yn
            yn=${yn:-y}
        else
            read -rp "$(echo -e "${CYAN}?${NC} $prompt [y/N]: ")" yn
            yn=${yn:-n}
        fi

        case $yn in
            [Yy]*) return 0 ;;
            [Nn]*) return 1 ;;
            *) warning "Please answer yes or no." ;;
        esac
    done
}

prompt_input() {
    local prompt="$1"
    local default="$2"
    local var_name="$3"

    if [[ "$AUTO_MODE" == "true" ]]; then
        eval "$var_name='$default'"
        return 0
    fi

    local input
    read -rp "$(echo -e "${CYAN}?${NC} $prompt [$default]: ")" input
    input=${input:-$default}
    eval "$var_name='$input'"
}

###############################################################################
# DEPENDENCY CHECKS
###############################################################################

check_python() {
    info "Checking Python installation..."

    local python_version
    python_version=$(get_python_version)

    if version_ge "$python_version" "$REQUIRED_PYTHON_VERSION"; then
        success "Python $python_version found"
        return 0
    else
        warning "Python $REQUIRED_PYTHON_VERSION+ is required (found: $python_version)"
        return 1
    fi
}

install_python() {
    local os
    os=$(detect_os)
    local pkg_mgr
    pkg_mgr=$(detect_package_manager)

    info "Attempting to install Python $REQUIRED_PYTHON_VERSION..."

    case "$os" in
        linux)
            case "$pkg_mgr" in
                apt)
                    sudo apt-get update && \
                    sudo apt-get install -y python3.12 python3.12-venv python3.12-dev
                    ;;
                dnf|yum)
                    sudo "$pkg_mgr" install -y python3.12 python3.12-devel
                    ;;
                pacman)
                    sudo pacman -Sy --noconfirm python
                    ;;
                *)
                    fatal "Cannot auto-install Python. Please install Python $REQUIRED_PYTHON_VERSION manually."
                    ;;
            esac
            ;;
        macos)
            if [[ "$pkg_mgr" == "brew" ]]; then
                brew install python@3.12
            else
                warning "Homebrew not found. Please install from https://brew.sh/"
                fatal "Cannot install Python without Homebrew."
            fi
            ;;
        *)
            fatal "Cannot auto-install Python on this platform. Please install manually."
            ;;
    esac

    check_python || fatal "Python installation failed"
    success "Python installed successfully"
}

check_poetry() {
    info "Checking Poetry installation..."

    if check_command poetry; then
        local poetry_version
        poetry_version=$(poetry --version | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
        success "Poetry $poetry_version found"
        return 0
    else
        warning "Poetry not found"
        return 1
    fi
}

install_poetry() {
    info "Installing Poetry..."

    curl -sSL https://install.python-poetry.org | python3 - || \
        fatal "Failed to install Poetry"

    # Add Poetry to PATH for current session
    export PATH="$HOME/.local/bin:$PATH"

    check_poetry || fatal "Poetry installation failed"

    add_rollback "curl -sSL https://install.python-poetry.org | python3 - --uninstall"
    success "Poetry installed successfully"
}

check_tesseract() {
    info "Checking Tesseract OCR..."

    if check_command tesseract; then
        local tesseract_version
        tesseract_version=$(tesseract --version 2>&1 | head -n1 | grep -oP '\d+\.\d+\.\d+' || echo "unknown")
        success "Tesseract $tesseract_version found"
        return 0
    else
        warning "Tesseract OCR not found (optional, required for image text recognition)"
        return 1
    fi
}

install_tesseract() {
    local os
    os=$(detect_os)
    local pkg_mgr
    pkg_mgr=$(detect_package_manager)

    if ! prompt_yes_no "Install Tesseract OCR (recommended for image analysis)?" "y"; then
        warning "Skipping Tesseract installation. Image text recognition will be disabled."
        return 0
    fi

    info "Installing Tesseract OCR..."

    case "$os" in
        linux)
            case "$pkg_mgr" in
                apt)
                    sudo apt-get install -y tesseract-ocr tesseract-ocr-eng
                    ;;
                dnf|yum)
                    sudo "$pkg_mgr" install -y tesseract tesseract-langpack-eng
                    ;;
                pacman)
                    sudo pacman -Sy --noconfirm tesseract tesseract-data-eng
                    ;;
                *)
                    warning "Cannot auto-install Tesseract. Install manually if needed."
                    return 0
                    ;;
            esac
            ;;
        macos)
            if [[ "$pkg_mgr" == "brew" ]]; then
                brew install tesseract
            else
                warning "Cannot install Tesseract without Homebrew."
                return 0
            fi
            ;;
    esac

    if check_tesseract; then
        success "Tesseract installed successfully"
    fi
}

check_playwright() {
    info "Checking Playwright browsers..."

    if poetry run python3 -c "import playwright" 2>/dev/null; then
        verbose "Playwright Python package found"
        return 0
    else
        return 1
    fi
}

install_playwright_browsers() {
    info "Installing Playwright browser dependencies..."

    poetry run playwright install chromium || \
        warning "Failed to install Playwright browsers. Web scraping may be limited."

    success "Playwright browsers installed"
}

###############################################################################
# PROJECT SETUP
###############################################################################

create_directories() {
    info "Creating project directories..."

    local dirs=(
        "data"
        "data/cache"
        "data/exports"
        "data/profiles"
        "logs"
        "config"
    )

    for dir in "${dirs[@]}"; do
        if [[ ! -d "$SCRIPT_DIR/$dir" ]]; then
            mkdir -p "$SCRIPT_DIR/$dir"
            verbose "Created directory: $dir"
            add_rollback "rm -rf '$SCRIPT_DIR/$dir'"
        fi
    done

    success "Directories created"
}

setup_environment_file() {
    info "Configuring environment variables..."

    local env_file="$SCRIPT_DIR/.env"
    local env_example="$SCRIPT_DIR/.env.example"

    if [[ -f "$env_file" ]]; then
        if prompt_yes_no "Existing .env file found. Backup and recreate?" "n"; then
            local backup_file="${BACKUP_DIR}/.env.backup.$(date +%s)"
            mkdir -p "$BACKUP_DIR"
            cp "$env_file" "$backup_file"
            success "Backed up existing .env to $backup_file"
            add_rollback "cp '$backup_file' '$env_file'"
        else
            info "Keeping existing .env file"
            return 0
        fi
    fi

    if [[ -f "$env_example" ]]; then
        cp "$env_example" "$env_file"
        verbose "Copied .env.example to .env"
    else
        # Create default .env if example doesn't exist
        cat > "$env_file" << 'EOF'
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
EOF
        verbose "Created default .env file"
    fi

    # Interactive configuration
    if ! [[ "$AUTO_MODE" == "true" ]]; then
        echo ""
        info "Environment Configuration"
        echo "Press Enter to accept defaults, or type your custom value"
        echo ""

        local debug
        prompt_input "Enable debug mode?" "false" debug
        sed -i "s|NYX_DEBUG=.*|NYX_DEBUG=$debug|" "$env_file"

        local db_url
        prompt_input "Database URL" "sqlite:///./nyx.db" db_url
        sed -i "s|NYX_DATABASE_URL=.*|NYX_DATABASE_URL=$db_url|" "$env_file"

        local log_level
        prompt_input "Logging level (DEBUG/INFO/WARNING/ERROR)" "INFO" log_level
        sed -i "s|NYX_LOGGING_LEVEL=.*|NYX_LOGGING_LEVEL=$log_level|" "$env_file"
    fi

    chmod 600 "$env_file"
    success "Environment file configured"
}

setup_config_file() {
    info "Setting up configuration file..."

    local config_file="$SCRIPT_DIR/config/settings.local.yaml"
    local config_template="$SCRIPT_DIR/config/settings.yaml"

    if [[ -f "$config_file" ]]; then
        if prompt_yes_no "Existing config file found. Backup and recreate?" "n"; then
            local backup_file="${BACKUP_DIR}/settings.local.yaml.backup.$(date +%s)"
            mkdir -p "$BACKUP_DIR"
            cp "$config_file" "$backup_file"
            success "Backed up existing config to $backup_file"
        else
            info "Keeping existing configuration"
            return 0
        fi
    fi

    if [[ -f "$config_template" ]]; then
        cp "$config_template" "$config_file"
        success "Configuration file created"
    else
        warning "Configuration template not found, skipping"
    fi
}

install_dependencies() {
    info "Installing Python dependencies..."

    cd "$SCRIPT_DIR"

    # Configure Poetry
    poetry config virtualenvs.in-project true
    verbose "Configured Poetry to use local virtualenv"

    # Install dependencies with progress
    if [[ "$VERBOSE" == "true" ]]; then
        poetry install || fatal "Failed to install dependencies"
    else
        (
            poetry install > /dev/null 2>&1 &
            spinner $!
        ) || fatal "Failed to install dependencies"
    fi

    success "Dependencies installed"
}

install_playwright_deps() {
    if prompt_yes_no "Install Playwright browser dependencies for web scraping?" "y"; then
        install_playwright_browsers
    else
        warning "Skipping Playwright installation. Web scraping features will be limited."
    fi
}

###############################################################################
# DATABASE SETUP
###############################################################################

initialize_database() {
    info "Initializing database..."

    cd "$SCRIPT_DIR"

    # Check if database already exists
    if [[ -f "$SCRIPT_DIR/nyx.db" ]]; then
        if prompt_yes_no "Database already exists. Reset it?" "n"; then
            local backup_file="${BACKUP_DIR}/nyx.db.backup.$(date +%s)"
            mkdir -p "$BACKUP_DIR"
            cp "$SCRIPT_DIR/nyx.db" "$backup_file"
            success "Backed up database to $backup_file"
            rm "$SCRIPT_DIR/nyx.db"
        else
            info "Keeping existing database"
            return 0
        fi
    fi

    # Initialize database schema
    poetry run python3 -c "
from nyx.core.database import initialize_database
import asyncio

async def init():
    await initialize_database()
    print('Database initialized')

asyncio.run(init())
" || fatal "Failed to initialize database"

    success "Database initialized"
}

###############################################################################
# VERIFICATION
###############################################################################

verify_installation() {
    info "Verifying installation..."

    local checks_passed=0
    local checks_total=5

    # Check 1: Python import
    echo -n "  Checking Python package... "
    if poetry run python3 -c "import nyx; print(nyx.__version__)" > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}✗${NC}"
    fi

    # Check 2: CLI command
    echo -n "  Checking CLI command... "
    if poetry run nyx-cli --version > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}✗${NC}"
    fi

    # Check 3: Configuration
    echo -n "  Checking configuration... "
    if [[ -f "$SCRIPT_DIR/.env" ]]; then
        echo -e "${GREEN}✓${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}✗${NC}"
    fi

    # Check 4: Database
    echo -n "  Checking database... "
    if [[ -f "$SCRIPT_DIR/nyx.db" ]]; then
        echo -e "${GREEN}✓${NC}"
        ((checks_passed++))
    else
        echo -e "${YELLOW}⚠${NC} (optional)"
    fi

    # Check 5: Directories
    echo -n "  Checking directories... "
    if [[ -d "$SCRIPT_DIR/data" ]] && [[ -d "$SCRIPT_DIR/logs" ]]; then
        echo -e "${GREEN}✓${NC}"
        ((checks_passed++))
    else
        echo -e "${RED}✗${NC}"
    fi

    echo ""

    if [[ $checks_passed -ge 3 ]]; then
        success "Installation verified ($checks_passed/$checks_total checks passed)"
        return 0
    else
        error "Installation verification failed ($checks_passed/$checks_total checks passed)"
        return 1
    fi
}

###############################################################################
# MAIN SETUP WORKFLOW
###############################################################################

show_banner() {
    cat << "EOF"
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
EOF
}

show_system_info() {
    info "System Information:"
    echo "  OS: $(detect_os)"
    echo "  Package Manager: $(detect_package_manager)"
    echo "  Python: $(get_python_version)"
    echo "  Working Directory: $SCRIPT_DIR"
    echo ""
}

show_summary() {
    echo ""
    echo "╔═══════════════════════════════════════════════════════════════╗"
    echo "║                     SETUP COMPLETE                            ║"
    echo "╚═══════════════════════════════════════════════════════════════╝"
    echo ""
    success "Nyx-OSINT has been successfully installed!"
    echo ""
    info "Next Steps:"
    echo ""
    echo "  1. Activate the virtual environment:"
    echo "     $ poetry shell"
    echo ""
    echo "  2. Run the CLI:"
    echo "     $ nyx-cli --help"
    echo ""
    echo "  3. Search for a username:"
    echo "     $ nyx-cli search <username>"
    echo ""
    echo "  4. Launch the GUI:"
    echo "     $ nyx"
    echo ""
    echo "  5. View documentation:"
    echo "     $ cat docs/USER_MANUAL.md"
    echo ""
    info "Configuration:"
    echo "  - Environment: .env"
    echo "  - Settings: config/settings.local.yaml"
    echo "  - Database: nyx.db"
    echo "  - Logs: logs/nyx.log"
    echo ""
    info "Resources:"
    echo "  - User Manual: docs/USER_MANUAL.md"
    echo "  - API Docs: docs/API.md"
    echo "  - Project Status: PROJECT_STATUS.md"
    echo "  - Setup Log: $LOG_FILE"
    echo ""
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --auto)
                AUTO_MODE=true
                shift
                ;;
            --verbose)
                VERBOSE=true
                shift
                ;;
            --skip-deps)
                SKIP_DEPS=true
                shift
                ;;
            --skip-db)
                SKIP_DB=true
                shift
                ;;
            --config)
                SETUP_CONFIG="$2"
                shift 2
                ;;
            --help)
                grep "^#" "$0" | grep -v "^#!/" | sed 's/^# *//'
                exit 0
                ;;
            *)
                error "Unknown option: $1"
                echo "Use --help for usage information"
                exit 1
                ;;
        esac
    done
}

main() {
    # Initialize
    parse_args "$@"

    # Start logging
    echo "=== Nyx-OSINT Setup Started at $(date) ===" > "$LOG_FILE"

    # Show banner
    clear
    show_banner
    echo ""
    show_system_info

    if ! [[ "$AUTO_MODE" == "true" ]]; then
        echo "This wizard will guide you through the installation process."
        echo ""
        if ! prompt_yes_no "Continue with setup?" "y"; then
            warning "Setup cancelled by user"
            exit 0
        fi
        echo ""
    fi

    # Dependency checks and installation
    if ! [[ "$SKIP_DEPS" == "true" ]]; then
        info "=== Step 1/6: Checking Dependencies ==="

        if ! check_python; then
            if prompt_yes_no "Install Python $REQUIRED_PYTHON_VERSION?" "y"; then
                install_python
            else
                fatal "Python $REQUIRED_PYTHON_VERSION is required"
            fi
        fi

        if ! check_poetry; then
            if prompt_yes_no "Install Poetry package manager?" "y"; then
                install_poetry
            else
                fatal "Poetry is required"
            fi
        fi

        check_tesseract || install_tesseract

        success "Dependency check completed"
        echo ""
    fi

    # Project setup
    info "=== Step 2/6: Setting Up Project Structure ==="
    create_directories
    echo ""

    info "=== Step 3/6: Configuring Environment ==="
    setup_environment_file
    setup_config_file
    echo ""

    info "=== Step 4/6: Installing Python Packages ==="
    install_dependencies
    install_playwright_deps
    echo ""

    # Database initialization
    if ! [[ "$SKIP_DB" == "true" ]]; then
        info "=== Step 5/6: Initializing Database ==="
        if prompt_yes_no "Initialize database now?" "y"; then
            initialize_database
        else
            warning "Skipping database initialization. Run manually later."
        fi
        echo ""
    fi

    # Verification
    info "=== Step 6/6: Verifying Installation ==="
    verify_installation
    echo ""

    # Summary
    show_summary

    # Save setup state
    echo "SETUP_COMPLETED=true" > "$SETUP_CONFIG"
    echo "SETUP_DATE=$(date -Iseconds)" >> "$SETUP_CONFIG"
    echo "SETUP_VERSION=1.0.0" >> "$SETUP_CONFIG"

    success "Setup completed successfully!"
    log "Setup completed successfully"
}

# Run main function
main "$@"
