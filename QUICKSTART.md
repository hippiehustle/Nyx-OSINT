# Nyx-OSINT Quick Start

Get up and running in under 5 minutes!

## One-Line Install

### Linux / macOS / WSL
```bash
chmod +x setup.sh && ./setup.sh
```

### Windows (PowerShell)
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass; .\setup.ps1
```

## Usage Cheat Sheet

### Activate Environment
```bash
poetry shell
```

### CLI Commands

```bash
# Search for a username across all platforms
nyx-cli search johndoe

# Search with filters
nyx-cli search johndoe --category social_media --exclude-nsfw

# Email investigation
nyx-cli email test@example.com

# Phone investigation
nyx-cli phone "+1234567890" --region US

# List available platforms
nyx-cli platforms

# Export results
nyx-cli export --format pdf --output report.pdf
```

### GUI Application

```bash
# Launch graphical interface
nyx
```

## Common Tasks

### Search a Username
```bash
nyx-cli search johndoe
```

### Investigate Email
```bash
nyx-cli email john@example.com
```

### Investigate Phone
```bash
nyx-cli phone "+1-555-123-4567"
```

### Advanced Search
```bash
nyx-cli search johndoe \
  --category social_media,professional \
  --exclude-nsfw \
  --save-search "my_investigation"
```

### Generate Report
```bash
nyx-cli export \
  --format pdf \
  --output ~/Desktop/investigation_report.pdf \
  --template professional
```

## Configuration Files

| File | Purpose |
|------|---------|
| `.env` | Environment variables |
| `config/settings.local.yaml` | Application settings |
| `nyx.db` | SQLite database |
| `logs/nyx.log` | Application logs |

## Troubleshooting

### Import Error
```bash
poetry install --no-cache
```

### Clear Cache
```bash
find . -type d -name "__pycache__" -exec rm -rf {} +
```

### Reset Database
```bash
rm nyx.db
poetry run python -c "from nyx.core.database import initialize_database; import asyncio; asyncio.run(initialize_database())"
```

### View Logs
```bash
tail -f logs/nyx.log
```

## Resources

- **Full Setup Guide**: `docs/SETUP_GUIDE.md`
- **User Manual**: `docs/USER_MANUAL.md`
- **API Documentation**: `docs/API.md`
- **Project Status**: `PROJECT_STATUS.md`

## Need Help?

```bash
# CLI help
nyx-cli --help

# Command-specific help
nyx-cli search --help

# Check version
nyx-cli --version
```

---

**Ready to investigate! 🔍**
