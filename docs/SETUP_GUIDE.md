# Nyx-OSINT Setup Guide

Complete installation and configuration guide for the Nyx-OSINT platform.

## Table of Contents

- [Quick Start](#quick-start)
- [Detailed Installation](#detailed-installation)
- [Configuration](#configuration)
- [Troubleshooting](#troubleshooting)
- [Advanced Setup](#advanced-setup)

---

## Quick Start

### Linux / macOS / WSL

```bash
# Make the setup script executable
chmod +x setup.sh

# Run the guided setup
./setup.sh

# Or run in automated mode
./setup.sh --auto
```

### Windows (PowerShell)

```powershell
# Run PowerShell as Administrator (recommended)

# Allow script execution (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run the guided setup
.\setup.ps1

# Or run in automated mode
.\setup.ps1 -Auto
```

---

## Detailed Installation

### Prerequisites

#### Required
- **Python 3.12+** - The setup script can install this automatically
- **Poetry** - Python dependency manager (auto-installed)
- **Internet Connection** - For downloading dependencies

#### Optional
- **Tesseract OCR** - For image text recognition
- **Git** - For version control and updates
- **Docker** - For containerized deployment

### Installation Steps

#### 1. Download Nyx-OSINT

```bash
# Clone with Git (recommended)
git clone https://github.com/hippiehustle/Nyx-OSINT.git
cd Nyx-OSINT

# Or download and extract ZIP
wget https://github.com/hippiehustle/Nyx-OSINT/archive/main.zip
unzip main.zip
cd Nyx-OSINT-main
```

#### 2. Run Setup Script

**Interactive Mode** (recommended for first-time setup):
```bash
./setup.sh
```

The interactive wizard will:
1. Check and install dependencies
2. Create project directories
3. Configure environment variables
4. Install Python packages
5. Initialize the database
6. Verify the installation

**Automated Mode** (for CI/CD or scripted deployments):
```bash
./setup.sh --auto --verbose
```

#### 3. Activate Environment

```bash
# Enter the Poetry virtual environment
poetry shell

# Your prompt should now show (.venv)
```

#### 4. Verify Installation

```bash
# Check CLI
nyx-cli --version

# Run a test search
nyx-cli search testuser --dry-run

# Check GUI (Linux/macOS with X11)
nyx
```

---

## Configuration

### Environment Variables (.env)

The setup script creates a `.env` file with default values. Edit this file to customize:

```bash
# Open in your editor
nano .env

# Or use the setup script's prompts during installation
```

**Key Settings:**

```ini
# Debug mode (set to true for verbose logging)
NYX_DEBUG=false

# Data directory (where investigations are stored)
NYX_DATA_DIR=./data

# Database configuration
NYX_DATABASE_URL=sqlite:///./nyx.db

# HTTP settings
NYX_HTTP_TIMEOUT=10
NYX_HTTP_MAX_CONCURRENT_REQUESTS=100

# Caching
NYX_CACHE_ENABLED=true
NYX_CACHE_TTL=3600

# Logging
NYX_LOGGING_LEVEL=INFO
NYX_LOGGING_FILE_PATH=logs/nyx.log

# Proxy (if needed)
NYX_PROXY_ENABLED=false
NYX_PROXY_HTTP_PROXY=http://proxy.example.com:8080

# Tor (for anonymity)
NYX_TOR_ENABLED=false
NYX_TOR_SOCKS_PORT=9050
```

### Configuration File (config/settings.local.yaml)

For advanced configuration, edit the YAML file:

```bash
nano config/settings.local.yaml
```

**Example Configuration:**

```yaml
debug: false
data_dir: ./data

database:
  url: sqlite:///./nyx.db
  pool_size: 20

http:
  timeout: 10
  user_agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) Nyx/0.1.0
  max_concurrent_requests: 100

cache:
  enabled: true
  ttl: 3600
  max_size: 1000

gui:
  theme: dark
  window_width: 1400
  window_height: 900

security:
  enable_encryption: true
  require_master_password: true

logging:
  level: INFO
  file_path: logs/nyx.log
```

---

## Troubleshooting

### Common Issues

#### Python Version Mismatch

**Problem:** "Python 3.12+ is required"

**Solution:**
```bash
# Check Python version
python3 --version

# Install Python 3.12 (Ubuntu/Debian)
sudo apt-get update
sudo apt-get install python3.12 python3.12-venv

# macOS (with Homebrew)
brew install python@3.12

# Windows (with winget)
winget install Python.Python.3.12
```

#### Poetry Not Found

**Problem:** "poetry: command not found"

**Solution:**
```bash
# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Add to PATH (add to ~/.bashrc or ~/.zshrc)
export PATH="$HOME/.local/bin:$PATH"

# Reload shell
source ~/.bashrc
```

#### Permission Denied

**Problem:** "Permission denied: ./setup.sh"

**Solution:**
```bash
# Make script executable
chmod +x setup.sh

# Run setup
./setup.sh
```

#### Import Errors After Installation

**Problem:** "ImportError: cannot import name..."

**Solution:**
```bash
# Clear Python cache
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete

# Reinstall dependencies
poetry install --no-cache

# Verify imports
poetry run python -c "import nyx; print(nyx.__version__)"
```

#### Database Initialization Failed

**Problem:** Database creation errors

**Solution:**
```bash
# Remove existing database
rm nyx.db

# Reinitialize
poetry run python -c "
from nyx.core.database import initialize_database
import asyncio
asyncio.run(initialize_database())
"
```

#### GUI Won't Start

**Problem:** "tkinter" errors or blank window

**Solution (Linux):**
```bash
# Install tkinter
sudo apt-get install python3-tk

# Set display (if using SSH)
export DISPLAY=:0
```

**Solution (macOS):**
```bash
# Install XQuartz
brew install --cask xquartz

# Restart terminal
```

**Solution (Windows):**
- Ensure Python was installed with tcl/tk support
- Reinstall Python with "tcl/tk and IDLE" option checked

### Setup Script Options

```bash
# Show help
./setup.sh --help

# Verbose output (for debugging)
./setup.sh --verbose

# Skip dependency installation
./setup.sh --skip-deps

# Skip database initialization
./setup.sh --skip-db

# Automated mode
./setup.sh --auto

# Combine options
./setup.sh --auto --verbose --skip-db
```

### Log Files

Check log files for detailed error information:

```bash
# Setup log
cat setup.log

# Application log
cat logs/nyx.log

# Tail logs in real-time
tail -f logs/nyx.log
```

---

## Advanced Setup

### Using PostgreSQL Instead of SQLite

1. Install PostgreSQL:
```bash
# Ubuntu/Debian
sudo apt-get install postgresql postgresql-contrib

# macOS
brew install postgresql
```

2. Create database:
```bash
sudo -u postgres psql
CREATE DATABASE nyx;
CREATE USER nyxuser WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE nyx TO nyxuser;
\q
```

3. Update `.env`:
```ini
NYX_DATABASE_URL=postgresql://nyxuser:secure_password@localhost/nyx
```

### Using Tor for Anonymity

1. Install Tor:
```bash
# Ubuntu/Debian
sudo apt-get install tor

# macOS
brew install tor

# Start Tor
sudo systemctl start tor  # Linux
brew services start tor   # macOS
```

2. Configure `.env`:
```ini
NYX_TOR_ENABLED=true
NYX_TOR_SOCKS_PORT=9050
NYX_TOR_CONTROL_PORT=9051
```

3. Test connection:
```bash
nyx-cli search testuser --use-tor
```

### Docker Deployment

1. Build Docker image:
```bash
docker build -t nyx-osint .
```

2. Run with Docker Compose:
```bash
docker-compose up -d
```

3. Access CLI:
```bash
docker-compose exec nyx-cli nyx-cli search username
```

### Development Setup

For contributors and developers:

```bash
# Install dev dependencies
poetry install --with dev

# Run tests
poetry run pytest

# Code formatting
poetry run black src/
poetry run isort src/

# Type checking
poetry run mypy src/

# Security scanning
poetry run bandit -r src/
```

---

## Post-Installation

### First Run

```bash
# Activate environment
poetry shell

# Run CLI help
nyx-cli --help

# Perform a search
nyx-cli search johndoe

# Launch GUI
nyx
```

### Updating Nyx-OSINT

```bash
# Pull latest changes (if using Git)
git pull origin main

# Update dependencies
poetry update

# Run database migrations (if any)
poetry run alembic upgrade head
```

### Backing Up Data

```bash
# Backup database
cp nyx.db nyx.db.backup

# Backup data directory
tar -czf nyx-data-backup.tar.gz data/

# Backup configuration
cp .env .env.backup
cp config/settings.local.yaml config/settings.local.yaml.backup
```

---

## Getting Help

- **Documentation**: Check `docs/` directory
- **User Manual**: `docs/USER_MANUAL.md`
- **API Documentation**: `docs/API.md`
- **GitHub Issues**: Report bugs and request features
- **Setup Log**: Check `setup.log` for detailed installation info

---

## Security Considerations

1. **Never commit `.env` files** - Contains sensitive configuration
2. **Use strong master password** - Protects encrypted data
3. **Enable Tor** - For anonymous investigations
4. **Review logs regularly** - Check for suspicious activity
5. **Keep software updated** - Apply security patches promptly

---

## Next Steps

After successful installation:

1. Read the [User Manual](USER_MANUAL.md)
2. Review the [API Documentation](API.md)
3. Check [PROJECT_STATUS.md](../PROJECT_STATUS.md) for features
4. Join the community and contribute!

---

**Setup complete! Happy investigating! 🔍**
