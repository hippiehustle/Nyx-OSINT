# Nyx Windows Executable Build

This directory contains everything needed to build standalone Windows executables for Nyx.

## Overview

The Windows executable version provides:
- **Single-file or folder-based distribution** - Choose between onefile (single .exe) or onedir (folder with .exe + dependencies)
- **Separate GUI and CLI executables** - `nyx-gui.exe` and `nyx-cli.exe`
- **Combined launcher** - `nyx.exe` auto-detects GUI/CLI mode based on arguments
- **Built-in auto-updater** - Check for updates, download, and install automatically
- **Full feature parity** - All Python version features work identically
- **No Python required** - End users don't need Python installed

## Quick Start

### Prerequisites

1. **Python 3.12+** (for building only)
2. **Poetry** (dependency manager)
3. **PyInstaller** (included in requirements-build.txt)

### Build All Variants

```powershell
cd nyx-windows-exe
.\build.bat
```

This will build:
- `dist/nyx-gui-onefile.exe` - Single-file GUI executable
- `dist/nyx-gui-onedir/nyx-gui.exe` - Folder-based GUI executable
- `dist/nyx-cli-onefile.exe` - Single-file CLI executable
- `dist/nyx-cli-onedir/nyx-cli.exe` - Folder-based CLI executable
- `dist/nyx-launcher-onefile.exe` - Single-file launcher
- `dist/nyx-launcher-onedir/nyx.exe` - Folder-based launcher

### Build Specific Variant

```powershell
# GUI onefile
python build_scripts/build_gui.py --mode onefile

# CLI onedir
python build_scripts/build_cli.py --mode onedir

# Launcher onefile
python build_scripts/build_launcher.py --mode onefile
```

## Directory Structure

```
nyx-windows-exe/
├── src/                    # Source code (symlinks/copies from main src/)
│   ├── nyx/
│   │   ├── core/
│   │   │   ├── resource_paths.py    # Path resolution for executables
│   │   │   ├── updater.py           # Update manager
│   │   │   ├── update_client.py     # Update HTTP client
│   │   │   ├── update_service.py   # Background update service
│   │   │   └── version.py           # Version management
│   │   ├── config/
│   │   │   └── updater_config.py   # Update configuration
│   │   ├── utils/
│   │   │   └── update_utils.py     # Update utilities
│   │   └── launcher.py              # Entry point launcher
│   └── ...
├── specs/                  # PyInstaller spec files
│   ├── nyx-gui-onefile.spec
│   ├── nyx-gui-onedir.spec
│   ├── nyx-cli-onefile.spec
│   ├── nyx-cli-onedir.spec
│   ├── nyx-launcher-onefile.spec
│   └── nyx-launcher-onedir.spec
├── build_scripts/         # Build automation
│   ├── prepare_resources.py
│   ├── build_gui.py
│   ├── build_cli.py
│   ├── build_launcher.py
│   └── build_all.py
├── resources/             # Bundled resources
│   ├── data/
│   │   └── platforms/    # Platform JSON files
│   └── config/           # Default config files
├── build_config.yaml      # Build configuration
├── requirements-build.txt # Build-time dependencies
├── build.bat              # Windows build script
├── test_exe.py           # Executable testing script
└── README.md              # This file
```

## Build Configuration

Edit `build_config.yaml` to customize:

```yaml
version: "0.1.0"
name: "Nyx"
description: "OSINT Investigation Platform"
icon: "resources/icon.ico"  # Optional
onefile_size_limit: 100  # MB
exclude_modules:
  - "matplotlib"
  - "pandas"
include_data:
  - "data/platforms/*.json"
  - "config/settings.yaml"
```

## Resource Path Resolution

The executable uses `resource_paths.py` to resolve file paths:

- **Development mode**: Uses relative paths from project root
- **Executable mode**: Uses bundled resources in `sys._MEIPASS` or user data directories

### Path Resolution Priority

1. **Bundled resources** (`sys._MEIPASS/`) - Files included in executable
2. **Executable directory** - Files next to .exe
3. **User data directory** (`%APPDATA%/Nyx/`) - User-specific files
4. **Temporary directory** - Cache and temp files

## Auto-Updater

The executable includes a built-in auto-updater:

### Update Sources

1. **GitHub Releases** (default)
   - Configure `github_repo` in updater config
   - Automatically finds latest release
   - Downloads installer from release assets

2. **Custom Update Server**
   - Configure `custom_url` in updater config
   - Must provide `/api/version` and `/api/download/{version}` endpoints

### Update Configuration

Edit `config/settings.yaml`:

```yaml
updater:
  enabled: true
  source: github  # or "custom"
  github_repo: "owner/repo"  # For GitHub source
  custom_url: "https://updates.example.com"  # For custom source
  check_on_startup: true
  check_frequency: daily  # on_startup, daily, weekly, manual_only
  auto_download: false
  auto_install: false
  channel: stable  # stable, beta, alpha
  skip_versions: []  # Versions to skip
```

### Update Manifest Format

For custom update servers, provide JSON at `/api/version`:

```json
{
  "version": "0.2.0",
  "current_version": "0.1.0",
  "release_date": "2024-01-15T10:00:00Z",
  "changelog": "Bug fixes and improvements...",
  "critical": false,
  "prerelease": false,
  "installer": {
    "url": "https://example.com/updates/nyx-0.2.0-installer.exe",
    "size": 52428800,
    "filename": "nyx-0.2.0-installer.exe",
    "checksum": "sha256:abc123..."
  }
}
```

### Using the Updater

**GUI:**
- Go to Settings → Updates tab
- Click "Check for Updates"
- Download and install when available

**CLI:**
```powershell
# Check for updates
nyx-cli update check

# Download update
nyx-cli update download

# Install update
nyx-cli update install

# Show update status
nyx-cli update status

# Configure settings
nyx-cli update settings
```

## Testing

Test the executable:

```powershell
python test_exe.py dist/nyx-gui-onefile.exe
```

Or manually:
```powershell
# Test GUI
.\dist\nyx-gui-onefile.exe

# Test CLI
.\dist\nyx-cli-onefile.exe --help
.\dist\nyx-cli-onefile.exe search username

# Test launcher
.\dist\nyx-launcher-onefile.exe
.\dist\nyx-launcher-onefile.exe --help
```

## Distribution

### Onefile vs Onedir

**Onefile:**
- ✅ Single .exe file
- ✅ Easy distribution
- ❌ Slower startup (extracts to temp)
- ❌ Larger file size

**Onedir:**
- ✅ Faster startup
- ✅ Smaller main .exe
- ❌ Multiple files to distribute
- ❌ Requires folder structure

**Recommendation:** Use **onefile** for end-user distribution, **onedir** for development/testing.

### File Sizes

Typical sizes:
- GUI onefile: ~80-120 MB
- CLI onefile: ~60-90 MB
- Launcher onefile: ~70-100 MB

### Installation

For end users:
1. Download the .exe file
2. Run it (no installation required for onefile)
3. Or extract onedir folder and run .exe

For installer-based updates:
1. Updater downloads installer .exe
2. Runs installer silently
3. Replaces old executable
4. Restarts application

## Troubleshooting

### "Failed to load resource"

- Ensure resource files are included in `build_config.yaml`
- Check `specs/*.spec` includes `datas` entries
- Verify files exist in `resources/` directory

### "Database not found"

- Database is created in `%APPDATA%/Nyx/nyx.db` for executables
- Ensure user has write permissions to `%APPDATA%`

### "Update check failed"

- Check internet connectivity
- Verify `github_repo` or `custom_url` is configured
- Check firewall/proxy settings

### "Import error"

- Ensure all dependencies are included in spec file
- Check `hiddenimports` in spec files
- Run with `--debug` flag to see detailed errors

## Advanced Configuration

### Custom Icons

1. Create `.ico` file (256x256 recommended)
2. Place in `resources/icon.ico`
3. Update `build_config.yaml`:
   ```yaml
   icon: "resources/icon.ico"
   ```

### Excluding Modules

Reduce file size by excluding unused modules in `build_config.yaml`:

```yaml
exclude_modules:
  - "matplotlib"
  - "pandas"
  - "jupyter"
```

### Adding Hidden Imports

If PyInstaller misses imports, add to spec files:

```python
a = Analysis(
    ...
    hiddenimports=[
        'some.module',
        'another.module',
    ],
)
```

## Development

### Building from Source

1. Install dependencies:
   ```powershell
   poetry install
   cd nyx-windows-exe
   pip install -r requirements-build.txt
   ```

2. Prepare resources:
   ```powershell
   python build_scripts/prepare_resources.py
   ```

3. Build:
   ```powershell
   python build_scripts/build_all.py
   ```

### Debugging

Run with debug output:
```powershell
.\dist\nyx-gui-onefile.exe --debug
```

Check logs in `%APPDATA%/Nyx/logs/nyx.log`

## License

Same as main Nyx project.
